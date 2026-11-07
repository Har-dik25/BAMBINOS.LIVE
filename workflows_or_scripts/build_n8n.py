"""Generates n8n_renewal_workflow.json (importable template). Credentials / URLs are placeholders (REPLACE_*)."""
import json, uuid
from pathlib import Path
HERE = Path(__file__).resolve().parent
code = (HERE / "n8n_rules_engine.js").read_text()
_ctr = [0]
def nid():
    _ctr[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"bambinos-node-{_ctr[0]}"))
N = []
def node(name, typ, ver, pos, params, **extra):
    N.append({"parameters": params, "id": nid(), "name": name, "type": typ, "typeVersion": ver, "position": pos, **extra})
def cond(left, right):
    return {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
            "conditions": [{"id": nid(), "leftValue": left, "rightValue": right, "operator": {"type": "string", "operation": "equals"}}], "combinator": "and"}}
def sw_rule(values, key):
    conds = [{"id": nid(), "leftValue": "={{ $json.outcome }}", "rightValue": v, "operator": {"type": "string", "operation": "equals"}} for v in values]
    return {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"}, "conditions": conds, "combinator": "or"},
            "renameOutput": True, "outputKey": key}
CTX = "https://REPLACE_WITH_CONTEXT_API"   # e.g. a Google Apps Script web app over the Sheet, or a read-only DB endpoint

node("Sticky: how it works", "n8n-nodes-base.stickyNote", 1, [-640, -260],
     {"content": "## Bambinos renewal automation (template)\n**Trigger A:** payment webhook (Razorpay/Stripe). **Trigger B:** 15-minute reconciliation sweep.\n"
                 "Both feed the SAME rules engine (Code node = n8n_rules_engine.js, mirrors reconcile.py and the Google Sheet).\n"
                 "**Zero-touch** -> create booking + WhatsApp confirmation. **SOFT / HUMAN / BLOCK** -> LLM drafts the message -> one named owner.\n"
                 "Replace every REPLACE_* value and connect credentials before activating. Run in SHADOW MODE first (log only).",
      "height": 260, "width": 520})
node("Payment captured (webhook)", "n8n-nodes-base.webhook", 2, [-560, 80],
     {"httpMethod": "POST", "path": "renewal-payment-captured", "options": {}}, webhookId=str(uuid.uuid4()))
node("Every 15 minutes (sweep)", "n8n-nodes-base.scheduleTrigger", 1.2, [-560, 420],
     {"rule": {"interval": [{"field": "minutes", "minutesInterval": 15}]}})
node("Fetch renewal context", "n8n-nodes-base.httpRequest", 4.2, [-320, 80],
     {"method": "GET", "url": f"{CTX}/context", "sendQuery": True,
      "queryParameters": {"parameters": [{"name": "invoice_id", "value": "={{ $json.body.invoice_id }}"}]}, "options": {}})
node("Fetch stuck / orphan candidates", "n8n-nodes-base.httpRequest", 4.2, [-320, 420],
     {"method": "GET", "url": f"{CTX}/sweep", "sendQuery": True,
      "queryParameters": {"parameters": [{"name": "min_hours", "value": "2"}]}, "options": {}})
node("Split candidates", "n8n-nodes-base.splitOut", 1, [-100, 420], {"fieldToSplitOut": "items", "options": {}})
node("Rules engine (12 checks)", "n8n-nodes-base.code", 2, [-100, 80],
     {"mode": "runOnceForAllItems", "language": "javaScript", "jsCode": code})
node("Route by outcome", "n8n-nodes-base.switch", 3, [160, 80],
     {"rules": {"values": [sw_rule(["AUTO_APPROVE", "AUTO_FIX"], "Zero-touch"), sw_rule(["SOFT"], "Soft"),
                           sw_rule(["HUMAN"], "Human"), sw_rule(["BLOCK"], "Block")]},
      "options": {"fallbackOutput": "none"}})
node("Create booking + schedule rows", "n8n-nodes-base.googleSheets", 4.5, [440, -80],
     {"operation": "append", "documentId": {"__rl": True, "mode": "id", "value": "REPLACE_WITH_SHEET_ID"},
      "sheetName": {"__rl": True, "mode": "name", "value": "AutoApproved"},
      "columns": {"mappingMode": "autoMapInputData", "value": {}}, "options": {}})
node("WhatsApp: confirm to parent", "n8n-nodes-base.httpRequest", 4.2, [700, -80],
     {"method": "POST", "url": "https://graph.facebook.com/v19.0/REPLACE_PHONE_NUMBER_ID/messages", "sendHeaders": True,
      "headerParameters": {"parameters": [{"name": "Authorization", "value": "Bearer REPLACE_WHATSAPP_TOKEN"}]},
      "sendBody": True, "specifyBody": "json",
      "jsonBody": "={{ JSON.stringify({messaging_product:'whatsapp', to:'REPLACE_PARENT_NUMBER', type:'template', template:{name:'renewal_confirmed', language:{code:'en'}}}) }}",
      "options": {}})
node("Draft message (LLM)", "n8n-nodes-base.httpRequest", 4.2, [440, 240],
     {"method": "POST", "url": "https://api.anthropic.com/v1/messages", "sendHeaders": True,
      "headerParameters": {"parameters": [{"name": "x-api-key", "value": "REPLACE_API_KEY"},
                                           {"name": "anthropic-version", "value": "2023-06-01"},
                                           {"name": "content-type", "value": "application/json"}]},
      "sendBody": True, "specifyBody": "json",
      "jsonBody": "={{ JSON.stringify({model:'claude-sonnet-5-5', max_tokens:600, temperature:0, "
                  "system:'REPLACE with the system prompt from prompts/message_drafter.md', "
                  "messages:[{role:'user', content: JSON.stringify({recipient_type:'parent', reason_code:$json.reason_codes, evidence:$json})}]}) }}",
      "options": {}})
node("Parse drafted message", "n8n-nodes-base.code", 2, [700, 240],
     {"mode": "runOnceForEachItem", "language": "javaScript",
      "jsCode": "const t = $json.content?.[0]?.text || '{}';\nlet m; try { m = JSON.parse(t); } catch (e) { m = {recipient:'Ops exec on duty', channel:'slack', message:'Could not parse draft: ' + t}; }\nreturn { json: { ...m, invoice_id: $('Rules engine (12 checks)').item.json.invoice_id, owner: $('Rules engine (12 checks)').item.json.owner, sla_hours: 24 } };"})
node("Slack or WhatsApp?", "n8n-nodes-base.if", 2.2, [960, 240],
     {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                     "conditions": [{"id": nid(), "leftValue": "={{ $json.channel }}", "rightValue": "slack", "operator": {"type": "string", "operation": "equals"}}],
                     "combinator": "and"}, "options": {}})
node("Slack: alert the owner", "n8n-nodes-base.slack", 2.2, [1220, 160],
     {"authentication": "oAuth2", "select": "channel", "channelId": {"__rl": True, "mode": "name", "value": "#ops-renewals"},
      "text": "={{ $json.message }}", "otherOptions": {}})
node("WhatsApp: parent / teacher", "n8n-nodes-base.httpRequest", 4.2, [1220, 340],
     {"method": "POST", "url": "https://graph.facebook.com/v19.0/REPLACE_PHONE_NUMBER_ID/messages", "sendHeaders": True,
      "headerParameters": {"parameters": [{"name": "Authorization", "value": "Bearer REPLACE_WHATSAPP_TOKEN"}]},
      "sendBody": True, "specifyBody": "json",
      "jsonBody": "={{ JSON.stringify({messaging_product:'whatsapp', to:'REPLACE_NUMBER', type:'text', text:{body:$json.message}}) }}", "options": {}})
node("Log exception + start SLA timer", "n8n-nodes-base.googleSheets", 4.5, [1480, 240],
     {"operation": "append", "documentId": {"__rl": True, "mode": "id", "value": "REPLACE_WITH_SHEET_ID"},
      "sheetName": {"__rl": True, "mode": "name", "value": "Exception log"},
      "columns": {"mappingMode": "autoMapInputData", "value": {}}, "options": {}})

C = {}
def connect(src, dst, out=0):
    m = C.setdefault(src, {"main": []})["main"]
    while len(m) <= out: m.append([])
    m[out].append({"node": dst, "type": "main", "index": 0})
connect("Payment captured (webhook)", "Fetch renewal context")
connect("Fetch renewal context", "Rules engine (12 checks)")
connect("Every 15 minutes (sweep)", "Fetch stuck / orphan candidates")
connect("Fetch stuck / orphan candidates", "Split candidates")
connect("Split candidates", "Rules engine (12 checks)")
connect("Rules engine (12 checks)", "Route by outcome")
connect("Route by outcome", "Create booking + schedule rows", 0)
connect("Create booking + schedule rows", "WhatsApp: confirm to parent")
for k in (1, 2, 3):
    connect("Route by outcome", "Draft message (LLM)", k)
connect("Draft message (LLM)", "Parse drafted message")
connect("Parse drafted message", "Slack or WhatsApp?")
connect("Slack or WhatsApp?", "Slack: alert the owner", 0)
connect("Slack or WhatsApp?", "WhatsApp: parent / teacher", 1)
connect("Slack: alert the owner", "Log exception + start SLA timer")
connect("WhatsApp: parent / teacher", "Log exception + start SLA timer")

wf = {"name": "Bambinos - Renewal payment to scheduled classes (zero-touch + exceptions)", "nodes": N, "connections": C,
      "active": False, "settings": {"executionOrder": "v1"}, "pinData": {}, "tags": [], "meta": {"templateCredsSetupCompleted": False}}
(HERE / "n8n_renewal_workflow.json").write_text(json.dumps(wf, indent=2, ensure_ascii=False))
names = {n["name"] for n in N}
bad = [(s, d["node"]) for s, v in C.items() for outs in v["main"] for d in outs if s not in names or d["node"] not in names]
print("nodes:", len(N), "| connections ok" if not bad else f"| BAD LINKS {bad}")
