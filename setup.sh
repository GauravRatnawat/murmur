#!/bin/bash
set -e

echo "=== Murmur Setup ==="
echo ""

# 1. Pick LLM provider
echo "[1/4] Choose your LLM provider:"
echo ""
echo "  1) Anthropic (Claude)        — paid, needs API key"
echo "  2) OpenAI (GPT)              — paid, needs API key"
echo "  3) Google Gemini              — free tier, needs API key (no credit card)"
echo "  4) Groq                       — free tier, needs API key"
echo "  5) Ollama                     — free, runs locally, no API key"
echo ""
read -rp "  Pick [1-5] (default 1): " choice
choice=${choice:-1}

case $choice in
    1) provider="anthropic"; pip_extra="anthropic"; env_var="ANTHROPIC_API_KEY"; key_url="https://console.anthropic.com/settings/keys" ;;
    2) provider="openai";    pip_extra="openai";    env_var="OPENAI_API_KEY";    key_url="https://platform.openai.com/api-keys" ;;
    3) provider="gemini";    pip_extra="gemini";    env_var="GEMINI_API_KEY";    key_url="https://aistudio.google.com/apikey" ;;
    4) provider="groq";      pip_extra="groq";      env_var="GROQ_API_KEY";      key_url="https://console.groq.com/keys" ;;
    5) provider="ollama";    pip_extra="ollama";    env_var="";                   key_url="" ;;
    *) echo "Invalid choice"; exit 1 ;;
esac
echo ""

# 2. Install Python package + chosen provider SDK
echo "[2/4] Installing Python package with $provider support..."
pip install -e ".[$pip_extra]" --quiet
echo "  Done."
echo ""

# 3. Install BlackHole
if brew list blackhole-2ch &>/dev/null; then
    echo "[3/4] BlackHole already installed. Skipping."
else
    echo "[3/4] Installing BlackHole (virtual audio driver)..."
    brew install blackhole-2ch
    echo "  Done."
fi
echo ""

# 4. API key + .env
echo "[4/4] Configuring .env"
if [ -f .env ]; then
    echo "  .env already exists."
else
    cp .env.example .env
fi

# Set provider
sed -i '' "s/^LLM_PROVIDER=.*/LLM_PROVIDER=$provider/" .env

if [ -n "$env_var" ]; then
    current=$(grep "^$env_var=" .env 2>/dev/null | cut -d= -f2-)
    if [ -n "$current" ] && [[ "$current" != *"your-key"* ]]; then
        echo "  $env_var already set. Skipping."
    else
        echo "  Get a key from: $key_url"
        echo ""
        read -rp "  Paste your API key: " api_key
        if [ -z "$api_key" ]; then
            echo "  Skipped. Add $env_var to .env later."
        else
            # Uncomment and set the key
            sed -i '' "s|^# *$env_var=.*|$env_var=$api_key|" .env
            sed -i '' "s|^$env_var=.*|$env_var=$api_key|" .env
            echo "  Saved to .env"
        fi
    fi
else
    echo "  Ollama selected — no API key needed."
    echo "  Make sure Ollama is running: ollama serve"
fi
echo ""

# 5. Audio device setup
echo "macOS audio device setup"
echo ""
echo "  You need to create two devices in Audio MIDI Setup:"
echo ""
echo "  a) Aggregate Device (combines mic + system audio for recording)"
echo "     - Check: MacBook Pro Microphone"
echo "     - Check: BlackHole 2ch (enable Drift Correction)"
echo ""
echo "  b) Multi-Output Device (lets you hear audio + routes it to BlackHole)"
echo "     - Check: MacBook Pro Speakers"
echo "     - Check: BlackHole 2ch (enable Drift Correction)"
echo ""
read -rp "  Open Audio MIDI Setup now? [Y/n] " open_midi
if [[ ! "$open_midi" =~ ^[Nn]$ ]]; then
    open /Applications/Utilities/Audio\ MIDI\ Setup.app
    echo ""
    read -rp "  Press Enter when done setting up devices..."
fi

# Verify
echo ""
echo "=== Verifying setup ==="
echo ""
echo "Devices:"
murmur devices
echo ""
echo "Provider: $provider"
echo ""
echo "=== Setup complete! ==="
echo ""
echo "Usage:"
echo "  murmur notes                  # full pipeline: record → transcribe → summarize"
echo "  murmur summarize -p gemini    # summarize with a specific provider"
echo "  murmur record                 # record only"
echo "  murmur --help                 # all commands"
echo ""
echo "Before a meeting, set System Settings → Sound → Output → Multi-Output Device"
