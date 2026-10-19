# Durham Pack 12 website

**Updating the site? [Open the browser editor](https://forest-newark.github.io/durham-pack-12-site/edit/) and follow the [volunteer guide](UPDATE-THE-SITE.md). No HTML, CSS, JavaScript, or software installation needed.**

Change form fields → download **site.json** → upload it to GitHub’s **content** folder → commit. The website rebuilds and publishes automatically after checks pass. Repository permission is required to publish. The form itself never publishes or asks for credentials.

## What volunteers can update

- Meeting day, time, season, address, and directions (one shared source).
- Contact email addresses, welcome text, headings, activity descriptions, FAQs.
- Events with date pickers, local times, locations, descriptions, and optional links.
- Calendars, parent guides, leader resources, bilingual document links.
- About Cub Scouting content and resource destinations.

All routine changes live in **content/site.json**. The editor writes this file so volunteers need not edit JSON. New documents can be uploaded to **uploads/**. Dates are sorted automatically; past events are retained separately after the next daily rebuild. No upcoming dates are invented.

## Project structure

| Location | Purpose |
| --- | --- |
| content/site.json | Volunteer-managed content |
| uploads/ | New PDFs and images |
| edit/ | Browser form editor |
| UPDATE-THE-SITE.md | Volunteer publishing and troubleshooting guide |
| templates/ | Developer-maintained page layouts |
| styles.css | Site design |
| scripts/content.py | Safe rendering and plain-language validation |
| PhotoBook/ | Original photo routes, images referenced by the build |
| content/source-inventory.json | Original migration inventory |

## Build and preview

Python 3.11+, no third-party packages for validation/rendering/build:

```sh
python scripts/test_content.py
python scripts/build.py
python scripts/check.py
python -m http.server 8000 --directory dist
```

Open http://localhost:8000/ and http://localhost:8000/edit/. For a quick preview with original-host images, run `python scripts/local_preview.py`. To use the form editor, serve that preview with `python -m http.server 8000 --directory preview`; opening an HTML file directly cannot fetch the content files.

Page templates are rendered at build time. The public website still needs no JavaScript for its content, meeting information, dates, or navigation. Only the separate volunteer form editor uses JavaScript. All text is escaped; volunteers enter plain text rather than markup.

## Deployment

Use **Settings → Pages → Source: GitHub Actions**. The single `pages.yml` workflow validates, builds, checks, and deploys **dist/**. The competing raw-repository deployment workflow is removed so it cannot overwrite the rendered site.

Content changes on main rebuild automatically. PRs validate without deploying. A daily 09:17 UTC rebuild updates past/upcoming date classification; GitHub may delay scheduled runs and disables schedules on inactive public repositories after 60 days. A manual run or new content commit also refreshes dates.

Live site: https://forest-newark.github.io/durham-pack-12-site/. The editor will appear at /edit/ after this change is merged and deployed.

## Original functionality

All 15 original images and 7 PDFs are still preserved byte-for-byte, including PDF links. Original photo filenames and previous/next/Home routes remain functional. Superseded documents and contacts remain accessible through a clearly dated **Original resources archive**, while volunteers can publish current information in the main page.

Migration checks no longer require old meeting times, email addresses, or dates to remain on the current homepage. They verify current editable data and original destination availability, preserving exact gallery behavior. Re-auditing the old source site is optional through the manual workflow input; routine content updates do not depend on a fresh crawl of that site.

## Checks

`scripts/test_content.py` tests propagation of meeting/contact edits, event ordering and visibility, historical and empty states, invalid dates/times/URLs, text escaping, and uploaded-document links.

`scripts/check.py` validates generated pages, local destinations, asset hashes, original routes, and current content. Chromium checks at 360/390/768/1440px also exercise the editor: changing fields, adding an event, exporting a file, validating and rendering it, reporting errors, importing it, and restoring a saved draft.

```sh
python -m pip install playwright==1.55.0
python -m playwright install chromium
python scripts/browser_check.py
```

A fresh original-site audit is available with `pip install pypdf==6.1.1` and `python scripts/audit_source.py`. Build artifacts include screenshots and the full static website.

A downloaded update contains the full content snapshot. Start from the current editor before each update and review GitHub’s diff before committing to avoid overwriting another volunteer’s newer work.
