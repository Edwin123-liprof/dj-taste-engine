from flask import Flask, render_template, jsonify
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import subprocess
import os

app = Flask(__name__)

def compute_scores():
    df_recent = pd.read_csv('recent_tracks.csv')
    df_top = pd.read_csv('top_tracks.csv')
    df_recent['played_at'] = pd.to_datetime(df_recent['played_at'], utc=True)

    weights = {'short_term': 3, 'medium_term': 2, 'long_term': 1}
    scores = {}

    for _, row in df_top.iterrows():
        tid = row['track_id']
        term_weight = weights[row['term']]
        rank_weight = (51 - row['rank']) / 50
        score = term_weight * rank_weight
        scores[tid] = scores.get(tid, 0) + score

    now = datetime.now(timezone.utc)
    for _, row in df_recent.iterrows():
        tid = row['track_id']
        hours_ago = (now - row['played_at']).total_seconds() / 3600
        recency_bonus = max(0, 1 - (hours_ago / 168))
        scores[tid] = scores.get(tid, 0) + recency_bonus

    track_info = {}
    for _, row in df_top.iterrows():
        track_info[row['track_id']] = {
            'track_name': row['track_name'],
            'artist': row['artist'],
            'album_image': row['album_image']
        }
    for _, row in df_recent.iterrows():
        track_info[row['track_id']] = {
            'track_name': row['track_name'],
            'artist': row['artist'],
            'album_image': row['album_image']
        }

    all_track_ids = list(set(df_top['track_id'].tolist() + df_recent['track_id'].tolist()))
    scored_tracks = []
    for tid in all_track_ids:
        info = track_info.get(tid, {})
        scored_tracks.append({
    'track_id': tid,
    'track_name': info.get('track_name', 'Unknown'),
    'artist': info.get('artist', 'Unknown'),
    'album_image': info.get('album_image', ''),
    'taste_score': round(scores.get(tid, 0), 2)
})


    return pd.DataFrame(scored_tracks).sort_values('taste_score', ascending=False), df_recent, df_top

def generate_queue(df_scored, n=20):
    pool = df_scored.head(40).copy().reset_index(drop=True)
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

    return queue

@app.route('/')
def index():
    return render_template('index.html')
def get_artist_insights(artist, df_top):
    short = df_top[(df_top['term']=='short_term') & (df_top['artist']==artist)]
    medium = df_top[(df_top['term']=='medium_term') & (df_top['artist']==artist)]
    long = df_top[(df_top['term']=='long_term') & (df_top['artist']==artist)]
    
    best_rank = min(
        [r['rank'] for _, r in short.iterrows()] +
        [r['rank'] for _, r in medium.iterrows()] +
        [r['rank'] for _, r in long.iterrows()] or [99]
    )
    appearances = len(short) + len(medium) + len(long)
    
    if len(short) > 0 and len(long) == 0:
        discovery = "Recent discovery"
    elif len(short) > 0 and len(long) > 0:
        discovery = "Long-term favourite"
    elif len(medium) > 0 and len(short) == 0:
        discovery = "Fading from rotation"
    else:
        discovery = "Deep catalogue"
    
    dominant = "short term" if len(short) >= len(medium) and len(short) >= len(long) else \
               "medium term" if len(medium) >= len(long) else "long term"
    
    return {
        'best_rank': best_rank,
        'appearances': appearances,
        'discovery': discovery,
        'dominant': dominant,
        'short_count': len(short),
        'medium_count': len(medium),
        'long_count': len(long)
    }

@app.route('/api/dashboard')
def dashboard():
    df_scored, df_recent, df_top = compute_scores()
    df_recent['hour'] = pd.to_datetime(df_recent['played_at'], utc=True).dt.hour
    df_recent['day'] = pd.to_datetime(df_recent['played_at'], utc=True).dt.day_name()

    top_artists = df_recent['artist'].value_counts().head(8)
    hour_counts = df_recent['hour'].value_counts().reindex(range(24), fill_value=0)
    day_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    day_counts = df_recent['day'].value_counts().reindex(day_order, fill_value=0)

    short = df_top[df_top['term']=='short_term'][['artist','rank']].rename(columns={'rank':'short_rank'})
    long = df_top[df_top['term']=='long_term'][['artist','rank']].rename(columns={'rank':'long_rank'})
    drift = pd.merge(short, long, on='artist').head(8)
    drift['change'] = drift['long_rank'] - drift['short_rank']
    drift = drift.sort_values('change', ascending=False)

    top10_now = df_top[df_top['term']=='short_term'].head(10)

    short_with_img = df_top[df_top['term']=='short_term'][['artist','rank','album_image']].rename(columns={'rank':'short_rank'})
    long_with_img = df_top[df_top['term']=='long_term'][['artist','rank']].rename(columns={'rank':'long_rank'})
    drift_full = pd.merge(short_with_img, long_with_img, on='artist').head(8)
    drift_full['change'] = drift_full['long_rank'] - drift_full['short_rank']
    drift_full = drift_full.sort_values('change', ascending=False)

    drift_records = []
    for _, row in drift_full.iterrows():
        insights = get_artist_insights(row['artist'], df_top)
        drift_records.append({
        'artist': row['artist'],
        'change': int(row['change']),
        'album_image': row['album_image'],
        'insights': insights
    })

    return jsonify({
        'top_artists': {'labels': top_artists.index.tolist(), 'values': top_artists.values.tolist()},
        'hour_counts': {'labels': list(range(24)), 'values': hour_counts.values.tolist()},
        'day_counts': {'labels': day_order, 'values': day_counts.values.tolist()},
        'drift': drift_records,
        'top10': top10_now[['track_name','artist','track_id','album_image']].to_dict(orient='records'),
        'top_scored': df_scored.head(5)[['track_name','artist','taste_score','track_id','album_image']].to_dict(orient='records')
    })

@app.route('/api/queue')
def queue():
    df_scored, _, _ = compute_scores()
    q = generate_queue(df_scored)
    return jsonify(q)

@app.route('/api/refresh')
def refresh():
    try:
        subprocess.run(['python', 'collect_data.py'], check=True, capture_output=True)
        return jsonify({'status': 'success', 'message': 'Data refreshed successfully'})
    except subprocess.CalledProcessError as e:
        return jsonify({'status': 'error', 'message': str(e)})
@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/queue')
def queue_page():
    return render_template('queue.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)