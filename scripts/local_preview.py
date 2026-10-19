"""Render editable content for a directly openable local preview."""
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from content import render_pages, archive_html
import re
import shutil
ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "preview"
ORIGIN = "https://pack12durham.org/"
css = (ROOT / "styles.css").read_text(encoding="utf-8")
pages = render_pages(ROOT)
pages["original-resources.html"] = archive_html(ROOT)
for path in (ROOT / "PhotoBook").glob("*.html"):
    pages[path.relative_to(ROOT).as_posix()] = path.read_text(encoding="utf-8")
for relative, content in pages.items():
    content = re.sub(r'<link rel="stylesheet" href="[^"]+">', lambda _: "<style>\n" + css + "\n</style>", content)
    def remote_asset(match):
        attr, value = match.groups()
        if urlsplit(value).scheme or value.startswith("#"):
            return match.group(0)
        target = urljoin(ORIGIN + relative, value)
        if urlsplit(target).path.lower().endswith((".png", ".jpeg", ".jpg", ".pdf")) and "/uploads/" not in target:
            return f'{attr}="{target}"'
        return match.group(0)
    content = re.sub(r'(src|href)="([^"]+)"', remote_asset, content)
    target = PREVIEW / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
for folder in ("edit", "content", "uploads"):
    shutil.copytree(ROOT / folder, PREVIEW / folder, dirs_exist_ok=True)
shutil.copyfile(ROOT / "favicon.svg", PREVIEW / "favicon.svg")
print(PREVIEW / "index.html")
