import { useEffect, useMemo, useState } from 'react'

import { AlertFeed } from './components/AlertFeed'
import { CrowdHeatmap } from './components/CrowdHeatmap'
import { LiveGrid } from './components/LiveGrid'
import { PersonCard } from './components/PersonCard'
import { PrivacyBanner } from './components/PrivacyBanner'
import { SemanticSearch } from './components/SemanticSearch'
import { SystemHealthPanel } from './components/SystemHealth'
import { useAuth } from './hooks/useAuth'
import { useWebSocket } from './hooks/useWebSocket'
import { useSceneStore } from './store/sceneStore'
import { LoginPage } from './pages/LoginPage'
import type { Camera, Incident, PersonProfileResponse } from './types'

function Dashboard({ token, logout }: { token: string; logout: () => void }) {
  const {
    cameras,
    activeAlerts,
    searchResults,
    selectedCameraId,
    selectedPersonId,
    selectedPersonProfile,
    systemHealth,
    wsConnected,
    latestHeatmap,
    setCameras,
    setSearchResults,
    selectPerson,
    selectCamera,
    acknowledgeAlert,
    setPersonProfile,
    setIncidents,
    setHeatmap,
  } = useSceneStore()
  const [tab, setTab] = useState<'live' | 'search' | 'heatmap'>('live')

  useWebSocket(token)

  useEffect(() => {
    async function bootstrap() {
      const headers = { Authorization: `Bearer ${token}` }
      const [cameraResponse, incidentResponse, healthResponse, heatmapResponse] = await Promise.all([
        fetch('/api/cameras', { headers }),
        fetch('/api/incidents', { headers }),
        fetch('/api/health', { headers }),
        fetch('/api/crowd/heatmap', { headers }),
      ])
      const cameraData = (await cameraResponse.json()) as Array<
        Camera & { persons_tracked?: number; fps_current?: number }
      >
      setCameras(
        cameraData.map((camera) => ({
          id: camera.id,
          name: camera.name,
          location: camera.location,
          status: camera.status,
          fpsCurrent: camera.fps_current ?? camera.fpsCurrent ?? 15,
          personsTracked: camera.persons_tracked ?? camera.personsTracked ?? 0,
          currentPersons: [],
        })),
      )
      setIncidents((await incidentResponse.json()) as Incident[])
      useSceneStore.getState().updateHealth(await healthResponse.json())
      setHeatmap(await heatmapResponse.json())
    }

    bootstrap()
  }, [setCameras, setHeatmap, setIncidents, token])

  useEffect(() => {
    if (!selectedPersonId) return
    async function loadProfile() {
      const response = await fetch(`/api/persons/${selectedPersonId}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = (await response.json()) as PersonProfileResponse
      setPersonProfile(data)
    }
    loadProfile()
  }, [selectedPersonId, setPersonProfile, token])

  const totalTracked = useMemo(
    () => cameras.reduce((sum, camera) => sum + camera.currentPersons.length, 0),
    [cameras],
  )

  return (
    <div className="app-shell">
      <PrivacyBanner
        privacyMode={systemHealth?.privacy_mode}
        retentionDays={systemHealth?.retention_days}
      />
      <header className="topbar">
        <div>
          <h1 className="brand">
            VisionGuard<span>AI</span>
          </h1>
          <div className="topbar-meta">
            {cameras.length} cameras online • {totalTracked} persons tracked • {activeAlerts.length} alerts
          </div>
        </div>
        <div className="topbar-right">
          <span className={`ws-dot ${wsConnected ? 'live' : 'down'}`} />
          <span className="clock">{new Date().toLocaleTimeString()}</span>
          <button className="ghost-button" onClick={logout}>
            Logout
          </button>
        </div>
      </header>

      <div className="layout">
        <aside className="sidebar left">
          <div className="panel-card">
            <div className="section-title">Cameras</div>
            <button className="camera-row selectable" onClick={() => selectCamera(null)}>
              <span>All Cameras</span>
              <span>Grid</span>
            </button>
            <div className="sidebar-list">
              {cameras.map((camera) => (
                <button
                  key={camera.id}
                  className={`camera-row selectable ${selectedCameraId === camera.id ? 'active' : ''}`}
                  onClick={() => selectCamera(camera.id)}
                >
                  <span>{camera.name}</span>
                  <span>{camera.currentPersons.length}</span>
                </button>
              ))}
            </div>
          </div>
          <SystemHealthPanel health={systemHealth} cameras={cameras} />
        </aside>

        <main className="main-panel">
          <div className="tab-row">
            <button className={tab === 'live' ? 'tab active' : 'tab'} onClick={() => setTab('live')}>
              Live Grid
            </button>
            <button className={tab === 'search' ? 'tab active' : 'tab'} onClick={() => setTab('search')}>
              Search
            </button>
            <button className={tab === 'heatmap' ? 'tab active' : 'tab'} onClick={() => setTab('heatmap')}>
              Heatmap
            </button>
          </div>
          {tab === 'live' ? (
            <LiveGrid
              cameras={cameras}
              selectedCameraId={selectedCameraId}
              onSelectCamera={selectCamera}
              onSelectPerson={selectPerson}
            />
          ) : null}
          {tab === 'search' ? (
            <SemanticSearch
              token={token}
              results={searchResults}
              onResults={setSearchResults}
              onSelectPerson={selectPerson}
            />
          ) : null}
          {tab === 'heatmap' ? <CrowdHeatmap densityMap={latestHeatmap?.density_map} /> : null}
        </main>

        <aside className="sidebar right">
          <AlertFeed alerts={activeAlerts} onAcknowledge={acknowledgeAlert} />
          <PersonCard profile={selectedPersonProfile} />
        </aside>
      </div>
    </div>
  )
}

function App() {
  const { token, login, logout, isAuthenticated } = useAuth()

  if (!isAuthenticated || !token) {
    return <LoginPage onLogin={login} />
  }

  return <Dashboard token={token} logout={logout} />
}

export default App
