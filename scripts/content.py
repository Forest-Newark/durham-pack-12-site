"""Validate volunteer content and render templates. No third-party dependencies."""
from datetime import date, datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import urlsplit, urlencode
import json
import re

ROOT = Path(__file__).resolve().parents[1]

class ContentError(ValueError):
    pass

def validate(value, rule, path="Website"):
    expected = rule["type"]
    types = {"object": dict, "array": list, "string": str, "boolean": bool}
    if not isinstance(value, types[expected]):
        raise ContentError(f"{path}: expected {expected}. Please use the website editor to download a fresh site.json.")
    if expected == "object":
        missing = [key for key in rule.get("required", []) if key not in value]
        if missing:
            raise ContentError(f"{path}: missing {', '.join(missing)}.")
        unknown = set(value) - set(rule["properties"])
        if unknown:
            raise ContentError(f"{path}: unknown field {', '.join(sorted(unknown))}.")
        for key, item in value.items():
            validate(item, rule["properties"][key], path + " → " + key.replace("_", " "))
    elif expected == "array":
        if len(value) < rule.get("minItems", 0) or len(value) > rule.get("maxItems", 500):
            raise ContentError(f"{path}: this section needs {rule.get('minItems', 0)}–{rule.get('maxItems', 500)} entries.")
        for i, item in enumerate(value, 1):
            validate(item, rule["items"], f"{path} → entry {i}")
    elif expected == "string":
        if len(value.strip()) < rule.get("minLength", 0):
            raise ContentError(f"{path}: please fill in this field.")
        if len(value) > rule.get("maxLength", 10000):
            raise ContentError(f"{path}: text is too long.")
        if rule.get("enum") and value not in rule["enum"]:
            raise ContentError(f"{path}: choose one of {', '.join(rule['enum'])}.")
        kind = rule.get("format")
        if kind == "date":
            try:
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                    raise ValueError()
                date.fromisoformat(value)
            except ValueError:
                raise ContentError(f"{path}: choose a real date, such as 2026-11-03.") from None
        if kind == "time":
            try:
                if not re.fullmatch(r"\d{2}:\d{2}", value):
                    raise ValueError()
                datetime.strptime(value, "%H:%M")
            except ValueError:
                raise ContentError(f"{path}: use a time such as 18:30 (6:30 pm).") from None
        if kind == "email" and (not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value) or any(ch in value for ch in '<>"')):
            raise ContentError(f"{path}: enter a valid email address.")
        if kind == "link" and value:
            part = urlsplit(value)
            if part.scheme:
                if part.scheme not in ("https", "http") or not part.netloc or any(ch.isspace() for ch in value):
                    raise ContentError(f"{path}: use a full https:// link.")
            elif not value.startswith("./") or ".." in part.path.split("/") or "\\" in value:
                raise ContentError(f"{path}: use https://... or ./uploads/filename.pdf.")
            if any(ch in value for ch in '<>"'):
                raise ContentError(f"{path}: the link contains an invalid character.")

def load_site(root=ROOT):
    try:
        site = json.loads((root / "content/site.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ContentError(f"content/site.json, line {error.lineno}: invalid formatting. Use the website editor to download site.json again.") from None
    schema = json.loads((root / "content/editor-schema.json").read_text(encoding="utf-8"))
    validate(site, schema)
    seen = set()
    for item in site["events"]:
        key = (item["title"].strip().lower(), item["date"])
        if key in seen:
            raise ContentError(f"Events: '{item['title']}' appears twice on {item['date']}. Remove the duplicate.")
        seen.add(key)
    return site

def time_label(value):
    hour, minute = map(int, value.split(":"))
    return f"{hour % 12 or 12}:{minute:02d} {'am' if hour < 12 else 'pm'}"

def paragraphs(value):
    return escape(value).replace("\n", "<br>")

def resources_html(rows, about=False):
    cards = []
    for row in rows:
        if about:
            links = [{"label": row["label"], "url": row["url"], "language": "en"}]
            heading = "h2"
            label = ""
        else:
            links, heading = row["links"], "h3"
            label = '<span class="card-number">' + escape(row["label"]) + '</span>'
        rendered_links = []
        for item in links:
            badge = "PDF ↗" if urlsplit(item["url"]).path.lower().endswith(".pdf") else "↗"
            rendered_links.append(f'<a class="resource-link" lang="{escape(item.get("language", "en"))}" href="{escape(item["url"], quote=True)}">{escape(item["label"])} <span>{badge}</span></a>')
        cards.append(f'<article class="resource-card">{label}<{heading}>{escape(row["title"])}</{heading}><p>{paragraphs(row["description"])}</p>{"".join(rendered_links)}</article>')
    return "".join(cards)

def events_html(site, today=None):
    # A daily Pages build updates this date classification; dates are local calendar dates.
    today = today or datetime.now(timezone.utc).date()
    events = sorted((item for item in site["events"] if item["enabled"]), key=lambda item: (item["date"], item["time"], item["title"]))
    future = [item for item in events if date.fromisoformat(item["date"]) >= today]
    past = [item for item in events if date.fromisoformat(item["date"]) < today]
    def card(item):
        day = date.fromisoformat(item["date"])
        label = f"{day.strftime('%A, %B')} {day.day}, {day.year}"
        link = f'<a class="text-link" href="{escape(item["link"], quote=True)}">Event details ↗</a>' if item["link"] else ""
        return f'<article class="resource-card event-card"><h3>{escape(item["title"])}</h3><p><time datetime="{item["date"]}">{label}</time> · {time_label(item["time"])}</p><p>{escape(item["location"])}</p><p>{paragraphs(item["description"])}</p>{link}</article>'
    result = '<div class="resource-grid upcoming-events">' + "".join(map(card, future)) + "</div>" if future else '<p class="event-empty">' + escape(site["events_intro"]["empty_message"]) + '</p>'
    if past:
        result += '<details class="past-events"><summary>Past events</summary><div class="resource-grid">' + "".join(map(card, reversed(past))) + '</div></details>'
    return result

def render(template, site, today=None):
    computed = {
        "meeting_time": time_label(site["meetings"]["time"]),
        "directions_url": "https://www.google.com/maps/search/?" + urlencode({"api": "1", "query": ", ".join(site["meetings"][key] for key in ("venue", "street", "city"))}),
    }
    blocks = {
        "events": events_html(site, today),
        "resources": resources_html(site["resources"]),
        "about_resources": resources_html(site["about"]["resources"], about=True),
        "faqs": "".join('<details><summary>' + escape(item["question"]) + '</summary><p>' + paragraphs(item["answer"]) + '</p></details>' for item in site["faqs"]),
    }
    def replace(match):
        token = match.group(1).strip()
        if token.startswith("html:"):
            return blocks[token[5:]]
        lines = token.startswith("lines:")
        if lines:
            token = token[6:]
        if token in computed:
            value = computed[token]
        else:
            value = site
            for key in token.split("."):
                value = value[int(key)] if isinstance(value, list) else value[key]
        return paragraphs(str(value)) if lines else escape(str(value), quote=True)
    return re.sub(r"{{\s*(.*?)\s*}}", replace, template)

def render_pages(root=ROOT, today=None):
    site = load_site(root)
    return {path.name: render(path.read_text(encoding="utf-8"), site, today)
            for path in sorted((root / "templates").glob("*.html"))}

def archive_html(root=ROOT):
    inventory = json.loads((root / "content/source-inventory.json").read_text(encoding="utf-8"))
    urls = {}
    for item in inventory["links"]:
        if item["tag"] in ("a", "area"):
            urls.setdefault(item["url"], item["label"] or urlsplit(item["url"]).path.rsplit("/", 1)[-1])
    def href(url):
        part = urlsplit(url)
        if part.hostname in ("pack12durham.org", "www.pack12durham.org"):
            return "./" + (part.path.lstrip("/") or "index.html") + ("?" + part.query if part.query else "") + ("#" + part.fragment if part.fragment else "")
        return url
    items = "".join(f'<li><a href="{escape(href(url), quote=True)}">{escape(label or url)}</a></li>' for url, label in sorted(urls.items()))
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Original resources archive · Pack 12</title><link rel="stylesheet" href="./styles.css"></head><body><main class="container section"><h1>Original resources archive</h1><p>Historical destinations from the original site, audited October 14, 2026. For current contacts, dates, and resources, use the main website.</p><p><a href="./index.html">Current Pack 12 website →</a></p><ul>' + items + '</ul></main></body></html>'
