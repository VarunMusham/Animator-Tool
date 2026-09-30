"""Command line:   python -m ualink_video <command> [options]      (run from the repository root)"""
import argparse, sys

def main(argv=None):
    from . import pipeline as P
    ap = argparse.ArgumentParser(prog="python -m ualink_video", description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="""examples:
  python -m ualink_video doctor                 check this machine
  python -m ualink_video all                    build all three parts + the joined film  (~35-45 min at 720p)
  python -m ualink_video all --parts 3          just part 3 (and the join if the other parts already exist)
  python -m ualink_video video --part 2 --hd    part 2 in 1080p
  python -m ualink_video still --part 1 12.5 40 quick look at single frames  -> build/stills/
""")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor", help="check Python packages, Cairo, fonts, ffmpeg and narration clips")
    t = sub.add_parser("tts", help="(re)generate narration clips with edge-tts (needs internet)")
    t.add_argument("--force", action="store_true", help="regenerate even if the clip already exists")
    t.add_argument("--parts", type=int, nargs="+", default=[1, 2, 3])
    tl = sub.add_parser("timeline", help="lay the beats out in time -> build/timeline<N>.json + audio<N>.wav")
    tl.add_argument("--part", type=int, choices=(1, 2, 3), required=True)
    st = sub.add_parser("still", help="render individual frames for a quick visual check -> build/stills/")
    st.add_argument("--part", type=int, choices=(1, 2, 3), required=True)
    st.add_argument("--hd", action="store_true")
    st.add_argument("times", type=float, nargs="+", help="times in seconds (see build/timeline<N>.json)")
    v = sub.add_parser("video", help="render one part -> out/partN_*.mp4")
    v.add_argument("--part", type=int, choices=(1, 2, 3), required=True)
    v.add_argument("--hd", action="store_true", help="1920x1080 instead of 1280x720 (about twice as slow)")
    v.add_argument("--workers", type=int, help="render processes (default: CPU cores - 2)")
    v.add_argument("--keep-frames", action="store_true", help="keep the PNG frames in build/frames/")
    c = sub.add_parser("concat", help="join the part videos into out/parking_permit_bug_full.mp4 (with chapters)")
    c.add_argument("--parts", type=int, nargs="+", default=[1, 2, 3])
    a = sub.add_parser("all", help="narration (if missing) -> every part -> joined film")
    a.add_argument("--parts", type=int, nargs="+", default=[1, 2, 3])
    a.add_argument("--hd", action="store_true")
    a.add_argument("--workers", type=int)
    a.add_argument("--keep-frames", action="store_true")
    a.add_argument("--force-tts", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd == "doctor": return 0 if P.doctor() else 1
    if args.cmd == "tts": P.tts(args.force, tuple(args.parts))
    elif args.cmd == "timeline": P.make_timeline(args.part)
    elif args.cmd == "still": P.make_stills(args.part, args.times, args.hd)
    elif args.cmd == "video": P.make_video(args.part, args.hd, args.workers, args.keep_frames)
    elif args.cmd == "concat": P.concat(tuple(args.parts))
    elif args.cmd == "all":
        parts = tuple(args.parts)
        P.tts(args.force_tts, parts)
        for n in parts: P.make_video(n, args.hd, args.workers, args.keep_frames)
        if all((P.OUT / P.PARTS[n]["video"]).exists() for n in (1, 2, 3)): P.concat((1, 2, 3))
        else: print("not joining: the joined film needs all three parts (python -m ualink_video video --part N)")
    return 0

if __name__ == "__main__":          # the guard matters: render workers are spawned processes on Windows/macOS
    sys.exit(main())
