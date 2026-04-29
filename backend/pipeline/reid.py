from __future__ import annotations

from collections import defaultdict
import hashlib

import numpy as np

from storage.models import AppearanceResult, Sighting, TrackedPerson


class ReIDEngine:
    def __init__(self) -> None:
        self.gallery: dict[str, dict] = {}
        self.track_to_global: dict[tuple[str, int], str] = {}
        self.timeline: defaultdict[str, list[Sighting]] = defaultdict(list)

    def identify(self, track: TrackedPerson, appearance: AppearanceResult) -> str:
        track_key = (track.camera_id, track.track_id)
        if track_key in self.track_to_global:
            return self.track_to_global[track_key]

        embedding = self._extract_embedding(appearance)
        for global_id, record in self.gallery.items():
            score = self._similarity(embedding, record["embedding"])
            if score > 0.92:
                self.track_to_global[track_key] = global_id
                self.gallery[global_id]["embedding"] = embedding
                return global_id

        global_id = f"gp_{track.track_id:04d}_{len(self.gallery)+1:03d}"
        self.gallery[global_id] = {"embedding": embedding}
        self.track_to_global[track_key] = global_id
        return global_id

    def update_journey(self, global_person_id: str, sighting: Sighting) -> None:
        history = self.timeline[global_person_id]
        if history and history[-1].camera_id == sighting.camera_id:
            history[-1] = sighting
        else:
            history.append(sighting)

    def get_journey(self, global_person_id: str) -> list[Sighting]:
        return self.timeline.get(global_person_id, [])

    def _extract_embedding(self, appearance: AppearanceResult) -> np.ndarray:
        text = "|".join(
            [
                appearance.upper_colour,
                appearance.upper_type,
                appearance.lower_colour,
                appearance.lower_type,
                appearance.bag_type,
                appearance.build,
            ]
        )
        digest = hashlib.sha256(text.encode()).digest()
        vector = np.frombuffer(digest * 8, dtype=np.uint8)[:128].astype(np.float32)
        norm = np.linalg.norm(vector) or 1.0
        return vector / norm

    def _similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
        return float(np.dot(a, b) / denom)
