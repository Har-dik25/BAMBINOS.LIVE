# Reconciliation summary

Snapshot (as-of) time: **2026-11-03 18:00** · invoices analysed: **13** · every invoice has exactly one outcome.

## Headline

- Fully paid renewals that reached scheduled classes: **1 of 11**
- Paid but not scheduled: **10** invoices, **₹1,21,600**
- Stuck more than 12 h: **6** invoices, **₹68,100**; oldest is invoice 84902 at **51.7 h**
- Forms pending Ops approval: **8 of 12** (oldest 32.5 h)
- Approved forms that actually got classes: **1 of 4**
- Teacher delay when a form is filed: median 25 min, max 50 min

## Outcome split of the outstanding renewals

| Outcome | Invoices | Meaning |
|---|---|---|
| ALREADY_SCHEDULED | 84901 | Classes already exist in table 4 |
| AUTO_APPROVE | 84903 | Clean - zero human touch |
| AUTO_FIX | 84902, 84905, 84908, 84913 | Safe defect repaired automatically, then scheduled |
| SOFT | 84904, 84906, 84910 | One-tap parent confirmation |
| HUMAN | 84907, 84912 | Needs judgement (discount / batch change) |
| BLOCK | 84909, 84911 | Payment problem - do not schedule |

**Zero-touch (auto-approve + auto-fix): 5 of 12 (42%)**. Adding one-tap soft confirmations: 8 of 12 (67%). Only 4 need real human judgement.

## Reason codes raised

| Code | Count |
|---|---|
| ORPHAN_NO_FORM | 2 |
| SESSIONS_UNDER_SCHEDULED | 1 |
| STUCK_AT_ALLOCATION | 1 |
| PAYER_MISMATCH | 1 |
| FALSE_BATCH_FULL | 1 |
| DISCOUNT_NEEDS_APPROVAL | 1 |
| DUPLICATE_FORM | 1 |
| PARTIAL_PAYMENT | 1 |
| AMOUNT_MISMATCH | 1 |
| PAYMENT_NOT_CONFIRMED | 1 |
| BATCH_CHANGE_PENDING | 1 |
| NO_MATCHING_BATCH | 1 |
| INVOICE_ID_TYPO | 1 |
| HOMOGLYPH_MISMATCH | 1 |

## Invoice by invoice

| Invoice | Outcome | Reason codes | Owner |
|---|---|---|---|
| 84901 | ALREADY_SCHEDULED | SESSIONS_UNDER_SCHEDULED | Ops exec (info) |
| 84902 | AUTO_FIX | STUCK_AT_ALLOCATION | Automation |
| 84903 | AUTO_APPROVE | - | Automation |
| 84904 | SOFT | PAYER_MISMATCH | Parent (registered number) + Ops exec |
| 84905 | AUTO_FIX | FALSE_BATCH_FULL | Automation |
| 84906 | SOFT | ORPHAN_NO_FORM | Parent (confirm) + Teacher (notify) |
| 84907 | HUMAN | DISCOUNT_NEEDS_APPROVAL | Ops lead / Head of Ops |
| 84908 | AUTO_FIX | DUPLICATE_FORM | Automation |
| 84909 | BLOCK | PARTIAL_PAYMENT, AMOUNT_MISMATCH | Ops exec / Finance | Ops exec |
| 84910 | SOFT | ORPHAN_NO_FORM | Parent (confirm) + Teacher (notify) |
| 84911 | BLOCK | PAYMENT_NOT_CONFIRMED | Parent, then Ops exec |
| 84912 | HUMAN | BATCH_CHANGE_PENDING, NO_MATCHING_BATCH | Parent + Ops exec | Ops exec / Academics |
| 84913 | AUTO_FIX | INVOICE_ID_TYPO, HOMOGLYPH_MISMATCH | Automation |
