import { Link, Outlet, useLocation } from 'react-router-dom'
import { ClipboardList, PlayCircle, Settings, Video, FileText } from 'lucide-react'

const navItems = [
  { path: '/', label: '新建任务', icon: PlayCircle },
  { path: '/tasks', label: '任务列表', icon: ClipboardList },
  { path: '/completed', label: '已完成视频脚本', icon: FileText },
  { path: '/settings', label: '设置', icon: Settings },
]

export default function Layout() {
  const location = useLocation()

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-primary-700 font-bold text-lg">
            <Video className="w-6 h-6" />
            <span>Video Script Extractor</span>
          </Link>
          <nav className="flex items-center gap-1">
            {navItems.map((item) => {
              const active = location.pathname === item.path ||
                (item.path !== '/' && location.pathname.startsWith(item.path))
              const Icon = item.icon
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    active
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </Link>
              )
            })}
          </nav>
        </div>
      </header>

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-6">
        <Outlet />
      </main>

      <footer className="bg-white border-t border-gray-200 py-4">
        <div className="max-w-6xl mx-auto px-4 text-center text-xs text-gray-400">
          Video Script Extractor - Team Edition
        </div>
      </footer>
    </div>
  )
}
