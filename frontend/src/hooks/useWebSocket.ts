import { useEffect } from 'react'

import { useSceneStore } from '../store/sceneStore'
import type { Alert, SceneUpdate } from '../types'

export function useWebSocket(token: string | null) {
  const handleSceneUpdate = useSceneStore((state) => state.handleSceneUpdate)
  const handleAlert = useSceneStore((state) => state.handleAlert)
  const setWsConnected = useSceneStore((state) => state.setWsConnected)
  const updateHealth = useSceneStore((state) => state.updateHealth)

  useEffect(() => {
    if (!token) return
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/scene?token=${token}`)

    socket.onopen = () => setWsConnected(true)
    socket.onclose = () => setWsConnected(false)
    socket.onerror = () => setWsConnected(false)
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data)
      if (payload.type === 'scene_update') handleSceneUpdate(payload as SceneUpdate)
      if (payload.type === 'alert') handleAlert(payload as Alert)
      if (payload.type === 'heartbeat') {
        const current = useSceneStore.getState().systemHealth
        updateHealth({
          cpu_percent: payload.system.cpu_percent,
          gpu_percent: payload.system.gpu_percent,
          ram_percent: payload.system.ram_percent,
          degraded_mode: current?.degraded_mode ?? false,
          privacy_mode: current?.privacy_mode ?? 'standard',
          retention_days: current?.retention_days ?? 30,
          hardware_profile: current?.hardware_profile ?? 'mid_range',
          model_versions: current?.model_versions ?? {},
          cameras: payload.cameras,
        })
      }
    }

    const heartbeat = window.setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) socket.send('ping')
    }, 1500)

    return () => {
      window.clearInterval(heartbeat)
      socket.close()
    }
  }, [token, handleAlert, handleSceneUpdate, setWsConnected, updateHealth])
}
