#!/bin/bash
set -e

echo "=== Notetaking Setup ==="
echo ""

# 1. Install Python package
echo "[1/4] Installing Python package..."
pip install -e . --quiet
echo "  Done."
echo ""

# 2. Install BlackHole
if brew list blackhole-2ch &>/dev/null; then
    echo "[2/4] BlackHole already installed. Skipping."
else
    echo "[2/4] Installing BlackHole (virtual audio driver)..."
    brew install blackhole-2ch
    echo "  Done."
fi
echo ""

# 3. API key
if [ -f .env ] && grep -q "ANTHROPIC_API_KEY=sk-ant-" .env; then
    echo "[3/4] API key already configured. Skipping."
else
    echo "[3/4] Anthropic API key setup"
    echo "  Get a key from: https://console.anthropic.com/settings/keys"
    echo ""
    read -rp "  Paste your API key (sk-ant-...): " api_key
    if [ -z "$api_key" ]; then
        echo "  Skipped. Add it later to .env"
        cp -n .env.example .env 2>/dev/null || true
    else
        echo "ANTHROPIC_API_KEY=$api_key" > .env
        echo "  Saved to .env"
    fi
fi
echo ""

# 4. Audio device setup
echo "[4/4] macOS audio device setup"
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
notetaking devices
echo ""
echo "Testing import..."
python -c "from notetaking.config import ANTHROPIC_API_KEY; print(f'API key: {\"configured\" if ANTHROPIC_API_KEY else \"missing\"}')"
echo ""
echo "=== Setup complete! ==="
echo ""
echo "Usage:"
echo "  notetaking notes     # full pipeline: record → transcribe → summarize"
echo "  notetaking record    # record only"
echo "  notetaking --help    # all commands"
echo ""
echo "Before a meeting, set System Settings → Sound → Output → Multi-Output Device"
