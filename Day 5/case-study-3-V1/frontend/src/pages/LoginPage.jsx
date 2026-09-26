import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(username, password)
      navigate('/')
    } catch (err) {
      setError(
        err?.response?.status === 401
          ? 'Invalid username or password.'
          : err?.response?.data?.detail
            ? String(err.response.data.detail)
            : err.message || 'Login failed.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="login-page">
      <h1>Log in</h1>
      <p className="page-intro">Sign in to upload, review, and submit documents.</p>

      {error && <div className="banner banner--error">{error}</div>}

      <form className="login-form" onSubmit={handleSubmit}>
        <label className="field">
          <span>Username</span>
          <input
            type="text"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </label>
        <label className="field">
          <span>Password</span>
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        <button type="submit" disabled={submitting || !username.trim() || !password.trim()}>
          {submitting ? 'Logging in…' : 'Log in'}
        </button>
      </form>

      <p className="hint">Demo credentials: admin / admin1234</p>
    </section>
  )
}
