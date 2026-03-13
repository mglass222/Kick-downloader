"""Kick.com API client — checks channel live status via the v2 API."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from curl_cffi import requests as curl_requests

log = logging.getLogger(__name__)

API_URL = "https://kick.com/api/v2/channels/{slug}"

REQUEST_TIMEOUT = 30


@dataclass
class ChannelStatus:
    slug: str
    is_live: bool
    playback_url: str | None = None
    title: str | None = None
    viewer_count: int | None = None
    started_at: str | None = None


def get_channel_status(slug: str) -> ChannelStatus:
    """Query the Kick v2 API for a channel's live status.

    Uses curl_cffi to impersonate a real browser TLS fingerprint,
    which is required to avoid Kick's 403 bot detection.

    Returns a ChannelStatus. On errors, returns is_live=False.
    """
    url = API_URL.format(slug=slug)
    try:
        resp = curl_requests.get(
            url,
            impersonate="chrome",
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except curl_requests.RequestsError as exc:
        log.warning("Request failed for channel '%s': %s", slug, exc)
        return ChannelStatus(slug=slug, is_live=False)
    except Exception as exc:
        log.warning("Unexpected error for channel '%s': %s", slug, exc)
        return ChannelStatus(slug=slug, is_live=False)

    livestream = data.get("livestream")
    if not livestream:
        return ChannelStatus(slug=slug, is_live=False)

    return ChannelStatus(
        slug=slug,
        is_live=True,
        playback_url=livestream.get("playback_url"),
        title=livestream.get("session_title"),
        viewer_count=livestream.get("viewer_count"),
        started_at=livestream.get("created_at"),
    )
