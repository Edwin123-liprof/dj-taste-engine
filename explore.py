import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import Counter

df_recent = pd.read_csv('recent_tracks.csv')
df_top = pd.read_csv('top_tracks.csv')

df_recent['played_at'] = pd.to_datetime(df_recent['played_at'], utc=True)
df_recent['hour'] = df_recent['played_at'].dt.hour
df_recent['day'] = df_recent['played_at'].dt.day_name()

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("Edwin's Music Taste Profile", fontsize=16, fontweight='bold')

# 1. Top artists in recent plays
artist_counts = df_recent['artist'].value_counts().head(10)
axes[0,0].barh(artist_counts.index[::-1], artist_counts.values[::-1], color='#1DB954')
axes[0,0].set_title('Most Played Artists (Recent)')
axes[0,0].set_xlabel('Play count')

# 2. Listening by hour of day
hour_counts = df_recent['hour'].value_counts().sort_index()
axes[0,1].bar(hour_counts.index, hour_counts.values, color='#1DB954', alpha=0.8)
axes[0,1].set_title('Listening by Hour of Day')
axes[0,1].set_xlabel('Hour (24h)')
axes[0,1].set_ylabel('Tracks played')
axes[0,1].set_xticks(range(0, 24, 2))

# 3. Top artists across all three time windows
for term, color, label in [
    ('short_term', '#1DB954', 'Last 4 weeks'),
    ('medium_term', '#17a844', 'Last 6 months'),
    ('long_term', '#0f6b2c', 'All time')
]:
    term_df = df_top[df_top['term'] == term]
    top_artists = term_df['artist'].value_counts().head(5)
    axes[1,0].barh(
        [f"{a} ({label})" for a in top_artists.index[::-1]],
        top_artists.values[::-1],
        color=color, alpha=0.85
    )
axes[1,0].set_title('Top Artists by Time Window')
axes[1,0].set_xlabel('Tracks in top 50')

# 4. Taste drift — rank changes between short and long term
short = df_top[df_top['term']=='short_term'][['artist','rank']].rename(columns={'rank':'short_rank'})
long = df_top[df_top['term']=='long_term'][['artist','rank']].rename(columns={'rank':'long_rank'})
drift = pd.merge(short, long, on='artist').head(10)
drift['change'] = drift['long_rank'] - drift['short_rank']
colors = ['#1DB954' if x > 0 else '#e74c3c' for x in drift['change']]
axes[1,1].barh(drift['artist'], drift['change'], color=colors)
axes[1,1].axvline(0, color='gray', linewidth=0.8)
axes[1,1].set_title('Taste Drift (green = rising, red = falling)')
axes[1,1].set_xlabel('Rank change (long term vs now)')

plt.tight_layout()
plt.savefig('taste_profile.png', dpi=150, bbox_inches='tight')
print("Saved taste_profile.png")
plt.show()