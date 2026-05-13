CREATE TABLE IF NOT EXISTS documents (
    id          SERIAL PRIMARY KEY,
    source      TEXT NOT NULL,
    source_id   TEXT NOT NULL,
    title       TEXT,
    body        TEXT NOT NULL,
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ,
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (source, source_id)
);

CREATE TABLE IF NOT EXISTS sync_state (
    source          TEXT PRIMARY KEY,
    last_synced_at  TIMESTAMPTZ
);
