# Experiment — Local reranker latency on CPU

**Status:** In progress (local run done first; VPS run pending)
**Feeds:** roadmap P1 (cross-encoder rerank, FEAT-04) · open decision AB-01
**Cost:** $0 — no OpenAI calls

---

## Question

Can a cross-encoder rerank the retrieval candidates **inside the production
container, on the VPS CPU**, fast enough and small enough to keep?

The owner's decision (2026-10-21): reranking is **local by default**. A hosted
reranker API is considered only if this experiment shows local is not viable.

## What a reranker does here

Retrieval today compares one vector per chunk, computed before any question
existed, with the question vector. A cross-encoder instead reads the question
**and** each candidate chunk together and scores the pair. It is more precise and
much slower, so it only runs on the few dozen candidates the first stage returns:

```
question → BM25 + dense (FAISS) → ~40 candidates → cross-encoder → top 5–8 → LLM
```

It is a small classifier-sized transformer (22M–280M parameters), not an LLM, so
it can run on CPU. This experiment measures **cost in time and memory only**.
Whether reranking improves retrieval quality is measured separately, by P0
(Recall@k / MRR on the golden set).

## Setup

| Item | Value |
|---|---|
| Runtime | `fastembed==0.8.1` on ONNX Runtime — **no torch** (torch brings the image to ~3 GB) |
| Base image | `python:3.11-slim`, same as production |
| Candidates | 20 and 40 per query (40 is the planned production value) |
| Threads | 1 and 2 (the VPS has 2 vCPUs) |
| Repetitions | 15 per configuration, after 2 warm-up runs; p50 and p95 reported |
| Data | 8 narrative questions × 50 real narrative chunks of the queried company, sampled from `data/index/chunks.json` (seed 42). Mean 1,140 chars ≈ 285 tokens — matches the corpus mean (283) |
| Isolation | each model × thread count runs in its own subprocess, so peak RSS is per model |
| Excluded from timing | model download (`prefetch`) and model load (once per app start in production) |

Models, smallest to largest (sizes from `list-models`):

| Model | Size | Note |
|---|---|---|
| `Xenova/ms-marco-MiniLM-L-6-v2` | 0.08 GB | General-domain (MS MARCO); option A in the roadmap |
| `Xenova/ms-marco-MiniLM-L-12-v2` | 0.12 GB | Deeper version of the above |
| `jinaai/jina-reranker-v1-tiny-en` | 0.13 GB | |
| `jinaai/jina-reranker-v1-turbo-en` | 0.15 GB | |
| `BAAI/bge-reranker-base` | 1.04 GB | Option B; expected to be too slow on 2 vCPUs |

Hardware:

| Machine | CPU | Notes |
|---|---|---|
| Local | AMD Ryzen 9 5900X (Zen 3, 12C/24T, AVX2) | Docker Desktop, limited with `--cpus=2` |
| VPS (Hostinger) | AMD EPYC 9354P (Zen 4, AVX-512), 2 vCPU, 8 GB RAM | Shared vCPUs; production app running idle alongside |

Which CPU is faster per core cannot be told in advance: Zen 3 boosts higher, Zen 4
has AVX-512 (used by ONNX Runtime) and the VPS vCPUs are shared. Hence the same
image runs on both.

## Viability criterion

> **Approved by the owner on 2026-10-21**, before the VPS numbers existed, so the
> decision cannot be fitted to the result.

Measured **on the VPS**, 2 threads, 40 candidates:

| Verdict | Condition |
|---|---|
| Viable | some model has p95 ≤ 1.0 s, peak RSS ≤ 1 GB |
| Viable with a trade-off | p95 ≤ 2.0 s only with 20 candidates or a smaller model |
| Not viable → evaluate APIs | every model above 2.0 s p95 at 20 candidates |

Reference for "fast enough": today a query spends ~0.4 s embedding the question
and 3–8 s generating the answer (ADR-07), so 1 s of reranking adds roughly
12–25% to the end-to-end time.

**Would be false if** a second concurrent user doubles the latency past the
threshold — two vCPUs are shared by all requests. Not tested here; noted as a
limitation.

## How to run

From the project root (Git Bash: `export MSYS_NO_PATHCONV=1` first):

```bash
python experiments/rerank_latency/bench.py make-sample      # host, reads data/index
docker build -t rerank-bench experiments/rerank_latency
docker run --rm -v rerank-cache:/cache rerank-bench prefetch
docker run --rm --cpus=2 -v rerank-cache:/cache \
    -v "$(pwd -W)/experiments/rerank_latency/results:/out" \
    rerank-bench run --label local-5900x-cpus2
```

Results land in `results/<label>_<timestamp>.json` and a Markdown table is
printed at the end.

## Results

### VPS — 2026-10-22, `results/vps-epyc9354p-2vcpu_20261022T010544Z.json`

p95 in seconds, 15 reps after 2 warm-ups (p50 in the JSON):

| Model | 1 thread, n=20 | 1 thread, n=40 | 2 threads, n=20 | 2 threads, n=40 |
|---|---|---|---|---|
| MiniLM-L6 | 3.37 | 6.28 | **1.66** | 3.22 |
| MiniLM-L12 | 6.27 | 12.04 | 3.07 | 8.51 |
| jina-v1-tiny | 2.40 | 6.20 | **1.75** | 3.27 |
| jina-v1-turbo | 3.72 | 8.84 | 2.08 | 4.71 |
| bge-reranker-base | 19.62 | 49.86 | 18.89 | 29.00 |

Peak RSS: ~2.0 GB for every small model, ~3.5 GB for bge-base (see open questions).

**Verdict against the approved criterion (preliminary — levers below not yet tried):**
not *Viable* (no model ≤ 1.0 s p95 at n=40); **Viable with a trade-off** —
MiniLM-L6 and jina-v1-tiny stay under 2.0 s p95 at n=20 with 2 threads.
bge-reranker-base is ruled out for local use on this VPS.
*Would be false if* the open questions below change the numbers by a large factor
in either direction.

My pre-run estimate for MiniLM-L6 (0.3–1 s at n=40) was wrong by ~3×. A FLOP count
agrees with the measurement: ~10M non-embedding parameters × ~300 tokens × 2 ≈
6 GFLOP per pair, ≈ 250 GFLOP per 40-candidate query — seconds on 2 vCPUs.

### Local — Ryzen 5900X, `--cpus=2`

Full run in progress at session close (2026-10-22). Three configurations survived the
first, invalid attempt (`results/INVALID-network-errors_*.json`, model loads failed on
network errors) and already answer "which CPU is faster per core": at 2 threads,
MiniLM-L6 p95 n=40 was 3.77 s locally vs 3.22 s on the VPS, jina-turbo 4.48 s vs
4.71 s. **The VPS is on par or slightly faster per core**; the local machine only
wins on core count.

### Open questions (next runs, all $0)

- **Peak RSS ~2 GB for an 80 MB model**, and it grows with the number of repetitions
  (1.1 GB after 2 reps vs 2.0 GB after 15). Hypothesis: ONNX Runtime's memory arena
  grows for every new input shape. Test: smaller `batch_size`, arena disabled.
- **Levers not yet tried:** int8-quantized ONNX models (typically 2–3× faster on
  CPU — hypothesis), truncating pairs to 256 tokens, smaller batches.
- `model_disk_mb` looks wrong (jina-tiny reports the same size as MiniLM-L12; bge
  2.26 GB vs 1.04 GB listed) — the cache-folder match in `bench.py` needs fixing.

## Fallback — hosted reranker APIs (`api_bench.py`)

### Cloudflare `@cf/baai/bge-reranker-base` — 2026-10-22

Seconds, 15 reps, keep-alive connection; `results/api_vps-epyc9354p_20261022T011659Z.json`
and `results/api_local-5900x_20261022T011634Z.json`. 0 errors in 60 calls.

| Called from | n=20 p50 | n=20 p95 | n=40 p50 | n=40 p95 | First call |
|---|---|---|---|---|---|
| **VPS** | 0.61 | 1.52 | **0.66** | 2.88 | 1.00 |
| Local | 0.65 | 1.65 | 0.69 | 1.59 | 1.40 |

Reading: the **same model** that takes 19 s p50 locally on the VPS (n=40, 2 threads)
answers in 0.66 s p50 through the API — and latency barely grows from 20 to 40
candidates, so the cost is mostly network and queueing, not compute. The tail is
noisy: with 15 samples p95 is effectively the second-largest value, and one slow call
moves it from ~1.6 s to 2.9 s. **Would be false if** a run with more repetitions
(free: ~2,900 queries/day) shows a p95 that stays near 3 s — then the tail is the
service, not sampling noise. Tokens billed are not returned by this API.

Against the same thresholds as the local criterion: p50 well under 1.0 s, p95 at
n=20 under 2.0 s → also *viable with a trade-off*, held back only by the tail.
Quality (bge-base vs MiniLM-L6) is P0's question.

### Second run — Cloudflare and SubQ Snap, 30 reps — 2026-10-22

`results/api_vps-epyc9354p_20261022T221636Z.json` and
`results/api_local-5900x_20261022T221535Z.json`. Seconds, keep-alive connection.

| Called from the **VPS** | n=20 p50 | n=20 p95 | n=40 p50 | n=40 p95 | First call | Errors |
|---|---|---|---|---|---|---|
| Cloudflare `bge-reranker-base` | 0.49 | 0.99 | 0.68 | **1.30** | 1.54 | 0 / 60 |
| SubQ `subq-snap-1.1` | 0.26 | 0.33 | **0.33** | **0.47** | 0.84 | 0 / 60 |

Called locally: Cloudflare n=40 p50 0.66 / p95 1.19, 0 errors; SubQ n=40 p50 0.43 /
p95 0.62, **3 / 60 errors** — `HTTP 403 "Model 'subq-snap-1.1' is not permitted for
this API key"`, intermittent, same key that succeeded on the other 117 calls.
Hypothesis: provider-side flakiness (model is in public preview). *Would be false if*
the 403s cluster by source IP or by request rate.

**Cloudflare tail:** with 30 reps the n=40 p95 is 1.30 s (1.19 s locally). The 2.88 s
of the first run was sampling noise — the falsifier stated above did not hold.

**SubQ Snap as a reranker.** It has no rerank endpoint; `api_bench.py` uses the
Decisions API (`POST /v1/systemone`): `state` = question + numbered passages, one
yes/no (`noul`) question per passage (max 128 per request), yes-probability = score.
- **Billing measured:** 507,558 input tokens for 60 requests / 1,800 passages on the
  VPS ≈ 282 tokens per passage → `state` is billed **once per request**, not per
  question (the docs do not say). ≈ 11k tokens per 40-candidate query ≈ $0.00045 at
  $0.04 / 1M (Models page, 2026-10-22); 100M free tokens ≈ 9,000 queries.
- **Sanity check** (one call, set 0, 20 random passages): scores discriminate — top
  0.049 for an inventory/lead-time passage, bottom 0.000 for "Available Information"
  boilerplate. Scores are low because random passages rarely answer the question;
  only the order matters for reranking. Quality vs a cross-encoder, and position bias
  from scoring all passages in one prompt, are P0's questions.

Cloudflare neuron accounting could not be checked: the owner did not find per-model
neuron usage in the dashboard. The ~2,900 queries/day estimate stays a hypothesis;
it holds for the demo's traffic even if it is off by 10×.

### Setup

Script dry-run validated (no keys → skip; fake key → HTTP 401, key not
written to the result file; real-run results also checked for the token). Keys go in a file
**outside the repo** (e.g. `~/.rerank-keys`, `KEY=VALUE` per line) and are piped via
`--keys-stdin`, locally and over `ssh` to the VPS — never on disk there, never on a
command line.

Candidates, prices checked 2026-10-21 on the official pages (~12k tokens per query
= 40 candidates × ~285 tokens):

| Provider / model | Price | Free | Per query | Source |
|---|---|---|---|---|
| Cloudflare Workers AI `@cf/baai/bge-reranker-base` | $0.003 / 1M tokens | 10k neurons/day ≈ 2,900 queries/day | ~$0.00004 | developers.cloudflare.com/workers-ai/platform/pricing |
| Voyage `rerank-2.5` / `-lite` (also `rerank-3` / `-lite`) | $0.05 / $0.02 per 1M | 200M tokens (page contradicts itself for 2.5) | $0.0006 / $0.00025 | docs.voyageai.com/docs/pricing |
| ZeroEntropy `zerank-2` | $0.025 / 1M | not stated | $0.0003 | zeroentropy.dev/pricing |
| Jina `jina-reranker-v3` / `v3.5` | not on the official page | free tokens for new keys; 100 RPM | ~$0.0006 (aggregators) | jina.ai/reranker |
| Subquadratic **SubQ Snap** | $0.05 / 1M input, output free | 100M tokens for the first 10k users | ~$0.0006 | subq.ai |
| Ruled out | Cohere (dedicated only, $2,500/mo), Pinecone (not in free plan, $2/1k), Together / Mixedbread (dedicated or bundles), NVIDIA build (trial endpoints, deprecations) | | | |

**SubQ Snap is not a reranker endpoint.** It is a 384K-context "decision model"
advertised for "routing, ranking, classifying, yes/no calls" with structured output
(choice, score, label). As a reranker it would be an LLM-style listwise/pointwise
scorer — latency and API shape unknown (docs at docs.subq.ai, not yet read). It may
fit better elsewhere in the roadmap: P2 query routing, and the P0 long-context arm
(384K holds a multi-company question of ~220k tokens).

Open: Cloudflare token creation is confusing — use the **"Workers AI" API token
template** (My Profile → API Tokens → Create Token) plus the Account ID from the
dashboard home.

## Limitations

- Latency only. Quality gain is P0's job.
- Single request at a time; concurrency on 2 vCPUs not measured.
- `--cpus=2` locally is a CFS quota, not core pinning; SMT siblings may share a
  physical core. The VPS run is the one that decides.
- Image growth measured on the benchmark image (+223 MB over `python:3.11-slim`,
  part of it numpy, which production already ships). The real delta is measured
  when the reranker enters the production image.
