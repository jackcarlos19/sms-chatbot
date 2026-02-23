import * as React from 'react'
import { Link, useLocation } from '@tanstack/react-router'
import { Button } from '../ui/Button'
import { SheetContent, SheetProvider } from '../ui/Sheet'
import { Icons } from '../ui/Icons'

const SIDEBAR_COOKIE = 'sidebar_state'

function getSidebarState(): boolean {
  if (typeof document === 'undefined') return true
  const v = document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${SIDEBAR_COOKIE}=`))
  return v ? v.split('=')[1] !== 'closed' : true
}

function setSidebarState(open: boolean) {
  document.cookie = `${SIDEBAR_COOKIE}=${open ? 'open' : 'closed'}; path=/; max-age=31536000`
}

type SidebarContextValue = {
  open: boolean
  setOpen: (open: boolean) => void
  mobileOpen: boolean
  setMobileOpen: (open: boolean) => void
}

const SidebarContext = React.createContext<SidebarContextValue | null>(null)

export function useSidebar() {
  const ctx = React.useContext(SidebarContext)
  if (!ctx) throw new Error('Sidebar components must be used within SidebarProvider')
  return ctx
}

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [open, setOpenState] = React.useState(getSidebarState)
  const [mobileOpen, setMobileOpen] = React.useState(false)

  const setOpen = React.useCallback((value: boolean) => {
    setOpenState(value)
    setSidebarState(value)
  }, [])

  const value = React.useMemo<SidebarContextValue>(
    () => ({ open, setOpen, mobileOpen, setMobileOpen }),
    [open, setOpen, mobileOpen]
  )

  React.useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
        e.preventDefault()
        setOpen(!open)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, setOpen])

  return <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>
}

const navItems: { to: string; label: string; icon: React.ReactNode }[] = [
  { to: '/', label: 'Dashboard', icon: <Icons.Dashboard className="h-5 w-5" /> },
  { to: '/contacts', label: 'Contacts', icon: <Icons.Contacts className="h-5 w-5" /> },
  { to: '/appointments', label: 'Appointments', icon: <Icons.Appointments className="h-5 w-5" /> },
  { to: '/waitlist', label: 'Waitlist', icon: <Icons.Waitlist className="h-5 w-5" /> },
  { to: '/workflows', label: 'Workflows', icon: <Icons.Workflows className="h-5 w-5" /> },
  { to: '/conversations', label: 'Conversations', icon: <Icons.Conversations className="h-5 w-5" /> },
  { to: '/campaigns', label: 'Campaigns', icon: <Icons.Campaigns className="h-5 w-5" /> },
  { to: '/admin-users', label: 'Admin Users', icon: <Icons.Security className="h-5 w-5" /> },
  { to: '/simulator', label: 'Simulator', icon: <Icons.Simulator className="h-5 w-5" /> },
  { to: '/slots', label: 'Slots', icon: <Icons.Slots className="h-5 w-5" /> },
]

function NavContent({ onNavigate }: { onNavigate?: () => void }) {
  const location = useLocation()
  const pathname = location.pathname

  return (
    <nav className="flex flex-1 flex-col gap-1 overflow-y-auto px-3 py-4">
      {navItems.map((item) => {
        const isActive = pathname === item.to || (item.to !== '/' && pathname.startsWith(item.to))
        return (
          <Link
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              isActive
                ? 'bg-secondary text-secondary-foreground'
                : 'text-muted-foreground hover:bg-secondary/50 hover:text-foreground'
            }`}
          >
            {item.icon}
            <span className="truncate">{item.label}</span>
          </Link>
        )
      })}
    </nav>
  )
}

export function Sidebar() {
  return (
    <aside
      className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r border-border bg-card text-card-foreground md:flex"
      data-state="open"
    >
      <SidebarHeader />
      <SidebarContent />
      <SidebarFooter />
    </aside>
  )
}

export function SidebarHeader() {
  return (
    <div className="flex h-16 shrink-0 items-center border-b border-border px-6">
      <h1 className="text-lg font-semibold tracking-tight">SMS Chatbot</h1>
      <span className="ml-2 rounded-full bg-secondary px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-secondary-foreground">
        Admin
      </span>
    </div>
  )
}

export function SidebarContent() {
  return <NavContent />
}

export function SidebarFooter() {
  const logout = async () => {
    const { api } = await import('../../api')
    await api.logout()
    window.location.reload()
  }
  return (
    <div className="border-t border-border p-4">
      <button
        type="button"
        className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-secondary/50 hover:text-foreground"
        onClick={logout}
      >
        <Icons.LogOut className="h-5 w-5" />
        Logout
      </button>
    </div>
  )
}

export function SidebarInset({ children }: { children: React.ReactNode }) {
  return <div className="flex flex-1 flex-col md:pl-64">{children}</div>
}

export function SidebarTrigger() {
  const { setMobileOpen, open, setOpen } = useSidebar()
  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border bg-transparent text-muted-foreground transition-colors hover:bg-secondary md:inline-flex"
      onClick={() => {
        if (window.innerWidth < 768) {
          setMobileOpen(true)
        } else {
          setOpen(!open)
        }
      }}
      aria-label="Toggle sidebar"
    >
      <Icons.Menu className="h-5 w-5" />
    </Button>
  )
}

export function AppSidebarWithSheet() {
  const { mobileOpen, setMobileOpen } = useSidebar()
  return (
    <>
      <Sidebar />
      <SheetProvider open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="flex flex-col p-0">
          <div className="flex h-16 items-center border-b border-border px-6">
            <h1 className="text-lg font-semibold tracking-tight">SMS Chatbot</h1>
            <span className="ml-2 rounded-full bg-secondary px-2 py-0.5 text-[10px] font-medium uppercase text-secondary-foreground">
              Admin
            </span>
          </div>
          <NavContent onNavigate={() => setMobileOpen(false)} />
          <div className="border-t border-border p-4">
            <button
              type="button"
              className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-secondary/50 hover:text-foreground"
              onClick={async () => {
                const { api } = await import('../../api')
                await api.logout()
                window.location.reload()
              }}
            >
              <Icons.LogOut className="h-5 w-5" />
              Logout
            </button>
          </div>
        </SheetContent>
      </SheetProvider>
    </>
  )
}
