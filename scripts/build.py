"""Build a dependency-free Pages site and preserve the original Pack 12 assets."""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError
import hashlib
import json
import shutil
import time
from content import render_pages, archive_html, load_site, ContentError

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
ORIGIN = "https://pack12durham.org/"
ASSETS = {
    "pics/Calendar_2026_08_19.pdf": b"%PDF-",
    "pics/DenLeaderHelp2026_08_28.pdf": b"%PDF-",
    "pics/PIP_EN_2026_08_23.pdf": b"%PDF-",
    "pics/PIP_ES_2026_08_23.pdf": b"%PDF-",
    "pics/FAQ_EN_2026_08_24.pdf": b"%PDF-",
    "pics/FAQ_ES_2026_08_24.pdf": b"%PDF-",
    "pics/ScoutMeIn.png": b"\x89PNG\r\n\x1a\n",
    "pics/EstamosListos.png": b"\x89PNG\r\n\x1a\n",
    "RegistrationInstructions_2024_08_04.pdf": b"%PDF-",
    "pics/Pack12Cubs_Color.png": b"\x89PNG\r\n\x1a\n",
    "PhotoBook/images/3OnBridge.jpeg": b"\xff\xd8\xff",
    "PhotoBook/images/3Cubs.jpeg": b"\xff\xd8\xff",
    "PhotoBook/images/BikeSafety.jpeg": b"\xff\xd8\xff",
    "PhotoBook/images/Campfire.jpeg": b"\xff\xd8\xff",
    "PhotoBook/images/Compass.jpeg": b"\xff\xd8\xff",
    "PhotoBook/images/CubsHi5.png": b"\x89PNG\r\n\x1a\n",
    "PhotoBook/images/Pals.jpeg": b"\xff\xd8\xff",
    "PhotoBook/images/Pinewood.jpeg": b"\xff\xd8\xff",
    "PhotoBook/images/PinewoodTrack.jpeg": b"\xff\xd8\xff",
    "PhotoBook/images/Salute.jpeg": b"\xff\xd8\xff",
    "PhotoBook/images/Toast.jpeg": b"\xff\xd8\xff",
    "PhotoBook/images/SpoonNose.jpeg": b"\xff\xd8\xff",
}

def download(path):
    url = ORIGIN + path
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={"User-Agent": "Pack12-Pages-POC/1.0"}), timeout=40) as response:
                return response.read()
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))

def build():
    pages = render_pages(ROOT)
    DIST.mkdir(exist_ok=True)
    for name, html in pages.items():
        (DIST / name).write_text(html, encoding="utf-8")
    (DIST / "original-resources.html").write_text(archive_html(ROOT), encoding="utf-8")
    shutil.copytree(ROOT / "edit", DIST / "edit", dirs_exist_ok=True)
    shutil.copytree(ROOT / "uploads", DIST / "uploads", dirs_exist_ok=True)
    for path in ("styles.css", "favicon.svg", ".nojekyll", "UPDATE-THE-SITE.html"):
        shutil.copyfile(ROOT / path, DIST / path)
    for path in sorted((ROOT / "PhotoBook").glob("*.html")):
        destination = DIST / "PhotoBook" / path.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
    for path in ("content/source-inventory.json", "content/site.json", "content/editor-schema.json"):
        destination = DIST / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, DIST / path)
    manifest = []
    for path, signature in ASSETS.items():
        cache = ROOT / "source-audit" / "assets" / path
        content = cache.read_bytes() if cache.is_file() else download(path)
        if not content.startswith(signature):
            raise ValueError(f"Unexpected file format from {ORIGIN + path}")
        destination = DIST / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        manifest.append({"path": path, "source": ORIGIN + path,
                         "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()})
        print(f"Preserved {path}: {len(content):,} bytes")
    (DIST / "asset-sources.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    # This portable preview uses the original asset URLs and can be opened directly in Chrome.
    preview = pages["index.html"]
    preview = preview.replace('<link rel="stylesheet" href="./styles.css">',
                              "<style>\n" + (ROOT / "styles.css").read_text(encoding="utf-8") + "\n</style>")
    preview = preview.replace('./pics/', ORIGIN + 'pics/')
    preview = preview.replace('./PhotoBook/index.html', ORIGIN + 'PhotoBook/pf1.html')
    preview = preview.replace('./PhotoBook/', ORIGIN + 'PhotoBook/')
    preview = preview.replace('./aboutCubScouting.html', ORIGIN + 'aboutCubScouting.html')
    preview = preview.replace('href="./RegistrationInstructions_2024_08_04.pdf"',
                              'href="' + ORIGIN + 'RegistrationInstructions_2024_08_04.pdf"')
    preview = preview.replace('<link rel="icon" href="./favicon.svg" type="image/svg+xml">', "")
    (DIST / "preview.html").write_text(preview, encoding="utf-8")
    print("Built dist/ (ready for GitHub Pages).")

if __name__ == "__main__":
    try:
        build()
    except ContentError as error:
        raise SystemExit(f"Please fix your website content: {error}") from None
