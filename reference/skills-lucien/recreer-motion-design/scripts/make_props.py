#!/usr/bin/env python3
"""Crée les props de sous-titres et de badges pour la vidéo cible."""

import argparse
import json
import subprocess
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def media_duration(path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def write(path, value):
    Path(path).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--captions", required=True)
    parser.add_argument("--placements", required=True)
    parser.add_argument("--chapters", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--fps", type=float, default=30)
    parser.add_argument("--chapter-card-id")
    parser.add_argument("--caption-name", default="captions.json")
    parser.add_argument("--badge-name", default="badges.json")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    total = media_duration(Path(args.source))
    frames = int(total * args.fps)
    captions = load(args.captions)
    write(
        output_dir / args.caption_name,
        {"durationInFrames": frames, "occs": captions.get("occs", [])},
    )

    placements = load(args.placements)
    chapters = load(args.chapters)
    cards = {}
    if args.chapter_card_id:
        cards = {
            item["at"]: item["at"] + item["dur"] / args.fps
            for item in placements
            if item["id"] == args.chapter_card_id
        }
    full = sorted(
        (item["at"], item["at"] + item["dur"] / args.fps)
        for item in placements
        if item["mode"] == "plein"
    )
    badge_ranges = []
    for index, chapter in enumerate(chapters):
        start = cards.get(chapter["start"], chapter["start"])
        end = chapters[index + 1]["start"] if index + 1 < len(chapters) else total
        cursor = start
        for block_start, block_end in full:
            if block_end <= cursor or block_start >= end:
                continue
            if block_start - cursor > 1.0:
                badge_ranges.append(
                    {
                        "niveau": chapter["niveau"],
                        "start": round(cursor, 3),
                        "end": round(block_start, 3),
                    }
                )
            cursor = max(cursor, block_end)
        if end - cursor > 1.0:
            badge_ranges.append(
                {
                    "niveau": chapter["niveau"],
                    "start": round(cursor, 3),
                    "end": round(end, 3),
                }
            )
    write(
        output_dir / args.badge_name,
        {"durationInFrames": frames, "chapitres": badge_ranges},
    )
    print(
        json.dumps(
            {
                "durationInFrames": frames,
                "captions": len(captions.get("occs", [])),
                "badges": len(badge_ranges),
            }
        )
    )


if __name__ == "__main__":
    main()

