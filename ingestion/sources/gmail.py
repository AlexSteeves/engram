import os
import base64
import json
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from ingestion.db import upsert_document, get_last_synced, set_last_synced

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
LABEL = "engram"
CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "/app/credentials.json")
TOKEN_PATH = "/app/token.json"


def get_gmail_service():
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def get_body(payload):
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")

    for part in payload.get("parts", []):
        if part["mimeType"] == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    return ""


def sync(conn):
    service = get_gmail_service()
    last_synced = get_last_synced(conn, "gmail")

    query = f"label:{LABEL}"
    if last_synced:
        date_str = last_synced.strftime("%Y/%m/%d")
        query += f" after:{date_str}"

    synced = 0
    page_token = None

    while True:
        kwargs = {"userId": "me", "q": query, "maxResults": 100}
        if page_token:
            kwargs["pageToken"] = page_token

        results = service.users().messages().list(**kwargs).execute()
        messages = results.get("messages", [])

        for msg_ref in messages:
            msg = service.users().messages().get(
                userId="me", id=msg_ref["id"], format="full"
            ).execute()

            headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
            subject = headers.get("Subject", "(no subject)")
            sender = headers.get("From", "unknown")
            date_ms = int(msg["internalDate"])
            created_at = datetime.fromtimestamp(date_ms / 1000, tz=timezone.utc)
            body = get_body(msg["payload"]).strip()

            if not body:
                continue

            upsert_document(
                conn=conn,
                source="gmail",
                source_id=msg["id"],
                title=subject,
                body=body,
                metadata={"sender": sender, "thread_id": msg["threadId"]},
                created_at=created_at,
            )
            synced += 1

        page_token = results.get("nextPageToken")
        if not page_token:
            break

    set_last_synced(conn, "gmail")
    print(f"gmail: synced {synced} emails")
