import { useState, type FormEvent } from 'react'
import { Navigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'

export function LoginPage() {
  const { user, loading, devLogin } = useAuth()
  const [email, setEmail] = useState('you@example.com')
  const [fullName, setFullName] = useState('You')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (!loading && user) return <Navigate to="/" replace />

  async function onDevSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await devLogin(email, fullName)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-shell">
      <div className="login-atmosphere" aria-hidden />
      <section className="login-panel">
        <p className="brand-mark">InsightBoard</p>
        <h1>See the story in your numbers</h1>
        <p className="lede">
          Upload a CSV or load the sample sales set. One API powers this dashboard and the analyst
          view.
        </p>

        <a className="btn btn-primary btn-block" href={api.googleLoginUrl}>
          Continue with Google
        </a>

        <div className="divider">
          <span>or local dev login</span>
        </div>

        <form className="stack" onSubmit={onDevSubmit}>
          <label>
            Email
            <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
          </label>
          <label>
            Name
            <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
          </label>
          {error ? <p className="error">{error}</p> : null}
          <button className="btn btn-secondary btn-block" type="submit" disabled={busy}>
            {busy ? 'Signing in…' : 'Dev login'}
          </button>
        </form>
      </section>
    </div>
  )
}
