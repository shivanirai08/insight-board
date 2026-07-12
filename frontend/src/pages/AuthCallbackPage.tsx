import { useEffect, useState } from 'react'
import { Navigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../auth'

export function AuthCallbackPage() {
  const [params] = useSearchParams()
  const { loginWithToken } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  useEffect(() => {
    const token = params.get('token')
    if (!token) {
      setError('Missing token in callback URL')
      return
    }
    void loginWithToken(token)
      .then(() => setDone(true))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Auth failed'))
  }, [params, loginWithToken])

  if (done) return <Navigate to="/" replace />

  return (
    <div className="login-shell">
      <section className="login-panel">
        <p className="brand-mark">InsightBoard</p>
        <h1>{error ? 'Sign-in failed' : 'Finishing sign-in…'}</h1>
        {error ? <p className="error">{error}</p> : <p className="lede">Saving your session.</p>}
      </section>
    </div>
  )
}
