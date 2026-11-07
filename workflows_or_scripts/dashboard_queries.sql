-- =====================================================================================
-- Bambinos.live - Ops Head dashboard queries (MySQL syntax)
-- One query per dashboard block. Paste each into Metabase as a saved question.
-- Tables: invoices, faculty_form_unapproved, booking_requests, class_schedule_bookings
-- Snapshot time: use NOW() in production; the examples set @asof to match the sample data.
-- =====================================================================================
SET @asof = '2026-11-03 18:00:00';
SET @stuck_hours = 12;

-- Q1: PAID renewal invoices with NO faculty form pointing at them (orphans) -------------
-- Note: on the sample data this also lists invoice 84913, whose form cites 84931 (typo). Q8 explains why.
SELECT i.id AS invoice_id, i.invoice_number, i.student_id, i.net_amount,
       TIMESTAMPDIFF(HOUR, i.paid_at, @asof) AS hours_since_paid
FROM invoices i
LEFT JOIN faculty_form_unapproved f
       ON f.invoice_id = i.id AND f.deleted_at IS NULL
WHERE i.payment_status = 'Paid' AND i.is_renewal = 'Yes' AND i.deleted_at IS NULL
  AND f.id IS NULL
ORDER BY hours_since_paid DESC;

-- Q2: STUCK invoices - paid, but no class_schedule_bookings row, older than the threshold ---
SELECT i.id AS invoice_id, i.net_amount, i.paid_at,
       TIMESTAMPDIFF(HOUR, i.paid_at, @asof) AS hours_since_paid
FROM invoices i
LEFT JOIN class_schedule_bookings c
       ON c.invoice_id = i.id AND c.deleted_at IS NULL
WHERE i.payment_status = 'Paid' AND i.deleted_at IS NULL
  AND c.id IS NULL
  AND TIMESTAMPDIFF(HOUR, i.paid_at, @asof) > @stuck_hours
ORDER BY hours_since_paid DESC;

-- Q3: Pending (unapproved) forms by age bucket -------------------------------------------
SELECT CASE WHEN TIMESTAMPDIFF(HOUR, created_at, @asof) < 2  THEN '0-2h'
            WHEN TIMESTAMPDIFF(HOUR, created_at, @asof) < 12 THEN '2-12h'
            WHEN TIMESTAMPDIFF(HOUR, created_at, @asof) < 24 THEN '12-24h'
            ELSE '24h+' END AS age_bucket,
       COUNT(*) AS forms
FROM faculty_form_unapproved
WHERE approval_status = 'Pending' AND deleted_at IS NULL
GROUP BY age_bucket
ORDER BY MIN(created_at) DESC;

-- Q4: Duplicate forms - more than one form per invoice -----------------------------------
SELECT invoice_id, COUNT(*) AS forms, GROUP_CONCAT(id ORDER BY created_at) AS form_ids
FROM faculty_form_unapproved
WHERE deleted_at IS NULL
GROUP BY invoice_id
HAVING COUNT(*) > 1;

-- Q5: Form vs invoice mismatches (amount actually paid; payer phone) ----------------------
SELECT f.id AS form_id, i.id AS invoice_id,
       f.amount_paid AS form_amount, i.net_amount AS invoice_net_amount,
       f.parent_mobile AS form_mobile, i.mobile AS invoice_mobile,
       CASE WHEN f.amount_paid <> i.net_amount THEN 'AMOUNT_MISMATCH' END AS amount_flag,
       CASE WHEN f.parent_mobile <> i.mobile  THEN 'PHONE_DIFFERS'   END AS phone_flag
FROM faculty_form_unapproved f
JOIN invoices i ON i.id = f.invoice_id
WHERE f.deleted_at IS NULL
  AND (f.amount_paid <> i.net_amount OR f.parent_mobile <> i.mobile);

-- Q6: Unscheduled booking requests by status (the dead ends after approval) ---------------
SELECT request_status, COUNT(*) AS bookings,
       MAX(TIMESTAMPDIFF(HOUR, updated_at, @asof)) AS oldest_hours_in_status
FROM booking_requests
WHERE batch_allocated = 'No' AND deleted_at IS NULL
GROUP BY request_status;

-- Q7: Payment-to-schedule turnaround per invoice (minutes) --------------------------------
SELECT i.id AS invoice_id,
       TIMESTAMPDIFF(MINUTE, i.paid_at, MIN(c.created_at)) AS minutes_payment_to_first_schedule
FROM invoices i
JOIN class_schedule_bookings c ON c.invoice_id = i.id AND c.deleted_at IS NULL
WHERE i.payment_status = 'Paid'
GROUP BY i.id, i.paid_at;

-- Q8: Forms whose invoice_id does not exist (typos such as 84931 instead of 84913) ---------
SELECT f.id AS form_id, f.invoice_id AS cited_invoice_id, f.user_id, f.student_id, f.amount_paid,
       i.id AS likely_invoice_id
FROM faculty_form_unapproved f
LEFT JOIN invoices i0 ON i0.id = f.invoice_id
LEFT JOIN invoices i  ON i.user_id = f.user_id AND i.student_id = f.student_id AND i.net_amount = f.amount_paid
WHERE i0.id IS NULL AND f.deleted_at IS NULL;

-- Q9: Morning KPI strip ---------------------------------------------------------------------
SELECT COUNT(*)                                                              AS paid_invoices,
       SUM(c.id IS NOT NULL)                                                 AS paid_and_scheduled,
       SUM(c.id IS NULL)                                                     AS paid_not_scheduled,
       SUM(CASE WHEN c.id IS NULL THEN i.net_amount ELSE 0 END)              AS revenue_at_risk_inr
FROM invoices i
LEFT JOIN (SELECT DISTINCT invoice_id, MIN(id) AS id FROM class_schedule_bookings
           WHERE deleted_at IS NULL GROUP BY invoice_id) c ON c.invoice_id = i.id
WHERE i.payment_status = 'Paid' AND i.deleted_at IS NULL;
