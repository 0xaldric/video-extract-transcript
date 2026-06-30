"""Unit tests for the pure (no-network) helpers in yt_transcript.cli."""

import pytest

from yt_transcript.cli import (
    extract_video_id,
    format_timestamp,
    to_paragraphs,
    to_srt,
)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("fv8zpYI9n6s", "fv8zpYI9n6s"),
        ("https://www.youtube.com/watch?v=fv8zpYI9n6s", "fv8zpYI9n6s"),
        ("https://www.youtube.com/watch?v=fv8zpYI9n6s&t=1s", "fv8zpYI9n6s"),
        ("https://youtu.be/fv8zpYI9n6s", "fv8zpYI9n6s"),
        ("https://www.youtube.com/embed/fv8zpYI9n6s", "fv8zpYI9n6s"),
        ("https://www.youtube.com/shorts/fv8zpYI9n6s", "fv8zpYI9n6s"),
        ("https://www.youtube.com/live/fv8zpYI9n6s", "fv8zpYI9n6s"),
    ],
)
def test_extract_video_id_accepts_many_forms(value, expected):
    assert extract_video_id(value) == expected


def test_extract_video_id_rejects_garbage():
    with pytest.raises(ValueError):
        extract_video_id("not a youtube url")


def test_format_timestamp():
    assert format_timestamp(0) == "00:00:00,000"
    assert format_timestamp(1.64) == "00:00:01,640"
    assert format_timestamp(3661.5) == "01:01:01,500"


def test_to_srt_structure():
    segments = [
        {"text": "Hello world", "start": 0.0, "duration": 2.0},
        {"text": "second line", "start": 2.0, "duration": 1.5},
    ]
    srt = to_srt(segments)
    assert "1\n00:00:00,000 --> 00:00:02,000\nHello world" in srt
    assert "2\n00:00:02,000 --> 00:00:03,500\nsecond line" in srt


def test_to_paragraphs_joins_chunks_into_sentences():
    # Caption chunks that split sentences mid-flow.
    segments = [
        {"text": "So recently we are seeing", "start": 0.0, "duration": 1.0},
        {"text": "a lot more layoffs.", "start": 1.0, "duration": 1.0},
        {"text": "Amazon laid off many", "start": 2.0, "duration": 1.0},
        {"text": "people. Meta did too.", "start": 3.0, "duration": 1.0},
    ]
    result = to_paragraphs(segments, sentences_per_paragraph=2)
    # First two sentences stitched and grouped into one paragraph.
    assert "So recently we are seeing a lot more layoffs." in result
    assert "Amazon laid off many people." in result
    # Two sentences per paragraph -> a blank line separates the groups.
    assert "\n\n" in result
