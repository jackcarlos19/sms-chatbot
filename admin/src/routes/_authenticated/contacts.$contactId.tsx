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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/Tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/Table'
import { Skeleton } from '../../components/ui/Skeleton'
import { api } from '../../api'
import type { ContactDetail, Message, Appointment } from '../../api'
import { contactPatchSchema } from '../../lib/schemas'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import type { z } from 'zod'

type ContactPatchForm = z.infer<typeof contactPatchSchema>

export const contactsContactIdRoute = createRoute({
  getParentRoute: () => _authenticatedRoute,
  path: '/contacts/$contactId',
  component: ContactDetailPage,
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

function ContactDetailPage() {
  const { contactId } = useParams({ strict: false })
  const [contact, setContact] = React.useState<ContactDetail | null>(null)
  const [messages, setMessages] = React.useState<Message[]>([])
  const [appointments, setAppointments] = React.useState<Appointment[]>([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)
  const [editOpen, setEditOpen] = React.useState(false)

  const fetchContact = React.useCallback(() => {
    if (!contactId) return
    setLoading(true)
    setError(null)
    api
      .getContact(contactId)
      .then((c) => setContact(c))
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false))
  }, [contactId])

  React.useEffect(() => {
    fetchContact()
  }, [fetchContact])

  React.useEffect(() => {
    if (!contactId) return
    api.getMessages(contactId).then(setMessages).catch(() => setMessages([]))
    api.getContactAppointments(contactId).then(setAppointments).catch(() => setAppointments([]))
  }, [contactId])

  const displayName =
    contact?.first_name || contact?.last_name
      ? [contact.first_name, contact.last_name].filter(Boolean).join(' ')
      : contact?.phone_number ?? 'Contact'

  return (
    <>
      <Header
        title={loading ? '…' : displayName}
        backTo="/contacts"
        backLabel="Contacts"
      />
      <Main>
        {error && (
          <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive">
            <p>{error}</p>
            <Button variant="secondary" size="sm" onClick={fetchContact}>
              Retry
            </Button>
          </div>
        )}

        {loading && !contact ? (
          <Skeleton className="h-48 w-full" />
        ) : contact ? (
          <>
            {/* Contact profile card + Edit dialog */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0">
                <div>
                  <CardTitle>Contact profile</CardTitle>
                  <CardDescription>Phone, timezone, opt-in status</CardDescription>
                </div>
                <Dialog open={editOpen} onOpenChange={setEditOpen}>
                  <DialogTrigger asChild>
                    <Button variant="secondary" size="sm">
                      Edit
                    </Button>
                  </DialogTrigger>
                  <DialogContent showClose>
                    <EditContactDialog
                      contact={contact}
                      onSuccess={() => {
                        setEditOpen(false)
                        fetchContact()
                      }}
                      onCancel={() => setEditOpen(false)}
                    />
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-sm">
                  <span className="font-medium text-muted-foreground">Phone:</span>{' '}
                  {contact.phone_number}
                </p>
                <p className="text-sm">
                  <span className="font-medium text-muted-foreground">Timezone:</span>{' '}
                  {contact.timezone}
                </p>
                <p className="text-sm">
                  <span className="font-medium text-muted-foreground">Opt-in status:</span>{' '}
                  <Badge
                    variant={
                      contact.opt_in_status === 'opted_in'
                        ? 'success'
                        : contact.opt_in_status === 'opted_out'
                          ? 'destructive'
                          : 'secondary'
                    }
                  >
                    {contact.opt_in_status}
                  </Badge>
                </p>
              </CardContent>
            </Card>

            {/* Tabs: Conversations, Appointments */}
            <Tabs defaultValue="conversations" className="mt-6">
              <TabsList>
                <TabsTrigger value="conversations">Conversations</TabsTrigger>
                <TabsTrigger value="appointments">Appointments</TabsTrigger>
              </TabsList>
              <TabsContent value="conversations" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Recent messages</CardTitle>
                    <CardDescription>Message history with this contact</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {messages.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No messages yet.</p>
                    ) : (
                      <div className="space-y-3">
                        {messages.map((m) => (
                          <div
                            key={m.id}
                            className={`rounded-lg border p-3 text-sm ${
                              m.direction === 'inbound'
                                ? 'mr-8 border-border bg-muted/50'
                                : 'ml-8 border-primary/20 bg-primary/5'
                            }`}
                          >
                            <div className="flex items-center justify-between gap-2 text-xs text-muted-foreground">
                              <span>{m.direction}</span>
                              <span>{formatDate(m.created_at)}</span>
                            </div>
                            <p className="mt-1">{m.body}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
              <TabsContent value="appointments" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Appointments</CardTitle>
                    <CardDescription>Upcoming and past slots</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {appointments.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No appointments.</p>
                    ) : (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Status</TableHead>
                            <TableHead>Booked</TableHead>
                            <TableHead>Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {appointments.map((a) => (
                            <TableRow key={a.id}>
                              <TableCell>
                                <Badge
                                  variant={
                                    a.status === 'cancelled' ? 'destructive' : 'secondary'
                                  }
                                >
                                  {a.status}
                                </Badge>
                              </TableCell>
                              <TableCell className="text-muted-foreground">
                                {formatDate(a.booked_at)}
                              </TableCell>
                              <TableCell>
                                <Link
                                  to="/appointments/$appointmentId"
                                  params={{ appointmentId: a.id }}
                                  className="text-primary hover:underline"
                                >
                                  View
                                </Link>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </>
        ) : null}
      </Main>
    </>
  )
}

function EditContactDialog({
  contact,
  onSuccess,
  onCancel,
}: {
  contact: ContactDetail
  onSuccess: () => void
  onCancel: () => void
}) {
  const [submitting, setSubmitting] = React.useState(false)
  const [submitError, setSubmitError] = React.useState<string | null>(null)

  const form = useForm<ContactPatchForm>({
    resolver: zodResolver(contactPatchSchema),
    defaultValues: {
      first_name: contact.first_name ?? '',
      last_name: contact.last_name ?? '',
      timezone: contact.timezone,
      opt_in_status: contact.opt_in_status as 'opted_in' | 'opted_out' | 'pending',
    },
  })

  const onSubmit = form.handleSubmit(async (data) => {
    setSubmitting(true)
    setSubmitError(null)
    try {
      await api.updateContact(contact.id, {
        first_name: data.first_name || null,
        last_name: data.last_name || null,
        timezone: data.timezone,
        opt_in_status: data.opt_in_status,
      })
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
        <DialogTitle>Edit contact</DialogTitle>
        <DialogDescription>Update name, timezone, and opt-in status.</DialogDescription>
      </DialogHeader>
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">First name</label>
          <Input {...form.register('first_name')} />
          {form.formState.errors.first_name && (
            <p className="text-sm text-destructive">
              {form.formState.errors.first_name.message}
            </p>
          )}
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Last name</label>
          <Input {...form.register('last_name')} />
          {form.formState.errors.last_name && (
            <p className="text-sm text-destructive">
              {form.formState.errors.last_name.message}
            </p>
          )}
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Timezone</label>
          <Input {...form.register('timezone')} />
          {form.formState.errors.timezone && (
            <p className="text-sm text-destructive">
              {form.formState.errors.timezone.message}
            </p>
          )}
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Opt-in status</label>
          <Select
            value={form.watch('opt_in_status')}
            onValueChange={(v) =>
              form.setValue('opt_in_status', v as 'opted_in' | 'opted_out' | 'pending')
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="opted_in">Opted in</SelectItem>
              <SelectItem value="opted_out">Opted out</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {submitError && (
          <p className="text-sm text-destructive">{submitError}</p>
        )}
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting ? 'Saving…' : 'Save'}
          </Button>
        </DialogFooter>
      </form>
    </>
  )
}

export const Route = contactsContactIdRoute
