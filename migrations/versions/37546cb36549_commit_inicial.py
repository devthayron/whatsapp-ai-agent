from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "37546cb36549"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Atualiza o schema do banco de dados."""

    for table in ("accounts", "messages", "users"):
        op.add_column(
            table,
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.add_column(
            table,
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )

        # Preenche os registros existentes antes de exigir valores não nulos.
        op.execute(
            sa.text(
                f"""
                UPDATE {table}
                SET created_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE created_at IS NULL OR updated_at IS NULL
                """
            )
        )

        op.alter_column(table, "created_at", nullable=False)
        op.alter_column(table, "updated_at", nullable=False)

    op.alter_column(
        "messages",
        "sent_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        postgresql_using="sent_at AT TIME ZONE 'UTC'",
    )

    op.alter_column(
        "users",
        "number",
        existing_type=sa.VARCHAR(length=13),
        type_=sa.String(length=20),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Reverte as alterações do schema."""

    op.alter_column(
        "users",
        "number",
        existing_type=sa.String(length=20),
        type_=sa.VARCHAR(length=13),
        existing_nullable=False,
    )

    op.alter_column(
        "messages",
        "sent_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=False,
        postgresql_using="sent_at AT TIME ZONE 'UTC'",
    )

    for table in ("users", "messages", "accounts"):
        op.drop_column(table, "updated_at")
        op.drop_column(table, "created_at")
