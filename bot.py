import asyncio
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import database as db
from cat_api import fetch_random_kitten
from config import BOT_TOKEN
from keyboards import FREQUENCY_OPTIONS, frequency_kb, main_menu, timezone_kb
from scheduler import first_send_utc, next_send_after, scheduler_loop

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

_WAITING_TIME = "waiting_for_time"

HELP_TEXT = (
    "🐱 *Everyday Kittens* — commands:\n\n"
    "/start — register and start receiving kittens\n"
    "/settings — configure frequency, time, and timezone\n"
    "/kitten — get a random kitten right now\n"
    "/stop — pause scheduled deliveries\n"
    "/resume — resume deliveries\n"
    "/help — show this message"
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _settings_text_and_kb(user):
    return main_menu(
        is_active=bool(user["is_active"]),
        frequency=user["frequency"],
        hour=user["send_hour"],
        minute=user["send_minute"],
        utc_offset=user["utc_offset"],
    )


# ── command handlers ──────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    u = update.effective_user
    db.upsert_user(u.id, u.username or u.first_name)

    user = db.get_user(u.id)
    if not user["next_send_utc"]:
        db.update_next_send(u.id, first_send_utc(9, 0, 0))

    await update.message.reply_text(
        "🐱 *Welcome to Everyday Kittens!*\n\n"
        "I'll send you adorable kitten photos on your own schedule.\n\n"
        "Use /settings to pick how often and when you'd like them.\n"
        "Use /kitten to get one right now!\n\n"
        "/help — full command list",
        parse_mode="Markdown",
    )


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = db.get_user(update.effective_user.id)
    text, kb = _settings_text_and_kb(user)
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)


async def cmd_kitten(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = await fetch_random_kitten()
    if url:
        await update.message.reply_photo(url, caption="Here's your kitten! 🐱")
    else:
        await update.message.reply_text("Couldn't fetch a kitten right now. Try again in a moment! 🐱")


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db.set_active(update.effective_user.id, False)
    await update.message.reply_text("Deliveries paused ⏸\nUse /resume to start again.")


async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    db.set_active(user_id, True)
    if not user["next_send_utc"]:
        db.update_next_send(user_id, next_send_after(user["frequency"]))
    await update.message.reply_text("Deliveries resumed! 🐱")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


# ── inline button handler ─────────────────────────────────────────────────────

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data: str = query.data
    user_id = query.from_user.id
    user = db.get_user(user_id)

    # ── back to main menu ────────────────────────────────────────────────────
    if data == "menu_back":
        text, kb = _settings_text_and_kb(user)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)

    # ── frequency menu ───────────────────────────────────────────────────────
    elif data == "menu_frequency":
        await query.edit_message_text(
            "📅 *Choose your delivery frequency:*",
            parse_mode="Markdown",
            reply_markup=frequency_kb(user["frequency"]),
        )

    elif data.startswith("freq_"):
        freq = data[5:]
        db.update_frequency(user_id, freq)
        db.update_next_send(
            user_id, first_send_utc(user["send_hour"], user["send_minute"], user["utc_offset"])
        )
        await query.edit_message_text(
            f"✅ Frequency set to *{FREQUENCY_OPTIONS[freq]}*!",
            parse_mode="Markdown",
            reply_markup=frequency_kb(freq),
        )

    # ── time input ───────────────────────────────────────────────────────────
    elif data == "menu_time":
        context.user_data[_WAITING_TIME] = True
        await query.edit_message_text(
            "🕐 *Set your preferred delivery time*\n\n"
            "Type the time in *HH:MM* format (24-hour clock).\n"
            "Example: `09:00` or `21:30`",
            parse_mode="Markdown",
        )

    # ── timezone menu ────────────────────────────────────────────────────────
    elif data == "menu_timezone":
        await query.edit_message_text(
            "🌍 *Select your UTC offset:*",
            parse_mode="Markdown",
            reply_markup=timezone_kb(user["utc_offset"]),
        )

    elif data.startswith("tz_"):
        offset = int(data[3:])
        db.update_utc_offset(user_id, offset)
        db.update_next_send(
            user_id, first_send_utc(user["send_hour"], user["send_minute"], offset)
        )
        tz_label = f"UTC{'+' if offset >= 0 else ''}{offset}"
        await query.edit_message_text(
            f"✅ Timezone set to *{tz_label}*!",
            parse_mode="Markdown",
            reply_markup=timezone_kb(offset),
        )

    # ── pause / resume toggle ────────────────────────────────────────────────
    elif data == "toggle_pause":
        new_state = not bool(user["is_active"])
        db.set_active(user_id, new_state)
        if new_state and not user["next_send_utc"]:
            db.update_next_send(user_id, next_send_after(user["frequency"]))
        # Refresh user row and return to main menu
        user = db.get_user(user_id)
        text, kb = _settings_text_and_kb(user)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)

    # ── instant kitten ───────────────────────────────────────────────────────
    elif data == "menu_now":
        url = await fetch_random_kitten()
        if url:
            await query.message.reply_photo(url, caption="Here's your kitten! 🐱")
        else:
            await query.message.reply_text("Couldn't fetch one right now. Try again! 🐱")


# ── free-text handler (time input) ────────────────────────────────────────────

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get(_WAITING_TIME):
        return

    raw = update.message.text.strip()
    try:
        parts = raw.split(":")
        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Invalid format. Please enter the time as *HH:MM* (e.g., `09:00`).",
            parse_mode="Markdown",
        )
        return

    user_id = update.effective_user.id
    user = db.get_user(user_id)
    db.update_time(user_id, hour, minute)
    db.update_next_send(user_id, first_send_utc(hour, minute, user["utc_offset"]))
    context.user_data[_WAITING_TIME] = False

    offset = user["utc_offset"]
    tz_label = f"UTC{'+' if offset >= 0 else ''}{offset}"
    await update.message.reply_text(
        f"✅ Time set to *{hour:02d}:{minute:02d}* ({tz_label})!\n\n"
        "Use /settings to review your full configuration.",
        parse_mode="Markdown",
    )


# ── application setup ─────────────────────────────────────────────────────────

async def _post_init(application: Application) -> None:
    asyncio.create_task(scheduler_loop(application.bot))


def main() -> None:
    db.init_db()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(_post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("settings", cmd_settings))
    app.add_handler(CommandHandler("kitten", cmd_kitten))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    logger.info("Bot is running.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
