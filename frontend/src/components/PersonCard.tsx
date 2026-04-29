import { PersonTimeline } from './PersonTimeline'
import type { PersonProfileResponse } from '../types'

interface PersonCardProps {
  profile: PersonProfileResponse | null
}

export function PersonCard({ profile }: PersonCardProps) {
  if (!profile) {
    return (
      <div className="panel-card">
        <div className="section-title">Person Intelligence</div>
        <div className="empty-block">Select a person from the live grid to inspect their profile.</div>
      </div>
    )
  }

  const { person } = profile

  return (
    <div className="panel-card">
      <div className="section-title">Person Intelligence</div>
      <div className="person-card-header">
        <img src={person.thumbnail_url} alt={person.description} />
        <div>
          <div className="person-id">{person.global_person_id.toUpperCase()}</div>
          <div className={`badge badge-${person.threat_level}`}>{person.threat_level}</div>
          <div className="person-score">{person.threat_score.toFixed(0)}</div>
        </div>
      </div>
      <p className="person-description">{person.description}</p>
      <div className="detail-grid">
        <div>Upper</div>
        <div>
          {person.upper_colour} {person.upper_type}
        </div>
        <div>Lower</div>
        <div>
          {person.lower_colour} {person.lower_type}
        </div>
        <div>Bag</div>
        <div>{person.has_bag ? person.bag_type : 'none'}</div>
        <div>Zone</div>
        <div>
          {person.zone} - {Math.round(person.dwell_time_seconds)}s
        </div>
      </div>
      <div className="breakdown">
        <div>
          <span>CLIP similarity</span>
          <progress max={100} value={person.audit?.clip_threat_score ?? 0} />
        </div>
        <div>
          <span>Pose aggression</span>
          <progress max={100} value={person.audit?.pose_aggression_score ?? 0} />
        </div>
        <div>
          <span>Behaviour risk</span>
          <progress max={100} value={person.audit?.behaviour_risk_score ?? 0} />
        </div>
      </div>
      <div className="section-title small">Cross-Camera Journey</div>
      <PersonTimeline journey={profile.journey} />
      <div className="action-row">
        <button className="ghost-button">Track this person</button>
        <button className="ghost-button">Create incident report</button>
        <button className="ghost-button">View full footage</button>
      </div>
    </div>
  )
}
