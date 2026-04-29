import { useState } from 'react'
import type { FormEvent } from 'react'

interface LoginPageProps {
  onLogin: (username: string, password: string) => Promise<void>
}

export function LoginPage({ onLogin }: LoginPageProps) {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('changeme')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      await onLogin(username, password)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-shell">
      <form className="login-card" onSubmit={handleSubmit}>
        <h1 className="brand">
          VisionGuard<span>AI</span>
        </h1>
        <p className="login-subtitle">Operator Access</p>
        <label>
          Username
          <input value={username} onChange={(event) => setUsername(event.target.value)} />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        {error ? <div className="error-banner">{error}</div> : null}
        <button className="primary-button" type="submit" disabled={loading}>
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
      </form>
    </div>
  )
}
