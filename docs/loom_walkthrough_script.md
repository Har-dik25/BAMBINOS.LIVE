# Loom walkthrough: talk track (2–3 minutes)

_Not recorded yet: use this as your script. Screen order: Sheet `Dashboard` → `Checks` → `Exceptions` → `Messages`._

**0:00–0:20 Problem (show Dashboard tab).**
"After a parent pays for a renewal, the child passes four tables and three manual handoffs. In the sample, only 1 of 11 paid
renewals has classes scheduled. Ten paid invoices, ₹1,21,600, are waiting; six for more than 12 hours."

**0:20–0:50 Insight.**
"Teachers are fast when they file (median 25 minutes). The leak is the process: the form re-types data the invoice already holds,
and every failure state is a dead end with no owner. Three of four approved forms still have no classes."

**0:50–1:30 The engine (show Checks tab).**
"Each invoice runs through one ordered rule set, in plain formulas. The sheet gives every invoice a reason code, a severity and an owner.
For example 84913: the form cites invoice 84931, a typo, and the parent's name has Cyrillic look-alike letters. The engine repairs the link
by matching user, student and amount, normalises the characters, and schedules it with no human touch."

**1:30–2:15 Exceptions and messages (show Exceptions, then Messages).**
"Five renewals are zero-touch. Three need only a one-tap parent confirmation, like 84904 where the mother paid from her own number.
Four need judgement: a discount, a batch change, a partial payment and a failed payment. Never approve on a screenshot.
Each exception gets one named owner and a drafted WhatsApp or Slack message with one ask and one deadline."

**2:15–2:45 Rollout.**
"Shadow mode for 30 days, a pilot, then all teachers in cohorts by day 90. A kill switch returns everything to manual, so live classes are safe.
The Ops Head sees stuck money first thing every morning."

**Close (2:45–3:00).** "Same rules also run as a Python script and an n8n workflow; all three agree on all 13 invoices. Thank you."
