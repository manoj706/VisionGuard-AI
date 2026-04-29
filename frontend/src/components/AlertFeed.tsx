import type { Alert } from '../types'

const severityClass: Record<string, string> = {
  safe: 'badge-safe',
  low: 'badge-low',
  medium: 'badge-medium',
  high: 'badge-high',
  critical: 'badge-critical',
}

interface AlertFeedProps {
  alerts: Alert[]
  onAcknowledge: (id: string) => void
}

export function AlertFeed({ alerts, onAcknowledge }: AlertFeedProps) {
  return (
    <div className="panel-card">
      <div className="section-title">Live Alerts</div>
      <div className="alert-list">
        {alerts.length === 0 ? <div className="empty-block">No live alerts</div> : null}
        {alerts.map((alert) => (
          <div
            key={alert.incidentId}
            className={`alert-card ${alert.threatLevel === 'critical' ? 'critical-pulse' : ''}`}
          >
            <div className="alert-header">
              <span className={`badge ${severityClass[alert.threatLevel]}`}>{alert.threatLevel}</span>
              <span>{alert.cameraName}</span>
            </div>
            <div className="alert-description">{alert.description}</div>
            <div className="score-strip">
              {Array.from({ length: 10 }, (_, index) => (
                <span
                  key={index}
                  className={index < Math.round(alert.threatScore / 10) ? 'filled' : ''}
                />
              ))}
            </div>
            <div className="alert-footer">
              <span>{new Date(alert.timestamp).toLocaleTimeString()}</span>
              <button className="ghost-button" onClick={() => onAcknowledge(alert.incidentId)}>
                Acknowledge
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
