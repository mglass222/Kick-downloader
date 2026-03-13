# Kick.com Stream Auto-Recorder — Implementation Plan

## Overview

A Python GUI application that monitors a user-managed list of Kick.com streamers, polls them every 5 minutes to detect when they go live, and automatically records their streams using **yt-dlp**. Recording stops when the stream ends (offline or raid). The GUI provides full control over the streamer list, displays live/recording status, and allows starting/stopping recordings manually.

---

## Technology Stack

| Component | Choice | Why |
|---|---|---|
| Language | **Python 3.10+** | yt-dlp ecosystem, simple async, rich HTTP libraries |
| GUI | **CustomTkinter** | Modern-looking tkinter wrapper, no heavy dependencies, cross-platform |
| Recording | **yt-dlp** (subprocess) | Built-in Kick.com extractor, handles HLS, quality selection, reconnection |
| Live detection | **Kick v2 API** (`/api/v2/channels/{slug}`) | No auth needed, returns `livestream` object + `playback_url` |
| HTTP client | **httpx** | Async support, clean API |
| Persistence | **JSON file** (`streamers.json`) | Stores the streamer list and settings between sessions |
| Muxing | **ffmpeg** (used internally by yt-dlp) | System dependency |

---

## GUI Design

### Main Window Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Kick Stream Recorder                              [─][□][×] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─── Add Streamer ───────────────────────────────────────┐ │
│  │  Channel slug: [________________]  [Add]               │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─── Streamer List ──────────────────────────────────────┐ │
│  │  Name            Status        Recording     Actions   │ │
│  │  ─────────────── ──────────── ──────────── ────────── │ │
│  │  xqc             🟢 LIVE      ● REC 02:34   [Stop][X] │ │
│  │  kaicenat         ○ Offline    —             [X]       │ │
│  │  hasanabi         ○ Offline    —             [X]       │ │
│  │  trainwreckstv   🟢 LIVE      ● REC 00:12   [Stop][X] │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─── Settings ───────────────────────────────────────────┐ │
│  │  Poll interval: [300] sec   Output dir: [./recordings] │ │
│  │  [Browse...]                                           │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─── Log ────────────────────────────────────────────────┐ │
│  │  [18:04:32] Monitoring started for 4 streamers         │ │
│  │  [18:05:01] xqc is LIVE — started recording            │ │
│  │  [18:05:03] trainwreckstv is LIVE — started recording  │ │
│  │  [18:10:01] Polling 4 channels...                      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  [ Start Monitoring ]  [ Stop Monitoring ]                  │
└─────────────────────────────────────────────────────────────┘
```

### GUI Features

- **Add/Remove streamers** — Type a Kick channel slug and click Add. Remove with the X button.
- **Streamer list table** — Shows each streamer's name, live/offline status, recording state (with elapsed time), and action buttons.
- **Per-streamer controls** — Stop an individual recording manually, or remove a streamer from the list.
- **Global controls** — Start/Stop monitoring toggle button.
- **Settings panel** — Configure poll interval and output directory (with folder browser dialog).
- **Log panel** — Scrollable text area showing timestamped events (live detection, recording start/stop, errors).
- **Persistent state** — Streamer list and settings are saved to `streamers.json` on every change and loaded on startup.

---

## Project Structure

```
Kick-downloader/
├── .gitignore
├── requirements.txt          # yt-dlp, httpx, customtkinter
├── streamers.json            # Persisted streamer list + settings (created at runtime)
├── src/
│   ├── __init__.py
│   ├── main.py               # Entry point — launches GUI
│   ├── config.py             # Settings dataclass, load/save streamers.json
│   ├── kick_api.py           # Hits /api/v2/channels/{slug}, returns ChannelStatus
│   ├── monitor.py            # Background polling loop, manages per-streamer state
│   ├── recorder.py           # Manages yt-dlp subprocess per streamer (start/stop/is_alive)
│   └── gui/
│       ├── __init__.py
│       ├── app.py            # Main window, layout, CustomTkinter setup
│       ├── streamer_list.py  # Streamer table widget with status indicators
│       ├── add_streamer.py   # Add streamer input bar
│       ├── settings_panel.py # Poll interval + output dir controls
│       └── log_panel.py      # Scrollable log text area
├── recordings/               # Default output directory (created at runtime)
└── tests/
    ├── test_kick_api.py
    ├── test_monitor.py
    └── test_recorder.py
```

---

## How Each Piece Works

### 1. Streamer List & Persistence (`config.py`)

Data model stored in `streamers.json`:
```json
{
  "settings": {
    "poll_interval_seconds": 300,
    "output_dir": "./recordings",
    "filename_template": "{channel}_{date}_{time}"
  },
  "streamers": [
    { "slug": "xqc", "enabled": true },
    { "slug": "kaicenat", "enabled": true },
    { "slug": "hasanabi", "enabled": true }
  ]
}
```

- Loaded on startup, saved on every add/remove/settings change.
- Each streamer has an `enabled` flag (for future use — temporarily disable without removing).

### 2. Live Detection (`kick_api.py`)
- `GET https://kick.com/api/v2/channels/{slug}` with browser-like `User-Agent`
- Response has `livestream` key: a dict when live, `null` when offline
- Returns a `ChannelStatus(is_live, playback_url, title, started_at)`
- Polls all streamers in the list each cycle, with a small stagger (1-2 sec between requests) to avoid rate limits

### 3. Polling Loop (`monitor.py`)
- Runs in a **background thread** (not asyncio) to avoid blocking the GUI
- Maintains per-streamer state machines: **IDLE**, **RECORDING**
- Every poll cycle: iterate all streamers → check API → start/stop recordings as needed
- Communicates with the GUI via thread-safe queue or `tkinter.after()` callbacks
- Failed API polls for one streamer do not affect others

### 4. Recording (`recorder.py`)
- One yt-dlp subprocess per streamer (multiple simultaneous recordings supported)
- Spawns: `yt-dlp https://kick.com/{slug} -o recordings/{slug}_{date}_{time}.mp4 --no-part --live-from-start`
- yt-dlp handles extracting the m3u8, selecting best quality, and writing the file
- Stop = send `SIGINT` (yt-dlp finalizes the file cleanly on interrupt)
- yt-dlp **self-terminates** when the HLS playlist signals end-of-stream (raids, going offline)
- Tracks recording start time for elapsed duration display in GUI

### 5. Raid/Offline Detection
- Raids end the stream → yt-dlp detects end-of-stream in the HLS playlist and exits
- The monitor's next poll confirms `is_live=false` and updates GUI state
- No special raid API needed — both mechanisms converge

### 6. GUI ↔ Backend Communication
- **GUI → Backend**: Direct method calls (add/remove streamer, start/stop monitoring, manual stop recording)
- **Backend → GUI**: Thread-safe callbacks via `root.after()` to update status indicators, log messages, and recording timers
- The monitor thread posts status updates to the GUI; the GUI never reads backend state directly

---

## Error Handling

| Scenario | Response |
|---|---|
| API poll fails (network/timeout) | Log warning, skip this streamer for this cycle, do NOT stop active recording |
| API returns 403 (rate limit) | Exponential backoff per-streamer (5m → 10m → 20m) |
| yt-dlp crashes mid-recording | Detect via exit code, log error, mark streamer as IDLE, partial file preserved |
| Brief stream interruption | yt-dlp handles HLS segment gaps internally |
| Disk full | yt-dlp errors out, detected via exit code, log error with warning |
| Invalid channel slug added | API returns 404, log "channel not found", remove or mark invalid in list |
| Multiple streamers live at once | Each gets its own yt-dlp subprocess — fully independent recordings |
| GUI closed while recording | Graceful shutdown: SIGINT all active yt-dlp processes, wait for finalization, then exit |

---

## Implementation Order

1. **`config.py`** — Settings + streamer list dataclass, JSON load/save
2. **`kick_api.py`** — API client, returns channel status
3. **`recorder.py`** — yt-dlp subprocess wrapper (start/stop/is_alive per streamer)
4. **`monitor.py`** — Background thread polling loop with per-streamer state
5. **`gui/app.py`** — Main window shell with CustomTkinter
6. **`gui/streamer_list.py`** — Streamer table with status indicators
7. **`gui/add_streamer.py`** — Add streamer input bar
8. **`gui/settings_panel.py`** — Poll interval + output dir controls
9. **`gui/log_panel.py`** — Scrollable log area
10. **`main.py`** — Entry point, wire GUI to backend
11. **Project scaffolding** (`.gitignore`, `requirements.txt`)

---

## Dependencies (`requirements.txt`)

```
yt-dlp>=2024.0.0
httpx>=0.27.0
customtkinter>=5.2.0
```

System requirements: Python 3.10+, ffmpeg (yt-dlp uses it for muxing).

---

## Optional Future Enhancements

- **Webhook-based detection** — Register a Kick App, subscribe to `livestream.status.updated` webhook for instant start (no 5-min delay)
- **Desktop notifications** — `notify-send` / system tray notifications when a streamer goes live
- **Per-streamer settings** — Custom output dir or filename template per streamer
- **Recording history** — Log of past recordings with file paths, duration, date
- **System tray mode** — Minimize to tray, keep monitoring in background
- **Auto-start on boot** — Systemd service or startup entry
