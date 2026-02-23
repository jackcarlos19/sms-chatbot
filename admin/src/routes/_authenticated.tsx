import { createRoute, redirect, Outlet } from '@tanstack/react-router'
import { __rootRoute } from './__root'
import { api } from '../api'
import { SidebarProvider, AppSidebarWithSheet, SidebarInset } from '../components/layout/sidebar'

async function ensureAuthenticated() {
  try {
    const res = await api.me()
    if (!res.authenticated) throw redirect({ to: '/sign-in' })
  } catch (e) {
    if (e && typeof e === 'object' && 'to' in e) throw e
    throw redirect({ to: '/sign-in' })
  }
}

export const _authenticatedRoute = createRoute({
  getParentRoute: () => __rootRoute,
  id: '_authenticated',
  beforeLoad: ensureAuthenticated,
  component: AuthenticatedLayout,
})

function AuthenticatedLayout() {
  return (
    <SidebarProvider>
      <AppSidebarWithSheet />
      <SidebarInset>
        <Outlet />
      </SidebarInset>
    </SidebarProvider>
  )
}

export const Route = _authenticatedRoute
