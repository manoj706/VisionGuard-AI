from __future__ import annotations

import os
from dataclasses import dataclass

import psutil


HARDWARE_PROFILES = {
    "gpu_server": {
        "detector": "yolov8m",
        "appearance_model": "efficientnet_b2",
        "clip_model": "ViT-L/14",
        "pose_enabled": True,
        "reid_enabled": True,
        "crowd_enabled": True,
        "target_fps": 25,
    },
    "mid_range": {
        "detector": "yolov8s",
        "appearance_model": "efficientnet_b0",
        "clip_model": "ViT-B/32",
        "pose_enabled": True,
        "reid_enabled": True,
        "crowd_enabled": True,
        "target_fps": 15,
    },
    "embedded": {
        "detector": "yolov8n",
        "appearance_model": "mobilenet_v3",
        "clip_model": "ViT-B/32",
        "pose_enabled": False,
        "reid_enabled": True,
        "crowd_enabled": False,
        "target_fps": 8,
    },
}

RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "30"))
PRIVACY_MODE = os.getenv("PRIVACY_MODE", "standard")
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"
ENABLE_REAL_MODELS = os.getenv("ENABLE_REAL_MODELS", "false").lower() == "true"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./visionguard.db")
MEDIA_ROOT = os.getenv("MEDIA_ROOT", "./media")
API_PREFIX = "/api"


@dataclass(slots=True)
class RuntimeSettings:
    hardware_profile: str
    detector: str
    appearance_model: str
    clip_model: str
    pose_enabled: bool
    reid_enabled: bool
    crowd_enabled: bool
    target_fps: int
    retention_days: int
    privacy_mode: str
    mock_mode: bool


def detect_hardware_profile() -> str:
    if os.getenv("FORCE_HARDWARE_PROFILE") in HARDWARE_PROFILES:
        return os.environ["FORCE_HARDWARE_PROFILE"]

    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            return "gpu_server"
    except Exception:
        pass

    cpu_count = psutil.cpu_count(logical=True) or 4
    total_gb = psutil.virtual_memory().total / (1024**3)
    if cpu_count <= 4 or total_gb < 8:
        return "embedded"
    return "mid_range"


def get_runtime_settings() -> RuntimeSettings:
    profile_name = detect_hardware_profile()
    profile = HARDWARE_PROFILES[profile_name]
    return RuntimeSettings(
        hardware_profile=profile_name,
        detector=profile["detector"],
        appearance_model=profile["appearance_model"],
        clip_model=profile["clip_model"],
        pose_enabled=profile["pose_enabled"],
        reid_enabled=profile["reid_enabled"],
        crowd_enabled=profile["crowd_enabled"],
        target_fps=profile["target_fps"],
        retention_days=RETENTION_DAYS,
        privacy_mode=PRIVACY_MODE,
        mock_mode=MOCK_MODE,
    )
