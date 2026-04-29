from __future__ import annotations

import asyncio
import base64
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import psutil
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageDraw, ImageFilter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from api.routes import limiter, router as api_router
from api.websocket import ConnectionManager, router as websocket_router
from config import MEDIA_ROOT, PRIVACY_MODE, RETENTION_DAYS, get_runtime_settings
from pipeline.appearance import AppearanceAnalyser
from pipeline.behaviour import BehaviourAnalyser
from pipeline.clip_engine import CLIPEngine
from pipeline.crowd import CrowdAnalyser
from pipeline.detector import SceneDetector
from pipeline.fusion import SceneFusion
from pipeline.ingestor import FrameIngestor, default_mock_cameras
from pipeline.pose import PoseAnalyser
from pipeline.reid import ReIDEngine
from pipeline.tracker import PersonTracker
from storage.event_store import EventStore
from storage.models import Sighting, SystemHealth
from storage.retention import start_retention_scheduler


def _ensure_media_dirs() -> Path:
    root = Path(MEDIA_ROOT)
    (root / "thumbnails").mkdir(parents=True, exist_ok=True)
    (root / "clips").mkdir(parents=True, exist_ok=True)
    return root


def _save_thumbnail(global_person_id: str, bbox: tuple[int, int, int, int], image_array: np.ndarray) -> None:
    x1, y1, x2, y2 = bbox
    crop = image_array[max(y1, 0):max(y2, 1), max(x1, 0):max(x2, 1)]
    if crop.size == 0:
        crop = np.zeros((120, 80, 3), dtype=np.uint8)
    image = Image.fromarray(crop.astype("uint8"), "RGB")
    blur = image.filter(ImageFilter.GaussianBlur(radius=8))
    if PRIVACY_MODE == "strict":
        image = blur
    else:
        draw = ImageDraw.Draw(image)
        width, height = image.size
        face_box = (
            width * 0.25,
            height * 0.1,
            width * 0.75,
            height * 0.45,
        )
        face_crop = image.crop(face_box).filter(ImageFilter.GaussianBlur(radius=6))
        image.paste(face_crop, face_box)
        draw.rectangle((0, height - 18, width, height), fill=(10, 10, 16))
    image.save(Path(MEDIA_ROOT) / "thumbnails" / f"{global_person_id}.jpg", format="JPEG")


async def _pipeline_loop(app: FastAPI) -> None:
    settings = get_runtime_settings()
    ingestor = FrameIngestor(app.state.cameras)
    detector = SceneDetector()
    tracker = PersonTracker()
    appearance = AppearanceAnalyser()
    pose = PoseAnalyser()
    behaviour = BehaviourAnalyser()
    clip_engine = CLIPEngine()
    reid = ReIDEngine()
    crowd = CrowdAnalyser()
    fusion = SceneFusion()

    async for frame in ingestor.stream():
        cpu_percent = psutil.cpu_percent()
        ram_percent = psutil.virtual_memory().percent
        degraded_mode = cpu_percent > 85
        detection_result = detector.detect(frame)
        tracked = tracker.update(detection_result.persons, frame)
        raw_people = {item["actor_id"]: item for item in (frame.raw or {}).get("persons", [])}

        intelligence = []
        incidents = []
        sightings = []
        for track in tracked:
            payload = raw_people.get(track.crop.decode() if track.crop else "", {})
            x1, y1, x2, y2 = track.bbox
            crop = frame.raw["image"][max(y1, 0):max(y2, 1), max(x1, 0):max(x2, 1)]
            payload = {
                **payload,
                "upper_crop": crop[: max(crop.shape[0] // 2, 1)] if getattr(crop, "size", 0) else None,
                "lower_crop": crop[max(crop.shape[0] // 2, 1):] if getattr(crop, "size", 0) else None,
                "crop_image": crop if getattr(crop, "size", 0) else None,
                "pil_image": Image.fromarray(crop.astype("uint8"), "RGB") if getattr(crop, "size", 0) else None,
            }
            appearance_result = appearance.analyse(payload)
            pose_result = pose.analyse(payload if not degraded_mode or track.track_id % 2 == 0 else {})
            behaviour_result = behaviour.analyse(track, pose_result, payload)
            embedding = clip_engine.embed_crop(payload)
            clip_score = clip_engine.threat_score(embedding, payload) if not degraded_mode or track.track_id % 2 == 0 else 0.2
            global_id = reid.identify(track, appearance_result)
            person = fusion.process_person(
                track=track,
                global_person_id=global_id,
                appearance=appearance_result,
                pose=pose_result,
                behaviour=behaviour_result,
                clip_score=clip_score,
                embedding_bytes=clip_engine.serialize_embedding(embedding),
                camera_name=frame.camera_name,
                degraded_mode=degraded_mode,
            )
            _save_thumbnail(global_id, track.bbox, frame.raw["image"])
            sighting = Sighting(
                camera_id=frame.camera_id,
                camera_name=frame.camera_name,
                location=frame.location,
                timestamp=frame.timestamp,
                zone=person.zone,
                thumbnail_url=person.thumbnail_url,
                dwell_time_seconds=person.dwell_time_seconds,
                active=True,
            )
            reid.update_journey(global_id, sighting)
            sightings.append(sighting)
            incident = fusion.maybe_create_incident(person)
            if incident:
                incidents.append(incident)
                await app.state.connection_manager.broadcast(
                    {
                        "type": "alert",
                        "incidentId": incident.id,
                        "cameraId": person.camera_id,
                        "cameraName": person.camera_name,
                        "globalPersonId": person.global_person_id,
                        "threatLevel": person.threat_level.value,
                        "threatScore": person.threat_score,
                        "description": person.description,
                        "thumbnailUrl": person.thumbnail_url,
                        "clipUrl": incident.clip_url,
                        "timestamp": person.timestamp.isoformat(),
                    }
                )
            intelligence.append(person)

        crowd_result = crowd.analyse(tracked, frame)
        await app.state.event_store.update_scene(frame.camera_id, intelligence, incidents, sightings)
        app.state.latest_heatmap = {
            "camera_id": frame.camera_id,
            "density_map": crowd_result.density_map,
            "flow_vectors": crowd_result.flow_vectors,
            "high_density_zones": crowd_result.high_density_zones,
            "congestion_score": crowd_result.congestion_score,
        }
        await app.state.event_store.update_health(
            SystemHealth(
                cpu_percent=cpu_percent,
                gpu_percent=0.0,
                ram_percent=ram_percent,
                degraded_mode=degraded_mode,
                privacy_mode=settings.privacy_mode,
                retention_days=RETENTION_DAYS,
                hardware_profile=settings.hardware_profile,
                model_versions={
                    "detector": settings.detector,
                    "appearance": settings.appearance_model,
                    "clip": settings.clip_model,
                },
                cameras=[
                    {
                        "id": camera.id,
                        "fps": settings.target_fps,
                        "persons_tracked": len(intelligence) if camera.id == frame.camera_id else 0,
                        "status": camera.status,
                    }
                    for camera in app.state.cameras
                ],
            )
        )
        await app.state.connection_manager.broadcast(
            {
                "type": "scene_update",
                "cameraId": frame.camera_id,
                "timestamp": frame.timestamp.isoformat(),
                "persons": [
                    {
                        "trackId": person.track_id,
                        "globalPersonId": person.global_person_id,
                        "cameraId": person.camera_id,
                        "bbox": list(person.bbox),
                        "threatLevel": person.threat_level.value,
                        "threatScore": person.threat_score,
                        "description": person.description,
                        "activity": person.activity,
                        "upperColour": person.upper_colour,
                        "upperType": person.upper_type,
                        "lowerColour": person.lower_colour,
                        "lowerType": person.lower_type,
                        "hasBag": person.has_bag,
                        "bagType": person.bag_type,
                        "dwellTime": person.dwell_time_seconds,
                        "zone": person.zone,
                        "thumbnailUrl": person.thumbnail_url,
                    }
                    for person in intelligence
                ],
                "crowdCount": crowd_result.total_count,
                "densityGrid": crowd_result.density_map,
            }
        )
        await app.state.connection_manager.broadcast(
            {
                "type": "heartbeat",
                "cameras": [
                    {
                        "id": camera.id,
                        "fps": settings.target_fps,
                        "persons_tracked": len(intelligence) if camera.id == frame.camera_id else 0,
                        "status": camera.status,
                    }
                    for camera in app.state.cameras
                ],
                "system": {
                    "cpu_percent": cpu_percent,
                    "gpu_percent": 0.0,
                    "ram_percent": ram_percent,
                },
            }
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    media_root = _ensure_media_dirs()
    app.state.cameras = default_mock_cameras()
    app.state.event_store = EventStore()
    app.state.connection_manager = ConnectionManager()
    app.state.latest_heatmap = {}
    await app.state.event_store.init_db()
    await app.state.event_store.register_cameras(app.state.cameras)
    app.state.pipeline_task = asyncio.create_task(_pipeline_loop(app))
    app.state.retention_task = start_retention_scheduler(str(media_root))
    yield
    app.state.pipeline_task.cancel()
    app.state.retention_task.cancel()
    await app.state.event_store.close()


app = FastAPI(title="VisionGuardAI", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/api/media", StaticFiles(directory=MEDIA_ROOT), name="media")
app.include_router(api_router)
app.include_router(websocket_router)


@app.get("/")
async def root():
    return {"service": "VisionGuardAI", "timestamp": datetime.now(timezone.utc).isoformat()}
