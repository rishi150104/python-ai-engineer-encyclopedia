"""Match source items to inventory concepts by token coverage. Usage: match.py [source ids...]  -> results/<id>.json + prints stats."""
import json
import re
import sys
from pathlib import Path

import yaml

S = Path(__file__).parent
ROOT = Path("<REPO_ROOT>")  # redacted machine path: set to the repository root
(S / "results").mkdir(exist_ok=True)
STOP = set("""a an the of in on for to and or with without vs via is are be as at by from into using use used how what why when which that this these those it its your you our we
overview introduction intro basics basic guide tutorial new changes change python more about getting started part chapter section reference docs documentation page index home
next previous skip content support tools tool concepts concept""".split())
NOISE = re.compile(r"^(next|previous|home|about|download|documentation|community|developers|legal notice|preface|skip to content|ask ai|sign in|log in|blog|github|heroku|"
                   r"contact|search|license|copyright|share feedback|get started|guides|manuals|reference|release notes|what.?s new|bug|glossary|index|credits|terms)\b", re.I)


def stem(w):
    for suf in ("ing", "ies", "es", "s", "ed"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)] + ("y" if suf == "ies" else "")
    return w


def toks(s):
    s = re.sub(r"([a-z])([A-Z])", lambda m: m.group(1) + " " + m.group(2), s)
    s = re.sub(r"^\s*(\d+(\.\d+)*\.?|[A-Z]\.|Part [IVX]+ -)\s+", "", s)
    return {stem(w) for w in re.findall(r"[a-z0-9_]+", s.lower()) if w not in STOP and len(w) > 1}


inv = yaml.safe_load((ROOT / "master-index.yaml").read_text(encoding="utf-8"))["nodes"]
concepts = [n for n in inv if n["level"] == "concept"]
ctoks = [(n, toks(n["title"]), toks(n["title"] + " " + n["scope"])) for n in concepts]


import math
from collections import Counter
df = Counter(w for _, _, ts in ctoks for w in ts)
idf = lambda w: math.log((len(ctoks) + 1) / (df.get(w, 0) + 1)) + 0.1


def best(item):
    """IDF-weighted share of the item's tokens found in one concept's title+scope (rare shared words count most)."""
    t = toks(item)
    if not t:
        return None, 0.0
    top = (None, 0.0)
    total = sum(idf(w) for w in t)
    for n, tt, ts in ctoks:
        shared = t & ts
        if not shared:
            continue
        score = sum(idf(w) for w in shared) / total
        if len(t) >= 2 and len(shared) < 2:
            score *= 0.7                         # one shared word out of several is weak evidence
        if score > top[1]:
            top = (n["id"], score)
    return top


def run(sid, thr=0.55):
    d = json.loads((S / "audit" / f"{sid}.json").read_text(encoding="utf-8"))
    matched, unmatched, noise = [], [], []
    for it in d["items"]:
        if NOISE.match(it) or len(toks(it)) == 0:
            noise.append(it)
            continue
        cid, sc = best(it)
        (matched if sc >= thr else unmatched).append({"item": it, "concept": cid, "score": round(sc, 2)})
    (S / "results" / f"{sid}.json").write_text(json.dumps({"id": sid, "matched": matched, "unmatched": unmatched, "noise": noise}, ensure_ascii=False, indent=0), encoding="utf-8")
    return d, matched, unmatched, noise


if __name__ == "__main__":
    ids = sys.argv[1:] or [p.stem for p in sorted((S / "audit").glob("*.json"))]
    for sid in ids:
        if sid.startswith("R-JOBS"):
            continue
        d, m, u, n = run(sid)
        print(f"{sid}: {len(d['items'])} items | matched {len(m)} | unmatched {len(u)} | noise {len(n)}")
