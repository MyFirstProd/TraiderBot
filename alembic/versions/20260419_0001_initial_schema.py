"""initial schema

Revision ID: 20260419_0001
Revises:
Create Date: 2026-04-19
"""

from alembic import op
import sqlalchemy as sa


revision = "20260419_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255)),
        sa.Column("first_name", sa.String(length=255)),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    for table_name, extra_columns in {
        "bot_settings": [sa.Column("key", sa.String(length=100), nullable=False), sa.Column("value", sa.Text(), nullable=False)],
        "strategy_configs": [
            sa.Column("symbol", sa.String(length=20), nullable=False),
            sa.Column("market_mode", sa.String(length=20), nullable=False),
            sa.Column("is_enabled", sa.Boolean(), nullable=False),
            sa.Column("ma_type", sa.String(length=10), nullable=False),
            sa.Column("ema_fast", sa.Integer(), nullable=False),
            sa.Column("ema_slow", sa.Integer(), nullable=False),
            sa.Column("sma_fast", sa.Integer(), nullable=False),
            sa.Column("sma_slow", sa.Integer(), nullable=False),
            sa.Column("wma_period", sa.Integer(), nullable=False),
            sa.Column("rsi_period", sa.Integer(), nullable=False),
            sa.Column("risk_pct", sa.Float(), nullable=False),
            sa.Column("min_model_score", sa.Float(), nullable=False),
            sa.Column("max_spread_bps", sa.Float(), nullable=False),
        ],
        "market_snapshots": [
            sa.Column("symbol", sa.String(length=20), nullable=False),
            sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("price", sa.Float(), nullable=False),
            sa.Column("bid", sa.Float(), nullable=False),
            sa.Column("ask", sa.Float(), nullable=False),
            sa.Column("high", sa.Float(), nullable=False),
            sa.Column("low", sa.Float(), nullable=False),
            sa.Column("volume", sa.Float(), nullable=False),
            sa.Column("volatility_bps", sa.Float(), nullable=False),
            sa.Column("orderbook_imbalance", sa.Float(), nullable=False),
            sa.Column("trade_imbalance", sa.Float(), nullable=False),
            sa.Column("is_synthetic", sa.Boolean(), nullable=False),
        ],
        "signals": [
            sa.Column("symbol", sa.String(length=20), nullable=False),
            sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("direction", sa.String(length=20), nullable=False),
            sa.Column("score", sa.Float(), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.Column("should_trade", sa.Boolean(), nullable=False),
            sa.Column("rationale", sa.JSON(), nullable=False),
            sa.Column("indicators_snapshot", sa.JSON(), nullable=False),
        ],
        "positions": [
            sa.Column("symbol", sa.String(length=20), nullable=False),
            sa.Column("side", sa.String(length=10), nullable=False),
            sa.Column("quantity", sa.Float(), nullable=False),
            sa.Column("entry_price", sa.Float(), nullable=False),
            sa.Column("stop_price", sa.Float(), nullable=False),
            sa.Column("take_price", sa.Float(), nullable=False),
            sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("closed_at", sa.DateTime(timezone=True)),
            sa.Column("is_open", sa.Boolean(), nullable=False),
            sa.Column("explanation", sa.JSON(), nullable=False),
        ],
        "trades": [
            sa.Column("symbol", sa.String(length=20), nullable=False),
            sa.Column("side", sa.String(length=10), nullable=False),
            sa.Column("quantity", sa.Float(), nullable=False),
            sa.Column("entry_price", sa.Float(), nullable=False),
            sa.Column("exit_price", sa.Float(), nullable=False),
            sa.Column("pnl", sa.Float(), nullable=False),
            sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("closed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("reason", sa.String(length=100), nullable=False),
            sa.Column("explanation", sa.JSON(), nullable=False),
        ],
        "risk_events": [
            sa.Column("event_type", sa.String(length=100), nullable=False),
            sa.Column("severity", sa.String(length=20), nullable=False),
            sa.Column("symbol", sa.String(length=20)),
            sa.Column("details", sa.JSON(), nullable=False),
        ],
        "news_events": [
            sa.Column("source", sa.String(length=100), nullable=False),
            sa.Column("title", sa.String(length=500), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("language", sa.String(length=10), nullable=False),
            sa.Column("sentiment", sa.Float(), nullable=False),
            sa.Column("relevance", sa.Float(), nullable=False),
            sa.Column("novelty", sa.Float(), nullable=False),
            sa.Column("entities", sa.JSON(), nullable=False),
            sa.Column("symbol_relevance", sa.JSON(), nullable=False),
        ],
        "whale_events": [
            sa.Column("asset", sa.String(length=20), nullable=False),
            sa.Column("chain", sa.String(length=30), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False),
            sa.Column("usd_value", sa.Float(), nullable=False),
            sa.Column("from_type", sa.String(length=50), nullable=False),
            sa.Column("to_type", sa.String(length=50), nullable=False),
            sa.Column("exchange_related", sa.Boolean(), nullable=False),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
            sa.Column("significance_score", sa.Float(), nullable=False),
        ],
        "llm_inferences": [
            sa.Column("provider", sa.String(length=50), nullable=False),
            sa.Column("model", sa.String(length=100), nullable=False),
            sa.Column("task_type", sa.String(length=50), nullable=False),
            sa.Column("prompt_hash", sa.String(length=64), nullable=False),
            sa.Column("input_excerpt", sa.Text(), nullable=False),
            sa.Column("response_json", sa.JSON(), nullable=False),
        ],
        "audit_logs": [
            sa.Column("actor", sa.String(length=100), nullable=False),
            sa.Column("action", sa.String(length=100), nullable=False),
            sa.Column("target", sa.String(length=100), nullable=False),
            sa.Column("details", sa.JSON(), nullable=False),
        ],
    }.items():
        op.create_table(
            table_name,
            sa.Column("id", sa.Integer(), primary_key=True),
            *extra_columns,
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )


def downgrade() -> None:
    for table_name in [
        "audit_logs",
        "llm_inferences",
        "whale_events",
        "news_events",
        "risk_events",
        "trades",
        "positions",
        "signals",
        "market_snapshots",
        "strategy_configs",
        "bot_settings",
        "users",
    ]:
        op.drop_table(table_name)
