import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timezone

df_recent = pd.read_csv('recent_tracks.csv')
df_top = pd.read_csv('top_tracks.csv')

df_recent['played_at'] = pd.to_datetime(df_recent['played_at'], utc=True)

# --- Step 1: Build a taste score for each track ---
# Tracks appearing in short_term top get highest weight,
# medium_term less, long_term least, recent plays add bonus

weights = {'short_term': 3, 'medium_term': 2, 'long_term': 1}

scores = {}

for _, row in df_top.iterrows():
    tid = row['track_id']
    term_weight = weights[row['term']]
    rank_weight = (51 - row['rank']) / 50  # rank 1 = 1.0, rank 50 = 0.02
    score = term_weight * rank_weight
    scores[tid] = scores.get(tid, 0) + score

# Add recency bonus for recently played tracks
now = datetime.now(timezone.utc)
for _, row in df_recent.iterrows():
    tid = row['track_id']
    hours_ago = (now - row['played_at']).total_seconds() / 3600
    recency_bonus = max(0, 1 - (hours_ago / 168))  # decays over 7 days
    scores[tid] = scores.get(tid, 0) + recency_bonus

# --- Step 2: Build the scored track pool ---
all_track_ids = list(set(
    df_top['track_id'].tolist() + df_recent['track_id'].tolist()
))

track_info = {}
for _, row in df_top.iterrows():
    track_info[row['track_id']] = {
        'track_name': row['track_name'],
        'artist': row['artist']
    }
for _, row in df_recent.iterrows():
    track_info[row['track_id']] = {
        'track_name': row['track_name'],
        'artist': row['artist']
    }

scored_tracks = []
for tid in all_track_ids:
    info = track_info.get(tid, {})
    scored_tracks.append({
        'track_id': tid,
        'track_name': info.get('track_name', 'Unknown'),
        'artist': info.get('artist', 'Unknown'),
        'taste_score': scores.get(tid, 0)
    })

df_scored = pd.DataFrame(scored_tracks)
df_scored = df_scored.sort_values('taste_score', ascending=False)

# --- Step 3: Generate a DJ-style queue ---
# Energy arc: pull top scoring tracks and sequence them
# We simulate an energy arc using track position in scoring as proxy

def generate_queue(df, n=20):
    pool = df.head(40).copy().reset_index(drop=True)
    
    # Assign a synthetic energy arc position
    # Real DJ arc: warm up (low) -> build -> peak -> cooldown
    arc = []
    for i in range(n):
        progress = i / (n - 1)
        if progress < 0.2:
            arc.append('warmup')
        elif progress < 0.5:
            arc.append('build')
        elif progress < 0.75:
            arc.append('peak')
        else:
            arc.append('cooldown')
    
    # Sort pool by score descending, assign peak slots to top scorers
    peak_tracks = pool.head(8).sample(frac=1).reset_index(drop=True)
    other_tracks = pool.iloc[8:].sample(frac=1).reset_index(drop=True)
    
    queue = []
    peak_idx = 0
    other_idx = 0
    
    for phase in arc:
        if phase == 'peak' and peak_idx < len(peak_tracks):
            queue.append({**peak_tracks.iloc[peak_idx].to_dict(), 'phase': phase})
            peak_idx += 1
        elif other_idx < len(other_tracks):
            queue.append({**other_tracks.iloc[other_idx].to_dict(), 'phase': phase})
            other_idx += 1
        elif peak_idx < len(peak_tracks):
            queue.append({**peak_tracks.iloc[peak_idx].to_dict(), 'phase': phase})
            peak_idx += 1
    
    return pd.DataFrame(queue)

print("Generating your DJ queue...\n")
queue = generate_queue(df_scored, n=20)

print(f"{'#':<4} {'Phase':<10} {'Track':<35} {'Artist':<25} {'Score'}")
print("-" * 85)
for i, row in queue.iterrows():
    print(f"{i+1:<4} {row['phase']:<10} {row['track_name'][:33]:<35} {row['artist'][:23]:<25} {row['taste_score']:.2f}")

queue.to_csv('dj_queue.csv', index=False)
print(f"\nQueue saved to dj_queue.csv")
print(f"\nTop 5 tracks by taste score:")
print(df_scored[['track_name','artist','taste_score']].head(5).to_string(index=False))