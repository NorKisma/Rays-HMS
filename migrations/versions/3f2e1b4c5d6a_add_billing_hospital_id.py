"""Add tenant hospital_id to Billing and BillingItem tables

Revision ID: 3f2e1b4c5d6a
Revises: 59be476927ef
Create Date: 2026-04-20 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3f2e1b4c5d6a'
down_revision = '59be476927ef'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    for table_name in ('billings', 'billing_items'):
        existing = conn.execute(
            sa.text("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=:table AND COLUMN_NAME='hospital_id'"),
            {'table': table_name}
        ).scalar()
        if existing:
            continue

        with op.batch_alter_table(table_name, schema=None) as batch_op:
            batch_op.add_column(sa.Column('hospital_id', sa.Integer(), sa.ForeignKey('hospitals.id'), nullable=True))


def downgrade():
    with op.batch_alter_table('billing_items', schema=None) as batch_op:
        batch_op.drop_column('hospital_id')

    with op.batch_alter_table('billings', schema=None) as batch_op:
        batch_op.drop_column('hospital_id')
