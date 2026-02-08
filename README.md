# Notetaking

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
notetaking/
├── notetaking/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py            # Click CLI commands
│   ├── config.py         # Settings (audio, model, paths)
│   ├── llm.py            # Multi-provider LLM dispatch
│   ├── recorder.py       # Audio recording via sounddevice
│   ├── transcriber.py    # Speech-to-text via Whisper
│   └── summarizer.py     # Meeting notes via LLM
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
git clone https://github.com/GauravRatnawat/notetaking.git
cd notetaking
./setup.sh
```

This single script lets you pick an LLM provider, installs the right SDK, sets up your API key, installs BlackHole, and walks you through audio device configuration.

For manual setup or details on audio devices, see [docs/setup_audio.md](docs/setup_audio.md).

## Usage

```bash
# Full pipeline: record → transcribe → summarize
notetaking notes

# Use a specific provider
notetaking notes --provider gemini
notetaking summarize --provider groq

# Individual steps
notetaking record              # record until Ctrl+C
notetaking record -t 60        # record for 60 seconds
notetaking transcribe          # transcribe latest recording
notetaking summarize           # summarize latest transcript

# Utilities
notetaking devices             # list audio devices
notetaking ls                  # list all saved files
```

### Switching providers

Set `LLM_PROVIDER` in `.env` to change the default, or use `--provider` / `-p` on any command:

```bash
# .env
LLM_PROVIDER=gemini

# or per-command
notetaking summarize -p ollama
```

### Before a meeting

1. Set **System Settings → Sound → Output** to **Multi-Output Device**
2. Run `notetaking notes` (or `notetaking record`)
3. After the meeting, switch output back to normal speakers

## License

MIT
