from __future__ import annotations

import hashlib

import numpy as np

from storage.models import SearchResult
from config import ENABLE_REAL_MODELS


class CLIPEngine:
    THREAT_PROMPTS = [
        "a person behaving aggressively",
        "a person running away from something",
        "a suspicious person loitering",
        "a person with an aggressive stance",
        "a person fighting",
        "a crowd surging or stampeding",
    ]

    SAFE_PROMPTS = [
        "a person walking normally",
        "a person standing calmly",
        "a person shopping",
        "a person talking on their phone",
    ]

    def __init__(self) -> None:
        self._clip = None
        self._device = "cpu"
        self._model = None
        self._preprocess = None
        if not ENABLE_REAL_MODELS:
            return
        try:
            import clip  # type: ignore
            import torch  # type: ignore

            self._clip = clip
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model, self._preprocess = clip.load("ViT-B/32", device=self._device)
        except Exception:
            self._model = None
            self._preprocess = None

    def embed_crop(self, person_payload: dict) -> np.ndarray:
        if self._model is not None and person_payload.get("pil_image") is not None:
            try:
                import torch  # type: ignore

                image = self._preprocess(person_payload["pil_image"]).unsqueeze(0).to(self._device)
                with torch.no_grad():
                    features = self._model.encode_image(image).cpu().numpy()[0].astype(np.float32)
                norm = np.linalg.norm(features) or 1.0
                return features / norm
            except Exception:
                pass
        text = "|".join(
            [
                person_payload.get("upper_colour", ""),
                person_payload.get("upper_type", ""),
                person_payload.get("lower_colour", ""),
                person_payload.get("lower_type", ""),
                person_payload.get("activity_hint", ""),
            ]
        )
        digest = hashlib.sha256(text.encode()).digest()
        vector = np.frombuffer(digest * 16, dtype=np.uint8)[:512].astype(np.float32)
        norm = np.linalg.norm(vector) or 1.0
        return vector / norm

    def threat_score(self, embedding: np.ndarray, person_payload: dict) -> float:
        if self._model is not None:
            try:
                import torch  # type: ignore

                prompts = self.THREAT_PROMPTS + self.SAFE_PROMPTS
                with torch.no_grad():
                    text = self._clip.tokenize(prompts).to(self._device)
                    text_features = self._model.encode_text(text).cpu().numpy().astype(np.float32)
                text_features = text_features / np.linalg.norm(text_features, axis=1, keepdims=True)
                sims = text_features @ embedding
                threat = float(np.mean(sims[: len(self.THREAT_PROMPTS)]))
                safe = float(np.mean(sims[len(self.THREAT_PROMPTS) :]))
                return float(min(1.0, max(0.0, (threat - safe + 1) / 2)))
            except Exception:
                pass
        wave = float(person_payload.get("threat_wave", 0.0))
        running_bonus = 0.18 if person_payload.get("activity_hint") == "running" else 0.0
        return float(min(1.0, max(0.0, wave * 0.82 + running_bonus)))

    def semantic_search(self, query: str, event_embeddings: list) -> list[SearchResult]:
        query_terms = query.lower().split()
        results = []
        for event in event_embeddings:
            text = f"{event.description} {event.activity} {event.zone}".lower()
            matches = sum(1 for term in query_terms if term in text)
            if matches:
                results.append(SearchResult(event=event, score=min(0.99, 0.4 + matches / max(len(query_terms), 1) * 0.5)))
        return sorted(results, key=lambda result: result.score, reverse=True)[:20]

    @staticmethod
    def serialize_embedding(embedding: np.ndarray) -> bytes:
        return embedding.astype(np.float32).tobytes()

    @staticmethod
    def similarity(a: np.ndarray, b: np.ndarray) -> float:
        denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
        return float(np.dot(a, b) / denom)
