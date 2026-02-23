import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type AppointmentFull } from '../api'
import { formatDate } from '../utils'
import { Card, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'

const PAGE_SIZE = 50

function formatSlot(slotStart: string): string {
  return new Date(slotStart).toLocaleString([], {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

function durationMinutes(startIso: string, endIso: string): number {
  const start = new Date(startIso).getTime()
  const end = new Date(endIso).getTime()
  return Math.max(0, Math.round((end - start) / 60000))
}

function getBadgeVariant(status: string): "success" | "destructive" | "warning" | "secondary" {
  if (status === 'confirmed') return 'success'
  if (status === 'cancelled') return 'destructive'
  if (status === 'rescheduled') return 'warning'
  return 'secondary'
}

export default function Appointments() {
  const [rows, setRows] = useState<AppointmentFull[]>([])
  const [statusFilter, setStatusFilter] = useState('all')
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadRows = async (nextOffset: number, reset = false, selectedStatus = statusFilter) => {
    try {
      setError('')
      const status = selectedStatus === 'all' ? undefined : selectedStatus
      const data = await api.getAllAppointments(PAGE_SIZE, nextOffset, status)
      setHasMore(data.length === PAGE_SIZE)
      setOffset(nextOffset + data.length)
      if (reset) {
        setRows(data)
      } else {
        setRows((prev) => [...prev, ...data])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load appointments')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRows(0, true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const onStatusChange = async (value: string) => {
    setStatusFilter(value)
    setLoading(true)
    await loadRows(0, true, value)
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Card className="animate-pulse"><CardContent className="p-6 h-16" /></Card>
        <Card className="animate-pulse"><CardContent className="p-6 h-[400px]" /></Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Appointments</h1>
      </div>

      {error && (
        <div className="flex items-center justify-between rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-destructive">
          <span className="text-sm font-medium">{error}</span>
          <Button variant="danger" size="sm" onClick={() => loadRows(0, true)}>
            Retry
          </Button>
        </div>
      )}

      <Card>
        <CardContent className="p-4 sm:p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
            <select
              value={statusFilter}
              onChange={(event) => onStatusChange(event.target.value)}
              className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:w-[200px]"
            >
              <option value="all">All Appointments</option>
              <option value="confirmed">Confirmed</option>
              <option value="cancelled">Cancelled</option>
              <option value="rescheduled">Rescheduled</option>
            </select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="px-0 py-0">
          {rows.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 text-center text-muted-foreground">
              <p className="text-sm font-medium">No appointments found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/50 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    <th className="px-6 py-4">Contact</th>
                    <th className="px-6 py-4">Date/Time</th>
                    <th className="px-6 py-4">Duration</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4">Booked</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {rows.map((appointment) => (
                    <tr key={appointment.id} className="transition-colors hover:bg-muted/50">
                      <td className="whitespace-nowrap px-6 py-4">
                        <Link to={`/contacts/${appointment.contact_id}`} className="font-medium text-foreground hover:underline">
                          {appointment.contact_name || appointment.contact_phone}
                        </Link>
                        {appointment.contact_name && (
                          <p className="text-xs text-muted-foreground mt-0.5">{appointment.contact_phone}</p>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-foreground">{formatSlot(appointment.slot_start)}</td>
                      <td className="whitespace-nowrap px-6 py-4 text-muted-foreground">
                        {durationMinutes(appointment.slot_start, appointment.slot_end)} min
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <Badge variant={getBadgeVariant(appointment.status)}>
                          {appointment.status}
                        </Badge>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-muted-foreground">{formatDate(appointment.booked_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-center">
        <Button
          variant="secondary"
          onClick={() => loadRows(offset)}
          disabled={!hasMore}
          className="w-full sm:w-auto"
        >
          Load More
        </Button>
      </div>
    </div>
  )
}
