from dash.dependencies import Input, Output


def register_callbacks(app, spotidash):
    @app.callback(
        Output("login-container", "children"),
        Output("login-container", "style"),
        Output("dashboard-container", "children"),
        Output("dashboard-container", "style"),
        Input("url", "pathname"),
    )
    def render_page(pathname):
        if spotidash.is_authenticated():
            try:
                sp = spotidash.get_spotipy_client()
                user = sp.current_user()
                dashboard = spotidash.layout_builder.build_dashboard(user)
            except Exception:
                dashboard = spotidash.layout_builder.build_dashboard()
            return "", {"display": "none"}, dashboard, {"display": "block"}
        else:
            login = spotidash.layout_builder.build_login_page()
            login_style = {
                "display": "block",
                "backgroundColor": "#121212",
                "minHeight": "100vh",
            }
            return login, login_style, "", {"display": "none"}
