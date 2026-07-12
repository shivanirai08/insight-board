import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api } from './api'
import type { User } from './types'

const TOKEN_KEY = 'insightboard_token'

type AuthState = {
  token: string | null
  user: User | null
  loading: boolean
  loginWithToken: (token: string) => Promise<void>
  devLogin: (email: string, fullName: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
  }, [])

  const loginWithToken = useCallback(async (next: string) => {
    const me = await api.me(next)
    localStorage.setItem(TOKEN_KEY, next)
    setToken(next)
    setUser(me)
  }, [])

  const devLogin = useCallback(
    async (email: string, fullName: string) => {
      const { access_token } = await api.devLogin(email, fullName)
      await loginWithToken(access_token)
    },
    [loginWithToken],
  )

  useEffect(() => {
    let cancelled = false
    async function boot() {
      if (!token) {
        setLoading(false)
        return
      }
      try {
        const me = await api.me(token)
        if (!cancelled) setUser(me)
      } catch {
        if (!cancelled) logout()
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void boot()
    return () => {
      cancelled = true
    }
  }, [token, logout])

  const value = useMemo(
    () => ({ token, user, loading, loginWithToken, devLogin, logout }),
    [token, user, loading, loginWithToken, devLogin, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
