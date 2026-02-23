import { createRoute } from '@tanstack/react-router'
import { _authenticatedRoute } from '../_authenticated'
import { Header } from '../../components/layout/header'
import { Main } from '../../components/layout/main'

export const indexRoute = createRoute({
  getParentRoute: () => _authenticatedRoute,
  path: '/',
  component: DashboardPlaceholder,
})

function DashboardPlaceholder() {
  return (
    <>
      <Header title="Dashboard" />
      <Main>
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Dashboard</h2>
            <p className="text-muted-foreground">Overview and key metrics (Phase 2)</p>
          </div>
        </div>
        <div className="mt-6 rounded-xl border border-border bg-card p-6 text-center text-muted-foreground">
          Shell ready. Dashboard content will be built in Phase 2.
        </div>
      </Main>
    </>
  )
}

export const Route = indexRoute
