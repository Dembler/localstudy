from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.infrastructure.database import Base
from src.infrastructure.models import PlanModel
from src.infrastructure.seed import seed_demo_data


async def test_demo_seed_repairs_missing_records(tmp_path) -> None:
    database_path = tmp_path / "partial-seed.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path.as_posix()}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        await seed_demo_data(session_factory)
        async with session_factory() as session:
            await session.execute(delete(PlanModel).where(PlanModel.id == "demo-plan"))
            await session.commit()

        await seed_demo_data(session_factory)
        async with session_factory() as session:
            restored = await session.scalar(select(PlanModel).where(PlanModel.id == "demo-plan"))
            assert restored is not None
    finally:
        await engine.dispose()
