"""Fetch Stripe doc pages and save raw HTML."""
import httpx
import hashlib
from pathlib import Path
from urllib.parse import urlparse

RAW_DIR = Path("data/raw_html")
RAW_DIR.mkdir(parents=True, exist_ok=True)

URLS = [
    "https://docs.stripe.com/payments/payment-intents",
    "https://docs.stripe.com/api/payment_intents/object",
    "https://docs.stripe.com/payments/accept-a-payment",
]

def url_to_filename(url: str) -> str:
    """Stable filename from URL path."""
    path = urlparse(url).path.strip("/").replace("/", "__")
    return f"{path or 'index'}.html"

def fetch(url: str) -> tuple[str, str]:
    """Returns (html_content, content_hash)."""
    resp = httpx.get(url, timeout=30, follow_redirects=True,
                     headers={"User-Agent": "Mozilla/5.0 (RAG portfolio project)"})
    resp.raise_for_status()
    html = resp.text
    h = hashlib.sha256(html.encode()).hexdigest()[:16]
    return html, h

def main():
    for url in URLS:
        print(f"Fetching {url}")
        html, content_hash = fetch(url)
        filename = url_to_filename(url)
        path = RAW_DIR / filename
        path.write_text(html, encoding="utf-8")
        print(f"  → saved {path} ({len(html)} bytes, hash {content_hash})")

if __name__ == "__main__":
    main()