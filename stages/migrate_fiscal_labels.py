"""
migrate_fiscal_labels.py — one-off: apply ADR-19's fiscal calendar to the
existing processed data, without re-ingesting.

Re-running ingest would fetch filings published since the corpus was built, so
the corpus and the labels would change together and EV-03 could not attribute
the effect. This script changes only what ADR-19 changes:

  - fiscal_year / fiscal_period metadata of every 10-Q document and chunk
  - the "Period: …" header inside every financial summary (10-K and 10-Q text),
    rewritten with period_label(): fiscal label + end date in words. Only chunks
    whose text changed are re-embedded; every other vector is kept as is

Idempotent: a second run finds nothing to change. The backup keeps the state from
before the first run.

Files (all under data/processed/): documents.json, chunks.json,
embedded_chunks.json, embeddings.npy. A backup of each is written to
data/processed/backup_pre_adr19/ before anything is overwritten. Rebuild the
FAISS index afterwards with:  python stages/index.py --no-test

Usage (from the project root):
  python stages/migrate_fiscal_labels.py            # dry run: report only
  python stages/migrate_fiscal_labels.py --apply    # write (paid: one embedding call, ≤40 texts)
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from data_loaders.fiscal import fiscal_year_period, period_label  # noqa: E402
from stages.embed import EMBEDDING_MODEL                          # noqa: E402

PROCESSED = Path("data/processed")
BACKUP    = PROCESSED / "backup_pre_adr19"
FILES     = ("documents.json", "chunks.json", "embedded_chunks.json", "embeddings.npy")
HEADER    = re.compile(r"Period: FY\d{4}(?: Q[1-4])?(?: \((?:quarter|fiscal year) ended [^)]*\))?")


def relabel(item: dict) -> tuple[bool, bool]:
    """Relabel one document/chunk in place. Returns (metadata_changed, text_changed)."""
    m = item["metadata"]
    if not m.get("period_end"):
        return False, False
    fy, fp = fiscal_year_period(m["company"], m["period_end"], m["filing_type"])
    old = (int(m["fiscal_year"]), m["fiscal_period"])
    if m["filing_type"] == "10-K" and old != (fy, fp):
        raise AssertionError(f"10-K label would change: {m}")   # ADR-19 must not touch 10-Ks
    m["fiscal_year"], m["fiscal_period"] = fy, fp

    text_changed = False
    if m.get("source_type") == "financial_data":
        label = period_label(m["company"], m["period_end"], m["filing_type"])
        new_text, n = HEADER.subn(f"Period: {label}", item["page_content"], count=1)
        if n != 1:
            raise AssertionError(f"no Period header in financial summary: {m}")
        text_changed = new_text != item["page_content"]
        item["page_content"] = new_text
    return old != (fy, fp), text_changed


def main() -> None:
    p = argparse.ArgumentParser(description="Apply ADR-19 fiscal labels to processed data.")
    p.add_argument("--apply", action="store_true", help="write files (re-embeds changed texts)")
    args = p.parse_args()

    docs     = json.loads((PROCESSED / "documents.json").read_text(encoding="utf-8"))
    chunks   = json.loads((PROCESSED / "chunks.json").read_text(encoding="utf-8"))
    embedded = json.loads((PROCESSED / "embedded_chunks.json").read_text(encoding="utf-8"))
    vectors  = np.load(PROCESSED / "embeddings.npy")
    assert len(embedded) == vectors.shape[0], "embedded_chunks.json and embeddings.npy misaligned"

    reembed: list[int] = []
    for name, items in (("documents", docs), ("chunks", chunks), ("embedded", embedded)):
        meta = text = 0
        for i, it in enumerate(items):
            mc, tc = relabel(it)
            meta += mc
            text += tc
            if tc and name == "embedded":
                reembed.append(i)
        print(f"[MIGRATE] {name:<9} {len(items):>5} items · {meta:>4} relabelled · {text:>3} texts changed")
    print(f"[MIGRATE] rows to re-embed: {len(reembed)} (of {vectors.shape[0]})")

    if not args.apply:
        print("[MIGRATE] dry run — nothing written. Re-run with --apply.")
        return

    from openai import OpenAI
    resp = OpenAI().embeddings.create(model=EMBEDDING_MODEL,
                                      input=[embedded[i]["page_content"] for i in reembed])
    new = np.array([d.embedding for d in resp.data], dtype=np.float32)
    for row, vec in zip(reembed, new):
        vectors[row] = vec

    BACKUP.mkdir(parents=True, exist_ok=True)
    for f in FILES:
        if not (BACKUP / f).exists():          # keep the first, pre-migration backup
            shutil.copy2(PROCESSED / f, BACKUP / f)
    for name, items in (("documents.json", docs), ("chunks.json", chunks),
                        ("embedded_chunks.json", embedded)):
        (PROCESSED / name).write_text(json.dumps(items, indent=2, default=str), encoding="utf-8")
    np.save(PROCESSED / "embeddings.npy", vectors)
    print(f"[MIGRATE] written; backup in {BACKUP}. Next: python stages/index.py --no-test")


if __name__ == "__main__":
    main()
