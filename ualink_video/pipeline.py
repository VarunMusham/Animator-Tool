"""Build pipeline:  narration (TTS)  ->  timeline  ->  SVG frames  ->  video  ->  joined film.

Every path is relative to the repository root, so the commands work from any directory.
"""
import asyncio, importlib, json, os, subprocess, sys, time, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NARRATION = ROOT / "narration"        # one mp3 per narrated beat (committed, so builds work offline)
BUILD = ROOT / "build"                # timelines, audio tracks, frames, stills   (git-ignored)
OUT = ROOT / "out"                    # finished videos                           (git-ignored)

SR, FPS = 24000, 24
TITLE_LEN = 4.0
LEAD, GAP, TAIL = 0.8, 0.45, 1.0      # seconds: before the first beat / between beats / after the last beat of a scene

PARTS = {
    1: dict(beats="beats_part1", video="part1_scenes1-9.mp4", name="Part 1 - The Car Park (Scenes 1-9)"),
    2: dict(beats="beats_part2", video="part2_scenes10-17.mp4", name="Part 2 - Same Story, in Code (Scenes 10-17)"),
    3: dict(beats="beats_part3", video="part3_scenes18-19_appendices.mp4", name="Part 3 - The Evidence (Scenes 18-19 + appendices)"),
}
FULL_VIDEO = "parking_permit_bug_full.mp4"


def beats_module(n):
    return importlib.import_module(f"ualink_video.{PARTS[n]['beats']}")

def ffmpeg_exe():
    import imageio_ffmpeg
    return os.environ.get("FFMPEG") or imageio_ffmpeg.get_ffmpeg_exe()

def narrated_beats(parts=(1, 2, 3)):
    """[(scene_id, beat_index, text)] for every beat that has a voice-over."""
    out = []
    for n in parts:
        for sc in beats_module(n).SCENES:
            for i, b in enumerate(sc["beats"]):
                if isinstance(b, str): out.append((sc["id"], i, b))
    return out

def narration_path(scene_id, i): return NARRATION / f"{scene_id}_b{i}.mp3"

# narration/manifest.json records which text + voice each clip was generated from, so editing a line in beats_part*.py
# is noticed (the clip is regenerated) instead of silently keeping the old audio.
MANIFEST = NARRATION / "manifest.json"

def _voice_cfg():
    return importlib.import_module("ualink_video.beats_part1")

def clip_hash(text):
    import hashlib
    c = _voice_cfg()
    return hashlib.sha1(f"{c.VOICE}|{c.RATE}|{text}".encode("utf-8")).hexdigest()[:16]

def load_manifest():
    try: return json.load(open(MANIFEST, encoding="utf-8"))
    except (OSError, ValueError): return {}

def save_manifest(m):
    json.dump(dict(sorted(m.items())), open(MANIFEST, "w", encoding="utf-8"), indent=1)

def stale_clips(parts=(1, 2, 3)):
    """clips that exist but were generated from different text/voice than the current beats files."""
    m = load_manifest()
    return [f"{s}_b{i}" for s, i, t in narrated_beats(parts) if narration_path(s, i).exists() and m.get(f"{s}_b{i}") != clip_hash(t)]


# ------------------------------------------------------------------ 1. narration
def tts(force=False, parts=(1, 2, 3), concurrency=4):
    """Generate the missing narration clips with edge-tts (needs an internet connection)."""
    try:
        import edge_tts
    except ImportError:
        sys.exit("edge-tts is not installed:  pip install -r requirements.txt")
    cfg = _voice_cfg()
    NARRATION.mkdir(exist_ok=True)
    manifest = load_manifest()
    todo = [(s, i, t) for s, i, t in narrated_beats(parts)
            if force or not narration_path(s, i).exists() or manifest.get(f"{s}_b{i}") != clip_hash(t)]
    if not todo:
        print("narration: all clips are present and up to date (use --force to regenerate)"); return

    async def one(sem, s, i, text):
        async with sem:
            await edge_tts.Communicate(text, cfg.VOICE, rate=cfg.RATE).save(str(narration_path(s, i)))
            manifest[f"{s}_b{i}"] = clip_hash(text)
            print(f"  tts {s}_b{i}", flush=True)

    async def run():
        sem = asyncio.Semaphore(concurrency)
        await asyncio.gather(*(one(sem, s, i, t) for s, i, t in todo))

    print(f"narration: generating {len(todo)} clip(s) with voice {cfg.VOICE} ...")
    try:
        asyncio.run(run())
        save_manifest(manifest)
    except Exception as e:                     # network problems are the usual cause
        save_manifest(manifest)                # keep what did succeed
        sys.exit(f"narration failed ({e.__class__.__name__}: {e}).\n"
                 "edge-tts needs internet access. The repo ships the clips in narration/, so you normally do not need this step.")


def decode(path):
    """mp3 -> 24 kHz mono int16, with the TTS padding trimmed (0.12 s of air kept)."""
    import numpy as np
    raw = subprocess.run([ffmpeg_exe(), "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    pcm = np.frombuffer(raw, dtype=np.int16)
    idx = np.where(np.abs(pcm) > 500)[0]
    pad = int(0.12 * SR)
    return pcm[max(0, idx[0] - pad): idx[-1] + pad] if len(idx) else pcm


# ------------------------------------------------------------------ 2. timeline + audio track
def make_timeline(n):
    """Lay the beats out in time using the real narration lengths. Writes build/timeline<n>.json and build/audio<n>.wav."""
    import numpy as np
    mod = beats_module(n)
    missing = [f"{s}_b{i}" for s, i, _ in narrated_beats((n,)) if not narration_path(s, i).exists()]
    if missing:
        sys.exit(f"missing narration clips for part {n}: {', '.join(missing[:6])}{' ...' if len(missing) > 6 else ''}\n"
                 "run:  python -m ualink_video tts")
    title = getattr(mod, "TITLE", None)
    scenes = [dict(id="title", start=0.0, len=TITLE_LEN, **({"info": title} if title else {}))]
    cur = TITLE_LEN
    audio = np.zeros(int((TITLE_LEN + 600) * SR), dtype=np.int16)
    for sc in mod.SCENES:
        T, D, texts = [], [], []
        t = LEAD
        for i, b in enumerate(sc["beats"]):
            if isinstance(b, dict):                                   # silent, on-screen-only beat
                T.append(round(t, 3)); D.append(float(b["silent"])); texts.append(b.get("cap", ""))
                t += b["silent"] + GAP
                continue
            pcm = decode(narration_path(sc["id"], i))
            dur = len(pcm) / SR
            T.append(round(t, 3)); D.append(round(dur, 3)); texts.append(b)
            off = int((cur + t) * SR)
            audio[off:off + len(pcm)] = pcm
            t += dur + GAP
        length = round(t - GAP + TAIL, 3)
        scenes.append(dict(id=sc["id"], chip=sc["chip"], start=round(cur, 3), len=length, T=T, D=D, texts=texts))
        cur += length
    audio = audio[:int(cur * SR)]
    BUILD.mkdir(exist_ok=True)
    json.dump(dict(total=cur, fps=FPS, scenes=scenes), open(BUILD / f"timeline{n}.json", "w", encoding="utf-8"), indent=1)
    with wave.open(str(BUILD / f"audio{n}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(audio.tobytes())
    print(f"part {n}: timeline {cur:.1f}s  ({', '.join(s['id'] for s in scenes[1:])})")
    return BUILD / f"timeline{n}.json"


# ------------------------------------------------------------------ 3. frames + video
def _render_png(args):
    """Worker: render one frame. Runs in a child process, so it loads the timeline itself."""
    tl_path, t, path, width = args
    import cairosvg
    from ualink_video import render
    if render.TL_PATH != tl_path: render.load_timeline(tl_path)
    cairosvg.svg2png(bytestring=render.frame_svg(t).encode("utf-8"), write_to=str(path),
                     output_width=width, output_height=width * 9 // 16)
    return path

def make_stills(n, times, hd=False):
    tl = BUILD / f"timeline{n}.json"
    if not tl.exists(): make_timeline(n)
    d = BUILD / "stills"; d.mkdir(parents=True, exist_ok=True)
    for t in times:
        p = d / f"part{n}_{t:07.2f}.png"
        _render_png((str(tl), t, p, 1920 if hd else 1280)); print("still", p)

def make_video(n, hd=False, workers=None, keep_frames=False):
    import shutil
    from multiprocessing import Pool
    tl = make_timeline(n)
    total = json.load(open(tl, encoding="utf-8"))["total"]
    frames = int(total * FPS)
    width = 1920 if hd else 1280
    fdir = BUILD / "frames" / f"part{n}"
    shutil.rmtree(fdir, ignore_errors=True); fdir.mkdir(parents=True)
    jobs = [(str(tl), i / FPS, fdir / f"f_{i:05d}.png", width) for i in range(frames)]
    workers = workers or max(1, (os.cpu_count() or 4) - 2)
    t0 = time.time()
    print(f"part {n}: rendering {frames} frames at {width}x{width * 9 // 16} with {workers} worker(s) ...", flush=True)
    with Pool(workers) as pool:
        for k, _ in enumerate(pool.imap_unordered(_render_png, jobs, chunksize=16)):
            if k % 500 == 0: print(f"  frame {k}/{frames}  ({time.time() - t0:.0f}s)", flush=True)
    OUT.mkdir(exist_ok=True)
    out = OUT / PARTS[n]["video"]
    subprocess.run([ffmpeg_exe(), "-y", "-v", "error", "-framerate", str(FPS), "-i", str(fdir / "f_%05d.png"),
                    "-i", str(BUILD / f"audio{n}.wav"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                    "-preset", "medium", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    if not keep_frames: shutil.rmtree(fdir, ignore_errors=True)
    print(f"part {n}: wrote {out}  ({(time.time() - t0) / 60:.1f} min)")
    return out


# ------------------------------------------------------------------ 4. join the parts into one film
def _duration(path):
    err = subprocess.run([ffmpeg_exe(), "-i", str(path)], capture_output=True, text=True).stderr
    h = [l for l in err.splitlines() if "Duration" in l][0].split("Duration:")[1].split(",")[0].strip()
    hh, mm, ss = h.split(":")
    return int(hh) * 3600 + int(mm) * 60 + float(ss)

def concat(parts=(1, 2, 3)):
    """Join out/part*.mp4 into one video with chapter markers. Each part starts and ends on black and silence,
    so the join is a clean dip through black with no click or flash."""
    files = [OUT / PARTS[n]["video"] for n in parts]
    for f in files:
        if not f.exists(): sys.exit(f"missing {f.name}: build it first (python -m ualink_video video --part N)")
    durs = [_duration(f) for f in files]
    meta = ";FFMETADATA1\ntitle=The Parking Permit Bug - UPLI Credit Accounting\n"
    t = 0.0
    for n, d in zip(parts, durs):
        meta += f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={int(t * 1000)}\nEND={int((t + d) * 1000)}\ntitle={PARTS[n]['name']}\n"
        t += d
    BUILD.mkdir(exist_ok=True)
    mp = BUILD / "chapters.txt"; mp.write_text(meta, encoding="utf-8")
    k = len(files)
    cmd = [ffmpeg_exe(), "-y", "-v", "error"]
    for f in files: cmd += ["-i", str(f)]
    cmd += ["-i", str(mp), "-filter_complex", "".join(f"[{i}:v][{i}:a]" for i in range(k)) + f"concat=n={k}:v=1:a=1[v][a]",
            "-map", "[v]", "-map", "[a]", "-map_metadata", str(k), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
            "-preset", "medium", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(OUT / FULL_VIDEO)]
    subprocess.run(cmd, check=True)
    print(f"wrote {OUT / FULL_VIDEO}  ({t / 60:.1f} min, {k} chapters)")


# ------------------------------------------------------------------ environment check
def font_installed(family):
    """cairo silently substitutes a default font when a family is missing, so compare the render against a bogus family."""
    import cairosvg
    def png(fam):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="60"><text x="4" y="40" font-size="32" '
               f'font-family="{fam}" font-weight="700">Wide Gatekeeper 0123 {{}}|</text></svg>')
        return cairosvg.svg2png(bytestring=svg.encode())
    return png(family) != png("__no_such_font_family__")

def doctor():
    """Check that this machine can build the video. Returns True when everything essential is OK."""
    ok = True
    def line(good, what, hint=""):
        nonlocal ok
        print(("  [ok]   " if good else "  [FAIL] ") + what + ("" if good else f"\n           -> {hint}"))
        ok = ok and good
    print(f"python {sys.version.split()[0]} on {sys.platform}")
    line(sys.version_info >= (3, 9), "Python >= 3.9", "install a newer Python")
    for mod, pipname in (("numpy", "numpy"), ("edge_tts", "edge-tts"), ("imageio_ffmpeg", "imageio-ffmpeg"), ("cairosvg", "cairosvg")):
        try:
            importlib.import_module(mod); line(True, f"python package {pipname}")
        except Exception as e:
            hint = "pip install -r requirements.txt"
            if mod == "cairosvg": hint = "the native Cairo library is missing - see 'Install Cairo' in the README  (" + str(e).splitlines()[0] + ")"
            line(False, f"python package {pipname}", hint)
            if mod == "cairosvg": return False
    try:
        line(subprocess.run([ffmpeg_exe(), "-version"], capture_output=True).returncode == 0, "ffmpeg (bundled by imageio-ffmpeg)", "set FFMPEG=/path/to/ffmpeg")
    except Exception as e:
        line(False, "ffmpeg", str(e))
    from ualink_video import render
    for label, fam in (("sans font", render.SANS), ("mono font", render.MONO)):
        have = font_installed(fam)
        line(have, f"{label}: '{fam}'", f"install it, or set UALINK_FONT_{'SANS' if 'sans' in label else 'MONO'} (and UALINK_MONO_ADVANCE for mono) - see README 'Fonts'")
    need = narrated_beats()
    miss = [f"{s}_b{i}" for s, i, _ in need if not narration_path(s, i).exists()]
    line(not miss, f"narration clips: {len(need) - len(miss)}/{len(need)} present", "run: python -m ualink_video tts   (needs internet)")
    stale = stale_clips()
    line(not stale, "narration clips match the current text", f"{len(stale)} clip(s) are out of date ({', '.join(stale[:4])}{' ...' if len(stale) > 4 else ''}): run  python -m ualink_video tts")
    used = {narration_path(s, i).name for s, i, _ in need}
    orphans = sorted(p.name for p in NARRATION.glob("*.mp3") if p.name not in used)
    if orphans: print(f"  [note] {len(orphans)} unused clip(s) in narration/ (safe to delete): {', '.join(orphans[:5])}{' ...' if len(orphans) > 5 else ''}")
    print("\nall good - run:  python -m ualink_video all" if ok else "\nfix the [FAIL] items above, then run doctor again")
    return ok
