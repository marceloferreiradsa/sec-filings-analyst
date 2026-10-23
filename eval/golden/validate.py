"""
validate.py
───────────
Checks the golden set against the indexed corpus before anyone reviews it.

Labels are (company, filing_type, period_end, section) plus a LITERAL evidence
phrase — not chunk IDs, which change whenever the corpus is re-chunked. A chunk is
"relevant" if it matches the four fields and contains the evidence (whitespace
collapsed). This script fails loudly if any evidence cannot be found.

Checks
  - every line parses and has the required fields; ids are unique
  - every evidence phrase exists in at least one matching chunk
  - every expected_figure accept string appears in its evidence
  - must_refuse questions carry no expected sources

Usage (from the project root):
  python eval/golden/validate.py              # validate
  python eval/golden/validate.py --table      # also print a review table
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

GOLDEN_PATH = Path("eval/golden/golden_set.jsonl")
CHUNKS_PATH = Path("data/index/chunks.json")

REQUIRED   = {"id", "category", "question", "expected", "expected_figure",
              "must_refuse", "notes", "reviewed"}
CATEGORIES = {"figure", "narrative", "comparison", "trend", "temporal", "out_of_corpus"}
KEYS       = ("company", "filing_type", "period_end", "section")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def load_corpus() -> dict[tuple, list[str]]:
    by_key: dict[tuple, list[str]] = {}
    for c in json.loads(CHUNKS_PATH.read_text(encoding="utf-8")):
        key = tuple(c["metadata"][k] for k in KEYS)
        by_key.setdefault(key, []).append(norm(c["page_content"]))
    return by_key


def matching_chunks(corpus: dict, exp: dict) -> int:
    key = tuple(exp[k] for k in KEYS)
    ev  = norm(exp["evidence"])
    return sum(ev in text for text in corpus.get(key, []))


def validate(items: list[dict], corpus: dict) -> list[str]:
    errors = []
    ids    = Counter(it.get("id") for it in items)
    for dup in [i for i, n in ids.items() if n > 1]:
        errors.append(f"{dup}: duplicate id")

    for it in items:
        qid = it.get("id", "?")
        missing = REQUIRED - it.keys()
        if missing:
            errors.append(f"{qid}: missing fields {sorted(missing)}")
            continue
        if it["category"] not in CATEGORIES:
            errors.append(f"{qid}: unknown category {it['category']!r}")
        if it["must_refuse"] and it["expected"]:
            errors.append(f"{qid}: must_refuse with expected sources")
        if not it["must_refuse"] and not it["expected"]:
            errors.append(f"{qid}: no expected sources")

        for exp in it["expected"]:
            if any(k not in exp for k in (*KEYS, "evidence")):
                errors.append(f"{qid}: expected entry missing keys")
                continue
            if matching_chunks(corpus, exp) == 0:
                errors.append(f"{qid}: evidence not found in "
                              f"{'/'.join(exp[k] for k in KEYS)}: {exp['evidence']!r}")

        # The first accepted form is the exact value and must be in the evidence;
        # the others are roundings of it (e.g. 416.16 → 416.2) within 0.05.
        fig = it["expected_figure"]
        if fig:
            evidence = " ".join(norm(e["evidence"]) for e in it["expected"])
            exact    = fig["accept"][0]
            if exact not in evidence:
                errors.append(f"{qid}: exact value {exact!r} not in evidence")
            for acc in fig["accept"][1:]:
                try:
                    off = abs(float(acc.rstrip("%")) - float(exact.rstrip("%")))
                except ValueError:
                    off = None
                if off is None or off > 0.05 + 1e-9:
                    errors.append(f"{qid}: accept {acc!r} is not a rounding of {exact!r}")
    return errors


def print_table(items: list[dict]) -> None:
    print("| id | Question | Source | Evidence | Answer |")
    print("|---|---|---|---|---|")
    for it in items:
        src = "; ".join(f"{e['company']} {e['filing_type']} {e['period_end']} {e['section']}"
                        for e in it["expected"]) or "—"
        ev  = "; ".join(e["evidence"] for e in it["expected"]) or "—"
        ans = (it["expected_figure"] or {}).get("text") or ("refuse" if it["must_refuse"] else "—")
        print(f"| {it['id']} | {it['question']} | {src} | {ev} | {ans} |")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--table", action="store_true")
    args = p.parse_args()

    items  = [json.loads(line) for line in GOLDEN_PATH.read_text(encoding="utf-8").splitlines()
              if line.strip()]
    errors = validate(items, load_corpus())

    by_cat = Counter(it["category"] for it in items)
    print(f"[GOLDEN] {len(items)} questions  "
          + "  ".join(f"{k}={v}" for k, v in sorted(by_cat.items()))
          + f"  reviewed={sum(it['reviewed'] for it in items)}")
    if args.table:
        print_table(items)
    if errors:
        print(f"\n[FAIL] {len(errors)} problem(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("[OK] every evidence phrase found in the corpus")


if __name__ == "__main__":
    main()
