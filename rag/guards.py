"""
rag/guards.py — Input validation and prompt injection protection.

Two attack surfaces in a RAG system:
  1. User query   — direct injection attempt in the question text.
  2. Retrieved context — indirect injection embedded in document content.

This module handles both, deliberately at different severity levels:
  - User queries:   BLOCK — malicious input never reaches the LLM.
  - Context chunks: LOG only — the SEC corpus is controlled; any match
                    is a pipeline anomaly, not a live attack.

The LLM's own RLHF training is the primary defence. This module catches
the obvious patterns at the application layer before they consume API tokens.

Public API:
  sanitize_query(query)             → str | raises InjectionAttemptError
  check_context_for_injection(chunks) → None (logs warnings)
  InjectionAttemptError             — catch this in the application layer
"""

import logging
import re

logger = logging.getLogger(__name__)

MAX_QUERY_LENGTH = 1000   # characters; long queries are often injection vectors


# ── Injection pattern library ─────────────────────────────────────────────────
# Ordered from most common to most specific.
# Not exhaustive — RLHF covers the long tail.

_PATTERNS = [
    # Direct override commands
    r"ignore\s+(all|your|previous|prior)\s+(instructions?|rules?|constraints?|prompts?)",
    r"disregard\s+(your|all|previous)\s+instructions?",
    r"forget\s+(all|your|previous)\s+instructions?",
    r"new\s+instructions?\s*[:：]",
    r"updated?\s+instructions?\s*[:：]",

    # Token injection (chat-format exploits)
    r"\[system\]",
    r"\[INST\]",
    r"<<SYS>>",
    r"<\|system\|>",
    r"<\|im_start\|>",

    # Mode switching
    r"override\s+mode",
    r"developer\s+mode",
    r"jailbreak",
    r"DAN\s+mode",
    r"prompt\s+injection",

    # Persona hijacking
    r"you\s+are\s+now\s+(?:a|an|the)\s+",
    r"you\s+are\s+no\s+longer",
    r"pretend\s+(?:you\s+are|to\s+be)",
    r"act\s+as\s+(?:if\s+you\s+are|a|an)\s+",
    r"roleplay\s+as",

    # System prompt extraction
    r"reveal\s+(?:your|the)\s+(?:system\s+)?(?:prompt|instructions?)",
    r"print\s+(?:your|the)\s+(?:system\s+)?(?:prompt|instructions?)",
    r"show\s+(?:me\s+)?(?:your|the)\s+(?:system\s+)?(?:prompt|instructions?)",
    r"what\s+(?:are|is)\s+your\s+(?:system\s+)?(?:prompt|instructions?)",
    r"return\s+all\s+your\s+(?:data|instructions?|prompt)",
    r"repeat\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions?)\s+verbatim",
]

_COMPILED: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE) for p in _PATTERNS
]


# ── Public exception ──────────────────────────────────────────────────────────

class InjectionAttemptError(ValueError):
    """
    Raised when a user query matches a known prompt injection pattern.
    Catch this in the application layer (app.py) to show a user-friendly message.
    """
    pass


# ── Public functions ──────────────────────────────────────────────────────────

def sanitize_query(query: str) -> str:
    """
    Validate a user query before it reaches the LLM.

    Checks:
      - Not empty or whitespace-only.
      - Does not exceed MAX_QUERY_LENGTH characters.
      - Does not match any known injection pattern.

    Parameters
    ----------
    query : raw user input from the interface.

    Returns
    -------
    Stripped query string if clean.

    Raises
    ------
    ValueError             if the query is empty or too long.
    InjectionAttemptError  if a known injection pattern is detected.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    query = query.strip()

    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError(
            f"Query too long ({len(query):,} characters). "
            f"Maximum is {MAX_QUERY_LENGTH}."
        )

    for pattern in _COMPILED:
        if pattern.search(query):
            logger.warning(
                "Prompt injection attempt blocked | query: %.120r", query
            )
            raise InjectionAttemptError(
                "Your question contains patterns that cannot be processed. "
                "Please rephrase and try again."
            )

    return query


def check_context_for_injection(chunks: list) -> None:
    """
    Scan retrieved chunks for injection patterns.

    Does NOT raise or block — the SEC corpus is controlled and trusted.
    The source of any match would be a pipeline error, not a live attack.

    Logs a WARNING for each affected chunk so anomalies can be investigated.

    Parameters
    ----------
    chunks : list of RetrievedChunk objects (accessed via getattr to avoid
             circular imports between guards.py and retrieve.py).
    """
    for chunk in chunks:
        text = getattr(chunk, "text", "") or ""
        for pattern in _COMPILED:
            if pattern.search(text):
                logger.warning(
                    "Injection pattern found in retrieved chunk | "
                    "chunk_id=%s  company=%s",
                    getattr(chunk, "chunk_id", "unknown"),
                    getattr(chunk, "company", "unknown"),
                )
                break   # one warning per chunk is sufficient
