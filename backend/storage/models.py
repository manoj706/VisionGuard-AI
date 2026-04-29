from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ThreatLevel(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Zone(BaseModel):
    name: str
    polygon: list[tuple[int, int]] = Field(default_factory=list)


class Frame(BaseModel):
    frame_id: str
    camera_id: str
    camera_name: str
    location: str
    timestamp: datetime
    raw: Any | None = None
    width: int
    height: int

    model_config = {"arbitrary_types_allowed": True}


class PersonDetection(BaseModel):
    detection_id: str
    bbox: tuple[int, int, int, int]
    confidence: float
    crop: bytes | None = None


class ObjectDetection(BaseModel):
    bbox: tuple[int, int, int, int]
    object_type: str
    confidence: float


class DetectionResult(BaseModel):
    persons: list[PersonDetection] = Field(default_factory=list)
    objects: list[ObjectDetection] = Field(default_factory=list)
    raw_result: dict[str, Any] = Field(default_factory=dict)


class AppearanceResult(BaseModel):
    upper_colour: str = "unknown"
    upper_type: str = "unknown"
    lower_colour: str = "unknown"
    lower_type: str = "unknown"
    has_bag: bool = False
    bag_type: str = "none"
    has_hat: bool = False
    hat_type: str = "none"
    estimated_height: str = "unknown"
    build: str = "unknown"
    colour_description: str = "person"


class PoseResult(BaseModel):
    keypoints: list[tuple[float, float, float]] = Field(default_factory=list)
    arms_raised: bool = False
    aggressive_stance: bool = False
    running: bool = False
    falling: bool = False
    fighting: bool = False

    @classmethod
    def neutral(cls) -> "PoseResult":
        return cls()


class BehaviourResult(BaseModel):
    activity: str = "walking_normal"
    loiter_duration: float = 0.0
    zone: str = "unknown"
    velocity_mps: float = 0.0


class CrowdGroup(BaseModel):
    group_id: str
    member_track_ids: list[int]
    zone: str


class CrowdResult(BaseModel):
    total_count: int = 0
    density_map: list[list[int]] = Field(default_factory=list)
    flow_vectors: list[list[tuple[float, float]]] = Field(default_factory=list)
    high_density_zones: list[str] = Field(default_factory=list)
    group_detections: list[CrowdGroup] = Field(default_factory=list)
    congestion_score: float = 0.0


class Sighting(BaseModel):
    camera_id: str
    camera_name: str
    location: str
    timestamp: datetime
    zone: str
    thumbnail_url: str = ""
    dwell_time_seconds: float = 0.0
    active: bool = False


class TrackedPerson(BaseModel):
    track_id: int
    camera_id: str
    camera_name: str
    bbox: tuple[int, int, int, int]
    age: int = 0
    velocity: tuple[float, float] = (0.0, 0.0)
    zone: str = "unknown"
    dwell_time: float = 0.0
    first_seen: datetime
    last_seen: datetime
    crop: bytes | None = None
    trail: list[tuple[int, int, int, int]] = Field(default_factory=list)

    def velocity_magnitude(self) -> float:
        vx, vy = self.velocity
        return (vx**2 + vy**2) ** 0.5


class AuditTrail(BaseModel):
    model_version: str = "mock-v1"
    hardware_profile: str = "mid_range"
    clip_threat_score: float = 0.0
    pose_aggression_score: float = 0.0
    behaviour_risk_score: float = 0.0
    degraded_mode: bool = False


class PersonIntelligence(BaseModel):
    track_id: int
    global_person_id: str
    camera_id: str
    camera_name: str
    timestamp: datetime
    bbox: tuple[int, int, int, int]
    thumbnail_url: str
    upper_colour: str
    upper_type: str
    lower_colour: str
    lower_type: str
    has_bag: bool
    bag_type: str
    has_hat: bool
    estimated_height: str
    build: str
    description: str
    activity: str
    zone: str
    dwell_time_seconds: float
    threat_score: float
    threat_level: ThreatLevel
    clip_embedding: bytes
    appearance: AppearanceResult | None = None
    pose: PoseResult | None = None
    behaviour: BehaviourResult | None = None
    audit: AuditTrail | None = None


class CameraConfig(BaseModel):
    id: str
    name: str
    location: str
    source_url: str
    source_type: str
    zones: list[Zone] = Field(default_factory=list)
    status: str = "online"
    fps_current: float = 0.0
    persons_tracked: int = 0


class IncidentReport(BaseModel):
    id: str
    camera_id: str
    person_global_id: str
    timestamp: datetime
    threat_level: ThreatLevel
    threat_score: float
    description: str
    clip_url: str
    thumbnail_url: str
    acknowledged: bool = False
    acknowledged_by: str | None = None
    activity: str = "walking_normal"
    zone: str = "unknown"
    audit: AuditTrail | None = None


class SearchResult(BaseModel):
    event: PersonIntelligence
    score: float


class SearchFilters(BaseModel):
    query: str
    camera_ids: list[str] = Field(default_factory=list)
    threat_levels: list[ThreatLevel] = Field(default_factory=list)
    activity: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


class SystemHealth(BaseModel):
    cpu_percent: float
    gpu_percent: float
    ram_percent: float
    degraded_mode: bool = False
    privacy_mode: str = "standard"
    retention_days: int = 30
    hardware_profile: str = "mid_range"
    model_versions: dict[str, str] = Field(default_factory=dict)
    cameras: list[dict[str, Any]] = Field(default_factory=list)


class AuthRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    token: str
    expires_in: int
