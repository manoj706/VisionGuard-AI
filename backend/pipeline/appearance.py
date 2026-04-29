from __future__ import annotations

import numpy as np

from storage.models import AppearanceResult


class AppearanceAnalyser:
    def analyse(self, person_payload: dict) -> AppearanceResult:
        upper_colour = self._dominant_colour(person_payload.get("upper_crop")) or person_payload.get(
            "upper_colour", "unknown"
        )
        upper_type = person_payload.get("upper_type", "unknown")
        lower_colour = self._dominant_colour(person_payload.get("lower_crop")) or person_payload.get(
            "lower_colour", "unknown"
        )
        lower_type = person_payload.get("lower_type", "unknown")
        bag_type = person_payload.get("bag_type", "none")

        colour_description = (
            f"person wearing {upper_colour} {upper_type}, "
            f"{lower_colour} {lower_type}, {bag_type if bag_type != 'none' else 'no bag'}"
        )
        return AppearanceResult(
            upper_colour=upper_colour,
            upper_type=upper_type,
            lower_colour=lower_colour,
            lower_type=lower_type,
            has_bag=person_payload.get("has_bag", False),
            bag_type=bag_type,
            has_hat=person_payload.get("has_hat", False),
            hat_type=person_payload.get("hat_type", "none"),
            estimated_height=person_payload.get("estimated_height", "medium"),
            build=person_payload.get("build", "medium"),
            colour_description=colour_description,
        )

    def _dominant_colour(self, crop: np.ndarray | None) -> str | None:
        if crop is None or crop.size == 0:
            return None
        avg = crop.reshape(-1, 3).mean(axis=0)
        palette = {
            "black": np.array([25, 25, 25]),
            "white": np.array([225, 225, 225]),
            "red": np.array([220, 60, 60]),
            "blue": np.array([60, 90, 220]),
            "green": np.array([80, 180, 90]),
            "yellow": np.array([210, 210, 60]),
            "grey": np.array([128, 128, 128]),
            "brown": np.array([120, 80, 50]),
        }
        return min(palette.items(), key=lambda item: np.linalg.norm(avg - item[1]))[0]
