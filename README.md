# Murmur

A CLI tool that records meeting audio, transcribes it with Whisper, and generates structured meeting notes using your choice of LLM.

Works with any app that plays audio through system output — Teams, Google Meet, Zoom, Slack, etc.

## Supported LLM Providers

| Provider | Cost | API Key | Install |
|----------|------|---------|---------|
| Anthropic (Claude) | Paid | Yes | `pip install -e ".[anthropic]"` |
| OpenAI (GPT) | Paid | Yes | `pip install -e ".[openai]"` |
| Google Gemini | Free tier | Yes (no credit card) | `pip install -e ".[gemini]"` |
| Groq | Free tier | Yes | `pip install -e ".[groq]"` |
| Ollama | Free (local) | No | `pip install -e ".[ollama]"` |

## Project Structure

```
murmur/
├── murmur/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py            # Click CLI commands
│   ├── config.py         # Settings (audio, model, paths)
│   ├── llm.py            # Multi-provider LLM dispatch
│   ├── recorder.py       # Audio recording via sounddevice
│   ├── transcriber.py    # Speech-to-text via Whisper
│   ├── summarizer.py     # Meeting notes via LLM
│   ├── tui.py            # Textual TUI dashboard
│   ├── watcher.py        # Auto-meeting detection
│   ├── diarizer.py       # Speaker diarization
│   ├── live_transcriber.py # Live transcription
│   └── backends/         # Pluggable transcription backends
│       ├── __init__.py
│       ├── _whisper.py
│       ├── _faster_whisper.py
│       └── _mlx_whisper.py
├── data/
│   ├── recordings/       # .wav files (gitignored)
│   ├── transcripts/      # .txt files (gitignored)
│   └── notes/            # .md files (gitignored)
├── docs/
│   └── setup_audio.md    # macOS audio setup guide
├── pyproject.toml
├── requirements.txt
├── .env.example
└── .gitignore
```

## Setup

```bash
git clone https://github.com/GauravRatnawat/murmur.git
cd murmur
./setup.sh
```

This single script lets you pick an LLM provider, installs the right SDK, sets up your API key, installs BlackHole, and walks you through audio device configuration.

For manual setup or details on audio devices, see [docs/setup_audio.md](docs/setup_audio.md).

## Usage

```bash
# Full pipeline: record → transcribe → summarize
murmur notes

# Use a specific provider
murmur notes --provider gemini
murmur summarize --provider groq

# Individual steps
murmur record              # record until Ctrl+C
murmur record -t 60        # record for 60 seconds
murmur transcribe          # transcribe latest recording
murmur summarize           # summarize latest transcript

# New features
murmur copy                # copy notes to clipboard
murmur export              # export notes to PDF
murmur export -f docx      # export to DOCX
murmur watch               # auto-record when meeting detected
murmur transcribe --backend faster   # use faster-whisper
murmur transcribe --diarize          # speaker diarization
murmur tui                 # interactive TUI dashboard

# Utilities
murmur devices             # list audio devices
murmur ls                  # list all saved files
```

### Switching providers

Set `LLM_PROVIDER` in `.env` to change the default, or use `--provider` / `-p` on any command:

```bash
# .env
LLM_PROVIDER=gemini

# or per-command
murmur summarize -p ollama
```

### Before a meeting

1. Set **System Settings → Sound → Output** to **Multi-Output Device**
2. Run `murmur notes` (or `murmur record`)
3. After the meeting, switch output back to normal speakers

## License

MIT
