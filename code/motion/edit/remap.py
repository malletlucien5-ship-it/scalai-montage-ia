#!/usr/bin/env python3
"""Reporte les ancres et sous-titres sur une nouvelle coupe."""

import argparse
import bisect
import difflib
import json
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    Path(path).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def normal_word(item):
    return str(item.get("w", item.get("raw", ""))).strip().lower()


def create_converter(old_words, new_words):
    matcher = difflib.SequenceMatcher(
        a=[normal_word(item) for item in old_words],
        b=[normal_word(item) for item in new_words],
        autojunk=False,
    )
    pairs = []
    for block in matcher.get_matching_blocks():
        for offset in range(block.size):
            pairs.append(
                (
                    float(old_words[block.a + offset]["s"]),
                    float(new_words[block.b + offset]["s"]),
                )
            )
    pairs.sort()
    if len(pairs) < 2:
        raise ValueError("moins de deux mots appariés")
    xs = [pair[0] for pair in pairs]

    def convert(time_value):
        if time_value is None:
            return None
        time_value = float(time_value)
        index = bisect.bisect_left(xs, time_value)
        if index < len(xs) and abs(xs[index] - time_value) < 1e-6:
            return pairs[index][1]
        if index == 0:
            return pairs[0][1] + time_value - pairs[0][0]
        if index >= len(pairs):
            return pairs[-1][1] + time_value - pairs[-1][0]
        (x0, y0), (x1, y1) = pairs[index - 1], pairs[index]
        return y0 + (time_value - x0) * (y1 - y0) / (x1 - x0)

    return convert, pairs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-words", required=True)
    parser.add_argument("--new-words", required=True)
    parser.add_argument("--old-anchors", required=True)
    parser.add_argument("--anchors", required=True)
    parser.add_argument("--old-captions")
    parser.add_argument("--captions")
    parser.add_argument("--old-placements", help="placements.json d'une coupe précédente")
    parser.add_argument("--placements", help="sortie : mêmes placements avec `at` reporté")
    parser.add_argument("--tolerance", type=float, default=0.75,
                        help="au-delà de cet écart (s) au mot apparié le plus proche, un placement est marqué non_apparie")
    args = parser.parse_args()

    old_words = load(args.old_words)
    new_words = load(args.new_words)
    convert, pairs = create_converter(old_words, new_words)

    anchors = load(args.old_anchors)
    for segment in anchors["segments"]:
        for key in ("cut_s", "cut_e"):
            if segment.get(key) is not None:
                segment[key] = round(convert(segment[key]), 3)
    for key_item in anchors.get("mots_cles", []):
        if key_item.get("cut_t") is not None:
            key_item["cut_t"] = round(convert(key_item["cut_t"]), 3)
    write(args.anchors, anchors)

    if args.old_captions or args.captions:
        if not args.old_captions or not args.captions:
            raise ValueError("--old-captions et --captions vont ensemble")
        captions = load(args.old_captions)
        for occurrence in captions["occs"]:
            occurrence["start"] = round(convert(occurrence["start"]), 3)
            occurrence["end"] = round(convert(occurrence["end"]), 3)
            for line in occurrence.get("lines", []):
                for word in line.get("words", []):
                    word[0] = round(convert(word[0]), 3)
        write(args.captions, captions)

    non_apparies = 0
    if args.old_placements or args.placements:
        if not args.old_placements or not args.placements:
            raise ValueError("--old-placements et --placements vont ensemble")
        xs_old = [pair[0] for pair in pairs]
        placements = load(args.old_placements)
        for placement in placements:
            if placement.get("at") is None:
                continue
            ancien = float(placement["at"])
            placement["at_precedent"] = ancien
            placement["at"] = round(convert(ancien), 3)
            index = bisect.bisect_left(xs_old, ancien)
            voisins = [xs_old[i] for i in (index - 1, index) if 0 <= i < len(xs_old)]
            ecart = min(abs(v - ancien) for v in voisins) if voisins else float("inf")
            if ecart > args.tolerance:
                placement["non_apparie"] = True
                non_apparies += 1
            else:
                placement.pop("non_apparie", None)
        write(args.placements, placements)

    print(
        json.dumps(
            {
                "mots_apparies": len(pairs),
                "placements_non_apparies": non_apparies,
                "anciens": len(old_words),
                "nouveaux": len(new_words),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
