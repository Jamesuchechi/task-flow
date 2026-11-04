"""added auth

Revision ID: 7c5db14cf50b
Revises: 69b05f6b0d69
Create Date: 2026-11-04 14:23:26.575384

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c5db14cf50b'
down_revision: Union[str, Sequence[str], None] = '69b05f6b0d69'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    task_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM tasks")
    ).scalar_one()
    user_ids = connection.execute(
        sa.text("SELECT id FROM users ORDER BY id")
    ).scalars().all()

    if task_count and len(user_ids) != 1:
        raise RuntimeError(
            "Cannot migrate existing tasks: expected exactly one user to own "
            f"them, found {len(user_ids)}. Assign the tasks to a user and retry."
        )

    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(sa.Column("owner_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_tasks_owner_id_users",
            "users",
            ["owner_id"],
            ["id"],
        )

    if task_count:
        connection.execute(
            sa.text("UPDATE tasks SET owner_id = :owner_id"),
            {"owner_id": user_ids[0]},
        )

    with op.batch_alter_table("tasks") as batch_op:
        batch_op.alter_column(
            "owner_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.drop_column("updated_at")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))
        batch_op.drop_constraint("fk_tasks_owner_id_users", type_="foreignkey")
        batch_op.drop_column("owner_id")

    op.execute(
        sa.text(
            "UPDATE tasks SET updated_at = CURRENT_TIMESTAMP "
            "WHERE updated_at IS NULL"
        )
    )

    with op.batch_alter_table("tasks") as batch_op:
        batch_op.alter_column(
            "updated_at",
            existing_type=sa.DateTime(),
            nullable=False,
        )
