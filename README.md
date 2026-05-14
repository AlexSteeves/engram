# Engram

Personal long-term memory for AI. Sync your Obsidian notes, Gmail, and Slack into Postgres. Ask Claude questions across all three.

https://github.com/user-attachments/assets/8f7d919b-d77b-4cb8-8e58-c857bb740c5b

Apply the engram label in Gmail, post to #engram in Slack, or drop a note in your Obsidian folder. Engram ingests all three.

<table>
  <tr>
    <td align="center"><img src="assets/gmail.png" width="100%" /><br/><sub>Gmail — engram label</sub></td>
    <td align="center"><img src="assets/slack.png" width="100%" /><br/><sub>Slack — #engram channel</sub></td>
    <td align="center"><img src="assets/obsidian_note.png" width="100%" /><br/><sub>Obsidian — vault folder</sub></td>
  </tr>
</table>

## The problem

MCP connections give Claude access to your data. They don't give it memory. Every session starts from scratch — Claude fetches, parses, and reasons through the same sources again. Token cost compounds. Context resets.

![access vs data](assets/vs_diagram.png)

Engram syncs your data into Postgres once. Claude queries SQL instead of hitting live APIs. Ask "what did I decide about this last month?" and get back a synthesized answer pulled from a note, a Slack message, and a labeled email — in one shot.

The agent holds no state. Postgres holds all state. Restart it, scale it, run multiple instances — the data stays.

![architecture flow](assets/architecture_flow.png)

## Stack

**Python + FastAPI** — ingestion pipeline, scheduler, and API in one container.

**PostgreSQL** — flat `documents` table, `source` column, JSONB metadata. Add a new source without touching the schema.

**Docker Compose** — two containers. One command starts everything.

**Two-phase query** — Claude writes SQL and fetches rows (phase 1), then reads those rows and writes an answer (phase 2). Not a file finder.

**You control what enters** — Gmail needs the `engram` label. Slack needs the `#engram` channel. Obsidian reads from a folder you set. Nothing gets in unless you put it there.

---

## Setup

### Prerequisites

- Docker Desktop
- Anthropic API key
- Slack bot token
- Google Cloud project with Gmail API enabled

---

### 1. Clone

```bash
git clone <your-repo-url>
cd stateless_rag
```

### 2. Configure `.env`

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

### 3. Gmail OAuth (one-time)

Download `credentials.json` from your Google Cloud project to the repo root. Run:

```bash
pip install google-auth-oauthlib
python -c "
from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_secrets_file('credentials.json', ['https://www.googleapis.com/auth/gmail.readonly'])
creds = flow.run_local_server(port=0)
open('token.json', 'w').write(creds.to_json())
"
```

Approve access in the browser. `token.json` gets saved. Docker uses it from here.

In Gmail, create a label called `engram` and apply it to emails you want ingested.

### 4. Slack

Create a Slack app at [api.slack.com/apps](https://api.slack.com/apps). Add bot scopes: `channels:history`, `channels:read`, `users:read`. Install to your workspace. Invite the bot to `#engram`.

### 5. Run

```bash
docker-compose up --build
```

Open `http://localhost:8000`. Engram syncs on startup. Hit **refresh data** to pull new content.

---

## Sources

| Source   | Filter            | Unique ID          |
| -------- | ----------------- | ------------------ |
| Obsidian | Vault folder path | Relative file path |
| Gmail    | `engram` label    | Gmail message ID   |
| Slack    | `#engram` channel | Message timestamp  |
