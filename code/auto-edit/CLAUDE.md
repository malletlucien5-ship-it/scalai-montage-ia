# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A French-language talking-head video auto-editor. Two Python scripts, no package manager, no tests, no build step. External binaries: `ffmpeg`/`ffprobe`. Python deps used at runtime: `torch` (Silero VAD via `torch.hub`), `requests`, `flask`. Optional polish stack: `deepfilternet` + `soundfile` (AI denoise — auto-skipped if missing).

The scripts target French content — filler words, dangling-word lists, and the Claude prompt are all French. Don't translate them when editing.

## Running

```bash
# CLI (full pipeline: VAD + ElevenLabs + Claude + export)
export ELEVENLABS_API_KEY=...
export OPENROUTER_API_KEY=...        # optional; without it, Claude content/restart pass is skipped
python3 auto_edit.py path/to/video.mp4

# Useful flags
python3 auto_edit.py video.mp4 --preview              # print cuts, no export
python3 auto_edit.py video.mp4 --preview-out cuts.json  # dump segments JSON, no export
python3 auto_edit.py video.mp4 --from-json cuts.json    # skip pipeline, export only
python3 auto_edit.py video.mp4 --no-cache             # bypass .transcache.json
python3 auto_edit.py video.mp4 --speed 1.06           # post-export speedup
python3 auto_edit.py video.mp4 --no-polish            # skip audio polish stage
python3 auto_edit.py video.mp4 --chapters             # generate chapters via Claude
python3 auto_edit.py video.mp4 --shownotes            # generate shownotes via Claude
python3 auto_edit.py video.mp4 --lufs -16             # podcast loudness target
python3 auto_edit.py video.mp4 --tail relaxed         # fins de phrase moins rognées (+0.30 s)
python3 auto_edit.py video.mp4 --tail relaxed --tail-pad 0.45   # dose la respiration

# Web UI (Flask, opens browser to localhost:7842)
python3 auto_edit_ui.py
```

Transcripts are cached next to the source as `<stem>.transcache.json`. Delete it or use `--no-cache` to force a re-transcription (each run hits the paid ElevenLabs API otherwise).

## Pipeline architecture

`auto_edit.py` is a single-file pipeline. Stages in `main()`:

1. **Audio extract** — `ffmpeg` → 16 kHz mono WAV in a tempdir.
2. **VAD** — Silero (`get_vad_segments`) returns speech intervals. Tuned threshold 0.40, min silence 220 ms. The audio is loaded by `load_audio_mono` (ffmpeg pipe → PCM s16le → torch tensor), NOT by silero's `read_audio`: torchaudio ≥ 2.9 delegates audio I/O to torchcodec, which is a separate package that lags behind current ffmpeg releases, so `read_audio` raises `torchaudio version X requires torchcodec for audio I/O` and the whole VAD stage dies. ffmpeg is already a hard dependency here, so decoding through it removes the torchaudio version coupling entirely. Keep it that way. `cut_silences.get_vad_tight` uses the same loader.
3. **Transcribe** — `transcribe_elevenlabs` posts MP3 to ElevenLabs Scribe (`scribe_v1`, `language_code=fr`, word timestamps). Critical: Scribe marks abandoned words with trailing `--`/`—`, which `find_abandoned_words` consumes directly. Whisper would lose this signal.
4. **Build cuts** — `build_segments` aggregates intervals to *remove* from many detectors, then subtracts them from VAD segments to produce kept segments.
5. **Export** — `export` re-encodes each kept segment individually with libx264 at the source bitrate/FPS (CFR forced), then concatenates via the concat demuxer in stream-copy mode. 40 ms audio fades at every cut. The per-segment encode is intentional: bounded memory for long videos and predictable A/V sync.
6. **Polish audio** (optional, on by default) — `polish_audio` runs *globally on the concatenated output* (not per-segment, because `loudnorm` and `dynaudnorm` need global context). Pipeline: extract 48 kHz mono → DeepFilterNet3 AI denoise → ffmpeg chain `highpass=80 → deesser → dynaudnorm → loudnorm` (EBU R128, default −14 LUFS) → mux back with `-c:v copy`. Replaces the original output in-place. DeepFilterNet failure is non-fatal (logs warning, skips denoise step).
7. **Chapters / shownotes** (optional, opt-in via `--chapters` / `--shownotes`) — reuses the OpenRouter/Claude scaffolding. `embed_chapters` writes ffmetadata2 chapter marks into the MP4 (no re-encode); `<stem>.chapters.txt` is also written for YouTube descriptions. Shownotes are written as `<stem>.shownotes.md`.

The cut detectors in `build_segments` (each appends `(start, end, type, label)` tuples to `bad`):

- `FILLERS` (always cut) vs `CONTEXTUAL_FILLERS` (cut only when surrounded by ≥150 ms silence).
- Stutters: same word repeated within 1.5 s, gated by `STUTTER_MIN_LEN`/`STUTTER_STOPWORDS` to avoid cutting common short words.
- `find_phrase_repeats` — n-gram (3) repetition where the second occurrence is within `PHRASE_MAX_BETWEEN=10` words. The narrow window is the discriminator between a restart and a natural structural repetition.
- `find_intra_segment_gaps` — long pauses *inside* a single VAD segment (VAD merged them).
- `find_coughs` / `find_leading_noise` — short VAD segments without words; or noise-then-speech inside one segment.
- `find_abandoned_words` — words ending in `--` from Scribe; cut from the start of the abandoned phrase to the next word.
- `find_all_restarts` — three heuristic strategies (bigram repeat, strong-word + pause, dangling-word abandon). Always on.
- `analyze_content` (gated by `--smart`, currently hardcoded `smart=True` in `main()`) — sends a marked-up transcript to Claude Sonnet via OpenRouter to flag `restart` and `content` cuts. **Claude's timestamps are interpolated from anchors and can drift 1–3 s**; `_anchor_claude_cuts` snaps `restart` cuts back to the nearest Whisper word. `content` cuts are not anchored — they need to fall on phrase boundaries, which Claude places better than word-level snapping would.
- `fix_coherence` — for `content` cuts only, if the word just before `cut_start` is a `DANGLING_WORDS` token (preposition/article/conjunction), back the start up to the previous ≥0.4 s pause so the orphaned fragment is included in the cut.

After collection: sort, merge overlapping bad intervals, subtract from VAD segments, then `_trim_trailing_silence` tightens kept segments around actual speech (≤150 ms lead, ≤250 ms trail).

## Fin de phrase : `--tail tight` (défaut) vs `--tail relaxed`

Three knobs act in cascade on the END boundary of a kept segment, and only the end — the lead is identical in both modes:

| knob | where | tight | relaxed |
|---|---|---|---|
| `trailing_padding` | `build_segments` (after the VAD end) | 0.02 | +pad |
| `trim_max_trail` | `_trim_trailing_silence` (silence kept after the last word) | 0.05 | +pad |
| `snap_pad_trail` | `snap_segments_to_silence` (margin after the real acoustic end) | 0.02 | +pad |

`tail_profile(mode, relax)` builds the dict; `pad` = `TAIL_RELAX_DEFAULT` (0.30 s) or `--tail-pad`. `tight` reproduces the historical numbers exactly — the default path is untouched.

The clipped half-words come from `snap_segments_to_silence`: ffmpeg `silencedetect` fires during the decay of the last syllable, so the end snaps to `silence_start + 0.02`, mid-word. Relaxing `snap_pad_trail` is what actually fixes it; the other two knobs stop `TRAILING_PADDING` and `_trim_trailing_silence` from capping the tail before the snap can use it.

Because the relaxed end can now extend past the segment boundary, `apply_tail_bounds` runs after the snap (relaxed only) and clamps each end to (a) the start of the next removed interval minus `CUT_PRE_PADDING` — otherwise the added breath re-injects the "euh" that was just cut — and (b) the start of the next kept segment, otherwise the same audio is exported twice and stutters at the join.

`cut_silences.py` exposes the same `--tail` / `--tail-pad`: relaxed shifts `--trail`, `--silence-pad-trail` and `--drop-db` (+6 dB, so the energy trim goes further down the decay before declaring the phrase over), and applies `apply_tail_bounds`. Explicit CLI values win — only defaults get relaxed.

`merge_contractions` runs immediately after transcription. ElevenLabs splits French contractions like `j'ai` → `["j", "'ai"]`; merging is gated by ADJACENCY (<80 ms gap) — without that gate, distant tokens fuse into a multi-second pseudo-word and the stutter detector wrecks the timeline.

## Tuning

The module-level constants at the top of `auto_edit.py` (around lines 19–66) are the tuning surface — `SILENCE_MIN_MS`, `INTRA_GAP_MIN`, `PHRASE_MAX_BETWEEN`, `RESTART_MIN_CUT`, `DANGLING_WORDS`, `FILLERS`, `STUTTER_STOPWORDS`, etc. Comments describe why each value was chosen; several are documented as fixes for specific failure cases. Read those before changing.

The Claude prompt in `analyze_content` is long, in French, and contains concrete few-shot examples drawn from real failure cases. Edits to it directly change cut behavior; treat it like code, not docs.

## Multicam (`multicam.py`)

Third pipeline: webcam (1..N camera parts, e.g. DJI file splits) + screen capture recorded in parallel → one edited MP4 with automatic per-segment framing. Imports from `auto_edit.py`/`cut_silences.py` like `cut_silences.py` does; the mono-cam pipelines are untouched.

```bash
python3 multicam.py CAM_PART1.MP4 [CAM_PART2.MP4 ...] --screen SCREEN.mp4 \
  --screen-crop X:Y:W:H --face-crop X:Y:W:H --split-ratio 0.55 --screen-fit fit

# Incremental validation (run these before a full render):
--sync-only        # multi-point GCC-PHAT audio sync: offsets, confidence, drift fit
--sync-check       # 10s hstack + amix clips at 3 points (audible echo = desync)
--calibrate [--at T]  # dump cam_frame.png + screen_frame.png to measure crops
--layout-only      # print the segment→layout table, no render
--preview-out cuts.json / --from-json cuts.json   # editable JSON round-trip
```

Key design points (learned the hard way — keep them):

- **The ffmpeg concat demuxer cannot seek** (`-ss` decodes from byte 0 → 90s+ per segment on 27 GB rushes). Camera parts are therefore NEVER physically concatenated nor seek-read through a concat list. Sequential reads (wav extraction) use the concat list; every positioned read goes through `SourceInput.locate()/segment_input()` which seeks directly in the right part file. `split_at_boundaries` guarantees no rendered segment straddles a part boundary (contiguous halves re-join exactly at concat).
- **Sync**: GCC-PHAT cross-correlation (numpy, spectral whitening — robust to the two different mics) at ~7 points including just after each camera-part boundary. Linear fit absorbs clock drift (measured ~11 µs/s on DJI vs Mac); residual > 15 ms falls back to piecewise anchors. `SyncMap` encapsulates wav-time↔video-time conversions (av_offsets of BOTH files) — never pass naked offsets around. Screen audio is never used in the output, so drift only affects screen video and is mapped per segment (<1 ms intra-segment error, no atempo needed).
- **Cuts**: silences + fillers only (euh/hm detectors from `build_segments`); no AI stutter/restart cuts — the user cuts those by hand on the composited output where both "tracks" are burned in. `--vad auto` (default) uses `auto_edit.get_vad_segments` (threshold 0.40, min silence 220 ms) — the main pipeline's silence-cut values, natural cadence. `--vad tight` is the aggressive `cut_silences` variant (25 ms) and choppy — avoid. `--min-gap` (default 0.25) is a light anti-chop net: a silence shorter than this is kept, so micro-pauses between words survive. `trim_segment_ends_batch` replaces `trim_segment_end` (which re-reads the whole WAV per segment — unusable at 44 min).
- **Layouts**: `face` | `split` per segment, decided by Claude via OpenRouter (chunked, loose JSON parsing + 1 retry) with `enforce_layout_constraints` ALWAYS applied after (LLM output is never trusted): intro/outro forced face, runs < `--min-shot` merged, split runs > `--max-split` broken by flipping a middle segment. Deterministic heuristic fallback without API key. `split_long_segments` splits >25 s keeps at word+pause boundaries so layout changes can only land on segment boundaries.
- **Render**: clone of `export()`'s per-segment parallel strategy with 2 inputs + hstack for `split`. The sample-locked audio chain, single shared encoder params (`-bf 0`, concat `-c:v copy`), `-frames:v` cap, and PCM→single-AAC-encode (via `polish_audio`) invariants are copied verbatim from `auto_edit.py`. `--screen-fit fit` letterboxes the screen crop onto `--pad-color` (default `0x181818` = Notion dark bg) instead of fill-cropping — used to "dezoom" the document.
- Persistent workdir (`<out>_work/`) caches wavs, sync anchors, and the multicam transcache keyed by source size/mtime.

Added 2026-09-12 (see `docs/superpowers/specs/2026-09-12-multicam-pip-script-design.md`):

- `--layout-mode pip` renders `split` segments as full-frame screen + a square face crop overlaid in a corner (`--pip-corner`, `--pip-size` fraction of height, `--pip-margin` px, `--pip-radius` rounded corners via a `geq` alpha mask on a `yuva444p` stream). JSON keeps the `split` name; the render mode changes.
- `--speed` works like auto_edit (effective speed per segment = input frames / output frames, `setpts` + `atempo`). **Every video chain ends with `tpad=stop_mode=clone` before `-frames:v`**: with `filter_complex` the `fps` filter does not pad, so a clip whose plan rounded up came out one frame short and the audio (exact `apad`) drifted ahead — 1.8 s over 221 clips. Keep the tpad.
- `--max-face` switches cadence to `solve_layouts_dp` (DP over segments: every run within [`--min-shot`, max(`--max-split`,`--max-face`)], soft bounds, locked face segments reset the counter). The greedy `enforce_layout_constraints` cascade cannot bound both layouts.
- `--face-ranges ranges.json` (screen-time `[start,end]` list) forces face on any segment whose screen window overlaps a range (script visible, OBS window…). `detect_script_ranges.py` produces it from 1 fps frames by fingerprint distance to reference frames.
- `--transcriber whisper` = local faster-whisper fallback when ElevenLabs is down (loses most "euh"; Scribe is literal).
- `--face-track` recenters the square per split run with OpenCV Haar (needs `opencv-python-headless<5`; 5.x dropped `CascadeClassifier`). Lucien prefers a fixed crop.

Orchestration end-to-end for Lucien's setup: `tools/pipeline.py` (prep / ranges / plan / render / verify / cuts) with the validated defaults, plus `tools/contact_sheets.py`, `tools/analyze_plan.py`, `tools/verify_output.py`, `tools/resolve_cuts.py` (reads the App Store Resolve SQLite project and transposes its cuts onto any render of the same plan). The operating procedure lives in the `montage-multicam` skill (`~/.claude/skills/montage-multicam/SKILL.md`).

## UI

`auto_edit_ui.py` is a single-file Flask app (HTML/CSS/JS embedded as a string) on port 7842. It uploads to `~/Desktop/AutoEdit/`, spawns the CLI with `--preview-out` / `--from-json`, polls a job dict, and streams stdout into a log panel. It supports two modes: `silence` (calls `cut_silences.py`) and `elevenlabs` (calls `auto_edit.py`).

UI options forwarded to the CLI: `polish` (default on), `chapters`, `shownotes` (opt-in), `tail_relaxed` → `--tail relaxed` (opt-in, works in both modes). `chapters` and `shownotes` are silently ignored in `silence` mode — that pipeline has no transcription. `tail_relaxed` changes the detected segments, so it is part of the preview cache key (`_preview_variant`) — toggling it does not reuse a stale preview.
