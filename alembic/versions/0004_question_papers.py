"""Create sgs_question_papers — saved auto-test papers

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-19

The shared RDS instances are not migrated by this app (the app user has no
DDL rights there); this file documents the schema and applies it to local
databases. For staging/production, run the SQL in ../sql/0004_question_papers.sql
through the DB-access process.
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sgs_question_papers",
        sa.Column("paper_id", sa.BigInteger, primary_key=True, autoincrement=True),
        # varchar: matches sgs_teacher_master.teacher_id and every sibling table
        sa.Column("teacher_id", sa.String,
                  sa.ForeignKey("sgs_teacher_master.teacher_id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("chapter_id", sa.BigInteger, nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(150), nullable=True),
        sa.Column("difficulty", sa.String(20), nullable=True),
        sa.Column("total_marks", sa.Integer, nullable=True),
        sa.Column("question_type", sa.String(30), nullable=True),
        sa.Column("paper_text", sa.Text, nullable=True),
        sa.Column("questions", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=True),
        # audit set shared by every sgs_ table
        sa.Column("created_user_id", sa.String(100), nullable=True),
        sa.Column("created_ip_address", sa.String(50), nullable=True),
        sa.Column("modified_datetime", sa.DateTime, nullable=True),
        sa.Column("modified_user_id", sa.String(100), nullable=True),
        sa.Column("modified_ip_address", sa.String(50), nullable=True),
        sa.Column("record_status", sa.String(20), server_default="Active", nullable=True),
        sa.Column("version_no", sa.Integer, server_default="1", nullable=True),
        sa.Column("updated_at", sa.DateTime, nullable=True),
        sa.CheckConstraint("paper_text IS NOT NULL OR questions IS NOT NULL",
                           name="ck_question_papers_has_content"),
    )
    op.create_index("ix_sgs_question_papers_teacher_id", "sgs_question_papers", ["teacher_id"])


def downgrade() -> None:
    op.drop_index("ix_sgs_question_papers_teacher_id", table_name="sgs_question_papers")
    op.drop_table("sgs_question_papers")
