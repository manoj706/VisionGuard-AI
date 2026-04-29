from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime
from uuid import uuid4

from config import get_runtime_settings
from storage.models import (
    AppearanceResult,
    AuditTrail,
    BehaviourResult,
    IncidentReport,
    PersonIntelligence,
    PoseResult,
    ThreatLevel,
    TrackedPerson,
)


class SceneFusion:
    THREAT_WEIGHTS = {
        "clip_threat_score": 0.40,
        "pose_aggression": 0.30,
        "behaviour_risk": 0.30,
    }
    ALERT_THRESHOLD = 70
    CONFIRMATION_FRAMES = 3

    def __init__(self) -> None:
        self.settings = get_runtime_settings()
        self._buffers: dict[str, deque[float]] = defaultdict(
            lambda: deque(maxlen=self.CONFIRMATION_FRAMES)
        )

    def process_person(
        self,
        track: TrackedPerson,
        global_person_id: str,
        appearance: AppearanceResult,
        pose: PoseResult,
        behaviour: BehaviourResult,
        clip_score: float,
        embedding_bytes: bytes,
        camera_name: str,
        degraded_mode: bool,
    ) -> PersonIntelligence:
        threat_score = self._compute_threat_score(clip_score, pose, behaviour)
        description = self._generate_description(appearance, behaviour)
        audit = AuditTrail(
            model_version="mock-v1",
            hardware_profile=self.settings.hardware_profile,
            clip_threat_score=clip_score * 100,
            pose_aggression_score=(1.0 if pose.aggressive_stance else 0.15) * 100,
            behaviour_risk_score=self._behaviour_risk(behaviour) * 100,
            degraded_mode=degraded_mode,
        )
        return PersonIntelligence(
            track_id=track.track_id,
            global_person_id=global_person_id,
            camera_id=track.camera_id,
            camera_name=camera_name,
            timestamp=track.last_seen,
            bbox=track.bbox,
            thumbnail_url=f"/api/media/thumbnails/{global_person_id}.jpg",
            upper_colour=appearance.upper_colour,
            upper_type=appearance.upper_type,
            lower_colour=appearance.lower_colour,
            lower_type=appearance.lower_type,
            has_bag=appearance.has_bag,
            bag_type=appearance.bag_type,
            has_hat=appearance.has_hat,
            estimated_height=appearance.estimated_height if self.settings.privacy_mode != "strict" else "suppressed",
            build=appearance.build if self.settings.privacy_mode != "strict" else "suppressed",
            description=description,
            activity=behaviour.activity,
            zone=behaviour.zone,
            dwell_time_seconds=track.dwell_time,
            threat_score=threat_score,
            threat_level=self._get_level(threat_score),
            clip_embedding=embedding_bytes,
            appearance=appearance,
            pose=pose,
            behaviour=behaviour,
            audit=audit,
        )

    def maybe_create_incident(self, person: PersonIntelligence) -> IncidentReport | None:
        buffer = self._buffers[person.global_person_id]
        buffer.append(person.threat_score)
        if (
            len(buffer) == self.CONFIRMATION_FRAMES
            and all(score >= self.ALERT_THRESHOLD for score in buffer)
        ):
            return IncidentReport(
                id=f"inc_{uuid4().hex[:8]}",
                camera_id=person.camera_id,
                person_global_id=person.global_person_id,
                timestamp=person.timestamp,
                threat_level=person.threat_level,
                threat_score=person.threat_score,
                description=person.description,
                clip_url=f"/api/media/clips/{person.global_person_id}.mp4",
                thumbnail_url=person.thumbnail_url,
                activity=person.activity,
                zone=person.zone,
                audit=person.audit,
            )
        return None

    def _compute_threat_score(
        self,
        clip_score: float,
        pose: PoseResult,
        behaviour: BehaviourResult,
    ) -> float:
        total = (
            clip_score * self.THREAT_WEIGHTS["clip_threat_score"]
            + (1.0 if pose.aggressive_stance else 0.15) * self.THREAT_WEIGHTS["pose_aggression"]
            + self._behaviour_risk(behaviour) * self.THREAT_WEIGHTS["behaviour_risk"]
        )
        return round(total * 100, 2)

    def _behaviour_risk(self, behaviour: BehaviourResult) -> float:
        mapping = {
            "walking_normal": 0.15,
            "loitering": 0.62,
            "running": 0.8,
            "fighting": 0.95,
            "falling": 0.5,
        }
        return mapping.get(behaviour.activity, 0.2)

    def _get_level(self, threat_score: float) -> ThreatLevel:
        if threat_score >= 85:
            return ThreatLevel.CRITICAL
        if threat_score >= 70:
            return ThreatLevel.HIGH
        if threat_score >= 50:
            return ThreatLevel.MEDIUM
        if threat_score >= 30:
            return ThreatLevel.LOW
        return ThreatLevel.SAFE

    def _generate_description(self, appearance: AppearanceResult, behaviour: BehaviourResult) -> str:
        bag_phrase = f", carrying {appearance.bag_type}" if appearance.has_bag else ""
        return (
            f"Person in {appearance.upper_colour} {appearance.upper_type} and "
            f"{appearance.lower_colour} {appearance.lower_type}{bag_phrase}, "
            f"{behaviour.activity.replace('_', ' ')} in {behaviour.zone}"
        )
