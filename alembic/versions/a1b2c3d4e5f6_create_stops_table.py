"""create stops table

Revision ID: a1b2c3d4e5f6
Revises: b0ebd22f9e5a
Create Date: 2025-01-19 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'b0ebd22f9e5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create stops table."""
    op.create_table(
        'stops',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trip_id', sa.Integer(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('country', sa.String(length=120), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('trip_id', 'order_index', name='uq_stops_trip_id_order')
    )
    
    # Create indexes
    op.create_index(op.f('ix_stops_id'), 'stops', ['id'], unique=False)
    op.create_index(op.f('ix_stops_trip_id'), 'stops', ['trip_id'], unique=False)
    op.create_index('ix_stops_trip_id_order', 'stops', ['trip_id', 'order_index'], unique=False)


def downgrade() -> None:
    """Drop stops table."""
    op.drop_index('ix_stops_trip_id_order', table_name='stops')
    op.drop_index(op.f('ix_stops_trip_id'), table_name='stops')
    op.drop_index(op.f('ix_stops_id'), table_name='stops')
    op.drop_table('stops')
