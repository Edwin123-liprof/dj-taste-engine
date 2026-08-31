import pandas as pd
from spotipy.oauth2 import SpotifyOauthError

from spotify_client import discard_cached_token, get_spotify_client, is_invalid_grant


def collect():
    try:
        _collect(get_spotify_client())
    except SpotifyOauthError as exc:
        if not is_invalid_grant(exc):
            raise
        print(
            "Spotify refresh token expired (they now last 6 months). "
            "Opening the sign-in flow to get a new one..."
        )
        discard_cached_token()
        _collect(get_spotify_client())


def _collect(sp):
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
            'album_image': track['album']['images'][0]['url'] if track['album']['images'] else '',
            'played_at': item['played_at'],
            'duration_ms': track['duration_ms'],
            'explicit': track['explicit']
        })

    print(f"Fetched {len(tracks)} tracks.")
    print("Fetching top tracks (short term)...")
    top_short = sp.current_user_top_tracks(limit=50, time_range='short_term')
    print("Fetching top tracks (medium term)...")
    top_medium = sp.current_user_top_tracks(limit=50, time_range='medium_term')
    print("Fetching top tracks (long term)...")
    top_long = sp.current_user_top_tracks(limit=50, time_range='long_term')

    def parse_top_tracks(results, term):
        rows = []
        for i, track in enumerate(results['items']):
            rows.append({
                'track_id': track['id'],
                'track_name': track['name'],
                'artist': track['artists'][0]['name'],
                'album': track['album']['name'],
                'album_image': track['album']['images'][0]['url'] if track['album']['images'] else '',
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
    print("\nSample with album art:")
    print(df_top[['track_name','artist','album_image']].head(3).to_string(index=False))


if __name__ == '__main__':
    collect()
