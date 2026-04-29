from __future__ import annotations

import asyncio
import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncGenerator
from uuid import uuid4

import numpy as np

from config import get_runtime_settings
from storage.models import CameraConfig, Frame, Zone


class CameraSource(str, Enum):
    RTSP = "rtsp"
    USB = "usb"
    HLS = "hls"
    FILE = "file"
    MOCK = "mock"


@dataclass(slots=True)
class MockActor:
    actor_id: str
    seed: int
    upper_colour: str
    upper_type: str
    lower_colour: str
    lower_type: str
    bag_type: str
    height: str
    build: str
    current_camera: str


class FrameIngestor:
    def __init__(self, cameras: list[CameraConfig]) -> None:
        self.settings = get_runtime_settings()
        self.cameras = cameras
        self._frame_no = 0
        self._actors = self._build_mock_actors()

    def _build_mock_actors(self) -> list[MockActor]:
        palettes = [
            ("red", "jacket", "black", "jeans", "backpack", "tall", "medium"),
            ("blue", "hoodie", "grey", "trousers", "none", "medium", "slim"),
            ("white", "shirt", "blue", "jeans", "handbag", "short", "medium"),
            ("green", "uniform", "black", "trousers", "shoulder_bag", "medium", "heavy"),
            ("yellow", "t-shirt", "brown", "shorts", "none", "medium", "slim"),
            ("black", "hoodie", "black", "trousers", "suitcase", "tall", "heavy"),
        ]
        actors: list[MockActor] = []
        for idx in range(12):
            profile = palettes[idx % len(palettes)]
            actors.append(
                MockActor(
                    actor_id=f"actor_{idx:02d}",
                    seed=idx + 7,
                    upper_colour=profile[0],
                    upper_type=profile[1],
                    lower_colour=profile[2],
                    lower_type=profile[3],
                    bag_type=profile[4],
                    height=profile[5],
                    build=profile[6],
                    current_camera=self.cameras[idx % len(self.cameras)].id,
                )
            )
        return actors

    async def stream(self) -> AsyncGenerator[Frame, None]:
        target_delay = 1 / max(self.settings.target_fps, 1)
        while True:
            await asyncio.sleep(0)
            now = datetime.now(timezone.utc)
            self._frame_no += 1
            for index, camera in enumerate(self.cameras):
                payload = self._generate_camera_payload(camera, index, now)
                yield Frame(
                    frame_id=f"{camera.id}-{self._frame_no}",
                    camera_id=camera.id,
                    camera_name=camera.name,
                    location=camera.location,
                    timestamp=now,
                    raw=payload,
                    width=640,
                    height=480,
                )
                await asyncio.sleep(0)
            await asyncio.sleep(target_delay)

    def _generate_camera_payload(
        self,
        camera: CameraConfig,
        camera_index: int,
        now: datetime,
    ) -> dict[str, Any]:
        t = self._frame_no / 10.0
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        image[:] = (24, 28, 34)

        active_actors = []
        for actor_index, actor in enumerate(self._actors):
            if actor_index == 0 and self._frame_no % (5 * self.settings.target_fps) == 0:
                actor.current_camera = self.cameras[(camera_index + 1) % len(self.cameras)].id
            if actor.current_camera != camera.id:
                continue

            local_t = t + actor.seed + camera_index
            x = int(40 + ((math.sin(local_t * 0.7) + 1) / 2) * 500)
            y = int(40 + ((math.cos(local_t * 0.5) + 1) / 2) * 280)
            w = 55 + (actor_index % 3) * 8
            h = 130 + (actor_index % 2) * 18
            bbox = (x, y, min(x + w, 620), min(y + h, 470))
            threat_wave = (math.sin(t * 0.4 + actor.seed) + 1) / 2
            behaviour = "walking_normal"
            alert_kind = None
            if actor_index == 0 and int(t) % 90 in {0, 1, 2}:
                behaviour = "running"
                alert_kind = "person_of_interest"
                threat_wave = 0.92
            elif threat_wave > 0.82:
                behaviour = "loitering"
            elif threat_wave > 0.68:
                behaviour = "running"

            colour = {
                "red": (60, 60, 220),
                "blue": (220, 100, 60),
                "white": (225, 225, 225),
                "green": (80, 180, 90),
                "yellow": (60, 210, 210),
                "black": (25, 25, 25),
            }.get(actor.upper_colour, (160, 160, 160))
            x1, y1, x2, y2 = bbox
            image[y1:y2, x1:x2] = colour

            active_actors.append(
                {
                    "actor_id": actor.actor_id,
                    "bbox": bbox,
                    "confidence": round(0.78 + (actor_index % 4) * 0.04, 2),
                    "upper_colour": actor.upper_colour,
                    "upper_type": actor.upper_type,
                    "lower_colour": actor.lower_colour,
                    "lower_type": actor.lower_type,
                    "bag_type": actor.bag_type,
                    "has_bag": actor.bag_type != "none",
                    "has_hat": actor_index % 5 == 0,
                    "hat_type": "cap" if actor_index % 5 == 0 else "none",
                    "estimated_height": actor.height,
                    "build": actor.build,
                    "activity_hint": behaviour,
                    "threat_wave": threat_wave,
                    "alert_kind": alert_kind,
                }
            )

        crowd_density = max(1, int(5 + 4 * math.sin(t / 8 + camera_index)))
        return {
            "image": image,
            "persons": active_actors,
            "objects": [],
            "crowd_density": crowd_density,
            "alert_window": int(t) % 90 in {0, 1, 2},
            "camera_status": "online",
            "generated_at": now.isoformat(),
            "frame_token": str(uuid4()),
        }


def default_mock_cameras() -> list[CameraConfig]:
    return [
        CameraConfig(
            id="cam_01",
            name="Main Entrance",
            location="East Exit",
            source_url="mock://cam_01",
            source_type=CameraSource.MOCK.value,
            zones=[
                Zone(name="entrance", polygon=[(0, 0), (320, 0), (320, 240), (0, 240)]),
                Zone(name="atrium", polygon=[(320, 0), (640, 0), (640, 480), (320, 480)]),
            ],
            status="online",
        ),
        CameraConfig(
            id="cam_02",
            name="Food Court",
            location="Level 2",
            source_url="mock://cam_02",
            source_type=CameraSource.MOCK.value,
            zones=[Zone(name="tables", polygon=[(0, 0), (640, 480)])],
            status="online",
        ),
        CameraConfig(
            id="cam_03",
            name="Gate 3",
            location="North Wing",
            source_url="mock://cam_03",
            source_type=CameraSource.MOCK.value,
            zones=[Zone(name="gate_3", polygon=[(0, 0), (640, 480)])],
            status="online",
        ),
        CameraConfig(
            id="cam_04",
            name="Exit Corridor",
            location="West Exit",
            source_url="mock://cam_04",
            source_type=CameraSource.MOCK.value,
            zones=[Zone(name="exit_corridor", polygon=[(0, 0), (640, 480)])],
            status="online",
        ),
    ]
