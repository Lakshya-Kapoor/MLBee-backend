
from os import getenv

from dotenv import load_dotenv

load_dotenv()

DB_URL = getenv("DB_URL")
NEWS_API_KEY = getenv("NEWS_API_KEY")
GEMINI_API_KEY = getenv("GEMINI_API_KEY")