"""Embedding boundary for approved public evidence.

Production configuration is OpenAI-compatible so the team can select one provider
without changing ingestion. Tests use a clearly labelled non-semantic fake.
"""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Protocol
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class EmbeddingProvider(Protocol):
    name: str
    model: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class OpenAICompatibleEmbeddingProvider:
    def __init__(self, *, name: str, base_url: str, api_key: str, model: str,
                 timeout_seconds: int = 30, maximum_response_bytes: int = 10 * 1024 * 1024):
        if not all(value.strip() for value in (name, base_url, api_key, model)):
            raise ValueError("embedding provider name, URL, API key and model are required")
        parsed = urlsplit(base_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("embedding endpoint must be a public HTTPS URL without credentials")
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.maximum_response_bytes = maximum_response_bytes

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        body = json.dumps({"model": self.model, "input": texts}).encode("utf-8")
        request = Request(self.base_url, data=body, method="POST",
                          headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        with urlopen(request, timeout=self.timeout_seconds) as response:
            raw = response.read(self.maximum_response_bytes + 1)
        if len(raw) > self.maximum_response_bytes:
            raise ValueError("embedding provider response exceeds the size limit")
        payload = json.loads(raw)
        rows = sorted(payload.get("data", []), key=lambda row: row.get("index", -1))
        vectors = [row.get("embedding") for row in rows]
        if len(vectors) != len(texts) or not all(isinstance(v, list) and v for v in vectors):
            raise ValueError("embedding provider returned an incomplete response")
        dimensions = len(vectors[0])
        if any(len(vector) != dimensions or not all(isinstance(value, (int, float)) for value in vector)
               for vector in vectors):
            raise ValueError("embedding provider returned invalid vector dimensions")
        return vectors


class DeterministicTestEmbeddingProvider:
    """Non-semantic test double. Never use it for a published corpus."""

    name = "TEST_ONLY"
    model = "sha256-test-vector-v1"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[(byte - 127.5) / 127.5 for byte in sha256(text.encode("utf-8")).digest()]
                for text in texts]
