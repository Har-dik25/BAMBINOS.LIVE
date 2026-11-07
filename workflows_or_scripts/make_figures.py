#!/usr/bin/env python3
"""Generates the diagrams used in Case_Report.pdf and the dashboard mock-up.
Numbers are read from results/dashboard_metrics.json so the pictures always match the engine output.
Requires: matplotlib."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parent.parent
M = json.loads((ROOT / "results" / "dashboard_metrics.json").read_text())
OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
(ROOT / "dashboard").mkdir(exist_ok=True)

NAVY, BLUE, GREEN, AMBER, ORANGE, RED, GREY, LIGHT = "#1F3864", "#2E75B6", "#4E9A3A", "#E0A800", "#ED7D31", "#C00000", "#7F7F7F", "#F2F5FA"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})


def box(ax, x, y, w, h, text, fc="white", ec=NAVY, tc=NAVY, fs=9.5, bold=False, lw=1.6, style="round,pad=0.02,rounding_size=0.12"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=style, fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc, fontsize=fs, fontweight="bold" if bold else "normal", wrap=True)


def arrow(ax, p, q, color=NAVY, lw=1.8, style="-|>", ls="-", cs="arc3"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=14, color=color, lw=lw, linestyle=ls, connectionstyle=cs))


def canvas(w, h, xl, yl):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xl); ax.set_ylim(0, yl); ax.axis("off")
    return fig, ax


# ------------------------------------------------------------------------------ 1. current flow with leaks
fig, ax = canvas(13, 6.2, 13, 6.2)
ax.text(0.1, 5.9, "TODAY: four tables, three manual handoffs, and a leak at every step", fontsize=13, fontweight="bold", color=NAVY)
steps = [("1. invoices", "Parent pays the link", "Owner: Parent / gateway"),
         ("2. faculty_form_unapproved", "Teacher re-types\ninvoice data", "Owner: Teacher"),
         ("3. booking_requests", "Ops checks and\napproves by hand", "Owner: Ops team"),
         ("4. class_schedule_bookings", "Batch / days / time\nchosen", "Owner: Parent / Ops")]
W, G = 2.95, 0.35
xs = [0.1 + k * (W + G) for k in range(4)]
for (t, d, o), x in zip(steps, xs):
    box(ax, x, 3.8, W, 1.5, f"{t}\n{d}\n{o}", fc=LIGHT, fs=8.6)
for a_, b_ in zip(xs[:-1], xs[1:]):
    arrow(ax, (a_ + W + 0.02, 4.55), (b_ - 0.02, 4.55))
leaks = [
    f"{M['paid']} paid renewals,\nonly {M['paid_scheduled']} scheduled\n(Rs {M['revenue_at_risk_inr']:,.0f} waiting)",
    "Paid, no form: 84906, 84910\nWrong invoice no.: 84913\n(typed as 84931)\nDuplicate forms: 84908",
    f"{M['forms_pending']} of {M['forms_total']} forms still pending\n(oldest {M['oldest_pending_form_hours']:.1f} h)\nDiscount / payer checks\ndone by eye",
    "3 of 4 approved forms\nstill have NO classes:\nstuck, 'batch full',\nawaiting parent",
]
for x, t in zip(xs, leaks):
    arrow(ax, (x + W / 2, 3.75), (x + W / 2, 3.0), color=RED, lw=1.6)
    box(ax, x, 1.45, W, 1.5, t, fc="#FDECEC", ec=RED, tc="#7A0000", fs=8.6)
ax.text(0.1, 0.95, "Root causes", fontsize=10.5, fontweight="bold", color=NAVY)
ax.text(0.1, 0.5, "Steps 2 and 3 re-type and re-check data the invoice already holds  |  failed states have no retry, alert or owner  |  free-text remarks are never read",
        fontsize=8.8, color="#333333")
ax.text(0.1, 0.12, "Capacity check double-counts the student's own seat  |  no orphan detection (paid, no form is invisible)  |  no owner or timer on any stuck record",
        fontsize=8.8, color="#333333")
fig.savefig(OUT / "fig_current_flow.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# ------------------------------------------------------------------------------ 2. target flow
fig, ax = canvas(13, 7.2, 13, 7.2)
ax.text(0.1, 6.95, "TARGET: zero-touch for clean renewals, one owner per exception", fontsize=13, fontweight="bold", color=NAVY)
box(ax, 0.1, 5.55, 3.35, 1.0, "Teacher creates the payment link\nfrom a Renewal Intent (student,\nbatch, sessions, discount code)", fc=LIGHT, fs=8.4)
box(ax, 3.85, 5.55, 2.6, 1.0, "Parent pays\nRazorpay / Stripe\nwebhook: captured", fc=LIGHT, fs=8.4)
box(ax, 6.85, 5.55, 2.8, 1.0, "RULES ENGINE\n12 ordered checks\n(Checks tab / reconcile.py)", fc="#E4EEF9", ec=BLUE, tc=NAVY, bold=True, fs=8.6)
box(ax, 10.05, 5.55, 2.85, 1.0, "Sweep every 15 min:\norphans, stuck bookings,\nduplicates", fc="#FFF4D6", ec=AMBER, fs=8.4)
arrow(ax, (3.47, 6.05), (3.83, 6.05)); arrow(ax, (6.47, 6.05), (6.83, 6.05)); arrow(ax, (10.03, 6.05), (9.67, 6.05), color=AMBER, ls="--")
# column headers (bands)
ax.add_patch(Rectangle((0.1, 4.75), 6.1, 0.42, fc=GREEN, ec=GREEN))
ax.text(0.25, 4.96, "HAPPY PATH: about 42% of the sample is zero-touch", color="white", fontsize=8.8, fontweight="bold", va="center")
ax.add_patch(Rectangle((6.8, 4.75), 6.1, 0.42, fc=RED, ec=RED))
ax.text(6.95, 4.96, "EXCEPTIONS: code, ONE owner, message, SLA timer", color="white", fontsize=8.8, fontweight="bold", va="center")
arrow(ax, (7.6, 5.52), (3.3, 5.2), color=GREEN, lw=2)
arrow(ax, (8.9, 5.52), (9.85, 5.2), color=RED, lw=2)
happy = ["1   Webhook confirms payment; every check passes (or is safely auto-fixed)",
         "2   Auto-create booking_request + class_schedule_bookings (same batch)",
         "3   WhatsApp confirmation to parent with first class date; FYI to teacher",
         "4   Dashboard: auto-approved +1, hours saved"]
for k, t in enumerate(happy):
    y = 3.95 - k * 0.92
    box(ax, 0.1, y, 6.1, 0.68, t, fc="#E8F5E2", ec=GREEN, tc="#1E5F10", fs=7.9)
    if k < 3:
        arrow(ax, (3.15, y - 0.01), (3.15, y - 0.22), color=GREEN, lw=1.4)
ex = [("SOFT\nOrphan / payer mismatch", "Parent confirms with one tap;\nteacher is notified", AMBER),
      ("HUMAN\nDiscount / batch change", "One named Ops owner decides;\nparent receives the options", ORANGE),
      ("BLOCK\nFailed / partial payment", "Retry link or instalment plan;\nnever approve on a screenshot", RED)]
for k, (t, d, c) in enumerate(ex):
    y = 3.72 - k * 1.18
    box(ax, 6.8, y, 2.7, 0.95, t, fc="white", ec=c, tc="#333333", fs=8.4, bold=True)
    arrow(ax, (9.52, y + 0.47), (9.82, y + 0.47), color=c)
    box(ax, 9.84, y, 3.06, 0.95, d, fc="white", ec=c, tc="#333333", fs=8.2)
ax.text(0.1, 0.45, "Safety nets: idempotency key = invoice_id  |  audit log of every decision  |  kill switch back to manual  |  shadow mode before go-live",
        fontsize=9, color="#333333")
fig.savefig(OUT / "fig_target_flow.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# ------------------------------------------------------------------------------ 3. leakage funnel
fig, ax = plt.subplots(figsize=(8.6, 3.9))
labels = ["Paid renewals", "Teacher form on file", "Form approved by Ops", "Classes scheduled"]
vals = [M["paid"], 9, M["forms_approved"], M["paid_scheduled"]]
cols = [NAVY, BLUE, AMBER, GREEN]
y = range(len(vals))[::-1]
ax.barh(list(y), vals, color=cols, height=0.62)
for yy, v in zip(y, vals):
    ax.text(v + 0.15, yy, str(v), va="center", fontweight="bold", color="#333333")
ax.set_yticks(list(y)); ax.set_yticklabels(labels)
ax.set_xlim(0, 12.5); ax.set_xlabel("Number of invoices (sample of 11 fully paid renewals)")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.set_title(f"Only {M['paid_scheduled']} of {M['paid']} paid renewals reached scheduled classes", loc="left", fontweight="bold", color=NAVY)
ax.text(12.4, 1.0, "11 paid minus 84906 and 84910 (no form at all).\n84913 counts as 'on file' but its form cites the wrong invoice no.\n3 of the 4 approved forms still have no classes.", fontsize=8, ha="right", va="center", color=GREY)
fig.savefig(OUT / "fig_leakage_funnel.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# ------------------------------------------------------------------------------ 4. outcome split
fig, ax = plt.subplots(figsize=(8.6, 3.4))
oc = M["outcome_counts"]
parts = [("Zero-touch\n(auto-approve + auto-fix)", oc.get("AUTO_APPROVE", 0) + oc.get("AUTO_FIX", 0), GREEN),
         ("One-tap confirm\n(soft)", oc.get("SOFT", 0), AMBER), ("Needs judgement\n(human)", oc.get("HUMAN", 0), ORANGE),
         ("Payment problem\n(block)", oc.get("BLOCK", 0), RED)]
left = 0
for t, v, c in parts:
    ax.barh(0, v, left=left, color=c, height=0.55, edgecolor="white")
    ax.text(left + v / 2, 0, str(v), ha="center", va="center", color="white", fontweight="bold", fontsize=13)
    ax.text(left + v / 2, -0.52, t, ha="center", va="top", fontsize=8.5, color="#333333")
    left += v
ax.set_xlim(0, left); ax.set_ylim(-1.2, 0.7); ax.axis("off")
ax.set_title(f"What the engine does with the {left} outstanding renewals", loc="left", fontweight="bold", color=NAVY)
fig.savefig(OUT / "fig_outcome_split.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# ------------------------------------------------------------------------------ 5. dashboard mock-up
fig = plt.figure(figsize=(13, 8.2), facecolor="#F4F6FA")
fig.text(0.02, 0.965, "Bambinos Renewals - Ops Head morning view", fontsize=15, fontweight="bold", color=NAVY)
fig.text(0.02, 0.935, f"As of {M['snapshot'][:16]} IST  |  stuck threshold 12 h  |  sample data (13 invoices)", fontsize=9, color=GREY)
kpis = [("Paid, not scheduled", f"{M['paid_not_scheduled']}", RED), ("Revenue at risk", f"Rs {M['revenue_at_risk_inr']:,.0f}", RED),
        ("Stuck > 12 h", f"{M['stuck_over_12h']}  (Rs {M['stuck_over_12h_inr']:,.0f})", ORANGE), ("Forms pending", f"{M['forms_pending']} of {M['forms_total']}", ORANGE),
        ("Zero-touch share", f"{M['zero_touch_pct']}%", GREEN), ("Hours saved / wk*", "12.5", GREEN)]
kax = fig.add_axes([0.02, 0.80, 0.96, 0.115]); kax.set_xlim(0, 6); kax.set_ylim(0, 1); kax.axis("off")
for k, (t, v, c) in enumerate(kpis):
    kax.add_patch(FancyBboxPatch((k + 0.04, 0.04), 0.92, 0.92, boxstyle="round,pad=0.01,rounding_size=0.05", fc="white", ec=c, lw=2))
    kax.text(k + 0.5, 0.68, v, ha="center", va="center", fontsize=14 if len(v) < 12 else 11, fontweight="bold", color=c)
    kax.text(k + 0.5, 0.25, t, ha="center", va="center", fontsize=8.5, color="#333333")
# stuck table
tax = fig.add_axes([0.02, 0.38, 0.58, 0.39]); tax.axis("off"); tax.set_xlim(0, 10); tax.set_ylim(0, 8)
tax.text(0, 7.6, "STUCK INVOICES > 12 h (owner, reason, hours, next action)", fontsize=10, fontweight="bold", color=NAVY)
rows = [("84902", "Rs 10,500", "Automation", "STUCK_AT_ALLOCATION", "51.7", "auto-fix"), ("84903", "Rs 9,000", "Automation", "pending approval", "32.9", "auto-approve"),
        ("84904", "Rs 12,000", "Parent+Ops", "PAYER_MISMATCH", "30.5", "confirm"), ("84905", "Rs 11,000", "Automation", "FALSE_BATCH_FULL", "28.8", "auto-fix"),
        ("84906", "Rs 18,000", "Parent+Tchr", "ORPHAN_NO_FORM", "26.0", "confirm"), ("84907", "Rs 7,600", "Ops lead", "DISCOUNT_NEEDS_APPR.", "23.2", "approve")]
hdr = ["Invoice", "Amount", "Owner", "Reason", "Hrs", "Action"]
cx = [0, 1.3, 2.9, 4.4, 7.0, 8.0]
for h, x in zip(hdr, cx):
    tax.text(x, 6.7, h, fontsize=8.5, fontweight="bold", color="white", bbox=dict(fc=NAVY, ec=NAVY, pad=2))
for i, rw in enumerate(rows):
    yy = 5.6 - i * 0.95
    tax.add_patch(Rectangle((-0.1, yy - 0.4), 10.1, 0.85, fc="white" if i % 2 else "#EAF1FB", ec="none"))
    for v, x in zip(rw, cx):
        col = RED if (x == 7.0 and float(rw[4]) > 30) else "#222222"
        tax.text(x, yy, v, fontsize=8.5, color=col, va="center")
# forms age
fax = fig.add_axes([0.66, 0.43, 0.32, 0.30])
b = M["pending_form_age_buckets"]
fax.bar(list(b.keys()), list(b.values()), color=[GREEN, BLUE, AMBER, RED])
for i, v in enumerate(b.values()):
    fax.text(i, v + 0.1, str(v), ha="center", fontweight="bold")
fax.set_title("Pending forms by age", loc="left", fontsize=10, fontweight="bold", color=NAVY)
for s in ("top", "right"):
    fax.spines[s].set_visible(False)
fax.set_ylim(0, max(b.values()) + 1.2)
# reason codes
rax = fig.add_axes([0.02, 0.05, 0.40, 0.28])
rc = {k: v for k, v in M["reason_code_counts"].items() if k != "SESSIONS_UNDER_SCHEDULED"}
names, vals = list(rc.keys())[::-1], list(rc.values())[::-1]
rax.barh(names, vals, color=BLUE)
rax.set_title("Exceptions by reason code", loc="left", fontsize=10, fontweight="bold", color=NAVY)
rax.tick_params(axis="y", labelsize=7.5); rax.set_xticks([0, 1, 2])
for s in ("top", "right"):
    rax.spines[s].set_visible(False)
# booking status + SLA
sax = fig.add_axes([0.50, 0.05, 0.22, 0.28])
bs = {"Pending\nallocation": 1, "Failed\nbatch full": 1, "Awaiting\nparent": 1, "Completed": 1}
sax.bar(list(bs.keys()), list(bs.values()), color=[ORANGE, RED, AMBER, GREEN])
sax.set_title("Booking requests by status", loc="left", fontsize=10, fontweight="bold", color=NAVY)
sax.tick_params(axis="x", labelsize=7.5); sax.set_ylim(0, 1.6); sax.set_yticks([0, 1])
for s in ("top", "right"):
    sax.spines[s].set_visible(False)
tx = fig.add_axes([0.76, 0.05, 0.22, 0.28]); tx.axis("off"); tx.set_xlim(0, 1); tx.set_ylim(0, 1)
tx.text(0, 0.95, "Turnaround vs SLA", fontsize=10, fontweight="bold", color=NAVY, va="top")
tx.text(0, 0.72, f"Payment to schedule\nbest case today: {M['payment_to_schedule_minutes_best_case'] // 60} h {M['payment_to_schedule_minutes_best_case'] % 60} min\nSLA: 2 h (clean renewals)", fontsize=9, va="top")
tx.text(0, 0.38, f"Teacher form delay (median)\n{M['pay_to_form_hours_median'] * 60:.0f} min  - OK", fontsize=9, va="top", color=GREEN)
tx.text(0, 0.10, "* illustrative: 300 renewals/wk x 42% x 6 min", fontsize=7.5, va="top", color=GREY)
fig.savefig(ROOT / "dashboard" / "ops_head_dashboard_mockup.png", dpi=170, bbox_inches="tight", facecolor=fig.get_facecolor())
fig.savefig(OUT / "fig_dashboard.png", dpi=170, bbox_inches="tight", facecolor=fig.get_facecolor()); plt.close(fig)

# ------------------------------------------------------------------------------ 6. rollout timeline
fig, ax = canvas(13, 4.6, 13, 4.6)
ax.text(0.1, 4.3, "Rollout: never break live classes - shadow first, kill switch always on", fontsize=13, fontweight="bold", color=NAVY)
phases = [("Days 1-30\nSHADOW", "Engine runs beside manual process\nOps still approves everything\nBaseline 3 months of data\nExit: >=95% agreement, 0 wrong approvals", BLUE),
          ("Days 31-60\nPILOT", "Auto-approve cleanest renewals for\n1-2 categories / ~20 teachers\nWhatsApp messages live\nExit: SLA met, no parent complaints", AMBER),
          ("Days 61-90\nSCALE", "All 200+ teachers in cohorts\nIntent-based link replaces the form\nOrphan sweep + SLA alerts live\nExit: auto-approval rate stable", GREEN)]
for k, (t, d, c) in enumerate(phases):
    x = 0.2 + k * 4.3
    ax.add_patch(FancyBboxPatch((x, 3.0), 4.0, 0.9, boxstyle="round,pad=0.02,rounding_size=0.1", fc=c, ec=c))
    ax.text(x + 2.0, 3.45, t, ha="center", va="center", color="white", fontweight="bold", fontsize=11)
    box(ax, x, 0.55, 4.0, 2.2, d, fc="white", ec=c, tc="#222222", fs=9)
    if k < 2:
        arrow(ax, (x + 4.02, 3.45), (x + 4.28, 3.45), color=NAVY)
ax.text(0.2, 0.15, "Gate between phases: Head of Ops sign-off on the dashboard numbers. Rollback = flip the kill switch; manual process is never retired until day 90.",
        fontsize=9, color="#333333")
fig.savefig(OUT / "fig_rollout.png", dpi=200, bbox_inches="tight"); plt.close(fig)
print("figures written to", OUT)
