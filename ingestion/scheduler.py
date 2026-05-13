import time
import threading
from ingestion.db import get_connection
from ingestion.sources import obsidian, slack, gmail

SYNC_INTERVAL = 3600


def run_all():
    print("sync started")
    conn = get_connection()
    try:
        obsidian.sync(conn)
    except Exception as e:
        print(f"obsidian sync failed: {e}")
    try:
        slack.sync(conn)
    except Exception as e:
        print(f"slack sync failed: {e}")
    try:
        gmail.sync(conn)
    except Exception as e:
        print(f"gmail sync failed: {e}")
    finally:
        conn.close()
    print("sync complete")


def start():
    def loop():
        while True:
            run_all()
            time.sleep(SYNC_INTERVAL)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
