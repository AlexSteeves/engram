import os
import re
from pathlib import Path
from datetime import datetime, timezone
from ingestion.db import upsert_document, get_last_synced, set_last_synced

VAULT_PATH = Path("/vault")


def extract_tags(body: str) -> list[str]:
    return re.findall(r"#([\w/]+)", body)


def sync(conn):
    last_synced = get_last_synced(conn, "obsidian")

    synced = 0
    for md_file in VAULT_PATH.rglob("*.md"):
        mtime = datetime.fromtimestamp(md_file.stat().st_mtime, tz=timezone.utc)

        if last_synced and mtime <= last_synced:
            continue

        body = md_file.read_text(encoding="utf-8", errors="ignore")
        if not body.strip():
            continue

        title = md_file.stem
        tags = extract_tags(body)
        created_at = datetime.fromtimestamp(md_file.stat().st_ctime, tz=timezone.utc)

        upsert_document(
            conn=conn,
            source="obsidian",
            source_id=str(md_file.relative_to(VAULT_PATH)),
            title=title,
            body=body,
            metadata={"tags": tags, "path": str(md_file.relative_to(VAULT_PATH))},
            created_at=created_at,
        )
        synced += 1

    set_last_synced(conn, "obsidian")
    print(f"obsidian: synced {synced} files")
