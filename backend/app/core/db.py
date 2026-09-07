from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    from app import models  # noqa: F401 — import all models so Base sees them
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_apply_sqlite_migrations)


def _apply_sqlite_migrations(connection):
    """Apply additive migrations for the local SQLite development database."""
    if connection.dialect.name != "sqlite":
        return
    migrations = {
        "jds": {
            "updated_at": "DATETIME", "status": "VARCHAR DEFAULT 'draft' NOT NULL",
            "posted_by": "INTEGER", "is_published": "BOOLEAN DEFAULT 0 NOT NULL",
            "location": "VARCHAR", "employment_type": "VARCHAR",
        },
        "assessments": {
            "application_id": "INTEGER", "overall_score": "FLOAT",
            "readiness_score": "FLOAT", "summary": "TEXT",
        },
    }
    for table, columns in migrations.items():
        existing = {row[1] for row in connection.exec_driver_sql(f"PRAGMA table_info({table})")}
        for column, definition in columns.items():
            if column not in existing:
                connection.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
