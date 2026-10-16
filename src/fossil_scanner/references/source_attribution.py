"""
Source attribution records.

Every reference media asset carries its own license, attribution, and
source. This module makes that obligation explicit and printable.
"""
from typing import Dict, Any, List


def make_attribution(
    media_id: str,
    source_page_url: str,
    institution: str,
    catalog_number: str,
    creator: str,
    license_text: str,
    attribution_text: str,
    retrieved_at: str,
) -> Dict[str, Any]:
    return {
        "media_id": media_id,
        "source_page_url": source_page_url,
        "institution": institution,
        "catalog_number": catalog_number,
        "creator": creator,
        "license": license_text,
        "attribution": attribution_text,
        "retrieved_at": retrieved_at,
    }


def format_attributions(records: List[Dict[str, Any]]) -> str:
    lines = []
    for r in records:
        lines.append(
            f"- {r['attribution']} [{r['license']}] "
            f"source: {r['source_page_url']} "
            f"ref: {r['institution']} {r['catalog_number']}"
        )
    return "\n".join(lines)
