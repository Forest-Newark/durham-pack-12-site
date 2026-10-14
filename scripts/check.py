"""Verify every page, original destination, asset, and legacy photo navigation route."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, urljoin, unquote
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
ORIGIN = "https://pack12durham.org/"

class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.images, self.text = [], [], [], []
        self.headings = 0
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag in ("a", "link"):
            self.links.append(attrs.get("href", ""))
        if tag == "img":
            self.images.append(attrs)
        if tag == "h1":
            self.headings += 1
    def handle_data(self, data):
        self.text.append(data)

def canonical(url):
    part = urlsplit(url)
    if part.hostname in ("pack12durham.org", "www.pack12durham.org"):
        return ORIGIN + (part.path.lstrip("/") or "index.html") + (
            "?" + part.query if part.query else "") + ("#" + part.fragment if part.fragment else "")
    return url

def check():
    parsers = {}
    for path in sorted(DIST.rglob("*.html")):
        if path.name == "preview.html":
            continue
        parser = SiteParser()
        parser.feed(path.read_text(encoding="utf-8"))
        assert parser.headings == 1, f"Expected one main heading: {path}"
        assert len(parser.ids) == len(set(parser.ids)), f"Duplicate IDs: {path}"
        parsers[path.relative_to(DIST).as_posix()] = parser
    for name, parser in parsers.items():
        page_url = ORIGIN + name
        for link in parser.links + [img["src"] for img in parser.images]:
            assert link, f"Empty destination in {name}"
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            target = urlsplit(urljoin(page_url, link))
            local = unquote(target.path.lstrip("/"))
            assert (DIST / local).is_file(), f"Missing local destination in {name}: {link}"
            if target.fragment:
                assert local in parsers and target.fragment in parsers[local].ids, f"Missing anchor: {name} → {link}"
        for img in parser.images:
            assert img.get("alt"), f"Missing image description: {name}"
    home = parsers["index.html"]
    text = " ".join(home.text)
    for phrase in ("A Pack for All People", "6:30 pm", "Yates Baptist Church",
                   "2819 Chapel Hill Rd.", "Rogers-Herr", "September–May",
                   "September 8 or 15, 2026", "These welcome dates have passed"):
        assert phrase in text, f"Source information missing: {phrase}"
    frozen = json.loads((ROOT / "content/source-inventory.json").read_text(encoding="utf-8"))
    live_path = ROOT / "source-audit/inventory.json"
    inventories = [frozen]
    if live_path.is_file():
        inventories.append(json.loads(live_path.read_text(encoding="utf-8")))
    coverage = []
    for inventory in inventories:
        for item in inventory["links"]:
            if item["tag"] not in ("a", "area", "img", "form", "frame", "iframe", "object", "embed"):
                continue
            source_page = canonical(item["page"])
            name = urlsplit(source_page).path.lstrip("/")
            assert name in parsers, f"Source page has no migrated route: {source_page}"
            parser = parsers[name]
            refs = [img["src"] for img in parser.images] if item["tag"] == "img" else parser.links
            targets = {canonical(urljoin(source_page, ref)) for ref in refs}
            assert canonical(item["url"]) in targets, f"Original function missing: {source_page} → {item['url']}"
            coverage.append({"source_page": item["page"], "destination": item["url"], "migrated_page": name, "status": "preserved"})
    manifest = json.loads((DIST / "asset-sources.json").read_text(encoding="utf-8"))
    for asset in manifest:
        content = (DIST / asset["path"]).read_bytes()
        assert hashlib.sha256(content).hexdigest() == asset["sha256"]
        assert len(content) == asset["bytes"]
    expected_assets = {urlsplit(item["url"]).path.lstrip("/") for item in frozen["links"]
                       if item["tag"] == "img" or item["url"].lower().endswith(".pdf")}
    assert expected_assets.issubset({asset["path"] for asset in manifest}), "Source asset not preserved"
    # Identical PDF bytes preserve embedded links, page navigation, and the full bilingual content.
    (DIST / "link-coverage.json").write_text(json.dumps(coverage, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(parsers)} pages, {len(manifest)} original assets, {len(coverage)} source references.")
    print("PASS: every original link/image is present on its corresponding page, including legacy gallery routes.")
    print("PASS: content, local destinations, anchors, accessibility descriptions, and preservation hashes.")

if __name__ == "__main__":
    check()
