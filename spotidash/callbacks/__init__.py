from dash.dependencies import Input, Output, State, ALL
import dash
import time


def register_callbacks(app, spotidash):
    app.clientside_callback(
        """
        function(n_intervals) {
            if (!document.visibilityState) return true;
            return document.visibilityState === 'visible';
        }
        """,
        Output("visibility-store", "data"),
        Input("now-playing-interval", "n_intervals"),
    )

    @app.callback(
        Output("top-tracks-cache", "data"),
        Input("tracks-prefetch-interval", "n_intervals"),
        Input("url", "pathname"),
        State("top-tracks-cache", "data"),
        prevent_initial_call=True,
    )
    def prefetch_top_tracks(n_intervals, pathname, cache_data):
        if not spotidash.is_authenticated():
            return dash.no_update
        
        if cache_data is None:
            cache_data = {"recent": None, "short_term": None, "medium_term": None, "long_term": None}
        
        loaded = [k for k, v in cache_data.items() if v is not None]
        
        time_ranges = ["recent", "short_term", "medium_term", "long_term"]
        next_range = None
        for tr in time_ranges:
            if tr not in loaded:
                next_range = tr
                break
        
        if next_range is None:
            return cache_data
        
        if next_range == "recent":
            data = spotidash.get_recently_played(limit=50)
            if data:
                track_play_counts = {}
                for item in data.get("items", []):
                    track = item.get("track", {})
                    track_id = track.get("id")
                    if track_id:
                        if track_id in track_play_counts:
                            track_play_counts[track_id]["count"] += 1
                        else:
                            track_play_counts[track_id] = {"track": track, "count": 1}
                sorted_tracks = sorted(track_play_counts.values(), key=lambda x: (-x["count"], x["track"].get("name", "")))
                cache_data[next_range] = {"items": [t["track"] for t in sorted_tracks[:50]]}
            else:
                cache_data[next_range] = {"items": []}
        else:
            data = spotidash.get_top_tracks(limit=50, time_range=next_range)
            cache_data[next_range] = data if data else {"items": []}
        
        return cache_data

    @app.callback(
        Output("top-artists-cache", "data"),
        Input("tracks-prefetch-interval", "n_intervals"),
        State("top-artists-cache", "data"),
        State("top-tracks-cache", "data"),
        prevent_initial_call=True,
    )
    def prefetch_recent_artists(n_intervals, artists_cache, tracks_cache):
        if not spotidash.is_authenticated():
            return dash.no_update
        
        if artists_cache is None:
            artists_cache = {}
        
        if "recent" in artists_cache:
            return artists_cache
        
        if not tracks_cache or not tracks_cache.get("recent"):
            return dash.no_update
        
        recent_tracks = tracks_cache.get("recent", {}).get("items", [])
        
        artist_scores = {}
        for idx, track in enumerate(recent_tracks):
            score = 51 - (idx + 1)
            for artist in track.get("artists", []):
                artist_id = artist.get("id")
                if artist_id:
                    if artist_id not in artist_scores:
                        artist_scores[artist_id] = {"artist": artist, "score": 0, "track_count": 0}
                    artist_scores[artist_id]["score"] += score
                    artist_scores[artist_id]["track_count"] += 1
        
        sorted_artists = sorted(artist_scores.values(), key=lambda x: (-x["score"], x["artist"].get("name", "") if x["artist"] else ""))
        
        artists_list = [
            {
                "id": a["artist"].get("id") if a["artist"] else None,
                "name": a["artist"].get("name") if a["artist"] else "Unknown",
                "images": a["artist"].get("images", []) if a["artist"] else [],
                "track_count": a["track_count"],
                "score": a["score"],
            }
            for a in sorted_artists
        ]
        
        artists_cache["recent"] = {"artists": artists_list}
        
        return artists_cache

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
        State("visibility-store", "data"),
        prevent_initial_call=True,
    )
    def update_currently_playing(n_intervals, progress_n_intervals, store_data, is_visible):
        triggered_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
        is_spotify_fetch = triggered_id == "now-playing-interval"
        
        if is_spotify_fetch:
            if not is_visible:
                return dash.no_update, dash.no_update
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
        Output("btn-time-recent", "className"),
        Output("btn-time-4weeks", "className"),
        Output("btn-time-6months", "className"),
        Output("btn-time-alltime", "className"),
        Output("btn-count-10", "className"),
        Output("btn-count-25", "className"),
        Output("btn-count-50", "className"),
        Output("btn-favourites-only", "className"),
        Output("favourites-store", "data"),
        Output("filter-state-store", "data"),
        Input("btn-time-recent", "n_clicks"),
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
        State("top-tracks-cache", "data"),
        prevent_initial_call=False,
    )
    def update_top_tracks(n_recent, n_4weeks, n_6months, n_alltime, n_10, n_25, n_50, n_fav_only, favourite_btns, pathname, store_data, favourites, filter_state, tracks_cache):
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
            "btn-time-recent": "recent",
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
        
        cached_tracks = tracks_cache.get(time_range) if tracks_cache else None
        
        if cached_tracks is not None:
            tracks = cached_tracks
        elif time_range == "recent":
            recent_tracks = spotidash.get_recently_played(limit=50)
            if recent_tracks:
                track_play_counts = {}
                for item in recent_tracks.get("items", []):
                    track = item.get("track", {})
                    track_id = track.get("id")
                    if track_id:
                        if track_id in track_play_counts:
                            track_play_counts[track_id]["count"] += 1
                        else:
                            track_play_counts[track_id] = {"track": track, "count": 1}
                sorted_tracks = sorted(track_play_counts.values(), key=lambda x: (-x["count"], x["track"].get("name", "")))
                tracks = {"items": [t["track"] for t in sorted_tracks[:50]]}
            else:
                tracks = {"items": []}
        else:
            tracks = spotidash.get_top_tracks(limit=50, time_range=time_range)
        
        time_range_labels = {
            "recent": "Recent",
            "short_term": "4 Weeks",
            "medium_term": "6 Months",
            "long_term": "All Time",
        }
        display_label = time_range_labels.get(time_range, "6 Months")
        
        btn_recent = "time-range-btn active" if time_range == "recent" else "time-range-btn"
        btn_4weeks = "time-range-btn active" if time_range == "short_term" else "time-range-btn"
        btn_6months = "time-range-btn active" if time_range == "medium_term" else "time-range-btn"
        btn_alltime = "time-range-btn active" if time_range == "long_term" else "time-range-btn"
        btn_10 = "time-range-btn active" if count == 10 else "time-range-btn"
        btn_25 = "time-range-btn active" if count == 25 else "time-range-btn"
        btn_50 = "time-range-btn active" if count == 50 else "time-range-btn"
        btn_fav_only = "time-range-btn active" if show_favourites_only else "time-range-btn"
        
        content = spotidash.layout_builder.build_top_tracks(tracks, display_label, count, set(favourites), show_favourites_only)
        
        return content, tracks, btn_recent, btn_4weeks, btn_6months, btn_alltime, btn_10, btn_25, btn_50, btn_fav_only, favourites, filter_state

    @app.callback(
        Output("top-artists-container", "children"),
        Output("top-artists-store", "data"),
        Output("btn-artist-recent", "className"),
        Output("btn-artist-4weeks", "className"),
        Output("btn-artist-6months", "className"),
        Output("btn-artist-alltime", "className"),
        Output("btn-artist-count-4", "className"),
        Output("btn-artist-count-12", "className"),
        Output("btn-artist-count-all", "className"),
        Output("artist-filter-store", "data"),
        Output("top-artists-cache", "data", allow_duplicate=True),
        Input("btn-artist-recent", "n_clicks"),
        Input("btn-artist-4weeks", "n_clicks"),
        Input("btn-artist-6months", "n_clicks"),
        Input("btn-artist-alltime", "n_clicks"),
        Input("btn-artist-count-4", "n_clicks"),
        Input("btn-artist-count-12", "n_clicks"),
        Input("btn-artist-count-all", "n_clicks"),
        Input("url", "pathname"),
        State("top-artists-store", "data"),
        State("artist-filter-store", "data"),
        State("top-artists-cache", "data"),
        State("top-tracks-cache", "data"),
        prevent_initial_call='initial_duplicate',
    )
    def update_top_artists(n_recent, n_4weeks, n_6months, n_alltime, n_4, n_12, n_all, pathname, store_data, filter_state, artists_cache, tracks_cache):
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if filter_state is None:
            filter_state = {"time_range": "short_term", "count": 12}
        
        time_range = filter_state.get("time_range", "short_term")
        count = filter_state.get("count", 12)
        
        time_ranges = {
            "btn-artist-recent": "recent",
            "btn-artist-4weeks": "short_term",
            "btn-artist-6months": "medium_term",
            "btn-artist-alltime": "long_term",
        }
        
        counts = {
            "btn-artist-count-4": 4,
            "btn-artist-count-12": 12,
            "btn-artist-count-all": 12,
        }
        
        if triggered_id in time_ranges:
            time_range = time_ranges[triggered_id]
        elif triggered_id in counts:
            count = counts[triggered_id]
        elif triggered_id == "url":
            time_range = "short_term"
            count = 12
        
        filter_state = {"time_range": time_range, "count": count}
        
        if not spotidash.is_authenticated():
            return "", None, "time-range-btn", "time-range-btn", "time-range-btn", "time-range-btn", "time-range-btn", "time-range-btn", "time-range-btn", filter_state
        
        cached_data = artists_cache.get(time_range) if artists_cache else None
        
        if cached_data is not None:
            artists_list = cached_data.get("artists", [])
        else:
            track_artist_scores = {}
            
            cached_tracks = tracks_cache.get(time_range) if tracks_cache else None
            
            if time_range == "recent":
                if cached_tracks:
                    tracks_items = cached_tracks.get("items", [])
                else:
                    recent_data = spotidash.get_recently_played(limit=50)
                    tracks_items = [item.get("track", {}) for item in recent_data.get("items", [])] if recent_data else []
            else:
                if cached_tracks:
                    tracks_items = cached_tracks.get("items", [])
                else:
                    tracks_data = spotidash.get_top_tracks(limit=50, time_range=time_range)
                    tracks_items = tracks_data.get("items", []) if tracks_data else []
            
            if tracks_items:
                for idx, track in enumerate(tracks_items):
                    score = 51 - (idx + 1)
                    for artist in track.get("artists", []):
                        artist_id = artist.get("id")
                        if artist_id:
                            if artist_id not in track_artist_scores:
                                track_artist_scores[artist_id] = {"score": 0, "track_count": 0, "artist_obj": artist}
                            track_artist_scores[artist_id]["score"] += score
                            track_artist_scores[artist_id]["track_count"] += 1
            
            top_artists = spotidash.get_top_artists(limit=42, time_range=time_range)
            
            artist_scores = {}
            if top_artists and top_artists.get("items"):
                for artist in top_artists["items"]:
                    artist_id = artist.get("id")
                    if artist_id in track_artist_scores:
                        artist_scores[artist_id] = {
                            "artist": artist,
                            "score": track_artist_scores[artist_id]["score"],
                            "track_count": track_artist_scores[artist_id]["track_count"],
                        }
                    else:
                        artist_scores[artist_id] = {
                            "artist": artist,
                            "score": 0,
                            "track_count": 0,
                        }
            
            scored_artists = sorted(artist_scores.values(), key=lambda x: (-x["score"], x["artist"].get("name", "") if x["artist"] else ""))
            
            artists_list = [
                {
                    "id": a["artist"].get("id") if a["artist"] else None,
                    "name": a["artist"].get("name") if a["artist"] else "Unknown",
                    "images": a["artist"].get("images", []) if a["artist"] else [],
                    "track_count": a["track_count"],
                    "score": a["score"],
                }
                for a in scored_artists
            ]
            
            if artists_cache is None:
                artists_cache = {}
            artists_cache[time_range] = {"artists": artists_list}
        
        artist_data = {"artists": artists_list}
        
        time_range_labels = {
            "recent": "Recent",
            "short_term": "4 Weeks",
            "medium_term": "6 Months",
            "long_term": "All Time",
        }
        display_label = time_range_labels.get(time_range, "4 Weeks")
        
        btn_recent = "time-range-btn active" if time_range == "recent" else "time-range-btn"
        btn_4weeks = "time-range-btn active" if time_range == "short_term" else "time-range-btn"
        btn_6months = "time-range-btn active" if time_range == "medium_term" else "time-range-btn"
        btn_alltime = "time-range-btn active" if time_range == "long_term" else "time-range-btn"
        btn_4 = "time-range-btn active" if count == 4 else "time-range-btn"
        btn_12 = "time-range-btn active" if count == 12 else "time-range-btn"
        btn_all = "time-range-btn active" if count == 50 else "time-range-btn"
        
        content = spotidash.layout_builder.build_top_artists(artist_data, display_label, count)
        
        return content, artist_data, btn_recent, btn_4weeks, btn_6months, btn_alltime, btn_4, btn_12, btn_all, filter_state, artists_cache
