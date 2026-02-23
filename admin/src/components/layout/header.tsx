import * as React from 'react'
import { Link } from '@tanstack/react-router'
import { SidebarTrigger } from './sidebar'
import { Separator } from '../ui/Separator'
import { Icons } from '../ui/Icons'
import { useTheme } from './theme-provider'

export function Header({
  title,
  className = '',
  backTo,
  backLabel = 'Back',
}: {
  title: string
  className?: string
  backTo?: string
  backLabel?: string
}) {
  const { theme, toggleTheme } = useTheme()
  const [healthy, setHealthy] = React.useState<boolean | null>(null)

  React.useEffect(() => {
    let mounted = true
    const check = async () => {
      try {
        const { api } = await import('../../api')
        await api.getHealth()
        if (mounted) setHealthy(true)
      } catch {
        if (mounted) setHealthy(false)
      }
    }
    check()
    const t = window.setInterval(check, 30000)
    return () => {
      mounted = false
      clearInterval(t)
    }
  }, [])

  return (
    <header
      className={`sticky top-0 z-20 flex h-16 shrink-0 items-center justify-between border-b border-border bg-background/80 px-4 backdrop-blur-md md:px-8 ${className}`}
    >
      <div className="flex items-center gap-4">
        <SidebarTrigger />
        <Separator orientation="vertical" className="h-5" />
        {backTo && (
          <>
            <Link
              to={backTo}
              className="inline-flex h-8 items-center justify-center rounded-md px-3 text-xs font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {backLabel}
            </Link>
            <Separator orientation="vertical" className="h-5" />
          </>
        )}
        <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <span className="relative flex h-2.5 w-2.5" aria-hidden>
            {healthy === true && (
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
            )}
            <span
              className={`relative inline-flex h-2.5 w-2.5 rounded-full ${
                healthy === true ? 'bg-green-500' : 'bg-destructive'
              } ${healthy === null ? 'animate-pulse' : ''}`}
            />
          </span>
          <span className="hidden sm:inline-block">
            {healthy === true ? 'System Healthy' : healthy === false ? 'System Degraded' : '…'}
          </span>
        </div>
        <Separator orientation="vertical" className="hidden h-5 sm:block" />
        <button
          type="button"
          onClick={toggleTheme}
          className="inline-flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? <Icons.Sun className="h-5 w-5" /> : <Icons.Moon className="h-5 w-5" />}
        </button>
      </div>
    </header>
  )
}
