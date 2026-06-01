import asyncio
import logging
from datetime import datetime, timedelta

from telegram import Bot
from telegram.error import Forbidden, TelegramError

import database as db
from cat_api import fetch_random_kitten

logger = logging.getLogger(__name__)

INTERVALS: dict[str, timedelta] = {
    "4x_day":       timedelta(hours=6),
    "3x_day":       timedelta(hours=8),
    "2x_day":       timedelta(hours=12),
    "daily":        timedelta(days=1),
    "every_2_days": timedelta(days=2),
    "every_3_days": timedelta(days=3),
    "weekly":       timedelta(weeks=1),
    "biweekly":     timedelta(weeks=2),
    "monthly":      timedelta(days=30),
}


def first_send_utc(hour: int, minute: int, utc_offset: int) -> datetime:
    """Return the next occurrence of HH:MM in the user's timezone, as UTC."""
    now_utc = datetime.utcnow()
    local_now = now_utc + timedelta(hours=utc_offset)
    target = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= local_now:
        target += timedelta(days=1)
    return target - timedelta(hours=utc_offset)


def next_send_after(frequency: str) -> datetime:
    return datetime.utcnow() + INTERVALS[frequency]


async def _send_kitten(bot: Bot, chat_id: int) -> bool:
    url = await fetch_random_kitten()
    if not url:
        logger.warning("Cat API returned nothing for chat_id=%s", chat_id)
        return False
    try:
        await bot.send_photo(chat_id=chat_id, photo=url, caption="Here's your daily dose of cuteness! 🐱")
        return True
    except Forbidden:
        logger.info("User %s blocked the bot — deactivating.", chat_id)
        db.set_active(chat_id, False)
    except TelegramError as e:
        logger.error("Failed to send to %s: %s", chat_id, e)
    return False


async def scheduler_loop(bot: Bot) -> None:
    logger.info("Scheduler started.")
    while True:
        now = datetime.utcnow()
        due = db.get_due_users(now)
        for user in due:
            await _send_kitten(bot, user["chat_id"])
            db.update_next_send(user["chat_id"], next_send_after(user["frequency"]))
        await asyncio.sleep(60)
