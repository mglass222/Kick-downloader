# Kick Stream Recorder

A Python desktop application that monitors your favorite Kick.com streamers and automatically records their live streams for watching later.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Linux-lightgrey)

## Features

- **Streamer watchlist** — Build and manage a list of Kick.com streamers to monitor
- **Automatic recording** — Streams are recorded automatically when a streamer goes live
- **Multi-stream support** — Record multiple streamers simultaneously, each in its own process
- **Auto-stop** — Recording ends when the stream goes offline or the streamer raids another channel
- **Live status display** — See which streamers are live, their stream title, viewer count, and recording duration in real time
- **Configurable settings** — Adjustable poll interval and output directory
- **Persistent watchlist** — Your streamer list and settings are saved between sessions
- **Activity log** — Timestamped log of all events (polls, live detection, recording start/stop, errors)

## Screenshots

The GUI features a dark-themed interface with:
- An input bar to add streamers by their Kick channel name
- A streamer table showing live/offline status and recording state
- Settings for poll interval and recording output directory
- A scrollable activity log

## Requirements

- **Python 3.10+**
- **ffmpeg** — Used by yt-dlp for muxing recorded streams
- **tkinter** — Python GUI toolkit (system package)

### Installing system dependencies

**Ubuntu/Debian:**
```bash
sudo apt install python3-tk ffmpeg
```

**Fedora:**
```bash
sudo dnf install python3-tkinter ffmpeg
```

**Arch Linux:**
```bash
sudo pacman -S tk ffmpeg
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mglass222/Kick-downloader.git
   cd Kick-downloader
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Install curl_cffi** (required to bypass Kick's bot detection):
   ```bash
   pip install curl_cffi
   ```

## Usage

1. **Activate the virtual environment and launch:**
   ```bash
   cd Kick-downloader
   source .venv/bin/activate
   python -m src.main
   ```

2. **Add streamers** — Type a Kick channel slug (e.g. `xqc`, `gmhikaru`) into the input field and click **Add**.

3. **Start monitoring** — Click **Start Monitoring**. The app will poll all streamers in your list every 5 minutes (configurable).

4. **Automatic recording** — When a streamer goes live, recording starts automatically. The streamer's row will show a red `REC` indicator with elapsed time.

5. **Manual stop** — Click the **Stop** button on a streamer's row to end that recording early.

6. **Settings** — Adjust the poll interval (minimum 10 seconds) and output directory in the Settings panel. Click **Browse...** to select a folder.

7. **Closing** — When you close the window, all active recordings are gracefully stopped and finalized before the app exits.

## Configuration

Settings and your streamer list are stored in `streamers.json` (created automatically on first run):

```json
{
  "settings": {
    "poll_interval_seconds": 300,
    "output_dir": "./recordings",
    "filename_template": "{channel}_{date}_{time}"
  },
  "streamers": [
    { "slug": "xqc", "enabled": true },
    { "slug": "gmhikaru", "enabled": true }
  ]
}
```

## Recordings

- **Format:** MP4
- **Quality:** Best available (yt-dlp default)
- **Filename pattern:** `{channel}_{YYYY-MM-DD}_{HH-MM-SS}.mp4`
- **Default location:** `./recordings/`

## Project Structure

```
Kick-downloader/
├── requirements.txt          # Python dependencies
├── streamers.json            # Streamer list & settings (created at runtime)
├── src/
│   ├── main.py               # Entry point
│   ├── config.py             # Settings and streamer list persistence
│   ├── kick_api.py           # Kick.com API client (live detection)
│   ├── monitor.py            # Background polling loop
│   ├── recorder.py           # yt-dlp subprocess management
│   └── gui/
│       ├── app.py            # Main application window
│       ├── streamer_list.py  # Streamer table widget
│       ├── add_streamer.py   # Add streamer input bar
│       ├── settings_panel.py # Settings controls
│       └── log_panel.py      # Activity log panel
└── recordings/               # Recorded streams (created at runtime)
```

## How It Works

1. **Polling** — A background thread queries `https://kick.com/api/v2/channels/{slug}` for each streamer on your list. Requests use `curl_cffi` to impersonate a Chrome browser TLS fingerprint, which is necessary to avoid Kick's bot detection (403 responses).

2. **Recording** — When a channel's `livestream` field is non-null, the app spawns a `yt-dlp` subprocess pointed at `https://kick.com/{slug}`. yt-dlp extracts the HLS stream URL and records it to an MP4 file.

3. **Stop detection** — yt-dlp monitors the HLS playlist and exits when the stream ends. The polling loop also detects offline status via the API as a secondary check. Both mechanisms handle raids (which end the stream).

## Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'tkinter'` | Install the system package: `sudo apt install python3-tk` |
| `403 Forbidden` from Kick API | Ensure `curl_cffi` is installed. Plain HTTP clients are blocked by Kick's bot detection. |
| Timeouts when polling | Kick's API can be slow. The default 30-second timeout handles most cases. Check your network connection. |
| `yt-dlp` not found | Make sure `yt-dlp` is installed in your venv: `pip install yt-dlp` |
| Recording file is 0 bytes | The stream may have ended before data was captured. Check that ffmpeg is installed. |

## License

This project is open source and available under the [MIT License](LICENSE).
