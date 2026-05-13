import os
from datetime import datetime, timezone
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from ingestion.db import upsert_document, get_last_synced, set_last_synced

CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")


def sync(conn):
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    last_synced = get_last_synced(conn, "slack")
    oldest = str(last_synced.timestamp()) if last_synced else None

    try:
        user_cache = {}
        synced = 0
        cursor = None

        while True:
            kwargs = {"channel": CHANNEL_ID, "limit": 200}
            if oldest:
                kwargs["oldest"] = oldest
            if cursor:
                kwargs["cursor"] = cursor

            response = client.conversations_history(**kwargs)
            messages = response.get("messages", [])

            for msg in messages:
                if msg.get("subtype"):
                    continue

                user_id = msg.get("user", "unknown")
                if user_id not in user_cache:
                    try:
                        info = client.users_info(user=user_id)
                        user_cache[user_id] = info["user"]["real_name"]
                    except SlackApiError:
                        user_cache[user_id] = user_id

                ts = float(msg["ts"])
                created_at = datetime.fromtimestamp(ts, tz=timezone.utc)
                body = msg.get("text", "").strip()

                if not body:
                    continue

                upsert_document(
                    conn=conn,
                    source="slack",
                    source_id=msg["ts"],
                    title=None,
                    body=body,
                    metadata={"user": user_cache[user_id], "channel": CHANNEL_ID},
                    created_at=created_at,
                )
                synced += 1

            if not response.get("has_more"):
                break
            cursor = response["response_metadata"]["next_cursor"]

    except SlackApiError as e:
        print(f"slack api error: {e.response['error']}")

    set_last_synced(conn, "slack")
    print(f"slack: synced {synced} messages")
