"""Create a directly openable local preview with modern pages and original-host assets."""
from pathlib import Path
from urllib.parse import urljoin, urlsplit
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "preview"
ORIGIN = "https://pack12durham.org/"
css = (ROOT / "styles.css").read_text(encoding="utf-8")
pages = [ROOT / "index.html", ROOT / "aboutCubScouting.html", *sorted((ROOT / "PhotoBook").glob("*.html"))]
for source in pages:
    relative = source.relative_to(ROOT).as_posix()
    content = source.read_text(encoding="utf-8")
    content = re.sub(r'<link rel="stylesheet" href="[^"]+">', "<style>\n" + css + "\n</style>", content)
    def remote_asset(match):
        attr, value = match.groups()
        if urlsplit(value).scheme or value.startswith("#"):
            return match.group(0)
        target = urljoin(ORIGIN + relative, value)
        if urlsplit(target).path.lower().endswith((".png", ".jpeg", ".jpg", ".pdf")):
            return f'{attr}="{target}"'
        return match.group(0)
    content = re.sub(r'(src|href)="([^"]+)"', remote_asset, content)
    target = PREVIEW / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
shutil.copyfile(ROOT / "favicon.svg", PREVIEW / "favicon.svg")
print(PREVIEW / "index.html")
