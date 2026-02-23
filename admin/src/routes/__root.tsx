import { createRootRoute, Outlet } from '@tanstack/react-router'
import { ThemeProvider } from '../components/layout/theme-provider'
import { Toaster } from '../components/ui/sonner'
import { NotFoundPage } from '../components/NotFoundPage'

function RootComponent() {
  return (
    <ThemeProvider>
      <Outlet />
      <Toaster />
    </ThemeProvider>
  )
}

export const __rootRoute = createRootRoute({
  component: RootComponent,
  notFoundComponent: NotFoundPage,
})
export const Route = __rootRoute
