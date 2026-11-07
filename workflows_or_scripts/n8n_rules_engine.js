// Bambinos renewal rules engine - for the n8n "Code" node (Run Once for All Items).
// Mirrors reconcile.py and the Checks tab of the Google Sheet. Input items look like:
// { invoice, forms[], booking|null, schedule_count, reference, batches[] }   (see README for the context API)
const CONF = {"\u0410":"A","\u0412":"B","\u0415":"E","\u041a":"K","\u041c":"M","\u041d":"H","\u041e":"O","\u0420":"P","\u0421":"C","\u0422":"T","\u0425":"X","\u0430":"a","\u0435":"e","\u043e":"o","\u0440":"p","\u0441":"c","\u0443":"y","\u0445":"x"};
const skel = s => (s || "").normalize("NFKC").split("").map(c => CONF[c] || c).join("").toLowerCase().trim();
const META = {
  PAYMENT_NOT_CONFIRMED: ["BLOCK", "Parent, then Ops exec"], PARTIAL_PAYMENT: ["BLOCK", "Ops exec / Finance"],
  AMOUNT_MISMATCH: ["HUMAN", "Ops exec"], ID_MISMATCH: ["HUMAN", "Ops exec"],
  DISCOUNT_NEEDS_APPROVAL: ["HUMAN", "Ops lead / Head of Ops"], NO_MATCHING_BATCH: ["HUMAN", "Ops exec / Academics"],
  BATCH_CHANGE_PENDING: ["HUMAN", "Parent + Ops exec"], BATCH_FULL: ["HUMAN", "Ops exec / Academics"],
  ORPHAN_NO_FORM: ["SOFT", "Parent (confirm) + Teacher (notify)"], PAYER_MISMATCH: ["SOFT", "Parent (registered number) + Ops exec"],
  DUPLICATE_FORM: ["AUTO_FIX", "Automation"], INVOICE_ID_TYPO: ["AUTO_FIX", "Automation"], HOMOGLYPH_MISMATCH: ["AUTO_FIX", "Automation"],
  STUCK_AT_ALLOCATION: ["AUTO_FIX", "Automation"], FALSE_BATCH_FULL: ["AUTO_FIX", "Automation"],
  SESSIONS_UNDER_SCHEDULED: ["INFO", "Ops exec (info)"],
};
const RANK = { INFO: 0, AUTO_FIX: 2, SOFT: 3, HUMAN: 4, BLOCK: 5 };

function decide(ctx) {
  const inv = ctx.invoice, ref = ctx.reference || {};
  const forms = [...(ctx.forms || [])].sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
  const form = forms[0] || null;                       // earliest form wins (idempotency)
  const bk = ctx.booking || null;
  const sched = Number(ctx.schedule_count || 0);
  const codes = [];

  if (inv.payment_status === "Failed") codes.push("PAYMENT_NOT_CONFIRMED");          // gateway is the only truth
  if (inv.payment_status === "Partially_Paid") codes.push("PARTIAL_PAYMENT");
  if (!form && inv.payment_status === "Paid" && sched === 0 && !bk) codes.push("ORPHAN_NO_FORM");
  if (form) {
    if (forms.length > 1) codes.push("DUPLICATE_FORM");
    if (Number(form.cited_invoice_id) !== Number(inv.id)) codes.push("INVOICE_ID_TYPO");
    if (Math.abs(Number(form.amount_paid) - Number(inv.net_amount)) > 0.5) codes.push("AMOUNT_MISMATCH");
    if (["user_id", "student_id", "class_id", "educator_id"].some(k => Number(form[k]) !== Number(inv[k]))) codes.push("ID_MISMATCH");
  }
  if (Number(inv.discount_amount) > 0) codes.push("DISCOUNT_NEEDS_APPROVAL");
  if (ref.student_id) {
    const mobOk = inv.mobile === ref.registered_mobile_masked, mailOk = inv.email === ref.registered_email_masked;
    const nameRaw = inv.parent_name === ref.parent_name_masked, nameSk = skel(inv.parent_name) === skel(ref.parent_name_masked);
    if (!mobOk || !mailOk || !nameSk) codes.push("PAYER_MISMATCH");
    else if (!nameRaw) codes.push("HOMOGLYPH_MISMATCH");
  }
  const batchId = form ? Number(form.current_classbatch_id) : Number(ref.current_classbatch_id);
  const ownSeat = Number(ref.current_classbatch_id) === batchId;
  if (bk) {
    if (bk.request_status === "Pending_Batch_Allocation") codes.push("STUCK_AT_ALLOCATION");
    else if (bk.request_status === "Failed_Batch_Full") codes.push(ownSeat ? "FALSE_BATCH_FULL" : "BATCH_FULL");
    else if (bk.request_status === "Awaiting_Parent_Batch_Selection") codes.push("BATCH_CHANGE_PENDING");
  }
  if (form && form.continue_same_batch === "No" && ref.student_id) {
    // match on category + educator + days + time + free seat (never days/time alone)
    const hit = (ctx.batches || []).filter(b => Number(b.category_id) === Number(ref.category_id)
      && Number(b.educator_id) === Number(ref.educator_id) && b.batch_days === form.preferred_days
      && b.batch_start_time === form.preferred_time_slot && Number(b.active_students_count) < Number(b.max_batch_size));
    if (!hit.length) codes.push("NO_MATCHING_BATCH");
  }
  const sessions = form ? Number(form.sessions_purchased) : 24;
  if (sched > 0 && sched < sessions) codes.push("SESSIONS_UNDER_SCHEDULED");

  let outcome;
  if (sched > 0) outcome = "ALREADY_SCHEDULED";
  else if (!codes.length) outcome = "AUTO_APPROVE";
  else outcome = codes.map(c => META[c][0]).reduce((a, b) => (RANK[b] > RANK[a] ? b : a), "INFO");
  if (outcome === "INFO") outcome = "AUTO_APPROVE";
  const owners = [...new Set(codes.filter(c => META[c][0] !== "INFO" || sched > 0).map(c => META[c][1]))];
  return {
    invoice_id: inv.id, student_id: inv.student_id, outcome, reason_codes: codes,
    owner: outcome === "AUTO_APPROVE" ? "Automation" : owners.join(" | "),
    classbatch_id: batchId, sessions, hours_since_payment: inv.paid_at ? Math.round((Date.now() - new Date(inv.paid_at)) / 36e5 * 10) / 10 : null,
  };
}

// n8n entry point
if (typeof $input !== "undefined") {
  return $input.all().map(i => ({ json: decide(i.json) }));
}
// (outside n8n) module.exports used by the test harness
if (typeof module !== "undefined") module.exports = { decide };
