import type { JourneySighting } from '../types'

interface PersonTimelineProps {
  journey: JourneySighting[]
}

export function PersonTimeline({ journey }: PersonTimelineProps) {
  if (!journey.length) return <div className="empty-block">No cross-camera sightings yet</div>

  return (
    <div className="timeline">
      {journey.map((item, index) => (
        <div key={`${item.camera_id}-${item.timestamp}-${index}`} className="timeline-node">
          <div className={`timeline-dot ${item.active ? 'active' : ''}`} />
          <div className="timeline-content">
            <strong>
              {item.camera_name} - {new Date(item.timestamp).toLocaleTimeString()}
            </strong>
            <span>{item.zone}</span>
            <span>{Math.round(item.dwell_time_seconds)}s dwell</span>
          </div>
        </div>
      ))}
    </div>
  )
}
