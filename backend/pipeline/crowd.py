from __future__ import annotations

from storage.models import CrowdGroup, CrowdResult, Frame, TrackedPerson


class CrowdAnalyser:
    def analyse(self, tracks: list[TrackedPerson], frame: Frame) -> CrowdResult:
        density_map = self._compute_density_grid(tracks, frame)
        flow_vectors = self._compute_flow(tracks)
        high_density = self._flag_dense_zones(density_map)
        groups = self._detect_groups(tracks)
        return CrowdResult(
            total_count=len(tracks),
            density_map=density_map,
            flow_vectors=flow_vectors,
            high_density_zones=high_density,
            group_detections=groups,
            congestion_score=self._congestion(density_map),
        )

    def _compute_density_grid(self, tracks: list[TrackedPerson], frame: Frame) -> list[list[int]]:
        rows, cols = 8, 8
        grid = [[0 for _ in range(cols)] for _ in range(rows)]
        for track in tracks:
            x_mid = (track.bbox[0] + track.bbox[2]) / 2
            y_mid = (track.bbox[1] + track.bbox[3]) / 2
            col = min(cols - 1, int((x_mid / max(frame.width, 1)) * cols))
            row = min(rows - 1, int((y_mid / max(frame.height, 1)) * rows))
            grid[row][col] += 1
        return grid

    def _compute_flow(self, tracks: list[TrackedPerson]) -> list[list[tuple[float, float]]]:
        rows, cols = 8, 8
        return [[(0.0, 0.0) for _ in range(cols)] for _ in range(rows)]

    def _flag_dense_zones(self, density_map: list[list[int]]) -> list[str]:
        zones = []
        for row_idx, row in enumerate(density_map):
            for col_idx, value in enumerate(row):
                if value >= 4:
                    zones.append(f"grid_{row_idx}_{col_idx}")
        return zones

    def _detect_groups(self, tracks: list[TrackedPerson]) -> list[CrowdGroup]:
        if len(tracks) < 3:
            return []
        return [
            CrowdGroup(
                group_id="grp_001",
                member_track_ids=[track.track_id for track in tracks[: min(4, len(tracks))]],
                zone=tracks[0].zone,
            )
        ]

    def _congestion(self, density_map: list[list[int]]) -> float:
        flattened = [cell for row in density_map for cell in row]
        return min(100.0, sum(flattened) * 2.5)
