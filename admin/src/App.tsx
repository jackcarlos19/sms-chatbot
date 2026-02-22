import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { api, clearApiKey, hasApiKey, setApiKey } from './api'
import Appointments from './pages/Appointments'
import Campaigns from './pages/Campaigns'
import ContactDetail from './pages/ContactDetail'
import Contacts from './pages/Contacts'
import Conversations from './pages/Conversations'
import Dashboard from './pages/Dashboard'
import Simulator from './pages/Simulator'
import Slots from './pages/Slots'

type NavItem = {
  to: string
  label: string
  icon: string
}

const navItems: NavItem[] = [
  { to: '/', icon: '📊', label: 'Dashboard' },
  { to: '/contacts', icon: '👥', label: 'Contacts' },
  { to: '/appointments', icon: '📅', label: 'Appointments' },
  { to: '/conversations', icon: '💬', label: 'Conversations' },
  { to: '/campaigns', icon: '📣', label: 'Campaigns' },
  { to: '/simulator', icon: '🧪', label: 'Simulator' },
  { to: '/slots', icon: '🗓️', label: 'Slots' },
]

function pageTitle(pathname: string): string {
  if (pathname.startsWith('/contacts/')) return 'Contact Detail'
  const match = navItems.find((item) => item.to === pathname)
  return match?.label ?? 'SMS Chatbot Admin'
}

function AuthGate({ onAuthenticated }: { onAuthenticated: () => void }) {
  const [apiKey, setEnteredApiKey] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.getHealth(apiKey)
      setApiKey(apiKey)
      onAuthenticated()
    } catch (err) {
      const message = err instanceof Error ? err.message : ''
      if (message.includes('401')) {
        setError('Invalid API key')
      } else {
        setError('Cannot reach server')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 p-6">
      <div className="w-full max-w-md rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-bold text-gray-900">SMS Chatbot Admin</h1>
        <p className="mt-2 text-sm text-gray-600">Enter your admin API key to continue</p>
        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <input
            type="password"
            value={apiKey}
            onChange={(event) => setEnteredApiKey(event.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900"
            placeholder="Admin API key"
            required
          />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {loading ? 'Connecting...' : 'Connect'}
          </button>
        </form>
      </div>
    </div>
  )
}

function AppShell() {
  const location = useLocation()
  const [isHealthy, setIsHealthy] = useState(true)
  const [mobileOpen, setMobileOpen] = useState(false)

  const currentTitle = useMemo(() => pageTitle(location.pathname), [location.pathname])

  useEffect(() => {
    let mounted = true
    const checkHealth = async () => {
      try {
        await api.getHealth()
        if (mounted) setIsHealthy(true)
      } catch {
        if (mounted) setIsHealthy(false)
      }
    }
    checkHealth()
    const timer = window.setInterval(checkHealth, 30000)
    return () => {
      mounted = false
      window.clearInterval(timer)
    }
  }, [])

  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  const sidebarClasses = [
    'fixed inset-y-0 left-0 z-40 w-64 bg-gray-900 text-white',
    'transform transition-transform duration-200 md:translate-x-0',
    mobileOpen ? 'translate-x-0' : '-translate-x-full',
  ].join(' ')

  return (
    <div className="min-h-screen bg-gray-50">
      <aside className={sidebarClasses}>
        <div className="flex h-full flex-col">
          <div className="border-b border-gray-800 px-6 py-5">
            <h1 className="text-lg font-bold">SMS Chatbot</h1>
            <p className="text-sm text-gray-400">Admin Panel</p>
          </div>
          <nav className="flex-1 space-y-1 px-3 py-4">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-md px-3 py-2 text-sm ${
                    isActive ? 'bg-gray-800 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }`
                }
              >
                <span aria-hidden="true">{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>
          <div className="border-t border-gray-800 p-3">
            <button
              type="button"
              className="w-full rounded-md bg-gray-800 px-3 py-2 text-left text-sm text-gray-200 hover:bg-gray-700"
              onClick={() => {
                clearApiKey()
                window.location.reload()
              }}
            >
              Logout
            </button>
          </div>
        </div>
      </aside>

      {mobileOpen && (
        <button
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
          type="button"
          onClick={() => setMobileOpen(false)}
          aria-label="Close sidebar"
        />
      )}

      <div className="md:ml-64">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-gray-200 bg-white px-4 md:px-6">
          <div className="flex items-center gap-3">
            <button
              className="rounded-md border border-gray-300 px-2 py-1 text-gray-700 md:hidden"
              type="button"
              onClick={() => setMobileOpen((open) => !open)}
              aria-label="Open sidebar"
            >
              ☰
            </button>
            <h2 className="text-lg font-semibold text-gray-900">{currentTitle}</h2>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                isHealthy ? 'animate-pulse bg-green-500' : 'bg-red-500'
              }`}
              aria-hidden="true"
            />
            <span>{isHealthy ? 'Healthy' : 'Unhealthy'}</span>
          </div>
        </header>
        <main className="p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/contacts" element={<Contacts />} />
            <Route path="/contacts/:id" element={<ContactDetail />} />
            <Route path="/appointments" element={<Appointments />} />
            <Route path="/conversations" element={<Conversations />} />
            <Route path="/campaigns" element={<Campaigns />} />
            <Route path="/simulator" element={<Simulator />} />
            <Route path="/slots" element={<Slots />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

function App() {
  const [authenticated, setAuthenticated] = useState(hasApiKey())

  if (!authenticated) {
    return <AuthGate onAuthenticated={() => setAuthenticated(true)} />
  }

  return <AppShell />
}

export default App
