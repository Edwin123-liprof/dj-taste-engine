"""Spotify auth for this app, including 6-month refresh-token expiry.

Spotify now invalidates refresh tokens 6 months after the user originally
authorized the app. Refreshing an access token does not extend that lifetime.
When the token endpoint returns invalid_grant, we discard the cached token
and send the user through the authorization code flow again.
"""

import json
import os
from datetime import datetime, timedelta, timezone

import spotipy
from dotenv import load_dotenv
from spotipy.cache_handler import CacheFileHandler
from spotipy.oauth2 import SpotifyOAuth, SpotifyOauthError

load_dotenv()

_ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(_ROOT, ".cache")
META_PATH = os.path.join(_ROOT, ".cache_meta.json")
SCOPE = "user-read-recently-played user-top-read"
REFRESH_TOKEN_LIFETIME = timedelta(days=180)


class ReauthRequired(Exception):
    """Cached Spotify token is missing or expired; sign-in is required."""


def is_invalid_grant(exc):
    error = (getattr(exc, "error", None) or "").lower()
    description = (getattr(exc, "error_description", None) or "").lower()
    message = str(exc).lower()
    return (
        error == "invalid_grant"
        or "invalid_grant" in description
        or "invalid_grant" in message
    )


def discard_cached_token():
    """Drop the stored token so the next sign-in issues a new refresh token."""
    for path in (CACHE_PATH, META_PATH):
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


def _read_authorized_at():
    try:
        with open(META_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        authorized_at = datetime.fromisoformat(raw["authorized_at"])
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    if authorized_at.tzinfo is None:
        authorized_at = authorized_at.replace(tzinfo=timezone.utc)
    return authorized_at


def _write_authorized_at():
    payload = {"authorized_at": datetime.now(timezone.utc).isoformat()}
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f)


def _is_authorization_stale():
    authorized_at = _read_authorized_at()
    if authorized_at is None:
        return False
    return datetime.now(timezone.utc) - authorized_at >= REFRESH_TOKEN_LIFETIME


def _oauth(open_browser=True, show_dialog=False):
    return SpotifyOAuth(
        scope=SCOPE,
        cache_handler=CacheFileHandler(cache_path=CACHE_PATH),
        open_browser=open_browser,
        show_dialog=show_dialog,
    )


def get_session_status():
    """Check the cached session without opening a browser.

    If the refresh token is expired (invalid_grant) or past our 6-month
    record, the cache is discarded and not retried.
    """
    if _is_authorization_stale():
        discard_cached_token()
        return {"ok": False, "reason": "refresh_token_expired"}

    auth = _oauth(open_browser=False)
    token = auth.cache_handler.get_cached_token()
    if not token:
        return {"ok": False, "reason": "no_token"}

    try:
        token_info = auth.validate_token(token)
    except SpotifyOauthError as exc:
        if is_invalid_grant(exc):
            discard_cached_token()
            return {"ok": False, "reason": "refresh_token_expired"}
        raise

    if token_info is None:
        return {"ok": False, "reason": "no_token"}
    return {"ok": True}


def get_spotify_client(allow_browser=True):
    """Return an authenticated Spotify client.

    When the stored refresh token is dead, the cache is discarded first.
    If allow_browser is True, Spotipy then opens the sign-in flow so a new
    refresh token can be issued. If False, raises ReauthRequired instead.
    """
    status = get_session_status()
    if status["ok"]:
        return spotipy.Spotify(auth_manager=_oauth(open_browser=False))

    if not allow_browser:
        reason = status.get("reason", "no_token")
        if reason == "refresh_token_expired":
            raise ReauthRequired(
                "Your Spotify login expired. Refresh tokens now last 6 months. "
                "Sign in again to continue."
            )
        raise ReauthRequired("No Spotify session found. Sign in to continue.")

    if status.get("reason") == "refresh_token_expired":
        print(
            "Spotify refresh token expired (they now last 6 months). "
            "Opening the sign-in flow to get a new one..."
        )
    else:
        print("No Spotify session found. Opening the sign-in flow...")

    auth = _oauth(open_browser=True, show_dialog=True)
    auth.get_access_token(as_dict=False, check_cache=False)
    _write_authorized_at()
    return spotipy.Spotify(auth_manager=auth)
