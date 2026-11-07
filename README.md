# Bambinos.live: Renewal → Class Scheduling Automation

**AI Program Manager (Operations) take-home case** · prepared by Hardik Choudhary · snapshot 2026-11-03 18:00 IST

A reconciliation and auto-approval engine for the four-table renewal pipeline
(`invoices → faculty_form_unapproved → booking_requests → class_schedule_bookings`), built three ways
(Google Sheet formulas, Python, n8n) so Ops can run it without code and the builds cross-check each other.

> Start with **[Case_Report.pdf](Case_Report.pdf)** (Deliverables A, B, D). The prototype (Deliverable C) is in
> `workflows_or_scripts/` and `results/`.

## What the data says (13 invoices)

| Finding | Number |
|---|---|
| Paid renewals that reached scheduled classes | **1 of 11** |
| Paid but not scheduled | **10 invoices, ₹121,600** |
| Stuck more than 12 h | 6 invoices, ₹68,100; oldest 51.7 h (invoice 84902) |
| Approved forms that actually got classes | 1 of 4 |
| Forms pending Ops approval | 8 of 12 (oldest 32.5 h) |
| Teacher delay when a form is filed | median 25 min, max 50 min |

**What the engine does with the 12 outstanding renewals:**
5 zero-touch (42%) · 3 one-tap parent confirmations · 4 need human judgement
(a discount, a batch change, a partial payment and a failed payment). Every invoice gets exactly one outcome.

| Outcome | Invoices |
|---|---|
| AUTO_APPROVE (clean) | 84903 |
| AUTO_FIX (safe defect repaired) | 84902 stuck allocation · 84905 false "batch full" · 84908 duplicate form · 84913 invoice-ID typo + look-alike characters |
| SOFT (one-tap parent confirm) | 84904 payer mismatch · 84906 and 84910 paid, no form |
| HUMAN | 84907 discount needs approval · 84912 batch change, no matching batch |
| BLOCK | 84909 partial payment · 84911 payment failed |
| ALREADY_SCHEDULED | 84901 (only 2 of 24 sessions exist in table 4; flagged for Ops) |

## Deliverable map

| Deliverable | Where |
|---|---|
| **A** Root-cause audit, metrics, SLAs | `Case_Report.pdf` §2 · `results/decisions_all.csv` (evidence for every invoice) |
| **B** Re-engineered zero-touch workflow | `Case_Report.pdf` §3 · `workflows_or_scripts/n8n_renewal_workflow.json` |
| **C** Working prototype | `workflows_or_scripts/` + `results/` + `prompts/` (see below) |
| **D** Dashboard, SOP, 30-60-90 | `Case_Report.pdf` §5 · `dashboard/ops_head_dashboard_mockup.png` · Sheet `Dashboard` tab · `dashboard_queries.sql` |

## The prototype: three outputs required by the brief

| Required output | File |
|---|---|
| (1) Auto-approved entries ready for `class_schedule_bookings` | `results/auto_approved.csv` + `results/proposed_class_schedule_bookings.csv` (120 proposed session rows) |
| (2) Flagged exceptions with exact reason codes | `results/exceptions.csv` (severity, owner, evidence values, next action) |
| (3) Drafted WhatsApp / Slack messages | `results/messages.md` and `results/messages.json` (21 messages; parents also get a Hinglish version) |

Also: `results/decisions_all.csv` (all 13 invoices), `results/summary.md`, `results/dashboard_metrics.json`.

## How to run

### Option 1: No code (Google Sheets), recommended for Ops
1. Upload `workflows_or_scripts/Renewal_Reconciliation_Sheet.xlsx` to Google Drive → *Open with Google Sheets*.
2. Tabs: `Dashboard` (Ops Head view), `Checks` (the rule engine, one row per invoice), `Exceptions`, `AutoApproved`,
   `Messages`, `Assumptions` (change the snapshot time here), and the 5 data tabs.
3. To use new data, replace the rows in the 5 data tabs (keep headers); lookups run to row 100.
All 752 formulas are plain COUNTIF / INDEX / MATCH / SUMPRODUCT / TEXTJOIN; no macros.

### Option 2: Python (reference engine, needs only pandas)
```bash
pip install pandas
python workflows_or_scripts/reconcile.py                       # reads data/, writes results/
python workflows_or_scripts/reconcile.py --asof "2026-11-03 18:00"
```

### Option 3: n8n (live automation template)
Import `workflows_or_scripts/n8n_renewal_workflow.json`. Two triggers (payment webhook; 15-minute sweep) feed one
Code node (`n8n_rules_engine.js`, the same rules) → route by outcome → create booking + WhatsApp confirmation, or LLM-draft
the message for the owner (prompts in `prompts/`). Replace every `REPLACE_*` value and connect credentials. The workflow
expects a small read-only "context API" (`/context?invoice_id=` and `/sweep`) that returns, per invoice:
`{invoice, forms[], booking, schedule_count, reference, batches[]}`. A Google Apps Script web app over the Sheet works.
**Run it in shadow mode first (log only).**

### SQL for Metabase
`workflows_or_scripts/dashboard_queries.sql` holds 9 MySQL queries (orphans, stuck >12 h, form ageing, duplicates,
mismatches, booking dead-ends, turnaround, ID typos, KPI strip).

## How it was verified
- The Sheet formulas, the Python engine and the n8n JavaScript give **identical outcomes and reason codes on all 13 invoices**
  (`workflows_or_scripts/test_n8n_rules.py` runs the JS in Node and compares).
- A mutation test (changing one form amount in the Sheet) flipped invoice 84903 from AUTO_APPROVE to HUMAN / AMOUNT_MISMATCH.
- The SQL was run on the same CSVs through SQLite (date functions translated) and reproduces the same counts.

## Rules in order (all builds)
payment status → orphan (paid, no form) → duplicate forms → invoice-ID typo (unique match on user + student + amount) →
amount mismatch → ID consistency → discount → payer vs registered parent (with look-alike-character normalisation) →
stuck booking states (capacity check **excludes the student's own seat**) → batch-change availability (match on
category + educator + days + time, never days/time alone) → sessions scheduled.

## Assumptions (full table in the report, §6)
- Snapshot time 2026-11-03 18:00; "stuck" = more than 12 h after payment.
- All purchased sessions (24) are proposed for auto-approved renewals; invoice 84901 shows only 2 of 24, so this is flagged to confirm.
- Any discount needs approval until a real policy is provided.
- Savings figures (300 renewals/week, 6 min each, ₹250/h) are **illustrative placeholders**; replace with real numbers.
- Times are used as stored; time zones for GCC/US tracks are not modelled. Names/phones are masked in the source data.

## Limits (honest)
- The sample has 13 invoices: percentages show what the design does on this data, not production rates.
- The n8n workflow, WhatsApp, Slack and LLM calls are a template; they were **not** run against live services.
- Messages in `results/` are template-based for reproducibility; the LLM prompt in `prompts/message_drafter.md` writes them in production. Hinglish text should get a native-speaker review.
- Loom video: not recorded; see `docs/loom_walkthrough_script.md` for a 2–3 minute talk track. Link: _(add here)_

## Repository structure
```
├── README.md
├── Case_Report.pdf
├── data/                         the 5 input CSVs (unchanged)
├── prompts/                      remark_parser.md · exception_triage.md · message_drafter.md
├── workflows_or_scripts/
│   ├── reconcile.py              reference engine (pandas)
│   ├── Renewal_Reconciliation_Sheet.xlsx   no-code build (Google Sheets)
│   ├── n8n_renewal_workflow.json · n8n_rules_engine.js
│   ├── dashboard_queries.sql
│   └── build_sheet.py · build_n8n.py · build_report.py · make_figures.py · test_n8n_rules.py   (generators / tests)
├── results/                      auto_approved · exceptions · messages · decisions_all · summary · metrics
├── dashboard/                    ops_head_dashboard_mockup.png
└── docs/                         assignment checklist · Loom talk track · figures/
```
