from __future__ import annotations

from config import ENABLE_REAL_MODELS, MOCK_MODE, get_runtime_settings
from storage.models import DetectionResult, Frame, ObjectDetection, PersonDetection


class SceneDetector:
    PERSON_CLASS = 0
    OBJECT_CLASSES = {
        24: "backpack",
        26: "handbag",
        28: "suitcase",
        67: "phone",
        73: "laptop",
    }

    def __init__(self) -> None:
        self.settings = get_runtime_settings()
        self.model = None
        if not MOCK_MODE and ENABLE_REAL_MODELS:
            try:
                from ultralytics import YOLO  # type: ignore

                self.model = YOLO(self.settings.detector)
            except Exception:
                self.model = None

    def detect(self, frame: Frame) -> DetectionResult:
        if self.model is not None and frame.raw is not None:
            try:
                result = self.model.predict(frame.raw["image"], verbose=False)[0]
                persons = []
                objects = []
                for box, cls_id, conf in zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf):
                    bbox = tuple(int(value) for value in box.tolist())
                    cls_int = int(cls_id.item())
                    confidence = float(conf.item())
                    if cls_int == self.PERSON_CLASS and confidence >= 0.45:
                        persons.append(
                            PersonDetection(
                                detection_id=f"det_{len(persons)}",
                                bbox=bbox,
                                confidence=confidence,
                            )
                        )
                    if cls_int in self.OBJECT_CLASSES and confidence >= 0.5:
                        objects.append(
                            ObjectDetection(
                                bbox=bbox,
                                object_type=self.OBJECT_CLASSES[cls_int],
                                confidence=confidence,
                            )
                        )
                return DetectionResult(persons=persons, objects=objects, raw_result=frame.raw)
            except Exception:
                pass

        raw = frame.raw or {}
        persons = [
            PersonDetection(
                detection_id=person["actor_id"],
                bbox=tuple(person["bbox"]),
                confidence=max(0.45, float(person["confidence"])),
            )
            for person in raw.get("persons", [])
        ]
        objects = [
            ObjectDetection(
                bbox=tuple(item["bbox"]),
                object_type=item["object_type"],
                confidence=max(0.5, float(item["confidence"])),
            )
            for item in raw.get("objects", [])
        ]
        return DetectionResult(persons=persons, objects=objects, raw_result=raw)
