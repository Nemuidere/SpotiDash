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
            dcc.Store(id="now-playing-store", data=None),
            dcc.Store(id="top-tracks-store", data=None),
            dcc.Store(id="top-artists-store", data=None),
            dcc.Store(id="favourites-store", data=[]),
            dcc.Store(id="filter-state-store", data={"time_range": "medium_term", "count": 50, "show_favourites_only": False}),
            dcc.Store(id="artist-filter-store", data={"time_range": "short_term", "count": 12}),
            dcc.Interval(id="now-playing-interval", interval=5000),
            dcc.Store(id="visibility-store", data=True),
            dcc.Interval(id="progress-interval", interval=1000),
            dcc.Store(id="top-tracks-cache", data=None),
            dcc.Interval(id="tracks-prefetch-interval", interval=1000, max_intervals=8),
            dcc.Store(id="top-artists-cache", data=None),
            dcc.Store(id="genre-filter-store", data={"time_range": "medium_term"}),
            dcc.Store(id="recently-played-cache", data=None),
            dcc.Store(id="playlists-cache", data=None),
            dcc.Store(id="playlist-view-store", data={"view": "treemap"}),
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
        # Hidden buttons for Dash callback validation (dashboard buttons).
        # These placeholders let the Top Tracks / Top Artists callbacks — which
        # run on initial load — resolve their button Inputs while the login
        # screen is shown, before the real dashboard buttons exist.
        html.Div([
            html.Button(id="btn-time-recent", style={"display": "none"}),
            html.Button(id="btn-time-4weeks", style={"display": "none"}),
            html.Button(id="btn-time-6months", style={"display": "none"}),
            html.Button(id="btn-time-alltime", style={"display": "none"}),
            html.Button(id="btn-count-10", style={"display": "none"}),
            html.Button(id="btn-count-25", style={"display": "none"}),
            html.Button(id="btn-count-50", style={"display": "none"}),
            html.Button(id="btn-favourites-only", style={"display": "none"}),
            html.Button(id="btn-artist-recent", style={"display": "none"}),
            html.Button(id="btn-artist-4weeks", style={"display": "none"}),
            html.Button(id="btn-artist-6months", style={"display": "none"}),
            html.Button(id="btn-artist-alltime", style={"display": "none"}),
            html.Button(id="btn-artist-count-4", style={"display": "none"}),
            html.Button(id="btn-artist-count-12", style={"display": "none"}),
            html.Button(id="btn-artist-count-24", style={"display": "none"}),
        ], style={"display": "none"}),
        # Hidden container placeholders. The content/graph callbacks run on
        # initial load and every interval tick; without these output targets on
        # the login screen, Dash retries them forever and logs "nonexistent
        # object in an Output" each second. The real containers live in the
        # dashboard, which is mutually exclusive with the login page (no dup ids).
        html.Div([
            html.Div(id="top-tracks-container"),
            html.Div(id="top-artists-container"),
            html.Div(id="now-playing-bar"),
            html.Div(id="listening-time-container"),
            html.Div(id="genre-stats-container"),
            html.Div(id="duration-container"),
            html.Div(id="playlists-container"),
        ], style={"display": "none"}),
        ])

    def build_dashboard_columns(self, user=None):
        # Build Top Tracks block
        top_tracks_block = html.Div([
            html.H3("Top Tracks", style={
                "fontSize": "18px",
                "fontWeight": "600",
                "margin": "0 0 16px 0",
            }),
            html.Div([
                html.Button(
                    "Recent",
                    id="btn-time-recent",
                    n_clicks=0,
                    className="time-range-btn"
                ),
                html.Button(
                    "4 Weeks",
                    id="btn-time-4weeks",
                    n_clicks=0,
                    className="time-range-btn"
                ),
                html.Button(
                    "6 Months",
                    id="btn-time-6months",
                    n_clicks=0,
                    className="time-range-btn"
                ),
                html.Button(
                    "All Time",
                    id="btn-time-alltime",
                    n_clicks=0,
                    className="time-range-btn"
                ),
            ], style={
                "display": "flex",
                "gap": "8px",
                "marginBottom": "16px",
            }),
            html.Div([
                html.Button(
                    "10",
                    id="btn-count-10",
                    n_clicks=0,
                    className="time-range-btn"
                ),
                html.Button(
                    "25",
                    id="btn-count-25",
                    n_clicks=0,
                    className="time-range-btn"
                ),
                html.Button(
                    "50",
                    id="btn-count-50",
                    n_clicks=0,
                    className="time-range-btn"
                ),
            ], style={
                "display": "flex",
                "gap": "8px",
                "marginBottom": "16px",
            }),
            html.Div([
                html.Button(
                    "★ Favourites Only",
                    id="btn-favourites-only",
                    n_clicks=0,
                    className="time-range-btn"
                ),
            ], style={
                "display": "flex",
                "gap": "8px",
                "marginBottom": "24px",
            }),
            html.Div(id="top-tracks-container"),
        ], style={
            "backgroundColor": self.styles["card_bg"],
            "borderRadius": self.styles["border_radius"],
            "padding": "24px",
            "border": "1px solid rgba(255, 255, 255, 0.05)",
            "minWidth": "320px",
            "width": "100%",
            "marginBottom": "24px",
            "boxShadow": "0 4px 24px 0 rgba(0,0,0,0.12)",
        })

        # Build Top Artists block (as currently rendered)
        top_artists_block = html.Div([
            html.H3("Top Artists", style={
                "fontSize": "18px",
                "fontWeight": "600",
                "margin": "0 0 16px 0",
            }),
            html.Div([
                html.Button(
                    "Recent",
                    id="btn-artist-recent",
                    n_clicks=0,
                    className="time-range-btn"
                ),
                html.Button(
                    "4 Weeks",
                    id="btn-artist-4weeks",
                    n_clicks=0,
                    className="time-range-btn"
                ),
                html.Button(
                    "6 Months",
                    id="btn-artist-6months",
                    n_clicks=0,
                    className="time-range-btn"
                ),
                html.Button(
                    "All Time",
                    id="btn-artist-alltime",
                    n_clicks=0,
                    className="time-range-btn"
                ),
            ], style={
                "display": "flex",
                "gap": "8px",
                "marginBottom": "16px",
            }),
            html.Div([
                html.Button(
                    "4",
                    id="btn-artist-count-4",
                    n_clicks=0,
                    className="time-range-btn"
                ),
                html.Button(
                    "12",
                    id="btn-artist-count-12",
                    n_clicks=0,
                    className="time-range-btn"
                ),
                html.Button(
                    "24",
                    id="btn-artist-count-24",
                    n_clicks=0,
                    className="time-range-btn"
                ),
            ], style={
                "display": "flex",
                "gap": "8px",
                "marginBottom": "24px",
            }),
            html.Div(id="top-artists-container"),
        ], style={
            "backgroundColor": self.styles["card_bg"],
            "borderRadius": self.styles["border_radius"],
            "padding": "24px",
            "border": "1px solid rgba(255, 255, 255, 0.05)",
            "minWidth": "320px",
            "width": "100%",
            "marginBottom": "24px",
            "boxShadow": "0 4px 24px 0 rgba(0,0,0,0.12)",
        })

        # Stats Panel block
        stats_panel_block = html.Div([
            html.H3("Stats", style={
                "fontSize": "18px",
                "fontWeight": "600",
                "margin": "0 0 16px 0",
            }),
            # Listening Time graph
            html.Div([
                html.H4("Listening Time", style={
                    "fontSize": "16px",
                    "fontWeight": "500",
                    "margin": "0 0 12px 0",
                    "color": self.styles["text"],
                }),
                dcc.Loading(
                    html.Div(id="listening-time-container", style={
                        "minHeight": "300px",
                    }),
                    type="default",
                    color="#4A90D9",
                ),
            ], style={"marginBottom": "24px"}),
            # Genre Evolution graph with time range buttons
            html.Div([
                html.H4("Genre Evolution", style={
                    "fontSize": "16px",
                    "fontWeight": "500",
                    "margin": "0 0 12px 0",
                    "color": self.styles["text"],
                }),
                html.Div([
                    html.Button(
                        "4 Weeks",
                        id="btn-genre-4weeks",
                        n_clicks=0,
                        className="time-range-btn"
                    ),
                    html.Button(
                        "6 Months",
                        id="btn-genre-6months",
                        n_clicks=0,
                        className="time-range-btn active"
                    ),
                    html.Button(
                        "All Time",
                        id="btn-genre-alltime",
                        n_clicks=0,
                        className="time-range-btn"
                    ),
                ], style={
                    "display": "flex",
                    "gap": "8px",
                    "marginBottom": "12px",
                }),
                dcc.Loading(
                    html.Div(id="genre-stats-container", style={
                        "minHeight": "300px",
                    }),
                    type="default",
                    color="#4A90D9",
                ),
            ], style={}),
        ], style={
            "backgroundColor": self.styles["card_bg"],
            "borderRadius": self.styles["border_radius"],
            "padding": "24px",
            "border": "1px solid rgba(255, 255, 255, 0.05)",
            "minWidth": "320px",
            "width": "100%",
            "marginBottom": "24px",
            "boxShadow": "0 4px 24px 0 rgba(0,0,0,0.12)",
        })

        # Music Library block (Duration + Playlists)
        music_library_block = html.Div([
            html.H3("Music Library", style={
                "fontSize": "18px",
                "fontWeight": "600",
                "margin": "0 0 16px 0",
            }),
            # Track Duration section
            html.Div([
                html.H4("Track Duration", style={
                    "fontSize": "16px",
                    "fontWeight": "500",
                    "margin": "0 0 12px 0",
                    "color": self.styles["text"],
                }),
                dcc.Loading(
                    html.Div(id="duration-container", style={
                        "minHeight": "350px",
                    }),
                    type="default",
                    color="#4A90D9",
                ),
            ], style={"marginBottom": "32px"}),
            # Playlist Overview section
            html.Div([
                html.H4("Playlist Overview", style={
                    "fontSize": "16px",
                    "fontWeight": "500",
                    "margin": "0 0 12px 0",
                    "color": self.styles["text"],
                }),
                html.Div([
                    html.Button(
                        "Treemap",
                        id="btn-playlist-treemap",
                        n_clicks=0,
                        className="time-range-btn active"
                    ),
                    html.Button(
                        "Donut",
                        id="btn-playlist-donut",
                        n_clicks=0,
                        className="time-range-btn"
                    ),
                ], style={
                    "display": "flex",
                    "gap": "8px",
                    "marginBottom": "12px",
                }),
                dcc.Loading(
                    html.Div(id="playlists-container", style={
                        "minHeight": "400px",
                    }),
                    type="default",
                    color="#4A90D9",
                ),
            ], style={}),
        ], style={
            "backgroundColor": self.styles["card_bg"],
            "borderRadius": self.styles["border_radius"],
            "padding": "24px",
            "border": "1px solid rgba(255, 255, 255, 0.05)",
            "minWidth": "320px",
            "width": "100%",
            "marginBottom": "24px",
            "boxShadow": "0 4px 24px 0 rgba(0,0,0,0.12)",
        })

        # Assign blocks to columns based on estimated height
        left_column = [top_tracks_block]
        right_column = [top_artists_block, stats_panel_block, music_library_block]

        # Responsive two-column flex layout
        columns = html.Div([
            html.Div(left_column, style={
                "flex": "1 1 0",
                "minWidth": "320px",
                "maxWidth": "900px",
                "display": "flex",
                "flexDirection": "column",
                "gap": "24px",
            }),
            html.Div(right_column, style={
                "flex": "1 1 0",
                "minWidth": "320px",
                "maxWidth": "900px",
                "display": "flex",
                "flexDirection": "column",
                "gap": "24px",
            }),
        ], style={
            "display": "flex",
            "gap": "24px",
            "alignItems": "flex-start",
            "width": "100%",
            "flexWrap": "wrap",
        },
        )
        return columns

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
                "position": "sticky",
                "top": "0",
                "zIndex": "100",
            }),
            html.Div(id="now-playing-bar", style={
                "backgroundColor": self.styles["card_bg"],
                "borderBottom": "1px solid rgba(255, 255, 255, 0.05)",
                "position": "sticky",
                "top": "81px",
                "zIndex": "99",
            }),
            html.Main([
                html.Div([
                    html.Div([
                        html.H2(greeting, style={
                            "fontSize": "28px",
                            "fontWeight": "600",
                            "marginBottom": "8px",
                        }),
                        html.P("Your Spotify dashboard is ready!", style={
                            "color": self.styles["text_muted"],
                        }),
                    ], style={"marginBottom": "24px"}),
                    self.build_dashboard_columns(user),
                ], style={
                    "padding": "0 32px",
                    "maxWidth": "1850px",
                }),
            ], style={
                "padding": f"{self.styles['spacing']} 32px",
            }),
        ])

    def build_currently_playing(self, track=None, elapsed_ms=0, animation_class=""):
        if track is None:
            return html.Div(style={"display": "none"})

        album_art = track.get("item", {}).get("album", {}).get("images", [{}])[0].get("url")
        track_name = track.get("item", {}).get("name", "Unknown Track")
        artist_name = ", ".join([a.get("name", "Unknown") for a in track.get("item", {}).get("artists", [])])
        is_playing = track.get("is_playing", False)
        progress_ms = track.get("progress_ms", 0)
        duration_ms = track.get("item", {}).get("duration_ms", 0)

        current_ms = progress_ms + elapsed_ms if is_playing else progress_ms
        current_ms = min(current_ms, duration_ms)
        progress_percent = (current_ms / duration_ms * 100) if duration_ms > 0 else 0

        def format_time(ms):
            seconds = int(ms / 1000)
            return f"{seconds // 60}:{seconds % 60:02d}"

        return html.Div(
            html.Div([
                html.Img(
                    src=album_art,
                    style={
                        "width": "40px",
                        "height": "40px",
                        "borderRadius": "4px",
                        "objectFit": "cover",
                        "marginRight": "12px",
                        "flexShrink": "0",
                    }
                ),
                html.Div([
                    html.Div(track_name, style={
                        "fontWeight": "600",
                        "fontSize": "14px",
                        "whiteSpace": "nowrap",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                    }),
                    html.Div(artist_name, style={
                        "color": self.styles["text_muted"],
                        "fontSize": "12px",
                        "whiteSpace": "nowrap",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                    }),
                ], style={
                    "flex": "0 0 auto",
                    "maxWidth": "200px",
                    "minWidth": "0",
                }),
                html.Div([
                    html.Span(format_time(current_ms), style={
                        "color": "#F0F0F0",
                        "fontSize": "14px",
                        "minWidth": "40px",
                        "flexShrink": "0",
                    }),
                    html.Div(style={
                        "flex": "1",
                        "height": "3px",
                        "backgroundColor": "rgba(255,255,255,0.15)",
                        "borderRadius": "1.5px",
                        "position": "relative",
                        "margin": "0 12px",
                        "minWidth": "120px",
                        "maxWidth": "75%",
                        "overflow": "hidden",
                    }, children=[
                        html.Div(style={
                            "position": "absolute",
                            "left": "0",
                            "top": "0",
                            "height": "100%",
                            "width": f"{progress_percent}%",
                            "backgroundColor": self.styles["accent"],
                            "borderRadius": "1.5px",
                        }),
                    ]),
                    html.Span(format_time(duration_ms), style={
                        "color": "#F0F0F0",
                        "fontSize": "14px",
                        "minWidth": "40px",
                        "textAlign": "right",
                        "flexShrink": "0",
                    }),
                ], style={
                    "display": "flex",
                    "alignItems": "center",
                    "flex": "1",
                    "minWidth": "0",
                    "margin": "0 16px",
                }),
                html.Div([
                    html.Span("●", style={
                        "color": "#1db954" if is_playing else self.styles["text_muted"],
                        "marginRight": "6px",
                    }),
                    html.Span("Playing" if is_playing else "Paused", style={
                        "color": "#1db954" if is_playing else self.styles["text_muted"],
                        "fontSize": "12px",
                    }),
                ], style={
                    "display": "flex",
                    "alignItems": "center",
                    "flexShrink": "0",
                }),
            ], style={
                "display": "flex",
                "alignItems": "center",
                "padding": "12px 32px",
                "width": "100%",
            }),
                className=animation_class,
                style={
                    "width": "100%",
                    "overflow": "hidden",
                }
            )

    def build_top_tracks(self, tracks=None, time_range_display="6 Months", limit=50, favourite_track_ids=None, show_favourites_only=False):
        if favourite_track_ids is None:
            favourite_track_ids = set()
        
        if show_favourites_only:
            track_items = [t for t in tracks.get("items", []) if t.get("id") in favourite_track_ids] if tracks else []
        else:
            track_items = tracks.get("items", [])[:limit] if tracks else []
        
        if not track_items:
            return html.Div([
                html.Div("No top tracks data available.", style={
                    "color": self.styles["text_muted"],
                    "textAlign": "center",
                    "padding": "40px",
                })
            ])

        current_label = time_range_display

        def format_duration(ms):
            seconds = int(ms / 1000)
            return f"{seconds // 60}:{seconds % 60:02d}"

        track_rows = []
        for idx, track in enumerate(track_items, 1):
            album_images = track.get("album", {}).get("images", [])
            album_art = album_images[0].get("url") if album_images else None
            track_name = track.get("name", "Unknown Track")
            artist_names = ", ".join([a.get("name", "Unknown") for a in track.get("artists", [])])
            duration_ms = track.get("duration_ms", 0)
            track_id = track.get("id", "")
            is_favourite = track_id in favourite_track_ids

            track_rows.append(html.Div([
                html.Div([
                    html.Button(
                        "★" if is_favourite else "☆",
                        id={"type": "btn-favourite", "index": track_id},
                        n_clicks=0,
                        style={
                            "background": "none",
                            "border": "none",
                            "color": "#FFD700" if is_favourite else self.styles["text_muted"],
                            "fontSize": "16px",
                            "cursor": "pointer",
                            "padding": "0",
                            "width": "24px",
                        }
                    ),
                    html.Span(str(idx), style={
                        "fontSize": "14px",
                        "fontWeight": "600",
                        "color": self.styles["text_muted"],
                    }),
                ], style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "8px",
                    "width": "48px",
                }),
                html.Img(
                    src=album_art,
                    style={
                        "width": "48px",
                        "height": "48px",
                        "borderRadius": "4px",
                        "objectFit": "cover",
                        "marginLeft": "8px",
                        "marginRight": "16px",
                    }
                ) if album_art else html.Div(style={
                    "width": "48px",
                    "height": "48px",
                    "backgroundColor": self.styles["bg"],
                    "borderRadius": "4px",
                    "marginLeft": "8px",
                    "marginRight": "16px",
                }),
                html.Div([
                    html.Div(track_name, style={
                        "fontWeight": "600",
                        "fontSize": "15px",
                        "marginBottom": "4px",
                        "whiteSpace": "nowrap",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                    }),
                    html.Div(artist_names, style={
                        "color": self.styles["text_muted"],
                        "fontSize": "13px",
                        "whiteSpace": "nowrap",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                    }),
                ], style={
                    "flex": "1",
                    "minWidth": "0",
                    "overflow": "hidden",
                }),
                html.Div(format_duration(duration_ms), style={
                    "color": self.styles["text_muted"],
                    "fontSize": "13px",
                    "minWidth": "45px",
                    "textAlign": "right",
                }),
            ], style={
                "display": "flex",
                "alignItems": "center",
                "padding": "12px 8px",
                "borderBottom": "1px solid rgba(255,255,255,0.05)",
            }))

        return html.Div([
            html.Div([
                html.Div(f"Showing: {current_label}{' - Favourites Only' if show_favourites_only else f' ({len(track_items)} tracks)'}",
                style={
                    "fontSize": "14px",
                    "color": self.styles["text_muted"],
                    "marginBottom": "16px",
                }),
            ]),
            html.Div(track_rows, style={
                "display": "flex",
                "flexDirection": "column",
            }),
        ])

    def build_top_artists(self, artist_data=None, time_range_display="6 Months", display_count=15):
        if not artist_data or not artist_data.get("artists"):
            return html.Div([
                html.Div("No top artists data available.", style={
                    "color": self.styles["text_muted"],
                    "textAlign": "center",
                    "padding": "40px",
                })
            ])
        
        artists = artist_data.get("artists", [])[:display_count]
        
        if not artists:
            return html.Div([
                html.Div("No top artists data available.", style={
                    "color": self.styles["text_muted"],
                    "textAlign": "center",
                    "padding": "40px",
                })
            ])
        
        artist_cards = []
        for idx, artist in enumerate(artists, 1):
            images = artist.get("images", [])
            artist_image = images[0].get("url") if images else None
            artist_name = artist.get("name", "Unknown Artist")
            track_count = artist.get("track_count", 0)
            score = artist.get("score", 0)
            
            artist_cards.append(html.Div([
                html.Div(str(idx), style={
                    "fontSize": "14px",
                    "fontWeight": "600",
                    "color": self.styles["text_muted"],
                    "marginBottom": "8px",
                }),
                html.Img(
                    src=artist_image,
                    style={
                        "width": "100%",
                        "aspectRatio": "1",
                        "objectFit": "cover",
                        "borderRadius": "8px",
                        "marginBottom": "12px",
                    }
                ) if artist_image else html.Div(style={
                    "width": "100%",
                    "aspectRatio": "1",
                    "backgroundColor": self.styles["bg"],
                    "borderRadius": "8px",
                    "marginBottom": "12px",
                }),
                html.Div(artist_name, style={
                    "fontWeight": "600",
                    "fontSize": "14px",
                    "textAlign": "center",
                    "marginBottom": "4px",
                    "whiteSpace": "nowrap",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                }),
                html.Div(f"{score} score - {track_count} tracks", style={
                    "color": self.styles["text_muted"],
                    "fontSize": "12px",
                    "textAlign": "center",
                    "display": "none",
                }),
            ], style={
                "width": "24%",
                "minWidth": "100px",
                "padding": "6px",
                "boxSizing": "border-box",
            }))
        
        items_per_row = 4
        rows = []
        for i in range(0, len(artist_cards), items_per_row):
            rows.append(html.Div(artist_cards[i:i+items_per_row], style={
                "display": "flex",
                "flexWrap": "wrap",
                "justifyContent": "flex-start",
                "gap": "8px",
            }))
        
        return html.Div([
            html.Div([
                html.Div(f"Showing: {time_range_display} ({len(artists)} artists)", style={
                    "fontSize": "14px",
                    "color": self.styles["text_muted"],
                    "marginBottom": "16px",
                }),
            ]),
            html.Div(rows, style={
                "display": "flex",
                "flexDirection": "column",
            }),
        ])
