# DJ Taste Engine 🎵

A personal music intelligence engine that analyzes your Spotify listening history to model your shifting taste over time and generates contextually smart, DJ-style track queues — served through a full web application.

## The Problem

Spotify's DJ feature replays familiar songs without adapting to how your taste shifts over time. A static recommendation engine treats your taste as fixed — but it isn't. Your listening persona at 8 AM is different from midnight. Your current favorite artists may be completely different from six months ago.

## The Solution

DJ Taste Engine pulls your real Spotify data across three time windows (last 4 weeks, 6 months, all time) and scores every track using a weighted model that prioritizes recency and current preference. It then generates a 20-track queue structured like a real DJ set — warmup, build, peak, cooldown — using your highest-scoring tracks at the right moments.

## Web Application

The project ships as a local web app with three pages:

- **Homepage** — animated hero with live audio visualizer, scrolling track ticker, top 10 tracks with album art, and feature navigation
- **Dashboard** — listening pattern charts, taste drift infographic with hover insights, top 10 and top scored tracks with album art and Spotify links
- **DJ Queue** — on-demand queue generation with phase badges, taste scores, album art, and direct Spotify playback links

## Features

- Spotify OAuth authentication via Spotipy
- Pulls recently played tracks and top tracks across three time windows
- Album artwork fetched and displayed throughout the app
- Weighted taste scoring model with recency decay
- DJ-style energy arc queue generation
- Listening pattern visualizations (artists, hour of day, day of week)
- Taste drift infographic with artist insights on hover
- One-click Spotify playback links for every track
- Refresh button to pull latest Spotify data on demand
- Live canvas audio visualizer background on homepage

## Tech Stack

- Python 3
- Flask
- Spotipy (Spotify Web API wrapper)
- Pandas
- Scikit-learn
- Chart.js
- Lucide Icons
- HTML / CSS / JavaScript

## Project Structure

```
dj-taste-engine/
├── app.py                # Flask web application
├── collect_data.py       # Spotify API data collection
├── explore.py            # Standalone visualizations
├── recommender.py        # Taste scoring + DJ queue generation
├── templates/
│   ├── index.html        # Homepage
│   ├── dashboard.html    # Taste dashboard
│   └── queue.html        # DJ queue page
├── static/
│   └── logo.png          # App logo
├── recent_tracks.csv     # Recently played tracks (generated)
├── top_tracks.csv        # Top tracks across time windows (generated)
├── dj_queue.csv          # Generated DJ queue (generated)
└── requirements.txt      # Dependencies
```

## Setup

1. Clone the repo
2. Create a virtual environment and install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your Spotify credentials:

```
SPOTIPY_CLIENT_ID=your_client_id
SPOTIPY_CLIENT_SECRET=your_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

4. Run data collection:

```bash
python collect_data.py
```

5. Start the web app:

```bash
python app.py
```

6. Open your browser at `http://127.0.0.1:5000`

## How the Model Works

Each track is scored using a combination of:

- **Term weight** — short term (3x), medium term (2x), long term (1x)
- **Rank weight** — rank 1 scores 1.0, rank 50 scores 0.02
- **Recency bonus** — tracks played recently get a bonus that decays over 7 days

The DJ queue slots your highest-scoring tracks into the peak phase of an energy arc, with lower-scored tracks filling the warmup and cooldown phases.

## Author

Edwin Silayo — Data Analyst & ML Engineer