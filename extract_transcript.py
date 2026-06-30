"""Backward-compatible entry point.

The tool now lives in the `yt_transcript` package. This shim keeps the old
`python extract_transcript.py <url>` command working.

Prefer installing the tool and using the `yt-transcript` command:
    pip install .
    yt-transcript "https://www.youtube.com/watch?v=fv8zpYI9n6s"
"""

from yt_transcript.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
