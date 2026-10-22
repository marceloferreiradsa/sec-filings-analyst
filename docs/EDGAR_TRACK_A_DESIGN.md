# Track A — XBRL Financial Data: Design Specification

**Status:** Pre-implementation design document  
**Sources:** SEC EDGAR API documentation (sec.gov/search-filings/edgar-application-programming-interfaces), FASB taxonomy browser (xbrl.fasb.org), empirical diagnostic output from five target companies, empirical period-fragmentation analysis

---

## 1. Data Source: What Is This Data and Can It Be Trusted?

The SEC's EDGAR system exposes all XBRL-tagged financial data through a free, unauthenticated REST API at `data.sec.gov`. Every value returned by this API was submitted by the filing company as part of a legally required disclosure to the US Securities and Exchange Commission.

**Why the values themselves are trustworthy:**
- Companies submit XBRL tags under the same legal obligation as the filing text. Knowingly false XBRL values carry the same SEC enforcement risk as false financial statements.
- Each fact entry includes an `accn` (accession number) field that uniquely identifies the specific SEC filing the value came from. Any value can be traced back to its source document.
- The FASB taxonomy defines what each concept tag must represent. `Revenues` means total net revenue. `GrossProfit` means revenue minus cost of goods sold. These definitions are publicly available at xbrl.fasb.org.

**Known honest limitations:**
- XBRL tagging quality varies by company and by year. Older filings (pre-2014) may have tagging errors or inconsistencies.
- Not all metrics are tagged by all companies. Google and Meta do not tag `GrossProfit` as a standalone item — they present cost information at the segment level instead. Our system will show `N/A` for those fields, which is the correct and honest answer.
- The taxonomy has evolved over time. The ASC 606 transition is handled explicitly in Section 4.

---

## 2. API Structure: The `companyfacts` JSON

**Endpoint:** `GET https://data.sec.gov/api/xbrl/companyfacts/CIK{10-digit-CIK}.json`

**Top-level structure:**
```
{
  "cik": 789019,
  "entityName": "MICROSOFT CORP",
  "facts": {
    "us-gaap": {
      "{ConceptName}": {
        "label": "Human-readable label",
        "description": "FASB definition",
        "units": {
          "USD": [ ...array of fact entries... ]
        }
      }
    }
  }
}
```

**Each fact entry — complete field definitions:**

| Field  | Type     | Official? | Definition |
|--------|----------|-----------|------------|
| `accn` | string   | ✅ SEC    | Accession number of the filing this value appeared in. Unique per filing. |
| `end`  | ISO date | ✅ SEC    | Period end date. Present on all entries. |
| `start`| ISO date | ✅ SEC    | Period start date. **Absent for instantaneous (balance-sheet) facts.** |
| `val`  | number   | ✅ SEC    | The reported value in the unit specified (USD for financial values). |
| `filed`| ISO date | ✅ SEC    | Date the filing was accepted by EDGAR. |
| `form` | string   | ✅ SEC    | Form type: `10-K`, `10-Q`, `10-K/A`, `10-Q/A`, etc. |
| `fy`   | integer  | ✅ SEC    | The fiscal year of the **filing** that reported this value — NOT the fiscal year the period belongs to. See Section 3. |
| `fp`   | string   | ✅ SEC    | Fiscal period label as recorded in the filing: `FY`, `Q1`, `Q2`, `Q3`, `Q4`. Subject to the same filing-context issue as `fy`. |
| `frame`| string   | ✅ SEC    | Present when the SEC matched this entry to a canonical calendar period: `CY####` (annual), `CY####Q#` (quarterly), `CY####Q#I` (instantaneous). Absent for year-to-date, multi-quarter, or unmatched entries. |

---

## 3. Critical Data Behavior: The Comparative Reporting Effect

This is the most important behavioral characteristic of the companyfacts API, and the root cause of the "3 documents instead of 4" problem confirmed by empirical investigation.

**What happens:** Every 10-K filing contains multiple years of financial data:
- Income statements: current year + 2 prior years (3 years total)
- Balance sheets: current year-end + 1 prior year-end (2 periods total)

EDGAR captures all of these. When a company files its FY2026 10-K, it creates XBRL entries for FY2026, FY2025, and FY2024 income statement data — all three carrying `fy=2026` because that is the year of the filing.

**Empirical evidence from NVIDIA (NVDA):**

| period_end   | fy (from entry) | what it actually is |
|--------------|-----------------|---------------------|
| 2026-01-25   | 2026            | FY2026 current year → fy correct |
| 2025-01-26   | 2026            | FY2025 as 1-year-prior in FY2026 10-K → fy wrong |
| 2024-01-28   | 2026            | FY2024 as 2-year-prior in FY2026 10-K → fy wrong |
| 2024-01-28   | 2025            | FY2024 balance sheet in FY2025 10-K → fy wrong |

For the same period-end date (2024-01-28), the income statement entry has `fy=2026` and the balance sheet entry has `fy=2025`. They were last filed in different 10-Ks, so our "prefer most recently filed" dedup gives them different fy values.

**Consequence for period bucketing:** Any bucket key that includes `fy` or `fp` will fragment the same economic period into multiple buckets — one per unique (fy, fp) combination — because different metrics' entries were last filed in different 10-Ks. This is not a code bug; it is an inherent property of how the XBRL data is structured.

**Rule derived from this:** The `fy` and `fp` fields from XBRL entries must NOT be used for period identification or metadata. They are filing-context labels, not period identity labels. Fiscal year and period must be derived from `period_end` independently.

---

## 4. The Tag Transition Problem (ASC 606)

FASB introduced ASC 606 (Revenue from Contracts with Customers) effective for fiscal years beginning after December 15, 2017. This changed the canonical XBRL tag for revenue:

| Period       | Tag used |
|--------------|----------|
| Pre-ASC 606  | `Revenues` or `SalesRevenueNet` |
| Post-ASC 606 | `RevenueFromContractWithCustomerExcludingAssessedTax` |

**Verified breakdown for our five companies:**

| Ticker | Revenue tag (modern) | Coverage gap |
|--------|----------------------|--------------|
| NVDA   | `Revenues` (through FY2026) | None — never switched |
| GOOGL  | `Revenues` for FY2025; `RevenueFromContract...` for FY2018–FY2024 | FY2022 revenue is in second tag only |
| MSFT   | `RevenueFromContract...` (FY2018–FY2025) | `Revenues` has entries only through FY2010 |
| META   | `RevenueFromContract...` (FY2018–FY2025) | `Revenues` has entries only through FY2017 |
| AAPL   | `RevenueFromContract...` (FY2019–FY2025) | `Revenues` ends FY2018, `SalesRevenueNet` ends FY2017 |

**Solution — combine strategy for tag-transition metrics:**
For `revenue` and `net_income`, pool entries from all candidate concepts before deduplication. The dedup then selects one entry per period regardless of tag source. This is safe because the candidates for these metrics are tag renames of the same economic concept.

**For all other metrics — first-match wins:**
For `cash`, `long_term_debt`, and others, candidates have different definitional scopes. First-match-wins keeps the definition consistent.

---

## 5. The Duplication Problem and Deduplication Strategy

The API returns every fact from every filing. The same period's value appears multiple times — once per filing that referenced it. Our deduplication selects one entry per `period_end`:

1. If any entry for a given `end` date has a valid `frame` (SEC's own canonical marker), prefer it.
2. When no frame is present, prefer the most recently `filed` entry.

This mirrors the SEC's own stated intent for the frame field: "the last filed that most closely fits the calendrical period."

**Valid frame patterns:**
- `CY####` — annual (365d ±30)
- `CY####Q#` — quarterly (91d ±30)
- `CY####Q#I` — instantaneous (balance-sheet point-in-time)

Frame is absent for year-to-date entries and for some older or amended filings. The fallback (most recently filed) handles those.

---

## 6. The YTD Problem for 10-Q Data

Some companies tag 10-Q income statement values as year-to-date (fiscal year start to period end), while others tag the standalone quarter.

**Confirmed examples:**
- NVIDIA: 10-Q revenue sample has span of 90 days (standalone Q1). Frame = `CY2026Q1`.
- MSFT: 10-Q revenue sample has span of 273 days (9-month YTD). Frame = absent.

The `frame` field naturally encodes this: only standalone quarterly entries receive a `CY####Q#` frame. YTD entries do not.

**Product decision:** Include 10-Q financial summaries. When a company only tags YTD values, include them with explicit labeling. The summary text will include the `start` date so the LLM and user can see "Range: 2025-07-01 to 2026-03-31" and understand it covers 9 months.

For companies where no `CY####Q#` frame entries exist for revenue (i.e., they only tag YTD), the summary includes:
```
Note: Revenue and income values cover a year-to-date period, not the standalone quarter.
This reflects how this company tags its 10-Q XBRL data. Margin ratios remain valid.
```

---

## 7. Period Bucketing

**Keying:** One bucket per `period_end` date. No compound key.

This is the direct consequence of Section 3: since `fy` and `fp` from entries reflect filing context rather than period identity, they cannot be part of the key. Two entries for the same economic period can have different `fy` values depending on which 10-K last reported them. A compound key would fragment the same period into multiple buckets.

**Deriving fiscal year and fiscal period from `period_end`:**

These fields must be derived independently, not read from XBRL entries.

```
fiscal_year   = int(period_end[:4])          # year component of the end date
fiscal_period = "FY"   if form_type == "10-K"
              = infer from period_end month   if form_type == "10-Q"
```

Quarter inference from month (approximate — works for calendar-year companies; acknowledged as imprecise for Apple, NVIDIA):
```
month 1–3  → Q1
month 4–6  → Q2
month 7–9  → Q3
month 10–12 → Q4
```

This derivation is already used in `document_builder.py`'s `_infer_fiscal_period` function and is appropriate here for consistency.

---

## 8. Form Variant Acceptance

MSFT and AAPL have `10-K/A` and `10-Q/A` (amended) entries. Amended filings correct errors in originals. We accept them — the "prefer most recently filed" dedup ensures the amendment supersedes the original automatically.

```python
form_variants = {form_type, f"{form_type}/A"}
```

---

## 9. Output Document Format

```
{company_name} ({ticker}) — {form_type} Financial Summary
Period: {period_label} | Range: {start} to {end} | Filed: {filed_date}
[Note: Revenue and income values cover a year-to-date period, not the standalone quarter.
This reflects how this company tags its 10-Q XBRL data. Margin ratios remain valid.]

Revenue:             $X.XXB
Gross Profit:        $X.XXB  (Gross Margin: XX.X%)
Operating Income:    $X.XXB  (Operating Margin: XX.X%)
Net Income:          $X.XXB  (Net Margin: XX.X%)
R&D Expense:         $X.XXB  (R&D as % Revenue: XX.X%)
Capital Expenditure: $X.XXB
Cash & Equivalents:  $X.XXB
Long-term Debt:      $X.XXB
```

The YTD note appears only when the revenue entry span exceeds 120 days on a 10-Q document.
Period label: `FY{year}` for 10-K; `FY{year} Q{n}` for 10-Q.

**Metadata schema:**
```
company, company_name, filing_type, section="financial_data",
section_name="Financial Summary", source_type="financial_data",
fiscal_year    ← derived from period_end[:4]
fiscal_period  ← "FY" or inferred from month
period_end, filed_date
```

---

## 10. Expected Output After Fix

| Company | 10-K docs | 10-Q docs | Notes |
|---------|-----------|-----------|-------|
| NVDA    | 4         | 4         | All from `Revenues` tag |
| MSFT    | 4         | 4         | Combine strategy; 10-Q may carry YTD note |
| GOOGL   | 4         | 4         | FY2022 gap filled by combine; no GrossProfit |
| META    | 4         | 4         | Combine strategy; no GrossProfit |
| AAPL    | 4         | 4         | Combine strategy for revenue |

Target is exactly 4 per company per form type. If a company genuinely has fewer than 4 years of XBRL-tagged data meeting our criteria, fewer summaries are built — but that is an accurate reflection of available data, not a code deficiency.

---

## 11. Scope Exclusions (Documented)

- **Segment-level data** (NVDA DataCenter, AAPL Services): company-specific extension namespaces. Extension point for v2.
- **YoY growth calculations**: derivable by the LLM at query time from adjacent documents.
- **International filers (IFRS)**: all five companies are US-GAAP filers.
- **Non-GAAP adjustments**: all values are as-reported GAAP.
