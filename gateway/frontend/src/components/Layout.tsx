import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../store/auth'
import LanguageSelector from './LanguageSelector'
import {
  LayoutDashboard,
  FileCode2,
  GitPullRequest,
  RefreshCw,
  Bot,
  FileText,
  Settings,
  LogOut,
  Menu,
  X,
  AlertTriangle,
  Zap,
  Database,
  Users,
  ShieldCheck,
  FlaskConical,
  UserCog,
} from 'lucide-react'

interface LayoutProps {
  children: React.ReactNode
}

const navigationKeys = [
  { key: 'nav.dashboard', href: '/dashboard', icon: LayoutDashboard },
  { key: 'nav.users', href: '/dashboard/midpoint-users', icon: Users },
  { key: 'nav.ldapGroups', href: '/dashboard/ldap-groups', icon: ShieldCheck },
  { key: 'nav.rules', href: '/dashboard/rules', icon: FileCode2 },
  { key: 'nav.workflows', href: '/dashboard/workflows', icon: GitPullRequest },
  { key: 'nav.reconciliation', href: '/dashboard/reconciliation', icon: RefreshCw },
  { key: 'nav.liveComparison', href: '/dashboard/live', icon: Zap },
  { key: 'nav.connectors', href: '/dashboard/connectors', icon: Database },
  { key: 'nav.gatewayUsers', href: '/dashboard/gateway-users', icon: UserCog },
  { key: 'nav.aiAssistant', href: '/dashboard/ai', icon: Bot },
  { key: 'nav.audit', href: '/dashboard/audit', icon: FileText },
  { key: 'nav.settings', href: '/dashboard/settings', icon: Settings },
]

export default function Layout({ children }: LayoutProps) {
  const { t } = useTranslation()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar */}
      <div
        className={`fixed inset-0 z-50 lg:hidden ${
          sidebarOpen ? 'block' : 'hidden'
        }`}
      >
        <div
          className="fixed inset-0 bg-gray-900/50"
          onClick={() => setSidebarOpen(false)}
        />
        <div className="fixed inset-y-0 left-0 w-64 bg-white shadow-xl">
          <div className="flex items-center justify-between h-16 px-6 border-b">
            <span className="text-xl font-bold text-blue-600">Gateway IAM</span>
            <button onClick={() => setSidebarOpen(false)}>
              <X className="w-6 h-6" />
            </button>
          </div>
          <nav className="p-4 space-y-1">
            {navigationKeys.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.key}
                  to={item.href}
                  className={`flex items-center px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-50 text-blue-600'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon className="w-5 h-5 mr-3" />
                  {t(item.key)}
                </Link>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-1 bg-white border-r border-gray-200">
          <div className="flex items-center h-16 px-6 border-b">
            <span className="text-xl font-bold text-blue-600">Gateway IAM</span>
          </div>
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {navigationKeys.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.key}
                  to={item.href}
                  className={`flex items-center px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-50 text-blue-600'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <item.icon className="w-5 h-5 mr-3" />
                  {t(item.key)}
                </Link>
              )
            })}
          </nav>
          <div className="p-4 border-t">
            <div className="flex items-center mb-4">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 font-semibold">
                  {user?.username?.[0]?.toUpperCase() || 'U'}
                </span>
              </div>
              <div className="ml-3">
                <p className="font-medium">{user?.username}</p>
                <p className="text-sm text-gray-500">
                  {user?.roles?.join(', ')}
                </p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center w-full px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-100"
            >
              <LogOut className="w-5 h-5 mr-3" />
              {t('common.logout')}
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <header className="sticky top-0 z-40 flex items-center h-16 px-4 bg-white border-b border-gray-200 lg:px-8">
          <button
            className="lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-6 h-6" />
          </button>

          <div className="flex-1" />

          {/* Language selector */}
          <LanguageSelector />

          {/* Test/Operations button */}
          <Link
            to="/dashboard/operations"
            className="flex items-center px-4 py-2 ml-2 text-purple-600 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors"
            title="Test - Operations"
          >
            <FlaskConical className="w-5 h-5 mr-2" />
            {t('nav.test')}
          </Link>

          {/* Emergency stop button */}
          <button className="flex items-center px-4 py-2 ml-2 text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors">
            <AlertTriangle className="w-5 h-5 mr-2" />
            {t('nav.emergencyStop')}
          </button>

          {/* Logout button */}
          <button
            onClick={handleLogout}
            className="flex items-center ml-2 px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <LogOut className="w-5 h-5 mr-2" />
            {t('common.logout')}
          </button>
        </header>

        {/* Page content */}
        <main className="p-4 lg:p-8">{children}</main>
      </div>
    </div>
  )
}
