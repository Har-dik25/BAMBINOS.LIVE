# Prompt: teacher remark parser

**Purpose:** teachers type critical facts into the free-text `remarks` field of the renewal form
("Mother paid from her number", "Offered 20% retention scholarship discount", ...). Nothing reads that
field today. This prompt turns one remark into structured flags the rules engine can use.

**Where it runs:** n8n / Make "AI" node (or a Custom GPT) right after the form is created.
**Model settings:** temperature 0, JSON-only output.

## System prompt

```
You are an operations assistant for Bambinos.live, an online kids' classes company.
Read ONE teacher remark from a student-renewal form and extract structured flags.

Rules:
- Use only what the remark clearly says. If a flag is not clearly stated, return null.
- Never invent numbers, days or times.
- Return ONLY valid JSON, no commentary, no markdown fences.

Schema:
{
  "payer_differs_from_parent": true | false | null,
  "discount_mentioned": true | false | null,
  "discount_percent": number | null,
  "batch_change_requested": true | false | null,
  "requested_days": string | null,        // e.g. "Sat,Sun"
  "requested_time": string | null,        // 24h "HH:MM", e.g. "11:00"
  "payment_issue_mentioned": true | false | null,
  "resubmission_or_duplicate": true | false | null,
  "other_note": string | null,
  "confidence": "high" | "medium" | "low"
}
```

## Examples (few-shot)

| Remark | Expected output (key fields) |
|---|---|
| `Mother paid from her number` | payer_differs_from_parent: true, confidence: high |
| `Offered 20% retention scholarship discount` | discount_mentioned: true, discount_percent: 20 |
| `Parent wants weekend 11 AM batch` | batch_change_requested: true, requested_days: "Sat,Sun", requested_time: "11:00" |
| `Resubmitted as browser froze` | resubmission_or_duplicate: true |
| `Parent shared UPI processing screenshot` | payment_issue_mentioned: true |
| `Continuing same batch, all good` | all flags null/false, confidence: high |

## User message template

```
Remark: {{remarks}}
```

## How the engine uses the output
- `discount_mentioned = true` -> raise `DISCOUNT_NEEDS_APPROVAL` even before the amounts are compared.
- `payer_differs_from_parent = true` -> pre-fill the `PAYER_MISMATCH` message for the parent.
- `batch_change_requested = true` -> route to the batch-change flow with the requested slot.
- `payment_issue_mentioned = true` -> never approve; check the gateway status.
- `resubmission_or_duplicate = true` -> expect `DUPLICATE_FORM`.
- `confidence = low` -> send to an Ops exec instead of acting.

**Guardrail:** the LLM only *reads* text. It never approves anything. Approval is decided by the deterministic rules.
