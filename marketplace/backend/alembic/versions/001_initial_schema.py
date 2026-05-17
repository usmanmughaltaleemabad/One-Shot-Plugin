"""Initial database schema with all marketplace tables

Revision ID: 001
Revises:
Create Date: 2026-05-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_creator", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("stripe_customer_id", sa.String(255)),
        sa.Column("stripe_account_id", sa.String(255)),
        sa.Column("bio", sa.Text()),
        sa.Column("avatar_url", sa.String(255)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("stripe_customer_id"),
        sa.UniqueConstraint("stripe_account_id"),
    )
    op.create_index("idx_email_active", "users", ["email", "is_active"])
    op.create_index("idx_creator_active", "users", ["is_creator", "is_active"])
    op.create_index("idx_users_email", "users", ["email"])

    # Create agents table
    op.create_table(
        "agents",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("creator_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("markdown_content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("keywords", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("version", sa.String(50), nullable=False, server_default="0.1.0"),
        sa.Column("price_usd", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("rating", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("rating_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("install_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("published_at", sa.DateTime()),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("creator_id", "slug", name="uq_creator_slug"),
    )
    op.create_index("idx_agents_creator_id", "agents", ["creator_id"])
    op.create_index("idx_agents_category", "agents", ["category"])
    op.create_index("idx_status_published", "agents", ["status", "published_at"])
    op.create_index("idx_category_rating", "agents", ["category", "rating"])
    op.create_index("idx_public_status", "agents", ["is_public", "status"])

    # Create agent_versions table
    op.create_table(
        "agent_versions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("agent_id", sa.String(36), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("markdown_content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id", "version", name="uq_agent_version"),
    )
    op.create_index("idx_agent_versions_agent_id", "agent_versions", ["agent_id"])

    # Create subscriptions table
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("agent_id", sa.String(36), nullable=False),
        sa.Column("stripe_subscription_id", sa.String(255)),
        sa.Column("stripe_customer_id", sa.String(255)),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("price_usd", sa.Integer()),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("current_period_end", sa.DateTime(), nullable=False),
        sa.Column("canceled_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_subscription_id"),
    )
    op.create_index("idx_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_index("idx_subscriptions_agent_id", "subscriptions", ["agent_id"])
    op.create_index("idx_user_status", "subscriptions", ["user_id", "status"])
    op.create_index("idx_agent_status", "subscriptions", ["agent_id", "status"])
    op.create_index("idx_period_end", "subscriptions", ["current_period_end"])

    # Create ratings table
    op.create_table(
        "ratings",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("agent_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("review", sa.Text()),
        sa.Column("helpful_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id", "user_id", name="uq_agent_user_rating"),
    )
    op.create_index("idx_ratings_agent_id", "ratings", ["agent_id"])
    op.create_index("idx_agent_rating", "ratings", ["agent_id", "rating"])

    # Create transactions table
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("user_id", sa.String(36)),
        sa.Column("agent_id", sa.String(36)),
        sa.Column("amount_usd", sa.Integer()),
        sa.Column("platform_fee_usd", sa.Integer()),
        sa.Column("creator_payout_usd", sa.Integer()),
        sa.Column("stripe_charge_id", sa.String(255)),
        sa.Column("stripe_transaction_id", sa.String(255)),
        sa.Column("metadata", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_transaction_id"),
    )
    op.create_index("idx_transactions_user_id", "transactions", ["user_id"])
    op.create_index("idx_transactions_agent_id", "transactions", ["agent_id"])
    op.create_index("idx_type_date", "transactions", ["type", "created_at"])
    op.create_index("idx_user_date", "transactions", ["user_id", "created_at"])

    # Create payouts table
    op.create_table(
        "payouts",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("creator_id", sa.String(36), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("total_revenue_usd", sa.Integer(), nullable=False),
        sa.Column("platform_fee_usd", sa.Integer(), nullable=False),
        sa.Column("amount_paid_usd", sa.Integer(), nullable=False),
        sa.Column("stripe_payout_id", sa.String(255)),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("paid_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("creator_id", "month", "year", name="uq_creator_month_year"),
        sa.UniqueConstraint("stripe_payout_id"),
    )
    op.create_index("idx_payouts_creator_id", "payouts", ["creator_id"])
    op.create_index("idx_creator_status", "payouts", ["creator_id", "status"])


def downgrade() -> None:
    op.drop_table("payouts")
    op.drop_table("transactions")
    op.drop_table("ratings")
    op.drop_table("subscriptions")
    op.drop_table("agent_versions")
    op.drop_table("agents")
    op.drop_table("users")
