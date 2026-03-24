from dash.dependencies import Input, Output, State, ALL
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

    @app.callback(
        Output("top-tracks-container", "children"),
        Output("top-tracks-store", "data"),
        Output("btn-time-4weeks", "className"),
        Output("btn-time-6months", "className"),
        Output("btn-time-alltime", "className"),
        Output("btn-count-10", "className"),
        Output("btn-count-25", "className"),
        Output("btn-count-50", "className"),
        Output("btn-favourites-only", "className"),
        Output("favourites-store", "data"),
        Output("filter-state-store", "data"),
        Input("btn-time-4weeks", "n_clicks"),
        Input("btn-time-6months", "n_clicks"),
        Input("btn-time-alltime", "n_clicks"),
        Input("btn-count-10", "n_clicks"),
        Input("btn-count-25", "n_clicks"),
        Input("btn-count-50", "n_clicks"),
        Input("btn-favourites-only", "n_clicks"),
        Input({"type": "btn-favourite", "index": ALL}, "n_clicks"),
        Input("url", "pathname"),
        State("top-tracks-store", "data"),
        State("favourites-store", "data"),
        State("filter-state-store", "data"),
        prevent_initial_call=False,
    )
    def update_top_tracks(n_4weeks, n_6months, n_alltime, n_10, n_25, n_50, n_fav_only, favourite_btns, pathname, store_data, favourites, filter_state):
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if favourites is None:
            favourites = []
        
        if filter_state is None:
            filter_state = {"time_range": "medium_term", "count": 50, "show_favourites_only": False}
        
        time_range = filter_state.get("time_range", "medium_term")
        count = filter_state.get("count", 50)
        show_favourites_only = filter_state.get("show_favourites_only", False)
        
        time_ranges = {
            "btn-time-4weeks": "short_term",
            "btn-time-6months": "medium_term",
            "btn-time-alltime": "long_term",
        }
        
        counts = {
            "btn-count-10": 10,
            "btn-count-25": 25,
            "btn-count-50": 50,
        }
        
        if triggered_id in time_ranges:
            time_range = time_ranges[triggered_id]
        elif triggered_id in counts:
            count = counts[triggered_id]
        elif triggered_id == "btn-favourites-only":
            show_favourites_only = not show_favourites_only
        elif triggered_id == "url":
            time_range = "medium_term"
            count = 50
            show_favourites_only = False
        elif triggered_id.startswith("{"):
            try:
                import json
                track_id = json.loads(triggered_id).get("index")
                if track_id:
                    if track_id in favourites:
                        favourites = [f for f in favourites if f != track_id]
                    else:
                        favourites = list(favourites) + [track_id]
            except:
                pass
        
        filter_state = {"time_range": time_range, "count": count, "show_favourites_only": show_favourites_only}
        
        if not spotidash.is_authenticated():
            return "", None, "time-range-btn", "time-range-btn", "time-range-btn", "time-range-btn", "time-range-btn", "time-range-btn", "time-range-btn", [], filter_state
        
        tracks = spotidash.get_top_tracks(limit=50, time_range=time_range)
        
        time_range_labels = {
            "short_term": "4 Weeks",
            "medium_term": "6 Months",
            "long_term": "All Time",
        }
        display_label = time_range_labels.get(time_range, "6 Months")
        
        btn_4weeks = "time-range-btn active" if time_range == "short_term" else "time-range-btn"
        btn_6months = "time-range-btn active" if time_range == "medium_term" else "time-range-btn"
        btn_alltime = "time-range-btn active" if time_range == "long_term" else "time-range-btn"
        btn_10 = "time-range-btn active" if count == 10 else "time-range-btn"
        btn_25 = "time-range-btn active" if count == 25 else "time-range-btn"
        btn_50 = "time-range-btn active" if count == 50 else "time-range-btn"
        btn_fav_only = "time-range-btn active" if show_favourites_only else "time-range-btn"
        
        content = spotidash.layout_builder.build_top_tracks(tracks, display_label, count, set(favourites), show_favourites_only)
        
        return content, tracks, btn_4weeks, btn_6months, btn_alltime, btn_10, btn_25, btn_50, btn_fav_only, favourites, filter_state
