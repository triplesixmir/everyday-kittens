from telegram import InlineKeyboardButton, InlineKeyboardMarkup

FREQUENCY_OPTIONS: dict[str, str] = {
    "4x_day":      "4 times a day",
    "3x_day":      "3 times a day",
    "2x_day":      "2 times a day",
    "daily":       "Once a day",
    "every_2_days": "Every 2 days",
    "every_3_days": "Every 3 days",
    "weekly":      "Once a week",
    "biweekly":    "Every 2 weeks",
    "monthly":     "Once a month",
}


def main_menu(is_active: bool, frequency: str, hour: int, minute: int, utc_offset: int) -> tuple[str, InlineKeyboardMarkup]:
    freq_label = FREQUENCY_OPTIONS.get(frequency, frequency)
    tz_label = f"UTC{'+' if utc_offset >= 0 else ''}{utc_offset}"
    status = "Active ✅" if is_active else "Paused ⏸"
    pause_btn = "⏸ Pause deliveries" if is_active else "▶️ Resume deliveries"

    text = (
        "⚙️ *Your settings*\n\n"
        f"📅 Frequency: *{freq_label}*\n"
        f"🕐 Preferred time: *{hour:02d}:{minute:02d}* ({tz_label})\n"
        f"📊 Status: *{status}*"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Frequency", callback_data="menu_frequency")],
        [InlineKeyboardButton("🕐 Delivery time", callback_data="menu_time")],
        [InlineKeyboardButton("🌍 Timezone (UTC offset)", callback_data="menu_timezone")],
        [InlineKeyboardButton(pause_btn, callback_data="toggle_pause")],
        [InlineKeyboardButton("🐱 Send me a kitten now!", callback_data="menu_now")],
    ])
    return text, keyboard


def frequency_kb(current: str) -> InlineKeyboardMarkup:
    rows = []
    for key, label in FREQUENCY_OPTIONS.items():
        text = f"✅ {label}" if key == current else label
        rows.append([InlineKeyboardButton(text, callback_data=f"freq_{key}")])
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="menu_back")])
    return InlineKeyboardMarkup(rows)


def timezone_kb(current_offset: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for offset in range(-12, 13):
        label = f"UTC{'+' if offset >= 0 else ''}{offset}"
        if offset == current_offset:
            label = f"✅ {label}"
        row.append(InlineKeyboardButton(label, callback_data=f"tz_{offset}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="menu_back")])
    return InlineKeyboardMarkup(rows)
