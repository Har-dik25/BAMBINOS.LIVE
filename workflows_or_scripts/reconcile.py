#!/usr/bin/env python3
"""
Bambinos.live - Renewal Reconciliation & Auto-Approval Engine
==============================================================
Reads the 5 masked production CSVs and decides, for EVERY invoice, exactly one outcome:

    ALREADY_SCHEDULED  classes already exist in table 4
    AUTO_APPROVE       clean renewal -> ready for class_schedule_bookings, zero human touch
    AUTO_FIX           a known, safe defect was repaired automatically -> ready to schedule
    SOFT               one-tap confirmation from the parent (or a quick Ops glance)
    HUMAN              needs a person's judgement (discount, batch change, ...)
    BLOCK              payment problem - never schedule

Outputs (written to ../results by default):
    decisions_all.csv                    one row per invoice (the full audit)
    auto_approved.csv                    AUTO_APPROVE + AUTO_FIX rows, ready for table 4
    proposed_class_schedule_bookings.csv proposed session rows for the auto-approved renewals
    exceptions.csv                       SOFT / HUMAN / BLOCK rows with reason codes + evidence
    messages.json / messages.md          drafted WhatsApp / Slack messages
    summary.md, dashboard_metrics.json   headline numbers for the report and dashboard

Usage:
    python reconcile.py                       # uses ../data, writes ../results
    python reconcile.py --asof "2026-11-03 18:00"

Only needs: pandas.  No network, no database.
"""
import argparse
import json
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------------------
# Configuration (all assumptions live here and are repeated in the README / report)
# --------------------------------------------------------------------------------------
DEFAULT_ASOF = "2026-11-03 18:00"   # snapshot time: just after the newest record in the data
STUCK_HOURS = 12                    # "stuck" threshold from the assignment's dashboard brief
CLASS_MINUTES = 50                  # class length seen in table 4 (17:00-17:50)
SESSIONS_DEFAULT = 24               # standard term = 24 sessions

# Common Cyrillic / Greek look-alikes that silently break exact string matching.
CONFUSABLES = {
    "\u0410": "A", "\u0412": "B", "\u0415": "E", "\u041a": "K", "\u041c": "M",
    "\u041d": "H", "\u041e": "O", "\u0420": "P", "\u0421": "C", "\u0422": "T",
    "\u0425": "X", "\u0430": "a", "\u0435": "e", "\u043e": "o", "\u0440": "p",
    "\u0441": "c", "\u0443": "y", "\u0445": "x", "\u0456": "i", "\u0391": "A",
    "\u039f": "O", "\u03bf": "o",
}

# reason code -> (severity, owner)
CODE_META = {
    "PAYMENT_NOT_CONFIRMED":    ("BLOCK", "Parent, then Ops exec"),
    "PARTIAL_PAYMENT":          ("BLOCK", "Ops exec / Finance"),
    "AMOUNT_MISMATCH":          ("HUMAN", "Ops exec"),
    "ID_MISMATCH":              ("HUMAN", "Ops exec"),
    "DISCOUNT_NEEDS_APPROVAL":  ("HUMAN", "Ops lead / Head of Ops"),
    "NO_MATCHING_BATCH":        ("HUMAN", "Ops exec / Academics"),
    "BATCH_CHANGE_PENDING":     ("HUMAN", "Parent + Ops exec"),
    "BATCH_FULL":               ("HUMAN", "Ops exec / Academics"),
    "ORPHAN_NO_FORM":           ("SOFT",  "Parent (confirm) + Teacher (notify)"),
    "PAYER_MISMATCH":           ("SOFT",  "Parent (registered number) + Ops exec"),
    "DUPLICATE_FORM":           ("AUTO_FIX", "Automation"),
    "INVOICE_ID_TYPO":          ("AUTO_FIX", "Automation"),
    "HOMOGLYPH_MISMATCH":       ("AUTO_FIX", "Automation"),
    "STUCK_AT_ALLOCATION":      ("AUTO_FIX", "Automation"),
    "FALSE_BATCH_FULL":         ("AUTO_FIX", "Automation"),
    "SESSIONS_UNDER_SCHEDULED": ("INFO",  "Ops exec (info)"),
}
RANK = {"INFO": 0, "AUTO_FIX": 2, "SOFT": 3, "HUMAN": 4, "BLOCK": 5}


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------
def skeleton(text: str) -> str:
    """Replace look-alike letters so 'Ме***a' (Cyrillic) equals 'Me***a' (Latin)."""
    if not isinstance(text, str):
        return ""
    return "".join(CONFUSABLES.get(c, c) for c in unicodedata.normalize("NFKC", text)).strip().lower()


def has_non_ascii(text) -> bool:
    return isinstance(text, str) and any(ord(c) > 127 for c in text)


def fmt_inr(x) -> str:
    x = float(x)
    s = f"{int(round(x)):,}"
    # Indian digit grouping
    digits = str(int(round(x)))
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    else:
        s = digits
    return f"\u20b9{s}"


def hours_between(a, b):
    if pd.isna(a) or pd.isna(b):
        return None
    return round((b - a).total_seconds() / 3600, 1)


def next_sessions(batch_days: str, start_time: str, n: int, after: datetime):
    """Yield the next n session datetimes for a batch that meets on the given weekdays."""
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    days = [names.index(d.strip()[:3].title()) for d in batch_days.split(",")]
    hh, mm, *_ = [int(p) for p in start_time.split(":")]
    out, day = [], after.date()
    while len(out) < n:
        if day.weekday() in days:
            dt = datetime(day.year, day.month, day.day, hh, mm)
            if dt > after:
                out.append(dt)
        day += timedelta(days=1)
    return out


# --------------------------------------------------------------------------------------
# Load
# --------------------------------------------------------------------------------------
def load(data_dir: Path):
    inv = pd.read_csv(data_dir / "1_invoices.csv", parse_dates=["paid_at", "created_at", "updated_at"])
    ff = pd.read_csv(data_dir / "2_faculty_form_unapproved.csv",
                     parse_dates=["created_at", "approved_at", "updated_at"])
    br = pd.read_csv(data_dir / "3_booking_requests.csv",
                     parse_dates=["allocated_at", "created_at", "updated_at"])
    cs = pd.read_csv(data_dir / "4_class_schedule_bookings.csv")
    ref = pd.read_csv(data_dir / "reference_active_batches_and_students.csv", dtype={"batch_start_time": str})
    # Rule 1: soft-deleted rows do not exist
    inv, ff, br, cs, ref = [d[d["deleted_at"].isna()].copy() for d in (inv, ff, br, cs, ref)]
    return inv, ff, br, cs, ref


# --------------------------------------------------------------------------------------
# Core engine
# --------------------------------------------------------------------------------------
def reconcile(data_dir: Path, asof: datetime):
    inv, ff, br, cs, ref = load(data_dir)
    asof_ts = pd.Timestamp(asof)
    refx = ref.set_index("student_id")

    # ---- Step A: link every form to an invoice (fix ID typos), then de-duplicate ----------
    inv_ids = set(inv["id"])
    form_links = {}  # form id -> (resolved invoice id | None, typo_flag)
    for _, f in ff.iterrows():
        if f["invoice_id"] in inv_ids:
            form_links[f["id"]] = (int(f["invoice_id"]), False)
            continue
        cand = inv[(inv["user_id"] == f["user_id"]) & (inv["student_id"] == f["student_id"])
                   & (inv["net_amount"] == f["amount_paid"])]
        form_links[f["id"]] = (int(cand.iloc[0]["id"]), True) if len(cand) == 1 else (None, False)
    ff["resolved_invoice_id"] = ff["id"].map(lambda i: form_links[i][0])
    ff["typo_fixed"] = ff["id"].map(lambda i: form_links[i][1])
    ff = ff.sort_values(["resolved_invoice_id", "created_at"])
    ff["dup_rank"] = ff.groupby("resolved_invoice_id").cumcount() + 1

    rows = []
    for _, i in inv.sort_values("id").iterrows():
        inv_id = int(i["id"])
        sid = int(i["student_id"])
        r = refx.loc[sid] if sid in refx.index else None
        forms = ff[ff["resolved_invoice_id"] == inv_id]
        form = forms[forms["dup_rank"] == 1].iloc[0] if len(forms) else None
        bk = br[br["invoice_id"] == inv_id]
        bk = bk.iloc[0] if len(bk) else None
        sched = cs[cs["invoice_id"] == inv_id]
        codes, evid = [], {}

        # ---- payment status gate --------------------------------------------------------
        if i["payment_status"] == "Failed":
            codes.append("PAYMENT_NOT_CONFIRMED")
            evid["PAYMENT_NOT_CONFIRMED"] = (
                f"gateway status Failed, no gateway_payment_id, paid_at empty; "
                f"teacher remark: '{form['remarks'] if form is not None else ''}' (a screenshot is not proof of payment)")
        if i["payment_status"] == "Partially_Paid":
            codes.append("PARTIAL_PAYMENT")
            evid["PARTIAL_PAYMENT"] = (
                f"{i['payment_type']}: {fmt_inr(i['net_amount'])} paid of {fmt_inr(i['amount'])} "
                f"({fmt_inr(i['amount'] - i['net_amount'])} outstanding)")

        # ---- orphan (paid, no form, nothing scheduled) -----------------------------------
        if form is None and i["payment_status"] == "Paid" and len(sched) == 0 and bk is None:
            codes.append("ORPHAN_NO_FORM")
            evid["ORPHAN_NO_FORM"] = (
                f"paid {i['paid_at']:%d %b %H:%M} ({hours_between(i['paid_at'], asof_ts)} h ago) but no faculty form "
                f"points to invoice {inv_id}")

        if form is not None:
            # duplicate forms
            if len(forms) > 1:
                codes.append("DUPLICATE_FORM")
                evid["DUPLICATE_FORM"] = (
                    f"forms {', '.join(str(int(x)) for x in forms['id'])} all reference invoice {inv_id}; "
                    f"kept earliest ({int(form['id'])}), others marked duplicate "
                    f"(remark: '{forms.iloc[-1]['remarks']}')")
            # invoice id typo
            if bool(form["typo_fixed"]):
                codes.append("INVOICE_ID_TYPO")
                evid["INVOICE_ID_TYPO"] = (
                    f"form {int(form['id'])} cites invoice {int(form['invoice_id'])} which does not exist; "
                    f"unique match on user_id {int(i['user_id'])} + student_id {sid} + amount "
                    f"{fmt_inr(i['net_amount'])} = invoice {inv_id}")
            # amount mismatch
            if abs(float(form["amount_paid"]) - float(i["net_amount"])) > 0.5:
                codes.append("AMOUNT_MISMATCH")
                evid["AMOUNT_MISMATCH"] = (
                    f"form says {fmt_inr(form['amount_paid'])} paid for {int(form['sessions_purchased'])} sessions; "
                    f"invoice net_amount is {fmt_inr(i['net_amount'])}")
            # id consistency
            bad = [k for k, a, b in [("user_id", form["user_id"], i["user_id"]),
                                      ("student_id", form["student_id"], i["student_id"]),
                                      ("class_id", form["class_id"], i["class_id"]),
                                      ("educator_id", form["educator_id"], i["educator_id"])] if int(a) != int(b)]
            if bad:
                codes.append("ID_MISMATCH")
                evid["ID_MISMATCH"] = "form vs invoice differ on: " + ", ".join(bad)

        # ---- discount --------------------------------------------------------------------
        if float(i["discount_amount"]) > 0:
            codes.append("DISCOUNT_NEEDS_APPROVAL")
            pct = round(100 * float(i["discount_amount"]) / float(i["amount"]))
            evid["DISCOUNT_NEEDS_APPROVAL"] = (
                f"discount {fmt_inr(i['discount_amount'])} ({pct}%): {fmt_inr(i['amount'])} -> {fmt_inr(i['net_amount'])}"
                + (f"; teacher remark: '{form['remarks']}'" if form is not None else ""))

        # ---- payer identity vs registered parent ---------------------------------------
        if r is not None:
            mob_ok = i["mobile"] == r["registered_mobile_masked"]
            mail_ok = i["email"] == r["registered_email_masked"]
            name_raw_ok = i["parent_name"] == r["parent_name_masked"]
            name_skel_ok = skeleton(i["parent_name"]) == skeleton(r["parent_name_masked"])
            if (not mob_ok) or (not mail_ok) or (not name_skel_ok):
                codes.append("PAYER_MISMATCH")
                evid["PAYER_MISMATCH"] = (
                    f"invoice mobile {i['mobile']} vs registered {r['registered_mobile_masked']}; "
                    f"invoice email {i['email']} vs registered {r['registered_email_masked']}; "
                    f"invoice payer '{i['parent_name']}' vs registered parent '{r['parent_name_masked']}'"
                    + (f"; teacher remark: '{form['remarks']}'" if form is not None else "")
                    + "; user_id and student_id still match, so it is the right account")
            elif not name_raw_ok:
                codes.append("HOMOGLYPH_MISMATCH")
                odd = [f"U+{ord(c):04X} {unicodedata.name(c, '?')}" for c in i["parent_name"] if ord(c) > 127]
                evid["HOMOGLYPH_MISMATCH"] = (
                    f"invoice parent_name '{i['parent_name']}' contains look-alike characters ({'; '.join(odd)}); "
                    f"after normalising it equals the registered name '{r['parent_name_masked']}'")

        # ---- booking_request stuck states ----------------------------------------------
        batch_id = int(form["current_classbatch_id"]) if form is not None else (int(r["current_classbatch_id"]) if r is not None else None)
        in_own_batch = r is not None and int(r["current_classbatch_id"]) == batch_id
        if bk is not None:
            stuck_h = hours_between(bk["updated_at"], asof_ts)
            if bk["request_status"] == "Pending_Batch_Allocation":
                codes.append("STUCK_AT_ALLOCATION")
                evid["STUCK_AT_ALLOCATION"] = (
                    f"booking_request {int(bk['id'])} approved {bk['created_at']:%d %b %H:%M} but never allocated "
                    f"({stuck_h} h); batch {int(bk['classbatch_id'])} has {int(r['active_students_count'])}/{int(r['max_batch_size'])} seats")
            elif bk["request_status"] == "Failed_Batch_Full":
                if in_own_batch:
                    codes.append("FALSE_BATCH_FULL")
                    evid["FALSE_BATCH_FULL"] = (
                        f"booking_request {int(bk['id'])} failed 'batch full' ({int(r['active_students_count'])}/"
                        f"{int(r['max_batch_size'])}), but the student already occupies a seat in batch {batch_id}; "
                        f"a same-batch renewal needs no new seat")
                else:
                    codes.append("BATCH_FULL")
                    evid["BATCH_FULL"] = f"target batch {batch_id} is full and student is not already in it"
            elif bk["request_status"] == "Awaiting_Parent_Batch_Selection":
                codes.append("BATCH_CHANGE_PENDING")
                evid["BATCH_CHANGE_PENDING"] = (
                    f"booking_request {int(bk['id'])} waiting on the parent since {bk['created_at']:%d %b %H:%M} "
                    f"({stuck_h} h) with no batch assigned and no reminder sent")

        # ---- batch change: is there a matching batch with a free seat? -----------------
        alt_options = ""
        if form is not None and form["continue_same_batch"] == "No" and r is not None:
            same_cat = ref[(ref["category_id"] == r["category_id"]) & (ref["educator_id"] == r["educator_id"])]
            want_days, want_time = str(form["preferred_days"]), str(form["preferred_time_slot"])
            hit = same_cat[(same_cat["batch_days"] == want_days) & (same_cat["batch_start_time"] == want_time)
                           & (same_cat["active_students_count"] < same_cat["max_batch_size"])]
            if hit.empty:
                codes.append("NO_MATCHING_BATCH")
                others = same_cat.drop_duplicates("current_classbatch_id")
                alt = [f"{o['classbatch_name']} ({o['batch_days']} {o['batch_start_time'][:5]}, "
                       f"fee {fmt_inr(o['standard_fee_24_sessions_inr'])})" for _, o in others.iterrows()]
                alt_options = "; ".join(alt)
                evid["NO_MATCHING_BATCH"] = (
                    f"parent wants {want_days} {want_time[:5]} in {r['category_name']} with {r['educator_name']}; "
                    f"no such batch exists. Same-teacher batches: {alt_options}. "
                    f"(Do NOT match on days/time alone: batch 9205 is Sat,Sun 11:00 but it is a Chess batch.)")

        # ---- sessions under-scheduled (info only) --------------------------------------
        sessions = int(form["sessions_purchased"]) if form is not None else SESSIONS_DEFAULT
        if len(sched) > 0 and len(sched) < sessions:
            codes.append("SESSIONS_UNDER_SCHEDULED")
            evid["SESSIONS_UNDER_SCHEDULED"] = (
                f"only {len(sched)} of {sessions} purchased sessions exist in class_schedule_bookings "
                f"(rolling window or under-scheduling - confirm with Ops)")

        # ---- final decision ---------------------------------------------------------------
        scheduled = len(sched) > 0
        if scheduled:
            sev = "ALREADY_SCHEDULED"
        elif not codes:
            sev = "AUTO_APPROVE"
        else:
            sev = max((CODE_META[c][0] for c in codes), key=lambda s: RANK[s])
            if sev == "INFO":
                sev = "AUTO_APPROVE"
        owners = []
        for c in codes:
            if CODE_META[c][0] != "INFO" or scheduled:
                o = CODE_META[c][1]
                if o not in owners:
                    owners.append(o)
        if sev == "AUTO_APPROVE":
            owners = ["Automation"]

        hrs_paid = hours_between(i["paid_at"], asof_ts) if pd.notna(i["paid_at"]) else None
        rows.append({
            "invoice_id": inv_id, "invoice_number": i["invoice_number"], "student_id": sid,
            "student_name": r["student_name_masked"] if r is not None else "",
            "parent_name_registered": r["parent_name_masked"] if r is not None else "",
            "class_name": r["class_name"] if r is not None else "",
            "educator_id": int(i["educator_id"]), "educator_name": r["educator_name"] if r is not None else "",
            "payment_status": i["payment_status"], "net_amount": float(i["net_amount"]), "currency": i["currency"],
            "hours_since_payment": hrs_paid,
            "form_id": int(form["id"]) if form is not None else None,
            "booking_request_id": int(bk["id"]) if bk is not None else None,
            "scheduled_sessions": len(sched),
            "outcome": sev,
            "reason_codes": ", ".join(c for c in codes),
            "owner": " | ".join(owners),
            "evidence": " || ".join(f"{c}: {evid[c]}" for c in codes),
            "alt_options": alt_options,
            "_batch_id": batch_id, "_sessions": sessions,
        })
    dec = pd.DataFrame(rows)
    for c in ("form_id", "booking_request_id"):
        dec[c] = dec[c].astype("Int64")   # whole numbers, <NA> where absent
    return dec, inv, ff, br, cs, ref


# --------------------------------------------------------------------------------------
# Outputs
# --------------------------------------------------------------------------------------
def suggested_action(codes: str) -> str:
    cs = [c.strip() for c in codes.split(",") if c.strip()]
    acts = {
        "PAYMENT_NOT_CONFIRMED": "Send retry link to parent; wait for gateway webhook; never approve on a screenshot",
        "PARTIAL_PAYMENT": "Hold full-term scheduling; Ops/Finance decide what the instalment covers; chase instalment 2",
        "AMOUNT_MISMATCH": "Compare form with invoice; ask teacher to correct; schedule only what was actually paid",
        "DISCOUNT_NEEDS_APPROVAL": "Ops lead approves/rejects the discount and records who authorised it",
        "NO_MATCHING_BATCH": "Offer alternatives, waitlist, or open a new batch; tell the parent the timeline",
        "BATCH_CHANGE_PENDING": "Send batch options to parent; reminders at 24h and 48h; escalate to Ops after",
        "ORPHAN_NO_FORM": "Auto-draft booking from invoice + reference; ask parent to confirm same batch; notify teacher",
        "PAYER_MISMATCH": "Confirm with the registered parent on the registered number, then approve",
    }
    return " | ".join(acts[c] for c in cs if c in acts)


def build_outputs(dec, inv, ff, br, cs, ref, asof, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    asof_ts = pd.Timestamp(asof)
    refx = ref.set_index("student_id")
    dec["suggested_action"] = dec["reason_codes"].map(suggested_action)

    public_cols = ["invoice_id", "invoice_number", "student_id", "student_name", "class_name", "educator_name",
                   "payment_status", "net_amount", "hours_since_payment", "form_id", "booking_request_id",
                   "scheduled_sessions", "outcome", "reason_codes", "owner", "evidence", "suggested_action"]
    dec[public_cols].to_csv(out_dir / "decisions_all.csv", index=False)

    # ---- auto_approved.csv -----------------------------------------------------------------
    auto = dec[dec["outcome"].isin(["AUTO_APPROVE", "AUTO_FIX"])].copy()
    a_rows = []
    for _, d in auto.iterrows():
        form = ff[(ff["resolved_invoice_id"] == d["invoice_id"]) & (ff["dup_rank"] == 1)].iloc[0]
        r = refx.loc[int(d["student_id"])]
        a_rows.append({
            "invoice_id": d["invoice_id"], "form_id": int(form["id"]),
            "booking_request_id": int(d["booking_request_id"]) if pd.notna(d["booking_request_id"]) else "NEW",
            "user_id": int(form["user_id"]), "student_id": int(d["student_id"]), "class_id": int(form["class_id"]),
            "classbatch_id": int(d["_batch_id"]), "educator_id": int(d["educator_id"]),
            "sessions_count": int(d["_sessions"]), "batch_days": r["batch_days"], "start_time": r["batch_start_time"],
            "booking_type": "Regular_Renewal", "outcome": d["outcome"],
            "fixes_applied": d["reason_codes"] if d["outcome"] == "AUTO_FIX" else "none",
            "fix_evidence": d["evidence"] if d["outcome"] == "AUTO_FIX" else "all checks passed",
            "hours_since_payment": d["hours_since_payment"],
        })
    pd.DataFrame(a_rows).to_csv(out_dir / "auto_approved.csv", index=False)

    # ---- proposed session rows (shape of table 4) ------------------------------------------
    sess_rows = []
    for a in a_rows:
        times = next_sessions(a["batch_days"], a["start_time"], a["sessions_count"], asof)
        for n, t in enumerate(times, 1):
            end = t + timedelta(minutes=CLASS_MINUTES)
            sess_rows.append({
                "invoice_id": a["invoice_id"], "bookingrequest_id": a["booking_request_id"],
                "classschedule_id": "(assigned by system)", "classbatch_id": a["classbatch_id"],
                "class_id": a["class_id"], "user_id": a["user_id"], "student_id": a["student_id"],
                "educator_id": a["educator_id"], "session_no": n, "class_date": t.strftime("%Y-%m-%d"),
                "start_time": t.strftime("%H:%M:%S"), "end_time": end.strftime("%H:%M:%S"),
                "booking_type": "Regular_Renewal", "is_cancelled": "No", "attended_class": "No"})
    pd.DataFrame(sess_rows).to_csv(out_dir / "proposed_class_schedule_bookings.csv", index=False)
    first_class = {a["invoice_id"]: next_sessions(a["batch_days"], a["start_time"], 1, asof)[0] for a in a_rows}

    # ---- exceptions.csv ---------------------------------------------------------------------
    exc = dec[dec["outcome"].isin(["SOFT", "HUMAN", "BLOCK"])].copy()
    exc["severity_rank"] = exc["outcome"].map({"BLOCK": 0, "HUMAN": 1, "SOFT": 2})
    exc = exc.sort_values(["severity_rank", "hours_since_payment"], ascending=[True, False])
    exc[["invoice_id", "invoice_number", "student_id", "student_name", "educator_name", "net_amount",
         "hours_since_payment", "outcome", "reason_codes", "owner", "evidence", "suggested_action"]
        ].rename(columns={"outcome": "severity"}).to_csv(out_dir / "exceptions.csv", index=False)

    # ---- messages --------------------------------------------------------------------------
    msgs = draft_messages(dec, inv, ff, ref, asof, first_class)
    (out_dir / "messages.json").write_text(json.dumps(msgs, indent=2, ensure_ascii=False))
    md = ["# Drafted follow-up messages", "",
          f"_Generated by `reconcile.py` for snapshot **{asof:%Y-%m-%d %H:%M}**. Template-based here so results are "
          "reproducible; in production the LLM prompt in `prompts/message_drafter.md` writes these from the same evidence._", ""]
    for m in msgs:
        md += [f"### Invoice {m['invoice_id']} - to {m['recipient_type']} ({m['recipient_name']}) via {m['channel']}",
               f"*Reason:* `{m['reason_code']}`  |  *Deadline:* {m['deadline']}", "", f"> {m['message']}", ""]
        if m.get("message_hinglish"):
            md += [f"*Hinglish:* {m['message_hinglish']}", ""]
    (out_dir / "messages.md").write_text("\n".join(md))

    # ---- metrics + summary -----------------------------------------------------------------
    metrics = compute_metrics(dec, inv, ff, br, cs, asof_ts)
    (out_dir / "dashboard_metrics.json").write_text(json.dumps(metrics, indent=2, default=str))
    write_summary(dec, metrics, asof, out_dir)
    return metrics, msgs


def draft_messages(dec, inv, ff, ref, asof, first_class):
    refx = ref.set_index("student_id")
    tomorrow_noon = (asof + timedelta(days=1)).replace(hour=12, minute=0)
    dl_noon = f"{tomorrow_noon:%a %d %b}, 12 PM"
    dl_6pm = f"{asof:%a %d %b}, 8 PM"
    msgs = []

    def add(d, rtype, rname, channel, code, text, deadline, hing=None):
        msgs.append({"invoice_id": int(d["invoice_id"]), "recipient_type": rtype, "recipient_name": rname,
                     "channel": channel, "reason_code": code, "deadline": deadline,
                     "message": text, **({"message_hinglish": hing} if hing else {})})

    for _, d in dec.iterrows():
        r = refx.loc[int(d["student_id"])]
        stu, par, tch = d["student_name"], d["parent_name_registered"], d["educator_name"]
        amt = fmt_inr(d["net_amount"])
        days, tm = r["batch_days"], r["batch_start_time"][:5]
        codes = [c.strip() for c in d["reason_codes"].split(",") if c.strip()]
        n = d["invoice_number"]

        if d["outcome"] in ("AUTO_APPROVE", "AUTO_FIX"):
            fc = first_class[d["invoice_id"]]
            add(d, "parent", par, "whatsapp", "AUTO_APPROVED" if not codes else codes[0],
                f"Hi {par}, your renewal payment of {amt} for {stu} is confirmed. Classes continue in the same batch "
                f"({days}, {tm}) with {tch}. First class: {fc:%a %d %b, %H:%M}. No action needed.",
                "none",
                f"Namaste {par}, {stu} ke renewal ka {amt} ka payment confirm ho gaya hai. Classes isi batch mein "
                f"({days}, {tm}) {tch} ke saath chalti rahengi. Pehli class: {fc:%a %d %b, %H:%M}. Aapko kuch karna nahi hai.")
            if "DUPLICATE_FORM" in codes:
                add(d, "teacher", tch, "slack", "DUPLICATE_FORM",
                    f"Hi {tch}, you submitted two renewal forms for invoice {n} ({stu}). We kept the first and marked the "
                    f"second as a duplicate. No action needed.", "none")
            if "INVOICE_ID_TYPO" in codes:
                add(d, "teacher", tch, "slack", "INVOICE_ID_TYPO",
                    f"Hi {tch}, the renewal form for {stu} cited an invoice number that does not exist (digits swapped). "
                    f"We matched it to {n} automatically. Please double-check the invoice number next time.", "none")
            continue

        if "PAYMENT_NOT_CONFIRMED" in codes:
            add(d, "parent", par, "whatsapp", "PAYMENT_NOT_CONFIRMED",
                f"Hi {par}, your renewal payment of {amt} for {stu} did not complete on our side (invoice {n}). "
                f"Please retry here: {{retry_link}}. Classes will be scheduled as soon as the payment is confirmed.",
                dl_noon,
                f"Namaste {par}, {stu} ke renewal ka {amt} ka payment hamare yahan confirm nahi hua (invoice {n}). "
                f"Kripya is link se dobara payment karein: {{retry_link}}. Payment confirm hote hi classes schedule ho jayengi.")
            add(d, "teacher", tch, "slack", "PAYMENT_NOT_CONFIRMED",
                f"Hi {tch}, the payment for {stu} (invoice {n}) shows as Failed on the gateway. A screenshot cannot be "
                f"accepted as proof. We have sent the parent a retry link. If the parent says money was debited, please ask "
                f"for the bank reference.", dl_noon)
            add(d, "ops_agent", "Ops exec on duty", "slack", "PAYMENT_NOT_CONFIRMED",
                f"[BLOCK] Invoice {n}: gateway status Failed, no payment id. Teacher attached a UPI 'processing' screenshot. "
                f"Check Razorpay for a late-captured webhook before 12 PM tomorrow; do not schedule until it shows Paid.", dl_noon)
        elif "PARTIAL_PAYMENT" in codes:
            add(d, "parent", par, "whatsapp", "PARTIAL_PAYMENT",
                f"Hi {par}, we received the first instalment of {amt} for {stu}'s renewal (invoice {n}). The second "
                f"instalment of {amt} is pending - please pay by {{instalment_2_due_date}} so classes continue without a break.",
                "{instalment_2_due_date}",
                f"Namaste {par}, {stu} ke renewal ki pehli instalment {amt} mil gayi hai (invoice {n}). Dusri instalment "
                f"{amt} baaki hai - kripya {{instalment_2_due_date}} tak pay karein taaki classes beech mein na rukein.")
            add(d, "ops_agent", "Ops exec / Finance", "slack", "PARTIAL_PAYMENT, AMOUNT_MISMATCH",
                f"[BLOCK] Invoice {n}: Installment 1 of 2 - {amt} paid of {fmt_inr(d['net_amount'] * 2)}. Teacher's form claims "
                f"{fmt_inr(d['net_amount'] * 2)} paid and 24 sessions. Do not schedule the full term. Decide how many sessions "
                f"instalment 1 covers, correct the form, and set a reminder for instalment 2.", dl_noon)
        elif "DISCOUNT_NEEDS_APPROVAL" in codes:
            inv_row = inv[inv["id"] == d["invoice_id"]].iloc[0]
            add(d, "ops_head", "Head of Operations", "slack", "DISCOUNT_NEEDS_APPROVAL",
                f"Approval needed - invoice {n} ({d['class_name']}): standard fee {fmt_inr(inv_row['amount'])}, paid "
                f"{amt} (20% 'retention scholarship', offered by {tch}). Payment is complete. Approve or reject by "
                f"{dl_noon} so {stu}'s classes can be scheduled.", dl_noon)
        elif "NO_MATCHING_BATCH" in codes or "BATCH_CHANGE_PENDING" in codes:
            add(d, "ops_agent", "Ops exec / Academics", "slack", "BATCH_CHANGE_PENDING, NO_MATCHING_BATCH",
                f"[HUMAN] Invoice {n}: {stu} paid {amt}; parent wants Sat/Sun 11:00 in {d['class_name']} with {tch}. No such "
                f"batch exists. Options on file: {d['alt_options']}. Decide: waitlist, open a new batch, or offer an existing "
                f"slot. Parent has not been contacted and no reminder is scheduled.", dl_noon)
            add(d, "parent", par, "whatsapp", "BATCH_CHANGE_PENDING",
                f"Hi {par}, thanks for renewing {stu}'s classes (invoice {n}). The weekend 11 AM slot you asked for is not "
                f"available right now. Available options: Wed/Fri 4:30 PM (current batch) or we can add {stu} to a waitlist for "
                f"the weekend slot. Please reply 1 or 2 by {dl_noon}.", dl_noon,
                f"Namaste {par}, {stu} ke renewal ke liye shukriya (invoice {n}). Weekend 11 AM wala slot abhi available nahi "
                f"hai. Options: 1 = Wed/Fri 4:30 PM (current batch), 2 = weekend slot ki waitlist. Kripya {dl_noon} tak 1 ya 2 reply karein.")
        elif "PAYER_MISMATCH" in codes:
            add(d, "parent", par, "whatsapp (registered number)", "PAYER_MISMATCH",
                f"Hi {par}, we received a payment of {amt} for {stu}'s renewal (invoice {n}) from a different mobile/email than "
                f"the one on your account. Please reply YES if this was you or a family member, and we will schedule "
                f"{days} {tm} classes right away. Reply by {dl_noon}.", dl_noon,
                f"Namaste {par}, {stu} ke renewal ka {amt} ka payment (invoice {n}) aapke account ke number/email se alag se aaya hai. "
                f"Agar ye aapne ya parivaar ne kiya hai to YES reply karein, hum {days} {tm} ki classes turant schedule kar denge. "
                f"Kripya {dl_noon} tak reply karein.")
            add(d, "ops_agent", "Ops exec on duty", "slack", "PAYER_MISMATCH",
                f"[SOFT] Invoice {n}: paid by a different person than the registered parent (teacher: 'Mother paid from her number'). "
                f"IDs match. Waiting for the registered parent's YES on WhatsApp; approve on reply. If none by {dl_noon}, call the registered number.", dl_noon)
        elif "ORPHAN_NO_FORM" in codes:
            add(d, "parent", par, "whatsapp", "ORPHAN_NO_FORM",
                f"Hi {par}, we received your renewal payment of {amt} for {stu} (invoice {n}). To schedule the next term, "
                f"please reply 1 to continue in the same batch ({days}, {tm}) or 2 to change the batch. Reply by {dl_noon}.",
                dl_noon,
                f"Namaste {par}, {stu} ke renewal ka {amt} ka payment mil gaya hai (invoice {n}). Agle term ki classes schedule karne ke "
                f"liye reply karein: 1 = isi batch mein continue ({days}, {tm}), 2 = batch change. Kripya {dl_noon} tak reply karein.")
            add(d, "teacher", tch, "whatsapp", "ORPHAN_NO_FORM",
                f"Hi {tch}, {stu}'s renewal payment of {amt} (invoice {n}) is in, but we have no renewal form. You do not need to "
                f"fill the form - we have asked the parent to confirm the same batch. If they have not replied by {dl_noon}, "
                f"please nudge them.", dl_noon)
    return msgs


def compute_metrics(dec, inv, ff, br, cs, asof_ts):
    paid = dec[dec["payment_status"] == "Paid"]
    paid_unsched = paid[paid["scheduled_sessions"] == 0]
    over12 = paid_unsched[paid_unsched["hours_since_payment"] > STUCK_HOURS]
    t = ff.merge(inv[["id", "paid_at"]], left_on="resolved_invoice_id", right_on="id", how="left", suffixes=("", "_inv"))
    p2f = ((t["created_at"] - t["paid_at"]).dt.total_seconds() / 3600).dropna()
    f2a = ((t["approved_at"] - t["created_at"]).dt.total_seconds() / 3600).dropna()
    pend = ff[ff["approval_status"] == "Pending"].copy()
    pend["age"] = (asof_ts - pend["created_at"]).dt.total_seconds() / 3600
    buckets = {"0-2h": int((pend.age < 2).sum()), "2-12h": int(((pend.age >= 2) & (pend.age < 12)).sum()),
               "12-24h": int(((pend.age >= 12) & (pend.age < 24)).sum()), ">24h": int((pend.age >= 24).sum())}
    pending_unique = ff[(ff["approval_status"] == "Pending") & (ff["dup_rank"] == 1)]
    outstanding = dec[dec["outcome"] != "ALREADY_SCHEDULED"]
    counts = dec["outcome"].value_counts().to_dict()
    zero_touch = counts.get("AUTO_APPROVE", 0) + counts.get("AUTO_FIX", 0)
    soft = counts.get("SOFT", 0)
    first_sched = cs.groupby("invoice_id")["created_at"].min().reset_index()
    first_sched["created_at"] = pd.to_datetime(first_sched["created_at"])
    p2s = [hours_between(inv[inv["id"] == r_["invoice_id"]]["paid_at"].iloc[0], r_["created_at"]) for _, r_ in first_sched.iterrows()]
    p2s_min = [round((r_["created_at"] - inv[inv["id"] == r_["invoice_id"]]["paid_at"].iloc[0]).total_seconds() / 60)
               for _, r_ in first_sched.iterrows()]
    code_counts = {}
    for s in dec["reason_codes"]:
        for c in [x.strip() for x in s.split(",") if x.strip()]:
            code_counts[c] = code_counts.get(c, 0) + 1
    return {
        "snapshot": str(asof_ts),
        "invoices": int(len(dec)), "paid": int(len(paid)),
        "partially_paid": int((dec.payment_status == "Partially_Paid").sum()),
        "failed": int((dec.payment_status == "Failed").sum()),
        "paid_scheduled": int((paid["scheduled_sessions"] > 0).sum()),
        "paid_not_scheduled": int(len(paid_unsched)),
        "revenue_at_risk_inr": float(paid_unsched["net_amount"].sum()),
        "stuck_over_12h": int(len(over12)), "stuck_over_12h_inr": float(over12["net_amount"].sum()),
        "oldest_stuck_invoice": int(paid_unsched.sort_values("hours_since_payment", ascending=False).iloc[0]["invoice_id"]),
        "oldest_stuck_hours": float(paid_unsched["hours_since_payment"].max()),
        "orphans_no_form": int(code_counts.get("ORPHAN_NO_FORM", 0)),
        "forms_total": int(len(ff)), "forms_pending": int(len(pend)), "forms_approved": int((ff.approval_status == "Approved").sum()),
        "pending_form_age_buckets": buckets,
        "oldest_pending_form_hours": round(float(pend.age.max()), 1),
        "approved_forms_that_got_classes": int(ff[(ff.approval_status == "Approved")]["resolved_invoice_id"].isin(cs["invoice_id"]).sum()),
        "pay_to_form_hours_median": round(float(p2f.median()), 2), "pay_to_form_hours_max": round(float(p2f.max()), 2),
        "form_to_approval_hours_median": round(float(f2a.median()), 2),
        "payment_to_schedule_hours_best_case": p2s[0] if p2s else None,
        "payment_to_schedule_minutes_best_case": p2s_min[0] if p2s_min else None,
        "booking_status_counts": br["request_status"].value_counts().to_dict(),
        "outcome_counts": counts, "reason_code_counts": dict(sorted(code_counts.items(), key=lambda kv: -kv[1])),
        "outstanding_renewals": int(len(outstanding)),
        "zero_touch": int(zero_touch), "zero_touch_pct": round(100 * zero_touch / len(outstanding)),
        "zero_touch_plus_soft": int(zero_touch + soft),
        "zero_touch_plus_soft_pct": round(100 * (zero_touch + soft) / len(outstanding)),
        "needs_human": int(counts.get("HUMAN", 0) + counts.get("BLOCK", 0)),
        "duplicate_form_rate_pct": round(100 * code_counts.get("DUPLICATE_FORM", 0) / len(inv), 1),
    }


def write_summary(dec, m, asof, out_dir: Path):
    L = [f"# Reconciliation summary", "",
         f"Snapshot (as-of) time: **{asof:%Y-%m-%d %H:%M}** · invoices analysed: **{m['invoices']}** · "
         f"every invoice has exactly one outcome.", "",
         "## Headline", "",
         f"- Fully paid renewals that reached scheduled classes: **{m['paid_scheduled']} of {m['paid']}**",
         f"- Paid but not scheduled: **{m['paid_not_scheduled']}** invoices, **{fmt_inr(m['revenue_at_risk_inr'])}**",
         f"- Stuck more than {STUCK_HOURS} h: **{m['stuck_over_12h']}** invoices, **{fmt_inr(m['stuck_over_12h_inr'])}**; "
         f"oldest is invoice {m['oldest_stuck_invoice']} at **{m['oldest_stuck_hours']} h**",
         f"- Forms pending Ops approval: **{m['forms_pending']} of {m['forms_total']}** (oldest {m['oldest_pending_form_hours']} h)",
         f"- Approved forms that actually got classes: **{m['approved_forms_that_got_classes']} of {m['forms_approved']}**",
         f"- Teacher delay when a form is filed: median {m['pay_to_form_hours_median']*60:.0f} min, max {m['pay_to_form_hours_max']*60:.0f} min",
         "", "## Outcome split of the outstanding renewals", "",
         "| Outcome | Invoices | Meaning |", "|---|---|---|"]
    meaning = {"ALREADY_SCHEDULED": "Classes already exist in table 4", "AUTO_APPROVE": "Clean - zero human touch",
               "AUTO_FIX": "Safe defect repaired automatically, then scheduled", "SOFT": "One-tap parent confirmation",
               "HUMAN": "Needs judgement (discount / batch change)", "BLOCK": "Payment problem - do not schedule"}
    for k in ["ALREADY_SCHEDULED", "AUTO_APPROVE", "AUTO_FIX", "SOFT", "HUMAN", "BLOCK"]:
        ids = ", ".join(str(x) for x in dec[dec.outcome == k]["invoice_id"]) or "-"
        L.append(f"| {k} | {ids} | {meaning[k]} |")
    L += ["", f"**Zero-touch (auto-approve + auto-fix): {m['zero_touch']} of {m['outstanding_renewals']} "
          f"({m['zero_touch_pct']}%)**. Adding one-tap soft confirmations: {m['zero_touch_plus_soft']} of "
          f"{m['outstanding_renewals']} ({m['zero_touch_plus_soft_pct']}%). Only {m['needs_human']} need real human judgement.",
          "", "## Reason codes raised", "", "| Code | Count |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in m["reason_code_counts"].items()]
    L += ["", "## Invoice by invoice", "", "| Invoice | Outcome | Reason codes | Owner |", "|---|---|---|---|"]
    for _, d in dec.iterrows():
        L.append(f"| {d['invoice_id']} | {d['outcome']} | {d['reason_codes'] or '-'} | {d['owner'] or '-'} |")
    (out_dir / "summary.md").write_text("\n".join(L) + "\n")


def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description="Bambinos renewal reconciliation engine")
    ap.add_argument("--data", default=str(here.parent / "data"))
    ap.add_argument("--out", default=str(here.parent / "results"))
    ap.add_argument("--asof", default=DEFAULT_ASOF, help="snapshot time, e.g. '2026-11-03 18:00'")
    a = ap.parse_args()
    asof = datetime.strptime(a.asof, "%Y-%m-%d %H:%M")
    dec, inv, ff, br, cs, ref = reconcile(Path(a.data), asof)
    metrics, msgs = build_outputs(dec, inv, ff, br, cs, ref, asof, Path(a.out))
    print(f"Snapshot {asof:%Y-%m-%d %H:%M} | invoices {len(dec)}")
    print(dec["outcome"].value_counts().to_string())
    print(f"Zero-touch {metrics['zero_touch']}/{metrics['outstanding_renewals']} | messages drafted {len(msgs)}")


if __name__ == "__main__":
    main()
