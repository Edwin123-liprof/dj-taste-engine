# DJ Taste Engine 🎵

A personal music intelligence engine that analyzes your Spotify listening history to model your shifting taste over time and generate contextually smart, DJ-style track queues tailored to your current mood and listening context.

## The Problem

Spotify's DJ feature replays familiar songs without adapting to how your taste shifts over time. A static recommendation engine treats your taste as fixed — but it isn't. Your listening persona at 8 AM is different from midnight. Your current favorite artists may be completely different from six months ago.

## The Solution

DJ Taste Engine pulls your real Spotify data across three time windows (last 4 weeks, 6 months, all time) and scores every track using a weighted model that prioritizes recency and current preference. It then generates a 20-track queue structured like a real DJ set — warmup, build, peak, cooldown — using your highest-scoring tracks at the right moments.

## Features

- Spotify OAuth authentication via the Spotipy library
- Pulls recently played tracks and top tracks across three time windows
- Weighted taste scoring model with recency decay
- DJ-style energy arc queue generation
- Listening pattern visualizations (most played artists, hour of day, day of week, taste drift)

## Tech Stack

- Python 3
- Spotipy (Spotify Web API wrapper)
- Pandas
- Scikit-learn
- Matplotlib

## Project Structure

```
dj-taste-engine/
├── collect_data.py       # Spotify API data collection
├── explore.py            # Listening pattern visualizations
├── recommender.py        # Taste scoring + DJ queue generation
├── recent_tracks.csv     # Recently played tracks (generated)
├── top_tracks.csv        # Top tracks across time windows (generated)
├── dj_queue.csv          # Generated DJ queue (generated)
├── taste_profile.png     # Visualization output (generated)
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

5. Generate your DJ queue:

```bash
python recommender.py
```

6. Visualize your taste profile:

```bash
python explore.py
```

## How the Model Works

Each track is scored using a combination of:

- **Term weight** — short term (3x), medium term (2x), long term (1x)
- **Rank weight** — rank 1 scores 1.0, rank 50 scores 0.02
- **Recency bonus** — tracks played recently get a bonus that decays over 7 days

The DJ queue then slots your highest-scoring tracks into the peak phase of an energy arc, with lower-scored tracks filling the warmup and cooldown phases.

## Sample Output

```
#    Phase      Track                               Artist                    Score
------------------------------------------------------------------------------------
1    warmup     News or Something                   Future                    2.50
2    warmup     White Iverson                       Post Malone               2.40
...
11   peak       YUKON                               Justin Bieber             3.68
14   peak       Ballin' (with Roddy Ricch)          Mustard                   4.07
...
20   cooldown   Nuvole Bianche                      Ludovico Einaudi          2.04
```

## Author

Edwin Silayo — Data Analyst & ML Engineer