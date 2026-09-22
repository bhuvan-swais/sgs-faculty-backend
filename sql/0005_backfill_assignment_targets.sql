-- 0005: give every existing assignment its target rows.
--
-- Before this change, sgs_assignment_results only got a row when a student
-- submitted. Assignments are now explicit about who received them (one
-- "assigned" row per student, written at creation), and student/parent apps
-- read a student's assignments from those rows. Older assignments were all
-- class-wide, so each one gets a row for every active student in its class
-- who doesn't already have one.
--
-- Idempotent. Run on STAGING first; production after QA sign-off.

INSERT INTO sgs_assignment_results
    (assignment_id, student_id, subject_id, assignment_title, due_date,
     status, created_datetime, record_status, version_no)
SELECT a.assignment_id, s.student_id, a.subject_id, a.assignment_title, a.due_date,
       'assigned', now(), 'Active', 1
FROM sgs_assignment_master a
JOIN sgs_student_master s
  ON s.class_id = a.class_id
 AND s.is_active IS TRUE
 AND (s.record_status = 'Active' OR s.record_status IS NULL)
WHERE (a.record_status = 'Active' OR a.record_status IS NULL)
  AND NOT EXISTS (
        SELECT 1 FROM sgs_assignment_results r
        WHERE r.assignment_id = a.assignment_id
          AND r.student_id    = s.student_id
  );

-- What it did:
SELECT count(*) AS assignments_with_targets,
       sum(n)   AS target_rows
FROM (SELECT assignment_id, count(*) n FROM sgs_assignment_results GROUP BY 1) t;
