from dash.dependencies import Input, Output, State, ALL
import dash
import dash.html as html
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ..utils.stats import extract_listening_time_distribution, aggregate_genres, extract_duration_distribution


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
        Output("top-artists-cache", "data"),
        Input("tracks-prefetch-interval", "n_intervals"),
        Input("url", "pathname"),
        State("top-tracks-cache", "data"),
        State("top-artists-cache", "data"),
        prevent_initial_call=True,
    )
    def prefetch_top_tracks(n_intervals, pathname, tracks_cache, artists_cache):
        # Guard clause: require authentication
        if not spotidash.is_authenticated():
            return dash.no_update, dash.no_update
        
        # Initialize caches if None (Fail Fast: ensure valid state)
        if tracks_cache is None:
            tracks_cache = {"recent": None, "short_term": None, "medium_term": None, "long_term": None}
        if artists_cache is None:
            artists_cache = {}
        
        # Determine which time range to fetch next
        loaded_tracks = [k for k, v in tracks_cache.items() if v is not None]
        time_ranges = ["recent", "short_term", "medium_term", "long_term"]
        next_range = None
        for tr in time_ranges:
            if tr not in loaded_tracks:
                next_range = tr
                break
        
        # All ranges loaded, return current state
        if next_range is None:
            return tracks_cache, artists_cache
        
        # Fetch tracks for the next range with error handling
        try:
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
                    tracks_cache[next_range] = {"items": [t["track"] for t in sorted_tracks[:50]]}
                else:
                    tracks_cache[next_range] = {"items": []}
            else:
                data = spotidash.get_top_tracks(limit=50, time_range=next_range)
                tracks_cache[next_range] = data if data else {"items": []}
        except Exception:
            # Fail Fast: on API error, preserve existing cache and return
            return tracks_cache, artists_cache
        
        # Derive or fetch artists for the same range with error handling
        try:
            if next_range == "recent":
                # Derive artists from tracks for "recent" range
                recent_tracks = tracks_cache.get("recent", {}).get("items", [])
                artist_scores = {}
                for idx, track in enumerate(recent_tracks):
                    score = 51 - (idx + 1)
                    for artist in track.get("artists", []):
                        artist_id = artist.get("id")
                        if artist_id:
                            if artist_id not in artist_scores:
                                # Initialize with empty genres (tracks don't have genre data)
                                artist_with_genres = dict(artist)
                                artist_with_genres["genres"] = []
                                artist_scores[artist_id] = {"artist": artist_with_genres, "score": 0, "track_count": 0}
                            artist_scores[artist_id]["score"] += score
                            artist_scores[artist_id]["track_count"] += 1
                
                # Copy images from other ranges if missing
                for artist_id, artist_data in artist_scores.items():
                    images = artist_data["artist"].get("images", [])
                    if not images:
                        for other_range in ["short_term", "medium_term", "long_term"]:
                            other_data = artists_cache.get(other_range, {}).get("artists", [])
                            for other_artist in other_data:
                                if other_artist.get("id") == artist_id:
                                    other_images = other_artist.get("images", [])
                                    if other_images:
                                        artist_data["artist"]["images"] = other_images
                                        break
                            if artist_data["artist"].get("images"):
                                break
                
                sorted_artists = sorted(artist_scores.values(), key=lambda x: (-x["score"], x["artist"].get("name", "") if x["artist"] else ""))
                
                artists_list = [
                    {
                        "id": a["artist"].get("id") if a["artist"] else None,
                        "name": a["artist"].get("name") if a["artist"] else "Unknown",
                        "images": a["artist"].get("images", []) if a["artist"] else [],
                        "genres": a["artist"].get("genres", []) if a["artist"] else [],
                        "track_count": a["track_count"],
                        "score": a["score"],
                    }
                    for a in sorted_artists
                ]
                
                artists_cache["recent"] = {"artists": artists_list}
            else:
                # Fetch artists from API for standard time ranges
                artists_data = spotidash.get_top_artists(limit=50, time_range=next_range)
                if artists_data and artists_data.get("items"):
                    # Get track scores from cached tracks for this range
                    tracks_items = tracks_cache.get(next_range, {}).get("items", [])
                    track_artist_scores = {}
                    for idx, track in enumerate(tracks_items):
                        score = 51 - (idx + 1)
                        for artist in track.get("artists", []):
                            artist_id = artist.get("id")
                            if artist_id:
                                if artist_id not in track_artist_scores:
                                    track_artist_scores[artist_id] = {"score": 0, "track_count": 0}
                                track_artist_scores[artist_id]["score"] += score
                                track_artist_scores[artist_id]["track_count"] += 1
                    
                    artists_list = [
                        {
                            "id": artist.get("id"),
                            "name": artist.get("name", "Unknown"),
                            "images": artist.get("images", []),
                            "genres": artist.get("genres", []),
                            "track_count": track_artist_scores.get(artist.get("id"), {}).get("track_count", 0),
                            "score": track_artist_scores.get(artist.get("id"), {}).get("score", 0),
                        }
                        for artist in artists_data["items"]
                    ]
                    artists_cache[next_range] = {"artists": artists_list}
                else:
                    artists_cache[next_range] = {"artists": []}
        except Exception:
            # Fail Fast: on API error, preserve existing cache and return
            return tracks_cache, artists_cache
        
        # Atomic Predictability: return new cache state, don't mutate
        return tracks_cache, artists_cache

    @app.callback(
        Output("recently-played-cache", "data"),
        Input("tracks-prefetch-interval", "n_intervals"),
        State("recently-played-cache", "data"),
        prevent_initial_call=True,
    )
    def prefetch_recently_played(n_intervals, recently_played_cache):
        if not spotidash.is_authenticated():
            return dash.no_update
        
        # Only fetch once - check if cache already has data
        if recently_played_cache and recently_played_cache.get("items"):
            return dash.no_update
        
        data = spotidash.get_recently_played(limit=50)
        if data:
            # Store raw data with played_at timestamps
            return {
                "items": [
                    {"track": item.get("track", {}), "played_at": item.get("played_at")}
                    for item in data.get("items", [])
                ]
            }
        
        return {"items": []}

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
        
        if filter_state is None:
            filter_state = {"time_range": "short_term", "count": 12}
        
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
            except Exception:
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
        Output("btn-artist-count-24", "className"),
        Output("artist-filter-store", "data"),
        Output("top-artists-cache", "data", allow_duplicate=True),
        Input("btn-artist-recent", "n_clicks"),
        Input("btn-artist-4weeks", "n_clicks"),
        Input("btn-artist-6months", "n_clicks"),
        Input("btn-artist-alltime", "n_clicks"),
        Input("btn-artist-count-4", "n_clicks"),
        Input("btn-artist-count-12", "n_clicks"),
        Input("btn-artist-count-24", "n_clicks"),
        Input("url", "pathname"),
        State("top-artists-store", "data"),
        State("artist-filter-store", "data"),
        State("top-artists-cache", "data"),
        State("top-tracks-cache", "data"),
        prevent_initial_call='initial_duplicate',
    )
    def update_top_artists(n_recent, n_4weeks, n_6months, n_alltime, n_4, n_12, n_24, pathname, store_data, filter_state, artists_cache, tracks_cache):
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
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
            "btn-artist-count-24": 24,
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
            return "", None, "time-range-btn", "time-range-btn", "time-range-btn", "time-range-btn", "time-range-btn", "time-range-btn", "time-range-btn", filter_state, artists_cache
        
        cached_data = artists_cache.get(time_range) if artists_cache else None
        
        if cached_data is not None:
            artists_list = cached_data.get("artists", [])
            if time_range == "recent":
                for artist in artists_list:
                    if not artist.get("images"):
                        artist_id = artist.get("id")
                        for other_range in ["short_term", "medium_term", "long_term"]:
                            other_data = artists_cache.get(other_range, {}).get("artists", []) if artists_cache else []
                            for other_artist in other_data:
                                if other_artist.get("id") == artist_id:
                                    other_images = other_artist.get("images", [])
                                    if other_images:
                                        artist["images"] = other_images
                                        break
                            if artist.get("images"):
                                break
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
            
            artist_scores = {}
            
            if time_range == "recent":
                for artist_id, data in track_artist_scores.items():
                    images = data["artist_obj"].get("images", [])
                    if not images:
                        for other_range in ["short_term", "medium_term", "long_term"]:
                            other_data = artists_cache.get(other_range, {}).get("artists", []) if artists_cache else []
                            for other_artist in other_data:
                                if other_artist.get("id") == artist_id:
                                    other_images = other_artist.get("images", [])
                                    if other_images:
                                        data["artist_obj"]["images"] = other_images
                                        break
                            if data["artist_obj"].get("images"):
                                break
                    artist_scores[artist_id] = {
                        "artist": data["artist_obj"],
                        "score": data["score"],
                        "track_count": data["track_count"],
                    }
            else:
                top_artists = spotidash.get_top_artists(limit=42, time_range=time_range)
                
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
                    "genres": a["artist"].get("genres", []) if a["artist"] else [],
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
        btn_24 = "time-range-btn active" if count == 24 else "time-range-btn"
        
        content = spotidash.layout_builder.build_top_artists(artist_data, display_label, count)
        
        return content, artist_data, btn_recent, btn_4weeks, btn_6months, btn_alltime, btn_4, btn_12, btn_24, filter_state, artists_cache

    # =============================================================================
    # Stats Panel Callbacks
    # =============================================================================

    # =============================================================================
    # Stats Panel Callbacks
    # =============================================================================

    @app.callback(
        Output("genre-filter-store", "data"),
        Output("btn-genre-4weeks", "className"),
        Output("btn-genre-6months", "className"),
        Output("btn-genre-alltime", "className"),
        Input("btn-genre-4weeks", "n_clicks"),
        Input("btn-genre-6months", "n_clicks"),
        Input("btn-genre-alltime", "n_clicks"),
        State("genre-filter-store", "data"),
        prevent_initial_call=True,
    )
    def toggle_genre_time_range(n_4weeks, n_6months, n_alltime, filter_state):
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update

        if filter_state is None:
            filter_state = {"time_range": "medium_term"}

        time_range = filter_state.get("time_range", "medium_term")

        time_ranges = {
            "btn-genre-4weeks": "short_term",
            "btn-genre-6months": "medium_term",
            "btn-genre-alltime": "long_term",
        }

        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if triggered_id in time_ranges:
            time_range = time_ranges[triggered_id]

        filter_state = {"time_range": time_range}

        btn_4weeks = "time-range-btn active" if time_range == "short_term" else "time-range-btn"
        btn_6months = "time-range-btn active" if time_range == "medium_term" else "time-range-btn"
        btn_alltime = "time-range-btn active" if time_range == "long_term" else "time-range-btn"

        return filter_state, btn_4weeks, btn_6months, btn_alltime

    # =============================================================================
    # Individual Graph Callbacks
    # =============================================================================

    @app.callback(
        Output("listening-time-container", "children"),
        Input("recently-played-cache", "data"),
    )
    def update_listening_time_graph(recently_played):
        if not recently_played:
            return html.Div(
                "No listening data available",
                style={"color": "#888888", "textAlign": "center", "padding": "40px"}
            )
        return render_listening_time_graph(recently_played)

    @app.callback(
        Output("genre-stats-container", "children"),
        Input("top-artists-cache", "data"),
        Input("genre-filter-store", "data"),
    )
    def update_genre_stats_graph(artists_cache, genre_filter):
        import logging
        logger = logging.getLogger(__name__)

        logger.debug("[Genre Debug] update_genre_stats_graph called")
        logger.debug(f"[Genre Debug] artists_cache keys: {list(artists_cache.keys()) if artists_cache else 'None'}")
        logger.debug(f"[Genre Debug] genre_filter: {genre_filter}")

        # Guard clause: Cache not loaded yet (initial load state)
        if not artists_cache:
            logger.warning("[Genre Debug] artists_cache is empty/None - still loading")
            return html.Div(
                "Loading artist data...",
                style={"color": "#888888", "textAlign": "center", "padding": "40px"}
            )

        # Guard clause: Cache exists but is empty dict (edge case)
        if not isinstance(artists_cache, dict) or len(artists_cache) == 0:
            logger.warning("[Genre Debug] artists_cache is invalid or empty")
            return html.Div(
                "Loading artist data...",
                style={"color": "#888888", "textAlign": "center", "padding": "40px"}
            )

        # Determine which time range we need to check
        time_range = genre_filter.get("time_range", "medium_term") if genre_filter else "medium_term"

        # Guard clause: Cache loaded but specific time_range not yet populated
        if time_range not in artists_cache:
            logger.warning(f"[Genre Debug] artists_cache loaded but '{time_range}' not yet available")
            return html.Div(
                "Loading artist data...",
                style={"color": "#888888", "textAlign": "center", "padding": "40px"}
            )

        # Cache is loaded and time_range exists - render the graph
        return render_genre_graph(artists_cache, genre_filter)

    @app.callback(
        Output("duration-container", "children"),
        Input("top-tracks-cache", "data"),
    )
    def update_duration_graph(tracks_cache):
        if not tracks_cache:
            return html.Div(
                "No track data available",
                style={"color": "#888888", "textAlign": "center", "padding": "40px"}
            )
        return render_duration_histogram(tracks_cache)

    @app.callback(
        Output("playlist-view-store", "data"),
        Output("btn-playlist-treemap", "className"),
        Output("btn-playlist-donut", "className"),
        Input("btn-playlist-treemap", "n_clicks"),
        Input("btn-playlist-donut", "n_clicks"),
        State("playlist-view-store", "data"),
        prevent_initial_call=True,
    )
    def toggle_playlist_view(n_treemap, n_donut, view_state):
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update

        if view_state is None:
            view_state = {"view": "treemap"}

        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if triggered_id == "btn-playlist-treemap":
            view_state = {"view": "treemap"}
        elif triggered_id == "btn-playlist-donut":
            view_state = {"view": "donut"}

        btn_treemap = "time-range-btn active" if view_state["view"] == "treemap" else "time-range-btn"
        btn_donut = "time-range-btn active" if view_state["view"] == "donut" else "time-range-btn"

        return view_state, btn_treemap, btn_donut

    @app.callback(
        Output("playlists-cache", "data"),
        Input("tracks-prefetch-interval", "n_intervals"),
        State("playlists-cache", "data"),
        prevent_initial_call=True,
    )
    def prefetch_playlists(n_intervals, playlists_cache):
        import logging
        logger = logging.getLogger(__name__)

        # Only fetch once - check if cache already has data
        if playlists_cache:
            logger.debug(f"[Playlist Debug] Cache exists with {len(playlists_cache)} items, skipping fetch")
            return dash.no_update

        if not spotidash.is_authenticated():
            logger.debug("[Playlist Debug] Not authenticated, skipping fetch")
            return dash.no_update

        try:
            playlists = spotidash.get_playlists(limit=50)
            logger.debug(f"[Playlist Debug] Fetched {len(playlists) if playlists else 0} playlists")

            if playlists:
                # Log first few playlists for debugging
                for i, p in enumerate(playlists[:3]):
                    logger.debug(f"[Playlist Debug] Playlist {i}: name='{p.get('name')}', track_count={p.get('track_count')}, type={type(p.get('track_count'))}")

            return playlists if playlists else []
        except Exception as e:
            logger.error(f"[Playlist Debug] Error fetching playlists: {e}")
            return []

    @app.callback(
        Output("playlists-container", "children"),
        Input("playlists-cache", "data"),
        Input("playlist-view-store", "data"),
    )
    def update_playlists_graph(playlists_data, view_state):
        if not playlists_data:
            return html.Div(
                "No playlist data available",
                style={"color": "#888888", "textAlign": "center", "padding": "40px"}
            )

        view = view_state.get("view", "treemap") if view_state else "treemap"

        if view == "treemap":
            return render_playlist_treemap(playlists_data)
        else:
            return render_playlist_donut(playlists_data)

    # =============================================================================
    # Stats Graph Helper Functions
    # =============================================================================

    def render_listening_time_graph(recently_played):
        if not recently_played or not recently_played.get("items"):
            return html.Div(
                "No listening history available",
                style={"color": "#888888", "textAlign": "center", "padding": "40px"}
            )
        
        distribution = extract_listening_time_distribution(recently_played)
        if not distribution:
            return html.Div(
                "Unable to analyze listening patterns",
                style={"color": "#888888", "textAlign": "center", "padding": "40px"}
            )
        
        hour_dist = distribution.get("hour_distribution", {})
        day_dist = distribution.get("day_distribution", {})
        
        hours = list(range(24))
        hour_values = [hour_dist.get(h, 0) for h in hours]
        
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_values = [day_dist.get(d, 0) for d in range(7)]
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Listening by Hour of Day', 'Listening by Day of Week'),
            vertical_spacing=0.15,
        )
        
        fig.add_trace(
            go.Bar(
                x=hours,
                y=hour_values,
                marker_color='#4A90D9',
                name='Hourly',
                hovertemplate='Hour %{x}:00<br>%{y} plays<extra></extra>',
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=days,
                y=day_values,
                marker_color='#6BA3E0',
                name='Daily',
                hovertemplate='%{x}<br>%{y} plays<extra></extra>',
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            paper_bgcolor='#1E1E1E',
            plot_bgcolor='#1E1E1E',
            showlegend=False,
            margin=dict(l=50, r=20, t=60, b=40),
            title=dict(
                text='When You Listen to Music',
                font=dict(color='#F0F0F0', size=16),
                x=0.5,
            ),
        )
        
        fig.update_xaxes(
            tickfont=dict(color='#888888', size=10),
            gridcolor='rgba(255, 255, 255, 0.05)',
            linecolor='rgba(255, 255, 255, 0.1)',
        )
        fig.update_yaxes(
            tickfont=dict(color='#888888', size=10),
            gridcolor='rgba(255, 255, 255, 0.1)',
            linecolor='rgba(255, 255, 255, 0.1)',
            title_text='Plays',
            title_font=dict(color='#888888', size=10),
        )
        
        fig.update_annotations(font=dict(color='#F0F0F0', size=12))
        
        return html.Div([
            dash.dcc.Graph(
                figure=fig,
                config={'displayModeBar': False},
                style={'height': '500px'}
            ),
            html.P(
                "Based on last 50 tracks (Spotify API limit)",
                style={"color": "#888888", "fontSize": "11px", "textAlign": "center", "marginTop": "8px"}
            ),
        ], style={'backgroundColor': '#1E1E1E', 'borderRadius': '12px', 'padding': '16px'})

    def render_genre_graph(artists_cache, filter_state):
        import logging
        logger = logging.getLogger(__name__)

        time_range = filter_state.get("time_range", "medium_term") if filter_state else "medium_term"

        # Debug logging to trace data flow
        logger.debug(f"[Genre Debug] filter_state: {filter_state}")
        logger.debug(f"[Genre Debug] time_range: {time_range}")
        logger.debug(f"[Genre Debug] artists_cache keys: {list(artists_cache.keys()) if artists_cache else 'None'}")
        logger.debug(f"[Genre Debug] artists_cache type: {type(artists_cache)}")

        # Guard clause: Cache not loaded yet
        if not artists_cache:
            logger.warning("[Genre Debug] No artists_cache provided")
            return html.Div(
                "Loading artist data...",
                style={"color": "#888888", "textAlign": "center", "padding": "40px"}
            )

        artists_data = artists_cache.get(time_range)

        logger.debug(f"[Genre Debug] artists_data for '{time_range}': {type(artists_data)}")
        if artists_data:
            logger.debug(f"[Genre Debug] artists_data keys: {list(artists_data.keys()) if isinstance(artists_data, dict) else 'N/A'}")
            if isinstance(artists_data, dict):
                artists_list = artists_data.get("artists", [])
                logger.debug(f"[Genre Debug] artists_list length: {len(artists_list)}")
                if artists_list:
                    logger.debug(f"[Genre Debug] First artist sample: {artists_list[0].get('name') if isinstance(artists_list[0], dict) else 'N/A'}")

        # Guard clause: No artists data for this time range
        if not artists_data:
            logger.warning(f"[Genre Debug] No artists_data for time_range '{time_range}' - cache not yet populated for this range")
            return html.Div(
                "Loading artist data...",
                style={"color": "#888888", "textAlign": "center", "padding": "40px"}
            )

        # Guard clause: Empty artists list (API returned no artists for this range)
        artists_list = artists_data.get("artists", []) if isinstance(artists_data, dict) else []
        if not artists_list:
            logger.warning(f"[Genre Debug] Empty artists list for time_range '{time_range}'")
            return html.Div(
                "No artists found for this time range",
                style={"color": "#888888", "textAlign": "center", "padding": "40px"}
            )

        top_genres = aggregate_genres(artists_data)

        # Guard clause: Artists exist but no genre classifications
        if not top_genres:
            logger.warning("[Genre Debug] No genre data available - artists not yet classified")
            return html.Div([
                html.P("No genre data available", style={
                    "color": "#F0F0F0",
                    "fontSize": "16px",
                    "marginBottom": "8px",
                    "fontWeight": "500"
                }),
                html.P("Spotify hasn't classified these artists yet.", style={
                    "color": "#888888",
                    "fontSize": "12px",
                    "marginBottom": "4px"
                }),
                html.P("Try a different time range or check back later.", style={
                    "color": "#888888",
                    "fontSize": "12px"
                }),
            ], style={"textAlign": "center", "padding": "40px"})
        
        genres = [g[0].title() for g in top_genres]
        counts = [g[1] for g in top_genres]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=counts,
            y=genres,
            orientation='h',
            marker=dict(
                color='#4A90D9',
                line=dict(color='#6BA3E0', width=1)
            ),
            hovertemplate='%{y}<br>%{x} artists<extra></extra>',
        ))
        
        fig.update_layout(
            paper_bgcolor='#1E1E1E',
            plot_bgcolor='#1E1E1E',
            margin=dict(l=120, r=20, t=60, b=40),
            title=dict(
                text='Your Top Genres',
                font=dict(color='#F0F0F0', size=16),
                x=0.5,
            ),
            xaxis=dict(
                title=dict(text='Number of Artists', font=dict(color='#888888', size=10)),
                tickfont=dict(color='#888888', size=10),
                gridcolor='rgba(255, 255, 255, 0.1)',
                linecolor='rgba(255, 255, 255, 0.1)',
            ),
            yaxis=dict(
                tickfont=dict(color='#F0F0F0', size=11),
                gridcolor='rgba(255, 255, 255, 0.05)',
                linecolor='rgba(255, 255, 255, 0.1)',
                autorange='reversed',
            ),
        )
        
        return html.Div(
            dash.dcc.Graph(
                figure=fig,
                config={'displayModeBar': False},
                style={'height': '400px'}
            ),
            style={'backgroundColor': '#1E1E1E', 'borderRadius': '12px', 'padding': '16px'}
        )

    def render_duration_histogram(tracks_cache):
        """Render a histogram of track duration distribution."""
        duration_data = extract_duration_distribution(tracks_cache)

        if not duration_data:
            return html.Div(
                "Unable to analyze track durations",
                style={"color": "#888888", "textAlign": "center", "padding": "40px"}
            )

        durations = duration_data.get("durations_seconds", [])
        avg_seconds = duration_data.get("avg_seconds", 0)

        if not durations:
            return html.Div(
                "No valid duration data found",
                style={"color": "#888888", "textAlign": "center", "padding": "40px"}
            )

        # Create histogram figure
        fig = go.Figure()

        # Add histogram trace
        fig.add_trace(go.Histogram(
            x=durations,
            nbinsx=20,
            marker=dict(
                color='#4A90D9',
                line=dict(color='#6BA3E0', width=1)
            ),
            hovertemplate='%{x:.0f}s - %{xbin:.0f}s<br>%{y} tracks<extra></extra>',
        ))

        # Add vertical line for average (dashed, white)
        fig.add_vline(
            x=avg_seconds,
            line=dict(color='#F0F0F0', width=2, dash='dash'),
            annotation_text=f"Avg: {avg_seconds/60:.1f}min",
            annotation_position="top",
            annotation_font=dict(color='#F0F0F0', size=11),
        )

        # Add vertical lines for 3min and 4min (dotted, gray)
        fig.add_vline(
            x=180,
            line=dict(color='#888888', width=1, dash='dot'),
            annotation_text="3 min",
            annotation_position="bottom",
            annotation_font=dict(color='#888888', size=10),
        )
        fig.add_vline(
            x=240,
            line=dict(color='#888888', width=1, dash='dot'),
            annotation_text="4 min",
            annotation_position="bottom",
            annotation_font=dict(color='#888888', size=10),
        )

        # Update layout with dark theme
        fig.update_layout(
            paper_bgcolor='#1E1E1E',
            plot_bgcolor='#1E1E1E',
            margin=dict(l=50, r=20, t=60, b=50),
            title=dict(
                text='Track Duration Distribution',
                font=dict(color='#F0F0F0', size=16),
                x=0.5,
            ),
            xaxis=dict(
                title=dict(text='Duration (seconds)', font=dict(color='#888888', size=10)),
                tickfont=dict(color='#888888', size=10),
                gridcolor='rgba(255, 255, 255, 0.05)',
                linecolor='rgba(255, 255, 255, 0.1)',
            ),
            yaxis=dict(
                title=dict(text='Number of Tracks', font=dict(color='#888888', size=10)),
                tickfont=dict(color='#888888', size=10),
                gridcolor='rgba(255, 255, 255, 0.1)',
                linecolor='rgba(255, 255, 255, 0.1)',
            ),
            showlegend=False,
        )

        # Build stats summary
        stats_text = (
            f"Min: {duration_data['min_seconds']/60:.1f}min | "
            f"Max: {duration_data['max_seconds']/60:.1f}min | "
            f"Avg: {duration_data['avg_seconds']/60:.1f}min | "
            f"Median: {duration_data['median_seconds']/60:.1f}min | "
            f"Tracks: {duration_data['total_tracks']}"
        )

        return html.Div([
            dash.dcc.Graph(
                figure=fig,
                config={'displayModeBar': False},
                style={'height': '350px'}
            ),
            html.P(
                stats_text,
                style={
                    "color": "#888888",
                    "fontSize": "11px",
                    "textAlign": "center",
                    "marginTop": "8px"
                }
            ),
        ], style={'backgroundColor': '#1E1E1E', 'borderRadius': '12px', 'padding': '16px'})

    def render_playlist_treemap(playlists):
        """Render a treemap showing playlists sized by track count."""
        import logging
        logger = logging.getLogger(__name__)

        # Guard clause: validate input data
        if not playlists:
            logger.debug("[Treemap Debug] No playlists provided")
            return html.Div(
                "No playlist data available",
                style={"color": "#888888", "textAlign": "center", "padding": "40px"}
            )

        # Prepare data for treemap
        names = [p.get("name", "Untitled") for p in playlists]
        values = [p.get("track_count", 0) for p in playlists]

        logger.debug(f"[Treemap Debug] Processing {len(names)} playlists")
        logger.debug(f"[Treemap Debug] Names: {names[:5]}...")  # Log first 5
        logger.debug(f"[Treemap Debug] Values: {values[:5]}...")  # Log first 5

        # Guard clause: validate extracted data
        if not names or not values or len(names) != len(values):
            logger.warning(f"[Treemap Debug] Invalid data: names={len(names)}, values={len(values)}")
            return html.Div(
                "No valid playlist data",
                style={"color": "#888888", "textAlign": "center", "padding": "40px"}
            )

        # Filter out playlists with 0 tracks to avoid rendering issues
        valid_playlists = [p for p in playlists if p.get("track_count", 0) > 0]
        if not valid_playlists:
            logger.warning("[Treemap Debug] All playlists have 0 tracks")
            return html.Div(
                "No playlists with tracks to display",
                style={"color": "#888888", "textAlign": "center", "padding": "40px"}
            )

        # Extract data from filtered playlists
        names = [p.get("name", "Untitled") for p in valid_playlists]
        values = [p.get("track_count", 0) for p in valid_playlists]
        # Parents must be empty strings for a flat treemap (no hierarchy)
        parents = [""] * len(names)

        # Prepare custom data for hovertemplate
        owners = []
        descriptions = []
        spotify_urls = []

        for p in valid_playlists:
            owner = p.get("owner", {})
            owner_name = owner.get("display_name") or owner.get("id", "Unknown")
            owners.append(owner_name)

            desc = p.get("description")
            descriptions.append(desc if desc else "No description")

            url = p.get("spotify_url") or p.get("uri", "")
            spotify_urls.append(url if url else "No link")

        customdata = list(zip(owners, descriptions, spotify_urls))

        logger.debug(f"[Treemap Debug] Creating treemap with {len(names)} items")

        fig = go.Figure(go.Treemap(
            labels=names,
            values=values,
            parents=parents,
            customdata=customdata,
            textinfo="label",
            texttemplate="<b>%{label}</b><br>Track count: %{value}",
            textfont=dict(
                color='#F0F0F0',
                size=14,
                family='Inter, -apple-system, BlinkMacSystemFont, sans-serif'
            ),
            marker=dict(
                colors=['#4A90D9', '#5B9FE3', '#6CAEED', '#7DBDF7',
                        '#3A7BC8', '#2B6AB7', '#1C59A6', '#0D4895',
                        '#5AA3DC', '#6BB2E6', '#7CC1F0', '#8DD0FA'],
                line=dict(color='#1E1E1E', width=2),
            ),
            hovertemplate=(
                '<b>%{label}</b><br>'
                'Track count: %{value}<br>'
                'Owner: %{customdata[0]}<br>'
                'Description: %{customdata[1]}<br>'
                'Spotify: %{customdata[2]}<extra></extra>'
            ),
        ))

        fig.update_layout(
            paper_bgcolor='#1E1E1E',
            plot_bgcolor='#1E1E1E',
            margin=dict(l=10, r=10, t=40, b=10),
            title=dict(
                text='Your Playlists (by Track Count)',
                font=dict(color='#F0F0F0', size=14),
                x=0.5,
            ),
        )

        return dash.dcc.Graph(
            figure=fig,
            config={'displayModeBar': False},
            style={'height': '400px'}
        )

    def render_playlist_donut(playlists):
        """Render a donut chart showing distribution of playlist sizes."""
        import logging
        logger = logging.getLogger(__name__)

        logger.debug(f"[Donut Debug] Received playlists: {len(playlists) if playlists else 0} items")

        if not playlists:
            return html.Div(
                "No playlist data available",
                style={"color": "#888888", "textAlign": "center", "padding": "40px"}
            )

        # Log sample data for debugging
        for i, p in enumerate(playlists[:5]):
            logger.debug(f"[Donut Debug] Playlist {i}: {p.get('name')} - track_count={p.get('track_count')} (type: {type(p.get('track_count'))})")

        # Categorize playlists by size
        size_categories = {
            "Small (< 25)": 0,
            "Medium (25-50)": 0,
            "Large (50-100)": 0,
            "Very Large (100-200)": 0,
            "Massive (200+)": 0,
        }

        for playlist in playlists:
            track_count = playlist.get("track_count", 0)
            # Ensure track_count is an integer
            try:
                track_count = int(track_count) if track_count is not None else 0
            except (ValueError, TypeError):
                logger.warning(f"[Donut Debug] Invalid track_count for '{playlist.get('name')}': {track_count}")
                track_count = 0

            if track_count < 25:
                size_categories["Small (< 25)"] += 1
            elif track_count < 50:
                size_categories["Medium (25-50)"] += 1
            elif track_count < 100:
                size_categories["Large (50-100)"] += 1
            elif track_count < 200:
                size_categories["Very Large (100-200)"] += 1
            else:
                size_categories["Massive (200+)"] += 1

        logger.debug(f"[Donut Debug] Categorized: {size_categories}")

        # Ensure labels are in correct order: Small → Massive
        labels = ["Small (< 25)", "Medium (25-50)", "Large (50-100)", "Very Large (100-200)", "Massive (200+)"]
        values = [
            size_categories["Small (< 25)"],
            size_categories["Medium (25-50)"],
            size_categories["Large (50-100)"],
            size_categories["Very Large (100-200)"],
            size_categories["Massive (200+)"]
        ]

        if sum(values) == 0:
            return html.Div(
                "No valid playlist data",
                style={"color": "#888888", "textAlign": "center", "padding": "40px"}
            )

        # Darker blues for better contrast with white text (Small → Massive)
        colors = ['#1E3A5F', '#2B6AB7', '#4A90D9', '#6CAEED', '#8DCCFF']

        fig = go.Figure(go.Pie(
            labels=labels,
            values=values,
            hole=0.6,
            marker=dict(colors=colors, line=dict(color='#1E1E1E', width=2)),
            textinfo='label+percent',
            textfont=dict(color='#F0F0F0', size=11),
            hovertemplate='<b>%{label}</b><br>%{value} playlists<br>%{percent}<extra></extra>',
        ))

        fig.update_layout(
            paper_bgcolor='#1E1E1E',
            plot_bgcolor='#1E1E1E',
            margin=dict(l=20, r=20, t=50, b=20),
            title=dict(
                text='Playlist Size Distribution',
                font=dict(color='#F0F0F0', size=14),
                x=0.5,
            ),
            showlegend=True,
            legend=dict(
                font=dict(color='#888888', size=10),
                orientation='h',
                yanchor='bottom',
                y=-0.15,
                xanchor='center',
                x=0.5,
                traceorder='normal',  # Ensure legend follows label order
            ),
        )

        # Add center text with total count
        total_playlists = len(playlists)
        fig.add_annotation(
            text=f"<b>{total_playlists}</b><br>Playlists",
            x=0.5, y=0.5,
            font=dict(size=16, color='#F0F0F0'),
            showarrow=False,
        )

        return dash.dcc.Graph(
            figure=fig,
            config={'displayModeBar': False},
            style={'height': '400px'}
        )
