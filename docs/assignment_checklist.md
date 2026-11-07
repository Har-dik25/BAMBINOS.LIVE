# Bambinos.live — AI Program Manager (Operations)
## Take-Home Case: Complete Execution Guide

**Student Renewal → Class Scheduling Pipeline**

| | |
|---|---|
| **Stage** | 2 (Operations) · Timebox 48–72 hours · No coding required |
| **Next stage** | Live case review with the Head of Operations (Bengaluru, in-office) |
| **Official repo** | https://github.com/bambinoslive/AI-PM-hiring-take-home-assignments |
| **Submit** | https://forms.gle/gu5gzySRHTSd5Uou9 |

**How to use this document:** Read Sections 1–3 first (5 minutes). Then work through Section 4 as your master checklist. Sections 5–10 hold the content for each deliverable. Appendices contain copy-paste prompts and message templates.

---

## Table of Contents

1. [The mission in one page](#1-the-mission-in-one-page)
2. [Where the points are (rubric map)](#2-where-the-points-are-rubric-map)
3. [Priorities and effort](#3-priorities-and-effort)
4. [Master checklist with Definition of Done](#4-master-checklist-with-definition-of-done)
5. [Deliverable A — Problem audit and baseline numbers](#5-deliverable-a--problem-audit-and-baseline-numbers)
6. [Deliverable A — Metrics and SLAs](#6-deliverable-a--metrics-and-slas)
7. [Deliverable B — Re-engineered workflow](#7-deliverable-b--re-engineered-workflow)
8. [Deliverable C — Prototype specification](#8-deliverable-c--prototype-specification)
9. [Deliverable D — Dashboard, SOP, rollout, 30-60-90](#9-deliverable-d--dashboard-sop-rollout-30-60-90)
10. [Report (PDF) outline](#10-report-pdf-outline)
11. [Live review preparation](#11-live-review-preparation)
12. [72-hour schedule](#12-72-hour-schedule)
13. [Mistakes to avoid](#13-mistakes-to-avoid)
14. [Final pre-submit checklist](#14-final-pre-submit-checklist)
15. [Appendix A — LLM prompt templates](#appendix-a--llm-prompt-templates)
16. [Appendix B — Message templates with real data](#appendix-b--message-templates-with-real-data)
17. [Appendix C — Assumptions register](#appendix-c--assumptions-register)

---

## 1. The mission in one page

**Today's flow (4 tables, 3 manual handoffs):**

```
 PARENT              TEACHER                 OPS TEAM                 PARENT / OPS
   │                    │                       │                          │
   ▼                    ▼                       ▼                          ▼
invoices ───────► faculty_form_unapproved ──► booking_requests ──► class_schedule_bookings
 (pays link)      (re-types invoice data)    (manual verify+approve)   (picks batch/days/time)
```

**Your job in four moves:**

| Move | Deliverable | One-line goal |
|------|-------------|---------------|
| 1. Find the leaks | **A** | Show exactly where paid students get stuck, with evidence from the CSVs |
| 2. Question the process | **B** | Eliminate steps that re-type data the system already has; fast-track clean renewals |
| 3. Prove it works | **C** | A working reconciliation engine on the 5 CSVs: auto-approve, flag with reason codes, draft messages |
| 4. Make it real | **D** | Morning dashboard, SOPs, and a rollout that never breaks live classes |

**What you hand in:**

| # | Item | Status |
|---|------|--------|
| 1 | Case Report / Deck (PDF): covers A, B, D | **COMPULSORY** |
| 2 | GitHub repo: prompts, README, datasets, results, scripts/workflows | **COMPULSORY** |
| 3 | Loom video, 2–3 min: prototype walkthrough | Optional (recommended) |
| 4 | Google Form with the PDF and repo links | **COMPULSORY** |

> Use **only** the `ops/` folder of the zip. Ignore `marketing/` and `sales/`.

---

## 2. Where the points are (rubric map)

Each dimension is 25%. Make each one visibly easy for the reviewer to tick.

| Dimension | What they look for | What to show | Proof artifact |
|-----------|--------------------|--------------|----------------|
| **1. Problem discovery & edge cases** | Real failure modes across all 4 tables | The 13-invoice audit table (Section 5.2) with evidence values | Report §A, `results/exceptions.csv` |
| **2. Process re-engineering** | Questioning why steps exist; fast-track for clean renewals | First-principles table (Section 7.1) + happy-path design | Report §B workflow diagram |
| **3. AI & no-code execution** | Prototype that reconciles messy data, flags accurately, drafts alerts | Script/flow + 3 output files + prompts | Repo `results/`, `prompts/`, Loom |
| **4. Data, SLAs & ownership** | Clear SLAs, dashboard, realistic savings, rollout SOPs | Metric definitions, SLA table, dashboard, 30-60-90, savings math with stated assumptions | Report §D |

**Score boosters:** an evidence-backed audit (numbers, not generic complaints); a design that removes steps instead of automating them; every flag carrying its evidence and a named owner; savings math that shows its assumptions.

---

## 3. Priorities and effort

`[MUST]` = needed to score. `[SHOULD]` = clearly raises the score. `[BONUS]` = polish if time remains.

| Task | Priority | Effort |
|------|----------|--------|
| Rule engine producing `auto_approved.csv` and `exceptions.csv` | MUST | 5–7 h |
| Drafted messages for every exception | MUST | 2–3 h |
| Failure-mode audit using the real data | MUST | 3–4 h |
| Metrics and SLA definitions | MUST | 2 h |
| Redesigned workflow diagram + exception routing | MUST | 3–4 h |
| Dashboard design | MUST | 2–3 h |
| 30-60-90 plan + change management | MUST | 2–3 h |
| Report PDF assembly | MUST | 4–5 h |
| Repo README + structure | MUST | 1–2 h |
| SOPs (Ops + teacher) | SHOULD | 2 h |
| LLM prompt for parsing teacher remarks | SHOULD | 1–2 h |
| Savings estimate with assumptions | SHOULD | 1 h |
| Loom video | SHOULD | 1 h |
| Working dashboard in Sheets/Metabase | BONUS | 3–4 h |
| n8n/Make workflow export | BONUS | 3–4 h |

Total for MUST + SHOULD: about 30–38 hours, which fits inside the 72-hour window.

---

## 4. Master checklist with Definition of Done

### Deliverable A — Problem audit and leakage
- [ ] Current-state map: 4 tables, owner and handoff at each step
- [ ] Failure modes listed per handoff (human, data, process, visibility)
- [ ] All 13 invoices classified with evidence (Section 5.2)
- [ ] Baseline numbers computed (Section 5.1)
- [ ] Metrics and SLAs defined (Section 6)

**Done when:** a reviewer can point at any claim and see the invoice ID and the values behind it.

### Deliverable B — Re-engineered workflow
- [ ] First-principles review of each step: eliminate / automate / keep
- [ ] Happy-path fast track defined with explicit eligibility rules
- [ ] Exception triage: code → owner → action → SLA
- [ ] Before/after diagram
- [ ] Tools named (n8n/Make, webhooks, Sheets/Metabase, WhatsApp API, LLM)

**Done when:** a clean same-batch renewal goes from payment to scheduled classes with no human step, and every exception has exactly one owner.

### Deliverable C — Prototype
- [ ] Ingests all 5 CSVs
- [ ] Output 1: `auto_approved.csv`
- [ ] Output 2: `exceptions.csv` with reason codes and evidence
- [ ] Output 3: drafted WhatsApp/Slack messages
- [ ] Prompts saved in `prompts/`; scripts/flows in `workflows_or_scripts/`
- [ ] README explains how to run it and lists assumptions

**Done when:** all 13 invoices end with exactly one outcome, re-running gives identical results, and you can explain every rule.

### Deliverable D — Dashboard, SOP, rollout
- [ ] Ops Head morning dashboard (stuck invoices >12h, unapproved forms, unscheduled bookings, hours saved)
- [ ] Ops SOP and teacher SOP
- [ ] Change-management plan for 200+ teachers and a 10-person Ops team
- [ ] 30-60-90 day plan
- [ ] Time and cost savings with stated assumptions

**Done when:** a Head of Ops could start the rollout Monday morning using only your document.

### Submission
- [ ] PDF exported and readable on a phone
- [ ] Repo public/shared; links tested in an incognito window
- [ ] Loom recorded and linked in the README (optional)
- [ ] Google Form submitted
- [ ] Live review rehearsed (Section 11)

---

## 5. Deliverable A — Problem audit and baseline numbers

### 5.1 Baseline from the sample data

> Snapshot time used below: **2026-11-03 18:00** (just after the latest record in the data at 17:15). State your own snapshot time in the README so "stuck >12h" is reproducible.

| Finding | Number |
|---------|--------|
| Invoices in the sample | 13 (11 Paid, 1 Partially_Paid, 1 Failed) |
| Fully paid renewals that reached scheduled classes | **1 of 11 (9%)** |
| Paid but not scheduled | 10 invoices, **₹1,21,600** |
| Paid but not scheduled for more than 12 hours | 6 invoices, **₹68,100** |
| Oldest stuck paid invoice | 84902, about **52 hours**, and it was already approved by Ops |
| Paid invoices with no teacher form | 3 (84906, 84910, and 84913 via a typo) |
| Forms pending Ops approval | 8 of 12 (oldest about 32 hours) |
| Approved forms that actually got classes | **1 of 4** (the other 3: stuck allocation, "batch full", awaiting parent) |
| The one success: payment to scheduled | 1 h 45 min (teacher filed in 30 min, Ops approved in 45 min) |
| Teacher delay when they do file | Median 25 min, max 50 min |

**Three insights worth stating in the report:**

1. **Ops approval is not the finish line.** Three of the four approved forms still have no classes. The pipeline has dead-end states with no retry, no alert, and no owner.
2. **Teachers are fast when they file; the leak is missing and wrong forms,** plus an Ops queue that builds up. Do not frame this as "lazy teachers". Frame it as a re-typing step that creates errors.
3. **Weekends matter.** Invoice 84902 was paid on Sunday 1 Nov, and batch 9202 meets Mon/Wed. It still has no scheduled sessions.

### 5.2 Invoice-by-invoice audit (also your answer key for the prototype)

| Invoice | Evidence in the data | Reason code | Expected outcome | Owner |
|---------|---------------------|-------------|------------------|-------|
| **84901** | Fully completed. Only 2 of 24 purchased sessions exist in table 4 | `SESSIONS_UNDER_SCHEDULED` (verify) | Already done; state your assumption (rolling vs under-scheduling) | Ops (info) |
| **84902** | Form approved; booking_request 5502 stuck at `Pending_Batch_Allocation`; batch 9202 has 5/6 seats | `STUCK_AT_ALLOCATION` | **Auto-fix**, then schedule | Automation |
| **84903** | Clean same-batch renewal; amount matches ₹9,000; IDs match; batch 3/6; form pending 32 h | None | **Auto-approve** | Automation |
| **84904** | Invoice mobile `+91-9844XXXX77`, email and parent name differ from the registered parent (`+91-9844XXXX04`). Teacher remark: "Mother paid from her number". user_id/student_id match | `PAYER_MISMATCH` | **Soft**: one-tap parent confirmation on the registered number, then approve | Parent + Ops |
| **84905** | booking 5505 `Failed_Batch_Full` (6/6), but the student already holds a seat in batch 9205 | `FALSE_BATCH_FULL` | **Auto-fix**: re-run capacity excluding the student's own seat | Automation |
| **84906** | Paid via Stripe (Dubai), ₹18,000, **no form** | `ORPHAN_NO_FORM` | **Soft**: auto-draft from invoice + reference, ask parent to confirm; notify teacher. Check currency/FX | Parent + Teacher |
| **84907** | Discount ₹1,900 (20%): ₹9,500 → ₹7,600. Remark: "retention scholarship" | `DISCOUNT_NEEDS_APPROVAL` | **Human review** (or auto-approve if a pre-approved discount policy exists) | Ops lead |
| **84908** | Forms 3308 and 3309 for the same invoice ("browser froze") | `DUPLICATE_FORM` | **Auto-fix**: keep the first, mark the second duplicate; then clean approval | Automation |
| **84909** | `Partially_Paid`, installment 1 of 2: ₹5,250 paid of ₹10,500. Form says ₹10,500 and 24 sessions | `PARTIAL_PAYMENT` + `AMOUNT_MISMATCH` | **Block**: do not schedule the full term; follow up installment 2 | Ops / Finance |
| **84910** | Paid ₹11,000, **no form** | `ORPHAN_NO_FORM` | **Soft** (same as 84906) | Parent + Teacher |
| **84911** | `Failed`, no gateway payment ID. Teacher forwarded a "UPI processing" screenshot | `PAYMENT_NOT_CONFIRMED` | **Block**: never approve on a screenshot; send retry link; wait for the gateway webhook | Parent, then Ops |
| **84912** | Parent wants a weekend 11 AM batch. Form approved; booking 5512 `Awaiting_Parent_Batch_Selection`, no batch assigned. No Gita batch at that slot exists | `BATCH_CHANGE_PENDING` + `NO_MATCHING_BATCH` | **Human review**: offer alternatives, waitlist, or new batch; nudge the parent at 24 h / 48 h | Parent + Ops |
| **84913** | Form points to invoice **84931** (digits swapped). The invoice parent name contains Cyrillic letters ("Ме") | `INVOICE_ID_TYPO` + `HOMOGLYPH_MISMATCH` | **Auto-fix**: unique match on user_id + student_id + amount; normalise the characters | Automation |

**Expected split of the 12 not-yet-complete renewals (validate when you build):**

| Bucket | Invoices | Count |
|--------|----------|-------|
| Zero-touch (auto-approve or auto-fix) | 84902, 84903, 84905, 84908, 84913 | 5 (about 42%) |
| Soft (one-tap confirmation) | 84904, 84906, 84910 | 3 |
| Human review | 84907, 84912 | 2 |
| Blocked (payment problem) | 84909, 84911 | 2 |

So about two thirds need no real Ops effort, and Ops attention goes only to the four cases that truly need judgment.

### 5.3 Systemic failure modes (beyond the sample rows)

**Human behaviour**
- Teachers forget, delay, or double-submit the form; no reminder or SLA exists
- Teachers paste wrong invoice links or amounts
- Discounts are offered informally with no approval trail
- Ops approves in batches, so evenings and weekends create long waits
- Free-text remarks carry critical facts (payer different, discount, batch change) that no system reads

**Data mismatches**
- Payer phone/email/name differs from the registered parent
- Invoice ID typos (transposed digits)
- Lookalike Unicode characters in names break exact matching
- Form amount differs from invoice `net_amount`; sessions purchased differ from what was paid for
- Batch matching on days/time alone can match the wrong class (batch 9205 is a Chess batch at Sat/Sun 11:00, while the 84912 student is a Gita student; always match on class and educator too)

**Process design**
- Steps 2 and 3 re-type and re-verify data the invoice already holds
- The capacity check counts the renewing student's own seat
- Failed states have no retry, alert, or owner
- Paid invoice with no form is invisible (no orphan detection)
- Batch-change renewals wait on a parent with no nudge and no deadline
- No idempotency: one invoice can create several forms or bookings

**Visibility**
- No single "paid but not scheduled" number
- No timer from `paid_at` to the first scheduled class
- No named owner per stuck record

---

## 6. Deliverable A — Metrics and SLAs

### 6.1 Metrics (give each a definition, formula, source table, and owner in the report)

| Metric | Definition |
|--------|------------|
| **Orphaned Invoice Rate** | Paid renewal invoices with no valid form after N hours ÷ all paid renewal invoices |
| **Payment-to-Schedule Turnaround** | First `class_schedule_bookings.created_at` − `invoices.paid_at` (median, p90) |
| **Payment-to-Form Time** | Form `created_at` − `paid_at` (teacher step) |
| **Form-to-Approval Time** | `approved_at` − form `created_at` (Ops step) |
| **Approval-to-Schedule Time** | Scheduling timestamp − `approved_at` (the dead-end step) |
| **Stuck Invoice Count (>12h)** | Paid invoices not scheduled after 12 hours |
| **Unapproved Form Backlog** | Pending forms by age bucket |
| **Unscheduled Booking Count** | `booking_requests` with `batch_allocated = No`, by status |
| **Duplicate Form Rate** | Invoices with more than 1 form |
| **Mismatch Rate** | Forms with ID / amount / phone mismatch against the invoice |
| **Auto-Approval Rate** | Renewals scheduled with zero human touch ÷ all renewals |
| **Exception Resolution Time** | Flag raised → resolved, by reason code |
| **Revenue at Risk (₹)** | Net amount of paid-but-unscheduled invoices |
| **Class Interruption Rate** | Renewing students who miss a class because scheduling was late |
| **Hours Saved** | Auto-handled renewals × manual minutes per renewal |

### 6.2 Proposed SLAs (adjust and justify in the report)

| Stage | Target |
|-------|--------|
| Payment → booking_request created (happy path) | ≤ 15 minutes, automatic |
| Payment → classes scheduled (clean same-batch) | ≤ 2 hours, automatic (today's best case: 1 h 45 min) |
| Orphan alert to teacher | 2 hours after payment; escalate to Ops at 12 hours |
| Exception acknowledged by owner | ≤ 4 working hours |
| Exception resolved | ≤ 24 hours |
| Parent batch-selection reminders | 24 h, 48 h, then escalate to Ops |
| Weekend/holiday cover | Automation 24x7; one on-call Ops owner |

---

## 7. Deliverable B — Re-engineered workflow

### 7.1 First principles: should each step exist?

| Today's step | Why it exists | Verdict |
|--------------|---------------|---------|
| Teacher fills the renewal form | Ops needs to know who paid and what they chose | **Eliminate for same-batch.** Invoice + student reference already hold it. Capture intent when the payment link is created, or confirm with the parent in one tap |
| Ops checks invoice vs form | Catch typos, wrong amounts, unpaid links | **Automate.** A rules engine is faster and does not make typos |
| Ops approves into `booking_requests` | Control gate | **Keep only for exceptions** |
| Parent/Ops selects the batch | Parent may want a change | **Skip for same-batch.** Keep only for real batch changes |

### 7.2 Target-state flow

```
Teacher creates the renewal payment link from a "Renewal Intent"
   (student, batch, sessions, discount code attached at pitch time)
                         │
                         ▼
        Razorpay / Stripe webhook: payment captured
                         │
                         ▼
          Rules engine validates (Section 8.2)
                         │
            ┌────────────┴─────────────┐
            ▼                          ▼
      ALL CHECKS PASS            ANY CHECK FAILS
            │                          │
            ▼                          ▼
  Auto-create booking_request     Assign reason code(s)
  + class_schedule_bookings       → route to ONE owner
            │                     → auto-draft the message
            ▼                     → start the SLA timer
  WhatsApp confirm to parent                │
  Slack/WA note to teacher                  ▼
            │                     Escalate if no action
            ▼
  Dashboard: "auto-approved" +1
```

A reconciliation sweep runs every 15 minutes in parallel. It catches paid invoices with no form, forms with no booking, and bookings with no schedule.

### 7.3 Happy-path eligibility (all must be true)

Payment `Paid` · amount equals the expected fee (or a pre-approved discount) · IDs consistent across tables · same batch · batch active · no duplicate form · payer identity matches (or soft-matches).

### 7.4 Exception routing

| Reason code | Owner | Action |
|-------------|-------|--------|
| `ORPHAN_NO_FORM` | Parent (confirm) + Teacher (notify) | Auto-draft the booking from invoice + reference; ask the parent "continue Tue/Thu 5 PM?"; escalate to Ops at 12 h |
| `INVOICE_ID_TYPO` | Automation | Auto-correct on a unique user_id + student_id + amount match; log it |
| `DUPLICATE_FORM` | Automation | Keep the first, mark the rest duplicate; inform the teacher |
| `AMOUNT_MISMATCH` | Ops exec | Compare form vs invoice; message the teacher |
| `PARTIAL_PAYMENT` | Finance / Ops exec | Schedule only what is covered (or hold); follow up installment 2 |
| `PAYMENT_NOT_CONFIRMED` | Parent, then Ops | Retry link; wait for the gateway webhook; never approve on a screenshot |
| `PAYER_MISMATCH` | Parent (registered number) + Ops | WhatsApp confirmation to the registered parent, then approve |
| `DISCOUNT_NEEDS_APPROVAL` | Ops lead / Head | Approval request with the discount reason; record who authorised |
| `FALSE_BATCH_FULL` | Automation | Re-run the capacity check without the student's own seat |
| `BATCH_CHANGE_PENDING` | Parent | Send batch options; reminders at 24 h and 48 h |
| `NO_MATCHING_BATCH` | Ops / Academics | Waitlist or open a batch; tell the parent the timeline |
| `HOMOGLYPH_MISMATCH` | Automation | Normalise lookalike characters; flag for data cleanup |

### 7.5 Key design decisions to defend in the review

| Decision | Reasoning | Risk and mitigation |
|----------|-----------|---------------------|
| Replace the teacher form with parent confirmation | The parent is the party who knows what they want; the teacher is just re-typing | Parent may not reply → reminders, then Ops fallback |
| Auto-approve only on strict rules | A wrong schedule for a paid child is costly | Shadow mode first; kill switch; audit log |
| Never approve on a screenshot | Only the gateway is the source of truth for payment | Retry link; webhook wait |
| Idempotency key = `invoice_id` | Prevents duplicate bookings | Unique constraint at the table level |
| Treat discounts as policy, not ad hoc | Revenue leakage and inconsistency | Pre-approved discount codes with limits |

### 7.6 Safety nets
- Idempotency on `invoice_id`
- Reconciliation sweep every 15 minutes
- LLM parses free-text teacher remarks into structured flags (Appendix A)
- Kill switch to return to manual at any time
- Audit log for every automated decision (what, why, which rule)

### 7.7 Tools to name
n8n or Make (orchestration) · Razorpay/Stripe webhooks · Google Sheets or the production DB · Metabase (dashboard) · WhatsApp Business API · Slack · an LLM for remark parsing and message drafting.

---

## 8. Deliverable C — Prototype specification

### 8.1 Choose one primary build

| Option | Best for | Note |
|--------|----------|------|
| Python script + prompts | Reproducible, easiest to review in a repo | Allowed under "script" |
| Google Sheet formulas + Apps Script | Non-technical reviewers | Good for the Loom demo |
| n8n / Make flow export | Shows real automation | Pair with sample outputs |

Recommended: a Python script as the engine, LLM prompts for remark parsing and message drafting, and the results CSVs committed to the repo. Add a Sheet or n8n export as a bonus.

### 8.2 Rule engine (apply in this order)

1. Drop soft-deleted rows (`deleted_at` not null).
2. Normalise text before any comparison: Unicode lookalikes, whitespace, case.
3. **Duplicate forms:** group by `invoice_id`, keep the earliest, flag the rest `DUPLICATE_FORM`.
4. **Invoice link:** if the form's `invoice_id` does not exist, fuzzy-match on `user_id` + `student_id` + `amount`; if exactly one match, apply `INVOICE_ID_TYPO`.
5. **Payment status:** `Failed` → `PAYMENT_NOT_CONFIRMED`; `Partially_Paid` → `PARTIAL_PAYMENT`.
6. **Amount:** form `amount_paid` vs invoice `net_amount` → `AMOUNT_MISMATCH`.
7. **Discount:** `discount_amount > 0`, or net below the standard fee from the reference table → `DISCOUNT_NEEDS_APPROVAL`.
8. **Identity:** `user_id`, `student_id`, `class_id`, `educator_id` consistent across invoice, form and reference; then phone/email vs the registered contact → `PAYER_MISMATCH`.
9. **Batch logic:**
   - `continue_same_batch = Yes`: capacity check **excluding the student's own seat**
   - `continue_same_batch = No`: search for a batch matching **class_id/category + educator + days + time** with a free seat; otherwise `NO_MATCHING_BATCH`
10. **Orphans:** paid invoice with no valid form after N hours → `ORPHAN_NO_FORM`.
11. **Stuck states:** booking in `Pending_Batch_Allocation`, `Failed_Batch_Full`, or `Awaiting_Parent_Batch_Selection` beyond its SLA → flag with the matching code.
12. If nothing fails → **AUTO_APPROVE**.

### 8.3 Outputs (save in `results/`)

| File | Contents |
|------|----------|
| `auto_approved.csv` | invoice_id, student_id, user_id, class_id, classbatch_id, educator_id, sessions, days, time (ready for `class_schedule_bookings`) |
| `exceptions.csv` | invoice_id, form_id, reason code(s), severity, owner, **evidence** (the exact mismatched values), hours stuck, suggested action |
| `messages.md` or `.json` | One drafted message per exception: recipient, channel, text |
| `summary.md` | Counts per bucket, revenue at risk, hours saved, snapshot time |

### 8.4 Quality checks before you call it done
- [ ] Every one of the 13 invoices has exactly one outcome
- [ ] Output matches your Section 5.2 answer key, or you can explain each difference
- [ ] Every exception shows evidence, not just a code
- [ ] Re-running gives identical results
- [ ] No match is made on masked names or phones alone; IDs first
- [ ] Assumptions listed in the README (snapshot time, SLA values, capacity logic, sessions rule)

### 8.5 Repo structure

```
your-repo/
├── README.md                  # overview, how to run, assumptions, results summary
├── Case_Report.pdf            # compulsory
├── data/                      # copy of the 5 input CSVs
├── prompts/
│   ├── remark_parser.md
│   ├── exception_triage.md
│   └── message_drafter.md
├── workflows_or_scripts/      # script / n8n or Make export / Sheet formulas
├── results/
│   ├── auto_approved.csv
│   ├── exceptions.csv
│   ├── messages.md
│   └── summary.md
└── dashboard/                 # mockup image or Metabase/Sheets file
```

### 8.6 Message rules
Short, specific (invoice number, amount, student), one clear ask, one deadline, polite. Parent messages in English with an optional Hinglish variant. Templates are in Appendix B.

---

## 9. Deliverable D — Dashboard, SOP, rollout, 30-60-90

### 9.1 Ops Head morning dashboard (wireframe, using the sample numbers)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ BAMBINOS RENEWALS — MORNING VIEW                      As of 09:00 IST    │
├──────────────┬──────────────┬──────────────┬─────────────┬───────────────┤
│ Paid renewals│ Auto-handled │ Scheduled    │ Revenue at  │ Hours saved   │
│ (sample)     │ %            │ %            │ risk (₹)    │ this week     │
│     11       │   ▲ target   │    9%  🔴    │ 1,21,600    │      —        │
├──────────────┴──────────────┴──────────────┴─────────────┴───────────────┤
│ STUCK INVOICES > 12h (6)         [owner]  [reason]   [hrs]  [action]     │
│  84902  ₹10,500  Ops exec  STUCK_AT_ALLOCATION   52   [fix]              │
│  84903  ₹9,000   Auto      Pending approval      33   [approve]          │
│  84904  ₹12,000  Parent    PAYER_MISMATCH        30   [confirm]          │
│  ...                                                                     │
├───────────────────────────────┬──────────────────────────────────────────┤
│ UNAPPROVED FORMS (8)          │ UNSCHEDULED BOOKINGS (3)                 │
│  0-2h: 1  2-12h: 4            │  Pending allocation: 1                   │
│  12-24h: 1  >24h: 2           │  Failed batch full:  1                   │
│                               │  Awaiting parent:    1                   │
├───────────────────────────────┴──────────────────────────────────────────┤
│ EXCEPTIONS BY REASON CODE (bar)        TURNAROUND vs SLA (median / p90)  │
├──────────────────────────────────────────────────────────────────────────┤
│ ORPHANED INVOICES by teacher           TEACHER FORM DELAY (coaching view)│
└──────────────────────────────────────────────────────────────────────────┘
```

Design notes: red/amber/green against SLA; every row has a named owner and a click-through; filters for date, teacher, category and region (India / GCC / US-UK). Build it in Metabase or Sheets, or deliver it as an image or HTML mockup.

### 9.2 Hours-saved formula (state assumptions explicitly)

```
Hours saved per week = renewals per week × % auto-handled × manual minutes per renewal ÷ 60
```

Illustration (replace with your own assumptions): 300 renewals/week × 60% auto-handled × 6 min ÷ 60 = **18 hours/week**. Add avoided teacher form time and avoided chasing/rework as separate lines. Use the sample's 42% zero-touch share (Section 5.2) as a conservative anchor and show the range.

### 9.3 SOPs

**Ops team SOP**
- [ ] Start of day: open the dashboard, clear red items first
- [ ] How to work each reason code: steps, whom to contact, template message
- [ ] Approval limits: what Ops can approve vs what goes to the Head (discounts)
- [ ] How to override the automation and log it
- [ ] Weekend and holiday cover rota
- [ ] Escalation ladder with timings

**Teacher SOP**
- [ ] What changes: no renewal form for same-batch renewals
- [ ] How to create a renewal payment link with the batch and discount attached
- [ ] How to flag a batch change or a discount
- [ ] What messages they will receive and how to reply
- [ ] Who to contact for help

**Parent communication**
- [ ] Automatic confirmation after payment (batch, days, first class date)
- [ ] Batch-selection nudge flow
- [ ] Failed and partial payment messages

### 9.4 Rollout principle: never break live classes

Run in **shadow mode** first (automation suggests, Ops still approves), then assisted, then auto, with a kill switch at every stage.

| Phase | What happens | Exit criteria |
|-------|--------------|---------------|
| **Shadow** | Automation runs beside the manual process; compare decisions | ≥ 95% agreement on clean cases; 0 wrong auto-approvals |
| **Pilot** | 1–2 categories / a small teacher group; auto-approve only the cleanest cases | SLA met; no parent complaints; Ops trusts the flags |
| **Scale** | All same-batch renewals; all categories and regions | Stable auto-approval rate; exception queue under control |
| **Optimise** | Retire the teacher form for the happy path; tune rules and messages | Form eliminated; targets hit |

### 9.5 30-60-90 plan

**Days 1–30 — Foundation and shadow mode**
- Pull the last 3 months of data and baseline every metric
- Build the reconciliation engine and dashboard v1
- Run in shadow mode; fix rules where it disagrees with Ops
- Train the Ops team; set up exception queues and owners

**Days 31–60 — Pilot and automate the happy path**
- Turn on auto-approval for the cleanest renewals with a pilot group
- Launch parent and teacher WhatsApp messages
- Add LLM remark parsing and the discount-approval flow
- Weekly exception review; tune rules

**Days 61–90 — Scale and eliminate**
- Roll out to all 200+ teachers in cohorts
- Replace the renewal form with the intent-based or one-tap flow
- Orphan sweep and SLA alerts live
- Publish results (hours saved, turnaround, revenue at risk) and plan the next phase (installment tracking, batch recommendation)

### 9.6 People and risk checklist
- [ ] Teacher training: short video, one-page guide, office hours
- [ ] Champions: 1 Ops lead plus a few teachers per cohort
- [ ] Rollback plan and kill switch tested before go-live
- [ ] Freeze periods around peak renewal weeks and term starts
- [ ] Feedback loop: weekly survey and a Slack channel
- [ ] Weekly metrics shared with the Head of Ops

---

## 10. Report (PDF) outline

Target 10–15 pages, visual (diagrams, tables, screenshots).

| Page(s) | Section |
|---------|---------|
| 1 | Executive summary: problem, impact (use the baseline numbers), solution, expected result |
| 2 | Current-state map: 4 tables, owners, handoffs |
| 3–4 | **A:** failure-mode audit with the 13-invoice evidence table |
| 5 | **A:** metrics and SLA definitions |
| 6 | **B:** first-principles review (eliminate / automate / keep) |
| 7 | **B:** redesigned workflow diagram + happy path |
| 8 | **B:** exception triage and routing table |
| 9 | **C:** prototype results (counts, screenshots), link to repo |
| 10 | **D:** dashboard design |
| 11 | **D:** SOPs (Ops and teacher) |
| 12 | **D:** rollout and 30-60-90 plan |
| 13 | Savings with assumptions |
| 14 | Risks, assumptions, next steps |

---

## 11. Live review preparation

Be ready to answer:
- Why did you eliminate the teacher form, and what could go wrong?
- What exactly can auto-approve, and what is the false-positive risk?
- What if the payment webhook fails or arrives late?
- How do you handle partial payments and discounts without hurting revenue?
- Why these SLA numbers?
- How do you roll out without disrupting live classes?
- Which of your numbers are assumptions, and how would you validate them with real data?
- What would you build next?

Practise a 5-minute walkthrough: **problem → insight → solution → proof (prototype) → rollout.** Lead with the headline: "Only 1 of 11 paid renewals had classes scheduled; 5 of the 12 outstanding could have been fixed with no human, and Ops attention is needed for only 4."

---

## 12. 72-hour schedule

| Time | Focus |
|------|-------|
| **0–6 h** | Read everything, map the flow, list failure modes, choose tools and assumptions |
| **6–24 h** | Build the reconciliation engine; generate `auto_approved`, `exceptions`, `messages` |
| **24–36 h** | Audit, metrics, SLAs; workflow design and routing |
| **36–48 h** | Dashboard, SOPs, 30-60-90, savings estimate |
| **48–60 h** | Assemble the PDF; write the README; clean the repo |
| **60–72 h** | Record the Loom; test all links; submit; rehearse the live review |

Aim to finish by hour 60 and use the last 12 hours as buffer.

---

## 13. Mistakes to avoid

- Automating a bad step instead of questioning why it exists
- Generic problems with no evidence from the CSVs
- Matching on masked names or phones instead of IDs first
- Matching batches on days/time only (can pick the wrong class)
- Approving on a payment screenshot instead of gateway confirmation
- Counting the renewing student's own seat against batch capacity
- Flags with a code but no evidence and no next action
- Savings numbers with no stated assumptions
- A rollout that flips everything at once
- A repo with no README, or links that do not open
- Forgetting the compulsory PDF

---

## 14. Final pre-submit checklist

- [ ] PDF covers A, B and D clearly and is readable on a phone
- [ ] Repo contains README, `prompts/`, `results/`, `workflows_or_scripts/`, and the PDF
- [ ] Results reproduce from the README instructions
- [ ] All 13 invoices have an outcome in `results/`
- [ ] Assumptions are written down (snapshot time, SLAs, minutes per task)
- [ ] Repo is public or shared with the right people
- [ ] Loom link added (if recorded)
- [ ] Form submitted before the deadline
- [ ] Live review rehearsed

---

## Appendix A — LLM prompt templates

### A.1 `prompts/remark_parser.md` — turn teacher remarks into structured flags

```
You are an operations assistant for Bambinos.live. Read ONE teacher remark from a
renewal form and extract structured flags. Do not guess; if a flag is not clearly
stated, set it to null.

Return ONLY valid JSON with these keys:
{
  "payer_differs_from_parent": true | false | null,
  "discount_mentioned": true | false | null,
  "discount_percent": number | null,
  "batch_change_requested": true | false | null,
  "requested_days": string | null,
  "requested_time": string | null,
  "payment_issue_mentioned": true | false | null,
  "resubmission_or_duplicate": true | false | null,
  "other_note": string | null,
  "confidence": "high" | "medium" | "low"
}

Examples:
"Mother paid from her number"        -> payer_differs_from_parent: true
"Offered 20% retention scholarship"  -> discount_mentioned: true, discount_percent: 20
"Parent wants weekend 11 AM batch"   -> batch_change_requested: true,
                                        requested_days: "Sat,Sun", requested_time: "11:00"
"Resubmitted as browser froze"       -> resubmission_or_duplicate: true
"Parent shared UPI processing screenshot" -> payment_issue_mentioned: true

Remark: {{remark}}
```

### A.2 `prompts/message_drafter.md` — draft the follow-up

```
You draft short WhatsApp/Slack messages for Bambinos.live Operations.

Inputs: recipient_type (teacher | parent | ops_agent | ops_head), reason_code,
evidence (JSON), deadline.

Rules:
- Under 70 words. Plain, polite, specific. No jargon or internal codes in
  parent or teacher messages.
- Name the student and invoice number. Give the exact amount or value that matters.
- Exactly ONE clear ask and ONE deadline.
- For ops_agent and ops_head: include the reason code, the evidence values, and
  the decision needed.
- For parents: offer an optional Hinglish version.
- Never promise a schedule you cannot guarantee.

Return JSON: {"recipient": "...", "channel": "whatsapp|slack", "message": "..."}
```

### A.3 `prompts/exception_triage.md` — optional LLM second opinion

```
You review a flagged renewal exception. Inputs: the rule engine's reason code(s)
and the evidence. Confirm or challenge the code(s), name the single best owner,
and state the next action in one sentence. If evidence is insufficient, say what is
missing. Never approve a payment based on a screenshot or a teacher's word alone.
```

---

## Appendix B — Message templates with real data

> Replace `{names}` with real values in the prototype. Examples use invoice numbers and amounts from the dataset.

**Teacher — missing form (invoice 84910, ₹11,000, Chess)**
> Hi Coach Arvind, the renewal payment of ₹11,000 for invoice BMB-INV-2026-84910 is received, but we have no renewal form. Please confirm by 6 PM today whether the student continues in the same batch (Wed/Fri 5 PM). Reply "SAME" or "CHANGE".

**Teacher — duplicate form (invoice 84908)**
> Hi Acharya Nancy, you submitted two forms for invoice BMB-INV-2026-84908. We kept the first one and marked the second as a duplicate. No action needed.

**Parent — confirm payer (invoice 84904)**
> Hello, we received a payment of ₹12,000 for {student}'s renewal from a different number than your registered one. Please reply "YES" to confirm it is yours so we can schedule Tue/Thu 5 PM classes. Reply by tomorrow 12 PM.

**Parent — failed payment (invoice 84911)**
> Hello, your renewal payment of ₹12,000 for {student} did not go through on our side (invoice BMB-INV-2026-84911). Please use this link to complete it: {link}. Classes will be scheduled as soon as payment is confirmed.

**Parent — partial payment (invoice 84909)**
> Hello, we received the first installment of ₹5,250 for {student}'s renewal. The second installment of ₹5,250 is due by {date}. We have scheduled {n} sessions; the rest will be added after the second payment.

**Ops head — discount approval (invoice 84907)**
> Approval needed: Invoice 84907, Phonics Level 1. Standard fee ₹9,500, paid ₹7,600 (20% discount, "retention scholarship", offered by Ms. Simran). Approve or reject by 5 PM so the student's classes can be scheduled.

**Ops agent — batch change with no match (invoice 84912)**
> Reason: BATCH_CHANGE_PENDING + NO_MATCHING_BATCH. Student wants Sat/Sun 11:00 in Gita Level 1 with Acharya Nancy; no such batch exists (closest: 9208 US track Sat/Sun 09:30, different fee). Decide: waitlist, open a new batch, or offer 9203 (Wed/Fri 16:30). Parent not yet contacted.

---

## Appendix C — Assumptions register

Write these into the README and the report so nothing looks hidden.

| Assumption | My value | Why / how to validate |
|------------|----------|-----------------------|
| Snapshot ("as-of") time | 2026-11-03 18:00 | Just after the last record in the data |
| "Stuck" threshold | 12 hours after payment | Per the assignment's dashboard brief |
| Sessions scheduled at renewal | Decide: all 24 or a rolling window | Invoice 84901 shows only 2 of 24; confirm with Ops |
| Discount policy | Pre-approved codes up to X% | Ask the Head of Ops; otherwise route to approval |
| Manual minutes per renewal | 6 min (illustrative) | Time two Ops execs on real renewals |
| Renewals per week | 300 (illustrative; the brief says "hundreds") | Pull the real number from the database |
| Auto-handled share | 42–67% (from the sample) | Re-measure on 3 months of real data |
| Currency for GCC/US invoices | Shown in INR | Confirm FX and gateway handling |
