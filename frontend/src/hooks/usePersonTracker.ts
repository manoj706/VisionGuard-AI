import { useMemo } from 'react'

import { useSceneStore } from '../store/sceneStore'

export function usePersonTracker(globalPersonId: string | null) {
  const cameras = useSceneStore((state) => state.cameras)

  return useMemo(() => {
    if (!globalPersonId) return []
    return cameras.flatMap((camera) =>
      camera.currentPersons.filter((person) => person.globalPersonId === globalPersonId),
    )
  }, [cameras, globalPersonId])
}
