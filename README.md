# Durham Pack 12 website

A modern, responsive GitHub Pages proof of concept for Pack 12 in Durham, NC. Plain HTML and CSS; no runtime dependencies, tracking, or JavaScript needed. Keyboard navigation and native expandable FAQs work at all screen sizes.

## Preview locally

Requires Python 3.11 or newer and an internet connection for the initial asset download:

```sh
python scripts/build.py
python scripts/check.py
python -m http.server 8000 --directory dist
```

Open http://localhost:8000 in Chrome. For a single-file preview, open `dist/preview.html` directly in Chrome (that preview loads the original images from pack12durham.org, so it needs internet). The full `dist/index.html` uses the preserved local assets.

## GitHub Pages

1. Merge the proof-of-concept PR into `main`.
2. In repository **Settings → Pages → Build and deployment → Source**, select **GitHub Actions**.
3. Run **Check and deploy Pack 12 Pages** from the Actions tab if the first deployment ran before Pages was enabled.

The expected address is https://forest-newark.github.io/durham-pack-12-site/ once Pages is enabled and deployment succeeds. No custom domain is configured. Relative paths support the repository subpath.

Every PR builds a downloadable `pack12-preview` artifact with the standalone preview, the full site, and mobile/tablet/desktop screenshots. PRs do not deploy. Main pushes deploy only after source and browser checks pass.

## Content and assets

Source: https://pack12durham.org/, inspected October 14, 2026.

The original homepage's content is retained and reorganized: girls and boys grades K–5; “A Pack for All People”; new games, friends, and skills; hiking, archery, camping, s’mores, cooking, family activities, life skills, and character development; September–May meetings on the first three Tuesdays at 6:30 pm; Yates Baptist Church, 2819 Chapel Hill Rd., next to Rogers-Herr Middle School; the September 8 or 15, 2026 welcome dates; both leader email addresses; the original registration PDF and Scouting program link.

The September welcome dates are explicitly historical. The August 2024 registration guide remains available in full, including English and Spanish pages and its embedded destinations; its fees are not presented as current. Families are directed to leaders for current details.

Build downloads preserve these exact original bytes without cropping or modification:

- `pics/ScoutMeIn.png`
- `pics/EstamosListos.png`
- `pics/Pack12Cubs_Color.png`
- `RegistrationInstructions_2024_08_04.pdf`

`dist/asset-sources.json` records the source URL, size, and SHA-256 of each file. Production image and download requests are local to Pages. The original PDF URL, program URL, and email destinations are retained. Directions and a preserved PDF download are additional conveniences. The build fails if an asset cannot be fetched or its format is invalid; it never silently substitutes an image. Preserve a downloaded build artifact if the original site is later retired.

## Visual inspiration

- [Discover Durham](https://www.discoverdurham.com/): expressive headings, generous spacing, and a strong sense of place.
- [Durham Central Park](https://durhamcentralpark.org/): welcoming community feel and clear visitor information.
- [Durham Parks & Recreation](https://www.dprplaymore.org/): practical meeting and location information.
- [Durham Cub Scout Pack 461](https://www.cubpack461.org/): prominent join invitation and grouped outdoor, skills, and friendship benefits.
- [Durham Pack 495](https://www.durhampack495.org/): family focus and scannable quick information.

Original design uses forest green, navy text, warm gold, cream backgrounds, serif headings, and small decorative SVG activity illustrations. Reference-site images and copy are not reused.

## Validation

`scripts/check.py` checks retained content and destinations, local files, unique IDs, anchor destinations, image descriptions, and preservation hashes. To run browser checks:

```sh
python -m pip install playwright==1.55.0
python -m playwright install chromium
python scripts/browser_check.py
```

Chromium checks 360, 390, 768, and 1440 pixel viewports at 2× display density for horizontal overflow, image loading without enlargement beyond native dimensions, mobile text sizes, keyboard skip navigation, menu links, and expandable FAQs, and writes full-page screenshots to `screenshots/`. Reduced-motion preferences are respected. Small-screen body text is at least 16px, navigation has 44px touch targets, welcome graphics stack into one column with full-size links, and decorative badges do not obscure original artwork.

## Editing

Edit `index.html` for content and `styles.css` for layout and color. Before publishing as the pack's official site, confirm meeting details and current registration information with pack leadership.
