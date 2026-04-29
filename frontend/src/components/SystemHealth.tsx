import type { Camera, SystemHealth } from '../types'

interface SystemHealthProps {
  health: SystemHealth | null
  cameras: Camera[]
}

export function SystemHealthPanel({ health, cameras }: SystemHealthProps) {
  return (
    <div className="panel-card">
      <div className="section-title">System Health</div>
      <div className="health-grid">
        <div className="health-metric">
          <span>CPU</span>
          <strong>{health ? `${health.cpu_percent.toFixed(0)}%` : '--'}</strong>
        </div>
        <div className="health-metric">
          <span>RAM</span>
          <strong>{health ? `${health.ram_percent.toFixed(0)}%` : '--'}</strong>
        </div>
        <div className="health-metric">
          <span>Profile</span>
          <strong>{health?.hardware_profile ?? 'mid_range'}</strong>
        </div>
        <div className="health-metric">
          <span>Retention</span>
          <strong>{health?.retention_days ?? 30}d</strong>
        </div>
      </div>
      <div className="sidebar-list compact">
        {cameras.map((camera) => (
          <div key={camera.id} className="camera-row">
            <span>{camera.name}</span>
            <span>{camera.personsTracked} tracked</span>
          </div>
        ))}
      </div>
    </div>
  )
}
