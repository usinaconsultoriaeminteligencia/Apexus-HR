import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { auth as authApi } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('apexus_user')
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })
  const [loading, setLoading] = useState(false)
  const [initialized, setInitialized] = useState(false)

  // Verificar token existente ao carregar
  useEffect(() => {
    const token = localStorage.getItem('apexus_token')
    if (token && !user) {
      authApi.me()
        .then((data) => {
          const u = data.user || data
          setUser(u)
          localStorage.setItem('apexus_user', JSON.stringify(u))
        })
        .catch(() => {
          localStorage.removeItem('apexus_token')
          localStorage.removeItem('apexus_user')
        })
        .finally(() => setInitialized(true))
    } else {
      setInitialized(true)
    }
  }, [])

  const login = useCallback(async (email, password) => {
    setLoading(true)
    try {
      const data = await authApi.login(email, password)
      const token = data.access_token || data.token
      const u = data.user || { email }
      localStorage.setItem('apexus_token', token)
      localStorage.setItem('apexus_user', JSON.stringify(u))
      setUser(u)
      return { success: true }
    } catch (err) {
      return { success: false, error: err.message }
    } finally {
      setLoading(false)
    }
  }, [])

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } catch {}
    localStorage.removeItem('apexus_token')
    localStorage.removeItem('apexus_user')
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, initialized, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}
