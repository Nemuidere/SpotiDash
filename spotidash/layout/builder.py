from dash import html, dcc
from .styles import STYLES


class LayoutBuilder:
    def __init__(self):
        self.styles = STYLES

    def build(self):
        return html.Div([
            html.Link(
                rel="stylesheet",
                href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
            ),
            dcc.Location(id="url", refresh=False),
            dcc.Store(id="auth-store", storage_type="session"),
            html.Div([
                html.Div(id="login-container", style={
                    "backgroundColor": self.styles["bg"],
                    "minHeight": "100vh",
                }),
                html.Div(id="dashboard-container", style={
                    "display": "none",
                    "backgroundColor": self.styles["bg"],
                    "minHeight": "100vh",
                }),
            ]),
        ], style={
            "backgroundColor": self.styles["bg"],
            "fontFamily": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
            "color": self.styles["text"],
        })

    def build_login_page(self):
        return html.Div([
            html.Div([
                html.Div([
                    html.H1("SpotiDash", style={
                        "fontSize": "48px",
                        "fontWeight": "700",
                        "marginBottom": "8px",
                        "color": self.styles["text"],
                    }),
                    html.P("Your personal Spotify analytics", style={
                        "fontSize": "18px",
                        "color": self.styles["text_muted"],
                        "marginBottom": "48px",
                    }),
                    html.A(
                        html.Button(
                            "Login with Spotify",
                            n_clicks=0,
                            style={
                                "backgroundColor": self.styles["accent"],
                                "color": self.styles["text"],
                                "border": "none",
                                "padding": "14px 32px",
                                "borderRadius": "12px",
                                "fontSize": "16px",
                                "fontWeight": "600",
                                "cursor": "pointer",
                                "fontFamily": "'Inter', sans-serif",
                            }
                        ),
                        href="/login",
                        style={"textDecoration": "none"}
                    ),
                ], style={
                    "backgroundColor": self.styles["card_bg"],
                    "borderRadius": "12px",
                    "padding": "48px",
                    "minWidth": "360px",
                    "textAlign": "center",
                    "border": "1px solid rgba(255, 255, 255, 0.05)",
                }),
            ], style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "minHeight": "100vh",
            }),
        ])

    def build_dashboard(self, user=None):
        greeting = f"Welcome, {user.get('display_name', 'User')}!" if user else "Welcome!"
        avatar_url = user.get("images", [{}])[0].get("url") if user else None
        
        return html.Div([
            html.Header([
                html.Div([
                    html.H1("SpotiDash", style={
                        "fontSize": "24px",
                        "fontWeight": "700",
                        "margin": "0",
                    }),
                ]),
                html.Div([
                    html.Img(
                        src=avatar_url,
                        style={
                            "width": "40px",
                            "height": "40px",
                            "borderRadius": "50%",
                            "display": "block" if avatar_url else "none",
                        }
                    ) if avatar_url else html.Div(style={"width": "40px", "height": "40px"}),
                    html.Div([
                        html.Span(user.get("display_name", "User") if user else "User", style={
                            "fontWeight": "500",
                        }),
                        html.A("Logout", href="/logout", style={
                            "fontSize": "14px",
                            "color": self.styles["text_muted"],
                            "marginLeft": "12px",
                        }),
                    ], style={"display": "flex", "alignItems": "center"}),
                ], style={"display": "flex", "alignItems": "center", "gap": "12px"}),
            ], style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "padding": f"{self.styles['spacing']} 32px",
                "backgroundColor": self.styles["card_bg"],
                "borderBottom": "1px solid rgba(255, 255, 255, 0.05)",
            }),
            html.Main([
                html.Div([
                    html.H2(greeting, style={
                        "fontSize": "28px",
                        "fontWeight": "600",
                        "marginBottom": "8px",
                    }),
                    html.P("Your Spotify dashboard is ready!", style={
                        "color": self.styles["text_muted"],
                    }),
                ], style={"marginBottom": "32px"}),
                html.Div(id="dashboard-content", style={
                    "padding": "0 32px",
                    "maxWidth": "1400px",
                }),
            ], style={
                "padding": f"{self.styles['spacing']} 32px",
            }),
        ])
