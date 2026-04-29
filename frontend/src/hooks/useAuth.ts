import { useMemo, useState } from 'react'

const STORAGE_KEY = 'visionguard_token'

function parseJwtExpiry(token: string): number | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.exp ? payload.exp * 1000 : null
  } catch {
    return null
  }
}

export function useAuth() {
  const [token, setToken] = useState<string | null>(() => {
    const stored = sessionStorage.getItem(STORAGE_KEY)
    if (!stored) return null
    const expiry = parseJwtExpiry(stored)
    if (expiry && expiry <= Date.now()) {
      sessionStorage.removeItem(STORAGE_KEY)
      return null
    }
    return stored
  })

  const isAuthenticated = useMemo(() => Boolean(token), [token])

  async function login(username: string, password: string) {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    if (!response.ok) {
      throw new Error('Invalid credentials')
    }
    const data = await response.json()
    sessionStorage.setItem(STORAGE_KEY, data.token)
    setToken(data.token)
  }

  function logout() {
    sessionStorage.removeItem(STORAGE_KEY)
    setToken(null)
  }

  return { token, login, logout, isAuthenticated }
}
