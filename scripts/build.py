"""Build a dependency-free Pages site and preserve the original Pack 12 assets."""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError
import hashlib
import json
import shutil
import time

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
ORIGIN = "https://pack12durham.org/"
ASSETS = {
    "pics/ScoutMeIn.png": b"\x89PNG\r\n\x1a\n",
    "pics/EstamosListos.png": b"\x89PNG\r\n\x1a\n",
    "pics/Pack12Cubs_Color.png": b"\x89PNG\r\n\x1a\n",
    "RegistrationInstructions_2024_08_04.pdf": b"%PDF-",
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
    DIST.mkdir(exist_ok=True)
    for path in ("index.html", "styles.css", "favicon.svg", ".nojekyll"):
        shutil.copyfile(ROOT / path, DIST / path)
    manifest = []
    for path, signature in ASSETS.items():
        content = download(path)
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
    preview = (ROOT / "index.html").read_text(encoding="utf-8")
    preview = preview.replace('<link rel="stylesheet" href="./styles.css">',
                              "<style>\n" + (ROOT / "styles.css").read_text(encoding="utf-8") + "\n</style>")
    preview = preview.replace('./pics/', ORIGIN + 'pics/')
    preview = preview.replace('href="./RegistrationInstructions_2024_08_04.pdf"',
                              'href="' + ORIGIN + 'RegistrationInstructions_2024_08_04.pdf"')
    preview = preview.replace('<link rel="icon" href="./favicon.svg" type="image/svg+xml">', "")
    (DIST / "preview.html").write_text(preview, encoding="utf-8")
    print("Built dist/ (ready for GitHub Pages).")

if __name__ == "__main__":
    build()
