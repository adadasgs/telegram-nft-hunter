import asyncio
import logging
import os
import sqlite3
from datetime import datetime, timezone

import aiohttp
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"),
                    format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("nft-hunter")

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
TARGET_CHAT_ID = os.environ["TARGET_CHAT_ID"]
SOURCE_CHATS = []
for item in os.environ["SOURCE_CHATS"].split(","):
    item = item.strip()
    if item:
        try:
            SOURCE_CHATS.append(int(item))
        except ValueError:
            SOURCE_CHATS.append(item.lstrip("@"))

DB_PATH = os.getenv("DB_PATH", "hunter.sqlite3")


def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("CREATE TABLE IF NOT EXISTS published_users "
                   "(username TEXT PRIMARY KEY, published_at TEXT NOT NULL)")
        db.commit()


def already_published(username):
    with sqlite3.connect(DB_PATH) as db:
        return db.execute("SELECT 1 FROM published_users WHERE username=?",
                          (username.lower(),)).fetchone() is not None


def mark_published(username):
    with sqlite3.connect(DB_PATH) as db:
        db.execute("INSERT OR IGNORE INTO published_users VALUES (?, ?)",
                   (username.lower(), datetime.now(timezone.utc).isoformat()))
        db.commit()


async def has_collectible_gift(client, user):
    """Only accept a collectible gift explicitly returned by Telegram."""
    try:
        result = await client(functions.payments.GetSavedStarGiftsRequest(
            peer=user, offset="", limit=100, exclude_hosted=True
        ))
        return any(
            isinstance(getattr(saved, "gift", None), types.StarGiftUnique)
            for saved in getattr(result, "gifts", [])
        )
    except Exception as exc:
        log.debug("Gift check unavailable for user %s: %s",
                  getattr(user, "id", "?"), exc)
        return False


async def publish_link(http, username):
    endpoint = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with http.post(endpoint, json={
        "chat_id": TARGET_CHAT_ID,
        "text": f"https://t.me/{username}",
        "disable_web_page_preview": False,
    }, timeout=aiohttp.ClientTimeout(total=20)) as response:
        data = await response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram Bot API error: {data}")


async def main():
    if not SOURCE_CHATS:
        raise RuntimeError("SOURCE_CHATS is empty; add source group usernames or IDs")
    init_db()
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        raise RuntimeError("SESSION_STRING is not authorized")
    me = await client.get_me()
    log.info("Connected as Telegram user id=%s; watching %d groups",
             me.id, len(SOURCE_CHATS))

    async with aiohttp.ClientSession() as http:
        @client.on(events.NewMessage(chats=SOURCE_CHATS))
        async def on_new_message(event):
            try:
                sender = await event.get_sender()
                username = getattr(sender, "username", None)
                if not username or already_published(username):
                    return
                if not await has_collectible_gift(client, sender):
                    return
                await publish_link(http, username)
                mark_published(username)
                log.info("Published verified collectible profile @%s", username)
            except Exception:
                log.exception("Message processing failed")

        await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
