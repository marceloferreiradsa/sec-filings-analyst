"""
score.py
────────
Scores the production retriever against the golden set (ADR-16).

A retrieved chunk is relevant to an expected source if it matches the source's
(company, filing_type, period_end, section) and contains its evidence phrase,
whitespace collapsed (ADR-15). Each expected source is credited once, at the rank
of the first chunk that matches it. out_of_corpus questions have no expected
source and are skipped here (refusal is scored in P0c).

Metrics, per category and overall, for each k
  recall@k  share of expected sources found in the top k
  all@k     1 if every expected source was found (matters for comparisons)
  MRR       1 / rank of the first relevant chunk, 0 if none in the top k
  nDCG@k    binary gain per newly credited source, ideal = all sources first

Configurations
  app    as the Streamlit app calls it: auto-detected filters, max_per_company=2
  plain  auto-detected filters, no per-company cap

Cost: one embedding call per question (text-embedding-3-small), cached in
data/eval_cache/ so later runs re-use identical vectors at no cost.

Usage (from the project root):
  python eval/golden/score.py run --config app          # writes eval/results/*.json
  python eval/golden/score.py run --oracle              # scorer self-check, no API
  python eval/golden/score.py compare A.json B.json     # paired bootstrap, 95% CI
  python eval/golden/score.py labels                    # chunks matching each label
"""

import argparse
import contextlib
import io
import json
import math
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.stdout.reconfigure(encoding="utf-8")

from eval.golden.validate import CHUNKS_PATH, GOLDEN_PATH, KEYS, norm  # noqa: E402

RESULTS_DIR = Path("eval/results")
CACHE_PATH  = Path("data/eval_cache/query_embeddings.json")
K_LIST      = (5, 10, 20)
CONFIGS     = {"app": 2, "plain": None}      # config → max_per_company
METRICS     = ("recall", "all", "mrr", "ndcg")


# ---------------------------------------------------------------------------
# Relevance
# ---------------------------------------------------------------------------

def matches(meta: dict, content: str, exp: dict) -> bool:
    return (all(meta.get(k) == exp[k] for k in KEYS)
            and norm(exp["evidence"]) in norm(content))


def credit(retrieved: list[tuple[dict, str]], expected: list[dict]) -> list[int]:
    """For each retrieved position, the index of the source it newly credits, or -1."""
    credited, hits = set(), []
    for meta, content in retrieved:
        hit = next((i for i, e in enumerate(expected)
                    if i not in credited and matches(meta, content, e)), -1)
        if hit >= 0:
            credited.add(hit)
        hits.append(hit)
    return hits


def metrics(hits: list[int], n_sources: int, k: int) -> dict:
    top   = hits[:k]
    found = sum(h >= 0 for h in top)
    first = next((r for r, h in enumerate(top, 1) if h >= 0), None)
    dcg   = sum(1 / math.log2(r + 1) for r, h in enumerate(top, 1) if h >= 0)
    idcg  = sum(1 / math.log2(r + 1) for r in range(1, min(n_sources, k) + 1))
    return {"recall": found / n_sources,
            "all":    float(found == n_sources),
            "mrr":    1 / first if first else 0.0,
            "ndcg":   dcg / idcg}


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def load_questions() -> list[dict]:
    items = [json.loads(l) for l in GOLDEN_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    return [it for it in items if not it["must_refuse"]]


def cached_retriever():
    """Production Retriever whose query embeddings are cached on disk."""
    from rag.retrieve import Retriever

    retriever = Retriever(verbose=False)
    cache = json.loads(CACHE_PATH.read_text(encoding="utf-8")) if CACHE_PATH.exists() else {}
    embed = retriever._embed_query
    calls = {"api": 0}

    def cached(question):
        import numpy as np
        key = f"{retriever.model}|{question}"
        if key not in cache:
            cache[key] = embed(question)[0].tolist()
            calls["api"] += 1
        return np.array(cache[key], dtype=np.float32).reshape(1, -1)

    retriever._embed_query = cached

    def save():
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(cache), encoding="utf-8")
    return retriever, save, calls


def oracle_lists(questions: list[dict]) -> dict[str, list[tuple[dict, str]]]:
    """The labelled chunks themselves: one matching chunk per expected source."""
    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    out = {}
    for q in questions:
        out[q["id"]] = [next((c["metadata"], c["page_content"]) for c in chunks
                             if matches(c["metadata"], c["page_content"], e))
                        for e in q["expected"]]
    return out


def git_state() -> dict:
    def git(*args):
        return subprocess.run(["git", *args], capture_output=True, text=True).stdout.strip()
    return {"commit": git("rev-parse", "--short", "HEAD"),
            "dirty":  bool(git("status", "--porcelain", "--untracked-files=no"))}


def run(args) -> None:
    questions = load_questions()
    rows = []
    if args.oracle:
        lists = oracle_lists(questions)
        for q in questions:
            hits = credit(lists[q["id"]], q["expected"])
            rows.append({"id": q["id"], "category": q["category"],
                         "n_sources": len(q["expected"]),
                         "by_k": {str(k): {"hits": hits, "chunks": []} for k in K_LIST}})
        label, calls = "oracle", {"api": 0}
    else:
        retriever, save, calls = cached_retriever()
        cap = CONFIGS[args.config]
        for q in questions:
            by_k = {}
            for k in K_LIST:
                with contextlib.redirect_stdout(io.StringIO()):
                    res = retriever.retrieve(q["question"], top_k=k, max_per_company=cap)
                by_k[str(k)] = {"hits": credit([(r.metadata, r.content) for r in res], q["expected"]),
                                "chunks": [r.chunk_id for r in res]}
            rows.append({"id": q["id"], "category": q["category"],
                         "n_sources": len(q["expected"]), "by_k": by_k})
        save()
        label = args.config

    for row in rows:
        row["metrics"] = {k: metrics(v["hits"], row["n_sources"], int(k))
                          for k, v in row["by_k"].items()}

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    out = {"run": {"date": stamp, "config": label, "k": list(K_LIST),
                   "embedding_api_calls": calls["api"], **git_state()},
           "questions": rows}
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"retrieval_{stamp}_{label}.json"
    path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"[SCORE] {len(rows)} questions · config={label} · "
          f"embedding calls={calls['api']} · {path}")
    print(summary_table(rows))


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def summary_table(rows: list[dict]) -> str:
    cats = sorted({r["category"] for r in rows}) + ["ALL"]
    head = "| category | n | " + " | ".join(f"{m}@{k}" for k in K_LIST for m in METRICS) + " |"
    lines = [head, "|" + "---|" * (2 + len(K_LIST) * len(METRICS))]
    for c in cats:
        sel = [r for r in rows if c == "ALL" or r["category"] == c]
        vals = [f"{mean([r['metrics'][str(k)][m] for r in sel]):.3f}"
                for k in K_LIST for m in METRICS]
        lines.append(f"| {c} | {len(sel)} | " + " | ".join(vals) + " |")
    return "\n".join(lines)


def compare(args) -> None:
    """Paired bootstrap of B − A over questions; 95% percentile interval."""
    a, b = (json.loads(Path(p).read_text(encoding="utf-8")) for p in (args.a, args.b))
    qa = {r["id"]: r for r in a["questions"]}
    qb = {r["id"]: r for r in b["questions"]}
    ids = sorted(qa.keys() & qb.keys())
    rng = random.Random(args.seed)
    print(f"[COMPARE] B − A  ·  A={a['run']['config']}@{a['run']['commit']}  "
          f"B={b['run']['config']}@{b['run']['commit']}  ·  {args.resamples} resamples")
    print(f"| category | n | metric | A | B | B−A | 95% CI | detectable |")
    print("|---|---|---|---|---|---|---|---|")
    for c in sorted({qa[i]["category"] for i in ids}) + ["ALL"]:
        sel = [i for i in ids if c == "ALL" or qa[i]["category"] == c]
        for m in METRICS:
            da = [qa[i]["metrics"][str(args.k)][m] for i in sel]
            db = [qb[i]["metrics"][str(args.k)][m] for i in sel]
            diffs = [y - x for x, y in zip(da, db)]
            boots = sorted(mean([diffs[rng.randrange(len(diffs))] for _ in diffs])
                           for _ in range(args.resamples))
            lo, hi = boots[int(0.025 * len(boots))], boots[int(0.975 * len(boots)) - 1]
            sig = "yes" if lo > 0 or hi < 0 else "no"
            print(f"| {c} | {len(sel)} | {m}@{args.k} | {mean(da):.3f} | {mean(db):.3f} | "
                  f"{mean(diffs):+.3f} | [{lo:+.3f}, {hi:+.3f}] | {sig} |")


def labels(args) -> None:
    """How many chunks each label matches (ADR-15's pending distinctiveness test)."""
    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    counts = []
    for q in load_questions():
        for e in q["expected"]:
            n = sum(matches(c["metadata"], c["page_content"], e) for c in chunks)
            counts.append((n, q["id"], e["company"], e["period_end"], e["section"]))
    dist = {}
    for n, *_ in counts:
        dist[n] = dist.get(n, 0) + 1
    print(f"[LABELS] {len(counts)} labels · chunks matched per label: "
          + ", ".join(f"{n}→{dist[n]}" for n in sorted(dist)))
    for row in sorted(counts, reverse=True):
        if row[0] > 1:
            print(f"  {row[0]} chunks  {row[1]}  {row[2]} {row[3]} §{row[4]}")


def main() -> None:
    p   = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--config", choices=sorted(CONFIGS), default="app")
    r.add_argument("--oracle", action="store_true")
    c = sub.add_parser("compare")
    c.add_argument("a"); c.add_argument("b")
    c.add_argument("--k", type=int, default=5, choices=K_LIST)
    c.add_argument("--resamples", type=int, default=10000)
    c.add_argument("--seed", type=int, default=16)
    sub.add_parser("labels")
    args = p.parse_args()
    {"run": run, "compare": compare, "labels": labels}[args.cmd](args)


if __name__ == "__main__":
    main()
