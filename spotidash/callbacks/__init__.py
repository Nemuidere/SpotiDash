from dash.dependencies import Input, Output, State
import dash
import time


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

    @app.callback(
        Output("now-playing-store", "data"),
        Output("now-playing-bar", "children"),
        Input("now-playing-interval", "n_intervals"),
        Input("progress-interval", "n_intervals"),
        State("now-playing-store", "data"),
        prevent_initial_call=True,
    )
    def update_currently_playing(n_intervals, progress_n_intervals, store_data):
        triggered_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
        is_spotify_fetch = triggered_id == "now-playing-interval"
        
        if is_spotify_fetch:
            if not spotidash.is_authenticated():
                return dash.no_update, ""
            fetch_start = time.time()
            track = spotidash.get_currently_playing()
            if track:
                track_id = track.get("item", {}).get("id", "")
                prev_track_id = store_data.get("track_id", "") if store_data else ""
                is_new_song = track_id != prev_track_id
                progress_at_fetch = track.get("progress_ms", 0)
                new_data = {
                    "track": track,
                    "fetch_start_time": fetch_start,
                    "progress_at_fetch": progress_at_fetch,
                    "track_id": track_id,
                }
                animation = "slide-down" if is_new_song else ""
                return new_data, spotidash.layout_builder.build_currently_playing(track, 0, animation)
            else:
                return None, ""
        else:
            if not store_data or not store_data.get("track"):
                return dash.no_update, dash.no_update
            
            track = store_data.get("track")
            fetch_start = store_data.get("fetch_start_time", time.time())
            progress_at_fetch = store_data.get("progress_at_fetch", 0)
            elapsed_ms = int((time.time() - fetch_start) * 1000)
            return dash.no_update, spotidash.layout_builder.build_currently_playing(track, elapsed_ms, "")
