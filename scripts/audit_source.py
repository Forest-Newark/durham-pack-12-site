"""Inventory every reachable original page, navigation link, image, and PDF destination."""
from collections import deque
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urldefrag
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from pypdf import PdfReader
import json
import hashlib
import re
import time

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://pack12durham.org/"
HOSTS = {"pack12durham.org", "www.pack12durham.org"}

class Inventory(HTMLParser):
    def __init__(self, url):
        super().__init__()
        self.base = url
        self.items = []
        self.anchor = None
        self.title = []
        self.in_title = False
    def add(self, tag, attr, value, label=""):
        if value:
            self.items.append({"tag": tag, "attribute": attr, "original": value,
                               "url": urljoin(self.base, value), "label": label})
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "base" and attrs.get("href"):
            self.base = urljoin(self.base, attrs["href"])
        if tag == "title":
            self.in_title = True
        if tag in ("a", "area") and attrs.get("href"):
            self.add(tag, "href", attrs["href"], attrs.get("title", attrs.get("alt", "")))
            if tag == "a":
                self.anchor = self.items[-1]
        if tag in ("frame", "iframe", "script", "embed"):
            self.add(tag, "src", attrs.get("src"), attrs.get("title", ""))
        if tag == "form":
            self.add(tag, "action", attrs.get("action"), attrs.get("name", ""))
        if tag == "object":
            self.add(tag, "data", attrs.get("data"))
        if tag == "img":
            self.add(tag, "src", attrs.get("src"), attrs.get("alt", ""))
            if self.anchor and attrs.get("alt"):
                self.anchor["label"] += " " + attrs["alt"]
        if tag == "link":
            self.add(tag, "href", attrs.get("href"), attrs.get("rel", ""))
        # Also record simple legacy inline navigation and script redirects.
        for key in ("onclick", "onchange", "onload"):
            for match in re.finditer(r"(?:location(?:\.href)?\s*=|window\.open\()\s*['\"]([^'\"]+)", attrs.get(key, "")):
                self.add(tag, key, match.group(1), attrs.get("title", ""))
    def handle_endtag(self, tag):
        if tag == "a":
            self.anchor = None
        if tag == "title":
            self.in_title = False
    def handle_data(self, data):
        if self.anchor:
            self.anchor["label"] += " " + data
        if self.in_title:
            self.title.append(data)

def get(url):
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={"User-Agent": "Pack12-Pages-Link-Audit/1.0"}), timeout=30) as response:
                return response.read(), response.headers.get("Content-Type", ""), response.geturl()
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(1 + attempt)

def audit():
    queue = deque([ORIGIN, "https://www.pack12durham.org/"])
    visited = set()
    pages, links, assets, failures, records = [], [], [], [], []
    archive = ROOT / "source-audit"
    archive.mkdir(exist_ok=True)
    while queue:
        url = urldefrag(queue.popleft())[0]
        if url in visited:
            continue
        if len(visited) >= 150:
            raise RuntimeError("Source crawl reached 150 pages; inspect before increasing the limit.")
        visited.add(url)
        try:
            content, kind, final_url = get(url)
        except Exception as error:
            failures.append({"url": url, "error": str(error)})
            print("SOURCE FETCH ISSUE", url, str(error))
            continue
        if "html" not in kind and not content.lstrip().lower().startswith((b"<!doctype", b"<html", b"<head")):
            continue
        parser = Inventory(final_url)
        text = content.decode("utf-8", errors="replace")
        parser.feed(text)
        title = " ".join(parser.title).strip()
        pages.append({"url": url, "final_url": final_url, "title": title})
        (archive / f"page-{len(pages):03d}.html").write_bytes(content)
        print("SOURCE PAGE", url, title)
        for item in parser.items:
            item["label"] = " ".join(item["label"].split())
            item["page"] = url
            links.append(item)
            print("SOURCE LINK", json.dumps(item, ensure_ascii=False))
            target = urlsplit(item["url"])
            if target.hostname in HOSTS and target.scheme in ("http", "https"):
                suffix = Path(target.path).suffix.lower()
                if item["tag"] in ("frame", "iframe") or (
                    item["tag"] in ("a", "area") and suffix in ("", ".htm", ".html", ".php", ".asp")):
                    queue.append(item["url"])
                elif suffix in (".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".doc", ".docx", ".ics"):
                    assets.append(item["url"])
    asset_urls = sorted({url.replace("://www.pack12durham.org/", "://pack12durham.org/") for url in assets})
    for url in asset_urls:
        try:
            content, kind, final_url = get(url)
            asset_path = urlsplit(url).path.lstrip("/")
            destination = archive / "assets" / asset_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
            records.append({"url": url, "path": asset_path, "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)})
            print("SOURCE ASSET OK", url, len(content), kind)
            if urlsplit(url).path.lower().endswith(".pdf"):
                reader = PdfReader(BytesIO(content))
                for number, page in enumerate(reader.pages, 1):
                    destinations = {uri.rstrip(".,;:)]}") for uri in re.findall(r"https?://[^\s<>]+", page.extract_text() or "")}
                    for annotation in page.get("/Annots", []):
                        obj = annotation.get_object()
                        action = obj.get("/A")
                        if action:
                            action = action.get_object()
                            if action.get("/URI"):
                                destinations.add(str(action["/URI"]))
                    for destination in sorted(destinations):
                        item = {"tag": "pdf-link", "attribute": "uri", "original": destination,
                                "url": destination, "label": f"PDF page {number}", "page": url}
                        links.append(item)
                        print("SOURCE PDF LINK", json.dumps(item, ensure_ascii=False))
        except Exception as error:
            failures.append({"url": url, "error": str(error)})
            print("SOURCE ASSET ISSUE", url, str(error))
    report = {"origin": ORIGIN, "pages": pages, "links": links,
              "assets": asset_urls, "asset_records": records, "fetch_issues": failures}
    (archive / "inventory.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not pages:
        raise RuntimeError("No source pages were fetched; audit is incomplete.")
    print(f"Audited {len(pages)} pages, {len(links)} references, {len(set(assets))} assets; {len(failures)} fetch issues.")
    if failures:
        raise RuntimeError("Source audit has fetch issues; inspect rather than silently omitting destinations.")

if __name__ == "__main__":
    audit()
