"""bind approvals to immutable SQL and dataset fingerprints

Revision ID: 0002_bind_sql_approvals
Revises: 0001_initial_schema
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_bind_sql_approvals"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("generated_sql_queries", sa.Column("approved_sql_hash", sa.String(length=64), nullable=True))
    op.add_column("generated_sql_queries", sa.Column("approved_dataset_fingerprint", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("generated_sql_queries", "approved_dataset_fingerprint")
    op.drop_column("generated_sql_queries", "approved_sql_hash")
