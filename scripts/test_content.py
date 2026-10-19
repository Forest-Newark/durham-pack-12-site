"""Meaningful content-editing regressions, using no network or third-party packages."""
from copy import deepcopy
from datetime import date
from pathlib import Path
import json
import unittest
from content import ContentError, events_html, load_site, render, validate

ROOT = Path(__file__).resolve().parents[1]

class ContentEditingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site = load_site()
        cls.schema = json.loads((ROOT / "content/editor-schema.json").read_text(encoding="utf-8"))
        cls.template = (ROOT / "templates/index.html").read_text(encoding="utf-8")
    def test_meeting_and_contacts_propagate_from_one_place(self):
        site = deepcopy(self.site)
        site["meetings"].update(time="19:15", venue="New meeting place", street="123 New Street", frequency="Every Monday")
        site["contacts"]["cubmaster_email"] = "new@example.org"
        output = render(self.template, site, date(2026, 10, 19))
        self.assertNotIn("6:30 pm", output.split('id="join"')[0])
        self.assertGreaterEqual(output.count("7:15 pm"), 2)
        self.assertIn("New meeting place", output)
        self.assertIn("123 New Street", output)
        self.assertIn("mailto:new@example.org", output)
        self.assertIn("New+meeting+place", output)
        self.assertNotIn("{{", output)
    def test_events_sorted_historical_hidden_and_empty(self):
        site = deepcopy(self.site)
        site["events"] = [
            dict(title="Later",date="2026-12-01",time="18:30",location="Durham",description="Later event",link="",enabled=True),
            dict(title="First",date="2026-11-01",time="09:00",location="Durham",description="First event",link="",enabled=True),
            dict(title="Past",date="2026-09-01",time="18:30",location="Durham",description="Past event",link="",enabled=True),
            dict(title="Hidden",date="2026-11-02",time="18:30",location="Durham",description="Not published",link="",enabled=False),
        ]
        html = events_html(site, date(2026,10,19))
        self.assertLess(html.index(">First<"), html.index(">Later<"))
        self.assertIn("<summary>Past events</summary>", html)
        self.assertNotIn("Hidden", html)
        site["events"] = []
        self.assertIn(site["events_intro"]["empty_message"], events_html(site, date(2026,10,19)))
    def test_real_dates_times_emails_and_safe_urls(self):
        examples = [("events.0.date","2026-02-30"),("meetings.time","25:00"),("contacts.cubmaster_email","not an email"),("registration.online_url","javascript:alert(1)"),("registration.online_url","//example.org"),("registration.online_url","./../secret")]
        for path, value in examples:
            with self.subTest(path=path,value=value):
                site = deepcopy(self.site)
                parent = site
                keys = path.split(".")
                for key in keys[:-1]:
                    parent = parent[int(key)] if isinstance(parent,list) else parent[key]
                parent[keys[-1]] = value
                with self.assertRaises(ContentError):
                    validate(site,self.schema)
    def test_plain_text_cannot_inject_html(self):
        site = deepcopy(self.site)
        site["hero"]["description"] = '<img src=x onerror="alert(1)"> & Friends'
        html = render(self.template, site)
        self.assertNotIn('<img src=x', html)
        self.assertIn('&lt;img src=x', html)
    def test_uploaded_resource_links_and_multiline_copy(self):
        site = deepcopy(self.site)
        site["resources"][0]["links"][0]["url"] = "./uploads/calendar-2027.pdf"
        site["hero"]["heading"] = "Hello\nDurham"
        validate(site,self.schema)
        html = render(self.template,site)
        self.assertIn('href="./uploads/calendar-2027.pdf"',html)
        self.assertIn("Hello<br>Durham",html)

if __name__ == "__main__":
    unittest.main()
