from __future__ import annotations

from storage.models import BehaviourResult, Frame, ObjectDetection, PoseResult, TrackedPerson


class BehaviourAnalyser:
    def analyse(self, track: TrackedPerson, pose: PoseResult, person_payload: dict) -> BehaviourResult:
        activity = self._classify_activity(track, pose, person_payload)
        return BehaviourResult(
            activity=activity,
            loiter_duration=track.dwell_time if track.dwell_time > 60 else 0.0,
            zone=track.zone,
            velocity_mps=round(track.velocity_magnitude() / 12.0, 2),
        )

    def detect_abandoned_objects(
        self,
        objects: list[ObjectDetection],
        tracks: list[TrackedPerson],
        frame: Frame,
    ) -> list[dict]:
        abandoned = []
        if not objects:
            return abandoned
        for item in objects:
            if not tracks:
                abandoned.append(
                    {
                        "bbox": item.bbox,
                        "object_type": item.object_type,
                        "duration_seconds": 61,
                    }
                )
        return abandoned

    def _classify_activity(self, track: TrackedPerson, pose: PoseResult, person_payload: dict) -> str:
        speed = track.velocity_magnitude()
        hint = person_payload.get("activity_hint")
        if hint == "running" or speed > 8.0 or pose.running:
            return "running"
        if track.dwell_time > 300 and speed < 1.0:
            return "loitering"
        if pose.falling:
            return "falling"
        if pose.aggressive_stance and speed > 3.0:
            return "fighting"
        return hint or "walking_normal"
