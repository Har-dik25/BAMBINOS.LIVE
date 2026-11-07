#!/usr/bin/env python3
"""Builds Case_Report.pdf (Deliverables A, B, D + prototype summary). Numbers come from results/dashboard_metrics.json."""
import json
from pathlib import Path

import matplotlib
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image as RLImage, KeepTogether, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parent.parent
M = json.loads((ROOT / "results" / "dashboard_metrics.json").read_text())
FIG = ROOT / "docs" / "figures"
OUT = ROOT / "Case_Report.pdf"

ttf = Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf"
pdfmetrics.registerFont(TTFont("DV", str(ttf / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DV-B", str(ttf / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DV-I", str(ttf / "DejaVuSans-Oblique.ttf")))
pdfmetrics.registerFont(TTFont("DV-BI", str(ttf / "DejaVuSans-BoldOblique.ttf")))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")

NAVY, BLUE, GREEN, AMBER, ORANGE, RED = (colors.HexColor(c) for c in ("#1F3864", "#2E75B6", "#4E9A3A", "#E0A800", "#ED7D31", "#C00000"))
LIGHT, GREY = colors.HexColor("#F2F5FA"), colors.HexColor("#595959")
SEV = {"AUTO": "#C6EFCE", "AUTO_FIX": "#E2EFDA", "SOFT": "#FFEB9C", "HUMAN": "#F8CBAD", "BLOCK": "#FFC7CE", "DONE": "#D9D9D9"}

S = {
    "body": ParagraphStyle("body", fontName="DV", fontSize=9, leading=13, textColor=colors.HexColor("#222222"), spaceAfter=5),
    "small": ParagraphStyle("small", fontName="DV", fontSize=7.6, leading=10),
    "cell": ParagraphStyle("cell", fontName="DV", fontSize=7.6, leading=9.8),
    "cellb": ParagraphStyle("cellb", fontName="DV-B", fontSize=7.6, leading=9.8),
    "head": ParagraphStyle("head", fontName="DV-B", fontSize=7.8, leading=10, textColor=colors.white),
    "h1": ParagraphStyle("h1", fontName="DV-B", fontSize=15, leading=19, textColor=NAVY, spaceBefore=10, spaceAfter=6, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="DV-B", fontSize=10.5, leading=14, textColor=BLUE, spaceBefore=8, spaceAfter=3, keepWithNext=1),
    "h2n": ParagraphStyle("h2n", fontName="DV-B", fontSize=10.5, leading=14, textColor=BLUE, spaceBefore=8, spaceAfter=3, keepWithNext=0),
    "cap": ParagraphStyle("cap", fontName="DV-I", fontSize=7.8, leading=10, textColor=GREY, spaceAfter=6),
    "title": ParagraphStyle("title", fontName="DV-B", fontSize=21, leading=26, textColor=NAVY, spaceAfter=4),
    "sub": ParagraphStyle("sub", fontName="DV", fontSize=11, leading=15, textColor=BLUE, spaceAfter=3),
    "kpi": ParagraphStyle("kpi", fontName="DV-B", fontSize=17, leading=20, textColor=RED, alignment=1),
    "kpil": ParagraphStyle("kpil", fontName="DV", fontSize=7.6, leading=10, textColor=colors.HexColor("#333333"), alignment=1),
    "bullet": ParagraphStyle("bullet", fontName="DV", fontSize=9, leading=13, leftIndent=11, bulletIndent=1, spaceAfter=2.5),
}
W = A4[0] - 36 * mm  # frame width


def P(t, s="body"):
    return Paragraph(t, S[s])


def bullets(items):
    return [Paragraph(t, S["bullet"], bulletText="\u2022") for t in items]


def img(name, width=W):
    p = FIG / name
    w, h = Image.open(p).size
    return RLImage(str(p), width=width, height=width * h / w)


def table(rows, widths, header=True, zebra=True, sevcol=None, font=None):
    data = []
    for r, row in enumerate(rows):
        data.append([c if not isinstance(c, str) else Paragraph(c, S["head"] if (header and r == 0) else S["cell"]) for c in row])
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BFBFBF")),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        st += [("BACKGROUND", (0, 0), (-1, 0), NAVY)]
    if zebra:
        for r in range(1 if header else 0, len(rows)):
            if (r % 2) == 0:
                st.append(("BACKGROUND", (0, r), (-1, r), LIGHT))
    if sevcol is not None:
        for r, row in enumerate(rows):
            if r == 0:
                continue
            key = row[sevcol].split()[0].replace("<b>", "").replace("</b>", "")
            for k, c in SEV.items():
                if key.upper().startswith(k.replace("AUTO_FIX", "AUTO-FIX")) or key.upper() == k:
                    st.append(("BACKGROUND", (sevcol, r), (sevcol, r), colors.HexColor(c)))
    t.setStyle(TableStyle(st))
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("DV", 7.5)
    canvas.setFillColor(GREY)
    canvas.drawString(18 * mm, 10 * mm, "Bambinos.live  |  AI Program Manager (Operations)  |  Take-home case report")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#D0D7E2"))
    canvas.line(18 * mm, 13.5 * mm, A4[0] - 18 * mm, 13.5 * mm)
    canvas.restoreState()


doc = BaseDocTemplate(str(OUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=18 * mm,
                      title="Re-engineering the Student Renewal to Class Scheduling Pipeline", author="Hardik Choudhary",
                      subject="Bambinos.live AI Program Manager (Operations) take-home case")
doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=footer)])
E = []
inr = lambda x: "\u20b9{:,}".format(int(x)).replace(",", ",")  # noqa: E731


def indian(n):
    s = str(int(n))
    if len(s) <= 3:
        return "\u20b9" + s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:]); head = head[:-2]
    if head:
        parts.insert(0, head)
    return "\u20b9" + ",".join(parts) + "," + tail


# =========================================================================== COVER + EXEC SUMMARY
E += [P("Re-engineering the Student Renewal \u2192 Class Scheduling Pipeline", "title"),
      P("AI Program Manager (Operations) \u2014 Take-Home Case Report", "sub"),
      P("Deliverables A (audit), B (workflow), D (dashboard, SOP, 30-60-90) + summary of C (prototype)  \u00b7  Prepared by Hardik Choudhary  \u00b7  "
        "Data snapshot 2026-11-03 18:00 IST  \u00b7  Repo: <b>bambinos-ops-renewal-automation</b>", "small"), Spacer(1, 5)]
kpi = [[Paragraph(f"{M['paid_scheduled']} of {M['paid']}", S["kpi"]), Paragraph(indian(M["revenue_at_risk_inr"]), S["kpi"]),
        Paragraph(f"{M['stuck_over_12h']}", S["kpi"]), Paragraph(f"{M['zero_touch_pct']}%", ParagraphStyle("g", parent=S["kpi"], textColor=GREEN))],
       [Paragraph("paid renewals that reached scheduled classes", S["kpil"]), Paragraph("paid but not scheduled (10 invoices)", S["kpil"]),
        Paragraph(f"invoices stuck more than 12 h ({indian(M['stuck_over_12h_inr'])})", S["kpil"]),
        Paragraph("of outstanding renewals are zero-touch with the new design", S["kpil"])]]
kt = Table(kpi, colWidths=[W / 4] * 4)
kt.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, NAVY), ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BFBFBF")),
                        ("BACKGROUND", (0, 0), (-1, -1), LIGHT), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
E += [kt, Spacer(1, 7), P("Executive summary", "h1")]
E += [P("<b>The problem.</b> After a parent pays for a renewal, the child must pass through four tables and three manual handoffs "
        "(teacher form, Ops approval, batch selection) before classes are scheduled. In the 13-invoice sample, only <b>1 of 11</b> fully paid renewals "
        f"reached <font name='DV'>class_schedule_bookings</font>. Ten paid invoices worth <b>{indian(M['revenue_at_risk_inr'])}</b> are waiting, "
        f"six of them for more than 12 hours; the oldest (invoice 84902, paid on a Sunday) has waited about {M['oldest_stuck_hours']:.0f} hours and was already approved by Ops."),
      P("<b>The insight.</b> This is not a lazy-teacher problem. When teachers file the form they do it fast (median "
        f"{M['pay_to_form_hours_median'] * 60:.0f} minutes after payment). The pipeline leaks because steps 2 and 3 re-type and re-check data the invoice "
        "already contains, so typos, duplicates and missing forms are common, and because every failure state is a dead end with no owner, alert or retry. "
        "Ops approval is not the finish line: <b>3 of the 4 approved forms still have no classes</b>."),
      P("<b>The redesign.</b> (1) Remove the teacher form for same-batch renewals. (2) A rules engine reconciles every payment within minutes and schedules clean "
        "renewals with no human step. (3) Every exception gets one reason code, one named owner, a drafted WhatsApp/Slack message and an SLA timer. "
        "(4) The Head of Operations opens one dashboard each morning that shows stuck money first."),
      P(f"<b>The proof.</b> I built the engine three ways (Google Sheet formulas, a Python script, and the JavaScript rules for n8n); all three give identical results on all 13 invoices. "
        f"Of the {M['outstanding_renewals']} outstanding renewals: <b>{M['zero_touch']} are zero-touch ({M['zero_touch_pct']}%)</b> (auto-approve or a safe automatic fix), "
        f"<b>3 need only a one-tap parent confirmation</b> (together {M['zero_touch_plus_soft']} of {M['outstanding_renewals']}, {M['zero_touch_plus_soft_pct']}%), and only "
        f"<b>{M['needs_human']} need real human judgement</b> (a discount, a batch change, and two payment problems)."),
      P("<b>The rollout.</b> Shadow mode for 30 days (the engine suggests, Ops still approves), a pilot with a small teacher group, then all 200+ teachers in cohorts by day 90. "
        "A kill switch returns everything to the manual process at any time, so live class schedules are never put at risk."),
      P("<i>Honesty note: the sample is 13 invoices, so the percentages show what the design does on the provided data, not production rates. "
        "Section 6 lists every assumption and how I would validate it on real data.</i>", "small")]
E.append(PageBreak())

# =========================================================================== 1. CURRENT STATE
E += [P("1. Current state: how a renewal travels today", "h1"), img("fig_current_flow.png"),
      P("Figure 1. The four-table chain with the leak found at each step (numbers from the provided CSVs).", "cap"),
      P("<b>Method.</b> I traced every invoice through all four tables and the reference sheet (active batches and students), joining on "
        "<font name='DV'>invoice_id</font>, <font name='DV'>user_id</font>, <font name='DV'>student_id</font>, <font name='DV'>classbatch_id</font> and "
        "<font name='DV'>faculty_form_id</font>. Names and phones are masked in the data, so I matched on IDs first and used masked strings only as a secondary check. "
        "Soft-deleted rows were ignored. I then wrote down every place a paid student could stall.")]
E += [P("Handoffs and owners today", "h2"),
      table([["Handoff", "Who acts", "What goes wrong in the data"],
             ["Payment \u2192 form", "Teacher", "Form never filed (84906, 84910); wrong invoice number typed (84913 entered as 84931); form filed twice (84908); wrong amount (84909 shows \u20b910,500 for a \u20b95,250 instalment)"],
             ["Form \u2192 booking request", "Ops exec (manual)", "8 of 12 forms pending, oldest 32.5 h; discount and payer differences caught only by eye (84904, 84907)"],
             ["Booking request \u2192 schedule", "Parent or Ops", "Dead ends: stuck at allocation (84902), false \"batch full\" (84905), waiting on parent with no reminder (84912)"]],
            [32 * mm, 28 * mm, W - 60 * mm])]

# =========================================================================== 2. DELIVERABLE A
E += [P("2. Deliverable A: root-cause audit and leakage", "h1"),
      P("2.1 Invoice-by-invoice audit (every row is evidence from the CSVs)", "h2n")]
audit = [["Invoice", "What the data shows", "Reason code", "Outcome"],
         ["84901", "Fully done in 1 h 45 min. But only 2 of 24 purchased sessions exist in table 4 (rolling window or under-scheduling: to confirm with Ops)", "SESSIONS_UNDER_SCHEDULED (info)", "DONE"],
         ["84902", "Form approved, booking 5502 stuck at Pending_Batch_Allocation for ~48 h; batch 9202 has 5 of 6 seats. Paid on a Sunday", "STUCK_AT_ALLOCATION", "AUTO-FIX"],
         ["84903", "Clean same-batch renewal; amount, IDs and batch capacity all fine; form still pending after 32 h", "none", "AUTO"],
         ["84904", "Invoice mobile, email and payer name differ from the registered parent; teacher remark: \"Mother paid from her number\". user_id and student_id match", "PAYER_MISMATCH", "SOFT"],
         ["84905", "Booking failed as batch full (6/6), but the student already holds a seat in that batch; a same-batch renewal needs no new seat", "FALSE_BATCH_FULL", "AUTO-FIX"],
         ["84906", "Paid via Stripe (Dubai parent), \u20b918,000, no teacher form at all", "ORPHAN_NO_FORM", "SOFT"],
         ["84907", "20% discount (\u20b99,500 \u2192 \u20b97,600) offered by the teacher as a \"retention scholarship\"; no approval trail", "DISCOUNT_NEEDS_APPROVAL", "HUMAN"],
         ["84908", "Two forms (3308, 3309) for one invoice because the browser froze; would create a double booking", "DUPLICATE_FORM", "AUTO-FIX"],
         ["84909", "Instalment 1 of 2: \u20b95,250 paid of \u20b910,500. Teacher's form claims \u20b910,500 paid and 24 sessions", "PARTIAL_PAYMENT + AMOUNT_MISMATCH", "BLOCK"],
         ["84910", "Paid \u20b911,000, no teacher form", "ORPHAN_NO_FORM", "SOFT"],
         ["84911", "Gateway status Failed, no payment id; teacher forwarded a UPI \"processing\" screenshot", "PAYMENT_NOT_CONFIRMED", "BLOCK"],
         ["84912", "Parent wants a weekend 11 AM batch. Form approved, booking waits on the parent, nobody nudges. No Gita batch exists at that slot (batch 9205 is Sat/Sun 11:00 but it is Chess)", "BATCH_CHANGE_PENDING + NO_MATCHING_BATCH", "HUMAN"],
         ["84913", "Form cites invoice 84931 (digits swapped). The invoice's parent name also contains Cyrillic look-alike letters, which silently breaks exact name matching", "INVOICE_ID_TYPO + HOMOGLYPH_MISMATCH", "AUTO-FIX"]]
E += [table(audit, [14 * mm, W - 14 * mm - 52 * mm - 17 * mm, 52 * mm, 17 * mm], sevcol=3)]
E += [Spacer(1, 4), P("Outcome key: AUTO = clean, zero touch; AUTO-FIX = safe defect repaired automatically; SOFT = one-tap parent confirmation; HUMAN = needs judgement; BLOCK = payment problem, never schedule.", "cap")]
E += [P("2.2 Systemic failure modes (beyond the 13 rows)", "h2"),
      table([["Human behaviour", "Data mismatches", "Process design", "Visibility"],
             ["Teachers forget, delay or double-submit; no reminder or SLA<br/>Discounts offered informally, no approval trail<br/>Ops approves in batches, so evenings and weekends wait<br/>Free-text remarks carry key facts nobody reads",
              "Payer differs from registered parent<br/>Invoice ID typos (transposed digits)<br/>Look-alike Unicode characters break exact match<br/>Form amount or sessions differ from what was paid<br/>Matching a batch on days/time alone can pick the wrong class",
              "Steps 2 and 3 re-type and re-verify known data<br/>Capacity check counts the student's own seat<br/>Failed states have no retry, alert or owner<br/>Paid-but-no-form is invisible<br/>No idempotency: one invoice can create two bookings",
              "No single \"paid but not scheduled\" number<br/>No timer from payment to first class<br/>No named owner on any stuck record<br/>Weekend delays are not measured"]],
            [W / 4] * 4, zebra=False)]
E += [P("2.3 Quantifying the leakage", "h2"), img("fig_leakage_funnel.png", width=W * 0.82),
      P("Figure 2. Funnel of the 11 fully paid renewals in the sample (snapshot 2026-11-03 18:00).", "cap")]
E += [table([["Baseline number (sample)", "Value", "Why it matters"],
             ["Paid renewals that reached scheduled classes", f"{M['paid_scheduled']} of {M['paid']} (9%)", "The headline leak"],
             ["Paid but not scheduled", f"10 invoices, {indian(M['revenue_at_risk_inr'])}", "Revenue at risk and broken parent experience"],
             ["Stuck more than 12 h", f"{M['stuck_over_12h']} invoices, {indian(M['stuck_over_12h_inr'])}", "The Ops Head's first morning question"],
             ["Oldest stuck invoice", f"84902, about {M['oldest_stuck_hours']:.0f} h", "Paid Sunday, approved by Ops, still no classes"],
             ["Forms pending Ops approval", f"{M['forms_pending']} of {M['forms_total']}; oldest {M['oldest_pending_form_hours']} h", "The manual queue"],
             ["Approved forms that actually got classes", f"{M['approved_forms_that_got_classes']} of {M['forms_approved']}", "Approval is not the finish line"],
             ["Paid with no valid form", "3 (84906, 84910, and 84913 via a typo)", "Orphans: invisible today"],
             ["Teacher delay when a form is filed", f"median {M['pay_to_form_hours_median'] * 60:.0f} min, max {M['pay_to_form_hours_max'] * 60:.0f} min", "Teachers are fast; the process is the problem"],
             ["Best-case payment to schedule today", "1 h 45 min (invoice 84901)", "Sets the SLA target (2 h, automatic)"]],
            [62 * mm, 52 * mm, W - 114 * mm])]
E += [Spacer(1, 4), P("2.4 Metrics and SLAs that are broken or invisible today", "h2"),
      table([["Metric", "Definition (source tables)", "Owner"],
             ["Orphaned Invoice Rate", "Paid renewal invoices with no valid form after N h \u00f7 all paid renewals (invoices, forms)", "Ops Head"],
             ["Payment-to-Schedule Turnaround", "First class_schedule_bookings.created_at \u2212 invoices.paid_at; median and p90", "Ops Head"],
             ["Payment-to-Form time / Form-to-Approval time", "Teacher step and Ops step measured separately (forms, invoices)", "Ops lead"],
             ["Approval-to-Schedule time", "Scheduling timestamp \u2212 approved_at; exposes the dead-end states (booking_requests)", "Ops lead"],
             ["Stuck Invoice Count (>12 h) and Revenue at Risk", "Paid, no schedule row, older than threshold; sum of net_amount", "Ops Head"],
             ["Auto-Approval Rate", "Renewals scheduled with zero human touch \u00f7 all renewals", "Program Mgr"],
             ["Duplicate Form Rate / Mismatch Rate", "Invoices with more than one form; forms with ID, amount or phone mismatch", "Ops lead"],
             ["Exception Resolution Time", "Flag raised \u2192 resolved, by reason code", "Ops lead"],
             ["Hours Saved", "Auto-handled renewals \u00d7 manual minutes per renewal", "Program Mgr"]],
            [52 * mm, W - 52 * mm - 22 * mm, 22 * mm])]
E += [Spacer(1, 5),
      table([["Stage", "Proposed SLA"],
             ["Payment \u2192 booking request created (happy path)", "\u2264 15 minutes, automatic"],
             ["Payment \u2192 classes scheduled (clean same-batch)", "\u2264 2 hours, automatic (best case today is 1 h 45 min, and manual)"],
             ["Orphan (paid, no form)", "Alert at 2 h after payment; escalate to Ops at 12 h"],
             ["Exception acknowledged / resolved", "\u2264 4 working hours / \u2264 24 hours"],
             ["Parent batch-selection reminders", "At 24 h and 48 h, then escalate to Ops"],
             ["Weekends and holidays", "Automation runs 24x7; one on-call Ops owner"]],
            [78 * mm, W - 78 * mm])]

# =========================================================================== 3. DELIVERABLE B
E += [P("3. Deliverable B: the re-engineered \"zero-touch\" workflow", "h1"),
      P("3.1 First principles: should each step exist?", "h2"),
      table([["Today's step", "Why it exists", "Verdict"],
             ["Teacher fills the renewal form", "Ops needs to know who paid and what they chose", "<b>Eliminate for same-batch renewals.</b> The invoice and the student record already hold it. Capture intent when the payment link is created, or confirm with the parent in one tap"],
             ["Ops compares invoice vs form", "Catch typos, wrong amounts, unpaid links", "<b>Automate.</b> A rules engine is faster and does not make typos"],
             ["Ops approves into booking_requests", "Control gate", "<b>Keep only for exceptions.</b> Clean renewals pass automatically"],
             ["Parent or Ops selects the batch", "Parent may want a change", "<b>Skip for same-batch.</b> Keep only for real batch changes, with reminders"]],
            [44 * mm, 45 * mm, W - 89 * mm]),
      Spacer(1, 4), img("fig_target_flow.png"), P("Figure 3. Target-state workflow: one rules engine, two lanes, one owner per exception.", "cap")]
E += [P("3.2 What can be fully eliminated (the happy path)", "h2"),
      P("A renewal is zero-touch when <b>all</b> are true: payment is Paid on the gateway; the amount equals the expected fee (or a pre-approved discount); IDs agree across invoice, form and reference; "
        "the student continues in the same batch and the batch is active; no duplicate form exists; and the payer matches the registered parent (or soft-matches). "
        "The engine then creates the booking request and the schedule rows, sends the parent a WhatsApp confirmation with the first class date, and tells the teacher \"nothing to do\". "
        "A 15-minute sweep also catches anything the webhook missed (orphans, stuck bookings, duplicates), so no paid invoice can stay invisible.")]
E += [P("3.3 Smart exception handling: code \u2192 one owner \u2192 message \u2192 timer", "h2"),
      table([["Reason code", "Owner", "What the automation does", "Message goes to"],
             ["ORPHAN_NO_FORM", "Parent (confirm) + Teacher (notify)", "Auto-draft the booking from invoice + reference; ask the parent \"same batch? reply 1 / change? reply 2\"; escalate to Ops at 12 h", "Parent, teacher"],
             ["INVOICE_ID_TYPO", "Automation", "Unique match on user_id + student_id + amount repairs the link; logged", "Teacher (FYI)"],
             ["DUPLICATE_FORM", "Automation", "Keep the earliest form, mark the rest duplicate (idempotency on invoice_id)", "Teacher (FYI)"],
             ["HOMOGLYPH_MISMATCH", "Automation", "Normalise look-alike characters before matching; flag record for data clean-up", "Ops log"],
             ["STUCK_AT_ALLOCATION / FALSE_BATCH_FULL", "Automation", "Allocate the batch; re-run the capacity check without the student's own seat", "Parent"],
             ["PAYER_MISMATCH", "Parent (registered number) + Ops", "WhatsApp to the registered parent: reply YES if the payment was yours or family's, then approve", "Parent, Ops"],
             ["DISCOUNT_NEEDS_APPROVAL", "Ops lead / Head", "Approval request with the discount, reason and teacher; record who authorised", "Head of Ops"],
             ["AMOUNT_MISMATCH", "Ops exec", "Show form vs invoice side by side; schedule only what was paid", "Ops, teacher"],
             ["PARTIAL_PAYMENT", "Ops exec / Finance", "Hold full-term scheduling; decide what the instalment covers; remind parent for instalment 2", "Parent, Ops"],
             ["PAYMENT_NOT_CONFIRMED", "Parent, then Ops", "Send retry link; wait for the gateway webhook; never approve on a screenshot", "Parent, teacher, Ops"],
             ["BATCH_CHANGE_PENDING / NO_MATCHING_BATCH", "Parent + Ops / Academics", "Send options; reminders at 24 h and 48 h; Ops decides waitlist, new batch or existing slot. Match on class + educator + days + time, never days/time alone", "Parent, Ops"]],
            [49 * mm, 31 * mm, W - 49 * mm - 31 * mm - 21 * mm, 21 * mm])]
E += [P("3.4 Design decisions I would defend", "h2"),
      table([["Decision", "Reasoning", "Risk and mitigation"],
             ["Replace the teacher form with parent confirmation for orphans", "The parent knows what they want; the teacher is only re-typing", "Parent may not reply \u2192 reminders, then an Ops phone call"],
             ["Auto-approve only on strict rules", "A wrong schedule for a paid child is costly", "Shadow mode first, kill switch, audit log of every decision"],
             ["Never approve on a screenshot", "Only the gateway is the source of truth for payment", "Retry link; wait for webhook; Ops checks the gateway"],
             ["Idempotency key = invoice_id", "Prevents duplicate bookings from double submissions", "Unique constraint at table level"],
             ["Discounts become policy, not ad hoc", "Revenue leakage and inconsistency", "Pre-approved discount codes with limits; anything else goes to approval"],
             ["LLM reads and drafts, rules decide", "LLMs are good at free text, bad at strict yes/no", "The LLM never approves anything; deterministic rules do"]],
            [52 * mm, 55 * mm, W - 107 * mm]),
      P("3.5 Tools", "h2"),
      P("n8n or Make for orchestration (payment webhook trigger + 15-minute sweep) \u00b7 Razorpay/Stripe webhooks \u00b7 Google Sheets or the production database \u00b7 Metabase for the dashboard \u00b7 "
        "WhatsApp Business API for parents and teachers \u00b7 Slack for Ops \u00b7 an LLM for reading teacher remarks and drafting messages (prompts in the repo). "
        "An importable n8n template is in the repo; it is a template and has not been run against live credentials.")]

# =========================================================================== 4. DELIVERABLE C SUMMARY
E += [P("4. Deliverable C: working prototype (summary; full detail in the repo)", "h1"),
      P("The prototype reads the 5 CSVs and gives every invoice exactly one outcome. I built the same rules three ways so Ops can choose how to run them, and so each build checks the others:"),
      table([["Build", "File", "Who it suits"],
             ["Google Sheets / Excel formulas (no code)", "workflows_or_scripts/Renewal_Reconciliation_Sheet.xlsx (752 formulas, 0 errors)", "Ops and PMs: open in Google Sheets, paste new rows, read every rule"],
             ["Python script (reference engine)", "workflows_or_scripts/reconcile.py (pandas only)", "Reproducible results, outputs the 3 required files"],
             ["n8n rules node + workflow template", "n8n_rules_engine.js, n8n_renewal_workflow.json", "Live automation: webhook and 15-minute sweep"],
             ["LLM prompts", "prompts/remark_parser.md, exception_triage.md, message_drafter.md", "Reading teacher remarks, drafting messages"],
             ["SQL for the dashboard", "workflows_or_scripts/dashboard_queries.sql (9 MySQL queries)", "Metabase questions on the production tables"]],
            [48 * mm, W - 48 * mm - 52 * mm, 52 * mm]),
      Spacer(1, 4),
      P("<b>Verification.</b> The Sheet, the Python engine and the n8n JavaScript agree on the outcome and reason codes of all 13 invoices. "
        "A mutation test (changing one form amount in the Sheet) flipped invoice 84903 from AUTO_APPROVE to HUMAN / AMOUNT_MISMATCH, so the formulas are live. "
        "The SQL queries were run on the same data (via SQLite with date functions translated) and reproduce the same counts (for example 6 stuck invoices, 10 paid-unscheduled, \u20b91,21,600).")]
E += [img("fig_outcome_split.png", width=W * 0.78), P("Figure 4. Engine outcome for the 12 outstanding renewals.", "cap")]
E += [P("The three required outputs", "h2"),
      table([["Required output", "File", "What is in it"],
             ["Auto-approved entries ready for class_schedule_bookings", "results/auto_approved.csv, proposed_class_schedule_bookings.csv", "5 renewals (84902, 84903, 84905, 84908, 84913) with any fix applied, plus 120 proposed session rows (24 each) in the shape of table 4"],
             ["Flagged exceptions with exact reason codes", "results/exceptions.csv", "7 renewals (84904, 84906, 84907, 84909, 84910, 84911, 84912) with severity, owner, evidence values and the next action"],
             ["Auto-drafted WhatsApp / Slack messages", "results/messages.md and messages.json", f"21 messages for parents (with Hinglish), teachers, Ops execs and the Head of Ops, one ask and one deadline each"]],
            [50 * mm, 48 * mm, W - 98 * mm]),
      Spacer(1, 5), P("Example (invoice 84904, to the parent on the registered number): <i>\"We received a payment of \u20b912,000 for the student's renewal from a different mobile/email than the one on your account. "
        "Please reply YES if this was you or a family member, and we will schedule Tue,Thu 17:00 classes right away. Reply by Wed 04 Nov, 12 PM.\"</i> "
        "The matching Ops message names the reason code, the evidence and the fallback (call the registered number).", "small"),
      P("<b>Limits.</b> Names and phones are masked in the source, so messages use masked names. Messages in the results are template-based for reproducibility; the LLM prompt writes them in production. "
        "Time zones for GCC/US tracks are not modelled. The n8n workflow and WhatsApp/Slack/LLM nodes are an importable template that was not executed against live services.", "small")]

# =========================================================================== 5. DELIVERABLE D
E += [P("5. Deliverable D: dashboard, SOPs, rollout and 30-60-90 plan", "h1"),
      P("5.1 The Ops Head's morning dashboard", "h2"), img("fig_dashboard.png"),
      P("Figure 5. Mock-up with the sample numbers (live version: Google Sheet 'Dashboard' tab, or Metabase on dashboard_queries.sql).", "cap"),
      table([["Block", "Shows", "Source"],
             ["Health strip", "Paid renewals, auto-handled %, scheduled %, revenue at risk, hours saved", "Q9 + Checks"],
             ["Stuck invoices > 12 h", "Invoice, amount, owner, reason, hours stuck, next action (click-through)", "Q2"],
             ["Unapproved forms", "Count by age bucket (0-2 h, 2-12 h, 12-24 h, >24 h)", "Q3"],
             ["Unscheduled bookings", "By status: pending allocation, failed batch full, awaiting parent", "Q6"],
             ["Orphans and duplicates", "Paid with no form (by teacher); duplicate and mismatched forms", "Q1, Q4, Q5, Q8"],
             ["Turnaround vs SLA", "Payment-to-schedule median and p90; teacher and Ops step times", "Q7"]],
            [34 * mm, W - 34 * mm - 22 * mm, 22 * mm]),
      P("Red/amber/green against SLA; every row has a named owner; filters for date, teacher, category and region (India, GCC, US/UK). The teacher view is for coaching, not blame.", "small")]
E += [P("5.2 SOPs", "h2"),
      table([["Ops team (daily)", "Teachers (what changes)"],
             ["1. 9:00 open the dashboard; clear red items first (oldest, highest \u20b9)<br/>"
              "2. Work each item by reason code using the template message; the system has already drafted it<br/>"
              "3. Approval limits: execs approve ID/amount fixes and payer confirmations; discounts go to the Ops lead or Head<br/>"
              "4. Never schedule on a screenshot; check the gateway status first<br/>"
              "5. To override the automation, use the override column and write the reason (audit log)<br/>"
              "6. Weekend rota: one on-call owner; automation keeps running<br/>"
              "7. Escalate if an item breaches SLA: exec \u2192 lead (4 h) \u2192 Head (24 h)",
              "1. For same-batch renewals there is <b>no renewal form</b>: create the payment link from the Renewal Intent (student, batch, sessions, discount code)<br/>"
              "2. For a batch change or a discount, tick it on the Intent; do not type it in remarks<br/>"
              "3. You will get a short message when the renewal is confirmed, or if the parent needs a nudge<br/>"
              "4. If a parent says they paid but the link failed, ask for the bank reference; a screenshot is not enough<br/>"
              "5. Questions: the #ops-renewals channel; response within 4 working hours"]],
            [W / 2, W / 2], zebra=False)]
E += [P("5.3 Rollout without breaking live class schedules", "h2"), img("fig_rollout.png", width=W * 0.95),
      P("Figure 6. Phased rollout with exit gates and a kill switch.", "cap"),
      table([["Phase", "What happens", "Exit gate (Head of Ops signs off)"],
             ["Days 1\u201330 Shadow", "Pull 3 months of data and baseline every metric. Engine runs beside the manual process; compare its decision with Ops on every renewal. Train Ops; set up queues and owners", "\u2265 95% agreement on clean cases; 0 wrong auto-approvals; dashboard v1 trusted"],
             ["Days 31\u201360 Pilot", "Auto-approve the cleanest renewals for 1\u20132 categories and about 20 teachers. WhatsApp messages and remark parsing go live; discount-approval flow starts", "Payment-to-schedule SLA met; no parent complaints; exception queue within SLA"],
             ["Days 61\u201390 Scale", "All 200+ teachers in cohorts. Intent-based payment link replaces the renewal form. Orphan sweep and SLA alerts live. Publish results", "Auto-approval rate stable; hours saved and turnaround reported; plan phase 2 (instalment tracking, batch recommendation)"]],
            [28 * mm, W - 28 * mm - 55 * mm, 55 * mm])]
E += [P("Change management for 200+ teachers and a 10-person Ops team", "h2")]
E += bullets(["<b>Teachers:</b> a 3-minute video, a one-page guide and weekly office hours; cohorts of about 40 teachers so support never gets overwhelmed; a champion teacher per cohort.",
              "<b>Ops team:</b> day-1 workshop on reason codes; every exec shadows the engine for two weeks; the Ops lead owns the rule book and approves any rule change.",
              "<b>Parents:</b> every message says what happened, what to do, and by when. Hinglish variant for parents; native-speaker review before launch.",
              "<b>Safety:</b> kill switch tested before go-live; manual process kept until day 90; freeze changes around term starts and peak renewal weeks.",
              "<b>Feedback loop:</b> weekly review of the exception log; every wrong call becomes a new rule or a prompt fix."])
E += [P("5.4 30-60-90 day plan", "h2"),
      table([["", "Days 1\u201330: Foundation", "Days 31\u201360: Pilot", "Days 61\u201390: Scale"],
             ["Build", "Rules engine and dashboard v1 on real data; reconciliation sweep; audit log", "Auto-approve for pilot group; WhatsApp templates approved and live; LLM remark parsing; discount approval flow", "Intent-based payment link; org-wide rollout; SLA alerts"],
             ["People", "Ops training; owners and queues; teacher comms plan", "Pilot teachers trained; weekly feedback", "Cohort training for all teachers; champions"],
             ["Measure", "Baseline: orphan rate, payment-to-schedule, stuck count, duplicate rate", "Auto-approval rate, SLA attainment, false-approval count (target 0)", "Hours saved, turnaround vs SLA, revenue at risk trend"],
             ["Decision", "Go / no-go for pilot", "Go / no-go for scale", "Phase 2: instalment tracking, batch recommendation"]],
            [18 * mm, (W - 18 * mm) / 3, (W - 18 * mm) / 3, (W - 18 * mm) / 3])]
E += [P("5.5 Time and cost savings (illustrative: inputs are assumptions, replace with real numbers)", "h2"),
      table([["Item", "Calculation", "Result"],
             ["Ops hours saved per week (sample zero-touch share)", "300 renewals/week \u00d7 42% \u00d7 6 min \u00f7 60", "\u2248 12.5 h/week"],
             ["Ops hours saved if soft cases are one-tap too", "300 \u00d7 67% \u00d7 6 min \u00f7 60", "\u2248 20 h/week"],
             ["Teacher time saved (form removed)", "300 \u00d7 42% \u00d7 4 min \u00f7 60", "\u2248 8.4 h/week"],
             ["Value of Ops time (assumed \u20b9250/h loaded cost)", "12.5 h \u00d7 52 weeks \u00d7 \u20b9250", "\u2248 \u20b91.6 lakh/year"],
             ["Revenue protected (sample)", "Paid but unscheduled today", f"{indian(M['revenue_at_risk_inr'])} in this sample alone"]],
            [64 * mm, W - 64 * mm - 40 * mm, 40 * mm]),
      P("The bigger prize is not hours; it is parents who paid and still get their class on time (retention). Tooling cost (n8n or Make plan, WhatsApp Business conversation fees, LLM calls only for exceptions) "
        "needs a quote; I expect it to be a small fraction of the hours saved, and I would confirm that before pilot.", "small")]
E += [P("5.6 Risks and mitigations", "h2"),
      table([["Risk", "Mitigation"],
             ["A wrong auto-approval schedules the wrong class for a paid child", "Strict eligibility rules; shadow mode with 0-error gate; audit log; kill switch"],
             ["Payment webhook arrives late or fails", "15-minute sweep catches missed payments; Ops checks the gateway for Failed/pending UPI"],
             ["Parents do not reply to the one-tap confirmation", "Reminders at 24 h and 48 h, then an Ops phone call; SLA timer visible on the dashboard"],
             ["Teachers keep using remarks/forms out of habit", "Renewal Intent makes the right path the easy path; champion teachers; coaching view"],
             ["WhatsApp template approval delays", "Start approval in week 1; Slack/email fallback during pilot"],
             ["Rules drift as policies change (discounts, instalments)", "Ops lead owns the rule book; every change versioned and tested on the sample first"]],
            [78 * mm, W - 78 * mm])]

# =========================================================================== 6. ASSUMPTIONS
E += [P("6. Assumptions, limits and what I would validate first", "h1"),
      table([["Assumption", "Value used", "How I would validate"],
             ["Snapshot time", "2026-11-03 18:00 IST (just after the newest record)", "Use NOW() in production"],
             ["Stuck threshold", "12 hours after payment", "From the assignment's dashboard brief; confirm with the Head of Ops"],
             ["Sessions per term / scheduled at renewal", "24; engine schedules all purchased sessions", "Invoice 84901 shows only 2 of 24: confirm whether scheduling is rolling"],
             ["Discount policy", "Any discount needs approval", "Ask for the real policy; turn pre-approved codes into an automatic rule"],
             ["Manual minutes per renewal", "6 min (illustrative)", "Time two Ops execs on real renewals"],
             ["Renewals per week", "300 (the brief says \"hundreds\")", "Pull the real number from the database"],
             ["Zero-touch share", "42% (67% with soft); from 12 outstanding sample renewals", "Re-measure on 3 months of production data in shadow mode"],
             ["Instalment coverage (84909)", "Not assumed; held for Ops/Finance", "Ask Finance how many sessions an instalment covers"],
             ["Time zones (GCC / US tracks)", "Times used as stored", "Confirm how batch times are stored per region"],
             ["Currency for GCC / US invoices", "Shown as INR in the data", "Confirm FX and gateway handling"]],
            [48 * mm, 58 * mm, W - 106 * mm]),
      Spacer(1, 6), P("What I did not do: I did not run the n8n workflow, WhatsApp, Slack or LLM calls against live services (credentials are placeholders); I did not record the Loom video (a talk track is in docs/); "
        "and the sample is too small to claim production percentages. Everything else described here is in the repository and was run on the provided CSVs.", "small"),
      P("Repository map", "h2"),
      table([["Path", "Contents"],
             ["README.md", "Overview, how to run each build, results, assumptions"],
             ["Case_Report.pdf", "This report"],
             ["data/", "The 5 input CSVs, unchanged"],
             ["prompts/", "remark_parser.md, exception_triage.md, message_drafter.md"],
             ["workflows_or_scripts/", "reconcile.py, Renewal_Reconciliation_Sheet.xlsx, n8n_renewal_workflow.json, n8n_rules_engine.js, dashboard_queries.sql, build and test scripts"],
             ["results/", "auto_approved.csv, proposed_class_schedule_bookings.csv, exceptions.csv, decisions_all.csv, messages.md/json, summary.md, dashboard_metrics.json"],
             ["dashboard/", "ops_head_dashboard_mockup.png"],
             ["docs/", "Execution checklist, Loom talk track, figures"]],
            [48 * mm, W - 48 * mm])]

doc.build(E)
print("wrote", OUT)
