import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
CAT_API_KEY: str = os.getenv("CAT_API_KEY", "")
DB_PATH: str = os.getenv("DB_PATH", "kittens.db")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Create a .env file based on .env.example.")
