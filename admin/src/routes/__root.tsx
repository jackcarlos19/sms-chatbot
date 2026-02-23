import { createRootRoute, Outlet } from '@tanstack/react-router'
import { ThemeProvider } from '../components/layout/theme-provider'

function RootComponent() {
  return (
    <ThemeProvider>
      <Outlet />
    </ThemeProvider>
  )
}

export const __rootRoute = createRootRoute({
  component: RootComponent,
})
export const Route = __rootRoute
