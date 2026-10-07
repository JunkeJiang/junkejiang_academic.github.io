"""Focused checks for reviewed publication data and repeatable page generation."""

import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import enrich_publication_metadata as enrichment
import update_academic_site as site


class PublicationUpdateTests(unittest.TestCase):
    def test_asset_merge_preserves_reviewed_fields_and_custom_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "assets.csv"
            reviewed = {
                "slug": "reviewed-paper",
                "title": "Reviewed title",
                "thumbnail_path": "/media/manually-curated.png",
                "thumbnail_status": "real",
                "topic": "Reviewed topic",
                "image_type": "journal_cover",
                "manual_action": "Keep this cover",
                "source_url": "https://example.org/verified-image",
            }
            with path.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(reviewed))
                writer.writeheader()
                writer.writerow(reviewed)
            records = [{"slug": "new-paper", "title": "New paper"}, {"slug": "reviewed-paper", "title": "Derived title"}]
            with patch.object(site, "PUBLICATION_ASSETS_REVIEW_CSV", path):
                site.write_publication_assets_review(records)
                first = path.read_bytes()
                with path.open(newline="") as handle:
                    rows = list(csv.DictReader(handle))
                self.assertEqual(rows[0], reviewed)
                self.assertEqual(rows[1]["thumbnail_status"], "fallback")
                site.write_publication_assets_review(records)
                self.assertEqual(path.read_bytes(), first)

    def test_enrichment_preserves_cleaned_records_dates_and_empty_abstracts(self):
        with tempfile.TemporaryDirectory() as directory:
            reviewed_path = Path(directory) / "reviewed.csv"
            old_source = Path(directory) / "old.csv"
            row = dict.fromkeys(enrichment.OUTPUT_FIELDS, "")
            row.update(slug="reviewed-paper", title="Manual title", publication_date="2026-09-02", date_precision="day", date_source="Manual verified date", official_url="https://example.org/article", custom_field="Preserve me")
            with reviewed_path.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(row))
                writer.writeheader()
                writer.writerow(row)
            old_source.write_text("slug,title\nremoved-paper,Old record\n")
            before = reviewed_path.read_bytes()
            with patch.object(enrichment, "OUTPUT_CSV", reviewed_path), patch.object(enrichment, "SOURCE_CSV", old_source), patch.object(enrichment, "enrich_row") as fetch:
                enrichment.main()
                fetch.assert_not_called()
            self.assertEqual(reviewed_path.read_bytes(), before)

    def test_archive_does_not_import_stale_citation_folders(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            metadata = root / "metadata.csv"
            metadata.write_text("slug,title,displayed_publication_year\nreviewed-paper,Reviewed paper,2026\n")
            for slug in ("reviewed-paper", "removed-paper"):
                folder = root / "publication" / slug
                folder.mkdir(parents=True)
                (folder / "cite.bib").write_text("@article{test, title = {Paper}, author = {Jiang, Junke}, journal = {Journal}, year = {2026}}")
            with patch.object(site, "ROOT", root), patch.object(site, "PUBLICATION_METADATA_CSV", metadata), patch.object(site, "PUBLICATION_ASSETS_REVIEW_CSV", root / "assets.csv"):
                records = site.archive_items()
            self.assertEqual([record["slug"] for record in records], ["reviewed-paper"])

    def test_archive_orders_by_recorded_dates_instead_of_titles(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            metadata = root / "metadata.csv"
            papers = [
                ("chang-2026-thickness", "Z May paper", "15/05/2026"),
                ("jiang-2026-constructing", "B July paper", "14/07/2026"),
                ("dai-2026-all-perovskite", "A September paper", "02/09/2026"),
                ("chang-2026-exploiting", "C August paper", "2026-08-26"),
            ]
            with metadata.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["slug", "title", "displayed_publication_year", "publication_date", "date_precision"])
                writer.writeheader()
                for slug, title, date in papers:
                    writer.writerow(dict(slug=slug, title=title, displayed_publication_year="2026", publication_date=date, date_precision="day"))
                    folder = root / "publication" / slug
                    folder.mkdir(parents=True)
                    (folder / "cite.bib").write_text("@article{paper, journal = {Journal}, year = {2026}}")
            with patch.object(site, "ROOT", root), patch.object(site, "PUBLICATION_METADATA_CSV", metadata), patch.object(site, "PUBLICATION_ASSETS_REVIEW_CSV", root / "assets.csv"):
                records = site.archive_items()
            self.assertEqual([record["slug"] for record in records], ["dai-2026-all-perovskite", "chang-2026-exploiting", "jiang-2026-constructing", "chang-2026-thickness"])

    def test_sort_key_preserves_partial_date_precision(self):
        record = {"year": "2027", "publication_date": "2027", "date_precision": "year"}
        self.assertEqual(site.publication_sort_key(record)[:3], (2027, 0, 0))
        record.update(publication_date="2027-02", date_precision="month")
        self.assertEqual(site.publication_sort_key(record)[:3], (2027, 2, 0))
        record.update(publication_date="2027-02-31", date_precision="day")
        self.assertEqual(site.publication_sort_key(record)[:3], (2027, 0, 0))
        record.update(publication_date="01/01/2027", date_precision="day")
        self.assertEqual(site.publication_sort_key(record)[:3], (2027, 1, 1))

    def test_year_groups_follow_dates_and_accept_future_years(self):
        records = [
            {"year": "2026", "publication_date": "2025-12-24", "date_precision": "day"},
            {"year": "2021", "publication_date": "2021", "date_precision": "year"},
            {"year": "2027", "publication_date": "2027-01-03", "date_precision": "day"},
        ]
        groups = site.grouped_by_year(records)
        self.assertEqual(list(groups), ["2027", "2025", "2021 and before"])
        self.assertEqual(groups["2025"][0]["year"], "2026")

    def test_all_doi_papers_omit_duplicate_publisher_buttons_by_default(self):
        for slug in ("dai-2026-all-perovskite", "jiang-2025-flexible", "future-paper-not-in-any-allowlist"):
            record = {"slug": slug, "doi": "https://doi.org/10.1234/example", "official_url": "https://publisher.example/article"}
            links = site.publication_detail_top_links(record)
            self.assertIn(record["doi"], links)
            self.assertNotIn("Article Page", links)
            self.assertNotIn(record["official_url"], links)
            self.assertEqual(record["official_url"], "https://publisher.example/article")
        thesis = {"slug": "jiang-2021-stabilizing", "official_url": "https://repository.example/thesis.pdf"}
        self.assertIn(thesis["official_url"], site.publication_detail_top_links(thesis))
        self.assertEqual(site.publication_primary_links(thesis), [("Thesis PDF", thesis["official_url"])])

    def test_legacy_article_page_cleanup_handles_case_and_nested_markup(self):
        original = '<a href="https://publisher.example/article"><span>ARTICLE</span>&nbsp;\nPAGE</a><a href="https://doi.org/10.1234/example">DOI</a><p>Article Page source metadata</p>'
        cleaned = site.remove_article_page_buttons(original)
        self.assertNotIn("https://publisher.example/article", cleaned)
        self.assertIn('href="https://doi.org/10.1234/example"', cleaned)
        self.assertIn("Article Page source metadata", cleaned)
        self.assertEqual(site.remove_article_page_buttons(cleaned), cleaned)

    def test_resource_buttons_drop_stale_article_page_but_keep_other_resources(self):
        record = {
            "href": "/publication/paper/",
            "links": [("DOI", "https://doi.org/10.1234/example"), ("ARTICLE PAGE", "https://publisher.example/article"), ("DFTB Parameters", "https://github.com/JunkeJiang/perov"), ("PDF", "/uploads/paper.pdf")],
        }
        links = site.publication_links_html(record)
        self.assertNotIn("https://publisher.example/article", links)
        for label in ("Details", "DOI", "DFTB Parameters", "PDF"):
            self.assertIn(f'>{label}</a>', links)

    def test_archive_keeps_source_urls_without_article_page_buttons(self):
        for record in site.archive_items():
            with self.subTest(slug=record["slug"]):
                self.assertNotIn("Article Page", site.publication_links_html(record))
                if record.get("doi"):
                    self.assertEqual(site.publication_primary_links(record), [("DOI", record["doi"])])

    def test_enrichment_removes_existing_article_page_buttons_without_slug_allowlist(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "publication" / "future-paper"
            folder.mkdir(parents=True)
            page = folder / "index.html"
            page.write_text('<main><a class="hb-attachment-link" href="https://publisher.example/article">Article Page</a><time></time></main>')
            record = {"slug": folder.name, "title": "Paper", "topic": "Electronic Structure", "links": [("DOI", "https://doi.org/10.1234/example")]}
            with patch.object(site, "ROOT", root), patch.object(site, "publication_records", return_value=[record]):
                site.enrich_publication_detail_pages()
                first = page.read_bytes()
                site.enrich_publication_detail_pages()
            self.assertNotIn("Article Page", page.read_text())
            self.assertIn("https://doi.org/10.1234/example", page.read_text())
            self.assertEqual(page.read_bytes(), first)

    def test_missing_page_is_created_even_when_citation_file_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "publication" / "new-paper"
            folder.mkdir(parents=True)
            (folder / "cite.bib").write_text("@article{new-paper}")
            record = {"slug": "new-paper", "title": "New paper", "year": "2026"}
            with patch.object(site, "ROOT", root), patch.object(site, "publication_records", return_value=[record]), patch.object(site, "make_page_from_template") as template, patch.object(site, "read", return_value="<title>New paper</title>"), patch.object(site, "write"):
                site.ensure_publication_detail_pages()
            self.assertEqual(template.call_count, 1)
            self.assertEqual(template.call_args.args[0], "publication/xi-2023-mechanism/index.html")
            self.assertEqual(template.call_args.args[1], "publication/new-paper/index.html")

    def test_summary_is_not_mislabeled_as_a_full_abstract(self):
        self.assertIn(">Summary</h2>", site.abstract_block({"curated_summary": "Reviewed summary."}))
        block = site.abstract_block({"abstract": "Verified abstract.", "curated_summary": "Reviewed summary."})
        self.assertIn(">Abstract</h2>", block)
        self.assertNotIn("Reviewed summary", block)
        self.assertEqual(site.abstract_block({}), "")

    def test_feed_does_not_invent_day_precision(self):
        record = {"slug": "paper", "href": "/publication/paper/", "title": "Paper", "year": "2026", "publication_date": "2026", "date_precision": "year"}
        self.assertNotIn("pubDate", site.publication_feed_item(record))
        record.update(publication_date="2026-09-02", date_precision="day")
        self.assertIn("Wed, 02 Sep 2026", site.publication_feed_item(record))

    def test_parameter_resources_are_paper_specific(self):
        bromide = site.dftb_resource_links({"slug": "jiang-2026-constructing", "tags": ["DFTB"]})
        self.assertEqual(bromide, [("DFTB Parameters", "https://github.com/JunkeJiang/perov")])
        self.assertNotIn(site.DFTB_ZENODO_RECORD, [url for _, url in bromide])
        self.assertEqual(len(site.dftb_resource_links({"slug": "jiang-2025-flexible"})), 2)
        self.assertEqual(site.dftb_resource_links({"slug": "unrelated-paper", "tags": ["DFTB"]}), [])

    def test_dftb_tags_match_between_selected_and_archive_records(self):
        expected = {
            "jiang-2025-flexible": ["DFTB", "Method Development", "2D Perovskites", "Iodide Perovskite", "Interfaces"],
            "jiang-2026-constructing": ["DFTB", "Method Development", "Bromide Perovskites", "Electronic Structure", "Low-Dimensional Perovskites"],
        }
        for records in (site.archive_items(), site.selected_publication_records()):
            by_slug = {record["slug"]: record for record in records}
            for slug, tags in expected.items():
                self.assertEqual(by_slug[slug]["tags"], tags)
                self.assertEqual(by_slug[slug]["topic"], "DFTB and Method Development")

    def test_specific_perovskite_tags_link_to_existing_topic_sections(self):
        tags = {"Iodide Perovskite": "Metal-Halide Perovskites", "Bromide Perovskites": "Metal-Halide Perovskites", "Low-Dimensional Perovskites": "2D and Layered Perovskites"}
        for tag, topic in tags.items():
            self.assertEqual(site.TAG_TO_TOPIC[tag], topic)
            cloud = site.tag_cloud_html([{"tags": [tag]}])
            self.assertIn(f'href="#topic-{site.anchor_id(topic)}"', cloud)

    def test_method_recommendations_require_method_tags(self):
        records = [
            {"slug": "optical-paper", "year": "2027", "tags": ["Perovskites", "Electronic Structure"]},
            {"slug": "older-method", "year": "2025", "tags": ["Method Development"]},
            {"slug": "newer-dftb", "year": "2026", "tags": ["DFTB", "Bromide Perovskites"]},
            {"slug": "jiang-2021-stabilizing", "year": "2021", "tags": ["DFTB"]},
        ]
        self.assertEqual([record["slug"] for record in site.method_development_publications(records)], ["newer-dftb", "older-method"])
        self.assertEqual(site.method_development_publications(records, limit=0), [])
        self.assertEqual(site.method_development_publications(records[:1]), [])

    def test_archive_method_block_omits_nano_letters_but_archive_keeps_it(self):
        body = site.publication_body()
        related = body.split('<section id="related-publications"', 1)[1].split('</section>', 1)[0]
        archive = body.split('<section id="publication-archive"', 1)[1]
        self.assertNotIn("dai-2026-all-perovskite", related)
        self.assertIn("dai-2026-all-perovskite", archive)
        self.assertIn('href="/publication/jiang-2026-constructing/"', related)
        self.assertIn('href="/publication/jiang-2025-flexible/"', related)
        self.assertEqual(related.count('<article class="jp-pub-card"'), 2)

    def test_issue_cover_credit_is_preserved_and_escaped(self):
        record = {"slug": "paper", "title": "Paper", "topic": "Electronic Structure", "year": "2025"}
        asset = {"thumbnail_path": "/media/cover.png", "thumbnail_status": "real", "image_type": "journal_cover", "image_credit": "Issue cover & publisher credit", "image_source_url": "https://example.org/gallery?year=2025&issue=32"}
        with patch.object(Path, "exists", return_value=True):
            site.apply_manual_thumbnail(record, {"paper": asset})
        block = site.publication_detail_enrichment_block(record)
        self.assertIn("Issue cover &amp; publisher credit", block)
        self.assertIn("year=2025&amp;issue=32", block)
        self.assertIn('data-image-type="journal_cover"', block)
        self.assertNotIn("<span>EL</span>", block)

    def test_home_news_links_to_the_bromide_paper(self):
        home = site.home_body()
        news = home.split('id="news"', 1)[1].split('</section>', 1)[0]
        self.assertEqual(news.count('href="/publication/jiang-2026-constructing/"'), 1)
        self.assertIn("July 2026", news)
        self.assertIn("The Journal of Chemical Physics", news)

    def test_bromide_paper_replaces_nano_letters_only_in_selected_publications(self):
        dois = [paper["doi"] for paper in site.SELECTED_PUBLICATIONS]
        self.assertEqual(dois[0], "https://doi.org/10.1063/5.0324424")
        self.assertNotIn("https://doi.org/10.1021/acs.nanolett.6c03508", dois)
        home = site.home_body()
        selected = home.split('id="papers"', 1)[1].split('</section>', 1)[0]
        news = home.split('id="news"', 1)[1].split('</section>', 1)[0]
        self.assertIn("lead-bromide perovskites", selected)
        self.assertNotIn("Nano Letters", selected)
        self.assertIn('href="/publication/dai-2026-all-perovskite/"', news)

    def test_home_news_includes_verified_conference_and_school_entries(self):
        news = site.home_body().split('id="news"', 1)[1].split('</section>', 1)[0]
        self.assertEqual(news.count("<li>"), 8)
        self.assertIn('href="https://chasam.materialsmodeling.org/"', news)
        self.assertIn("28 September - 2 October", news)
        self.assertIn("neuroevolution potentials (NEP)", news)
        self.assertIn("machine-learning interatomic potentials (MLIPs)", news)
        self.assertIn('href="https://www.sc.stfc.ac.uk/events/mcc-conference-2026/"', news)
        self.assertIn("Presented my research", news)
        self.assertIn("STFC Daresbury Laboratory", news)
        self.assertIn("1-3 July 2026", news)


if __name__ == "__main__":
    unittest.main()
