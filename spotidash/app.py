from dash import Dash
from .core import Config, SpotifyClient
from .layout.builder import LayoutBuilder
from .callbacks import register_callbacks


class SpotiDash:
    def __init__(self):
        self.app = Dash(__name__)
        self.spotify = SpotifyClient()
        self._setup_layout()
        register_callbacks(self.app, self.spotify)

    def _setup_layout(self):
        builder = LayoutBuilder()
        self.app.layout = builder.build()

    def run(self, **kwargs):
        self.app.run(**kwargs)
