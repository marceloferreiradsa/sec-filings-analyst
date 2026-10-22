# ── Rerank latency benchmark image ────────────────────────────────────────────
# Same base as the production image (python:3.11-slim), so the numbers reflect
# what the app container would see. Models are NOT baked in: they download into
# the /cache volume with `prefetch`, keeping download time out of the timings
# and the image small enough to ship to the VPS.
#
# Build (from project root):  docker build -t rerank-bench experiments/rerank_latency

FROM python:3.11-slim

WORKDIR /bench

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bench.py sample.json ./

ENTRYPOINT ["python", "bench.py"]
CMD ["--help"]
