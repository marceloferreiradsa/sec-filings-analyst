"""
api_bench.py
────────────
Latency benchmark for HOSTED reranker APIs — the fallback if local reranking
is not viable (see README.md). Same sample.json as bench.py, so the numbers are
directly comparable with the local cross-encoders.

Standard library only: runs with the system python3 on the VPS, no image needed.
Connections are kept alive per provider, as a production client would do; the
first call (TLS handshake included) is reported separately as `cold_s`.

Keys come from environment variables, or — to run on the VPS without writing
them to disk or to the command line — as KEY=VALUE lines on stdin with
--keys-stdin. A provider without a key is skipped. Keys are never printed.

  CLOUDFLARE_ACCOUNT_ID + CLOUDFLARE_API_TOKEN   → @cf/baai/bge-reranker-base
  VOYAGE_API_KEY                                 → rerank-2.5, rerank-2.5-lite
  JINA_API_KEY                                   → jina-reranker-v3
  ZEROENTROPY_API_KEY                            → zerank-2
  SUBQ_SEC_FILINGS_API_KEY                       → subq-snap-1.1 (decision model)

Cost: all within each provider's free tier (~0.3M tokens per provider per run).

Usage:
  python experiments/rerank_latency/api_bench.py --label local-5900x
  printf 'VOYAGE_API_KEY=%s\n' "$VOYAGE_API_KEY" | \
      ssh vps "python3 ~/api_bench.py --keys-stdin --label vps --sample ~/sample.json"
"""

import argparse
import http.client
import json
import os
import socket
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent

DEFAULT_CANDIDATES = [20, 40]
DEFAULT_REPS       = 15
TIMEOUT_S          = 30


# ─── providers ────────────────────────────────────────────────────────────────
# Each returns (host, path, headers, body) for one rerank call, and a parser
# that extracts (n_scores, tokens_billed or None) from the JSON response.

def cloudflare(model, query, docs, keys):
    path = f"/client/v4/accounts/{keys['CLOUDFLARE_ACCOUNT_ID']}/ai/run/{model}"
    body = {"query": query, "contexts": [{"text": d} for d in docs], "top_k": len(docs)}
    return ("api.cloudflare.com", path,
            {"Authorization": f"Bearer {keys['CLOUDFLARE_API_TOKEN']}"}, body)


def parse_cloudflare(r):
    return len(r["result"]["response"]), None


def voyage(model, query, docs, keys):
    body = {"model": model, "query": query, "documents": docs, "top_k": len(docs)}
    return ("api.voyageai.com", "/v1/rerank",
            {"Authorization": f"Bearer {keys['VOYAGE_API_KEY']}"}, body)


def parse_voyage(r):
    return len(r["data"]), r.get("usage", {}).get("total_tokens")


def jina(model, query, docs, keys):
    body = {"model": model, "query": query, "documents": docs, "top_n": len(docs)}
    return ("api.jina.ai", "/v1/rerank",
            {"Authorization": f"Bearer {keys['JINA_API_KEY']}"}, body)


def parse_jina(r):
    return len(r["results"]), r.get("usage", {}).get("total_tokens")


def zeroentropy(model, query, docs, keys):
    body = {"model": model, "query": query, "documents": docs, "top_n": len(docs)}
    return ("api.zeroentropy.dev", "/v1/models/rerank",
            {"Authorization": f"Bearer {keys['ZEROENTROPY_API_KEY']}"}, body)


def parse_zeroentropy(r):
    return len(r["results"]), None


def subq(model, query, docs, keys):
    # SubQ Snap is a decision model, not a reranker: one request carries the
    # question plus all numbered passages as `state`, and one yes/no ("noul")
    # question per passage. The yes-probability is the relevance score.
    # Max 128 questions per request (docs.subq.ai, Decisions API).
    passages = "\n\n".join(f"[p{i:02d}] {d}" for i, d in enumerate(docs))
    state = f"USER QUESTION: {query}\n\nPASSAGES:\n{passages}"
    questions = {
        f"p{i:02d}": {
            "type": "noul",
            "instructions": f"Does passage p{i:02d} contain information that helps "
                            f"answer the user question?",
            "criteria": {"true": "It directly addresses the question",
                         "false": "It is off-topic or only loosely related"},
        }
        for i in range(len(docs))
    }
    body = {"model": model, "state": state, "questions": questions}
    return ("api.subq.ai", "/v1/systemone",
            {"Authorization": f"Bearer {keys['SUBQ_SEC_FILINGS_API_KEY']}"}, body)


def parse_subq(r):
    # input_tokens tells whether `state` is billed once per request or once per
    # question — the docs do not say.
    return len(r["answers"]), r.get("usage", {}).get("input_tokens")


PROVIDERS = [
    # (name, model, required keys, request builder, response parser)
    ("cloudflare",  "@cf/baai/bge-reranker-base",
     ["CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN"], cloudflare, parse_cloudflare),
    ("voyage",      "rerank-2.5",      ["VOYAGE_API_KEY"],      voyage,      parse_voyage),
    ("voyage",      "rerank-2.5-lite", ["VOYAGE_API_KEY"],      voyage,      parse_voyage),
    ("jina",        "jina-reranker-v3", ["JINA_API_KEY"],       jina,        parse_jina),
    ("zeroentropy", "zerank-2",        ["ZEROENTROPY_API_KEY"], zeroentropy, parse_zeroentropy),
    ("subq",        "subq-snap-1.1",   ["SUBQ_SEC_FILINGS_API_KEY"], subq,   parse_subq),
]


# ─── measurement ──────────────────────────────────────────────────────────────

class Client:
    """One keep-alive HTTPS connection per host, reopened after any failure."""

    def __init__(self, host: str):
        self.host = host
        self.conn = None

    def post(self, path: str, headers: dict, body: dict) -> dict:
        if self.conn is None:
            self.conn = http.client.HTTPSConnection(self.host, timeout=TIMEOUT_S)
        payload = json.dumps(body).encode("utf-8")
        try:
            self.conn.request("POST", path, body=payload, headers={
                **headers, "Content-Type": "application/json"})
            resp = self.conn.getresponse()
            data = resp.read()
        except (http.client.HTTPException, OSError):
            self.conn.close()
            self.conn = None
            raise
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status}: {data[:300].decode('utf-8', 'replace')}")
        return json.loads(data)


def bench_provider(name, model, build, parse, keys, sets, candidates, reps) -> dict:
    host   = build(model, "x", ["x"], keys)[0]
    client = Client(host)

    # Cold call: opens the connection (DNS + TCP + TLS) — what the first
    # request after an idle period pays.
    s0 = sets[0]
    _, path, headers, body = build(model, s0["query"], s0["docs"][:candidates[0]], keys)
    t0 = time.perf_counter()
    client.post(path, headers, body)
    cold_s = time.perf_counter() - t0

    by_n, tokens = {}, 0
    for n in candidates:
        times, errors = [], []
        for i in range(reps):
            s = sets[i % len(sets)]
            _, path, headers, body = build(model, s["query"], s["docs"][:n], keys)
            t0 = time.perf_counter()
            try:
                resp = client.post(path, headers, body)
            except Exception as exc:               # report, keep measuring
                errors.append(str(exc)[:200])
                continue
            times.append(time.perf_counter() - t0)
            n_scores, billed = parse(resp)
            if n_scores != n:
                errors.append(f"expected {n} scores, got {n_scores}")
            tokens += billed or 0
        times.sort()
        by_n[str(n)] = {
            "ok"    : len(times),
            "p50_s" : round(statistics.median(times), 3) if times else None,
            "p95_s" : round(statistics.quantiles(times, n=20)[18], 3) if len(times) >= 2 else None,
            "min_s" : round(times[0], 3) if times else None,
            "max_s" : round(times[-1], 3) if times else None,
            "errors": errors[:3],
        }

    return {"provider": name, "model": model, "host": host,
            "cold_s": round(cold_s, 3), "latency": by_n,
            "tokens_billed": tokens or None}


def read_keys(from_stdin: bool) -> dict:
    keys = {k: v for k, v in os.environ.items()
            if k.startswith(("CLOUDFLARE_", "VOYAGE_", "JINA_", "ZEROENTROPY_", "SUBQ_"))}
    if from_stdin:
        for line in sys.stdin.read().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                if v.strip():
                    keys[k.strip()] = v.strip()
    return keys


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--label",      required=True)
    p.add_argument("--sample",     default=str(HERE / "sample.json"))
    p.add_argument("--out",        default=str(HERE / "results"))
    p.add_argument("--reps",       type=int, default=DEFAULT_REPS)
    p.add_argument("--candidates", type=int, nargs="+", default=DEFAULT_CANDIDATES)
    p.add_argument("--keys-stdin", action="store_true")
    args = p.parse_args()

    keys = read_keys(args.keys_stdin)
    sets = json.loads(Path(args.sample).read_text(encoding="utf-8"))["sets"]
    info = {"label": args.label, "hostname": socket.gethostname(),
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    print(f"[HOST] {info}")

    results = []
    for name, model, required, build, parse in PROVIDERS:
        missing = [k for k in required if k not in keys]
        if missing:
            print(f"[SKIP] {name}/{model}: no {', '.join(missing)}")
            continue
        print(f"[RUN] {name}/{model} ...", flush=True)
        try:
            r = bench_provider(name, model, build, parse, keys, sets,
                               args.candidates, args.reps)
        except Exception as exc:
            print(f"[FAIL] {name}/{model}: {str(exc)[:300]}")
            results.append({"provider": name, "model": model, "error": str(exc)[:300]})
            continue
        results.append(r)
        for n, lat in r["latency"].items():
            print(f"       n={n:<3} ok={lat['ok']}  p50={lat['p50_s']}s  "
                  f"p95={lat['p95_s']}s  errors={len(lat['errors'])}")
        print(f"       cold={r['cold_s']}s  tokens_billed={r['tokens_billed']}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path  = out_dir / f"api_{args.label}_{stamp}.json"
    path.write_text(json.dumps({"host": info, "results": results}, indent=2),
                    encoding="utf-8")
    print(f"\n[SAVE] {path}")


if __name__ == "__main__":
    main()
