from dash import html, dcc
from dash.dependencies import Input, Output


class LayoutBuilder:
    def build(self):
        return html.Div([
            dcc.Location(id="url", refresh=False),
            dcc.Store(id="auth-store", storage_type="session"),
            html.Div(id="page-content"),
            html.Div(id="login-container", style={
                "display": "flex",
                "flexDirection": "column",
                "alignItems": "center",
                "justifyContent": "center",
                "height": "100vh",
                "fontFamily": "Arial, sans-serif",
            }),
            html.Div(id="dashboard-container", style={"display": "none"}),
        ])

    def build_login_page(self):
        return html.Div([
            html.H1("SpotiDash", style={"marginBottom": "2rem"}),
            html.A(
                html.Button("Login with Spotify", id="login-button", n_clicks=0),
                href="/login",
                style={"textDecoration": "none"}
            ),
        ])

    def build_dashboard(self, user=None):
        greeting = f"Welcome, {user.get('display_name', 'User')}!" if user else "Welcome!"
        return html.Div([
            html.Header([
                html.H1("SpotiDash", style={"margin": "0", "flex": "1"}),
                html.A("Logout", href="/logout", style={
                    "color": "#fff",
                    "textDecoration": "none",
                    "padding": "10px 20px",
                    "background": "#1db954",
                    "borderRadius": "20px",
                }),
            ], style={
                "display": "flex",
                "alignItems": "center",
                "padding": "20px",
                "background": "#191414",
                "color": "#fff",
            }),
            html.Div([
                html.H2(greeting),
                html.P("Your Spotify dashboard is ready!"),
            ], style={"padding": "20px"}),
        ])
