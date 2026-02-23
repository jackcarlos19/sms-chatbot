import * as React from 'react'
import { Link, createRoute } from '@tanstack/react-router'
import { _authenticatedRoute } from '../_authenticated'
import { Header } from '../../components/layout/header'
import { Main } from '../../components/layout/main'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../../components/ui/Card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/Table'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Skeleton } from '../../components/ui/Skeleton'
import { api } from '../../api'
import type { DashboardStats, AppointmentFull, Conversation } from '../../api'

export const indexRoute = createRoute({
  getParentRoute: () => _authenticatedRoute,
  path: '/',
  component: DashboardPage,
})

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: 'short',
      timeStyle: 'short',
    })
  } catch {
    return iso
  }
}

function StatCard({
  title,
  value,
  description,
  loading,
}: {
  title: string
  value: string | number
  description?: string
  loading?: boolean
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-16" />
        ) : (
          <>
            <div className="text-2xl font-bold">{value}</div>
            {description && (
              <p className="text-xs text-muted-foreground">{description}</p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}

function DashboardPage() {
  const [stats, setStats] = React.useState<DashboardStats | null>(null)
  const [appointments, setAppointments] = React.useState<AppointmentFull[]>([])
  const [conversations, setConversations] = React.useState<Conversation[]>([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    Promise.all([
      api.getDashboardStats(),
      api.getAllAppointmentsFiltered({ limit: 10 }),
      api.getConversations(10, 0),
    ])
      .then(([s, a, c]) => {
        if (cancelled) return
        setStats(s)
        setAppointments(a.data ?? [])
        setConversations(c.data ?? [])
      })
      .catch((err) => {
        if (cancelled) return
        setError(err instanceof Error ? err.message : String(err))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <>
      <Header title="Dashboard" />
      <Main>
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Dashboard</h2>
            <p className="text-muted-foreground">
              Overview and key metrics
            </p>
          </div>
        </div>

        {error && (
          <div className="mt-4 rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive">
            <p>{error}</p>
            <Button
              variant="secondary"
              size="sm"
              className="mt-2"
              onClick={() => window.location.reload()}
            >
              Retry
            </Button>
          </div>
        )}

        {/* Stats grid */}
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Contacts (total)"
            value={stats?.contacts_total ?? 0}
            loading={loading}
          />
          <StatCard
            title="Opted in"
            value={stats?.contacts_opted_in ?? 0}
            loading={loading}
          />
          <StatCard
            title="Appointments today"
            value={stats?.appointments_today ?? 0}
            loading={loading}
          />
          <StatCard
            title="Upcoming"
            value={stats?.appointments_upcoming ?? 0}
            loading={loading}
          />
          <StatCard
            title="Messages today"
            value={stats?.messages_today ?? 0}
            loading={loading}
          />
          <StatCard
            title="Active conversations"
            value={stats?.conversations_active ?? 0}
            loading={loading}
          />
          <StatCard
            title="Campaigns active"
            value={stats?.campaigns_active ?? 0}
            loading={loading}
          />
          <StatCard
            title="Campaigns total"
            value={stats?.campaigns_total ?? 0}
            loading={loading}
          />
        </div>

        {/* Recent appointments & Active conversations */}
        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Recent appointments</CardTitle>
              <CardDescription>Latest booked appointments</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-10 w-full" />
                  ))}
                </div>
              ) : appointments.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No appointments yet.
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Contact</TableHead>
                      <TableHead>Date / Time</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {appointments.map((a) => (
                      <TableRow key={a.id}>
                        <TableCell>
                          <Link
                            to="/appointments/$appointmentId"
                            params={{ appointmentId: a.id }}
                            className="font-medium text-primary hover:underline"
                          >
                            {a.contact_name || a.contact_phone}
                          </Link>
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {formatDate(a.slot_start)}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              a.status === 'cancelled' ? 'destructive' : 'secondary'
                            }
                          >
                            {a.status}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Active conversations</CardTitle>
              <CardDescription>Recent conversation activity</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-10 w-full" />
                  ))}
                </div>
              ) : conversations.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No active conversations.
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Contact</TableHead>
                      <TableHead>State</TableHead>
                      <TableHead>Last message</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {conversations.map((c) => (
                      <TableRow key={c.id}>
                        <TableCell>
                          <Link
                            to="/contacts/$contactId"
                            params={{ contactId: c.contact_id }}
                            className="font-medium text-primary hover:underline"
                          >
                            {c.contact_name || c.contact_phone}
                          </Link>
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary">{c.current_state}</Badge>
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {c.last_message_at
                            ? formatDate(c.last_message_at)
                            : '—'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
      </Main>
    </>
  )
}

export const Route = indexRoute
