interface CrowdHeatmapProps {
  densityMap?: number[][]
}

export function CrowdHeatmap({ densityMap }: CrowdHeatmapProps) {
  const grid = densityMap ?? Array.from({ length: 8 }, () => Array.from({ length: 8 }, () => 0))

  return (
    <div className="panel-card">
      <div className="section-title">Crowd Heatmap</div>
      <div className="heatmap-grid">
        {grid.flatMap((row, rowIndex) =>
          row.map((value, colIndex) => (
            <div
              key={`${rowIndex}-${colIndex}`}
              className="heatmap-cell"
              style={{
                opacity: Math.min(1, value / 8 + 0.1),
                background:
                  value >= 9
                    ? 'rgba(239,68,68,0.85)'
                    : value >= 4
                      ? 'rgba(245,158,11,0.55)'
                      : 'rgba(245,158,11,0.2)',
              }}
            >
              {value}
            </div>
          )),
        )}
      </div>
    </div>
  )
}
