import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    scope="user-read-recently-played user-top-read user-library-read",
    cache_path=".cache"
))

results = sp.current_user_recently_played(limit=5)
for item in results['items']:
    track = item['track']
    print(f"{track['name']} — {track['artists'][0]['name']}")