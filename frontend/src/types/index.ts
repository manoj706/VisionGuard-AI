export type ThreatLevel = 'safe' | 'low' | 'medium' | 'high' | 'critical'

export interface TrackedPerson {
  trackId: number
  globalPersonId: string
  cameraId: string
  bbox: [number, number, number, number]
  threatLevel: ThreatLevel
  threatScore: number
  description: string
  activity: string
  upperColour: string
  upperType: string
  lowerColour: string
  lowerType: string
  hasBag: boolean
  bagType: string
  dwellTime: number
  zone: string
  thumbnailUrl?: string
}

export interface SceneUpdate {
  type: 'scene_update'
  cameraId: string
  timestamp: string
  persons: TrackedPerson[]
  crowdCount: number
  densityGrid: number[][]
}

export interface Alert {
  type: 'alert'
  incidentId: string
  cameraId: string
  cameraName: string
  globalPersonId: string
  threatLevel: ThreatLevel
  threatScore: number
  description: string
  thumbnailUrl: string
  clipUrl: string
  timestamp: string
}

export interface Camera {
  id: string
  name: string
  location: string
  status: 'online' | 'offline' | 'degraded'
  fpsCurrent: number
  personsTracked: number
  currentPersons: TrackedPerson[]
}

export interface Incident {
  id: string
  camera_id: string
  person_global_id: string
  timestamp: string
  threat_level: ThreatLevel
  threat_score: number
  description: string
  clip_url: string
  thumbnail_url: string
  acknowledged: boolean
  acknowledged_by?: string | null
  activity: string
  zone: string
}

export interface SearchResult {
  event: {
    global_person_id: string
    camera_name: string
    timestamp: string
    description: string
    activity: string
    zone: string
    threat_level: ThreatLevel
    threat_score: number
    thumbnail_url: string
  }
  score: number
}

export interface JourneySighting {
  camera_id: string
  camera_name: string
  location: string
  timestamp: string
  zone: string
  thumbnail_url: string
  dwell_time_seconds: number
  active: boolean
}

export interface PersonProfileResponse {
  person: {
    global_person_id: string
    track_id: number
    camera_id: string
    camera_name: string
    thumbnail_url: string
    description: string
    threat_level: ThreatLevel
    threat_score: number
    upper_colour: string
    upper_type: string
    lower_colour: string
    lower_type: string
    has_bag: boolean
    bag_type: string
    has_hat: boolean
    estimated_height: string
    build: string
    activity: string
    zone: string
    dwell_time_seconds: number
    audit?: {
      clip_threat_score: number
      pose_aggression_score: number
      behaviour_risk_score: number
    }
  }
  journey: JourneySighting[]
}

export interface SystemHealth {
  cpu_percent: number
  gpu_percent: number
  ram_percent: number
  degraded_mode: boolean
  privacy_mode: 'standard' | 'strict'
  retention_days: number
  hardware_profile: string
  model_versions: Record<string, string>
  cameras: Array<{ id: string; fps: number; persons_tracked: number; status: string }>
}
