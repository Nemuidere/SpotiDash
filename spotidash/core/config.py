import os
import secrets
from dotenv import load_dotenv

load_dotenv()


class Config:
    SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
    SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
    SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

    # Flask session signing key. Set FLASK_SECRET_KEY in production so sessions
    # survive restarts; falls back to a random per-process key for local dev.
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)

    SCOPE = "user-top-read user-read-recently-played playlist-read-private user-read-currently-playing"
