from __future__ import annotations
import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = Path(__file__).parent.parent / "data.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS properties (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            address TEXT,
            phone_number TEXT,
            email_address TEXT,
            management_company TEXT,
            property_url TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS inquiries (
            id TEXT PRIMARY KEY,
            property_id TEXT NOT NULL REFERENCES properties(id),
            type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            content TEXT,
            response TEXT,
            result_json TEXT,
            retell_call_id TEXT,
            sent_at TEXT,
            replied_at TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_properties_status ON properties(status);
        CREATE INDEX IF NOT EXISTS idx_inquiries_property ON inquiries(property_id);

        CREATE TABLE IF NOT EXISTS conversation_blocks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'question',
            content TEXT NOT NULL,
            description TEXT,
            is_system INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS conversation_templates (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS template_blocks (
            template_id TEXT NOT NULL REFERENCES conversation_templates(id) ON DELETE CASCADE,
            block_id TEXT NOT NULL REFERENCES conversation_blocks(id) ON DELETE CASCADE,
            sort_order INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (template_id, block_id)
        );
    """)
    conn.commit()

    # ALTER TABLE: add template_id to properties (idempotent)
    try:
        conn.execute("ALTER TABLE properties ADD COLUMN template_id TEXT")
        conn.commit()
    except Exception:
        pass

    conn.close()


# ── Config ──

def get_config(key: str) -> Optional[str]:
    conn = _get_conn()
    row = conn.execute("SELECT value FROM config WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else None


def set_config(key: str, value: str):
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
        (key, value),
    )
    conn.commit()
    conn.close()


# ── Properties ──

def create_property(data: dict) -> dict:
    now = datetime.now().isoformat()
    prop_id = str(uuid.uuid4())
    conn = _get_conn()
    conn.execute(
        """INSERT INTO properties (id, name, address, phone_number, email_address,
           management_company, property_url, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            prop_id,
            data["name"],
            data.get("address"),
            data.get("phone_number"),
            data.get("email_address"),
            data.get("management_company"),
            data.get("property_url"),
            data.get("status", "pending"),
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()
    return get_property(prop_id)


def get_property(prop_id: str) -> Optional[dict]:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM properties WHERE id = ?", (prop_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_properties(status: Optional[str] = None) -> List[dict]:
    conn = _get_conn()
    if status:
        rows = conn.execute(
            "SELECT * FROM properties WHERE status = ? ORDER BY created_at DESC",
            (status,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM properties ORDER BY created_at DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_property(prop_id: str, data: dict) -> Optional[dict]:
    data["updated_at"] = datetime.now().isoformat()
    sets = ", ".join(f"{k} = ?" for k in data)
    vals = list(data.values()) + [prop_id]
    conn = _get_conn()
    conn.execute(f"UPDATE properties SET {sets} WHERE id = ?", vals)
    conn.commit()
    conn.close()
    return get_property(prop_id)


def delete_property(prop_id: str):
    conn = _get_conn()
    conn.execute("DELETE FROM inquiries WHERE property_id = ?", (prop_id,))
    conn.execute("DELETE FROM properties WHERE id = ?", (prop_id,))
    conn.commit()
    conn.close()


# ── Inquiries ──

def create_inquiry(data: dict) -> dict:
    inq_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    conn = _get_conn()
    conn.execute(
        """INSERT INTO inquiries (id, property_id, type, status, content, response,
           result_json, retell_call_id, sent_at, replied_at, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            inq_id,
            data["property_id"],
            data["type"],
            data.get("status", "pending"),
            data.get("content"),
            data.get("response"),
            json.dumps(data.get("result_json"), ensure_ascii=False) if data.get("result_json") else None,
            data.get("retell_call_id"),
            data.get("sent_at"),
            data.get("replied_at"),
            now,
        ),
    )
    conn.commit()
    conn.close()
    conn2 = _get_conn()
    row = conn2.execute("SELECT * FROM inquiries WHERE id = ?", (inq_id,)).fetchone()
    conn2.close()
    return dict(row) if row else {}


def get_inquiries(property_id: Optional[str] = None) -> List[dict]:
    conn = _get_conn()
    if property_id:
        rows = conn.execute(
            "SELECT * FROM inquiries WHERE property_id = ? ORDER BY created_at DESC",
            (property_id,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM inquiries ORDER BY created_at DESC").fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        if d.get("result_json"):
            d["result_json"] = json.loads(d["result_json"])
        result.append(d)
    return result


def update_inquiry(inq_id: str, data: dict) -> Optional[dict]:
    if "result_json" in data and isinstance(data["result_json"], dict):
        data["result_json"] = json.dumps(data["result_json"], ensure_ascii=False)
    sets = ", ".join(f"{k} = ?" for k in data)
    vals = list(data.values()) + [inq_id]
    conn = _get_conn()
    conn.execute(f"UPDATE inquiries SET {sets} WHERE id = ?", vals)
    conn.commit()
    conn.close()
    conn2 = _get_conn()
    row = conn2.execute("SELECT * FROM inquiries WHERE id = ?", (inq_id,)).fetchone()
    conn2.close()
    d = dict(row) if row else None
    if d and d.get("result_json"):
        d["result_json"] = json.loads(d["result_json"])
    return d
