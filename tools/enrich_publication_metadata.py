#!/usr/bin/env python3
"""Build derived publication metadata from the reviewed local CSV.

The input file, ``publication_date_review.csv``, remains the hand-reviewed
source for which generated publication pages should stay in the archive. This
helper adds DOI/Crossref date metadata where available and appends a few
curated DFTB resource records that are intentionally retained even though they
are not in the cleaned CSV.

Run from the repository root:

    python3 tools/enrich_publication_metadata.py
"""

from __future__ import annotations

import csv
import html
import json
import re
import ssl
import time
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CSV = ROOT / "tools" / "publication_date_review.csv"
OUTPUT_CSV = ROOT / "tools" / "publication_metadata_enriched.csv"

GITHUB_RELEASES = "https://github.com/dftbparams/perov/releases"
ZENODO_RECORD = "https://zenodo.org/records/14778741"

CURATED_EXTRA_ROWS = [
    {
        "slug": "jiang-2025-flexible",
        "title": "Flexible and efficient semiempirical DFTB parameters for electronic structure prediction of 3D, 2D iodide perovskites and heterostructures",
        "displayed_publication_year": "2025",
        "doi_found_in_page": "https://doi.org/10.1103/PhysRevMaterials.9.023803",
        "status": "Curated DFTB parameter paper retained for data/parameter links.",
    },
    {
        "slug": "jiang-2024-flexible",
        "title": "Flexible and Efficient Semi-Empirical DFTB methods for Electronic Structure Prediction of 3D, 2D Perovskites and Heterostructures",
        "displayed_publication_year": "2024",
        "doi_found_in_page": "",
        "status": "Curated DFTB conference record retained for data/parameter context; exact date requires manual confirmation.",
    },
    {
        "slug": "jiang-2023-flexible",
        "title": "Flexible and Efficient Semi-Empirical DFTB methods for Electronic Structure Prediction of 3D, 2D and 3D/2D Halide Perovskites",
        "displayed_publication_year": "2023",
        "doi_found_in_page": "",
        "status": "Curated DFTB conference record retained for data/parameter context; exact date requires manual confirmation.",
    },
    {
        "slug": "thebaud-2024-extending",
        "title": "Extending tight-binding models from bulk to layered halide perovskites",
        "displayed_publication_year": "2024",
        "doi_found_in_page": "",
        "status": "Curated tight-binding conference record retained for data/parameter context; exact date requires manual confirmation.",
    },
    {
        "slug": "selected-duan-2026-photostability",
        "title": "Structure and device-operando photostability of quasi-2D Ruddlesden-Popper perovskites: engineering the spacer cation matters",
        "displayed_publication_year": "2026",
        "doi_found_in_page": "https://doi.org/10.1021/acsenergylett.5c03228",
        "status": "Curated selected publication without a generated detail page.",
    },
    {
        "slug": "selected-geng-2025-bidentate",
        "title": "Bidentate pyridine passivators attaching trifluoromethyl substitute groups in varied positions for efficient carbon-based perovskite solar cells",
        "displayed_publication_year": "2025",
        "doi_found_in_page": "https://doi.org/10.1021/acsami.5c18690",
        "status": "Curated selected publication without a generated detail page.",
    },
]

OFFICIAL_OVERRIDES = {
    "https://doi.org/10.1103/physrevmaterials.9.023803": {
        "publication_date": "2025-02-21",
        "date_precision": "day",
        "date_source": "Official APS article page",
        "official_url": "https://journals.aps.org/prmaterials/abstract/10.1103/PhysRevMaterials.9.023803",
    }
}

OUTPUT_FIELDS = [
    "slug",
    "title",
    "displayed_publication_year",
    "doi_found_in_page",
    "status",
    "official_url",
    "publication_date",
    "date_precision",
    "date_source",
    "abstract",
    "metadata_checked_at",
]


def normalize_doi(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if value.lower().startswith("https://doi.org/"):
        return "https://doi.org/" + value.split("doi.org/", 1)[1]
    if value.lower().startswith("http://doi.org/"):
        return "https://doi.org/" + value.split("doi.org/", 1)[1]
    if value.lower().startswith(("http://", "https://")):
        return value
    if value.lower().startswith("doi:"):
        value = value[4:]
    return "https://doi.org/" + value.strip()


def doi_key(value: str) -> str:
    return normalize_doi(value).lower()


def is_doi_url(value: str) -> bool:
    return normalize_doi(value).lower().startswith("https://doi.org/")


def strip_abstract(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def date_from_parts(parts: list[int]) -> tuple[str, str]:
    if len(parts) >= 3:
        return f"{parts[0]:04d}-{parts[1]:02d}-{parts[2]:02d}", "day"
    if len(parts) == 2:
        return f"{parts[0]:04d}-{parts[1]:02d}", "month"
    if len(parts) == 1:
        return f"{parts[0]:04d}", "year"
    return "", ""


def best_crossref_date(message: dict) -> tuple[str, str, str]:
    priorities = ["published-online", "published-print", "published", "issued"]
    partial: tuple[str, str, str] = ("", "", "")
    for key in priorities:
        date_parts = message.get(key, {}).get("date-parts", [])
        if not date_parts or not date_parts[0]:
            continue
        iso, precision = date_from_parts([int(x) for x in date_parts[0]])
        if precision == "day":
            return iso, precision, f"Crossref {key}"
        if not partial:
            partial = (iso, precision, f"Crossref {key}")
    return partial


def fetch_crossref(doi_url: str) -> dict:
    doi = normalize_doi(doi_url).split("doi.org/", 1)[1]
    url = f"https://api.crossref.org/works/{quote(doi, safe='')}"
    request = Request(url, headers={"User-Agent": "junkejiang-academic-site-metadata/1.0 (mailto:junke.jiang@york.ac.uk)"})
    cafile = "/etc/ssl/cert.pem" if Path("/etc/ssl/cert.pem").exists() else None
    context = ssl.create_default_context(cafile=cafile)
    with urlopen(request, timeout=20, context=context) as response:
        return json.loads(response.read().decode("utf-8"))


def enrich_row(row: dict[str, str]) -> dict[str, str]:
    out = {field: row.get(field, "") for field in OUTPUT_FIELDS}
    out["doi_found_in_page"] = normalize_doi(out["doi_found_in_page"])
    out["metadata_checked_at"] = date.today().isoformat()
    out["official_url"] = out["doi_found_in_page"]
    out["publication_date"] = out.get("displayed_publication_year", "")
    out["date_precision"] = "year" if out["publication_date"] else ""
    out["date_source"] = "Reviewed local CSV year" if out["publication_date"] else ""

    override = OFFICIAL_OVERRIDES.get(doi_key(out["doi_found_in_page"]))
    if override:
        out.update(override)
        return out

    if not out["doi_found_in_page"]:
        return out

    if not is_doi_url(out["doi_found_in_page"]):
        out["official_url"] = out["doi_found_in_page"]
        return out

    try:
        payload = fetch_crossref(out["doi_found_in_page"])
        message = payload.get("message", {})
        official_url = message.get("URL") or out["doi_found_in_page"]
        pub_date, precision, source = best_crossref_date(message)
        if pub_date:
            out["publication_date"] = pub_date
            out["date_precision"] = precision
            out["date_source"] = source
        out["official_url"] = official_url
        out["abstract"] = strip_abstract(message.get("abstract", ""))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
        out["status"] = f"{out.get('status', '').strip()} Crossref enrichment failed: {exc}".strip()
    time.sleep(0.12)
    return out


def main() -> None:
    if not SOURCE_CSV.exists():
        raise SystemExit(f"Missing input CSV: {SOURCE_CSV}")
    rows = list(csv.DictReader(SOURCE_CSV.open(encoding="utf-8-sig")))
    seen = {row["slug"] for row in rows}
    for row in CURATED_EXTRA_ROWS:
        if row["slug"] not in seen:
            rows.append(row)
            seen.add(row["slug"])

    enriched = [enrich_row(row) for row in rows]
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(enriched)
    print(f"Wrote {len(enriched)} rows to {OUTPUT_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
