# Murmur — AI Meeting Notes That Run Locally

> **Open-source, privacy-first AI note-taking app.** Records meeting audio, transcribes speech to text with Whisper, and generates structured meeting notes using any LLM — all running locally on your machine. No cloud. No subscriptions. Your data stays yours.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://github.com/GauravRatnawat/murmur/actions/workflows/python-app.yml/badge.svg)](https://github.com/GauravRatnawat/murmur/actions)

## Why Murmur?

Most AI meeting note apps send your audio to the cloud. Murmur runs **entirely on your machine** — your conversations never leave your computer.

- **Local-first AI transcription** — OpenAI Whisper, faster-whisper, or MLX Whisper (Apple Silicon GPU)
- **Any LLM provider** — Ollama (fully local), Anthropic, OpenAI, Gemini, Groq
- **One command** — `murmur notes` records, transcribes, and summarizes in a single pipeline
- **Auto-meeting detection** — detects Zoom, Teams, WebEx, Slack, FaceTime and starts recording
- **Speaker diarization** — identifies who said what using pyannote.audio
- **Live transcription** — see real-time text while recording
- **Export anywhere** — PDF, DOCX, or clipboard
- **Interactive TUI** — terminal dashboard with keyboard shortcuts
- **Works with any meeting app** — Teams, Google Meet, Zoom, Slack, Discord, etc.

## Features

| Feature | CLI | TUI | Description |
|---------|-----|-----|-------------|
| Record audio | `murmur record` | `r` | Captures mic + system audio |
| Transcribe | `murmur transcribe` | `t` | Speech-to-text via Whisper |
| Summarize | `murmur summarize` | `n` | Structured notes via LLM |
| Full pipeline | `murmur notes` | — | Record + transcribe + summarize |
| Copy to clipboard | `murmur copy` | `c` | Copy notes/transcript |
| Export PDF/DOCX | `murmur export` | `e` | Export notes to file |
| Auto-record meetings | `murmur watch` | `w` | Detect meeting apps, auto-record |
| Speaker labels | `--diarize` | — | Who said what |
| Backend selection | `--backend faster` | — | Choose transcription engine |
| Live transcript | — | automatic | Real-time text during recording |
| Interactive dashboard | `murmur tui` | — | Full TUI with keybindings |

## Quick Start

```bash
git clone https://github.com/GauravRatnawat/murmur.git
cd murmur
./setup.sh
```

The setup script lets you pick an LLM provider, installs dependencies, configures your API key, and walks you through macOS audio device setup.

### Fully Local Setup (No Cloud)

For a completely offline, privacy-first setup using Ollama:

```bash
pip install -e ".[ollama]"
# Make sure Ollama is running: ollama serve
echo "LLM_PROVIDER=ollama" > .env
murmur notes
```

## Usage

```bash
# Full pipeline: record, transcribe, summarize — one command
murmur notes

# Use a specific LLM provider
murmur notes --provider gemini
murmur notes --provider ollama     # fully local, no API key needed

# Individual steps
murmur record                      # record until Ctrl+C
murmur record -t 60                # record for 60 seconds
murmur transcribe                  # transcribe latest recording
murmur summarize                   # summarize latest transcript

# Faster transcription (4x faster on CPU)
murmur transcribe --backend faster

# Speaker diarization (who said what)
murmur transcribe --diarize

# Export and share
murmur copy                        # copy notes to clipboard
murmur export                      # export to PDF
murmur export -f docx              # export to DOCX

# Auto-record when meetings start
murmur watch                       # detects Zoom, Teams, etc.

# Interactive TUI dashboard
murmur tui

# Utilities
murmur devices                     # list audio devices
murmur ls                          # list all saved files
```

## Supported LLM Providers

| Provider | Cost | Local? | API Key | Install |
|----------|------|--------|---------|---------|
| **Ollama** | Free | Yes | No | `pip install -e ".[ollama]"` |
| Groq | Free tier | No | Yes | `pip install -e ".[groq]"` |
| Google Gemini | Free tier | No | Yes (no credit card) | `pip install -e ".[gemini]"` |
| Anthropic (Claude) | Paid | No | Yes | `pip install -e ".[anthropic]"` |
| OpenAI (GPT) | Paid | No | Yes | `pip install -e ".[openai]"` |

## Transcription Backends

| Backend | Speed | Hardware | Install |
|---------|-------|----------|---------|
| `whisper` (default) | Baseline | CPU | Included |
| `faster` | ~4x faster | CPU (CTranslate2) | `pip install -e ".[faster]"` |
| `mlx` | GPU-accelerated | Apple Silicon | `pip install -e ".[mlx]"` |

## How It Works

```
Meeting audio ──→ Record ──→ Transcribe (Whisper) ──→ Summarize (LLM) ──→ Markdown notes
                    │              │                        │
                    ▼              ▼                        ▼
               data/recordings/  data/transcripts/    data/notes/
                  *.wav             *.txt                *.md
```

All data is stored locally in the `data/` directory. Nothing is sent to the cloud unless you choose a cloud LLM provider.

## Project Structure

```
murmur/
├── murmur/
│   ├── cli.py              # Click CLI commands
│   ├── tui.py              # Textual TUI dashboard
│   ├── config.py           # Settings (audio, model, paths)
│   ├── recorder.py         # Audio recording via sounddevice
│   ├── transcriber.py      # Speech-to-text orchestration
│   ├── summarizer.py       # Meeting notes via LLM
│   ├── llm.py              # Multi-provider LLM dispatch
│   ├── watcher.py          # Auto-meeting detection (psutil)
│   ├── diarizer.py         # Speaker diarization (pyannote)
│   ├── live_transcriber.py # Real-time transcription
│   └── backends/           # Pluggable transcription engines
│       ├── _whisper.py     # OpenAI Whisper
│       ├── _faster_whisper.py  # faster-whisper (CTranslate2)
│       └── _mlx_whisper.py     # MLX Whisper (Apple Silicon)
├── tests/                  # 87 tests
├── data/                   # Local data (gitignored)
└── docs/
    └── setup_audio.md      # macOS audio setup guide
```

## macOS Audio Setup

Murmur captures both your microphone and system audio (e.g., the other person on a Zoom call). On macOS, this requires [BlackHole](https://github.com/ExistentialAudio/BlackHole) (free, open-source virtual audio driver).

```bash
brew install blackhole-2ch
```

See [docs/setup_audio.md](docs/setup_audio.md) for the full setup guide.

### Before a meeting

1. Set **System Settings > Sound > Output** to **Multi-Output Device**
2. Run `murmur notes` (or `murmur watch` for auto-detection)
3. After the meeting, switch output back to normal speakers

## Optional Dependencies

```bash
pip install -e ".[clipboard]"   # pyperclip — clipboard copy
pip install -e ".[export]"      # pypandoc — PDF/DOCX export
pip install -e ".[faster]"      # faster-whisper — 4x faster CPU transcription
pip install -e ".[mlx]"         # mlx-whisper — Apple Silicon GPU transcription
pip install -e ".[watch]"       # psutil — auto-meeting detection
pip install -e ".[diarize]"     # pyannote.audio — speaker diarization
pip install -e ".[tui]"         # textual — interactive TUI dashboard
pip install -e ".[all]"         # everything (except mlx and diarize)
```

## License

MIT
