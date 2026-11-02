"""Checks for the independent news archive, detail pages, and shared navigation."""

import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

import update_academic_site as site


class NewsUpdateTests(unittest.TestCase):
    def test_news_is_between_research_and_publications(self):
        self.assertEqual([label for label, _ in site.NAV_ITEMS], ["Home", "Research", "News", "Publications", "CV", "Teaching", "Contact"])
        for path in ("news/index.html", "news/chasam-school-2026/index.html"):
            self.assertTrue(site.active_for(path, "/news/"))
            self.assertIn('class="nav-link active" href=/news/>News</a>', site.nav_html(path))
            self.assertFalse(site.active_for(path, "/"))
        self.assertFalse(site.active_for("publication/index.html", "/news/"))

    def test_home_no_longer_contains_the_news_section(self):
        home = site.home_body()
        self.assertNotIn('id="news"', home)
        self.assertNotIn("CHASAM 2026", home)
        for content in ('id="papers"', 'id="contact"', "Research Directions"):
            self.assertIn(content, home)

    def test_each_archive_row_is_one_clickable_local_story(self):
        records = site.news_records()
        body = site.news_body()
        self.assertEqual(len({record["slug"] for record in records}), 8)
        self.assertEqual(body.count('<article class="jp-news-row">'), len(records))
        for record in records:
            self.assertEqual(body.count(f'href="/news/{record["slug"]}/"'), 1)
            self.assertIn(f'id="news-title-{record["slug"]}"', body)
            self.assertIn(record["date_label"], body)
        self.assertNotIn('href="/publication/', body)

    def test_story_rows_do_not_contain_nested_links(self):
        class LinkParser(HTMLParser):
            depth = 0
            nested = False

            def handle_starttag(self, tag, attrs):
                if tag == "a":
                    self.nested = self.nested or self.depth > 0
                    self.depth += 1

            def handle_endtag(self, tag):
                if tag == "a":
                    self.depth -= 1

        parser = LinkParser()
        parser.feed(site.news_body())
        self.assertFalse(parser.nested)
        self.assertEqual(parser.depth, 0)

    def test_detail_pages_keep_original_copy_and_previous_next_links(self):
        records = site.news_records()
        for index, record in enumerate(records):
            body = site.news_detail_body(record, records)
            self.assertIn(record["body_html"], body)
            self.assertIn('href="/news/"', body)
            if index > 0:
                self.assertIn(f'href="/news/{records[index - 1]["slug"]}/"', body)
            if index + 1 < len(records):
                self.assertIn(f'href="/news/{records[index + 1]["slug"]}/"', body)
            self.assertEqual("Newer news" in body, index > 0)
            self.assertEqual("Older news" in body, index + 1 < len(records))

    def test_dates_keep_month_year_and_range_precision(self):
        records = site.news_records()
        self.assertEqual(site.news_date_html(records[0]), '<time datetime="2026-10">October 2026</time>')
        self.assertEqual(site.news_date_html(records[5]), '<time datetime="2026">2026</time>')
        self.assertEqual(site.news_date_html(records[-1]), '<span>2024-2025</span>')
        for record in records:
            self.assertNotIn("-01-01", site.news_date_html(record))

    def test_plain_text_preview_preserves_link_and_emphasis_spacing(self):
        self.assertEqual(site.news_plain_text('<p>Published in <em>Nano Letters</em>.</p><p>Read <a href="/">more</a>.</p>'), "Published in Nano Letters. Read more.")

    def test_figures_and_captions_do_not_change_archive_excerpts(self):
        body = '<p>Original news.</p><figure><a href="/photo.jpg"><img src="/photo.jpg" alt="Photo"></a><figcaption>Photo caption.</figcaption></figure><p>Another paragraph.</p>'
        self.assertEqual(site.news_plain_text(body), "Original news. Another paragraph.")
        caption = "CHASAM 2026 group photograph."
        records = site.news_records()
        item = next(record for record in records if record["slug"] == "chasam-school-2026")
        self.assertIn(caption, site.news_detail_body(item, records))
        self.assertNotIn(caption, site.news_body())

    def test_invalid_or_duplicate_records_fail_before_writing_pages(self):
        item = {"slug": "valid-news", "title": "Title", "date_label": "2026", "date": "2026", "body_html": "<p>News.</p>"}
        cases = [[item, item], [{**item, "slug": "../outside"}], [{**item, "date": "2026-13"}], [{**item, "body_html": ""}]]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "news.json"
            with patch.object(site, "NEWS_DATA_JSON", path):
                for records in cases:
                    with self.subTest(records=records):
                        path.write_text(json.dumps(records))
                        with self.assertRaises(ValueError):
                            site.news_records()

    def test_news_metadata_removes_inherited_cv_dates_and_article_schema(self):
        source = '<head><meta property="article:published_time" content="2025-06-06T00:00:00Z"><meta property="article:modified_time" content="2025-06-06T00:00:00Z"><meta property="og:updated_time" content="2026-05-03"><script type=application/ld+json>{"@type":"ScholarlyArticle"}</script></head>'
        for record in [None] + site.news_records():
            output = site.news_page_metadata(source, record)
            self.assertNotIn("2025-06-06", output)
            self.assertNotIn("2026-05-03", output)
            self.assertNotIn("ScholarlyArticle", output)
            self.assertNotIn("datePublished", output)
            self.assertIn('"@type":"BlogPosting"' if record else '"@type":"CollectionPage"', output)
            self.assertEqual(site.news_page_metadata(output, record), output)

    def test_news_generation_reuses_header_footer_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            template = root / "experience/index.html"
            template.parent.mkdir()
            template.write_text('<html><head><title>CV</title><meta name=description content="CV"><link rel=canonical href=https://junkejiang.com/experience/></head><body><header>' + site.nav_html("experience/index.html") + '</header><div class=page-body>Old CV</div><div class=page-footer>Shared footer</div></body></html>')
            with patch.object(site, "ROOT", root):
                site.generate_news_pages()
                first = {path: path.read_bytes() for path in (root / "news").rglob("index.html")}
                self.assertEqual(len(first), 9)
                for path in first:
                    text = path.read_text()
                    self.assertIn("Shared footer", text)
                    self.assertIn('class="nav-link active" href=/news/>News</a>', text)
                    self.assertIn(site.PROFILE_STYLESHEET, text)
                    self.assertIn('href=https://junkejiang.com/' + path.parent.relative_to(root).as_posix() + '/', text)
                    self.assertNotIn("Old CV", text)
                site.generate_news_pages()
                self.assertEqual(first, {path: path.read_bytes() for path in first})

    def test_news_sitemap_additions_preserve_existing_entries_without_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sitemap = root / "sitemap.xml"
            original = '<url><loc>https://junkejiang.com/</loc><lastmod>2026-05-03</lastmod></url>'
            sitemap.write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + original + '</urlset>')
            with patch.object(site, "ROOT", root):
                site.sync_news_sitemap_entries()
                first = sitemap.read_bytes()
                site.sync_news_sitemap_entries()
            self.assertEqual(sitemap.read_bytes(), first)
            self.assertIn(original, sitemap.read_text())
            document = ET.fromstring(sitemap.read_text())
            urls = [item.text for item in document.findall("{*}url/{*}loc")]
            self.assertEqual(len(urls), 10)
            self.assertEqual(len(set(urls)), len(urls))

    def test_news_photos_only_appear_in_the_assigned_stories(self):
        class ImageParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.images = []

            def handle_starttag(self, tag, attrs):
                if tag == "img":
                    self.images.append(dict(attrs))

        expected = {
            "chasam-school-2026": ("/media/news/chasam-school-2026/group-photo.jpg", "1600", "1200"),
            "university-of-york-2026": ("/media/news/university-of-york-2026/lakeside-view.jpg", "1919", "1080"),
        }
        records = site.news_records()
        self.assertNotIn("<img", site.news_body())
        for record in records:
            body = site.news_detail_body(record, records)
            parser = ImageParser()
            parser.feed(body)
            with self.subTest(slug=record["slug"]):
                if record["slug"] in expected:
                    self.assertEqual(len(parser.images), 1)
                    image = parser.images[0]
                    self.assertEqual((image["src"], image["width"], image["height"]), expected[record["slug"]])
                    self.assertTrue(image["alt"])
                    self.assertEqual(image["loading"], "lazy")
                    self.assertTrue((site.ROOT / image["src"].lstrip("/")).is_file())
                else:
                    self.assertEqual(parser.images, [])
            for tag in ("<video", "<iframe"):
                self.assertNotIn(tag, body)


if __name__ == "__main__":
    unittest.main()
