"""Move cut points onto the nearest quiet mic window so no word is chopped.
usage: snap_cuts.py mic.wav in.txt out.txt [--quiet-db -48] [--range 1.0]   (in/out: 'start end' per line)"""
import argparse, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from keep_list import rms_db, W


def snap(t, m, quiet, rng):
    i0, best = int(t / W), None
    for d in range(-int(rng / W), int(rng / W) + 1):
        i = i0 + d
        if 0 <= i < len(m) and m[i] < quiet and (best is None or abs(d) < abs(best - i0)):
            best = i
    return best * W if best is not None else t


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mic"); p.add_argument("inp"); p.add_argument("out")
    p.add_argument("--quiet-db", type=float, default=-48); p.add_argument("--range", type=float, default=1.0)
    a = p.parse_args()
    m = rms_db(a.mic)
    rows = [tuple(map(float, l.split())) for l in open(a.inp) if l.strip()]
    open(a.out, "w").write("\n".join(f"{snap(s, m, a.quiet_db, a.range)} {snap(e, m, a.quiet_db, a.range)}" for s, e in rows))
