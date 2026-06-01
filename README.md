# 🐱 Everyday Kittens

A Telegram bot that sends random kitten photos to your inbox on a schedule you control — anywhere from 4 times a day down to once a month.

---

## Features

- **Flexible frequency** — 9 options from 4×/day to once a month
- **Custom delivery time** — set the hour and minute for your first daily kitten
- **Timezone support** — UTC offset from −12 to +12
- **Pause & resume** — stop deliveries any time without losing your settings
- **On-demand kittens** — `/kitten` sends one instantly, no waiting
- **Inline settings menu** — everything configurable via buttons, no typing required

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourname/everyday-kittens.git
cd everyday-kittens
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in:

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ Yes | Token from [@BotFather](https://t.me/BotFather) |
| `CAT_API_KEY` | No | API key from [thecatapi.com](https://thecatapi.com) — removes rate limits |
| `DB_PATH` | No | Path for the SQLite file (default: `kittens.db`) |

### 4. Run the bot

```bash
python bot.py
```

The bot creates `kittens.db` automatically on first run.

---

## Bot commands

| Command | Description |
|---|---|
| `/start` | Register and start receiving kittens |
| `/settings` | Open the settings menu |
| `/kitten` | Get a random kitten right now |
| `/stop` | Pause scheduled deliveries |
| `/resume` | Resume deliveries |
| `/help` | Show all commands |

---

## Frequency options

| Option | Interval |
|---|---|
| 4 times a day | Every 6 hours |
| 3 times a day | Every 8 hours |
| 2 times a day | Every 12 hours |
| Once a day | Every 24 hours |
| Every 2 days | Every 48 hours |
| Every 3 days | Every 72 hours |
| Once a week | Every 7 days |
| Every 2 weeks | Every 14 days |
| Once a month | Every 30 days |

---

## Project structure

```
everyday-kittens/
├── bot.py          # Entry point — handlers and app setup
├── scheduler.py    # Background loop that sends kittens on schedule
├── database.py     # SQLite read/write helpers
├── cat_api.py      # Fetches random kitten images from The Cat API
├── keyboards.py    # Inline keyboard builders
├── config.py       # Loads environment variables
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## How scheduling works

1. When you `/start`, the bot schedules your first kitten for **09:00 in your timezone** (default).
2. After each delivery, the next one is queued at `now + interval`.
3. Changing frequency, time, or timezone **resets** the schedule to the next occurrence of your preferred time.
4. If the bot is restarted, any overdue deliveries are sent within 60 seconds of startup.

---

## Keeping the bot alive

For a personal bot you can simply run `python bot.py` in a terminal. For something more reliable:

**systemd (Linux):**

```ini
[Unit]
Description=Everyday Kittens Bot
After=network.target

[Service]
WorkingDirectory=/path/to/everyday-kittens
ExecStart=/path/to/.venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**screen / tmux** — simplest option for a VPS:

```bash
screen -S kittens
python bot.py
# Ctrl+A, D to detach
```

---

## License

MIT
