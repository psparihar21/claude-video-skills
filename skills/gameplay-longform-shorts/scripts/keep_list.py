"""Keep list for commentary-led gameplay: keep speech or loud game audio, drop dead air.
usage: keep_list.py mic.wav game.wav out.txt [--cut A-B ...] [--mic-db -32] [--game-db -23] [--pad 2] [--gap 2.5] [--min 2] [--head 5]
Writes one 'start end' (seconds) per line. --cut forces a stretch out (menus, loading, idle gaps)."""
import argparse, subprocess, numpy as np

W = 0.5  # window seconds


def rms_db(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "8000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype=np.float32)
    n = len(a) // 4000
    return 20 * np.log10(np.sqrt((a[:n * 4000].reshape(n, 4000) ** 2).mean(1)) + 1e-9)


def keep(mic, game, mic_db=-32, game_db=-23, pad=2, gap=2.5, min_len=2, head=5, cuts=()):
    n = min(len(mic), len(game))
    act = (mic[:n] > mic_db) | (game[:n] > game_db)
    for a, b in cuts:
        act[int(a / W):int(b / W)] = False
    act[:int(head / W)] = False
    d = np.convolve(act, np.ones(2 * pad + 1), "same") > 0  # dilate so words and impacts are not clipped
    segs, s = [], None
    for i, v in enumerate(d):
        if v and s is None:
            s = i
        if not v and s is not None:
            segs.append([s * W, i * W]); s = None
    if s is not None:
        segs.append([s * W, n * W])
    out = []
    for a, b in segs:
        if out and a - out[-1][1] < gap:
            out[-1][1] = b
        else:
            out.append([a, b])
    return [x for x in out if x[1] - x[0] >= min_len]


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mic"); p.add_argument("game"); p.add_argument("out")
    p.add_argument("--cut", action="append", default=[])
    p.add_argument("--mic-db", type=float, default=-32); p.add_argument("--game-db", type=float, default=-23)
    p.add_argument("--pad", type=int, default=2); p.add_argument("--gap", type=float, default=2.5)
    p.add_argument("--min", type=float, default=2); p.add_argument("--head", type=float, default=5)
    a = p.parse_args()
    cuts = [tuple(float(x) for x in c.split("-")) for c in a.cut]
    segs = keep(rms_db(a.mic), rms_db(a.game), a.mic_db, a.game_db, a.pad, a.gap, a.min, a.head, cuts)
    open(a.out, "w").write("\n".join(f"{x[0]} {x[1]}" for x in segs))
    print(len(segs), "segments,", round(sum(x[1] - x[0] for x in segs)), "s")
