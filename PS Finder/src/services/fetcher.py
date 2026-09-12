import hashlib
import ipaddress
import logging
from urllib.parse import urlparse
import httpx

from src.config.settings import get_settings
from src.sources.base import RawSource

logger = logging.getLogger(__name__)
settings = get_settings()


class SafeFetcher:
    """Safe asynchronous fetcher with SSRF prevention, timeouts, and hashing."""

    def __init__(self):
        self.timeout = httpx.Timeout(settings.REQUEST_TIMEOUT_SECONDS, connect=10.0)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 (ALPHA SIH Verified Opportunity Discovery Agent)"
        }

    def _is_safe_url(self, url: str) -> bool:
        """Validate URL to prevent SSRF against loopback or private networks."""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return False
            hostname = parsed.hostname
            if not hostname:
                return False

            # Check for localhost/loopback
            if hostname.lower() in ("localhost", "127.0.0.1", "::1"):
                return False

            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
                    return False
            except ValueError:
                # Hostname is a domain name, which is normal
                pass
            return True
        except Exception:
            return False

    @staticmethod
    def _decode(resp: httpx.Response) -> str:
        """Decode response bytes to text with correct encoding.

        Many Indian government portals (mygov.in, *.gov.in) serve UTF-8 without a
        charset in the Content-Type header. httpx then guesses and can mangle
        characters like ' or – into U+FFFD (the "Avinya�27" bug). We honour an
        explicit header charset when present, otherwise prefer strict UTF-8 and only
        fall back to httpx's best-effort decode if the bytes are genuinely not UTF-8.
        """
        charset = resp.charset_encoding  # charset declared in Content-Type header, else None
        if charset:
            try:
                return resp.content.decode(charset, errors="replace")
            except (LookupError, TypeError):
                pass
        try:
            return resp.content.decode("utf-8")
        except UnicodeDecodeError:
            return resp.text

    async def fetch(self, url: str) -> RawSource:
        """Fetch URL content safely and compute SHA-256 hash."""
        if not self._is_safe_url(url):
            raise ValueError(f"Blocked unsafe or non-HTTP URL: {url}")

        async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()

            content = resp.content
            if len(content) > settings.MAX_FILE_SIZE_BYTES:
                raise ValueError(f"Content length {len(content)} exceeds maximum limit {settings.MAX_FILE_SIZE_BYTES} bytes")

            content_type = resp.headers.get("content-type", "").lower()
            doc_hash = hashlib.sha256(content).hexdigest()

            text_content = self._decode(resp)
            return RawSource(
                url=url,
                final_url=str(resp.url),
                status_code=resp.status_code,
                content_type=content_type,
                text_content=text_content,
                raw_html=text_content if "text/html" in content_type else None,
                document_hash=doc_hash,
                metadata={"content_length": len(content)}
            )

    def fetch_sync(self, url: str, timeout_seconds: float | None = None) -> RawSource:
        """Synchronously fetch URL content safely and compute SHA-256 hash.

        ``timeout_seconds`` optionally overrides the configured timeout (used by the
        monitoring job, which re-checks many sources and should not block for long).
        """
        if not self._is_safe_url(url):
            raise ValueError(f"Blocked unsafe or non-HTTP URL: {url}")

        timeout = httpx.Timeout(timeout_seconds, connect=10.0) if timeout_seconds else self.timeout
        with httpx.Client(headers=self.headers, timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()

            content = resp.content
            if len(content) > settings.MAX_FILE_SIZE_BYTES:
                raise ValueError(f"Content length {len(content)} exceeds maximum limit {settings.MAX_FILE_SIZE_BYTES} bytes")

            content_type = resp.headers.get("content-type", "").lower()
            doc_hash = hashlib.sha256(content).hexdigest()

            text_content = self._decode(resp)
            return RawSource(
                url=url,
                final_url=str(resp.url),
                status_code=resp.status_code,
                content_type=content_type,
                text_content=text_content,
                raw_html=text_content if "text/html" in content_type else None,
                document_hash=doc_hash,
                metadata={"content_length": len(content)}
            )

