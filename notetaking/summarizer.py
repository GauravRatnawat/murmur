import re
from pathlib import Path

from notetaking.config import LLM_PROVIDER, NOTES_DIR, RECORDINGS_DIR, TRANSCRIPTS_DIR
from notetaking.llm import call_llm

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


SLUG_SYSTEM_PROMPT = (
    "Generate a short kebab-case filename (3-5 words) for these meeting notes. "
    "Reply with ONLY the slug, nothing else. Example: product-roadmap-review"
)


def _sanitize_slug(raw_slug: str) -> str | None:
    """Sanitize a raw LLM slug into a clean kebab-case string, or None if unusable."""
    slug = raw_slug.strip().lower()
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    slug = slug[:50].strip("-")
    return slug or None


def _generate_smart_stem(
    old_stem: str, notes_text: str, provider: str
) -> str | None:
    """Generate a new stem like YYYYMMDD_HHMMSS_slug from the old meeting_ stem."""
    match = re.match(r"meeting_(\d{8}_\d{6})", old_stem)
    if not match:
        return None

    timestamp = match.group(1)

    try:
        raw_slug = call_llm(provider, SLUG_SYSTEM_PROMPT, notes_text[:500])
        slug = _sanitize_slug(raw_slug)
        if not slug:
            return None
        return f"{timestamp}_{slug}"
    except Exception:
        return None


def _rename_meeting_files(old_stem: str, new_stem: str) -> None:
    """Rename all meeting files from old_stem to new_stem across all directories."""
    for directory, ext in [
        (RECORDINGS_DIR, ".wav"),
        (TRANSCRIPTS_DIR, ".txt"),
        (NOTES_DIR, ".md"),
    ]:
        old_file = directory / f"{old_stem}{ext}"
        if old_file.exists():
            new_file = directory / f"{new_stem}{ext}"
            old_file.rename(new_file)


def summarize(transcript_path: str, provider: str | None = None, quiet: bool = False) -> str:
    """Summarize a transcript using an LLM.

    Returns the path to the saved notes file.
    """
    provider = provider or LLM_PROVIDER

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

    if not quiet:
        print(f"Summarizing {transcript_path.name} with {provider}...")
    user_message = f"Here is the meeting transcript:\n\n{transcript_text}"
    notes_text = call_llm(provider, SYSTEM_PROMPT, user_message)

    notes_content = f"# Meeting Notes: {stem}\n\n"
    notes_content += notes_text

    # Save notes first, then attempt smart rename
    notes_path.write_text(notes_content)

    new_stem = _generate_smart_stem(stem, notes_text, provider)
    if new_stem:
        _rename_meeting_files(stem, new_stem)
        notes_path = NOTES_DIR / f"{new_stem}.md"

    if not quiet:
        print(f"Notes saved to {notes_path}")
    return str(notes_path)
