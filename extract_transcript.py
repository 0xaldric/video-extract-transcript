"""Extract the full transcript from a YouTube video.

Usage:
    python extract_transcript.py "https://www.youtube.com/watch?v=fv8zpYI9n6s"
    python extract_transcript.py fv8zpYI9n6s --languages en vi
    python extract_transcript.py <url> --output my_transcript

Outputs three files next to the script:
    <video_id>.txt    plain text, one line per caption segment
    <video_id>.srt    SubRip subtitles with timestamps
    <video_id>.json   raw segments (text + start + duration)
"""

import argparse
import json
import re
import sys
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)


def extract_video_id(url_or_id: str) -> str:
    """Accept a full YouTube URL or a bare 11-character video id."""
    # Already a bare id.
    if re.fullmatch(r"[0-9A-Za-z_-]{11}", url_or_id):
        return url_or_id

    patterns = [
        r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    raise ValueError(f"Could not extract a video id from: {url_or_id!r}")


def format_timestamp(seconds: float) -> str:
    """Convert seconds to an SRT timestamp: HH:MM:SS,mmm."""
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def to_srt(segments: list[dict]) -> str:
    """Render segments as SubRip (.srt) subtitles."""
    blocks = []
    for index, seg in enumerate(segments, start=1):
        start = format_timestamp(seg["start"])
        end = format_timestamp(seg["start"] + seg["duration"])
        text = seg["text"].replace("\n", " ").strip()
        blocks.append(f"{index}\n{start} --> {end}\n{text}\n")
    return "\n".join(blocks)


def fetch_segments(video_id: str, languages: list[str]) -> list[dict]:
    """Fetch transcript segments, preferring the requested languages.

    Falls back to any available transcript (including auto-generated ones)
    so we always return *something* if captions exist at all.
    """
    api = YouTubeTranscriptApi()

    # First try the caller's preferred languages directly.
    try:
        fetched = api.fetch(video_id, languages=languages)
        return [
            {"text": s.text, "start": s.start, "duration": s.duration}
            for s in fetched
        ]
    except NoTranscriptFound:
        pass  # Fall through to "grab whatever exists".

    transcript_list = api.list(video_id)
    transcript = next(iter(transcript_list))  # first available transcript
    print(
        f"  Requested {languages} not found; "
        f"using '{transcript.language}' ({transcript.language_code}) instead.",
        file=sys.stderr,
    )
    fetched = transcript.fetch()
    return [
        {"text": s.text, "start": s.start, "duration": s.duration}
        for s in fetched
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", help="YouTube URL or 11-character video id")
    parser.add_argument(
        "--languages",
        nargs="+",
        default=["en"],
        help="Preferred caption languages, in order (default: en)",
    )
    parser.add_argument(
        "--output",
        help="Output filename stem (default: the video id)",
    )
    args = parser.parse_args()

    try:
        video_id = extract_video_id(args.video)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Fetching transcript for video: {video_id}")
    try:
        segments = fetch_segments(video_id, args.languages)
    except TranscriptsDisabled:
        print("Error: transcripts are disabled for this video.", file=sys.stderr)
        return 1
    except VideoUnavailable:
        print("Error: the video is unavailable.", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - surface anything else clearly
        print(f"Error fetching transcript: {exc}", file=sys.stderr)
        return 1

    stem = args.output or video_id
    base = Path(__file__).resolve().parent / stem

    plain_text = "\n".join(seg["text"] for seg in segments)
    base.with_suffix(".txt").write_text(plain_text, encoding="utf-8")
    base.with_suffix(".srt").write_text(to_srt(segments), encoding="utf-8")
    base.with_suffix(".json").write_text(
        json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    word_count = sum(len(seg["text"].split()) for seg in segments)
    print(
        f"Done: {len(segments)} segments, ~{word_count} words.\n"
        f"  {base.with_suffix('.txt')}\n"
        f"  {base.with_suffix('.srt')}\n"
        f"  {base.with_suffix('.json')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
