from __future__ import annotations

import asyncio

from app.db.session import SessionLocal
from app.services.container import get_container
from app.utils.logging import configure_logging, get_logger


async def worker_loop() -> None:
    logger = get_logger("worker")
    runtime = get_container().runtime
    ml = get_container().ml
    cycle_count = 0
    retrain_every = 60  # Переобучать каждые 60 циклов (10 минут при цикле 10 сек)

    while True:
        async with SessionLocal() as session:
            try:
                result = await runtime.cycle(session)
                await session.commit()
                logger.info("runtime_cycle_completed", **result)

                cycle_count += 1
                if cycle_count >= retrain_every:
                    try:
                        logger.info("auto_retrain_starting", cycle=cycle_count)
                        train_result = await ml.train(session)
                        await session.commit()
                        logger.info("auto_retrain_completed", **train_result)
                        cycle_count = 0
                    except Exception:
                        logger.exception("auto_retrain_failed")

            except Exception:
                await session.rollback()
                logger.exception("runtime_cycle_failed")
        await asyncio.sleep(runtime.settings.RUNTIME_LOOP_SECONDS)


def main() -> None:
    configure_logging()
    asyncio.run(worker_loop())


if __name__ == "__main__":
    main()
