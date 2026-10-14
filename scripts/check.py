"""Check the built site, including the source content and every local link."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.images = []
        self.text = []
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

def check():
    parser = SiteParser()
    parser.feed((DIST / "index.html").read_text(encoding="utf-8"))
    assert parser.headings == 1, "Expected one main heading"
    assert len(parser.ids) == len(set(parser.ids)), "Duplicate element IDs"
    for link in parser.links:
        assert link, "Empty link"
        url = urlsplit(link)
        if url.scheme or url.netloc:
            continue
        if url.path:
            assert (DIST / unquote(url.path)).is_file(), f"Missing local link: {link}"
        if url.fragment:
            assert url.fragment in parser.ids, f"Missing anchor: {link}"
    expected_images = {"./pics/ScoutMeIn.png", "./pics/EstamosListos.png", "./pics/Pack12Cubs_Color.png"}
    assert {img["src"] for img in parser.images} == expected_images, "Original image missing"
    for img in parser.images:
        assert img.get("alt"), "Missing image description"
        assert (DIST / img["src"]).is_file(), f"Missing image: {img['src']}"
    expected_links = {
        "https://pack12durham.org/RegistrationInstructions_2024_08_04.pdf",
        "https://www.scouting.org/programs/cub-scouts/what-cub-scouts-earn/",
        "mailto:committeechair@pack12durham.org",
        "mailto:cubmaster@pack12durham.org",
    }
    assert expected_links.issubset(parser.links), "Original destination missing"
    text = " ".join(parser.text)
    for phrase in ("A Pack for All People", "6:30 pm", "Yates Baptist Church",
                   "2819 Chapel Hill Rd.", "Rogers-Herr", "September–May",
                   "September 8 or 15, 2026", "These welcome dates have passed"):
        assert phrase in text, f"Source information missing: {phrase}"
    for asset in json.loads((DIST / "asset-sources.json").read_text(encoding="utf-8")):
        content = (DIST / asset["path"]).read_bytes()
        assert hashlib.sha256(content).hexdigest() == asset["sha256"]
        assert len(content) == asset["bytes"]
    print("PASS: source content, original destinations, images, local links, anchors, and asset hashes.")

if __name__ == "__main__":
    check()
