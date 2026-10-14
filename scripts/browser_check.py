"""Render the site at phone, tablet, and desktop sizes; save review screenshots."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright
import os

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "screenshots"
OUTPUT.mkdir(exist_ok=True)
handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT))
server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
Thread(target=server.serve_forever, daemon=True).start()
# Serve from a non-root path to exercise GitHub Pages project-site relative URLs.
base = f"http://127.0.0.1:{server.server_port}/dist/"
errors = []
try:
    with sync_playwright() as playwright:
        options = {"headless": True}
        if os.environ.get("PACK12_CHROME"):
            options["executable_path"] = os.environ["PACK12_CHROME"]
        browser = playwright.chromium.launch(**options)
        for width in (360, 390, 768, 1440):
            page = browser.new_page(viewport={"width": width, "height": 960}, reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))
            response = page.goto(base, wait_until="networkidle")
            assert response.status == 200
            assert page.title() == "Pack 12 Durham · A Pack for All People"
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), f"Overflow at {width}px"
            page.keyboard.press("Tab")
            assert page.locator(".skip-link").evaluate("(el) => el === document.activeElement")
            page.keyboard.press("Enter")
            page.locator('nav a[href="#meetings"]').click()
            assert page.locator("#meetings").is_visible()
            page.locator("details").first.locator("summary").click()
            assert page.locator("details").first.get_attribute("open") is not None
            # Scroll through all lazy images before checking decoding and taking a screenshot.
            for img in page.locator("img").all():
                img.scroll_into_view_if_needed()
                img.evaluate("(el) => el.decode()")
                assert img.evaluate("(el) => el.complete && el.naturalWidth > 0")
            page.locator("details").first.locator("summary").click()
            page.evaluate("window.scrollTo(0, 0)")
            page.screenshot(path=str(OUTPUT / f"pack12-{width}.png"), full_page=True)
            print(f"PASS: {width}px, images, no horizontal overflow, keyboard skip link, navigation, FAQ.")
            page.close()
        assert not errors, errors
        browser.close()
finally:
    server.shutdown()
