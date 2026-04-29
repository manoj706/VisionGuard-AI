from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine

from config import DATABASE_URL, RETENTION_DAYS
from storage.event_store import IncidentRow, PersonSightingRow


async def purge_old_data(storage_path: str) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    engine = create_async_engine(DATABASE_URL, future=True)
    async with engine.begin() as conn:
        await conn.execute(delete(IncidentRow).where(IncidentRow.timestamp < cutoff))
        await conn.execute(delete(PersonSightingRow).where(PersonSightingRow.timestamp < cutoff))
    await engine.dispose()
    for folder in ["thumbnails", "clips"]:
        path = Path(storage_path) / folder
        if not path.exists():
            continue
        for child in path.iterdir():
            if child.is_file() and datetime.fromtimestamp(child.stat().st_mtime, timezone.utc) < cutoff:
                child.unlink(missing_ok=True)


def start_retention_scheduler(storage_path: str) -> asyncio.Task:
    async def loop() -> None:
        while True:
            now = datetime.now(timezone.utc)
            next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            await asyncio.sleep((next_run - now).total_seconds())
            await purge_old_data(storage_path)

    return asyncio.create_task(loop())
