from flask import Flask, session, redirect, request
from dash import Dash
from dash.dependencies import Input, Output
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
        self.server.secret_key = "spotidash-secret-key"
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
        return spotipy.Spotify(auth=token_info["access_token"])

    def get_currently_playing(self):
        sp = self.get_spotipy_client()
        if sp is None:
            return None
        try:
            return sp.currently_playing()
        except Exception:
            return None

    def run(self, **kwargs):
        self.app.run(**kwargs)
