"""Deterministic HTML/PDF parsing for public sources.

The parser preserves structural anchors and reports pages that require OCR. It
does not infer medical applicability or approve extracted text.
"""

from __future__ import annotations

from hashlib import sha256
import re
import shutil
import subprocess
import unicodedata
from typing import Protocol

from bs4 import BeautifulSoup
import fitz

from app.schemas.ingestion import IngestionIssue, ParsedBlock

PARSER_VERSION = "1.0.0"


class OcrProvider(Protocol):
    """Explicit adapter for pages with no usable text layer."""

    name: str
    version: str

    def extract_page(self, png: bytes, page_number: int) -> tuple[str, float]: ...


class TesseractCliOcrProvider:
    """Local OCR adapter. It never downloads models or silently changes language."""

    name = "tesseract-cli"

    def __init__(self, executable: str = "tesseract", language: str = "eng"):
        resolved = shutil.which(executable)
        if resolved is None:
            raise ValueError(f"Tesseract executable is unavailable: {executable}")
        self.executable = resolved
        self.language = language
        result = subprocess.run([self.executable, "--version"], capture_output=True, text=True, check=False)
        if result.returncode:
            raise ValueError("Tesseract version check failed")
        self.version = result.stdout.splitlines()[0].strip()

    def extract_page(self, png: bytes, page_number: int) -> tuple[str, float]:
        result = subprocess.run([self.executable, "stdin", "stdout", "-l", self.language],
                                input=png, capture_output=True, check=False, timeout=60)
        if result.returncode:
            raise ValueError(f"Tesseract failed on page {page_number}")
        return result.stdout.decode("utf-8", errors="replace"), 0.75


def normalize_text(value: str) -> str:
    """Create conservative search text while preserving original citation text."""
    value = unicodedata.normalize("NFKC", value)
    value = value.replace("\u00ad", "").replace("\u2018", "'").replace("\u2019", "'")
    value = value.replace("\u201c", '"').replace("\u201d", '"')
    value = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2212]", "-", value)
    return " ".join(value.casefold().split())


def _identifier(prefix: str, *values: object) -> str:
    digest = sha256("\x1f".join(str(v) for v in values).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}-{digest}"


def parse_html(source_id: str, raw: bytes) -> tuple[list[ParsedBlock], list[IngestionIssue]]:
    try:
        soup = BeautifulSoup(raw, "html.parser")
    except Exception as exc:
        return [], [IngestionIssue(code="HTML_PARSE_FAILED", severity="error",
                                   message=f"HTML could not be parsed: {type(exc).__name__}.",
                                   source_id=source_id)]
    for tag in soup.select("script, style, nav, footer, form, noscript, svg, template"):
        tag.decompose()
    container = soup.find("main") or soup.find("article") or soup.body or soup
    blocks: list[ParsedBlock] = []
    headings: dict[int, str] = {}
    ordinal = 0
    for node in container.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "table"]):
        if node.find_parent("table") is not None and node.name != "table":
            continue
        if node.name == "table":
            rows = []
            for row in node.find_all("tr"):
                cells = [" ".join(cell.get_text(" ", strip=True).split()) for cell in row.find_all(["th", "td"])]
                if any(cells):
                    rows.append(" | ".join(cells))
            text = "\n".join(rows)
            kind = "table"
        else:
            text = " ".join(node.get_text(" ", strip=True).split())
            kind = "heading" if node.name.startswith("h") else "list_item" if node.name == "li" else "paragraph"
        if not text:
            continue
        if kind == "heading":
            level = int(node.name[1])
            headings = {key: value for key, value in headings.items() if key < level}
            headings[level] = text
        path = [headings[key] for key in sorted(headings)]
        locator = " / ".join(path) if path else f"HTML block {ordinal + 1}"
        if kind != "heading":
            locator += f" / {kind} {ordinal + 1}"
        blocks.append(ParsedBlock(block_id=_identifier("B", source_id, ordinal, text), source_id=source_id,
                                  ordinal=ordinal, block_kind=kind, text=text,
                                  normalized_text=normalize_text(text), locator=locator,
                                  heading_path=path, extraction_method="html_structure",
                                  extraction_confidence=1.0))
        ordinal += 1
    issues = []
    if not blocks:
        issues.append(IngestionIssue(code="NO_TEXT", severity="error", message="HTML contained no usable structured text.",
                                     source_id=source_id))
    return blocks, issues


def _pdf_text(block: dict) -> tuple[str, float]:
    lines, sizes = [], []
    for line in block.get("lines", []):
        parts = []
        for span in line.get("spans", []):
            value = span.get("text", "").strip()
            if value:
                parts.append(value)
                sizes.append(float(span.get("size", 0)))
        if parts:
            lines.append(" ".join(parts))
    return " ".join(lines), max(sizes, default=0)


def parse_pdf(source_id: str, raw: bytes, *, selected_pages: set[int] | None = None,
              minimum_page_characters: int = 40,
              ocr_provider: OcrProvider | None = None) -> tuple[list[ParsedBlock], list[IngestionIssue]]:
    try:
        document = fitz.open(stream=raw, filetype="pdf")
    except Exception as exc:
        return [], [IngestionIssue(code="PDF_OPEN_FAILED", severity="error",
                                   message=f"PDF could not be opened: {type(exc).__name__}.", source_id=source_id)]
    if document.needs_pass:
        document.close()
        return [], [IngestionIssue(code="PDF_LOCKED", severity="error", message="PDF requires a password.", source_id=source_id)]
    blocks: list[ParsedBlock] = []
    issues: list[IngestionIssue] = []
    ordinal = 0
    for page_number, page in enumerate(document, 1):
        if selected_pages and page_number not in selected_pages:
            continue
        page_items = []
        try:
            dictionary = page.get_text("dict", sort=True)
        except Exception as exc:
            issues.append(IngestionIssue(code="PDF_PAGE_PARSE_FAILED", severity="error",
                                         message=f"PDF page could not be parsed: {type(exc).__name__}.",
                                         source_id=source_id, page=page_number,
                                         locator=f"Page {page_number}"))
            continue
        for raw_block in dictionary.get("blocks", []):
            if raw_block.get("type") != 0:
                continue
            text, maximum_size = _pdf_text(raw_block)
            if text:
                page_items.append((raw_block.get("bbox", (0, 0, 0, 0)), text, maximum_size))
        page_text = " ".join(item[1] for item in page_items)
        if len(normalize_text(page_text)) < minimum_page_characters:
            if ocr_provider is None:
                issues.append(IngestionIssue(code="NEEDS_OCR", severity="error",
                                             message="Page has too little extractable text; configure an OCR provider.",
                                             source_id=source_id, page=page_number, locator=f"Page {page_number}"))
                continue
            try:
                png = page.get_pixmap(dpi=200, alpha=False).tobytes("png")
                ocr_text, confidence = ocr_provider.extract_page(png, page_number)
                ocr_text = " ".join(ocr_text.split())
                if (not isinstance(confidence, (int, float)) or isinstance(confidence, bool)
                        or not 0 <= confidence <= 1):
                    raise ValueError("OCR confidence must be numeric")
            except Exception as exc:
                issues.append(IngestionIssue(code="OCR_FAILED", severity="error",
                                             message=f"OCR failed safely: {type(exc).__name__}.",
                                             source_id=source_id, page=page_number, locator=f"Page {page_number}"))
                continue
            if len(normalize_text(ocr_text)) < minimum_page_characters:
                issues.append(IngestionIssue(code="OCR_NO_TEXT", severity="error",
                                             message="OCR returned too little usable text.",
                                             source_id=source_id, page=page_number, locator=f"Page {page_number}"))
                continue
            blocks.append(ParsedBlock(block_id=_identifier("B", source_id, page_number, "ocr", ocr_text),
                                      source_id=source_id, ordinal=ordinal, block_kind="paragraph",
                                      text=ocr_text, normalized_text=normalize_text(ocr_text),
                                      locator=f"Page {page_number} / OCR", page=page_number,
                                      extraction_method="ocr", extraction_confidence=confidence))
            ordinal += 1
            issues.append(IngestionIssue(code="OCR_APPLIED", severity="info",
                                         message=f"Page text was extracted with {ocr_provider.name} {ocr_provider.version}.",
                                         source_id=source_id, page=page_number, locator=f"Page {page_number}"))
            continue
        font_sizes = sorted(item[2] for item in page_items if item[2] > 0)
        median_size = font_sizes[len(font_sizes) // 2] if font_sizes else 0
        current_heading = ""
        for _bbox, text, maximum_size in page_items:
            kind = "heading" if maximum_size >= median_size * 1.35 and len(text) <= 180 else "paragraph"
            if kind == "heading":
                current_heading = text
            locator = f"Page {page_number}"
            if current_heading:
                locator += f" / {current_heading}"
            if kind != "heading":
                locator += f" / block {ordinal + 1}"
            blocks.append(ParsedBlock(block_id=_identifier("B", source_id, page_number, ordinal, text),
                                      source_id=source_id, ordinal=ordinal, block_kind=kind,
                                      text=text, normalized_text=normalize_text(text), locator=locator,
                                      heading_path=[current_heading] if current_heading else [], page=page_number,
                                      extraction_method="pdf_text", extraction_confidence=1.0))
            ordinal += 1
        # Preserve detected table cell relationships as a separate structured block.
        try:
            tables = page.find_tables().tables
        except Exception:
            tables = []
        for table_number, table in enumerate(tables, 1):
            rows = []
            for row in table.extract():
                cells = [" ".join((cell or "").split()) for cell in row]
                if any(cells):
                    rows.append(" | ".join(cells))
            text = "\n".join(rows)
            if text:
                locator = f"Page {page_number} / table {table_number}"
                blocks.append(ParsedBlock(block_id=_identifier("B", source_id, page_number, "table", table_number, text),
                                          source_id=source_id, ordinal=ordinal, block_kind="table", text=text,
                                          normalized_text=normalize_text(text), locator=locator,
                                          page=page_number, extraction_method="pdf_text",
                                          extraction_confidence=1.0))
                ordinal += 1
    document.close()
    if not blocks and not issues:
        issues.append(IngestionIssue(code="NO_TEXT", severity="error", message="PDF contained no usable text.", source_id=source_id))
    return blocks, issues
