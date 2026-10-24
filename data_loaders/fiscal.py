"""
fiscal.py — fiscal year and quarter of a period, per company (ADR-19).

A fiscal year is named after the calendar year in which it ends; quarters are
counted from the month after the company's fiscal year-end. Derived from
period_end, never from the XBRL fy/fp fields (ADR-05).

  Company   FY ends     10-Q period_end 2025-12-27 → FY2026 Q1 (Apple)
  AAPL      September   10-Q period_end 2025-09-30 → FY2026 Q1 (Microsoft)
  MSFT      June        10-Q period_end 2025-10-26 → FY2026 Q3 (NVIDIA)
  NVDA      January     10-K period_end 2026-01-25 → FY2026    (NVIDIA)
  GOOGL     December
  META      December

52/53-week years end on a weekday near the month end (Apple: last Saturday of
September; NVIDIA: last Sunday of January), so the month is enough. A company
not listed here raises — add it rather than guess its calendar.
"""

FISCAL_YEAR_END_MONTH: dict[str, int] = {
    "AAPL":  9,
    "MSFT":  6,
    "NVDA":  1,
    "GOOGL": 12,
    "META":  12,
}


def fiscal_year_period(company: str, period_end: str, form_type: str) -> tuple[int, str]:
    """Return (fiscal_year, fiscal_period) — fiscal_period is "FY" or "Q1".."Q3"."""
    if company not in FISCAL_YEAR_END_MONTH:
        raise ValueError(f"No fiscal calendar for {company}; add it to FISCAL_YEAR_END_MONTH")
    fye   = FISCAL_YEAR_END_MONTH[company]
    year  = int(period_end[:4])
    month = int(period_end[5:7])

    fiscal_year = year if month <= fye else year + 1
    if form_type == "10-K":
        return fiscal_year, "FY"

    quarter = round(((month - fye) % 12) / 3)
    if quarter not in (1, 2, 3):
        raise ValueError(f"{company} 10-Q ending {period_end} does not fall in Q1–Q3")
    return fiscal_year, f"Q{quarter}"


MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")


def period_label(company: str, period_end: str, form_type: str) -> str:
    """Fiscal label plus the calendar end date in words, as written in the filing.

    "FY2026 Q2 (quarter ended December 31, 2025)" · "FY2025 (fiscal year ended
    September 27, 2025)". The date in words lets a question phrased by calendar
    date match the summary text, not only its fiscal label (ADR-19, ADR-03).
    """
    fiscal_year, fiscal_period = fiscal_year_period(company, period_end, form_type)
    ended = f"{MONTHS[int(period_end[5:7]) - 1]} {int(period_end[8:10])}, {period_end[:4]}"
    if fiscal_period == "FY":
        return f"FY{fiscal_year} (fiscal year ended {ended})"
    return f"FY{fiscal_year} {fiscal_period} (quarter ended {ended})"
