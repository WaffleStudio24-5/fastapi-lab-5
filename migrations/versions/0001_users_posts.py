"""lab 4: users와 posts 생성."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
    )
    op.create_table(
        "posts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
    )


def downgrade():
    op.drop_table("posts")
    op.drop_table("users")
