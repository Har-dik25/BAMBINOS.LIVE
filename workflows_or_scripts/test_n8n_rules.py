"""Builds a context object per invoice from the CSVs, runs n8n_rules_engine.js in Node, and compares with reconcile.py."""
import json, subprocess, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from datetime import datetime
from reconcile import reconcile
HERE = Path(__file__).resolve().parent
dec, inv, ff, br, cs, ref = reconcile(HERE.parent / "data", datetime(2026, 11, 3, 18, 0))
def rec(df): return json.loads(df.to_json(orient="records", date_format="iso"))
ctxs = []
for _, i in inv.iterrows():
    forms = ff[ff["resolved_invoice_id"] == i["id"]].copy()
    forms["cited_invoice_id"] = forms["invoice_id"]
    bk = br[br["invoice_id"] == i["id"]]
    ctxs.append({"invoice": rec(inv[inv["id"] == i["id"]])[0], "forms": rec(forms),
                 "booking": rec(bk)[0] if len(bk) else None,
                 "schedule_count": int((cs["invoice_id"] == i["id"]).sum()),
                 "reference": rec(ref[ref["student_id"] == i["student_id"]])[0], "batches": rec(ref)})
js = (HERE / "n8n_rules_engine.js").read_text()
runner = "const {decide}=(()=>{const module={exports:{}};" + js.replace("return $input", "//").replace("if (typeof $input", "if (false && typeof $input") + ";return module.exports})();" \
         "const ctx=JSON.parse(require('fs').readFileSync(0,'utf8'));console.log(JSON.stringify(ctx.map(decide)));"
out = subprocess.run(["node", "-e", runner], input=json.dumps(ctxs), capture_output=True, text=True)
if out.returncode: print(out.stderr); sys.exit(1)
res = {r["invoice_id"]: r for r in json.loads(out.stdout)}
ok = True
for _, d in dec.iterrows():
    r = res[int(d["invoice_id"])]
    py_codes = {c.strip() for c in d["reason_codes"].split(",") if c.strip()}
    same = (r["outcome"] == d["outcome"]) and set(r["reason_codes"]) == py_codes
    ok &= same
    print(f"{int(d['invoice_id'])}  js={r['outcome']:17s} py={d['outcome']:17s} {'OK' if same else 'MISMATCH'}")
print("ALL MATCH" if ok else "DIFFERENCES FOUND")
