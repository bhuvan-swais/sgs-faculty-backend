-- 0004: sgs_question_papers — saved auto-test papers.
-- Run on STAGING (swais-db-test-env) first; production only after QA sign-off.
-- Idempotent: safe to re-run.
-- swais_app_user owns the sgs_ tables and has CREATE on public, so it can run this.

CREATE TABLE IF NOT EXISTS sgs_question_papers (
    paper_id            BIGSERIAL PRIMARY KEY,
    -- varchar, not bigint: that is what sgs_teacher_master.teacher_id actually is,
    -- and what sgs_teacher_notes / sgs_assessments / sgs_teacher_lesson_plans use.
    teacher_id          VARCHAR NOT NULL REFERENCES sgs_teacher_master(teacher_id) ON DELETE CASCADE,
    chapter_id          BIGINT,
    title               VARCHAR(255) NOT NULL,
    subject             VARCHAR(150),
    difficulty          VARCHAR(20),
    total_marks         INTEGER,
    question_type       VARCHAR(30),          -- MCQ / True/False / Short Answer / NULL = mixed
    paper_text          TEXT,                 -- plain-text paper (what the AI returns today)
    questions           JSONB,                -- structured questions (when the AI returns them)
    created_at          TIMESTAMP DEFAULT now(),
    -- audit set shared by every sgs_ table
    created_user_id     VARCHAR(100),
    created_ip_address  VARCHAR(50),
    modified_datetime   TIMESTAMP,
    modified_user_id    VARCHAR(100),
    modified_ip_address VARCHAR(50),
    record_status       VARCHAR(20) DEFAULT 'Active',
    version_no          INTEGER DEFAULT 1,
    updated_at          TIMESTAMP,
    CONSTRAINT ck_question_papers_has_content CHECK (paper_text IS NOT NULL OR questions IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS ix_sgs_question_papers_teacher_id ON sgs_question_papers (teacher_id);

-- Same audit trigger as every other sgs_ table: trg_audit_stamp → fn_stamp_updated_at,
-- which stamps modified_datetime / updated_at on UPDATE.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'fn_stamp_updated_at')
     AND NOT EXISTS (SELECT 1 FROM pg_trigger t
                     WHERE t.tgname = 'trg_audit_stamp' AND t.tgrelid = 'sgs_question_papers'::regclass) THEN
    EXECUTE 'CREATE TRIGGER trg_audit_stamp BEFORE UPDATE ON sgs_question_papers
             FOR EACH ROW EXECUTE FUNCTION fn_stamp_updated_at()';
  END IF;
END $$;
