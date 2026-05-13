# Engram

Engram is a personal long-term memory system for AI — it ingests your Obsidian notes, Gmail, and Slack into a unified Postgres store and lets Claude query across all of them with a single natural language question.

<!-- demo video -->

## Why this project exists

Every time you start a new conversation with an AI, it starts cold. You can give it MCP connections to Gmail, Slack, and Obsidian — but that only gives it *access*, not *data*. It still has to fetch, parse, and reason through everything from scratch, every session, every time.

Engram solves this with a unified context store. Your data is continuously synced into Postgres. Claude speaks SQL to one place instead of learning N different API shapes. History accumulates. Answers get better over time.

The difference becomes obvious the moment you ask a question that crosses sources — "what have I decided about this architecture?" — and get back a synthesized answer drawn from a note you wrote last week, a Slack message from yesterday, and an email you labeled this morning. That query is impossible with live API connections. With a persistent store, it's one SQL statement.

The other insight: **stateless agents are better agents**. The agent holds no state. The database holds all state. Any instance is identical, restartable, and horizontally scalable. You're not managing session memory or warm/cold agent distinctions — you're just querying a database.

## Why this tech stack

**Python + FastAPI** — FastAPI is async-first and pairs naturally with background sync tasks. The ingestion pipeline, scheduler, and API all live in one container without threading complexity.

**PostgreSQL** — a flat `documents` table with a `source` column and JSONB metadata handles every source shape without schema migrations when you add a new one. SQL is also what Claude writes best — giving it raw database access over a well-described schema produces accurate, auditable queries.

**Docker Compose** — two containers: `postgres` (with a persistent volume) and `app` (FastAPI + scheduler). The app waits for Postgres to pass its healthcheck before starting. One command boots the entire system.

**Two-phase query** — phase one has Claude write SQL and fetch relevant documents. Phase two has Claude read those documents and synthesize an actual answer. This is the difference between a file finder and a knowledge assistant.

**Label/folder filtering** — nothing enters the context store unless you put it there. Gmail emails need the `engram` label. Slack messages need to be in the `#engram` channel. Obsidian notes come from a vault path you configure. You control what Claude remembers.

---

## How to run

### Prerequisites

- Docker Desktop
- An Anthropic API key
- A Slack workspace (with a bot token)
- A Google Cloud project (with Gmail API enabled)

---

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd stateless_rag
```

---

### 2. Configure environment variables

Copy `.env` and fill in your values:

```env
POSTGRES_DB=stateless_rag
POSTGRES_USER=rag_user
POSTGRES_PASSWORD=yourpassword
DATABASE_URL=postgresql://rag_user:yourpassword@postgres:5432/stateless_rag

OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/folder

ANTHROPIC_API_KEY=your-key-here

GMAIL_CREDENTIALS_PATH=/app/credentials.json
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_CHANNEL_ID=your-channel-id
```

---

### 3. Set up Gmail OAuth

Create a Google Cloud project, enable the Gmail API, and download `credentials.json` to the repo root. Then run the one-time auth flow locally:

```bash
pip install google-auth-oauthlib
python -c "
from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_secrets_file('credentials.json', ['https://www.googleapis.com/auth/gmail.readonly'])
creds = flow.run_local_server(port=0)
open('token.json', 'w').write(creds.to_json())
"
```

This saves `token.json` — Docker uses it on every run after that.

In Gmail, create a label called `engram` and apply it to emails you want ingested.

---

### 4. Set up Slack

Create a Slack app at [api.slack.com/apps](https://api.slack.com/apps) with these bot scopes: `channels:history`, `channels:read`, `users:read`. Install it to your workspace and invite the bot to your `#engram` channel.

---

### 5. Start Engram

```bash
docker-compose up --build
```

Open `http://localhost:8000`. On startup, Engram runs an initial sync across all three sources. Hit **refresh data** at any time to pull in new content.

---

## How it works

```
[ Sources ]                  [ Sync ]            [ Store ]           [ Agent ]
Obsidian (vault folder)  →                  →                  →
Gmail (engram label)     →   polling +      →   PostgreSQL     →   Claude (SQL)
Slack (#engram channel)  →   high-water     →   documents      →
                              mark                table
```

Each source runs on a polling loop with a high-water mark — only new content is ingested on each sync. Documents from all sources land in one flat table. Claude gets the schema as context and writes SQL to answer your question. A second Claude call reads the results and synthesizes a natural language answer.

---

## Supported sources

| Source | Filter mechanism | Identifier |
|---|---|---|
| Obsidian | Vault folder path | File path (relative) |
| Gmail | `engram` label | Gmail message ID |
| Slack | `#engram` channel | Message timestamp |
