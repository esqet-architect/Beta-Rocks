"""
Reference repository.

Stores taxa, reference specimens, media, and character rules in a SQLite
database. Images and models are kept as files; only their metadata and
checksums live in the database.

The schema is created on first use. Populating the repository is a separate,
reviewed step (see reference_pack_importer.py).
"""
import os
import sqlite3
from typing import Optional, Dict, Any, List

SCHEMA = """
CREATE TABLE IF NOT EXISTS pack_manifest (
    pack_id TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    source TEXT,
    imported_at TEXT,
    checksum TEXT
);

CREATE TABLE IF NOT EXISTS taxa (
    taxon_id TEXT PRIMARY KEY,
    scientific_name TEXT,
    rank TEXT,
    parent_taxon_id TEXT,
    source_system TEXT,
    source_taxon_id TEXT,
    retrieved_at TEXT,
    mapping_review_status TEXT
);

CREATE TABLE IF NOT EXISTS taxon_names (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taxon_id TEXT,
    name TEXT,
    name_type TEXT,
    source TEXT
);

CREATE TABLE IF NOT EXISTS reference_specimens (
    reference_specimen_id TEXT PRIMARY KEY,
    taxon_id TEXT,
    institution TEXT,
    catalog_number TEXT,
    source_page_url TEXT,
    identification_review_status TEXT
);

CREATE TABLE IF NOT EXISTS media (
    media_id TEXT PRIMARY KEY,
    reference_specimen_id TEXT,
    taxon_id TEXT,
    view TEXT,
    scale_mm_per_pixel REAL,
    creator TEXT,
    license TEXT,
    attribution TEXT,
    sha256 TEXT,
    local_path TEXT
);

CREATE TABLE IF NOT EXISTS characters (
    character_id TEXT PRIMARY KEY,
    name TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS taxon_character_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taxon_id TEXT,
    character_id TEXT,
    expected_states TEXT,
    weight REAL,
    diagnostic INTEGER,
    citation TEXT
);
"""


class ReferenceRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)) or ".", exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def install_manifest(self, pack_id: str, version: str, source: str, checksum: str) -> None:
        import time
        self._conn.execute(
            "INSERT OR REPLACE INTO pack_manifest "
            "(pack_id, version, source, imported_at, checksum) "
            "VALUES (?, ?, ?, ?, ?)",
            (pack_id, version, source,
             time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), checksum),
        )
        self._conn.commit()

    def add_taxon(self, taxon: Dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO taxa "
            "(taxon_id, scientific_name, rank, parent_taxon_id, "
            " source_system, source_taxon_id, retrieved_at, mapping_review_status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                taxon["taxon_id"],
                taxon.get("scientific_name"),
                taxon.get("rank"),
                taxon.get("parent_taxon_id"),
                taxon.get("source_system"),
                taxon.get("source_taxon_id"),
                taxon.get("retrieved_at"),
                taxon.get("mapping_review_status"),
            ),
        )
        self._conn.commit()

    def add_character_rule(self, taxon_id: str, rule: Dict[str, Any]) -> None:
        import json
        self._conn.execute(
            "INSERT INTO taxon_character_rules "
            "(taxon_id, character_id, expected_states, weight, diagnostic, citation) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                taxon_id,
                rule["character_id"],
                json.dumps(rule.get("expected_states", [])),
                float(rule.get("weight", 1.0)),
                1 if rule.get("diagnostic") else 0,
                rule.get("citation"),
            ),
        )
        self._conn.commit()

    def get_character_rules(self, taxon_id: str) -> List[Dict[str, Any]]:
        import json
        cur = self._conn.execute(
            "SELECT character_id, expected_states, weight, diagnostic, citation "
            "FROM taxon_character_rules WHERE taxon_id = ?",
            (taxon_id,),
        )
        out = []
        for row in cur:
            out.append({
                "character_id": row["character_id"],
                "expected_states": json.loads(row["expected_states"]),
                "weight": row["weight"],
                "diagnostic": bool(row["diagnostic"]),
                "citation": row["citation"],
            })
        return out

    def list_taxa(self) -> List[Dict[str, Any]]:
        cur = self._conn.execute("SELECT * FROM taxa ORDER BY scientific_name")
        return [dict(row) for row in cur]
