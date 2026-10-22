"""
bench.py
────────
Latency and memory benchmark for LOCAL cross-encoder rerankers on CPU.

Question this answers (see README.md for the full design):
  Can a cross-encoder rerank the retrieval candidates inside the production
  container, on the VPS CPU, fast enough and small enough to keep?

Runtime: fastembed (ONNX Runtime) — no torch. torch would bring the image back
to ~3 GB, which the production requirements file was written to avoid.

No OpenAI calls. Cost: $0.

Subcommands
  make-sample  run on the HOST: builds sample.json from data/index/chunks.json
  list-models  print the cross-encoders fastembed supports in this version
  prefetch     download the models into the cache volume (kept out of timings)
  run          benchmark every model × thread count, one subprocess each
  one          internal: benchmark a single model in an isolated process

Usage (from the project root):
  python experiments/rerank_latency/bench.py make-sample
  docker build -t rerank-bench experiments/rerank_latency
  docker run --rm --cpus=2 -v rerank-cache:/cache rerank-bench prefetch
  docker run --rm --cpus=2 -v rerank-cache:/cache \
      -v "$PWD/experiments/rerank_latency/results:/out" \
      rerank-bench run --label local-5900x
"""

import argparse
import json
import os
import platform
import random
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE        = Path(__file__).resolve().parent
SAMPLE_PATH = HERE / "sample.json"

# Models under test. Verified against `list-models` before the first run.
# Ordered from smallest to largest.
DEFAULT_MODELS = [
    "Xenova/ms-marco-MiniLM-L-6-v2",       # option A in the roadmap discussion
    "Xenova/ms-marco-MiniLM-L-12-v2",
    "jinaai/jina-reranker-v1-tiny-en",
    "jinaai/jina-reranker-v1-turbo-en",
    "BAAI/bge-reranker-base",              # option B — expected to be too slow
]

# Candidate counts handed to the reranker. 40 is the planned production value
# (fused BM25 + dense top 30–50 → rerank → top 5–8).
DEFAULT_CANDIDATES = [20, 40]
DEFAULT_THREADS    = [1, 2]
DEFAULT_REPS       = 15
WARMUP_RUNS        = 2

# Narrative questions, one company each. Latency depends on query and chunk
# length, not on relevance, so realistic text is what matters here.
QUERIES = [
    ("NVDA",  "What drove NVIDIA's gross margin changes in fiscal 2024?"),
    ("MSFT",  "What AI-related risks did Microsoft describe in its annual report?"),
    ("META",  "How is Meta describing its AI infrastructure investment plans?"),
    ("GOOGL", "How did Alphabet describe competition in cloud computing?"),
    ("AAPL",  "What factors affected Apple's Services revenue growth?"),
    ("NVDA",  "How did NVIDIA describe export controls affecting data center sales?"),
    ("MSFT",  "What drove growth in Microsoft's Intelligent Cloud segment?"),
    ("META",  "What regulatory risks did Meta identify for its advertising business?"),
]
SET_SIZE = 50   # docs per candidate set — the largest candidate count we test
SEED     = 42


# ─── make-sample (host) ───────────────────────────────────────────────────────

def make_sample(chunks_path: Path, out_path: Path) -> None:
    """
    Build candidate sets from real narrative chunks of the queried company, so
    the token-length distribution matches what the reranker will see.
    """
    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    by_company: dict[str, list[str]] = {}
    for c in chunks:
        meta = c["metadata"]
        if meta["source_type"] == "narrative":
            by_company.setdefault(meta["company"], []).append(c["page_content"])

    rng  = random.Random(SEED)
    sets = []
    for company, query in QUERIES:
        docs = rng.sample(by_company[company], SET_SIZE)
        sets.append({"company": company, "query": query, "docs": docs})

    total_chars = sum(len(d) for s in sets for d in s["docs"])
    n_docs      = len(sets) * SET_SIZE
    out_path.write_text(json.dumps({"seed": SEED, "sets": sets}), encoding="utf-8")
    print(f"[SAMPLE] {len(sets)} sets x {SET_SIZE} docs -> {out_path}")
    print(f"[SAMPLE] avg doc length: {total_chars // n_docs:,} chars "
          f"(~{total_chars // n_docs // 4} tokens)")


# ─── host info (container) ────────────────────────────────────────────────────

def cpu_model() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "unknown"


def cpu_quota() -> str:
    """Effective CPU limit set by `docker run --cpus` (cgroup v2), if any."""
    try:
        quota, period = Path("/sys/fs/cgroup/cpu.max").read_text().split()
        return "unlimited" if quota == "max" else f"{int(quota) / int(period):g}"
    except (OSError, ValueError):
        return "unknown"


def host_info(label: str) -> dict:
    return {
        "label"       : label,
        "cpu_model"   : cpu_model(),
        "visible_cpus": os.cpu_count(),
        "cpu_quota"   : cpu_quota(),
        "python"      : platform.python_version(),
        "timestamp"   : datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


# ─── one model (isolated subprocess) ──────────────────────────────────────────

def dir_size_mb(path: Path) -> float:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1e6


def model_cache_size_mb(cache: Path, model: str) -> float | None:
    """fastembed stores models as models--<org>--<name>; match on the name."""
    needle = model.split("/")[-1].lower()
    hits   = [p for p in cache.iterdir() if p.is_dir() and needle in p.name.lower()]
    return round(sum(dir_size_mb(p) for p in hits), 1) if hits else None


def bench_one(model: str, threads: int, candidates: list[int],
              reps: int, cache: str) -> dict:
    # Thread env must be set before onnxruntime is imported.
    os.environ["OMP_NUM_THREADS"] = str(threads)
    # Load from the prefetched cache only. Without this, fastembed checks the
    # HuggingFace Hub on every load, and a network failure aborts the run.
    os.environ["HF_HUB_OFFLINE"] = "1"

    import resource
    import onnxruntime
    import fastembed
    from fastembed.rerank.cross_encoder import TextCrossEncoder

    sets = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))["sets"]

    t0      = time.perf_counter()
    encoder = TextCrossEncoder(model_name=model, cache_dir=cache, threads=threads)
    load_s  = time.perf_counter() - t0

    for i in range(WARMUP_RUNS):
        s = sets[i % len(sets)]
        list(encoder.rerank(s["query"], s["docs"][:max(candidates)]))

    by_n = {}
    for n in candidates:
        times, spreads = [], []
        for i in range(reps):
            s  = sets[i % len(sets)]
            t0 = time.perf_counter()
            scores = list(encoder.rerank(s["query"], s["docs"][:n], batch_size=64))
            times.append(time.perf_counter() - t0)
            spreads.append(max(scores) - min(scores))
        times.sort()
        by_n[str(n)] = {
            "p50_s"  : round(statistics.median(times), 3),
            "p95_s"  : round(statistics.quantiles(times, n=20)[18], 3),
            "min_s"  : round(times[0], 3),
            "max_s"  : round(times[-1], 3),
            # Sanity: constant scores would mean the model did not really run.
            "min_score_spread": round(min(spreads), 3),
        }

    return {
        "model"        : model,
        "threads"      : threads,
        "load_s"       : round(load_s, 2),
        "peak_rss_mb"  : round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
        "model_disk_mb": model_cache_size_mb(Path(cache), model),
        "latency"      : by_n,
        "versions"     : {"fastembed": fastembed.__version__,
                          "onnxruntime": onnxruntime.__version__},
    }


# ─── run (orchestrator) ───────────────────────────────────────────────────────

def run_all(args) -> None:
    info    = host_info(args.label)
    results = []
    print(f"[HOST] {info}")

    for model in args.models:
        for threads in args.threads:
            cmd = [sys.executable, __file__, "one",
                   "--model", model, "--threads", str(threads),
                   "--reps", str(args.reps), "--cache", args.cache,
                   "--candidates", *map(str, args.candidates)]
            print(f"\n[RUN] {model}  threads={threads} ...", flush=True)
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                print(f"[FAIL] {proc.stderr.strip()[-800:]}")
                results.append({"model": model, "threads": threads,
                                "error": proc.stderr.strip()[-800:]})
                continue
            r = json.loads(proc.stdout.strip().splitlines()[-1])
            results.append(r)
            for n, lat in r["latency"].items():
                print(f"       n={n:<3} p50={lat['p50_s']:.3f}s  p95={lat['p95_s']:.3f}s")
            print(f"       load={r['load_s']}s  rss={r['peak_rss_mb']} MB  "
                  f"disk={r['model_disk_mb']} MB")

    print_table(info, results)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp   = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path    = out_dir / f"{args.label}_{stamp}.json"
    path.write_text(json.dumps({"host": info, "results": results}, indent=2),
                    encoding="utf-8")
    print(f"\n[SAVE] {path}")


def print_table(info: dict, results: list[dict]) -> None:
    print(f"\n## {info['label']} - {info['cpu_model']} "
          f"(quota {info['cpu_quota']} CPUs)\n")
    print("| Model | Threads | n | p50 (s) | p95 (s) | Peak RSS (MB) | Disk (MB) |")
    print("|---|---|---|---|---|---|---|")
    for r in results:
        if "error" in r:
            print(f"| {r['model']} | {r['threads']} | - | error | | | |")
            continue
        for n, lat in r["latency"].items():
            print(f"| {r['model']} | {r['threads']} | {n} | {lat['p50_s']:.3f} | "
                  f"{lat['p95_s']:.3f} | {r['peak_rss_mb']} | {r['model_disk_mb']} |")


def prefetch(models: list[str], cache: str) -> None:
    from fastembed.rerank.cross_encoder import TextCrossEncoder
    for model in models:
        t0 = time.perf_counter()
        TextCrossEncoder(model_name=model, cache_dir=cache)
        print(f"[PREFETCH] {model}  {time.perf_counter() - t0:.1f}s")


def list_models() -> None:
    from fastembed.rerank.cross_encoder import TextCrossEncoder
    for m in TextCrossEncoder.list_supported_models():
        print(f"{m.get('model', m)}  size_gb={m.get('size_in_GB', '?')}")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    p   = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("make-sample")
    s.add_argument("--chunks", default="data/index/chunks.json")
    s.add_argument("--out",    default=str(SAMPLE_PATH))

    sub.add_parser("list-models")

    s = sub.add_parser("prefetch")
    s.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    s.add_argument("--cache",  default="/cache")

    for name in ("run", "one"):
        s = sub.add_parser(name)
        s.add_argument("--cache",      default="/cache")
        s.add_argument("--reps",       type=int, default=DEFAULT_REPS)
        s.add_argument("--candidates", type=int, nargs="+", default=DEFAULT_CANDIDATES)
        if name == "run":
            s.add_argument("--models",  nargs="+", default=DEFAULT_MODELS)
            s.add_argument("--threads", type=int, nargs="+", default=DEFAULT_THREADS)
            s.add_argument("--label",   required=True)
            s.add_argument("--out",     default="/out")
        else:
            s.add_argument("--model",   required=True)
            s.add_argument("--threads", type=int, required=True)

    args = p.parse_args()
    if args.cmd == "make-sample":
        make_sample(Path(args.chunks), Path(args.out))
    elif args.cmd == "list-models":
        list_models()
    elif args.cmd == "prefetch":
        prefetch(args.models, args.cache)
    elif args.cmd == "run":
        run_all(args)
    elif args.cmd == "one":
        print(json.dumps(bench_one(args.model, args.threads, args.candidates,
                                   args.reps, args.cache)))


if __name__ == "__main__":
    main()
