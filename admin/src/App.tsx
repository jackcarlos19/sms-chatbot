import React, { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { api } from './api'
import Appointments from './pages/Appointments'
import AppointmentDetailPage from './pages/AppointmentDetail'
import AdminUsers from './pages/AdminUsers'
import Campaigns from './pages/Campaigns'
import ContactDetail from './pages/ContactDetail'
import Contacts from './pages/Contacts'
import Conversations from './pages/Conversations'
import Dashboard from './pages/Dashboard'
import Simulator from './pages/Simulator'
import Slots from './pages/Slots'
import Waitlist from './pages/Waitlist'
import Workflows from './pages/Workflows'
import { Icons } from './components/ui/Icons'
import { Button } from './components/ui/Button'
import { Input } from './components/ui/Input'
import { ErrorBoundary } from './components/ErrorBoundary'

const ThemeContext = React.createContext<{ theme: 'light' | 'dark'; toggleTheme: () => void }>({
  theme: 'light',
  toggleTheme: () => {},
})

function useTheme() {
  return React.useContext(ThemeContext)
}

function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    return (localStorage.getItem('theme') as 'light' | 'dark') || 'light'
  })

  useEffect(() => {
    const root = window.document.documentElement
    if (theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'))
  }

  return <ThemeContext.Provider value={{ theme, toggleTheme }}>{children}</ThemeContext.Provider>
}

type NavItem = {
  to: string
  label: string
  icon: React.ReactNode
}

const navItems: NavItem[] = [
  { to: '/', icon: <Icons.Dashboard className="h-5 w-5" />, label: 'Dashboard' },
  { to: '/contacts', icon: <Icons.Contacts className="h-5 w-5" />, label: 'Contacts' },
  { to: '/appointments', icon: <Icons.Appointments className="h-5 w-5" />, label: 'Appointments' },
  { to: '/waitlist', icon: <Icons.Waitlist className="h-5 w-5" />, label: 'Waitlist' },
  { to: '/workflows', icon: <Icons.Workflows className="h-5 w-5" />, label: 'Workflows' },
  { to: '/conversations', icon: <Icons.Conversations className="h-5 w-5" />, label: 'Conversations' },
  { to: '/campaigns', icon: <Icons.Campaigns className="h-5 w-5" />, label: 'Campaigns' },
  { to: '/admin-users', icon: <Icons.Security className="h-5 w-5" />, label: 'Admin Users' },
  { to: '/simulator', icon: <Icons.Simulator className="h-5 w-5" />, label: 'Simulator' },
  { to: '/slots', icon: <Icons.Slots className="h-5 w-5" />, label: 'Slots' },
]

function pageTitle(pathname: string): string {
  if (pathname.startsWith('/contacts/')) return 'Contact Detail'
  if (pathname.startsWith('/appointments/')) return 'Appointment Detail'
  const match = navItems.find((item) => item.to === pathname)
  return match?.label ?? 'SMS Chatbot Admin'
}

function AuthGate({ onAuthenticated }: { onAuthenticated: () => void }) {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.login({ username, password })
      onAuthenticated()
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      if (message.includes('401')) {
        setError('Invalid credentials')
      } else if (message.includes('Failed to fetch') || message.includes('NetworkError')) {
        setError('Cannot reach server. Check that the app is running at this URL and try again.')
      } else {
        setError(message || 'Cannot reach server')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <div className="w-full max-w-sm rounded-xl border border-border bg-card p-8 shadow-sm">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">SMS Chatbot</h1>
          <p className="mt-2 text-sm text-muted-foreground">Sign in to your admin account</p>
        </div>
        <form className="space-y-4" onSubmit={onSubmit}>
          <div className="space-y-1">
            <label className="text-sm font-medium text-foreground">Username</label>
            <Input
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="Username"
              autoComplete="username"
              required
            />
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium text-foreground">Password</label>
            <Input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Password"
              autoComplete="current-password"
              required
            />
          </div>
          {error && <p className="text-sm font-medium text-destructive">{error}</p>}
          <Button type="submit" disabled={loading} className="w-full" size="md">
            {loading ? 'Connecting...' : 'Connect'}
          </Button>
        </form>
      </div>
    </div>
  )
}

function AppShell() {
  const location = useLocation()
  const { theme, toggleTheme } = useTheme()
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
    // eslint-disable-next-line
    setMobileOpen(false)
  }, [location.pathname])

  const sidebarClasses = [
    'fixed inset-y-0 left-0 z-40 w-64 border-r border-border bg-card text-card-foreground',
    'transform transition-transform duration-200 ease-in-out md:translate-x-0',
    mobileOpen ? 'translate-x-0' : '-translate-x-full',
  ].join(' ')

  return (
    <div className="min-h-screen bg-background text-foreground flex">
      {/* Sidebar */}
      <aside className={sidebarClasses}>
        <div className="flex h-full flex-col">
          <div className="flex h-16 items-center border-b border-border px-6">
            <h1 className="text-lg font-semibold tracking-tight">SMS Chatbot</h1>
            <span className="ml-2 rounded-full bg-secondary px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-secondary-foreground">
              Admin
            </span>
          </div>
          <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-secondary text-secondary-foreground'
                      : 'text-muted-foreground hover:bg-secondary/50 hover:text-foreground'
                  }`
                }
              >
                {item.icon}
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="border-t border-border p-4">
            <button
              type="button"
              className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-secondary/50 hover:text-foreground"
              onClick={async () => {
                await api.logout()
                window.location.reload()
              }}
            >
              <Icons.LogOut className="h-5 w-5" />
              Logout
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <button
          className="fixed inset-0 z-30 bg-black/40 backdrop-blur-sm transition-opacity md:hidden"
          type="button"
          onClick={() => setMobileOpen(false)}
          aria-label="Close sidebar"
        />
      )}

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col md:pl-64 w-full">
        {/* Topbar */}
        <header className="sticky top-0 z-20 flex h-16 shrink-0 items-center justify-between border-b border-border bg-background/80 px-4 backdrop-blur-md md:px-8">
          <div className="flex items-center gap-4">
            <button
              className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border bg-transparent text-muted-foreground transition-colors hover:bg-secondary md:hidden"
              type="button"
              onClick={() => setMobileOpen((open) => !open)}
              aria-label="Open sidebar"
            >
              <Icons.Menu className="h-5 w-5" />
            </button>
            <h2 className="text-lg font-semibold tracking-tight">{currentTitle}</h2>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <span
                className={`relative flex h-2.5 w-2.5 ${isHealthy ? '' : 'animate-pulse'}`}
                aria-hidden="true"
              >
                {isHealthy && (
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"></span>
                )}
                <span className={`relative inline-flex h-2.5 w-2.5 rounded-full ${isHealthy ? 'bg-green-500' : 'bg-destructive'}`}></span>
              </span>
              <span className="hidden sm:inline-block">{isHealthy ? 'System Healthy' : 'System Degraded'}</span>
            </div>
            
            <div className="h-5 w-px bg-border hidden sm:block"></div>
            
            <button
              onClick={toggleTheme}
              className="inline-flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <Icons.Sun className="h-5 w-5" /> : <Icons.Moon className="h-5 w-5" />}
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-4 md:p-8">
          <div className="mx-auto max-w-6xl w-full">
            <ErrorBoundary>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/contacts" element={<Contacts />} />
                <Route path="/contacts/:id" element={<ContactDetail />} />
                <Route path="/appointments" element={<Appointments />} />
                <Route path="/appointments/:id" element={<AppointmentDetailPage />} />
                <Route path="/waitlist" element={<Waitlist />} />
                <Route path="/workflows" element={<Workflows />} />
                <Route path="/conversations" element={<Conversations />} />
                <Route path="/campaigns" element={<Campaigns />} />
                <Route path="/admin-users" element={<AdminUsers />} />
                <Route path="/simulator" element={<Simulator />} />
                <Route path="/slots" element={<Slots />} />
              </Routes>
            </ErrorBoundary>
          </div>
        </main>
      </div>
    </div>
  )
}

function App() {
  const [authenticated, setAuthenticated] = useState<boolean | null>(null)

  useEffect(() => {
    let mounted = true
    const loadAuth = async () => {
      try {
        await api.me()
        if (mounted) setAuthenticated(true)
      } catch {
        if (mounted) setAuthenticated(false)
      }
    }
    loadAuth()
    return () => {
      mounted = false
    }
  }, [])

  if (authenticated === null) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background p-6">
        <div className="h-10 w-48 animate-pulse rounded-md bg-secondary" />
      </div>
    )
  }

  return (
    <ThemeProvider>
      {!authenticated ? (
        <AuthGate onAuthenticated={() => setAuthenticated(true)} />
      ) : (
        <AppShell />
      )}
    </ThemeProvider>
  )
}

export default App
