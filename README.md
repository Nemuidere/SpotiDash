# SpotiDash

Your personal Spotify analytics dashboard. SpotiDash logs into your Spotify
account and turns your listening data into a clean, live web dashboard — top
tracks and artists, genre evolution, listening stats, a playlist overview, and
a real-time "now playing" bar.

Built with [Dash](https://dash.plotly.com/) + Flask and the Spotify Web API
(via [Spotipy](https://spotipy.readthedocs.io/)).

## Features

- **Now Playing** — live track, artist, and progress bar (refreshes every few seconds)
- **Top Tracks** — filter by time range (recent / 4 weeks / 6 months / all time) and count, with a favourites list
- **Top Artists** — ranked artist grid with time-range filters
- **Stats** — listening time and genre evolution over time
- **Music Library** — track-duration breakdown and a playlist overview (treemap or donut)

## Prerequisites

- **Python 3.11+** (or **Docker**, if you prefer containers)
- A **Spotify account**
- **Spotify API credentials** (free — see below)

## 1. Get Spotify API credentials

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and log in.
2. Click **Create app**. Give it any name and description.
3. Set the **Redirect URI** to exactly:
   ```
   http://localhost:8050/callback
   ```
4. Save, then open the app's **Settings** to copy your **Client ID** and **Client Secret**.

## 2. Configure environment variables

Copy the provided template and fill in your values:

```bash
cp .env.example .env
```

Then edit `.env`:

```bash
SPOTIPY_CLIENT_ID=your_client_id_here
SPOTIPY_CLIENT_SECRET=your_client_secret_here
SPOTIPY_REDIRECT_URI=http://localhost:8050/callback

# Optional for local dev; recommended in production so login sessions
# survive restarts. Generate one with: python -c "import secrets; print(secrets.token_hex(32))"
FLASK_SECRET_KEY=your_random_secret_here
```

> The redirect URI here **must match** the one you registered in the Spotify
> dashboard, character for character.

## 3. Start the app

Pick one of the two options below.

### Option A — Run locally with Python

```bash
# From the project root
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

python -m spotidash
```

### Option B — Run with Docker

Make sure your `.env` file exists (step 2), then:

```bash
docker compose up --build
```

## 4. Open the dashboard

Once it's running, visit:

```
http://localhost:8050
```

Click **Login with Spotify**, approve the requested permissions, and your
dashboard will load. Use **Logout** in the top-right to switch accounts.

## Project structure

```
spotidash/
├── __main__.py            # Entry point (python -m spotidash)
├── app.py                 # SpotiDash app: Dash/Flask setup, OAuth, Spotify API calls
├── core/
│   ├── config.py          # Loads env vars and Spotify scopes
│   └── spotify_client.py  # Spotify client wrapper
├── layout/
│   ├── builder.py         # Builds the login page and dashboard UI
│   └── styles.py          # Theme and global CSS
├── callbacks/             # Dash interactivity (filters, live updates)
└── utils/
    └── stats.py           # Stats/aggregation helpers
```

## Troubleshooting

- **`INVALID_CLIENT: Invalid redirect URI`** — the `SPOTIPY_REDIRECT_URI` in
  `.env` doesn't exactly match the one registered in the Spotify dashboard.
- **Login loops back to the login page** — confirm your Client ID/Secret are
  correct and that your `.env` is being loaded from the project root.
- **Port 8050 already in use** — stop the other process, or change the port in
  `spotidash/__main__.py` (and update the redirect URI to match).

## Configuration reference

| Variable | Description |
| --- | --- |
| `SPOTIPY_CLIENT_ID` | Your Spotify app's Client ID |
| `SPOTIPY_CLIENT_SECRET` | Your Spotify app's Client Secret |
| `SPOTIPY_REDIRECT_URI` | OAuth callback URL — must match the Spotify dashboard (e.g. `http://localhost:8050/callback`) |
| `FLASK_SECRET_KEY` | *(Optional)* Flask session signing key. If unset, a random key is generated per process (fine for local dev; set it in production so sessions persist across restarts) |

The app requests these Spotify scopes: `user-top-read`,
`user-read-recently-played`, `playlist-read-private`,
`user-read-currently-playing`.
