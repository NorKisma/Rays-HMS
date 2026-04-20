"""Add tenant hospital_id to doctors table

Revision ID: 4a9b7c8d2e1f
Revises: 3f2e1b4c5d6a
Create Date: 2026-04-20 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4a9b7c8d2e1f'
down_revision = '3f2e1b4c5d6a'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    existing = conn.execute(
        sa.text("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='doctors' AND COLUMN_NAME='hospital_id'")
    ).scalar()
    if existing:
        return

    with op.batch_alter_table('doctors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('hospital_id', sa.Integer(), sa.ForeignKey('hospitals.id'), nullable=True))


def downgrade():
    with op.batch_alter_table('doctors', schema=None) as batch_op:
        batch_op.drop_column('hospital_id')
