# stateless_rag — build log

## Status: design phase

## Decisions locked
- Architecture: unified Postgres context store, stateless agent
- Use case: read-heavy (Obsidian vault, Gmail, Slack → long-term recall)
- Writes: out of scope for now — add MCP action layer later if needed
- Why: access ≠ data; every MCP session starts cold; SQL beats N API shapes
- Sync: polling with high-water mark, unified scheduler owns all three sources
- Schema: flat documents table (Option A) — use case is retrieval, not source correlation
- Query interface: raw SQL — Claude connects directly to Postgres
- Language: Python
- Infra: Docker, two containers (postgres + app)
- Frontend: plain HTML/JS served by FastAPI, no framework
- API: FastAPI — POST /query, POST /sync
- Scheduler runs as background thread inside app container

## Completed
1. docker-compose.yml + Dockerfile
2. db/schema.sql + db/migrate.py
3. ingestion/db.py
4. agent/query.py
5. api/main.py
6. frontend/index.html
7. ingestion/sources/obsidian.py
8. ingestion/scheduler.py
9. ingestion/sources/slack.py

## Roadmap
### Gmail ingestion
- Create `ingestion/sources/gmail.py`
- Label filter: only ingest emails tagged `engram` in Gmail
- OAuth2 setup: Google Cloud project, credentials.json, gmail readonly scope
- High-water mark on received date

### Phase 2 reasoning
- Two-phase query in `agent/query.py`
- Phase 1: Claude writes SQL, fetch relevant rows
- Phase 2: Claude reads those rows and synthesizes an actual answer
- Currently Claude only returns raw rows — this makes it actually answer questions

### Polish
- Remove SQL from status bar (debug only, not user-facing)
- Add "sources" label above document cards

### GitHub + README
- ✅ git init and push to new repo
- ✅ Write README
- README is too long — needs to be more concise
- Create Canva diagrams to replace text-heavy explanations (architecture flow, why access ≠ data)
- Record demo video: one question, three sources, one synthesized answer
- Embed video in README

### LinkedIn post
- Draft post around the cross-source query demo
- Link to GitHub repo

## Open questions
- Gmail + Slack OAuth credentials (needed before those sources can be built)
- Sync interval (hardcoded for now, configurable later)

## Session log
### 2026-05-13
- Project scoped: unified Postgres intermediary for multi-source LLM queries
- All architecture decisions locked
- Full stack built and running: Docker, Postgres, FastAPI, Obsidian ingestion, Claude SQL agent, frontend
- End-to-end query proven: natural language → Claude SQL → Postgres → results
- High-water mark working correctly across both sources
- Slack ingestion working: 3 messages synced from #engram channel
- Cross-source query proven: one question returned results from both Obsidian and Slack
- Sync switched from background thread to foreground for reliability
- Next: Gmail ingestion, phase 2 reasoning (synthesize results, not just return rows)
