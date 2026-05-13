import os
import anthropic
from ingestion.db import get_connection

SCHEMA_CONTEXT = """
You have access to a PostgreSQL database with the following table:

documents (
    id          SERIAL PRIMARY KEY,
    source      TEXT NOT NULL,          -- 'obsidian', 'gmail', or 'slack'
    source_id   TEXT NOT NULL,
    title       TEXT,
    body        TEXT NOT NULL,
    metadata    JSONB,                  -- source-specific fields
    created_at  TIMESTAMPTZ,            -- when the document was created in the source
    ingested_at TIMESTAMPTZ             -- when it was pulled into this database
)

Write a single read-only SQL SELECT query to answer the user's question.
Return only the raw SQL with no explanation, no markdown, no code fences.
"""

SYNTHESIS_CONTEXT = """
You are a personal knowledge assistant. The user asked a question and the following documents were retrieved from their personal context store (Obsidian notes, emails, Slack messages).

Read the documents and answer the user's question directly and concisely.
Cite which source each insight came from (obsidian, gmail, or slack).
If the documents don't contain enough information to answer, say so.
"""


def fetch_documents(question: str) -> dict:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    sql_response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": f"{SCHEMA_CONTEXT}\n\nQuestion: {question}"}
        ],
    )
    sql = sql_response.content[0].text.strip()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    col_names = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()

    results = [dict(zip(col_names, row)) for row in rows]
    return {"sql": sql, "results": results}


def synthesize_answer(question: str, results: list) -> str:
    if not results:
        return "No relevant documents found."

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    docs_text = ""
    for r in results:
        docs_text += f"\n---\nSource: {r.get('source')}\nTitle: {r.get('title', 'untitled')}\n{r.get('body', '')}\n"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"{SYNTHESIS_CONTEXT}\n\nQuestion: {question}\n\nDocuments:\n{docs_text}"
            }
        ],
    )
    return response.content[0].text.strip()
