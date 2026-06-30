"""Command-line interface for yt-transcript.

Cross-platform: pure Python, pathlib paths, explicit UTF-8 everywhere, so it
runs identically on macOS, Windows, and Linux.

Usage:
    yt-transcript "https://www.youtube.com/watch?v=fv8zpYI9n6s"
    yt-transcript fv8zpYI9n6s --languages en vi
    yt-transcript <url> --output my_transcript --output-dir ./out
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from . import __version__


def extract_video_id(url_or_id: str) -> str:
    """Accept a full YouTube URL or a bare 11-character video id."""
    if re.fullmatch(r"[0-9A-Za-z_-]{11}", url_or_id):
        return url_or_id

    match = re.search(
        r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/|/live/)([0-9A-Za-z_-]{11})",
        url_or_id,
    )
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


def to_srt(segments: List[dict]) -> str:
    """Render segments as SubRip (.srt) subtitles."""
    blocks = []
    for index, seg in enumerate(segments, start=1):
        start = format_timestamp(seg["start"])
        end = format_timestamp(seg["start"] + seg["duration"])
        text = seg["text"].replace("\n", " ").strip()
        blocks.append(f"{index}\n{start} --> {end}\n{text}\n")
    return "\n".join(blocks)


def to_paragraphs(segments: List[dict], sentences_per_paragraph: int = 4) -> str:
    """Join caption chunks into full sentences grouped into paragraphs."""
    joined = " ".join(seg["text"].replace("\n", " ") for seg in segments)
    joined = re.sub(r"\s+", " ", joined).strip()

    sentences = re.split(r"(?<=[.!?])\s+", joined)
    sentences = [s.strip() for s in sentences if s.strip()]

    paragraphs = [
        " ".join(sentences[i : i + sentences_per_paragraph])
        for i in range(0, len(sentences), sentences_per_paragraph)
    ]
    return "\n\n".join(paragraphs)


def fetch_segments(video_id: str, languages: List[str]) -> List[dict]:
    """Fetch transcript segments, preferring the requested languages.

    Falls back to any available transcript (including auto-generated ones)
    so we always return *something* if captions exist at all.
    """
    api = YouTubeTranscriptApi()

    try:
        fetched = api.fetch(video_id, languages=languages)
        return [
            {"text": s.text, "start": s.start, "duration": s.duration}
            for s in fetched
        ]
    except NoTranscriptFound:
        pass  # Fall through to "grab whatever exists".

    transcript_list = api.list(video_id)
    transcript = next(iter(transcript_list))
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yt-transcript",
        description="Extract the full transcript from a YouTube video "
        "(plain text, readable paragraphs, SRT subtitles, and JSON).",
    )
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
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to write the files into (default: current directory)",
    )
    parser.add_argument(
        "--sentences-per-paragraph",
        type=int,
        default=4,
        help="Sentences per paragraph in the readable .paragraphs.txt (default: 4)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

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
    out_dir = Path(args.output_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / stem

    plain_text = "\n".join(seg["text"] for seg in segments)
    paragraphs = to_paragraphs(segments, args.sentences_per_paragraph)

    txt_path = base.with_suffix(".txt")
    srt_path = base.with_suffix(".srt")
    json_path = base.with_suffix(".json")
    paragraphs_path = base.with_name(base.name + ".paragraphs.txt")

    txt_path.write_text(plain_text, encoding="utf-8")
    srt_path.write_text(to_srt(segments), encoding="utf-8")
    json_path.write_text(
        json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    paragraphs_path.write_text(paragraphs, encoding="utf-8")

    word_count = sum(len(seg["text"].split()) for seg in segments)
    print(
        f"Done: {len(segments)} segments, ~{word_count} words.\n"
        f"  {paragraphs_path}\n"
        f"  {txt_path}\n"
        f"  {srt_path}\n"
        f"  {json_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
