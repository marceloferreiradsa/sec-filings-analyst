"""
rerank.py — second-stage reranking through hosted APIs, in a fallback chain.

A reranker reads the question and each candidate passage *together* (a
cross-encoder), which orders a short candidate list better than the first-stage
retrieval can. Running one on the VPS CPU was measured and rejected (2–29 s per
query, experiments/rerank_latency); hosted APIs answer in ~0.3–1.3 s (ADR-14).

Chain, first that answers wins (ADR-14, ADR-22):
  1. Cloudflare Workers AI  @cf/baai/bge-reranker-base   — free daily quota
  2. SubQ Snap              subq-snap-1.1 (decision model; yes-probability as score)
  3. none                   → the caller keeps the first-stage order and the app
                              tells the user that reranking is unavailable

Keys come from the environment and are never logged: CLOUDFLARE_ACCOUNT_ID,
CLOUDFLARE_API_TOKEN, SUBQ_SEC_FILINGS_API_KEY. A provider whose keys are missing
is skipped. Standard library only (no new dependency in the image).
"""

import hashlib
import http.client
import json
import os
from pathlib import Path
from typing import Optional

CLOUDFLARE_MODEL = "@cf/baai/bge-reranker-base"
SUBQ_MODEL       = "subq-snap-1.1"
DEFAULT_CHAIN    = ("cloudflare", "subq")
TIMEOUT_S        = 3.0


def _post(host: str, path: str, token: str, body: dict, timeout: float) -> dict:
    conn = http.client.HTTPSConnection(host, timeout=timeout)
    try:
        conn.request("POST", path, json.dumps(body),
                     {"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        resp = conn.getresponse()
        data = resp.read()
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status}")   # body may echo request data; not logged
        return json.loads(data)
    finally:
        conn.close()


def _cloudflare(query: str, texts: list[str], timeout: float) -> list[float]:
    account = os.environ["CLOUDFLARE_ACCOUNT_ID"]
    r = _post("api.cloudflare.com", f"/client/v4/accounts/{account}/ai/run/{CLOUDFLARE_MODEL}",
              os.environ["CLOUDFLARE_API_TOKEN"],
              {"query": query, "contexts": [{"text": t} for t in texts], "top_k": len(texts)},
              timeout)
    scores = [0.0] * len(texts)
    for item in r["result"]["response"]:
        scores[item["id"]] = float(item["score"])
    return scores


def _subq(query: str, texts: list[str], timeout: float) -> list[float]:
    # Decision model, not a reranker: one request holds the question and all numbered
    # passages; one yes/no question per passage; P(yes) is the score (max 128).
    passages = "\n\n".join(f"[p{i:02d}] {t}" for i, t in enumerate(texts))
    questions = {
        f"p{i:02d}": {
            "type": "noul",
            "instructions": f"Does passage p{i:02d} contain information that helps "
                            f"answer the user question?",
            "criteria": {"true": "It directly addresses the question",
                         "false": "It is off-topic or only loosely related"},
        }
        for i in range(len(texts))
    }
    r = _post("api.subq.ai", "/v1/systemone", os.environ["SUBQ_SEC_FILINGS_API_KEY"],
              {"model": SUBQ_MODEL,
               "state": f"USER QUESTION: {query}\n\nPASSAGES:\n{passages}",
               "questions": questions},
              timeout)
    return [float(r["answers"][f"p{i:02d}"]["noul"]) for i in range(len(texts))]


PROVIDERS = {
    "cloudflare": (_cloudflare, ("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN")),
    "subq":       (_subq,       ("SUBQ_SEC_FILINGS_API_KEY",)),
}


class Reranker:
    """Scores candidates with the first provider in `chain` that answers.

    cache_path: optional JSON file of past scores, keyed by provider + question +
    passage texts — used by the evaluation so repeated runs spend no quota.
    """

    def __init__(self, chain: tuple[str, ...] = DEFAULT_CHAIN, timeout: float = TIMEOUT_S,
                 cache_path: Optional[Path] = None) -> None:
        unknown = set(chain) - PROVIDERS.keys()
        if unknown:
            raise ValueError(f"unknown rerank providers: {sorted(unknown)}")
        self.chain      = chain
        self.timeout    = timeout
        self.cache_path = cache_path
        self.cache: dict = (json.loads(cache_path.read_text(encoding="utf-8"))
                            if cache_path and cache_path.exists() else {})
        self.calls      = {name: 0 for name in chain}
        self.failures   = {name: 0 for name in chain}

    @staticmethod
    def _key(provider: str, query: str, texts: list[str]) -> str:
        h = hashlib.sha256(json.dumps([provider, query, texts]).encode("utf-8")).hexdigest()
        return f"{provider}:{h}"

    def score(self, query: str, texts: list[str]) -> tuple[Optional[list[float]], str]:
        """(scores aligned with texts, provider) — (None, "none") if every provider failed."""
        if not texts:
            return [], "none"
        for name in self.chain:
            fn, keys = PROVIDERS[name]
            if not all(os.environ.get(k) for k in keys):
                continue
            key = self._key(name, query, texts)
            if key in self.cache:
                return self.cache[key], name
            try:
                self.calls[name] += 1
                scores = fn(query, texts, self.timeout)
            except Exception:          # timeout, HTTP error, malformed body → next provider
                self.failures[name] += 1
                continue
            self.cache[key] = scores
            return scores, name
        return None, "none"

    def save_cache(self) -> None:
        if self.cache_path:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(json.dumps(self.cache), encoding="utf-8")
