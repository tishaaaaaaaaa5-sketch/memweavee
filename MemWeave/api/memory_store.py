"""Isolated private workspace storage for the MemWeave web application.

This is a transparent lexical retrieval baseline, not the learned research selector.
"""
from __future__ import annotations
import hashlib, re, secrets, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "memweave_app.sqlite3"

def connect(db_path=DEFAULT_DB):
    path = Path(db_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db

def initialize(db_path=DEFAULT_DB):
    with connect(db_path) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS workspaces (
          id TEXT PRIMARY KEY, key_hash TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS memories (
          id TEXT PRIMARY KEY,
          workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
          content TEXT NOT NULL, source TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS memories_workspace_created
          ON memories(workspace_id, created_at DESC);
        """)

def create_workspace(db_path=DEFAULT_DB):
    initialize(db_path)
    workspace_id, key = uuid.uuid4().hex, secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc).isoformat()
    with connect(db_path) as db:
        db.execute("INSERT INTO workspaces VALUES(?,?,?)",
                   (workspace_id, hashlib.sha256(key.encode()).hexdigest(), now))
    return {"workspace_id": workspace_id, "workspace_key": key, "created_at": now}

def authenticate(workspace_id, key, db_path=DEFAULT_DB):
    if not workspace_id or not key:
        return False
    with connect(db_path) as db:
        row = db.execute("SELECT key_hash FROM workspaces WHERE id=?", (workspace_id,)).fetchone()
    if row is None:
        return False
    return secrets.compare_digest(hashlib.sha256(key.encode()).hexdigest(), row["key_hash"])

def add_memory(workspace_id, content, source="manual", db_path=DEFAULT_DB):
    item = {"id": uuid.uuid4().hex, "content": content, "source": source,
            "created_at": datetime.now(timezone.utc).isoformat()}
    with connect(db_path) as db:
        db.execute("INSERT INTO memories VALUES(?,?,?,?,?)",
                   (item["id"], workspace_id, content, source, item["created_at"]))
    return item

def list_memories(workspace_id, limit=100, db_path=DEFAULT_DB):
    with connect(db_path) as db:
        rows = db.execute(
            "SELECT id,content,source,created_at FROM memories WHERE workspace_id=? ORDER BY created_at DESC LIMIT ?",
            (workspace_id, limit)).fetchall()
    return [dict(row) for row in rows]

def delete_memory(workspace_id, memory_id, db_path=DEFAULT_DB):
    with connect(db_path) as db:
        cur = db.execute("DELETE FROM memories WHERE workspace_id=? AND id=?", (workspace_id, memory_id))
    return cur.rowcount > 0

def retrieve(workspace_id, query, limit=5, db_path=DEFAULT_DB):
    """Rank notes by fraction of query terms found; no model or embeddings are used."""
    terms = set(re.findall(r"[a-z0-9_]{2,}", query.casefold()))
    if not terms:
        return []
    ranked = []
    for item in list_memories(workspace_id, limit=1000, db_path=db_path):
        words = set(re.findall(r"[a-z0-9_]{2,}", item["content"].casefold()))
        matched = terms & words
        if matched:
            ranked.append({**item, "score": round(len(matched) / len(terms), 4),
                           "matched_terms": sorted(matched)})
    ranked.sort(key=lambda x: (x["score"], x["created_at"]), reverse=True)
    return ranked[:limit]
