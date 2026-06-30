# YouTube Transcript Extractor

Extract the full transcript from any YouTube video using
[`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api).
No API key required.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# By full URL
python extract_transcript.py "https://www.youtube.com/watch?v=fv8zpYI9n6s"

# By bare video id
python extract_transcript.py fv8zpYI9n6s

# Prefer specific languages (falls back to any available captions)
python extract_transcript.py fv8zpYI9n6s --languages en vi

# Custom output filename stem
python extract_transcript.py fv8zpYI9n6s --output my_transcript
```

## Output

For each run, three files are written next to the script (named after the
video id, or the `--output` stem):

| File                   | Description                                              |
|------------------------|---------------------------------------------------------|
| `<id>.paragraphs.txt`  | **Readable prose** — chunks rejoined into full sentences and grouped into paragraphs |
| `<id>.txt`             | Plain text, one line per caption segment                |
| `<id>.srt`             | SubRip subtitles with timestamps                        |
| `<id>.json`            | Raw segments (`text`, `start`, `duration`)              |

Tune paragraph length with `--sentences-per-paragraph N` (default: 4).

## Example

The repo includes a sample run for
[`fv8zpYI9n6s`](https://www.youtube.com/watch?v=fv8zpYI9n6s)
(526 segments, ~3,363 words).
