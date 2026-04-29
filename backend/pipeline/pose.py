from __future__ import annotations

from config import ENABLE_REAL_MODELS, get_runtime_settings
from storage.models import PoseResult


class PoseAnalyser:
    def __init__(self) -> None:
        self.settings = get_runtime_settings()
        self._mp_pose = None
        if self.settings.pose_enabled and ENABLE_REAL_MODELS:
            try:
                import mediapipe as mp  # type: ignore

                self._mp_pose = mp.solutions.pose.Pose(
                    static_image_mode=False,
                    model_complexity=0,
                    enable_segmentation=False,
                )
            except Exception:
                self._mp_pose = None

    def analyse(self, person_payload: dict) -> PoseResult:
        if not self.settings.pose_enabled:
            return PoseResult.neutral()

        if self._mp_pose is not None and "crop_image" in person_payload:
            try:
                result = self._mp_pose.process(person_payload["crop_image"])
                if result.pose_landmarks:
                    landmarks = result.pose_landmarks.landmark
                    arms_raised = landmarks[15].y < landmarks[11].y and landmarks[16].y < landmarks[12].y
                    return PoseResult(
                        keypoints=[(lm.x, lm.y, lm.visibility) for lm in landmarks],
                        arms_raised=arms_raised,
                        aggressive_stance=arms_raised,
                        running=person_payload.get("activity_hint") == "running",
                        falling=False,
                        fighting=person_payload.get("activity_hint") == "fighting",
                    )
            except Exception:
                pass

        activity = person_payload.get("activity_hint", "walking_normal")
        threat_wave = float(person_payload.get("threat_wave", 0.0))
        return PoseResult(
            keypoints=[],
            arms_raised=threat_wave > 0.85,
            aggressive_stance=activity in {"running", "fighting"} and threat_wave > 0.75,
            running=activity == "running",
            falling=activity == "falling",
            fighting=person_payload.get("alert_kind") == "person_of_interest" and threat_wave > 0.88,
        )
