"""Exercise the full site at project-subpath URLs and save review screenshots."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
import json
import os

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "screenshots"
OUTPUT.mkdir(exist_ok=True)
server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(ROOT)))
Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_port}/dist/"
inventory = json.loads((ROOT / "content/source-inventory.json").read_text(encoding="utf-8"))
routes = sorted({urlsplit(page).path.lstrip("/") or "index.html" for page in inventory["pages"]})
errors = []

def check_layout(page, width):
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), f"Overflow: {width}px at {page.url}"
    for image in page.locator("img").all():
        image.scroll_into_view_if_needed()
        image.evaluate("(el) => el.decode()")
        assert image.evaluate("(el) => el.complete && el.naturalWidth > 0")
        assert image.evaluate("(el) => el.getBoundingClientRect().width <= el.naturalWidth + 1"), f"Image enlarged: {page.url}"
    if width <= 768:
        for selector in (".hero-description", ".adventure-card p", ".registration-card > p:not(.fine-print)", ".faq details p", "nav a", ".resource-card p", ".resource-link", ".page-intro"):
            for element in page.locator(selector).all():
                assert element.evaluate("(el) => parseFloat(getComputedStyle(el).fontSize) >= 16"), f"Small text: {selector}"
    page.evaluate("window.scrollTo(0, 0)")

try:
    with sync_playwright() as playwright:
        options = {"headless": True}
        if os.environ.get("PACK12_CHROME"):
            options["executable_path"] = os.environ["PACK12_CHROME"]
        browser = playwright.chromium.launch(**options)
        for width in (360, 390, 768, 1440):
            page = browser.new_page(viewport={"width": width, "height": 960}, device_scale_factor=2, reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))
            response = page.goto(base + "index.html", wait_until="networkidle")
            assert response.status == 200
            assert page.title() == "Pack 12 Durham · A Pack for All People"
            assert page.locator(".adventure-stamp svg").count() == 1
            assert page.locator(".adventure-stamp").evaluate("(el) => getComputedStyle(el).transform === 'none'")
            page.keyboard.press("Tab")
            assert page.locator(".skip-link").evaluate("(el) => el === document.activeElement")
            page.keyboard.press("Enter")
            page.locator('nav a[href="#meetings"]').click()
            assert page.locator("#meetings").is_visible()
            page.locator('nav a[href="#resources"]').click()
            assert page.locator("#resources").is_visible()
            page.locator("details").first.locator("summary").click()
            assert page.locator("details").first.get_attribute("open") is not None
            page.locator("details").first.locator("summary").click()
            check_layout(page, width)
            page.screenshot(path=str(OUTPUT / f"pack12-{width}.png"), full_page=True)
            if width in (390, 1440):
                for route in routes + ["PhotoBook/index.html"]:
                    if route == "index.html":
                        continue
                    response = page.goto(base + route, wait_until="networkidle")
                    assert response.status == 200, route
                    check_layout(page, width)
                    if route in ("PhotoBook/index.html", "PhotoBook/pf1.html", "aboutCubScouting.html"):
                        page.screenshot(path=str(OUTPUT / f"{Path(route).stem}-{width}.png"), full_page=True)
                page.goto(base + "PhotoBook/pf1.html")
                page.locator(".photo-controls").get_by_role("link", name="Next Photo").click()
                assert page.url.endswith("/PhotoBook/pf2.html")
                page.locator(".photo-controls").get_by_role("link", name="Previous Photo").click()
                assert page.url.endswith("/PhotoBook/pf1.html")
                page.locator(".photo-controls").get_by_role("link", name="All photos").click()
                assert page.locator(".photo-tile").count() == 12
                page.locator(".photo-tile").nth(11).click()
                assert page.url.endswith("/PhotoBook/pf16.html")
                page.locator(".photo-controls").get_by_role("link", name="Next Photo").click()
                assert page.url.endswith("/PhotoBook/pf1.html")
                page.locator(".photo-controls").get_by_role("link", name="Home", exact=True).click()
                assert page.url.endswith("/index.html")
            if width == 390:
                assets = json.loads((ROOT / "dist/asset-sources.json").read_text(encoding="utf-8"))
                for asset in assets:
                    if asset["path"].endswith(".pdf"):
                        response = page.request.get(base + asset["path"])
                        assert response.status == 200 and response.body().startswith(b"%PDF-"), asset["path"]
            print(f"PASS: {width}px, sharp SVG badge, native-size images, readable text, navigation, resource PDFs, and gallery.")
            page.close()
        assert not errors, errors
        browser.close()
finally:
    server.shutdown()
