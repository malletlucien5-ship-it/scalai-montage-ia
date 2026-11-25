#!/usr/bin/env python3
"""Assemble les rendus par segments. Aucune commande n'ouvre de fenêtre."""

import argparse
import bisect
import json
import math
import shlex
import subprocess
import time
from pathlib import Path


def run(command, cwd=None):
    result = subprocess.run(
        command, cwd=cwd, capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise RuntimeError(
            f"commande en échec: {shlex.join(map(str, command))}\n{result.stderr[-3000:]}"
        )
    return result.stdout


def duration(path):
    return float(
        run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                str(path),
            ]
        ).strip()
    )


def has_audio(path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def video_codec(path):
    return run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name",
            "-of",
            "csv=p=0",
            str(path),
        ]
    ).strip()


def keyframes(path, total):
    output = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-skip_frame",
            "nokey",
            "-select_streams",
            "v:0",
            "-show_entries",
            "frame=best_effort_timestamp_time",
            "-of",
            "csv=p=0",
            str(path),
        ]
    )
    values = [0.0]
    for line in output.splitlines():
        try:
            values.append(float(line.strip().split(",")[0]))
        except ValueError:
            continue
    values.append(total)
    return sorted(set(values))


def expand_to_keyframes(intervals, points, total):
    expanded = []
    for start, end in intervals:
        left_index = max(0, bisect.bisect_right(points, start) - 1)
        right_index = min(len(points) - 1, bisect.bisect_left(points, end))
        expanded.append((points[left_index], min(total, points[right_index])))
    return merge(expanded, total)


def merge(intervals, limit):
    result = []
    for start, end in sorted(intervals):
        start = max(0.0, start)
        end = min(limit, end)
        if end <= start:
            continue
        if result and start <= result[-1][1] + 0.001:
            result[-1] = (result[-1][0], max(result[-1][1], end))
        else:
            result.append((start, end))
    return result


def segments(active, limit):
    result = []
    cursor = 0.0
    for start, end in active:
        if start > cursor:
            result.append((cursor, start, False))
        result.append((start, end, True))
        cursor = end
    if cursor < limit:
        result.append((cursor, limit, False))
    return result


def asset_path(config, placement):
    render_dir = Path(config["render_dir"])
    suffix = ".mov" if placement["mode"] == "overlay" else ".mp4"
    return render_dir / f"{placement['id']}{suffix}"


def render_active(config, placements, start, end, output, source_origin=0.0):
    source = Path(config["source"])
    fps = float(config.get("output_fps", config.get("source_fps", 30)))
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{source_origin + start:.6f}",
        "-to",
        f"{source_origin + end:.6f}",
        "-i",
        str(source),
    ]
    selected = []
    for placement in placements:
        item_start = float(placement["at"])
        item_end = item_start + float(placement["dur"]) / float(config["fps"])
        if item_end <= start or item_start >= end:
            continue
        media = asset_path(config, placement)
        if not media.exists():
            raise FileNotFoundError(media)
        source_offset = float(placement.get("_asset_offset", 0.0)) + max(
            0.0, start - item_start
        )
        command += ["-ss", f"{source_offset:.6f}", "-i", str(media)]
        selected.append((placement, item_start, item_end))

    filters = ["[0:v]setpts=PTS-STARTPTS[base0]"]
    current = "base0"
    for index, (placement, item_start, item_end) in enumerate(selected, start=1):
        offset = max(0.0, item_start - start)
        visible_end = min(end, item_end) - start
        overlay_label = f"ov{index}"
        output_label = f"base{index}"
        filters.append(
            f"[{index}:v]setpts=PTS-STARTPTS+{offset:.6f}/TB[{overlay_label}]"
        )
        filters.append(
            f"[{current}][{overlay_label}]overlay=0:0:eof_action=pass:"
            f"enable='between(t,{offset:.6f},{visible_end:.6f})'[{output_label}]"
        )
        current = output_label

    encoder = config.get("video_encoder", "libx264")
    encoder_args = [str(item) for item in config.get("video_encoder_args", ["-crf", "16"])]
    command += [
        "-filter_complex",
        ";".join(filters),
        "-map",
        f"[{current}]",
        "-an",
        "-r",
        str(fps),
        "-c:v",
        encoder,
        *encoder_args,
        "-pix_fmt",
        config.get("pixel_format", "yuv420p"),
        str(output),
    ]
    run(command)


def render_plain(config, start, end, output, copy_video):
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{start:.6f}",
        "-to",
        f"{end:.6f}",
        "-i",
        config["source"],
        "-map",
        "0:v:0",
        "-an",
    ]
    if copy_video:
        command += ["-c:v", "copy"]
    else:
        command += [
            "-c:v",
            config.get("video_encoder", "libx264"),
            *[str(item) for item in config.get("video_encoder_args", ["-crf", "16"])],
            "-pix_fmt",
            config.get("pixel_format", "yuv420p"),
        ]
    command.append(str(output))
    run(command)


def assemble(config, limit=None, start_at=0.0, output_override=None):
    source_total = duration(config["source"])
    total = min(source_total, start_at + limit) if limit else source_total
    placements = json.loads(Path(config["placements"]).read_text(encoding="utf-8"))
    range_start = {}
    for item in placements:
        composition_id = item["id"]
        frame = int(item["from"])
        range_start[composition_id] = min(
            frame, range_start.get(composition_id, frame)
        )
    shifted = []
    active = []
    for item in placements:
        item = dict(item)
        original_start = float(item["at"])
        original_end = original_start + float(item["dur"]) / float(config["fps"])
        if original_end <= start_at or original_start >= total:
            continue
        item["at"] = original_start - start_at
        item["_asset_offset"] = (
            int(item["from"]) - range_start[item["id"]]
        ) / float(config["fps"])
        shifted.append(item)
        active.append((max(0.0, original_start - start_at), original_end - start_at))

    local_total = total - start_at
    active = merge(active, local_total)
    encoder = config.get("video_encoder", "libx264")
    compatible_codecs = {
        "libx264": "h264",
        "h264_videotoolbox": "h264",
        "libx265": "hevc",
        "hevc_videotoolbox": "hevc",
    }
    copy_inactive = bool(config.get("copy_inactive", True)) and (
        compatible_codecs.get(encoder) == video_codec(config["source"])
    )
    if copy_inactive and active:
        source_points = [
            max(0.0, point - start_at)
            for point in keyframes(config["source"], source_total)
            if start_at <= point <= total
        ]
        source_points += [0.0, local_total]
        active = expand_to_keyframes(active, sorted(set(source_points)), local_total)
    plan = segments(active, local_total)
    work = Path(config.get("work_dir", Path(config["output"]).parent / ".motion-work"))
    work.mkdir(parents=True, exist_ok=True)
    pieces = []
    began = time.monotonic()
    for index, (start, end, is_active) in enumerate(plan):
        piece = work / f"segment-{index:04d}.mp4"
        if is_active:
            render_active(config, shifted, start, end, piece, start_at)
        else:
            render_plain(
                config,
                start_at + start,
                start_at + end,
                piece,
                copy_inactive,
            )
        pieces.append(piece)

    concat_file = work / "concat.txt"
    concat_file.write_text(
        "".join(f"file '{path.as_posix()}'\n" for path in pieces), encoding="utf-8"
    )
    joined = work / "video.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c:v",
            "copy",
            "-an",
            str(joined),
        ]
    )
    output = Path(output_override or config["output"])
    mix_command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(joined),
    ]
    audio_filters = []
    audio_labels = []
    input_index = 1
    if has_audio(config["source"]):
        mix_command += [
            "-ss",
            f"{start_at:.6f}",
            "-t",
            f"{local_total:.6f}",
            "-i",
            config["source"],
        ]
        audio_filters.append(
            f"[{input_index}:a]asetpts=PTS-STARTPTS,"
            f"volume={float(config.get('voice_gain', 1.0))}[voice]"
        )
        audio_labels.append("[voice]")
        input_index += 1

    audio_items = []
    for item in shifted:
        media = asset_path(config, item)
        if not has_audio(media):
            continue
        item_start = float(item["at"])
        item_end = item_start + float(item["dur"]) / float(config["fps"])
        visible_start = max(0.0, item_start)
        visible_end = min(local_total, item_end)
        if visible_end <= visible_start:
            continue
        source_offset = float(item.get("_asset_offset", 0.0)) + max(
            0.0, visible_start - item_start
        )
        audio_items.append(
            {
                "path": media,
                "source_offset": source_offset,
                "duration": visible_end - visible_start,
                "delay_ms": max(0, round(visible_start * 1000)),
                "gain": float(config.get("sfx_gain", 1.0)),
            }
        )
    for track in config.get("audio_tracks", []):
        track_start = float(track.get("at", 0.0)) - start_at
        track_duration = float(track.get("duration", local_total))
        visible_start = max(0.0, track_start)
        visible_end = min(local_total, track_start + track_duration)
        track_path = Path(track["path"])
        if not track_path.is_absolute():
            track_path = Path(config["project_root"]) / track_path
        if visible_end <= visible_start or not has_audio(track_path):
            continue
        audio_items.append(
            {
                "path": track_path,
                "source_offset": float(track.get("offset", 0.0))
                + max(0.0, visible_start - track_start),
                "duration": visible_end - visible_start,
                "delay_ms": max(0, round(visible_start * 1000)),
                "gain": float(track.get("gain", 1.0)),
            }
        )

    for number, item in enumerate(audio_items):
        mix_command += [
            "-ss",
            f"{item['source_offset']:.6f}",
            "-t",
            f"{item['duration']:.6f}",
            "-i",
            str(item["path"]),
        ]
        label = f"a{number}"
        audio_filters.append(
            f"[{input_index}:a]asetpts=PTS-STARTPTS,"
            f"adelay={item['delay_ms']}:all=1,volume={item['gain']}[{label}]"
        )
        audio_labels.append(f"[{label}]")
        input_index += 1

    mix_command += ["-map", "0:v:0", "-c:v", "copy"]
    if audio_labels:
        audio_filters.append(
            "".join(audio_labels)
            + f"amix=inputs={len(audio_labels)}:duration=first:dropout_transition=0[aout]"
        )
        mix_command += [
            "-filter_complex",
            ";".join(audio_filters),
            "-map",
            "[aout]",
            "-c:a",
            config.get("audio_encoder", "aac"),
        ]
    else:
        mix_command += ["-an"]
    mix_command += ["-shortest", str(output)]
    run(mix_command)
    return {
        "output": str(output),
        "duration": local_total,
        "segments": len(plan),
        "seconds": round(time.monotonic() - began, 3),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--benchmark", type=float)
    parser.add_argument("--start", type=float, default=0.0)
    parser.add_argument("--output")
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    for key in ("source", "output", "placements", "render_dir", "work_dir"):
        if key in config and not Path(config[key]).is_absolute():
            config[key] = str((config_path.parent / config[key]).resolve())
    result = assemble(config, args.benchmark, args.start, args.output)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
