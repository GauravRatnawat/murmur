import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RECORDINGS_DIR = DATA_DIR / "recordings"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
NOTES_DIR = DATA_DIR / "notes"

for d in (RECORDINGS_DIR, TRANSCRIPTS_DIR, NOTES_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Audio settings
SAMPLE_RATE = 48000
CHANNELS = 2
DEFAULT_DEVICE = "Aggregate"

# Whisper settings
WHISPER_MODEL = "base.en"

# Transcription backend
TRANSCRIPTION_BACKEND = os.getenv("TRANSCRIPTION_BACKEND", "whisper")

# LLM settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")
