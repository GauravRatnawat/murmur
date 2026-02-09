# macOS Audio Setup for Meeting Recording

This tool captures both your **microphone** and **system audio** (e.g., the other person on a Zoom/Meet call). On macOS, this requires a virtual audio driver and some one-time configuration.

## Prerequisites

Install **BlackHole 2ch** (free, open-source virtual audio driver):

```bash
brew install blackhole-2ch
```

## Setup Steps

Open **Audio MIDI Setup** (search in Spotlight or find it in `/Applications/Utilities/`).

### 1. Create a Multi-Output Device

This lets you hear system audio normally while also routing it to BlackHole for capture.

1. Click the **+** button at the bottom-left → **Create Multi-Output Device**
2. Check these devices (in this order):
   - **MacBook Pro Speakers** (or your preferred output)
   - **BlackHole 2ch**
3. Rename it to **Multi-Output** (right-click → rename)
4. Make sure **Drift Correction** is checked for BlackHole 2ch

### 2. Create an Aggregate Device

This combines your microphone and BlackHole into a single input device the recorder can use.

1. Click the **+** button → **Create Aggregate Device**
2. Check these devices:
   - **MacBook Pro Microphone** (or your preferred mic)
   - **BlackHole 2ch**
3. Rename it to **Aggregate** (right-click → rename)
4. Make sure **Drift Correction** is checked for BlackHole 2ch

### 3. Set System Output

Before starting a meeting:

1. Go to **System Settings → Sound → Output**
2. Select **Multi-Output** as your output device

This ensures system audio plays through your speakers AND gets captured by BlackHole.

## How It Works

```
Your mic ──────────────────────┐
                               ├──→ Aggregate Device ──→ murmur recorder
System audio ──→ Multi-Output ─┤
                   ├──→ Speakers (you hear it)
                   └──→ BlackHole 2ch ─┘
```

## Verify Setup

```bash
python -m murmur devices
```

You should see **Aggregate** and **Multi-Output** in the device list.

## Notes

- You can adjust the sample rate of BlackHole in Audio MIDI Setup (default 48000 Hz matches this tool's settings)
- If you get "no input channels" errors, make sure your Aggregate Device has at least one input device checked
- After a meeting, switch your output back to normal speakers if you don't want the Multi-Output routing active
