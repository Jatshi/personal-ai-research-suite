from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen

from bs4 import BeautifulSoup


def load_url(url: str, timeout: int = 10) -> dict[str, Any]:
    parsed = urlparse(url)
    if parsed.scheme == "file":
        html = Path(parsed.path).read_text(encoding="utf-8", errors="ignore")
    else:
        with urlopen(url, timeout=timeout) as response:  # nosec - user supplied local demo URLs are intentional.
            html = response.read().decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    title = soup.title.string.strip() if soup.title and soup.title.string else url
    author = ""
    meta_author = soup.find("meta", attrs={"name": "author"})
    if meta_author:
        author = meta_author.get("content", "")
    return {
        "text": soup.get_text("\n"),
        "metadata": {
            "title": title,
            "author": author,
            "source_url": url,
            "site_name": parsed.netloc or "local",
            "file_type": "html",
            "language": "zh" if any("\u4e00" <= c <= "\u9fff" for c in title) else "en",
        },
    }

