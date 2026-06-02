import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    scope="user-read-recently-played user-top-read",
    cache_path=".cache"
))

print("Fetching recently played tracks...")
results = sp.current_user_recently_played(limit=50)

tracks = []
for item in results['items']:
    track = item['track']
    tracks.append({
        'track_id': track['id'],
        'track_name': track['name'],
        'artist': track['artists'][0]['name'],
        'album': track['album']['name'],
        'played_at': item['played_at'],
        'duration_ms': track['duration_ms'],
        'explicit': track['explicit']
    })

print(f"Fetched {len(tracks)} tracks.")
print("Fetching your top tracks (short term)...")
top_short = sp.current_user_top_tracks(limit=50, time_range='short_term')
print("Fetching your top tracks (medium term)...")
top_medium = sp.current_user_top_tracks(limit=50, time_range='medium_term')
print("Fetching your top tracks (long term)...")
top_long = sp.current_user_top_tracks(limit=50, time_range='long_term')

def parse_top_tracks(results, term):
    rows = []
    for i, track in enumerate(results['items']):
        rows.append({
            'track_id': track['id'],
            'track_name': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'rank': i + 1,
            'term': term,
            'duration_ms': track['duration_ms'],
            'explicit': track['explicit']
        })
    return rows

top_tracks = (
    parse_top_tracks(top_short, 'short_term') +
    parse_top_tracks(top_medium, 'medium_term') +
    parse_top_tracks(top_long, 'long_term')
)

df_recent = pd.DataFrame(tracks)
df_recent['played_at'] = pd.to_datetime(df_recent['played_at'])
df_recent = df_recent.sort_values('played_at', ascending=False)

df_top = pd.DataFrame(top_tracks)

df_recent.to_csv('recent_tracks.csv', index=False)
df_top.to_csv('top_tracks.csv', index=False)

print(f"\nSaved {len(df_recent)} recent tracks to recent_tracks.csv")
print(f"Saved {len(df_top)} top tracks to top_tracks.csv")
print("\nYour recent tracks:")
print(df_recent[['track_name', 'artist', 'played_at']].head(10).to_string(index=False))
print("\nYour top tracks right now (short term):")
print(df_top[df_top['term']=='short_term'][['rank','track_name','artist']].head(10).to_string(index=False))