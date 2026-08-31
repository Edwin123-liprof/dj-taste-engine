from spotify_client import get_spotify_client

sp = get_spotify_client()

results = sp.current_user_recently_played(limit=5)
for item in results['items']:
    track = item['track']
    print(f"{track['name']} — {track['artists'][0]['name']}")
