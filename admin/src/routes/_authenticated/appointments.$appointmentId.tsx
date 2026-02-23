import * as React from 'react'
import { createRoute, Link, useParams } from '@tanstack/react-router'
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
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { Textarea } from '../../components/ui/Textarea'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../../components/ui/Dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/Select'
import { Skeleton } from '../../components/ui/Skeleton'
import { api } from '../../api'
import type { AppointmentDetail as AppointmentDetailType, Slot, AuditEvent } from '../../api'
import { appointmentCancelSchema, appointmentRescheduleSchema, appointmentNotesSchema } from '../../lib/schemas'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import type { z } from 'zod'

type CancelForm = z.infer<typeof appointmentCancelSchema>
type RescheduleForm = z.infer<typeof appointmentRescheduleSchema>
type NotesForm = z.infer<typeof appointmentNotesSchema>

export const appointmentsAppointmentIdRoute = createRoute({
  getParentRoute: () => _authenticatedRoute,
  path: '/appointments/$appointmentId',
  component: AppointmentDetailPage,
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

function AppointmentDetailPage() {
  const params = useParams({ strict: false })
  const appointmentId = params.appointmentId as string
  const [appointment, setAppointment] = React.useState<AppointmentDetailType | null>(null)
  const [slots, setSlots] = React.useState<Slot[]>([])
  const [auditEvents, setAuditEvents] = React.useState<AuditEvent[]>([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)
  const [cancelOpen, setCancelOpen] = React.useState(false)
  const [rescheduleOpen, setRescheduleOpen] = React.useState(false)

  const fetchAppointment = React.useCallback(() => {
    if (!appointmentId) return
    setLoading(true)
    setError(null)
    api
      .getAppointment(appointmentId)
      .then(setAppointment)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false))
  }, [appointmentId])

  React.useEffect(() => {
    fetchAppointment()
  }, [fetchAppointment])

  React.useEffect(() => {
    api.getSlots(14).then(setSlots).catch(() => setSlots([]))
  }, [])

  const fetchAudit = React.useCallback(() => {
    if (!appointmentId) return
    api
      .getAuditEvents('appointment', appointmentId)
      .then(setAuditEvents)
      .catch(() => setAuditEvents([]))
  }, [appointmentId])

  React.useEffect(() => {
    fetchAudit()
  }, [fetchAudit])

  const title = appointment
    ? `${appointment.contact_name || appointment.contact_phone} – ${formatDate(appointment.slot_start)}`
    : 'Appointment'

  const isCancelled = appointment?.status === 'cancelled'

  return (
    <>
      <Header
        title={loading ? '…' : title}
        backTo="/appointments"
        backLabel="Appointments"
      />
      <Main>
        {error && (
          <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive">
            <p>{error}</p>
            <Button variant="secondary" size="sm" onClick={fetchAppointment}>
              Retry
            </Button>
          </div>
        )}

        {loading && !appointment ? (
          <Skeleton className="h-48 w-full" />
        ) : appointment ? (
          <>
            <Card>
              <CardHeader>
                <CardTitle>Appointment details</CardTitle>
                <CardDescription>Slot, contact, status</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-sm">
                  <span className="font-medium text-muted-foreground">Status:</span>{' '}
                  <Badge
                    variant={
                      appointment.status === 'cancelled' ? 'destructive' : 'secondary'
                    }
                  >
                    {appointment.status}
                  </Badge>
                </p>
                <p className="text-sm">
                  <span className="font-medium text-muted-foreground">Contact:</span>{' '}
                  <Link
                    to="/contacts/$contactId"
                    params={{ contactId: appointment.contact_id }}
                    className="text-primary hover:underline"
                  >
                    {appointment.contact_name || appointment.contact_phone}
                  </Link>
                </p>
                <p className="text-sm">
                  <span className="font-medium text-muted-foreground">Phone:</span>{' '}
                  {appointment.contact_phone}
                </p>
                <p className="text-sm">
                  <span className="font-medium text-muted-foreground">Slot:</span>{' '}
                  {formatDate(appointment.slot_start)} – {formatDate(appointment.slot_end)}
                </p>
                <p className="text-sm">
                  <span className="font-medium text-muted-foreground">Booked:</span>{' '}
                  {formatDate(appointment.booked_at)}
                </p>
                {appointment.cancelled_at && (
                  <p className="text-sm">
                    <span className="font-medium text-muted-foreground">Cancelled:</span>{' '}
                    {formatDate(appointment.cancelled_at)}
                    {appointment.cancellation_reason && (
                      <> – {appointment.cancellation_reason}</>
                    )}
                  </p>
                )}
                {appointment.notes && (
                  <p className="text-sm">
                    <span className="font-medium text-muted-foreground">Notes:</span>{' '}
                    {appointment.notes}
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Internal Notes */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle>Internal notes</CardTitle>
                <CardDescription>Private notes for this appointment</CardDescription>
              </CardHeader>
              <CardContent>
                <InternalNotesForm
                  appointmentId={appointmentId}
                  initialNotes={appointment.notes ?? ''}
                  onSuccess={() => {
                    fetchAppointment()
                    fetchAudit()
                  }}
                />
              </CardContent>
            </Card>

            {/* Audit Trail */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle>Audit Trail</CardTitle>
                <CardDescription>History of actions on this appointment</CardDescription>
              </CardHeader>
              <CardContent>
                {auditEvents.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No audit events yet.</p>
                ) : (
                  <ul className="space-y-3">
                    {auditEvents.map((event) => (
                      <li
                        key={event.id}
                        className="flex flex-wrap items-baseline gap-x-2 gap-y-1 border-l-2 border-border pl-3 py-1"
                      >
                        <span className="font-medium">{event.action}</span>
                        <span className="text-muted-foreground text-sm">
                          {event.actor_username}
                        </span>
                        <span className="text-muted-foreground text-xs">
                          {formatDate(event.created_at)}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            {!isCancelled && (
              <div className="mt-6 flex gap-2">
                <Dialog open={rescheduleOpen} onOpenChange={setRescheduleOpen}>
                  <DialogTrigger asChild>
                    <Button variant="secondary" size="sm">
                      Reschedule
                    </Button>
                  </DialogTrigger>
                  <DialogContent showClose>
                    <RescheduleDialog
                      appointmentId={appointmentId}
                      slots={slots}
                      onSuccess={() => {
                        setRescheduleOpen(false)
                        fetchAppointment()
                        fetchAudit()
                      }}
                      onCancel={() => setRescheduleOpen(false)}
                    />
                  </DialogContent>
                </Dialog>
                <Dialog open={cancelOpen} onOpenChange={setCancelOpen}>
                  <DialogTrigger asChild>
                    <Button variant="danger" size="sm">
                      Cancel appointment
                    </Button>
                  </DialogTrigger>
                  <DialogContent showClose>
                    <CancelDialog
                      appointmentId={appointmentId}
                      onSuccess={() => {
                        setCancelOpen(false)
                        fetchAppointment()
                        fetchAudit()
                      }}
                      onCancel={() => setCancelOpen(false)}
                    />
                  </DialogContent>
                </Dialog>
              </div>
            )}
          </>
        ) : null}
      </Main>
    </>
  )
}

function InternalNotesForm({
  appointmentId,
  initialNotes,
  onSuccess,
}: {
  appointmentId: string
  initialNotes: string
  onSuccess: () => void
}) {
  const [submitting, setSubmitting] = React.useState(false)
  const [submitError, setSubmitError] = React.useState<string | null>(null)

  const form = useForm<NotesForm>({
    resolver: zodResolver(appointmentNotesSchema),
    defaultValues: { notes: initialNotes },
  })

  React.useEffect(() => {
    form.reset({ notes: initialNotes })
  }, [initialNotes, form])

  const onSubmit = form.handleSubmit(async (data) => {
    setSubmitting(true)
    setSubmitError(null)
    try {
      await api.updateAppointmentNotes(appointmentId, data.notes)
      onSuccess()
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : String(err))
    } finally {
      setSubmitting(false)
    }
  })

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <Textarea
        {...form.register('notes')}
        placeholder="Add internal notes…"
        rows={4}
      />
      {form.formState.errors.notes && (
        <p className="text-sm text-destructive">
          {form.formState.errors.notes.message}
        </p>
      )}
      {submitError && <p className="text-sm text-destructive">{submitError}</p>}
      <Button type="submit" disabled={submitting}>
        {submitting ? 'Saving…' : 'Save notes'}
      </Button>
    </form>
  )
}

function CancelDialog({
  appointmentId,
  onSuccess,
  onCancel,
}: {
  appointmentId: string
  onSuccess: () => void
  onCancel: () => void
}) {
  const [submitting, setSubmitting] = React.useState(false)
  const [submitError, setSubmitError] = React.useState<string | null>(null)

  const form = useForm<CancelForm>({
    resolver: zodResolver(appointmentCancelSchema),
    defaultValues: { reason: '' },
  })

  const onSubmit = form.handleSubmit(async (data) => {
    setSubmitting(true)
    setSubmitError(null)
    try {
      await api.cancelAppointment(appointmentId, data.reason)
      onSuccess()
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : String(err))
    } finally {
      setSubmitting(false)
    }
  })

  return (
    <>
      <DialogHeader>
        <DialogTitle>Cancel appointment</DialogTitle>
        <DialogDescription>
          Provide a reason for cancellation. This action cannot be undone.
        </DialogDescription>
      </DialogHeader>
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Reason</label>
          <Input {...form.register('reason')} placeholder="Reason for cancellation" />
          {form.formState.errors.reason && (
            <p className="text-sm text-destructive">
              {form.formState.errors.reason.message}
            </p>
          )}
        </div>
        {submitError && <p className="text-sm text-destructive">{submitError}</p>}
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onCancel}>
            Back
          </Button>
          <Button type="submit" variant="danger" disabled={submitting}>
            {submitting ? 'Cancelling…' : 'Cancel appointment'}
          </Button>
        </DialogFooter>
      </form>
    </>
  )
}

function RescheduleDialog({
  appointmentId,
  slots,
  onSuccess,
  onCancel,
}: {
  appointmentId: string
  slots: Slot[]
  onSuccess: () => void
  onCancel: () => void
}) {
  const [submitting, setSubmitting] = React.useState(false)
  const [submitError, setSubmitError] = React.useState<string | null>(null)

  const availableSlots = slots.filter((s) => s.is_available)

  const form = useForm<RescheduleForm>({
    resolver: zodResolver(appointmentRescheduleSchema),
    defaultValues: { new_slot_id: '' },
  })

  const onSubmit = form.handleSubmit(async (data) => {
    setSubmitting(true)
    setSubmitError(null)
    try {
      await api.rescheduleAppointment(appointmentId, data.new_slot_id)
      onSuccess()
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : String(err))
    } finally {
      setSubmitting(false)
    }
  })

  return (
    <>
      <DialogHeader>
        <DialogTitle>Reschedule appointment</DialogTitle>
        <DialogDescription>
          Choose a new slot. Only available slots are shown.
        </DialogDescription>
      </DialogHeader>
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">New slot</label>
          <Select
            value={form.watch('new_slot_id')}
            onValueChange={(v) => form.setValue('new_slot_id', v)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select slot" />
            </SelectTrigger>
            <SelectContent>
              {availableSlots.map((s) => (
                <SelectItem key={s.id} value={s.id}>
                  {formatDate(s.start_time)} – {formatDate(s.end_time)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {form.formState.errors.new_slot_id && (
            <p className="text-sm text-destructive">
              {form.formState.errors.new_slot_id.message}
            </p>
          )}
        </div>
        {submitError && <p className="text-sm text-destructive">{submitError}</p>}
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onCancel}>
            Back
          </Button>
          <Button type="submit" disabled={submitting || availableSlots.length === 0}>
            {submitting ? 'Rescheduling…' : 'Reschedule'}
          </Button>
        </DialogFooter>
      </form>
    </>
  )
}

export const Route = appointmentsAppointmentIdRoute
