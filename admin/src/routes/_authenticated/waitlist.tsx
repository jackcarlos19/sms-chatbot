import * as React from 'react'
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from '@tanstack/react-table'
import { createRoute } from '@tanstack/react-router'
import { _authenticatedRoute } from '../_authenticated'
import { Header } from '../../components/layout/header'
import { Main } from '../../components/layout/main'
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
import { Input } from '../../components/ui/Input'
import { Textarea } from '../../components/ui/Textarea'
import { Skeleton } from '../../components/ui/Skeleton'
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
import { api } from '../../api'
import type { WaitlistEntry, Contact } from '../../api'
import { waitlistCreateSchema } from '../../lib/schemas'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import type { z } from 'zod'

type WaitlistCreateForm = z.infer<typeof waitlistCreateSchema>

export const waitlistRoute = createRoute({
  getParentRoute: () => _authenticatedRoute,
  path: '/waitlist',
  component: WaitlistPage,
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

/** Convert datetime-local value to ISO string */
function toISOFromDatetimeLocal(value: string): string | undefined {
  if (!value) return undefined
  try {
    return new Date(value).toISOString()
  } catch {
    return undefined
  }
}

/** Get datetime-local string from ISO for input value */
function toDatetimeLocalValue(iso: string | undefined): string {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const h = String(d.getHours()).padStart(2, '0')
    const min = String(d.getMinutes()).padStart(2, '0')
    return `${y}-${m}-${day}T${h}:${min}`
  } catch {
    return ''
  }
}

const STATUS_OPTIONS = [
  { value: 'open', label: 'Open' },
  { value: 'notified', label: 'Notified' },
  { value: 'closed', label: 'Closed' },
]

const columnHelper = createColumnHelper<WaitlistEntry>()

const columns = [
  columnHelper.accessor(
    (row) => row.contact_name || row.contact_phone,
    {
      id: 'contact',
      header: 'Contact Name / Phone',
      cell: (info) => info.getValue(),
    }
  ),
  columnHelper.accessor(
    (row) => {
      const parts: string[] = []
      if (row.desired_start) parts.push(formatDate(row.desired_start))
      if (row.desired_end) parts.push(formatDate(row.desired_end))
      return parts.length ? parts.join(' – ') : '—'
    },
    {
      id: 'timeframe',
      header: 'Requested Timeframe',
      cell: (info) => info.getValue(),
    }
  ),
  columnHelper.accessor('status', {
    header: 'Status',
    cell: (info) => {
      const v = info.getValue()
      const variant =
        v === 'open' ? 'secondary' : v === 'notified' ? 'success' : 'destructive'
      return <Badge variant={variant}>{v}</Badge>
    },
  }),
  columnHelper.accessor('created_at', {
    header: 'Added Date',
    cell: (info) => formatDate(info.getValue()),
  }),
]

function WaitlistPage() {
  const [data, setData] = React.useState<WaitlistEntry[]>([])
  const [contacts, setContacts] = React.useState<Contact[]>([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)
  const [statusFilter, setStatusFilter] = React.useState('open')
  const [newEntryOpen, setNewEntryOpen] = React.useState(false)

  const fetchWaitlist = React.useCallback(() => {
    setLoading(true)
    setError(null)
    api
      .getWaitlist(statusFilter)
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false))
  }, [statusFilter])

  React.useEffect(() => {
    fetchWaitlist()
  }, [fetchWaitlist])

  React.useEffect(() => {
    if (newEntryOpen) {
      api.getContacts(100, 0, '', '').then((res) => setContacts(res.data)).catch(() => setContacts([]))
    }
  }, [newEntryOpen])

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  })

  return (
    <>
      <Header title="Waitlist" />
      <Main>
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Waitlist</h2>
            <p className="text-muted-foreground">Manage waitlist entries</p>
          </div>
          <Dialog open={newEntryOpen} onOpenChange={setNewEntryOpen}>
            <DialogTrigger asChild>
              <Button size="sm">New Entry</Button>
            </DialogTrigger>
            <DialogContent showClose>
              <NewWaitlistEntryDialog
                contacts={contacts}
                onSuccess={() => {
                  setNewEntryOpen(false)
                  fetchWaitlist()
                }}
                onCancel={() => setNewEntryOpen(false)}
              />
            </DialogContent>
          </Dialog>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-4">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              {STATUS_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="secondary" size="sm" onClick={fetchWaitlist}>
            Apply
          </Button>
        </div>

        {error && (
          <div className="mt-4 rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive">
            <p>{error}</p>
            <Button variant="secondary" size="sm" className="mt-2" onClick={fetchWaitlist}>
              Retry
            </Button>
          </div>
        )}

        <div className="mt-6 rounded-xl border border-border">
          {loading ? (
            <div className="space-y-2 p-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : data.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              No waitlist entries found.
            </div>
          ) : (
            <Table>
              <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => (
                  <TableRow key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <TableHead key={header.id}>
                        {header.isPlaceholder
                          ? null
                          : flexRender(
                              header.column.columnDef.header,
                              header.getContext()
                            )}
                      </TableHead>
                    ))}
                  </TableRow>
                ))}
              </TableHeader>
              <TableBody>
                {table.getRowModel().rows.map((row) => (
                  <TableRow key={row.id}>
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id}>
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext()
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>
      </Main>
    </>
  )
}

function NewWaitlistEntryDialog({
  contacts,
  onSuccess,
  onCancel,
}: {
  contacts: Contact[]
  onSuccess: () => void
  onCancel: () => void
}) {
  const [submitting, setSubmitting] = React.useState(false)
  const [submitError, setSubmitError] = React.useState<string | null>(null)

  const form = useForm<WaitlistCreateForm>({
    resolver: zodResolver(waitlistCreateSchema),
    defaultValues: {
      contact_id: '',
      desired_start: undefined,
      desired_end: undefined,
      notes: '',
    },
  })

  const onSubmit = form.handleSubmit(async (data) => {
    setSubmitting(true)
    setSubmitError(null)
    try {
      await api.createWaitlist({
        contact_id: data.contact_id,
        desired_start: data.desired_start,
        desired_end: data.desired_end,
        notes: data.notes || undefined,
      })
      onSuccess()
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : String(err))
    } finally {
      setSubmitting(false)
    }
  })

  const contactValue = form.watch('contact_id')

  return (
    <>
      <DialogHeader>
        <DialogTitle>New waitlist entry</DialogTitle>
        <DialogDescription>
          Add a contact to the waitlist with optional desired timeframe.
        </DialogDescription>
      </DialogHeader>
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Contact</label>
          <Select
            value={contactValue}
            onValueChange={(v) => form.setValue('contact_id', v)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select contact" />
            </SelectTrigger>
            <SelectContent>
              {contacts.map((c) => (
                <SelectItem key={c.id} value={c.id}>
                  {c.first_name || c.last_name
                    ? [c.first_name, c.last_name].filter(Boolean).join(' ')
                    : c.phone_number}
                  {c.phone_number ? ` (${c.phone_number})` : ''}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {form.formState.errors.contact_id && (
            <p className="text-sm text-destructive">
              {form.formState.errors.contact_id.message}
            </p>
          )}
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Desired start (optional)</label>
          <Input
            type="datetime-local"
            value={toDatetimeLocalValue(form.watch('desired_start'))}
            onChange={(e) => {
              form.setValue('desired_start', toISOFromDatetimeLocal(e.target.value))
            }}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Desired end (optional)</label>
          <Input
            type="datetime-local"
            value={toDatetimeLocalValue(form.watch('desired_end'))}
            onChange={(e) => {
              form.setValue('desired_end', toISOFromDatetimeLocal(e.target.value))
            }}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Notes (optional)</label>
          <Textarea {...form.register('notes')} rows={3} placeholder="Notes…" />
        </div>
        {submitError && <p className="text-sm text-destructive">{submitError}</p>}
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting ? 'Adding…' : 'Add entry'}
          </Button>
        </DialogFooter>
      </form>
    </>
  )
}

export const Route = waitlistRoute
