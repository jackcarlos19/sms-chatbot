import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type AppointmentFull, type Conversation, type DashboardStats } from '../api'
import { formatDate, formatTime } from '../utils'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'

function getStatusBadgeVariant(status: string): "success" | "destructive" | "warning" | "secondary" {
  if (status === 'confirmed') return 'success'
  if (status === 'cancelled') return 'destructive'
  if (status === 'rescheduled') return 'warning'
  return 'secondary'
}

function getConversationBadgeVariant(state: string): "secondary" | "success" | "destructive" | "warning" {
  if (state === 'idle') return 'secondary'
  if (state === 'confirmed') return 'success'
  if (state === 'cancelling') return 'destructive'
  return 'warning'
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [appointments, setAppointments] = useState<AppointmentFull[]>([])
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const loadData = useCallback(async () => {
    try {
      setError('')
      const [statsData, appointmentData, conversationData] = await Promise.all([
        api.getDashboardStats(),
        api.getAllAppointments(5, 0, 'confirmed'),
        api.getConversations(10, 0),
      ])
      setStats(statsData)
      setAppointments(appointmentData.data)
      setConversations(
        conversationData.data.filter((item: Conversation) => item.current_state !== 'idle'),
      )
      setLastUpdated(new Date())
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load dashboard'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
    const timer = window.setInterval(loadData, 15000)
    return () => window.clearInterval(timer)
  }, [loadData])

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <Card key={index} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-5 w-32 rounded bg-muted" />
                <div className="mt-4 h-10 w-20 rounded bg-muted" />
                <div className="mt-3 h-4 w-24 rounded bg-muted" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Dashboard</h1>
        {lastUpdated && (
          <span className="text-xs font-medium text-muted-foreground">
            Updated {lastUpdated.toLocaleTimeString()}
          </span>
        )}
      </div>

      {error && (
        <div className="flex items-center justify-between rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-destructive">
          <span className="text-sm font-medium">{error}</span>
          <Button variant="danger" size="sm" onClick={loadData}>
            Retry
          </Button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="border-l-4 border-l-blue-500">
          <CardHeader className="pb-2">
            <CardDescription className="font-medium">Appointments Today</CardDescription>
            <CardTitle className="text-3xl">{stats?.appointments_today ?? 0}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">Upcoming: {stats?.appointments_upcoming ?? 0}</p>
          </CardContent>
        </Card>
        
        <Card className="border-l-4 border-l-orange-500">
          <CardHeader className="pb-2">
            <CardDescription className="font-medium">Active Conversations</CardDescription>
            <CardTitle className="text-3xl">{stats?.conversations_active ?? 0}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">Total campaigns: {stats?.campaigns_total ?? 0}</p>
          </CardContent>
        </Card>
        
        <Card className="border-l-4 border-l-purple-500">
          <CardHeader className="pb-2">
            <CardDescription className="font-medium">Messages Today</CardDescription>
            <CardTitle className="text-3xl">{stats?.messages_today ?? 0}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600 dark:text-green-400">↑{stats?.messages_inbound_today ?? 0}</span> inbound
              {' · '}
              <span className="text-blue-600 dark:text-blue-400">↓{stats?.messages_outbound_today ?? 0}</span> outbound
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-green-500">
          <CardHeader className="pb-2">
            <CardDescription className="font-medium">Total Contacts</CardDescription>
            <CardTitle className="text-3xl">{stats?.contacts_total ?? 0}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">{stats?.contacts_opted_in ?? 0} active</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Upcoming Appointments</CardTitle>
          </CardHeader>
          <CardContent className="px-0 pt-0">
            {appointments.length === 0 ? (
              <p className="px-6 pb-6 text-sm text-muted-foreground">No upcoming appointments</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-y border-border bg-muted/50 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      <th className="px-6 py-3">Contact</th>
                      <th className="px-6 py-3">Time</th>
                      <th className="px-6 py-3 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {appointments.map((item) => (
                      <tr key={item.id} className="transition-colors hover:bg-muted/50">
                        <td className="px-6 py-3">
                          <Link to={`/contacts/${item.contact_id}`} className="font-medium text-foreground hover:underline">
                            {item.contact_name || item.contact_phone}
                          </Link>
                        </td>
                        <td className="whitespace-nowrap px-6 py-3 text-muted-foreground">
                          {formatDate(item.slot_start)}
                          <span className="ml-1 hidden text-xs sm:inline">({formatTime(item.slot_start)})</span>
                        </td>
                        <td className="px-6 py-3 text-right">
                          <Badge variant={getStatusBadgeVariant(item.status)}>
                            {item.status}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Active Conversations</CardTitle>
          </CardHeader>
          <CardContent>
            {conversations.length === 0 ? (
              <p className="text-sm text-muted-foreground">No active conversations</p>
            ) : (
              <ul className="space-y-4">
                {conversations.map((item) => (
                  <li key={item.id} className="flex flex-col justify-between gap-x-6 border-b border-border pb-4 last:border-0 last:pb-0 sm:flex-row sm:items-center">
                    <div className="flex flex-col">
                      <Link to={`/contacts/${item.contact_id}`} className="text-sm font-medium text-foreground hover:underline">
                        {item.contact_phone}
                      </Link>
                      <p className="mt-1 text-xs text-muted-foreground">Last message: {formatDate(item.last_message_at)}</p>
                    </div>
                    <div className="mt-2 sm:mt-0">
                      <Badge variant={getConversationBadgeVariant(item.current_state)}>
                        {item.current_state.replace('_', ' ')}
                      </Badge>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
