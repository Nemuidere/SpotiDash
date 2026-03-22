from dash import html, dcc
from dash.dependencies import Input, Output, State


class LayoutBuilder:
    def build(self):
        return html.Div([
            html.H1("SpotiDash"),
            dcc.Location(id="url", refresh=False),
            html.Div(id="page-content"),
        ])
