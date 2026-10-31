# JunkeJiang.github.io

A personal academic website for Junke Jiang. The site is based on the [theme-academic-cv theme](https://github.com/HugoBlox/theme-academic-cv) and was published with Hugo Blox Builder.

This repository currently contains the generated static site rather than the Hugo source tree. The main manually edited pages are:

- `index.html` — homepage, research vision, selected publications, and contact.
- `research/index.html` — research themes and future group/lab directions.
- `news/index.html` and `news/*/index.html` — news archive and individual news pages.
- `publication/index.html` — selected publications plus the existing generated publication archive.
- `experience/index.html` — academic CV content adapted from the latest Chinese CV.
- `teaching/index.html` — teaching and future supervision interests.
- `css/profile-polish.css` — site-specific layout and typography refinements layered on top of Hugo Blox.
- `tools/update_academic_site.py` — helper script used to apply the current static-page updates.

If the Hugo source files are restored later, prefer editing the source content and regenerating the site instead of editing the generated HTML directly.

## News Updates

`tools/news.json` stores the reviewed news items in display order. Each item has a stable `slug`, a `title`, the original `date_label`, an optional ISO `date` at the known precision, and `body_html`. Preserve the existing text until the author supplies expanded copy and media. Leave `date` empty for a date range; a month or year is never converted to a fabricated day.

`python3 tools/update_academic_site.py` builds `/news/` and every `/news/<slug>/` detail page using the existing site header and footer, adds News between Research and Publications throughout the site, and registers the pages in the sitemap. The full news list is no longer part of the homepage. Each list item opens its local detail page, which has an archive link and older/newer navigation. New pages do not inherit the template's old CV/article dates or structured metadata.

No placeholder photos, videos, or expanded event accounts are generated. Author-supplied figures, photographs, captions, and video embeds can be added later inside the article content. The scoped news styles constrain future images and videos without changing publication-card styles. Run `python3 -m unittest discover -s tools -p 'test_*.py'` for news and publication regression checks.

## Publication Updates

`tools/publication_metadata_enriched.csv` and `tools/publication_assets_review.csv` are the reviewed sources of truth. Preserve their manually edited values and exclusions. For a new paper, add its approved metadata row, asset row, and internal `publication/<slug>/cite.bib`. The citation file stores full authors and journal details; optional `keywords` (semicolon-separated) and `summary` fields store reviewed tags and an original short description, not a publisher abstract.

Optional `corresponding_authors` and `equal_contributors` fields in the internal citation file contain semicolon-separated full names verified against the publisher. They add `*` and `#` display markers without altering the author names used as metadata, with explanations on the detail page. Omit these fields when roles are unverified. Articles added only to the reviewed archive metadata do not become selected publications or news entries.

Run `python3 tools/update_academic_site.py` to create missing detail pages using the existing Hugo Blox wrapper, refresh the archive and related papers, and synchronize the publication feed and sitemap. The asset CSV is merged without replacing reviewed values or custom columns. Internal citation files are never linked as public downloads.

`tools/enrich_publication_metadata.py` now fills only missing date/URL fields in the reviewed metadata file. It preserves the cleaned record set, existing dates, custom columns, and abstracts, including intentionally blank abstracts. It does not import removed records from the older review CSV.

Run `python3 -m unittest discover -s tools -p 'test_publication_updates.py'` for the publication-generation regression checks.

The October 2026 additions are documented in `tools/publication_profile_review.csv`, including publisher/DOI verification sources and the distinction between online-first and final issue dates. New papers use the neutral fallback thumbnail until an author-supplied or reuse-permitted figure is provided. The 2026 bromide paper links to the author-confirmed parameter repository at https://github.com/JunkeJiang/perov. The 2025 iodide paper retains its separate releases and Zenodo links; the iodide dataset is not attributed to the bromide paper.

`tools/publication_cover_review.csv` records exact issue-cover sources and blocked or unavailable cases. `python3 tools/download_publication_covers.py` (requires Pillow) downloads only entries explicitly marked `verified_issue_cover`, converts them to compact PNGs, and merges their paths and credits into the asset CSV. Existing publication images, including curated alternative paths, are never overwritten. Regenerate the site afterwards. Issue covers are not presented as article-specific artwork; image credits appear on the detail page. Publisher availability is not a reuse license: check the review notes and obtain permission before publishing any cover whose reuse rights remain unverified.

## License
The theme is available as open source under the terms of the [MIT License](https://github.com/alshedivat/al-folio/blob/main/LICENSE).
