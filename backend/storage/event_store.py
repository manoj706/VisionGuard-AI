from __future__ import annotations

import asyncio
import csv
import io
import json
from collections import defaultdict, deque
from datetime import datetime
from typing import Iterable

from sqlalchemy import Boolean, DateTime, Float, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config import DATABASE_URL
from storage.models import (
    CameraConfig,
    IncidentReport,
    PersonIntelligence,
    SearchFilters,
    SearchResult,
    Sighting,
    SystemHealth,
)


class Base(DeclarativeBase):
    pass


class IncidentRow(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    camera_id: Mapped[str] = mapped_column(String(64))
    person_global_id: Mapped[str] = mapped_column(String(128))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    threat_level: Mapped[str] = mapped_column(String(32))
    threat_score: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(Text)
    clip_url: Mapped[str] = mapped_column(Text)
    thumbnail_url: Mapped[str] = mapped_column(Text)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    activity: Mapped[str] = mapped_column(String(64))
    zone: Mapped[str] = mapped_column(String(64))
    audit_json: Mapped[str] = mapped_column(Text, default="{}")


class PersonSightingRow(Base):
    __tablename__ = "person_sightings"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    global_person_id: Mapped[str] = mapped_column(String(128), index=True)
    camera_id: Mapped[str] = mapped_column(String(64))
    camera_name: Mapped[str] = mapped_column(String(128))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    person_json: Mapped[str] = mapped_column(Text)


class EventStore:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._cameras: dict[str, CameraConfig] = {}
        self._persons_by_camera: dict[str, dict[str, PersonIntelligence]] = defaultdict(dict)
        self._persons: dict[str, PersonIntelligence] = {}
        self._journeys: dict[str, deque[Sighting]] = defaultdict(lambda: deque(maxlen=50))
        self._incidents: deque[IncidentReport] = deque(maxlen=500)
        self._search_index: deque[PersonIntelligence] = deque(maxlen=5000)
        self._last_search_results: list[SearchResult] = []
        self._system_health = SystemHealth(
            cpu_percent=0.0,
            gpu_percent=0.0,
            ram_percent=0.0,
            model_versions={},
        )
        self._engine = create_async_engine(DATABASE_URL, future=True)
        self._sessionmaker = async_sessionmaker(self._engine, expire_on_commit=False)

    async def init_db(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def register_cameras(self, cameras: Iterable[CameraConfig]) -> None:
        async with self._lock:
            for camera in cameras:
                self._cameras[camera.id] = camera

    async def list_cameras(self) -> list[CameraConfig]:
        async with self._lock:
            return list(self._cameras.values())

    async def upsert_camera(self, camera: CameraConfig) -> CameraConfig:
        async with self._lock:
            self._cameras[camera.id] = camera
            return camera

    async def update_scene(
        self,
        camera_id: str,
        persons: list[PersonIntelligence],
        incidents: list[IncidentReport],
        sightings: list[Sighting],
    ) -> None:
        async with self._lock:
            self._persons_by_camera[camera_id] = {
                person.global_person_id: person for person in persons
            }
            for person in persons:
                self._persons[person.global_person_id] = person
                self._search_index.append(person)
            for incident in incidents:
                existing_ids = {item.id for item in self._incidents}
                if incident.id not in existing_ids:
                    self._incidents.appendleft(incident)
            for person in persons:
                self._journeys[person.global_person_id].append(
                    Sighting(
                        camera_id=person.camera_id,
                        camera_name=person.camera_name,
                        location=next(
                            (
                                camera.location
                                for camera in self._cameras.values()
                                if camera.id == person.camera_id
                            ),
                            person.camera_name,
                        ),
                        timestamp=person.timestamp,
                        zone=person.zone,
                        thumbnail_url=person.thumbnail_url,
                        dwell_time_seconds=person.dwell_time_seconds,
                        active=True,
                    )
                )
        await self._persist_scene(persons, incidents)

    async def _persist_scene(
        self,
        persons: list[PersonIntelligence],
        incidents: list[IncidentReport],
    ) -> None:
        async with self._sessionmaker() as session:
            for person in persons:
                await session.merge(
                    PersonSightingRow(
                        id=f"{person.global_person_id}:{person.camera_id}",
                        global_person_id=person.global_person_id,
                        camera_id=person.camera_id,
                        camera_name=person.camera_name,
                        timestamp=person.timestamp,
                        person_json=person.model_dump_json(),
                    )
                )
            for incident in incidents:
                await session.merge(
                    IncidentRow(
                        id=incident.id,
                        camera_id=incident.camera_id,
                        person_global_id=incident.person_global_id,
                        timestamp=incident.timestamp,
                        threat_level=incident.threat_level.value,
                        threat_score=incident.threat_score,
                        description=incident.description,
                        clip_url=incident.clip_url,
                        thumbnail_url=incident.thumbnail_url,
                        acknowledged=incident.acknowledged,
                        acknowledged_by=incident.acknowledged_by,
                        activity=incident.activity,
                        zone=incident.zone,
                        audit_json=incident.audit.model_dump_json() if incident.audit else "{}",
                    )
                )
            await session.commit()

    async def get_persons(self, camera_id: str | None = None) -> list[PersonIntelligence]:
        async with self._lock:
            if camera_id:
                return list(self._persons_by_camera.get(camera_id, {}).values())
            return list(self._persons.values())

    async def get_person(self, global_person_id: str) -> PersonIntelligence | None:
        async with self._lock:
            return self._persons.get(global_person_id)

    async def get_journey(self, global_person_id: str) -> list[Sighting]:
        async with self._lock:
            return list(self._journeys.get(global_person_id, []))

    async def list_incidents(self) -> list[IncidentReport]:
        async with self._lock:
            if self._incidents:
                return list(self._incidents)
        async with self._sessionmaker() as session:
            rows = (await session.execute(select(IncidentRow).order_by(IncidentRow.timestamp.desc()))).scalars().all()
            return [
                IncidentReport(
                    id=row.id,
                    camera_id=row.camera_id,
                    person_global_id=row.person_global_id,
                    timestamp=row.timestamp,
                    threat_level=row.threat_level,
                    threat_score=row.threat_score,
                    description=row.description,
                    clip_url=row.clip_url,
                    thumbnail_url=row.thumbnail_url,
                    acknowledged=row.acknowledged,
                    acknowledged_by=row.acknowledged_by,
                    activity=row.activity,
                    zone=row.zone,
                    audit=json.loads(row.audit_json or "{}"),
                )
                for row in rows
            ]

    async def get_incident(self, incident_id: str) -> IncidentReport | None:
        async with self._lock:
            for incident in self._incidents:
                if incident.id == incident_id:
                    return incident
        async with self._sessionmaker() as session:
            row = await session.get(IncidentRow, incident_id)
            if row:
                return IncidentReport(
                    id=row.id,
                    camera_id=row.camera_id,
                    person_global_id=row.person_global_id,
                    timestamp=row.timestamp,
                    threat_level=row.threat_level,
                    threat_score=row.threat_score,
                    description=row.description,
                    clip_url=row.clip_url,
                    thumbnail_url=row.thumbnail_url,
                    acknowledged=row.acknowledged,
                    acknowledged_by=row.acknowledged_by,
                    activity=row.activity,
                    zone=row.zone,
                    audit=json.loads(row.audit_json or "{}"),
                )
        return None

    async def acknowledge_incident(self, incident_id: str, operator: str) -> IncidentReport | None:
        async with self._lock:
            for incident in self._incidents:
                if incident.id == incident_id:
                    incident.acknowledged = True
                    incident.acknowledged_by = operator
                    result = incident
                    break
            else:
                result = None
        async with self._sessionmaker() as session:
            row = await session.get(IncidentRow, incident_id)
            if row:
                row.acknowledged = True
                row.acknowledged_by = operator
                await session.commit()
        return result

    async def search(self, filters: SearchFilters) -> list[SearchResult]:
        query = filters.query.lower()
        async with self._lock:
            results: list[SearchResult] = []
            for event in list(self._search_index):
                if filters.camera_ids and event.camera_id not in filters.camera_ids:
                    continue
                if filters.threat_levels and event.threat_level not in filters.threat_levels:
                    continue
                if filters.activity and filters.activity != event.activity:
                    continue
                if filters.start_time and event.timestamp < filters.start_time:
                    continue
                if filters.end_time and event.timestamp > filters.end_time:
                    continue
                haystack = " ".join(
                    [
                        event.description,
                        event.upper_colour,
                        event.upper_type,
                        event.lower_colour,
                        event.lower_type,
                        event.activity,
                        event.zone,
                    ]
                ).lower()
                token_hits = sum(1 for token in query.split() if token in haystack)
                if token_hits == 0:
                    continue
                score = min(0.99, 0.35 + (token_hits / max(len(query.split()), 1)) * 0.6)
                results.append(SearchResult(event=event, score=score))
            results.sort(key=lambda item: item.score, reverse=True)
            self._last_search_results = results[:20]
            return self._last_search_results

    async def export_last_search_csv(self) -> str:
        async with self._lock:
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(
                [
                    "timestamp",
                    "camera_name",
                    "global_person_id",
                    "description",
                    "activity",
                    "threat_level",
                    "threat_score",
                    "zone",
                    "similarity_pct",
                ]
            )
            for result in self._last_search_results:
                writer.writerow(
                    [
                        result.event.timestamp.isoformat(),
                        result.event.camera_name,
                        result.event.global_person_id,
                        result.event.description,
                        result.event.activity,
                        result.event.threat_level.value,
                        round(result.event.threat_score, 2),
                        result.event.zone,
                        round(result.score * 100, 1),
                    ]
                )
            return buffer.getvalue()

    async def update_health(self, health: SystemHealth) -> None:
        async with self._lock:
            self._system_health = health

    async def get_health(self) -> SystemHealth:
        async with self._lock:
            return self._system_health

    async def get_stats(self) -> dict:
        async with self._lock:
            persons = list(self._persons.values())
            top_zones: dict[str, int] = defaultdict(int)
            for person in persons:
                top_zones[person.zone] += 1
            return {
                "cameras_online": len([camera for camera in self._cameras.values() if camera.status == "online"]),
                "persons_tracked": len(persons),
                "alerts_today": len(self._incidents),
                "top_zones": sorted(top_zones.items(), key=lambda item: item[1], reverse=True)[:5],
            }

    async def close(self) -> None:
        await self._engine.dispose()
