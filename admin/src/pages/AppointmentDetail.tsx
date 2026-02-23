import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, type AppointmentDetail, type AuditEvent, type Slot } from '../api'
import { formatDate } from '../utils'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { Textarea } from '../components/ui/Textarea'

function getAppointmentBadgeVariant(status: string): "success" | "destructive" | "warning" | "secondary" {
  if (status === 'confirmed') return 'success'
  if (status === 'cancelled') return 'destructive'
  if (status === 'rescheduled') return 'warning'
  return 'secondary'
}

export default function AppointmentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [appointment, setAppointment] = useState<AppointmentDetail | null>(null)
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([])
  const [slots, setSlots] = useState<Slot[]>([])
  const [cancelReason, setCancelReason] = useState('')
  const [selectedSlotId, setSelectedSlotId] = useState('')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(true)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    if (!id) return
    try {
      setError('')
      const [detail, audits, availableSlots] = await Promise.all([
        api.getAppointment(id),
        api.getAuditEvents('appointment', id),
        api.getSlots(14),
      ])
      setAppointment(detail)
      setAuditEvents(audits)
      setSlots(availableSlots)
      setNotes(detail.notes || '')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load appointment')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const onCancel = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!id || !cancelReason.trim()) return
    setWorking(true)
    try {
      await api.cancelAppointment(id, cancelReason.trim())
      setCancelReason('')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel appointment')
    } finally {
      setWorking(false)
    }
  }

  const onReschedule = async () => {
    if (!id || !selectedSlotId) return
    setWorking(true)
    try {
      await api.rescheduleAppointment(id, selectedSlotId)
      setSelectedSlotId('')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reschedule appointment')
    } finally {
      setWorking(false)
    }
  }

  const onSaveNotes = async () => {
    if (!id) return
    setWorking(true)
    try {
      await api.updateAppointmentNotes(id, notes)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save notes')
    } finally {
      setWorking(false)
    }
  }

  if (loading) {
    return (
      <Card className="animate-pulse">
        <CardContent className="h-48 p-6" />
      </Card>
    )
  }

  if (error || !appointment) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm font-medium text-destructive">
        {error || 'Appointment not found'}
      </div>
    )
  }

  const rescheduleOptions = slots.filter((slot) => slot.is_available && slot.id !== appointment.slot_id)

  return (
    <div className="space-y-6">
      <Link to="/appointments" className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground">
        ← Back to Appointments
      </Link>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Appointment
            <Badge variant={getAppointmentBadgeVariant(appointment.status)}>{appointment.status}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p><span className="font-medium">Contact:</span> <Link className="underline" to={`/contacts/${appointment.contact_id}`}>{appointment.contact_name || appointment.contact_phone}</Link></p>
          <p><span className="font-medium">Phone:</span> {appointment.contact_phone}</p>
          <p><span className="font-medium">Slot:</span> {formatDate(appointment.slot_start)} - {formatDate(appointment.slot_end)}</p>
          <p><span className="font-medium">Booked:</span> {formatDate(appointment.booked_at)}</p>
          <p><span className="font-medium">Cancelled:</span> {formatDate(appointment.cancelled_at)}</p>
          <p><span className="font-medium">Cancel reason:</span> {appointment.cancellation_reason || '—'}</p>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-base">Internal Notes</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows={4}
              placeholder="Add admin notes..."
            />
            <Button size="sm" onClick={onSaveNotes} disabled={working}>
              {working ? 'Saving...' : 'Save Notes'}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-base">Cancel Appointment</CardTitle></CardHeader>
          <CardContent>
            <form className="space-y-3" onSubmit={onCancel}>
              <Input
                value={cancelReason}
                onChange={(event) => setCancelReason(event.target.value)}
                placeholder="Cancellation reason"
                required
              />
              <Button type="submit" variant="danger" size="sm" disabled={working}>
                {working ? 'Cancelling...' : 'Cancel Appointment'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-base">Reschedule</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Select
            value={selectedSlotId}
            onChange={(event) => setSelectedSlotId(event.target.value)}
          >
            <option value="">Select a new available slot</option>
            {rescheduleOptions.map((slot) => (
              <option key={slot.id} value={slot.id}>
                {formatDate(slot.start_time)} - {formatDate(slot.end_time)}
              </option>
            ))}
          </Select>
          <Button size="sm" onClick={onReschedule} disabled={working || !selectedSlotId}>
            {working ? 'Rescheduling...' : 'Reschedule'}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base">Audit Trail</CardTitle></CardHeader>
        <CardContent>
          {auditEvents.length === 0 ? (
            <p className="text-sm text-muted-foreground">No audit events found.</p>
          ) : (
            <div className="space-y-2">
              {auditEvents.map((event) => (
                <div key={event.id} className="rounded border border-border px-3 py-2">
                  <p className="text-sm font-medium text-foreground">
                    {event.action} by {event.actor_username}
                  </p>
                  <p className="text-xs text-muted-foreground">{formatDate(event.created_at)}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
