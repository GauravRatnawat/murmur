from pathlib import Path

import anthropic

from notetaking.config import ANTHROPIC_API_KEY, CLAUDE_MODEL, NOTES_DIR

SYSTEM_PROMPT = """You are a meeting notes assistant. Given a meeting transcript, produce clean, structured meeting notes in Markdown format.

Your output must include these sections:

## Summary
A concise 2-3 sentence overview of the meeting.

## Key Discussion Points
Bulleted list of the main topics discussed.

## Action Items
Bulleted list of action items, with owners if identifiable from the transcript.

## Decisions Made
Bulleted list of any decisions that were reached during the meeting.

If a section has no relevant content, write "None identified." under it."""


def summarize(transcript_path: str) -> str:
    """Summarize a transcript using Claude.

    Returns the path to the saved notes file.
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Add it to your .env file."
        )

    transcript_path = Path(transcript_path)
    stem = transcript_path.stem
    notes_path = NOTES_DIR / f"{stem}.md"

    # Read just the full text portion (before timestamped segments)
    raw = transcript_path.read_text()
    if "=== TIMESTAMPED SEGMENTS ===" in raw:
        transcript_text = raw.split("=== TIMESTAMPED SEGMENTS ===")[0]
    else:
        transcript_text = raw

    # Clean up header
    transcript_text = transcript_text.replace("=== TRANSCRIPT ===", "").strip()

    if not transcript_text:
        raise RuntimeError("Transcript is empty")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    print(f"Summarizing {transcript_path.name} with Claude...")
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Here is the meeting transcript:\n\n{transcript_text}",
            }
        ],
    )

    notes_content = f"# Meeting Notes: {stem}\n\n"
    notes_content += message.content[0].text

    notes_path.write_text(notes_content)
    print(f"Notes saved to {notes_path}")
    return str(notes_path)
