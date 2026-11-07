#!/usr/bin/env python3
"""
Builds Renewal_Reconciliation_Sheet.xlsx - the NO-CODE prototype.

Every rule is a plain spreadsheet formula (COUNTIF / INDEX / MATCH / SUMPRODUCT / TEXTJOIN),
so Ops can read, audit and tweak it without programming. Upload the .xlsx to Google Drive and
open with Google Sheets; all formulas are Sheets-compatible.

This script only *generates* the workbook. You do not need to run it to use the sheet.
Requires: pandas, openpyxl.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.comments import Comment

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reconcile import CONFUSABLES, DEFAULT_ASOF  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "data"
OUT = HERE / "Renewal_Reconciliation_Sheet.xlsx"

FONT = "Arial"
F_BASE = Font(name=FONT, size=10)
F_BOLD = Font(name=FONT, size=10, bold=True)
F_HEAD = Font(name=FONT, size=10, bold=True, color="FFFFFF")
F_TITLE = Font(name=FONT, size=16, bold=True, color="1F3864")
F_H2 = Font(name=FONT, size=12, bold=True, color="1F3864")
F_INPUT = Font(name=FONT, size=10, color="0000FF", bold=True)       # blue = hard-coded input
F_LINK = Font(name=FONT, size=10, color="008000")                   # green = cross-sheet link
F_NOTE = Font(name=FONT, size=9, italic=True, color="595959")
FILL_HEAD = PatternFill("solid", fgColor="1F3864")
FILL_CALC = PatternFill("solid", fgColor="DDEBF7")
FILL_INPUT = PatternFill("solid", fgColor="FFFF00")
FILL_SEC = PatternFill("solid", fgColor="F2F2F2")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
DT = "yyyy-mm-dd hh:mm"

SEV_COLORS = {"AUTO_APPROVE": "C6EFCE", "AUTO_FIX": "E2EFDA", "ALREADY_SCHEDULED": "D9D9D9",
              "SOFT": "FFEB9C", "HUMAN": "F8CBAD", "BLOCK": "FFC7CE"}

wb = Workbook()


# ----------------------------------------------------------------------------- helpers
def clean(v):
    if v is None:
        return None
    if isinstance(v, float):
        if pd.isna(v):
            return None
        return int(v) if v.is_integer() else v
    if isinstance(v, pd.Timestamp):
        return None if pd.isna(v) else v.to_pydatetime()
    if v is pd.NaT:
        return None
    return v


def write_df(ws, df, dt_cols=(), date_cols=()):
    for c, name in enumerate(df.columns, 1):
        cell = ws.cell(row=1, column=c, value=name)
        cell.font, cell.fill, cell.border = F_HEAD, FILL_HEAD, BORDER
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for r, row in enumerate(df.itertuples(index=False), 2):
        for c, v in enumerate(row, 1):
            col = df.columns[c - 1]
            v = clean(v)
            if col in dt_cols and isinstance(v, str):
                v = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
            if col in date_cols and isinstance(v, str):
                v = datetime.strptime(v, "%Y-%m-%d")
            cell = ws.cell(row=r, column=c, value=v)
            cell.font, cell.border = F_BASE, BORDER
            if col in dt_cols:
                cell.number_format = DT
            if col in date_cols:
                cell.number_format = "yyyy-mm-dd"
    ws.freeze_panes = "B2"
    ws.row_dimensions[1].height = 30
    for c, name in enumerate(df.columns, 1):
        width = max(len(str(name)), *(len(str(clean(x) if clean(x) is not None else "")) for x in df[name].tolist())) + 2
        ws.column_dimensions[get_column_letter(c)].width = min(max(width, 10), 38)


def head(ws, col, text, width=None, calc=True, note=None):
    cell = ws.cell(row=1, column=col, value=text)
    cell.font, cell.border = F_HEAD, BORDER
    cell.fill = PatternFill("solid", fgColor="2E75B6" if calc else "1F3864")
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    if width:
        ws.column_dimensions[get_column_letter(col)].width = width
    if note:
        cell.comment = Comment(note, "Ops automation")


def fcell(ws, row, col, formula, fmt=None, bold=False, wrap=False):
    cell = ws.cell(row=row, column=col, value=formula)
    cell.font = F_BOLD if bold else F_BASE
    cell.fill, cell.border = FILL_CALC, BORDER
    if fmt:
        cell.number_format = fmt
    if wrap:
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    return cell


# ----------------------------------------------------------------------------- load data
inv = pd.read_csv(DATA / "1_invoices.csv", dtype=str)
ff = pd.read_csv(DATA / "2_faculty_form_unapproved.csv", dtype=str)
br = pd.read_csv(DATA / "3_booking_requests.csv", dtype=str)
cs = pd.read_csv(DATA / "4_class_schedule_bookings.csv", dtype=str)
ref = pd.read_csv(DATA / "reference_active_batches_and_students.csv", dtype=str)
NUMERIC = {
    "inv": ["id", "user_id", "student_id", "class_id", "educator_id", "amount", "discount_amount", "net_amount"],
    "ff": ["id", "educator_id", "user_id", "student_id", "class_id", "current_classbatch_id", "invoice_id",
           "amount_paid", "sessions_purchased"],
    "br": ["id", "faculty_form_id", "invoice_id", "user_id", "student_id", "class_id", "educator_id",
           "classbatch_id", "sessions_count"],
    "cs": ["id", "bookingrequest_id", "invoice_id", "classschedule_id", "classbatch_id", "class_id", "user_id",
           "student_id", "educator_id"],
    "ref": ["student_id", "user_id", "current_classbatch_id", "class_id", "category_id", "educator_id",
            "standard_fee_24_sessions_inr", "active_students_count", "max_batch_size"],
}
for name, df in (("inv", inv), ("ff", ff), ("br", br), ("cs", cs), ("ref", ref)):
    for c in NUMERIC[name]:
        df[c] = pd.to_numeric(df[c])
inv_n, ff_n, br_n, cs_n, ref_n = len(inv), len(ff), len(br), len(cs), len(ref)
LAST = 100  # lookup ranges run to row 100 so new rows can be pasted in

# ----------------------------------------------------------------------------- README sheet
ws = wb.active
ws.title = "README"
ws.sheet_view.showGridLines = False
ws["A1"] = "Bambinos.live - Renewal Reconciliation Sheet (no-code prototype)"
ws["A1"].font = F_TITLE
lines = [
    ("What this is", "A formula-only reconciliation engine. Paste the 5 production tables into the data tabs; the 'Checks' tab "
                     "applies the rules to every invoice and writes a reason code, severity and owner. 'Exceptions', 'AutoApproved' "
                     "and 'Dashboard' read from 'Checks'. No macros, no scripts."),
    ("Tabs", "Assumptions (inputs) | Invoices, Forms, Bookings, Schedule, Reference (the 5 CSVs) | Checks (the rule engine) | "
             "Exceptions | AutoApproved | Messages (drafted follow-ups) | Dashboard (Ops Head morning view)"),
    ("Colour legend", "Blue bold text on yellow = input you may change.  Green text = link to another tab.  Light-blue cells = formulas "
                      "(do not overwrite).  Dark-blue headers = raw data columns; mid-blue headers = calculated columns."),
    ("How to open in Google Sheets", "Upload the .xlsx to Google Drive > right-click > Open with Google Sheets. All formulas used "
                                     "(COUNTIF/COUNTIFS/SUMIFS, INDEX/MATCH, SUMPRODUCT, SUBSTITUTE, EXACT, TEXTJOIN, MAXIFS) work in Sheets."),
    ("How to use with new data", "Replace the rows in the 5 data tabs (keep the headers). Lookup ranges run to row 100. If you have more "
                                 "than 13 invoices, copy the last row of 'Checks' down and add rows to 'Exceptions' / 'AutoApproved'."),
    ("Snapshot time", "Assumptions!B2 is the 'as-of' time used for every 'hours stuck' calculation. Change it to re-run the ageing."),
    ("Rule order in 'Checks'", "1 payment status > 2 orphan (paid, no form) > 3 duplicate forms > 4 invoice-ID typo > 5 amount mismatch > "
                               "6 ID consistency > 7 discount > 8 payer vs registered parent (+ look-alike characters) > 9 stuck booking states > "
                               "10 batch-change availability > 11 sessions scheduled."),
    ("Severity meaning", "AUTO_APPROVE = clean, zero touch | AUTO_FIX = safe defect repaired automatically | SOFT = one-tap parent confirmation | "
                         "HUMAN = needs judgement | BLOCK = payment problem, never schedule | ALREADY_SCHEDULED = nothing to do."),
    ("Limits", "Messages tab holds text drafted from the same evidence (by script templates / the LLM prompt in /prompts); it is the one tab "
               "that is not formula-driven. Times are used as stored; time zones for GCC/US tracks are not modelled."),
]
r = 3
for k, v in lines:
    ws.cell(row=r, column=1, value=k).font = F_BOLD
    c = ws.cell(row=r, column=2, value=v)
    c.font, c.alignment = F_BASE, Alignment(wrap_text=True, vertical="top")
    ws.cell(row=r, column=1).alignment = Alignment(vertical="top")
    ws.row_dimensions[r].height = 48 if len(v) > 180 else 34
    r += 1
ws.column_dimensions["A"].width = 28
ws.column_dimensions["B"].width = 120

# ----------------------------------------------------------------------------- Assumptions
wa = wb.create_sheet("Assumptions")
wa.sheet_view.showGridLines = False
wa["A1"] = "Assumptions & inputs"
wa["A1"].font = F_TITLE
rows = [
    ("Snapshot (as-of) time", datetime.strptime(DEFAULT_ASOF, "%Y-%m-%d %H:%M"), DT,
     "Just after the newest record in the data (2026-11-03 17:15). Change to re-age every invoice."),
    ("Stuck threshold (hours after payment)", 12, "0", "Assignment's dashboard brief: 'stuck invoices >12h'."),
    ("Renewals per week (ILLUSTRATIVE)", 300, "#,##0", "Brief says 'hundreds per week'. Replace with the real number from the database."),
    ("Manual minutes per renewal (ILLUSTRATIVE)", 6, "0.0", "Assumption: verify by timing two Ops execs on real renewals."),
    ("Standard sessions per term", 24, "0", "Reference table fee column is for 24 sessions."),
]
for n, (label, val, fmt, note) in enumerate(rows, 2):
    wa.cell(row=n, column=1, value=label).font = F_BOLD
    c = wa.cell(row=n, column=2, value=val)
    c.font, c.fill, c.border, c.number_format = F_INPUT, FILL_INPUT, BORDER, fmt
    wa.cell(row=n, column=3, value=note).font = F_NOTE
wa.column_dimensions["A"].width = 44
wa.column_dimensions["B"].width = 20
wa.column_dimensions["C"].width = 100
ASOF, STUCK, WEEKLY, MINS, SESS = ("Assumptions!$B$2", "Assumptions!$B$3", "Assumptions!$B$4", "Assumptions!$B$5", "Assumptions!$B$6")

# ----------------------------------------------------------------------------- data tabs
w_inv = wb.create_sheet("Invoices")
write_df(w_inv, inv, dt_cols={"paid_at", "created_at", "updated_at"})
w_ff = wb.create_sheet("Forms")
write_df(w_ff, ff, dt_cols={"approved_at", "created_at", "updated_at"})
w_br = wb.create_sheet("Bookings")
write_df(w_br, br, dt_cols={"allocated_at", "created_at", "updated_at"})
w_cs = wb.create_sheet("Schedule")
write_df(w_cs, cs, dt_cols={"created_at", "updated_at"}, date_cols={"class_date"})
w_ref = wb.create_sheet("Reference")
write_df(w_ref, ref)

# Forms helper columns (X..AC) - link every form to its invoice, de-duplicate, age it
form_helpers = ["resolved_invoice_id", "link_status", "dup_rank", "pending_age_hours", "age_bucket", "pay_to_form_hours"]
for k, h in enumerate(form_helpers):
    head(w_ff, 24 + k, h, width=18, note={
        0: "If the form's invoice_id exists use it; otherwise find the ONE invoice with the same user_id + student_id + amount (fixes typos like 84931 -> 84913).",
        1: "OK / TYPO_FIXED / UNRESOLVED",
        2: "1 = earliest form for that invoice. >1 = duplicate submission.",
        3: "Hours since the form was created, for Pending forms only (uses Assumptions!B2).",
        4: "Age bucket for the dashboard.",
        5: "Teacher delay: form created minus invoice paid_at.",
    }[k])
SUMP = "(Invoices!$C$2:$C${L}=D{r})*(Invoices!$D$2:$D${L}=E{r})*(Invoices!$M$2:$M${L}=L{r})"
for r in range(2, ff_n + 2):
    sp = SUMP.format(L=LAST, r=r)
    fcell(w_ff, r, 24, f'=IF(COUNTIF(Invoices!$A$2:$A${LAST},J{r})>0,J{r},IF(SUMPRODUCT({sp})=1,SUMPRODUCT({sp}*Invoices!$A$2:$A${LAST}),""))')
    fcell(w_ff, r, 25, f'=IF(X{r}="","UNRESOLVED",IF(X{r}=J{r},"OK","TYPO_FIXED"))')
    fcell(w_ff, r, 26, f'=IF(X{r}="","",COUNTIFS($X$2:$X${LAST},X{r},$U$2:$U${LAST},"<"&U{r})+1)')
    fcell(w_ff, r, 27, f'=IF(R{r}="Pending",ROUND(({ASOF}-U{r})*24,1),"")', "0.0")
    fcell(w_ff, r, 28, f'=IF(AA{r}="","",IF(AA{r}<2,"0-2h",IF(AA{r}<12,"2-12h",IF(AA{r}<24,"12-24h","24h+"))))')
    fcell(w_ff, r, 29, f'=IF(X{r}="","",IF(INDEX(Invoices!$V$2:$V${LAST},MATCH(X{r},Invoices!$A$2:$A${LAST},0))="","",'
                       f'ROUND((U{r}-INDEX(Invoices!$V$2:$V${LAST},MATCH(X{r},Invoices!$A$2:$A${LAST},0)))*24,2)))', "0.00")

# ----------------------------------------------------------------------------- Checks (the engine)
wc = wb.create_sheet("Checks")
cols = [
    ("invoice_id", 11), ("student_id", 11), ("payment_status", 15), ("net_amount", 12), ("hours_since_paid", 12),
    ("form_id (primary)", 12), ("form_row", 9), ("form_amount_paid", 13), ("form_same_batch", 12), ("forms_for_invoice", 11),
    ("typo_fixed", 9), ("ref_row", 8), ("mobile_vs_registered", 13), ("email_vs_registered", 13), ("name_vs_registered", 14),
    ("discount_flag", 9), ("amount_mismatch", 11), ("id_mismatch", 9), ("booking_status", 28), ("scheduled_sessions", 11),
    ("sessions_purchased", 11), ("batch_id", 9), ("student_in_batch", 10), ("batch_row", 8), ("matching_batch_for_change", 14),
    ("orphan_flag", 9), ("REASON_CODES", 46), ("OUTCOME", 18), ("OWNER", 36), ("exc_flag", 8), ("exc_seq", 8),
    ("auto_flag", 8), ("auto_seq", 8),
]
for k, (h, w) in enumerate(cols, 1):
    head(wc, k, h, width=w, calc=True)
for k in (27, 28, 29):
    wc.cell(row=1, column=k).fill = PatternFill("solid", fgColor="C00000")
wc.freeze_panes = "B2"
wc.row_dimensions[1].height = 42

norm = "Invoices!G{r}"
for ch, rep in CONFUSABLES.items():
    norm = f'SUBSTITUTE({norm},"{ch}","{rep}")'


def tok(code, ref_cell):  # exact-token search in the comma-separated reason list
    return f'ISNUMBER(SEARCH(", {code},",", "&{ref_cell}&","))'


for r in range(2, inv_n + 2):
    R = r  # Checks row == Invoices row
    f = {}
    f[1] = f"=Invoices!A{R}"
    f[2] = f"=Invoices!D{R}"
    f[3] = f"=Invoices!T{R}"
    f[4] = f"=Invoices!M{R}"
    f[5] = f'=IF(Invoices!V{R}="","",ROUND(({ASOF}-Invoices!V{R})*24,1))'
    f[6] = f"=SUMPRODUCT((Forms!$X$2:$X${LAST}=A{r})*(Forms!$Z$2:$Z${LAST}=1)*Forms!$A$2:$A${LAST})"
    f[7] = f"=IF(F{r}=0,0,MATCH(F{r},Forms!$A$2:$A${LAST},0))"
    f[8] = f'=IF(G{r}=0,"",INDEX(Forms!$L$2:$L${LAST},G{r}))'
    f[9] = f'=IF(G{r}=0,"",INDEX(Forms!$N$2:$N${LAST},G{r}))'
    f[10] = f"=COUNTIF(Forms!$X$2:$X${LAST},A{r})"
    f[11] = f'=IF(G{r}=0,0,IF(INDEX(Forms!$Y$2:$Y${LAST},G{r})="TYPO_FIXED",1,0))'
    f[12] = f"=MATCH(B{r},Reference!$A$2:$A${LAST},0)"
    f[13] = f'=IF(Invoices!H{R}=INDEX(Reference!$E$2:$E${LAST},L{r}),"OK","MISMATCH")'
    f[14] = f'=IF(Invoices!I{R}=INDEX(Reference!$F$2:$F${LAST},L{r}),"OK","MISMATCH")'
    f[15] = (f'=IF(EXACT(Invoices!G{R},INDEX(Reference!$D$2:$D${LAST},L{r})),"OK",'
             f'IF(EXACT({norm.format(r=R)},INDEX(Reference!$D$2:$D${LAST},L{r})),"HOMOGLYPH","DIFFERENT"))')
    f[16] = f"=IF(Invoices!L{R}>0,1,0)"
    f[17] = f"=IF(G{r}=0,0,IF(ABS(H{r}-D{r})>0.5,1,0))"
    f[18] = (f"=IF(G{r}=0,0,IF(AND(INDEX(Forms!$D$2:$D${LAST},G{r})=Invoices!C{R},INDEX(Forms!$E$2:$E${LAST},G{r})=Invoices!D{R},"
             f"INDEX(Forms!$H$2:$H${LAST},G{r})=Invoices!E{R},INDEX(Forms!$B$2:$B${LAST},G{r})=Invoices!F{R}),0,1))")
    f[19] = f'=IFERROR(INDEX(Bookings!$N$2:$N${LAST},MATCH(A{r},Bookings!$C$2:$C${LAST},0)),"")'
    f[20] = f"=COUNTIF(Schedule!$C$2:$C${LAST},A{r})"
    f[21] = f"=IF(G{r}=0,{SESS},INDEX(Forms!$M$2:$M${LAST},G{r}))"
    f[22] = f"=IF(G{r}=0,INDEX(Reference!$G$2:$G${LAST},L{r}),INDEX(Forms!$I$2:$I${LAST},G{r}))"
    f[23] = f"=IF(INDEX(Reference!$G$2:$G${LAST},L{r})=V{r},1,0)"
    f[24] = f"=MATCH(V{r},Reference!$G$2:$G${LAST},0)"
    f[25] = (f'=IF(I{r}="No",IF(SUMPRODUCT((Reference!$K$2:$K${LAST}=INDEX(Reference!$K$2:$K${LAST},L{r}))'
             f'*(Reference!$M$2:$M${LAST}=INDEX(Reference!$M$2:$M${LAST},L{r}))'
             f'*(Reference!$P$2:$P${LAST}=INDEX(Forms!$O$2:$O${LAST},G{r}))'
             f'*(Reference!$Q$2:$Q${LAST}=INDEX(Forms!$P$2:$P${LAST},G{r}))'
             f'*(Reference!$R$2:$R${LAST}<Reference!$S$2:$S${LAST}))>0,"YES","NO"),"")')
    f[26] = f'=IF(AND(G{r}=0,C{r}="Paid",T{r}=0,S{r}=""),1,0)'
    pieces = [
        f'IF(C{r}="Failed","PAYMENT_NOT_CONFIRMED","")',
        f'IF(C{r}="Partially_Paid","PARTIAL_PAYMENT","")',
        f'IF(Z{r}=1,"ORPHAN_NO_FORM","")',
        f'IF(J{r}>1,"DUPLICATE_FORM","")',
        f'IF(K{r}=1,"INVOICE_ID_TYPO","")',
        f'IF(Q{r}=1,"AMOUNT_MISMATCH","")',
        f'IF(R{r}=1,"ID_MISMATCH","")',
        f'IF(P{r}=1,"DISCOUNT_NEEDS_APPROVAL","")',
        f'IF(OR(M{r}="MISMATCH",N{r}="MISMATCH",O{r}="DIFFERENT"),"PAYER_MISMATCH","")',
        f'IF(AND(M{r}="OK",N{r}="OK",O{r}="HOMOGLYPH"),"HOMOGLYPH_MISMATCH","")',
        f'IF(S{r}="Pending_Batch_Allocation","STUCK_AT_ALLOCATION","")',
        f'IF(AND(S{r}="Failed_Batch_Full",W{r}=1),"FALSE_BATCH_FULL","")',
        f'IF(AND(S{r}="Failed_Batch_Full",W{r}=0),"BATCH_FULL","")',
        f'IF(S{r}="Awaiting_Parent_Batch_Selection","BATCH_CHANGE_PENDING","")',
        f'IF(Y{r}="NO","NO_MATCHING_BATCH","")',
        f'IF(AND(T{r}>0,T{r}<U{r}),"SESSIONS_UNDER_SCHEDULED","")',
    ]
    f[27] = "=_xlfn.TEXTJOIN(\", \",TRUE," + ",".join(pieces) + ")"
    AA = f"AA{r}"
    block = " ,".join([])  # (kept for readability)
    blk = ",".join(tok(c, AA) for c in ("PAYMENT_NOT_CONFIRMED", "PARTIAL_PAYMENT"))
    hum = ",".join(tok(c, AA) for c in ("AMOUNT_MISMATCH", "ID_MISMATCH", "DISCOUNT_NEEDS_APPROVAL", "NO_MATCHING_BATCH",
                                         "BATCH_CHANGE_PENDING", "BATCH_FULL"))
    sft = ",".join(tok(c, AA) for c in ("ORPHAN_NO_FORM", "PAYER_MISMATCH"))
    f[28] = (f'=IF(T{r}>0,"ALREADY_SCHEDULED",IF({AA}="","AUTO_APPROVE",IF(OR({blk}),"BLOCK",IF(OR({hum}),"HUMAN",'
             f'IF(OR({sft}),"SOFT","AUTO_FIX")))))')
    f[29] = (f'=IF(AB{r}="ALREADY_SCHEDULED","Ops exec (info)",IF(OR(AB{r}="AUTO_APPROVE",AB{r}="AUTO_FIX"),"Automation",'
             f'IF({tok("PAYMENT_NOT_CONFIRMED", AA)},"Parent, then Ops exec",IF({tok("PARTIAL_PAYMENT", AA)},"Ops exec / Finance",'
             f'IF({tok("DISCOUNT_NEEDS_APPROVAL", AA)},"Ops lead / Head of Ops",IF(OR({tok("NO_MATCHING_BATCH", AA)},{tok("BATCH_CHANGE_PENDING", AA)}),"Parent + Ops exec",'
             f'IF({tok("ORPHAN_NO_FORM", AA)},"Parent (confirm) + Teacher (notify)",IF({tok("PAYER_MISMATCH", AA)},"Parent (registered number) + Ops exec","Ops exec"))))))))')
    f[30] = f'=IF(OR(AB{r}="BLOCK",AB{r}="HUMAN",AB{r}="SOFT"),1,0)'
    f[31] = f'=IF(AD{r}=1,SUM(AD$2:AD{r}),"")'
    f[32] = f'=IF(OR(AB{r}="AUTO_APPROVE",AB{r}="AUTO_FIX"),1,0)'
    f[33] = f'=IF(AF{r}=1,SUM(AF$2:AF{r}),"")'
    for k, formula in f.items():
        fmt = "0.0" if k == 5 else ("#,##0" if k in (4, 8) else None)
        fcell(wc, r, k, formula, fmt, bold=(k in (27, 28, 29)), wrap=False)
CH_LAST = inv_n + 1
rng = f"AB2:AB{CH_LAST}"
for sev, color in SEV_COLORS.items():
    wc.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=[f'"{sev}"'], fill=PatternFill("solid", bgColor=color, fgColor=color)))

# ----------------------------------------------------------------------------- Exceptions & AutoApproved
we = wb.create_sheet("Exceptions")
ehead = ["#", "invoice_id", "student_id", "payment_status", "net_amount", "hours_since_paid", "severity", "reason_codes", "owner"]
src = ["", "A", "B", "C", "D", "E", "AB", "AA", "AC"]
for k, (h, s) in enumerate(zip(ehead, src), 1):
    head(we, k, h, width=[5, 11, 11, 15, 12, 12, 11, 52, 40][k - 1], calc=(k > 1))
we.freeze_panes = "B2"
for n in range(1, inv_n + 1):
    r = n + 1
    c = we.cell(row=r, column=1, value=n)
    c.font, c.border = F_BASE, BORDER
    for k in range(2, 10):
        col = src[k - 1]
        fcell(we, r, k, f'=IFERROR(INDEX(Checks!${col}$2:${col}${CH_LAST},MATCH($A{r},Checks!$AE$2:$AE${CH_LAST},0)),"")',
              "#,##0" if k == 5 else ("0.0" if k == 6 else None))
for sev, color in SEV_COLORS.items():
    we.conditional_formatting.add(f"G2:G{inv_n + 1}", CellIsRule(operator="equal", formula=[f'"{sev}"'], fill=PatternFill("solid", bgColor=color, fgColor=color)))
we.cell(row=inv_n + 3, column=1, value="Rows fill automatically from 'Checks' (SOFT, HUMAN and BLOCK outcomes). Full evidence text is in results/exceptions.csv.").font = F_NOTE

wp = wb.create_sheet("AutoApproved")
ahead = ["#", "invoice_id", "student_id", "outcome", "fixes_applied", "classbatch_id", "sessions_count", "batch_days", "start_time", "booking_request"]
for k, h in enumerate(ahead, 1):
    head(wp, k, h, width=[5, 11, 11, 14, 46, 13, 13, 12, 11, 15][k - 1], calc=(k > 1))
wp.freeze_panes = "B2"
for n in range(1, inv_n + 1):
    r = n + 1
    c = wp.cell(row=r, column=1, value=n)
    c.font, c.border = F_BASE, BORDER
    m = f"MATCH($A{r},Checks!$AG$2:$AG${CH_LAST},0)"
    fcell(wp, r, 2, f'=IFERROR(INDEX(Checks!$A$2:$A${CH_LAST},{m}),"")')
    fcell(wp, r, 3, f'=IFERROR(INDEX(Checks!$B$2:$B${CH_LAST},{m}),"")')
    fcell(wp, r, 4, f'=IFERROR(INDEX(Checks!$AB$2:$AB${CH_LAST},{m}),"")')
    fcell(wp, r, 5, f'=IF(B{r}="","",IF(D{r}="AUTO_FIX",INDEX(Checks!$AA$2:$AA${CH_LAST},{m}),"none - all checks passed"))')
    fcell(wp, r, 6, f'=IFERROR(INDEX(Checks!$V$2:$V${CH_LAST},{m}),"")')
    fcell(wp, r, 7, f'=IFERROR(INDEX(Checks!$U$2:$U${CH_LAST},{m}),"")')
    fcell(wp, r, 8, f'=IF(F{r}="","",INDEX(Reference!$P$2:$P${LAST},MATCH(F{r},Reference!$G$2:$G${LAST},0)))')
    fcell(wp, r, 9, f'=IF(F{r}="","",INDEX(Reference!$Q$2:$Q${LAST},MATCH(F{r},Reference!$G$2:$G${LAST},0)))')
    fcell(wp, r, 10, f'=IF(B{r}="","",IFERROR(INDEX(Bookings!$A$2:$A${LAST},MATCH(B{r},Bookings!$C$2:$C${LAST},0)),"NEW"))')
wp.cell(row=inv_n + 3, column=1, value="Ready for class_schedule_bookings. Proposed session rows: results/proposed_class_schedule_bookings.csv.").font = F_NOTE

# ----------------------------------------------------------------------------- Messages (static text from the engine)
wm = wb.create_sheet("Messages")
msgs = json.loads((ROOT / "results" / "messages.json").read_text())
mh = ["invoice_id", "recipient_type", "recipient_name", "channel", "reason_code", "deadline", "message", "message_hinglish"]
for k, h in enumerate(mh, 1):
    head(wm, k, h, width=[11, 14, 22, 18, 30, 20, 90, 70][k - 1], calc=False)
for r, m in enumerate(msgs, 2):
    for k, h in enumerate(mh, 1):
        c = wm.cell(row=r, column=k, value=m.get(h, ""))
        c.font, c.border = F_BASE, BORDER
        c.alignment = Alignment(wrap_text=True, vertical="top")
wm.freeze_panes = "B2"
wm.cell(row=len(msgs) + 3, column=1, value="Static text: drafted from the Checks evidence by reconcile.py templates (the LLM prompt in /prompts does this in production). Names are masked as in the source data.").font = F_NOTE

# ----------------------------------------------------------------------------- Dashboard
wd = wb.create_sheet("Dashboard")
wd.sheet_view.showGridLines = False
wd["A1"] = "Ops Head - Morning Dashboard"
wd["A1"].font = F_TITLE
wd["A2"] = "=\"As of \"&TEXT(" + ASOF + ",\"yyyy-mm-dd hh:mm\")&\"  |  stuck threshold \"&" + STUCK + "&\" h\""
wd["A2"].font = F_NOTE
C = lambda col: f"Checks!${col}$2:${col}${CH_LAST}"  # noqa: E731
sections = [
    ("PIPELINE HEALTH", [
        ("Invoices analysed", f"=COUNTA(Invoices!$A$2:$A${LAST})", "0", ""),
        ("Fully paid invoices", f'=COUNTIF({C("C")},"Paid")', "0", ""),
        ("Paid AND scheduled", f'=COUNTIFS({C("C")},"Paid",{C("T")},">0")', "0", "Reached class_schedule_bookings"),
        ("Paid but NOT scheduled", f'=COUNTIFS({C("C")},"Paid",{C("T")},0)', "0", "The leakage"),
        ("Revenue at risk (INR)", f'=SUMIFS({C("D")},{C("C")},"Paid",{C("T")},0)', "#,##0", "Paid, no classes yet"),
        ("Scheduled share of paid renewals", "=IF(B5=0,0,B6/B5)", "0%", "Target: ~100% within SLA"),
    ]),
    ("STUCK INVOICES", [
        ("Stuck > threshold (count)", f'=COUNTIFS({C("C")},"Paid",{C("T")},0,{C("E")},">"&{STUCK})', "0", "Paid, unscheduled, older than the threshold"),
        ("Stuck > threshold (INR)", f'=SUMIFS({C("D")},{C("C")},"Paid",{C("T")},0,{C("E")},">"&{STUCK})', "#,##0", ""),
        ("Oldest stuck invoice (hours)", f'=_xlfn.MAXIFS({C("E")},{C("C")},"Paid",{C("T")},0)', "0.0", ""),
        ("Paid invoices with no form (orphans)", f'=COUNTIF({C("Z")},1)', "0", "Teacher never filed; invisible today"),
    ]),
    ("FORMS & BOOKINGS", [
        ("Forms pending Ops approval", f'=COUNTIF(Forms!$R$2:$R${LAST},"Pending")', "0", ""),
        ("   0-2 h", f'=COUNTIF(Forms!$AB$2:$AB${LAST},"0-2h")', "0", "Age since form created"),
        ("   2-12 h", f'=COUNTIF(Forms!$AB$2:$AB${LAST},"2-12h")', "0", ""),
        ("   12-24 h", f'=COUNTIF(Forms!$AB$2:$AB${LAST},"12-24h")', "0", ""),
        ("   24 h +", f'=COUNTIF(Forms!$AB$2:$AB${LAST},"24h+")', "0", ""),
        ("Unscheduled booking requests", f'=COUNTIF(Bookings!$O$2:$O${LAST},"No")', "0", "batch_allocated = No (stuck / failed / awaiting parent)"),
        ("Approved forms", f'=COUNTIF(Forms!$R$2:$R${LAST},"Approved")', "0", ""),
        ("Approved forms that actually got classes", f'=SUMPRODUCT((Forms!$R$2:$R${LAST}="Approved")*(COUNTIF(Schedule!$C$2:$C${LAST},Forms!$X$2:$X${LAST})>0))', "0", "Approval is not the finish line"),
        ("Duplicate-form invoices", f'=COUNTIF({C("J")},">1")', "0", ""),
        ("Median teacher delay (minutes)", f'=ROUND(MEDIAN(Forms!$AC$2:$AC${LAST})*60,0)', "0", "Payment to form submitted"),
    ]),
    ("OUTCOMES (what the engine decided)", [
        ("AUTO_APPROVE (clean)", f'=COUNTIF({C("AB")},"AUTO_APPROVE")', "0", ""),
        ("AUTO_FIX (repaired automatically)", f'=COUNTIF({C("AB")},"AUTO_FIX")', "0", ""),
        ("SOFT (one-tap confirmation)", f'=COUNTIF({C("AB")},"SOFT")', "0", ""),
        ("HUMAN (needs judgement)", f'=COUNTIF({C("AB")},"HUMAN")', "0", ""),
        ("BLOCK (payment problem)", f'=COUNTIF({C("AB")},"BLOCK")', "0", ""),
        ("ALREADY_SCHEDULED", f'=COUNTIF({C("AB")},"ALREADY_SCHEDULED")', "0", ""),
        ("Zero-touch share of outstanding", "=IF(B1000=0,0,(B{a}+B{b})/(B3-B{c}))", "0%", "(Auto-approve + auto-fix) / outstanding"),
        ("Zero-touch + soft share", "=(B{a}+B{b}+B{d})/(B3-B{c})", "0%", ""),
    ]),
    ("SAVINGS (illustrative - inputs on Assumptions)", [
        ("Hours saved per week", f"={WEEKLY}*B{{z}}*{MINS}/60", "0.0", "Renewals/week x zero-touch share x minutes / 60"),
    ]),
]
row = 4
pos = {}
for title, items in sections:
    c = wd.cell(row=row, column=1, value=title)
    c.font, c.fill = F_H2, FILL_SEC
    wd.cell(row=row, column=2).fill = FILL_SEC
    wd.cell(row=row, column=3).fill = FILL_SEC
    row += 1
    for label, formula, fmt, note in items:
        pos[label] = row
        wd.cell(row=row, column=1, value=label).font = F_BASE
        fcell(wd, row, 2, formula, fmt, bold=True)
        wd.cell(row=row, column=3, value=note).font = F_NOTE
        row += 1
    row += 1
# patch the placeholder references now that row numbers are known
a, b, d, c_, z = (pos["AUTO_APPROVE (clean)"], pos["AUTO_FIX (repaired automatically)"], pos["SOFT (one-tap confirmation)"],
                  pos["ALREADY_SCHEDULED"], pos["Zero-touch share of outstanding"])
inv_cell = pos["Invoices analysed"]
wd.cell(row=pos["Zero-touch share of outstanding"], column=2, value=f"=IF(B{inv_cell}-B{c_}=0,0,(B{a}+B{b})/(B{inv_cell}-B{c_}))")
wd.cell(row=pos["Zero-touch + soft share"], column=2, value=f"=IF(B{inv_cell}-B{c_}=0,0,(B{a}+B{b}+B{d})/(B{inv_cell}-B{c_}))")
wd.cell(row=pos["Hours saved per week"], column=2, value=f"={WEEKLY}*B{z}*{MINS}/60")
wd.cell(row=pos["Scheduled share of paid renewals"], column=2,
        value=f"=IF(B{pos['Fully paid invoices']}=0,0,B{pos['Paid AND scheduled']}/B{pos['Fully paid invoices']})")
wd.column_dimensions["A"].width = 46
wd.column_dimensions["B"].width = 18
wd.column_dimensions["C"].width = 60

# sheet order and tab colours
order = ["README", "Dashboard", "Assumptions", "Checks", "Exceptions", "AutoApproved", "Messages", "Invoices", "Forms", "Bookings", "Schedule", "Reference"]
wb._sheets = [wb[n] for n in order]
for n, colr in {"README": "7F7F7F", "Dashboard": "1F3864", "Assumptions": "FFC000", "Checks": "C00000", "Exceptions": "ED7D31",
                "AutoApproved": "70AD47", "Messages": "5B9BD5"}.items():
    wb[n].sheet_properties.tabColor = colr
for wsx in wb.worksheets:
    for rowc in wsx.iter_rows():
        for cell in rowc:
            if cell.font is None or cell.font.name != FONT:
                cell.font = Font(name=FONT, size=cell.font.size if cell.font else 10, bold=cell.font.bold if cell.font else False,
                                 italic=cell.font.italic if cell.font else False, color=cell.font.color if cell.font else None)
wb.save(OUT)
print("saved", OUT)
