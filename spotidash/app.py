from flask import session, redirect, request
from dash import Dash
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler

from .core import Config
from .layout.builder import LayoutBuilder
from .callbacks import register_callbacks
from .layout.styles import GLOBAL_CSS


class SpotiDash:
    def __init__(self):
        self.app = Dash(__name__, suppress_callback_exceptions=True)
        self.app.index_string = f'''
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link rel="preconnect" href="https://fonts.googleapis.com">
                <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
                <style>{GLOBAL_CSS}</style>
                {{%metas%}}
                <title>{{title}}</title>
                {{%css%}}
            </head>
            <body>
                {{%app_entry%}}
                <footer>
                    {{%config%}}
                    {{%scripts%}}
                    {{%renderer%}}
                </footer>
            </body>
        </html>
        '''
        self.server = self.app.server
        self.server.secret_key = Config.SECRET_KEY
        self.cache_handler = FlaskSessionCacheHandler(session)
        self.sp_oauth = SpotifyOAuth(
            client_id=Config.SPOTIPY_CLIENT_ID,
            client_secret=Config.SPOTIPY_CLIENT_SECRET,
            redirect_uri=Config.SPOTIPY_REDIRECT_URI,
            scope=Config.SCOPE,
            cache_handler=self.cache_handler,
            show_dialog=True,
        )
        self.layout_builder = LayoutBuilder()
        self._setup_routes()
        self._setup_layout()
        register_callbacks(self.app, self)

    def _setup_routes(self):
        @self.server.route("/login")
        def login():
            auth_url = self.sp_oauth.get_authorize_url()
            return redirect(auth_url)

        @self.server.route("/callback")
        def callback():
            code = request.args.get("code")
            if code:
                token_info = self.sp_oauth.get_access_token(code)
                self.cache_handler.save_token_to_cache(token_info)
            return redirect("/")

        @self.server.route("/logout")
        def logout():
            session.clear()
            return redirect("/")

    def _setup_layout(self):
        self.app.layout = self.layout_builder.build()

    def is_authenticated(self):
        token_info = self.cache_handler.get_cached_token()
        return token_info is not None

    def get_spotipy_client(self):
        token_info = self.cache_handler.get_cached_token()
        if token_info is None:
            return None
        return spotipy.Spotify(auth_manager=self.sp_oauth)

    def get_currently_playing(self):
        sp = self.get_spotipy_client()
        if sp is None:
            return None
        try:
            return sp.currently_playing()
        except Exception:
            return None

    def get_top_tracks(self, limit=50, time_range="medium_term"):
        sp = self.get_spotipy_client()
        if sp is None:
            return None
        try:
            return sp.current_user_top_tracks(limit=limit, time_range=time_range)
        except Exception:
            return None

    def get_recently_played(self, limit=50):
        sp = self.get_spotipy_client()
        if sp is None:
            return None
        try:
            return sp.current_user_recently_played(limit=limit)
        except Exception:
            return None

    def get_top_artists(self, limit=50, time_range="medium_term"):
        sp = self.get_spotipy_client()
        if sp is None:
            return None
        try:
            return sp.current_user_top_artists(limit=limit, time_range=time_range)
        except Exception:
            return None

    def get_playlists(self, limit=50):
        """
        Fetch user's playlists with pagination support.

        Args:
            limit: Maximum number of playlists to fetch (default 50, capped at 200)

        Returns:
            List of playlist dicts with name, track_count, images, id, etc.
            Or None if error occurs.
        """
        # Early exit: Cap limit at 200 to prevent excessive API calls
        if limit is None or not isinstance(limit, int) or limit <= 0:
            limit = 50
        limit = min(limit, 200)

        sp = self.get_spotipy_client()
        if sp is None:
            return None

        try:
            all_playlists = []
            offset = 0
            page_size = 50  # Spotify's max per request

            while len(all_playlists) < limit:
                response = sp.current_user_playlists(
                    limit=min(page_size, limit - len(all_playlists)),
                    offset=offset
                )

                if not response or not isinstance(response, dict):
                    break

                items = response.get("items", [])
                if not items:
                    break

                for playlist in items:
                    if not isinstance(playlist, dict):
                        continue

                    # Extract track count: try items.total first (recommended), fallback to tracks.total (deprecated)
                    track_count = 0

                    items_data = playlist.get("items", {})
                    if isinstance(items_data, dict) and "total" in items_data:
                        track_count = items_data.get("total", 0)
                    else:
                        tracks_data = playlist.get("tracks", {})
                        if isinstance(tracks_data, dict):
                            track_count = tracks_data.get("total", 0)

                    all_playlists.append({
                        "id": playlist.get("id"),
                        "name": playlist.get("name", "Untitled Playlist"),
                        "track_count": track_count,
                        "images": playlist.get("images", []),
                        "owner": playlist.get("owner", {}),
                        "public": playlist.get("public", False),
                        "collaborative": playlist.get("collaborative", False),
                        "uri": playlist.get("uri"),
                        "href": playlist.get("href"),
                        "description": playlist.get("description"),
                        "spotify_url": playlist.get("external_urls", {}).get("spotify"),
                    })

                # Check if there are more pages
                total = response.get("total", 0)
                if offset + len(items) >= total:
                    break

                offset += page_size

            return all_playlists

        except Exception:
            # Fail fast: Return None on any error
            return None

    def run(self, **kwargs):
        self.app.run(**kwargs)
