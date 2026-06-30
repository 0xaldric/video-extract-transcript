# yt-transcript

[![CI](https://github.com/0xaldric/video-extract-transcript/actions/workflows/ci.yml/badge.svg)](https://github.com/0xaldric/video-extract-transcript/actions/workflows/ci.yml)

A small, cross-platform command-line tool to extract the full transcript from
any YouTube video — as readable paragraphs, plain text, `.srt` subtitles, and
JSON. Pure Python, no API key required. Runs the same on **macOS**, **Windows**,
and **Linux**.

**Version:** 1.0.0

## Install

You need Python 3.8 or newer ([python.org/downloads](https://www.python.org/downloads/)).

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

### Windows (PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install .
```

After installation the `yt-transcript` command is available on your PATH (inside
the virtual environment). To install globally instead, you can use
[pipx](https://pipx.pypa.io/): `pipx install .`

## Usage

```bash
# By full URL (extra params like &t=1s are fine)
yt-transcript "https://www.youtube.com/watch?v=fv8zpYI9n6s"

# By bare video id
yt-transcript fv8zpYI9n6s

# Prefer specific languages (falls back to any available captions)
yt-transcript fv8zpYI9n6s --languages en vi

# Write somewhere else with a custom name
yt-transcript fv8zpYI9n6s --output my_transcript --output-dir ./transcripts

# Bigger paragraphs
yt-transcript fv8zpYI9n6s --sentences-per-paragraph 6

# Version
yt-transcript --version
```

Don't want to install? Run it as a module from the project folder:

```bash
python -m yt_transcript fv8zpYI9n6s
```

## Output

Each run writes four files into the output directory (current folder by default),
named after the video id or your `--output` stem:

| File                   | Description                                              |
|------------------------|---------------------------------------------------------|
| `<id>.paragraphs.txt`  | **Readable prose** — chunks rejoined into full sentences and grouped into paragraphs |
| `<id>.txt`             | Plain text, one line per caption segment                |
| `<id>.srt`             | SubRip subtitles with timestamps                        |
| `<id>.json`            | Raw segments (`text`, `start`, `duration`)              |

## Options

| Option                         | Default        | Description                                  |
|--------------------------------|----------------|----------------------------------------------|
| `--languages L [L ...]`        | `en`           | Preferred caption languages, in order        |
| `--output STEM`                | the video id   | Output filename stem                         |
| `--output-dir DIR`             | `.`            | Directory to write files into                |
| `--sentences-per-paragraph N`  | `4`            | Sentences per paragraph in the readable file |
| `--version`                    |                | Print the version and exit                   |

## Example

The repo includes a sample run for
[`fv8zpYI9n6s`](https://www.youtube.com/watch?v=fv8zpYI9n6s)
(526 segments, ~3,363 words) — see
[`fv8zpYI9n6s.paragraphs.txt`](fv8zpYI9n6s.paragraphs.txt).

## License

[MIT](LICENSE)
