# Notetaking

A CLI tool that records meeting audio, transcribes it with Whisper, and generates structured meeting notes using Claude.

Works with any app that plays audio through system output — Teams, Google Meet, Zoom, Slack, etc.

## Project Structure

```
notetaking/
├── notetaking/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py            # Click CLI commands
│   ├── config.py         # Settings (audio, model, paths)
│   ├── recorder.py       # Audio recording via sounddevice
│   ├── transcriber.py    # Speech-to-text via Whisper
│   └── summarizer.py     # Meeting notes via Claude
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

### 1. Install dependencies

```bash
pip install -e .
```

### 2. Add your API key

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Get a key from [console.anthropic.com](https://console.anthropic.com).

### 3. macOS audio setup (for capturing both sides of a call)

Install BlackHole and configure Aggregate/Multi-Output devices. See [docs/setup_audio.md](docs/setup_audio.md) for step-by-step instructions.

## Usage

```bash
# Full pipeline: record → transcribe → summarize
notetaking notes

# Individual steps
notetaking record              # record until Ctrl+C
notetaking record -t 60        # record for 60 seconds
notetaking transcribe          # transcribe latest recording
notetaking summarize           # summarize latest transcript

# Utilities
notetaking devices             # list audio devices
notetaking ls                  # list all saved files
```

### Before a meeting

1. Set **System Settings → Sound → Output** to **Multi-Output Device**
2. Run `notetaking notes` (or `notetaking record`)
3. After the meeting, switch output back to normal speakers

## License

MIT
