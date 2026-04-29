import type { Camera, TrackedPerson } from '../types'

const threatToColor: Record<string, string> = {
  safe: '#22c55e',
  low: '#84cc16',
  medium: '#f59e0b',
  high: '#ef4444',
  critical: '#ff0080',
}

interface LiveGridProps {
  cameras: Camera[]
  selectedCameraId: string | null
  onSelectCamera: (cameraId: string | null) => void
  onSelectPerson: (globalPersonId: string) => void
}

function PersonOverlay({
  person,
  onSelectPerson,
}: {
  person: TrackedPerson
  onSelectPerson: (globalPersonId: string) => void
}) {
  const [x1, y1, x2, y2] = person.bbox
  const width = x2 - x1
  const height = y2 - y1

  return (
    <button
      className="person-overlay"
      style={{
        left: `${(x1 / 640) * 100}%`,
        top: `${(y1 / 480) * 100}%`,
        width: `${(width / 640) * 100}%`,
        height: `${(height / 480) * 100}%`,
        borderColor: threatToColor[person.threatLevel],
      }}
      onClick={() => onSelectPerson(person.globalPersonId)}
    >
      <span className="person-label">
        {person.upperColour} {person.upperType} • {Math.round(person.threatScore)}
      </span>
    </button>
  )
}

export function LiveGrid({
  cameras,
  selectedCameraId,
  onSelectCamera,
  onSelectPerson,
}: LiveGridProps) {
  const visible = selectedCameraId
    ? cameras.filter((camera) => camera.id === selectedCameraId)
    : cameras

  return (
    <div className={`live-grid ${visible.length === 1 ? 'single' : ''}`}>
      {visible.map((camera) => {
        const highestThreat =
          [...camera.currentPersons].sort((a, b) => b.threatScore - a.threatScore)[0]?.threatLevel ??
          'safe'
        return (
          <div key={camera.id} className="camera-tile">
            <button className="camera-select" onClick={() => onSelectCamera(camera.id)}>
              <span>{camera.name}</span>
              <span>
                {camera.personsTracked} tracked • {camera.fpsCurrent.toFixed(0)} fps
              </span>
            </button>
            <div className="video-mock">
              <div className="scanlines" />
              {camera.currentPersons.map((person) => (
                <PersonOverlay
                  key={`${camera.id}-${person.globalPersonId}`}
                  person={person}
                  onSelectPerson={onSelectPerson}
                />
              ))}
              <div className={`tile-threat badge badge-${highestThreat}`}>{highestThreat}</div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
