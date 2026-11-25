#!/usr/bin/env python3
"""Indexe les compositions Remotion et les images publiques sans copier les assets."""

import argparse
import json
import re
from pathlib import Path


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif", ".svg"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".webm", ".mkv"}
AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}


def catalogue_rows(path):
    rows = {}
    if not path or not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or re.match(r"^\|[- :|]+$", line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 4 or cells[0].lower() == "id":
            continue
        rows[cells[0].zfill(2)] = {
            "name": cells[1],
            "reference_ranges": cells[2],
            "description": cells[3],
        }
    return rows


def scalar(source, key):
    match = re.search(
        rf"\b{re.escape(key)}\s*:\s*(?:['\"]([^'\"]+)['\"]|([0-9.]+))",
        source,
    )
    if not match:
        return None
    value = match.group(1) or match.group(2)
    if match.group(2):
        return float(value) if "." in value else int(value)
    return value


def referenced_files(source):
    found = set()
    patterns = [
        r"staticFile\(\s*['\"]([^'\"]+)['\"]\s*\)",
        r"(?:src|source|file)\s*:\s*['\"]([^'\"]+\.(?:png|jpe?g|webp|svg|mp4|mov|wav|mp3))['\"]",
    ]
    for pattern in patterns:
        found.update(re.findall(pattern, source, flags=re.IGNORECASE))
    return sorted(found)


def media_type(path):
    suffix = path.suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        return "image"
    if suffix in VIDEO_SUFFIXES:
        return "video"
    if suffix in AUDIO_SUFFIXES:
        return "audio"
    return None


def index_project(project, catalogue):
    project = project.resolve()
    comps = project / "remotion" / "src" / "comps"
    public = project / "remotion" / "public"
    if not comps.exists() and (project / "src" / "comps").exists():
        comps = project / "src" / "comps"
        public = project / "public"
    rows = catalogue_rows(catalogue)
    compositions = []
    if comps.exists():
        for entry in sorted(comps.glob("*/index.tsx")):
            source = entry.read_text(encoding="utf-8", errors="replace")
            composition_id = scalar(source, "id") or entry.parent.name
            prefix = str(composition_id).split("-", 1)[0].zfill(2)
            from_catalogue = rows.get(prefix, {})
            compositions.append(
                {
                    "id": composition_id,
                    "path": entry.relative_to(project).as_posix(),
                    "durationInFrames": scalar(source, "durationInFrames"),
                    "fps": scalar(source, "fps"),
                    "description": scalar(source, "description")
                    or from_catalogue.get("description"),
                    "catalogue_name": from_catalogue.get("name"),
                    "reference_ranges": from_catalogue.get("reference_ranges"),
                    "referenced_files": referenced_files(source),
                }
            )

    assets = []
    if public.exists():
        for file_path in sorted(public.rglob("*")):
            if not file_path.is_file():
                continue
            kind = media_type(file_path)
            if not kind:
                continue
            assets.append(
                {
                    "type": kind,
                    "path": file_path.relative_to(project).as_posix(),
                    "name": file_path.stem,
                    "bytes": file_path.stat().st_size,
                }
            )
    return {
        "project": project.name,
        "compositions": compositions,
        "assets": assets,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", action="append", required=True)
    parser.add_argument("--catalogue")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    projects = [Path(item).expanduser() for item in args.project]
    catalogue = Path(args.catalogue).expanduser() if args.catalogue else None
    indexed = []
    for index, project in enumerate(projects):
        project_catalogue = catalogue if index == 0 else project / "CATALOGUE.md"
        indexed.append(index_project(project, project_catalogue))
    document = {"version": 1, "projects": indexed}
    Path(args.output).write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "projects": len(indexed),
                "compositions": sum(len(item["compositions"]) for item in indexed),
                "assets": sum(len(item["assets"]) for item in indexed),
                "output": str(Path(args.output)),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

