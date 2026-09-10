"""Restricted network capture for registered public sources.

Runtime health answers never call this module. It belongs to an administrative,
offline ingestion job and accepts only the exact registered HTTPS URL.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from app.schemas.content import SourceRecord

MAX_SOURCE_BYTES = 20 * 1024 * 1024


def _public_host(hostname: str) -> None:
    addresses = {result[4][0] for result in socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)}
    if not addresses:
        raise ValueError("registered source hostname did not resolve")
    for address in addresses:
        value = ipaddress.ip_address(address)
        if not value.is_global:
            raise ValueError("registered source resolved to a non-public address")


def fetch_registered_source(source: SourceRecord, *, maximum_bytes: int = MAX_SOURCE_BYTES,
                            timeout_seconds: int = 30) -> bytes:
    parsed = urlsplit(source.canonical_url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("source capture requires a registered public HTTPS URL without credentials")
    _public_host(parsed.hostname)
    request = Request(source.canonical_url, headers={"User-Agent": "NestlineOfflineIngestion/1.0"})
    with urlopen(request, timeout=timeout_seconds) as response:
        final = urlsplit(response.geturl())
        if final.scheme != "https" or final.hostname != parsed.hostname:
            raise ValueError("source redirected outside its registered HTTPS host")
        declared = response.headers.get("Content-Length")
        if declared and int(declared) > maximum_bytes:
            raise ValueError("source exceeds the ingestion size limit")
        expected = "pdf" if source.document_type == "pdf" else "html"
        content_type = response.headers.get_content_type()
        if expected == "pdf" and content_type != "application/pdf":
            raise ValueError("registered PDF returned a different content type")
        if expected == "html" and content_type not in {"text/html", "application/xhtml+xml"}:
            raise ValueError("registered HTML source returned a different content type")
        raw = response.read(maximum_bytes + 1)
    if len(raw) > maximum_bytes:
        raise ValueError("source exceeds the ingestion size limit")
    if not raw:
        raise ValueError("source returned an empty body")
    return raw
