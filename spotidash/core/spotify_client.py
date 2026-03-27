import spotipy
from spotipy.oauth2 import SpotifyOAuth
from .config import Config


class SpotifyClient:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = spotipy.Spotify(
                auth_manager=SpotifyOAuth(
                    client_id=Config.SPOTIPY_CLIENT_ID,
                    client_secret=Config.SPOTIPY_CLIENT_SECRET,
                    redirect_uri=Config.SPOTIPY_REDIRECT_URI,
                    scope=Config.SCOPE,
                )
            )
        return self._client

    def get_current_user(self):
        return self.client.current_user()

    def get_top_tracks(self, limit=10, time_range="medium_term"):
        return self.client.current_user_top_tracks(limit=limit, time_range=time_range)

    def get_top_artists(self, limit=10, time_range="medium_term"):
        return self.client.current_user_top_artists(limit=limit, time_range=time_range)
