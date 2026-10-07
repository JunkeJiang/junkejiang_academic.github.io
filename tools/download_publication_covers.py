"""Download only manually verified official issue previews; never overwrite images."""

import csv
import io
import re
import ssl
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "tools/publication_cover_review.csv"
ASSETS = ROOT / "tools/publication_assets_review.csv"
METADATA = ROOT / "tools/publication_metadata_enriched.csv"
OFFICIAL_IMAGE_HOSTS = {"blogs.rsc.org", "pubs.rsc.org", "pubs.acs.org", "aipp.silverchair-cdn.com", "ars.els-cdn.com"}


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames), list(reader)


def main():
    fields, assets = read_rows(ASSETS)
    _, reviews = read_rows(REVIEW)
    _, metadata = read_rows(METADATA)
    by_slug = {row["slug"]: row for row in assets}
    if len(by_slug) != len(assets) or set(by_slug) != {row["slug"] for row in metadata}:
        raise ValueError("Reviewed metadata and asset slugs must match without duplicates")
    updated = 0
    for review in reviews:
        if review["review_status"] != "verified_issue_cover":
            continue
        slug = review["slug"]
        if slug not in by_slug or not re.fullmatch(r"[a-z0-9-]+", slug):
            raise ValueError(f"Unapproved publication slug: {slug}")
        target = ROOT / "media/publications" / slug / "publication-thumbnail.png"
        row = by_slug[slug]
        if target.exists():
            print(f"Preserved existing image: {slug}")
            continue
        # Respect a curated alternative path as well as the conventional PNG path.
        existing = ROOT / row["thumbnail_path"].lstrip("/")
        if row["thumbnail_status"] == "real" and existing.is_file():
            print(f"Preserved alternative curated image: {slug}")
            continue
        source = urlsplit(review["cover_url"])
        if source.scheme != "https" or source.hostname not in OFFICIAL_IMAGE_HOSTS:
            raise ValueError(f"Not an approved official image host: {source.hostname}")
        tls = ssl.create_default_context()
        # macOS framework Python may not include the system CA bundle by default.
        system_ca = Path("/etc/ssl/cert.pem")
        if system_ca.is_file():
            tls.load_verify_locations(cafile=str(system_ca))
        with urlopen(review["cover_url"], timeout=25, context=tls) as response:
            if not response.headers.get_content_type().startswith("image/"):
                raise ValueError(f"Not an image response for {slug}")
            payload = response.read(5_000_001)
        if len(payload) > 5_000_000:
            raise ValueError(f"Cover exceeds the preview download limit: {slug}")
        with Image.open(io.BytesIO(payload)) as original:
            original.load()
            image = original.convert("RGB")
        image.thumbnail((600, 900))
        encoded = io.BytesIO()
        image.save(encoded, format="PNG", optimize=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write(encoded.getvalue())
        row.update(
            thumbnail_path="/" + target.relative_to(ROOT).as_posix(),
            thumbnail_status="real",
            image_type="journal_cover",
            manual_action="Issue cover only; replace later with article artwork if desired. Confirm reuse permission before public deployment.",
            image_source_url=review["issue_url"],
            image_credit=review["image_credit"],
        )
        updated += 1
        print(f"Added verified issue preview: {slug} ({image.width} x {image.height})")
    if updated:
        fields.extend(field for field in ("image_source_url", "image_credit") if field not in fields)
        with ASSETS.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(assets)
    print(f"New covers: {updated}; existing images are never overwritten.")


if __name__ == "__main__":
    main()
