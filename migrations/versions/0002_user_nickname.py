"""lab 4: 사용자 nickname 추가."""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("nickname", sa.String(50), nullable=True))


def downgrade():
    op.drop_column("users", "nickname")
