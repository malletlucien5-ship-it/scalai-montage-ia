#!/usr/bin/env python3
"""Construit placements.json depuis les ancres et les occurrences Remotion."""

import argparse
import bisect
import json
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def mapper(anchors, tolerance):
    segments = sorted(anchors["segments"], key=lambda item: item["ref_s"])
    kept = [item for item in segments if not item.get("absent")]
    keys = sorted(
        (
            item
            for item in anchors.get("mots_cles", [])
            if item.get("cut_t") is not None and item.get("ref_t") is not None
        ),
        key=lambda item: item["ref_t"],
    )
    key_times = [item["ref_t"] for item in keys]
    points = sorted(
        point
        for segment in kept
        for point in (
            (segment["ref_s"], segment["cut_s"]),
            (segment["ref_e"], segment["cut_e"]),
        )
    )

    if not points:
        raise ValueError("anchors.json ne contient aucun segment conservé")

    def is_absent(time_value):
        return any(
            segment["ref_s"] - 0.05 <= time_value <= segment["ref_e"] + 0.05
            and segment.get("absent")
            for segment in segments
        )

    def map_time(time_value):
        index = bisect.bisect_left(key_times, time_value)
        near = [
            keys[pos]
            for pos in (index - 1, index)
            if 0 <= pos < len(keys)
            and abs(keys[pos]["ref_t"] - time_value) < tolerance
        ]
        if near:
            key = min(near, key=lambda item: abs(item["ref_t"] - time_value))
            return key["cut_t"] + time_value - key["ref_t"]
        if is_absent(time_value):
            return None
        xs = [point[0] for point in points]
        pos = bisect.bisect_right(xs, time_value)
        if pos == 0:
            return points[0][1] + time_value - points[0][0]
        if pos >= len(points):
            return points[-1][1] + time_value - points[-1][0]
        (x0, y0), (x1, y1) = points[pos - 1], points[pos]
        if x1 == x0:
            return y0
        return y0 + (time_value - x0) * (y1 - y0) / (x1 - x0)

    return map_time


def build(args):
    occurrences = load(args.occurrences)
    map_time = mapper(load(args.anchors), args.key_tolerance)
    skipped_ids = set(args.skip_id)
    dropped_ids = set(args.drop_id)
    placements = []
    skipped = []

    for composition_id, meta in occurrences.items():
        if composition_id in skipped_ids or composition_id in dropped_ids:
            continue
        for index, occurrence in enumerate(meta.get("occurrences") or []):
            start = map_time(float(occurrence["ref"][0]))
            if start is None:
                skipped.append(f"{composition_id}#{index}")
                continue
            placements.append(
                {
                    "id": composition_id,
                    "occ": index,
                    "from": int(occurrence["from"]),
                    "dur": int(occurrence["durationInFrames"]),
                    "at": round(start, 3),
                    "mode": occurrence["mode"],
                    "ref": occurrence["ref"],
                }
            )

    placements.sort(key=lambda item: item["at"])
    full = [item for item in placements if item["mode"] == "plein"]
    for current, following in zip(full, full[1:]):
        end = current["at"] + current["dur"] / args.fps
        if end > following["at"]:
            current["dur"] = max(
                1, int((following["at"] - current["at"]) * args.fps)
            )
            current["raccourci"] = True

    Path(args.placements).write_text(
        json.dumps(placements, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    chapters = []
    if args.chapter_id:
        source = [
            item
            for item in placements
            if item["id"] == args.chapter_id and item["occ"] >= args.chapter_first_occ
        ]
        chapters = [
            {"niveau": index + 1, "start": item["at"]}
            for index, item in enumerate(sorted(source, key=lambda item: item["at"]))
        ]
    Path(args.chapters).write_text(
        json.dumps(chapters, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "placements": len(placements),
                "raccourcis": sum(item.get("raccourci", False) for item in placements),
                "non_poses": skipped,
                "chapitres": len(chapters),
            },
            ensure_ascii=False,
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--anchors", required=True)
    parser.add_argument("--occurrences", required=True)
    parser.add_argument("--placements", required=True)
    parser.add_argument("--chapters", required=True)
    parser.add_argument("--fps", type=float, default=30)
    parser.add_argument("--key-tolerance", type=float, default=2.0)
    parser.add_argument("--skip-id", action="append", default=[])
    parser.add_argument("--drop-id", action="append", default=[])
    parser.add_argument("--chapter-id")
    parser.add_argument("--chapter-first-occ", type=int, default=1)
    build(parser.parse_args())


if __name__ == "__main__":
    main()

