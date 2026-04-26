const VALID_USERNAME = (import.meta.env.VITE_ADMIN_USERNAME || '').trim()
const VALID_PASSWORD = import.meta.env.VITE_ADMIN_PASSWORD || ''

const AUTH_KEY = 'auth_session'
const SESSION_DAYS = 7

interface Session {
  user: string
  expiry: number
}

function readSession(): Session | null {
  const raw = localStorage.getItem(AUTH_KEY)
  if (!raw) return null
  try {
    const session = JSON.parse(raw) as Session
    if (Date.now() > session.expiry) {
      localStorage.removeItem(AUTH_KEY)
      return null
    }
    return session
  } catch {
    localStorage.removeItem(AUTH_KEY)
    return null
  }
}

export function login(username: string, password: string): boolean {
  if (!VALID_USERNAME || !VALID_PASSWORD) return false
  if (username !== VALID_USERNAME || password !== VALID_PASSWORD) return false
  const session: Session = {
    user: username,
    expiry: Date.now() + SESSION_DAYS * 24 * 60 * 60 * 1000,
  }
  localStorage.setItem(AUTH_KEY, JSON.stringify(session))
  return true
}

export function logout(): void {
  localStorage.removeItem(AUTH_KEY)
}

export function isAuthenticated(): boolean {
  return readSession() !== null
}

export function getCurrentUser(): string | null {
  return readSession()?.user ?? null
}

export function isAuthConfigured(): boolean {
  return Boolean(VALID_USERNAME && VALID_PASSWORD)
}
