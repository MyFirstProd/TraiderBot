import os

import pytest

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "x" * 32
os.environ["ADMIN_API_KEY"] = "y" * 32

from app.db.bootstrap import create_all
from app.db.session import SessionLocal, engine
from app.services.container import get_container


@pytest.mark.asyncio
async def test_runtime_cycle_executes():
    await create_all(engine)
    runtime = get_container().runtime
    runtime.trading_enabled = True
    async with SessionLocal() as session:
        result = await runtime.cycle(session)
    assert "decisions" in result
