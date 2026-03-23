# SpofiDash — Project Plan

## What is this?
A Spotify dashboard web app built with **Dash by Plotly** (Python), running in **Docker**.
Connects to the Spotify Web API via **Spotipy** (OAuth2) to display listening stats, currently playing songs, auto-generated playlists, and genre/artist graphs.

## Stack
- **Python 3.11**
- **Dash by Plotly** — UI, graphs, stats
- **Spotipy** — Spotify Web API OAuth2 client
- **Docker + Docker Compose** — containerized deployment

## Project Structure

```
SpotiDash/
├── spotidash/              # Main application package
│   ├── __init__.py
│   ├── __main__.py         # Entry point
│   ├── app.py              # Dash app initialization
│   ├── callbacks/          # Dash callbacks
│   │   └── __init__.py
│   ├── core/               # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py       # Environment configuration (.env variables)
│   │   └── spotify_client.py
│   ├── layout/             # UI layout components
│   │   ├── __init__.py
│   │   └── builder.py
│   └── utils/
│       └── __init__.py
├── .env                    # Environment variables (not committed)
├── .env.example            # Template for .env
├── .gitignore              # Ignores .env
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker image
└── docker-compose.yml      # Docker Compose
```
## Design and frontend
The app uses a dark theme throughout with no light mode. The background is a deep dark gray (#121212 or similar), not pure black, to reduce eye strain. The accent color is a muted, desaturated blue (#4A90D9 or similar — calm, not electric) used for highlights, active states, buttons, and chart accents. All text is white or near-white (#F0F0F0), using a clean and slightly soft sans-serif font like Inter or DM Sans.
All containers, cards, and panels have rounded corners (border-radius around 12–16px), a slightly lighter background than the page (#1E1E1E or similar), and subtle borders or shadows to separate them without being harsh. Spacing should feel generous — nothing cramped. Interactive elements like buttons and dropdowns should feel consistent with the overall palette, no jarring colors.
Charts and graphs should use the same muted blue as the primary color, with supporting tones that stay within a cool, dark-friendly palette. The overall feel should be calm, readable, and modern — closer to a personal analytics tool than a flashy dashboard.

## Phases
## Setup phases
- [ ] **Phase 1 — Project Foundation**
  Core files are wired up correctly: dependencies, env vars loading, Spotipy client initializing, and the Dash app running without errors.

- [ ] **Phase 2 — Docker Setup**
  The app builds and runs inside Docker. `docker compose up` starts the container, port 8050 is exposed, and the `.env` file is passed through. App is reachable at `http://localhost:8050`.

- [ ] **Phase 3 — Spotify OAuth Flow**
  User can log in via Spotify. App handles the redirect, exchanges the code for a token, and stores it for use in API calls throughout the session.
## Feature phases
- [ ] **Phase 4 — Currently Playing Widget**
  A card that shows the song, artist, and album art currently playing on the user's Spotify account. Polls the API every few seconds and handles the "nothing playing" state.

- [ ] **Phase 5 — Top Tracks Dashboard**
  Displays the user's top tracks with a time range selector (4 weeks / 6 months / all time). Includes a chart ranked by popularity.

- [ ] **Phase 6 — Genre & Artist Stats**
  Charts showing top artists and aggregated genres based on listening history. Visualized with Plotly graphs.

- [ ] **Phase 7 — Auto-Generate Playlists**
  User can generate a playlist based on their top tracks/artists, preview the suggestions, and save it directly to their Spotify account.
## Final phases
- [ ] **Phase 8 — Polish & UX**
  Loading states, error handling for expired tokens, logout button, dark theme, and responsive layout.

- [ ] **Phase 9 — Final Docker & Cleanup**
  App runs cleanly in Docker, `.env` is gitignored, `.env.example` is up to date, and a basic README exists.

---

## Notes
- Files and references to 'SpotiDash' need to be renamed to 'SpofiDash'
- `.env` credentials must be filled before OAuth works

## Commands

Run locally:
```bash
python -m spotidash
```

With Docker:
```bash
docker-compose up
```
