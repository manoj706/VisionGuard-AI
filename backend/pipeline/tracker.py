from __future__ import annotations

from datetime import datetime

from storage.models import Frame, PersonDetection, TrackedPerson


class PersonTracker:
    def __init__(self) -> None:
        self._tracks: dict[str, TrackedPerson] = {}
        self._id_map: dict[str, int] = {}
        self._next_track_id = 1

    def update(self, detections: list[PersonDetection], frame: Frame) -> list[TrackedPerson]:
        active_ids = set()
        tracked: list[TrackedPerson] = []
        raw_persons = {item["actor_id"]: item for item in (frame.raw or {}).get("persons", [])}

        for detection in detections:
            actor_id = detection.detection_id
            active_ids.add(actor_id)
            if actor_id not in self._id_map:
                self._id_map[actor_id] = self._next_track_id
                self._next_track_id += 1

            prev = self._tracks.get(actor_id)
            now = frame.timestamp
            bbox = tuple(detection.bbox)
            prev_bbox = prev.bbox if prev else bbox
            velocity = (
                float(bbox[0] - prev_bbox[0]),
                float(bbox[1] - prev_bbox[1]),
            )
            zone = self._detect_zone(frame, bbox)
            dwell = prev.dwell_time + max((now - prev.last_seen).total_seconds(), 0) if prev and prev.zone == zone else 0.0
            trail = (prev.trail if prev else [])[-2:] + [bbox]
            tracked_person = TrackedPerson(
                track_id=self._id_map[actor_id],
                camera_id=frame.camera_id,
                camera_name=frame.camera_name,
                bbox=bbox,
                age=(prev.age + 1) if prev else 1,
                velocity=velocity,
                zone=zone,
                dwell_time=dwell,
                first_seen=prev.first_seen if prev else now,
                last_seen=now,
                crop=raw_persons.get(actor_id, {}).get("actor_id", actor_id).encode(),
                trail=trail,
            )
            self._tracks[actor_id] = tracked_person
            tracked.append(tracked_person)

        self._tracks = {
            actor_id: track
            for actor_id, track in self._tracks.items()
            if actor_id in active_ids
        }
        return tracked

    def _detect_zone(self, frame: Frame, bbox: tuple[int, int, int, int]) -> str:
        x_mid = (bbox[0] + bbox[2]) / 2
        zones = getattr(frame.raw, "zones", None)
        if zones:
            return zones[0].name
        return "zone_a" if x_mid < frame.width / 2 else "zone_b"
