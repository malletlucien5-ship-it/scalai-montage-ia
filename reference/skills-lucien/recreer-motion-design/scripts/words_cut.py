#!/usr/bin/env python3
"""Reporte des mots horodatés depuis un montage vers sa nouvelle coupe."""

import argparse
import bisect
import json
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def spans(document):
    fps = float(document["fps"])
    timeline = 0.0
    output = []
    for chunk in document["chunks"]:
        duration = float(chunk["frames"]) / fps
        audio = chunk["audio"]
        output.append(
            (
                timeline,
                timeline + duration,
                audio["path"],
                float(audio["start"]),
                float(audio["end"]),
            )
        )
        timeline += duration
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-map", required=True)
    parser.add_argument("--cut-map", required=True)
    parser.add_argument("--words", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--transcript", required=True)
    parser.add_argument("--edge-tolerance", type=float, default=0.02)
    args = parser.parse_args()

    source_spans = spans(load(args.source_map))
    cut_spans = spans(load(args.cut_map))
    starts = [item[0] for item in source_spans]

    def to_source(time_value):
        index = max(0, bisect.bisect_right(starts, time_value) - 1)
        t0, t1, path, s0, s1 = source_spans[index]
        ratio = (s1 - s0) / max(t1 - t0, 1e-9)
        return path, s0 + (time_value - t0) * ratio

    def to_cut(path, source_time):
        for t0, t1, candidate, s0, s1 in cut_spans:
            if (
                candidate == path
                and s0 - args.edge_tolerance
                <= source_time
                <= s1 + args.edge_tolerance
            ):
                ratio = (t1 - t0) / max(s1 - s0, 1e-9)
                return t0 + (source_time - s0) * ratio
        return None

    input_words = load(args.words)
    output = []
    for word in input_words:
        start_path, source_start = to_source(float(word["start"]))
        end_path, source_end = to_source(float(word["end"]))
        cut_start = to_cut(start_path, source_start)
        cut_end = to_cut(end_path, source_end)
        if cut_start is None:
            continue
        raw = word.get("raw", word.get("w", ""))
        output.append(
            {
                "w": raw,
                "s": round(cut_start, 3),
                "e": round(cut_end if cut_end is not None else cut_start + 0.2, 3),
            }
        )

    Path(args.output).write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = []
    current = []
    for word in output:
        current.append(word)
        if str(word["w"]).endswith((".", "?", "!")) or len(current) > 28:
            lines.append(
                f"[{current[0]['s']:7.2f}] "
                + " ".join(str(item["w"]) for item in current)
            )
            current = []
    if current:
        lines.append(
            f"[{current[0]['s']:7.2f}] "
            + " ".join(str(item["w"]) for item in current)
        )
    Path(args.transcript).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"entree": len(input_words), "gardes": len(output)}))


if __name__ == "__main__":
    main()

