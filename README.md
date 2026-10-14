# Durham Pack 12 website

A modern, responsive GitHub Pages proof of concept for Pack 12 in Durham, NC. Plain HTML and CSS, with no runtime JavaScript, tracking, or frontend dependencies.

## Local Chrome preview

Requires Python 3.11 or newer and internet for the initial asset download:

```sh
python scripts/build.py
python scripts/check.py
python -m http.server 8000 --directory dist
```

Open http://localhost:8000 in Chrome. For an immediate preview without downloading assets, run `python scripts/local_preview.py` and open `preview/index.html` in Chrome. All modern HTML pages work locally; images and PDFs load from the original host. The full build includes all original images, PDFs, and redesigned photo pages. Open `dist/preview.html` directly for a single-file homepage preview; that file uses original-site images and document destinations and needs internet. Use the full build to review the redesigned photo and resource pages.

## GitHub Pages

1. Merge the proof-of-concept PR into `main`.
2. Set **Settings → Pages → Build and deployment → Source** to **GitHub Actions**.
3. If the first deployment ran before Pages was enabled, run **Check and deploy Pack 12 Pages** from Actions.

Expected address after successful deployment: https://forest-newark.github.io/durham-pack-12-site/. No custom domain is configured. All internal links support the repository subpath.

PRs run validation without deployment. The downloadable `pack12-preview` artifact includes the full build, standalone homepage preview, screenshots, source crawl, and link inventory.

## Full original-site preservation

Source audited October 14, 2026: https://pack12durham.org/.

The audit reads HTML rather than relying on a search engine's text view. That captures the original CSS-rendered navigation as well as ordinary links. The complete reachable site includes the homepage, About Cub Scouting, and 12 photo viewer pages. Both original hostnames and the home/index.html aliases are checked.

- Homepage content, meeting information, email addresses, registration PDF, and Scouting program destination are retained.
- Calendar: `pics/Calendar_2026_08_19.pdf`.
- Den leader help: `pics/DenLeaderHelp2026_08_28.pdf`.
- Parent information: `pics/PIP_EN_2026_08_23.pdf` and `pics/PIP_ES_2026_08_23.pdf`.
- FAQs: `pics/FAQ_EN_2026_08_24.pdf` and `pics/FAQ_ES_2026_08_24.pdf`.
- About Cub Scouting retains all three original external resource links, including the exact leader-book URL.
- All 12 photo viewer routes keep their original `PhotoBook/pf*.html` filenames, original photographs, Home links, and original previous/next destinations. A new album overview provides direct access to every photo. Original navigation quirks are retained rather than silently changing their destinations.
- All 15 original images and 7 original PDFs are downloaded unchanged. PDFs retain their complete content, embedded links, and bilingual pages.
- The online registration destination found inside the original PDF is also surfaced as a direct homepage link.

September 8 and 15, 2026 welcome dates are explicitly historical. The registration guide is dated August 2024, so families are directed to leaders for current costs and instructions. The current resource documents retain their original 2026 publication dates. Older, search-indexed 2024 FAQs and the 2025–2026 calendar are not substituted for the current live navigation documents.

`content/source-inventory.json` records the discovered source pages and destinations. The build creates `asset-sources.json` with source URLs, sizes, and SHA-256 hashes. `link-coverage.json` maps every original page link/image to its migrated route.

## Visual inspiration and readability

References: [Discover Durham](https://www.discoverdurham.com/), [Durham Central Park](https://durhamcentralpark.org/), [Durham Parks & Recreation](https://www.dprplaymore.org/), [Durham Cub Scout Pack 461](https://www.cubpack461.org/), and [Durham Pack 495](https://www.durhampack495.org/).

The original design uses forest green, navy text, warm gold, cream backgrounds, serif headings, and vector illustrations. No reference-site photographs or copy are reused.

Small-screen body text is at least 16px. Navigation has 44px touch targets. Graphics stack vertically and can open at full size. Raster images are never stretched past native dimensions. The “Do Your Best” badge is a large, unrotated SVG with vector lettering. Keyboard skip links, native expandable FAQs, and reduced-motion support are included.

## Validation

`scripts/audit_source.py` crawls the full reachable original navigation, image links, frames, and linked PDFs. It preserves downloaded source bytes, extracts PDF destinations, and records HTTP availability and redirects for external links. A provider that blocks automated requests is reported rather than silently replaced. CI fails on source-fetch issues rather than silently omitting them.

`scripts/check.py` verifies every local link, anchor, legacy page route, original image, original per-page destination, and asset hash. It compares the implementation with both the tracked inventory and a fresh source crawl, so future source additions are caught.

For the full audit and browser checks:

```sh
python -m pip install pypdf==6.1.1 playwright==1.55.0
python scripts/audit_source.py
python scripts/build.py
python scripts/check.py
python -m playwright install chromium
python scripts/browser_check.py
```

Chromium checks phone, tablet, and desktop viewports at 2× display density for horizontal overflow, native-size image rendering, readable text, keyboard navigation, resource downloads, and photo navigation. Screenshots are written to `screenshots/`.

External links keep their original destinations. Login, registration submissions, and authenticated Scout services remain with their original providers; no credentials or registrations are submitted by the checks.

## Editing

Edit `index.html`, `aboutCubScouting.html`, and `PhotoBook/*.html` for content, and `styles.css` for layout. Rebuild to refresh the original asset copies. Preserve a build artifact if the original site is later retired.
