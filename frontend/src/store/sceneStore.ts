import { create } from 'zustand'

import type {
  Alert,
  Camera,
  Incident,
  PersonProfileResponse,
  SearchResult,
  SceneUpdate,
  SystemHealth,
} from '../types'

interface SceneStore {
  cameras: Camera[]
  activeAlerts: Alert[]
  allIncidents: Incident[]
  searchResults: SearchResult[]
  selectedPersonId: string | null
  selectedCameraId: string | null
  selectedPersonProfile: PersonProfileResponse | null
  systemHealth: SystemHealth | null
  wsConnected: boolean
  latestHeatmap: { camera_id?: string; density_map?: number[][]; flow_vectors?: unknown[] } | null
  handleSceneUpdate: (update: SceneUpdate) => void
  handleAlert: (alert: Alert) => void
  acknowledgeAlert: (id: string) => void
  selectPerson: (globalPersonId: string | null) => void
  selectCamera: (cameraId: string | null) => void
  setSearchResults: (results: SearchResult[]) => void
  updateHealth: (health: SystemHealth) => void
  setCameras: (cameras: Camera[]) => void
  setWsConnected: (connected: boolean) => void
  setPersonProfile: (profile: PersonProfileResponse | null) => void
  setIncidents: (incidents: Incident[]) => void
  setHeatmap: (heatmap: SceneStore['latestHeatmap']) => void
}

export const useSceneStore = create<SceneStore>((set) => ({
  cameras: [],
  activeAlerts: [],
  allIncidents: [],
  searchResults: [],
  selectedPersonId: null,
  selectedCameraId: null,
  selectedPersonProfile: null,
  systemHealth: null,
  wsConnected: false,
  latestHeatmap: null,
  handleSceneUpdate: (update) =>
    set((state) => {
      const next = [...state.cameras]
      const index = next.findIndex((camera) => camera.id === update.cameraId)
      const current = next[index]
      const merged: Camera = {
        id: update.cameraId,
        name: current?.name ?? update.cameraId,
        location: current?.location ?? 'Unknown',
        status: current?.status ?? 'online',
        fpsCurrent: current?.fpsCurrent ?? 0,
        personsTracked: update.persons.length,
        currentPersons: update.persons,
      }
      if (index >= 0) next[index] = { ...current, ...merged }
      else next.push(merged)
      return { cameras: next }
    }),
  handleAlert: (alert) =>
    set((state) => ({
      activeAlerts: [alert, ...state.activeAlerts.filter((item) => item.incidentId !== alert.incidentId)].slice(0, 8),
    })),
  acknowledgeAlert: (id) =>
    set((state) => ({
      activeAlerts: state.activeAlerts.filter((item) => item.incidentId !== id),
    })),
  selectPerson: (selectedPersonId) => set({ selectedPersonId }),
  selectCamera: (selectedCameraId) => set({ selectedCameraId }),
  setSearchResults: (searchResults) => set({ searchResults }),
  updateHealth: (systemHealth) => set({ systemHealth }),
  setCameras: (cameras) => set({ cameras }),
  setWsConnected: (wsConnected) => set({ wsConnected }),
  setPersonProfile: (selectedPersonProfile) => set({ selectedPersonProfile }),
  setIncidents: (allIncidents) => set({ allIncidents }),
  setHeatmap: (latestHeatmap) => set({ latestHeatmap }),
}))
