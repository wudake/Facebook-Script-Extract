import { useState, useRef } from 'react'
import { useNavigate, useLocation, Navigate } from 'react-router-dom'
import { Lock, User, LogIn, Loader2, Video, AlertCircle } from 'lucide-react'
import { login, isAuthenticated } from '../utils/auth'

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const isSubmittingRef = useRef(false)

  if (isAuthenticated()) {
    const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname || '/'
    return <Navigate to={from} replace />
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (isSubmittingRef.current) return
    isSubmittingRef.current = true
    setError('')
    setLoading(true)

    try {
      const ok = login(username.trim(), password)
      if (!ok) {
        setError('用户名或密码错误')
        return
      }
      const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname || '/'
      navigate(from, { replace: true })
    } finally {
      setLoading(false)
      isSubmittingRef.current = false
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-gray-50 to-primary-100 px-4">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-primary-600 text-white flex items-center justify-center shadow-lg mb-3">
            <Video className="w-7 h-7" />
          </div>
          <h1 className="text-xl font-bold text-gray-900">Video Script Extractor</h1>
          <p className="text-sm text-gray-500 mt-1">团队版 · 请登录后使用</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-5"
        >
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">用户名</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                required
                autoComplete="username"
                placeholder="请输入用户名"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">密码</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="password"
                required
                autoComplete="current-password"
                placeholder="请输入密码"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
              />
            </div>
          </div>

          {error && (
            <div className="bg-red-50 text-red-700 text-sm rounded-lg px-4 py-3 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-700 text-white font-medium py-2.5 rounded-lg transition-colors disabled:opacity-60"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <LogIn className="w-4 h-4" />}
            {loading ? '登录中...' : '登录'}
          </button>
        </form>

        <p className="text-center text-xs text-gray-400 mt-6">
          仅限授权用户访问 · 登录状态保留 7 天
        </p>
      </div>
    </div>
  )
}
