import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import client, { setAuthToken } from '../api/client.js'

// The session auth token (from POST /auth/login) lives ONLY here, in React
// state, for the lifetime of this tab. It is never written to
// localStorage/sessionStorage/cookies and never logged — same rule as the
// BYOK LLM key in SessionContext.jsx. On every change we also mirror it into
// api/client.js's in-memory authToken variable (via setAuthToken) so the
// axios request interceptor there can attach it to every authenticated
// call; that mirror is itself just a module-level variable, never
// persisted to disk/browser storage.
const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null)

  const login = useCallback(async (username, password) => {
    // Let a 401 (invalid credentials) propagate as a rejected promise —
    // LoginPage is responsible for catching it and showing a message.
    const { data } = await client.post('/auth/login', { username, password })
    setToken(data.token)
    setAuthToken(data.token)
    return data
  }, [])

  const logout = useCallback(async () => {
    // Best-effort: tell the backend to invalidate the token, but clear the
    // local session either way so the UI never gets stuck "logged in" just
    // because the network call failed.
    try {
      await client.post('/auth/logout')
    } catch {
      // ignore — logging out client-side still proceeds below
    }
    setToken(null)
    setAuthToken(null)
  }, [])

  const value = useMemo(
    () => ({
      token,
      isAuthenticated: Boolean(token),
      login,
      logout,
    }),
    [token, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}
