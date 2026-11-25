#!/usr/bin/env python3
"""Rend les compositions modifiées sur Lambda puis lance l'assemblage segmenté."""

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def run(command, cwd=None, env=None, attempts=1):
    last = None
    for attempt in range(attempts):
        last = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if last.returncode == 0:
            return last.stdout
        sys.stderr.write(f"essai {attempt + 1}/{attempts} en échec\n")
    raise RuntimeError(
        f"commande en échec: {shlex.join(map(str, command))}\n{last.stderr[-4000:]}"
    )


def resolve_config(path):
    path = Path(path).resolve()
    config = json.loads(path.read_text(encoding="utf-8"))
    path_keys = {
        "project_root",
        "remotion_dir",
        "source",
        "output",
        "placements",
        "render_dir",
        "work_dir",
    }
    for key in path_keys:
        if key in config and not Path(config[key]).is_absolute():
            config[key] = str((path.parent / config[key]).resolve())
    props = {}
    for composition_id, props_path in config.get("props_by_id", {}).items():
        props_path = Path(props_path)
        if not props_path.is_absolute():
            props_path = (path.parent / props_path).resolve()
        props[composition_id] = str(props_path)
    config["props_by_id"] = props
    required = [
        "project_root",
        "remotion_dir",
        "source",
        "output",
        "placements",
        "render_dir",
        "site_name",
        "region",
        "profile",
        "fps",
    ]
    missing = [key for key in required if key not in config]
    if missing:
        raise ValueError("configuration incomplète: " + ", ".join(missing))
    config["config_path"] = str(path)
    return config


def files_under(paths):
    files = []
    for path in paths:
        path = Path(path)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(item for item in path.rglob("*") if item.is_file())
    return sorted(set(files))


def digest(paths, base):
    value = hashlib.sha256()
    for path in files_under(paths):
        try:
            label = path.relative_to(base)
        except ValueError:
            label = path.name
        value.update(str(label).encode())
        value.update(path.read_bytes())
    return value.hexdigest()


def range_by_composition(placements):
    result = {}
    for item in placements:
        composition_id = item["id"]
        low = int(item["from"])
        high = low + int(item["dur"]) - 1
        mode = item["mode"]
        if composition_id not in result:
            result[composition_id] = [low, high, mode]
        else:
            result[composition_id][0] = min(result[composition_id][0], low)
            result[composition_id][1] = max(result[composition_id][1], high)
            if result[composition_id][2] != mode:
                raise ValueError(f"modes mélangés pour {composition_id}")
    return result


def public_prefix(composition_id):
    return composition_id.split("-", 1)[0]


def job_signature(config, composition_id, low, high, mode, command):
    remotion = Path(config["remotion_dir"])
    project = Path(config["project_root"])
    paths = [
        remotion / "src" / "comps" / composition_id,
        remotion / "src" / "shared",
        remotion / "src" / "Root.tsx",
        remotion / "src" / "index.ts",
        remotion / "public" / public_prefix(composition_id),
        remotion / "public" / "sfx",
        remotion / "remotion.config.ts",
        remotion / "package.json",
        remotion / "package-lock.json",
    ]
    props = config.get("props_by_id", {}).get(composition_id)
    if props:
        paths.append(Path(props))
    stable_command = [item for item in command if not item.startswith("--concurrency=")]
    payload = {
        "command": stable_command,
        "composition": composition_id,
        "frames": [low, high],
        "mode": mode,
        "sha256": digest(paths, project),
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"


def probe_video(path, mode, expected_seconds, fps):
    if not path.exists() or path.stat().st_size == 0:
        return False
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,pix_fmt:format=duration",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        return False
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    if not streams:
        return False
    actual = float(data.get("format", {}).get("duration", 0))
    if actual < expected_seconds - 0.5 / fps:
        return False
    stream = streams[0]
    if mode == "overlay":
        return stream.get("codec_name") == "prores" and str(
            stream.get("pix_fmt", "")
        ).startswith("yuva444p")
    return stream.get("codec_name") == "h264"


def lambda_environment(config):
    env = os.environ.copy()
    env["AWS_PROFILE"] = config["profile"]
    env["REMOTION_AWS_PROFILE"] = config["profile"]
    env["AWS_SDK_LOAD_CONFIG"] = "1"
    env["AWS_REGION"] = config["region"]
    env["AWS_DEFAULT_REGION"] = config["region"]
    env["REMOTION_AWS_REGION"] = config["region"]
    return env


def preflight(config):
    project_profile = config.get("project_profile", config["profile"])
    run(
        ["aws", "sts", "get-caller-identity", "--profile", project_profile],
        attempts=1,
    )
    region = run(
        ["aws", "configure", "get", "region", "--profile", project_profile]
    ).strip()
    if region and region != config["region"]:
        raise RuntimeError(
            f"région du profil {region}, configuration {config['region']}"
        )
    quota_output = run(
        ["npx", "--no-install", "remotion", "lambda", "quotas"],
        cwd=config["remotion_dir"],
        env=lambda_environment(config),
    )
    return {"region": config["region"], "quotas_checked": bool(quota_output.strip())}


def lambda_job(config, composition_id, low, high, mode, output):
    command = [
        "npx",
        "--no-install",
        "remotion",
        "lambda",
        "render",
        config["site_name"],
        composition_id,
        str(output),
        f"--frames={low}-{high}",
        f"--scale={config.get('scale', 1)}",
        f"--frames-per-lambda={config.get('frames_per_lambda', 250)}",
        "--log=info",
    ]
    if mode == "overlay":
        command += [
            "--codec=prores",
            "--prores-profile=4444",
            "--pixel-format=yuva444p10le",
            "--image-format=png",
            '--props={"showPlate":false}',
        ]
    else:
        command += ["--codec=h264", f"--crf={config.get('crf', 12)}"]
    props = config.get("props_by_id", {}).get(composition_id)
    if props:
        command.append(f"--props={props}")
    return command


def render_changed(config):
    preflight_result = preflight(config)
    render_dir = Path(config["render_dir"])
    render_dir.mkdir(parents=True, exist_ok=True)
    placements = json.loads(Path(config["placements"]).read_text(encoding="utf-8"))
    ranges = range_by_composition(placements)
    rendered = []
    cached = []
    costs = []
    env = lambda_environment(config)
    for composition_id, (low, high, mode) in sorted(ranges.items()):
        suffix = ".mov" if mode == "overlay" else ".mp4"
        output = render_dir / f"{composition_id}{suffix}"
        temporary = render_dir / f".{composition_id}.download{suffix}"
        cache_file = Path(str(output) + ".range")
        command = lambda_job(config, composition_id, low, high, mode, temporary)
        signature = job_signature(
            config, composition_id, low, high, mode, command
        )
        expected = (high - low + 1) / float(config["fps"])
        valid = probe_video(output, mode, expected, float(config["fps"]))
        if valid and cache_file.exists() and cache_file.read_text() == signature:
            cached.append(composition_id)
            continue
        temporary.unlink(missing_ok=True)
        try:
            output_text = run(
                command,
                cwd=config["remotion_dir"],
                env=env,
                attempts=int(config.get("render_attempts", 3)),
            )
            if not probe_video(temporary, mode, expected, float(config["fps"])):
                raise RuntimeError(f"sortie Lambda invalide: {composition_id}")
            temporary.replace(output)
            cache_file.write_text(signature, encoding="utf-8")
            rendered.append(composition_id)
            for line in output_text.splitlines():
                if "Estimated cost" in line or "Accrued costs" in line:
                    costs.append(line.strip())
        finally:
            temporary.unlink(missing_ok=True)
    return {
        "preflight": preflight_result,
        "rendered": rendered,
        "cached": cached,
        "cost_lines": costs,
    }


def assemble(config, benchmark=None, start=0.0):
    command = [
        sys.executable,
        str(SCRIPT_DIR / "assemble_fast.py"),
        "--config",
        config["config_path"],
        "--no-open",
    ]
    if benchmark:
        benchmark_output = str(
            Path(config["output"]).with_name(f"benchmark-{benchmark:g}s.mp4")
        )
        command += [
            "--benchmark",
            str(benchmark),
            "--start",
            str(start),
            "--output",
            benchmark_output,
        ]
    output = run(command)
    return json.loads(output.strip().splitlines()[-1])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--render-only", action="store_true")
    parser.add_argument("--skip-renders", action="store_true")
    parser.add_argument("--benchmark", type=float)
    parser.add_argument("--start", type=float, default=0.0)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    config = resolve_config(args.config)

    if args.preflight:
        print(json.dumps(preflight(config), ensure_ascii=False))
        return
    result = {}
    if not args.skip_renders:
        result["lambda"] = render_changed(config)
    if not args.render_only:
        result["assembly"] = assemble(config, args.benchmark, args.start)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

