"""Allow multiple anomalies per observation

Revision ID: e3f5c2a1b8d9
Revises: 14b1be682e17
Create Date: 2026-07-27 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3f5c2a1b8d9'
down_revision: Union[str, None] = '14b1be682e17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove unique constraint on observation_id to allow multiple algorithms to flag same observation
    # First, drop the unique constraint if it exists
    try:
        op.drop_constraint('detected_anomalies_observation_id_key', 'detected_anomalies', type_='unique')
    except:
        pass
    
    # Add index to observation_id for query performance
    try:
        op.create_index('ix_detected_anomalies_observation_id', 'detected_anomalies', ['observation_id'])
    except:
        pass


def downgrade() -> None:
    # Restore unique constraint (though this may fail if duplicate data exists)
    try:
        op.drop_index('ix_detected_anomalies_observation_id', table_name='detected_anomalies')
    except:
        pass
    
    try:
        op.create_unique_constraint('detected_anomalies_observation_id_key', 'detected_anomalies', ['observation_id'])
    except:
        pass
