import * as React from 'react'
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from '@tanstack/react-table'
import { createRoute } from '@tanstack/react-router'
import { toast } from 'sonner'
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
import type { ReminderWorkflow } from '../../api'
import { reminderWorkflowCreateSchema } from '../../lib/schemas'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import type { z } from 'zod'

type WorkflowCreateForm = z.input<typeof reminderWorkflowCreateSchema>

export const workflowsRoute = createRoute({
  getParentRoute: () => _authenticatedRoute,
  path: '/workflows',
  component: WorkflowsPage,
})

const TRIGGER_OPTIONS = [
  { value: 'any', label: 'Any' },
  { value: 'appointment_scheduled', label: 'Appointment scheduled' },
  { value: 'appointment_reminder', label: 'Appointment reminder' },
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'scheduled', label: 'Scheduled' },
]

const CHANNEL_OPTIONS = [
  { value: 'sms', label: 'SMS' },
  { value: 'email', label: 'Email' },
  { value: 'voice', label: 'Voice' },
]

const columnHelper = createColumnHelper<ReminderWorkflow>()

const columns = [
  columnHelper.accessor('name', { header: 'Name', cell: (info) => info.getValue() }),
  columnHelper.accessor('appointment_status', {
    header: 'Trigger',
    cell: (info) => info.getValue() || 'Any',
  }),
  columnHelper.accessor('minutes_before', {
    header: 'Offset (min)',
    cell: (info) => info.getValue(),
  }),
  columnHelper.accessor('is_active', {
    header: 'Status',
    cell: (info) => (
      <Badge variant={info.getValue() ? 'default' : 'secondary'}>
        {info.getValue() ? 'active' : 'inactive'}
      </Badge>
    ),
  }),
]

function NewWorkflowDialog({
  onSuccess,
  onCancel,
}: {
  onSuccess: () => void
  onCancel: () => void
}) {
  const [submitting, setSubmitting] = React.useState(false)
  const [submitError, setSubmitError] = React.useState<string | null>(null)

  const form = useForm<WorkflowCreateForm>({
    resolver: zodResolver(reminderWorkflowCreateSchema),
    defaultValues: {
      name: '',
      minutes_before: 60,
      template: '',
      appointment_status: 'any',
      channel: 'sms',
    },
  })

  const onSubmit = form.handleSubmit(async (data) => {
    setSubmitting(true)
    setSubmitError(null)
    try {
      await api.createReminderWorkflow({
        name: data.name,
        minutes_before: data.minutes_before,
        template: data.template,
        appointment_status: data.appointment_status === 'any' ? undefined : data.appointment_status,
        channel: data.channel,
      })
      toast.success('Workflow created')
      onSuccess()
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : String(err))
    } finally {
      setSubmitting(false)
    }
  })

  const triggerValue = form.watch('appointment_status') ?? 'any'
  const channelValue = form.watch('channel')

  return (
    <>
      <DialogHeader>
        <DialogTitle>New workflow</DialogTitle>
        <DialogDescription>
          Create a reminder workflow. Triggers run before the appointment based on offset minutes.
        </DialogDescription>
      </DialogHeader>
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Name</label>
          <Input {...form.register('name')} placeholder="e.g. 24h reminder" />
          {form.formState.errors.name && (
            <p className="text-sm text-destructive">{form.formState.errors.name.message}</p>
          )}
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Trigger type</label>
          <Select
            value={triggerValue}
            onValueChange={(v) => form.setValue('appointment_status', v)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select trigger" />
            </SelectTrigger>
            <SelectContent>
              {TRIGGER_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Offset (minutes before)</label>
          <Input
            type="number"
            {...form.register('minutes_before', { valueAsNumber: true })}
            min={1}
          />
          {form.formState.errors.minutes_before && (
            <p className="text-sm text-destructive">
              {form.formState.errors.minutes_before.message}
            </p>
          )}
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Channel</label>
          <Select value={channelValue} onValueChange={(v) => form.setValue('channel', v as 'sms' | 'email' | 'voice')}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CHANNEL_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Message template</label>
          <Textarea {...form.register('template')} rows={4} placeholder="Hi {{name}}, your appointment…" />
          {form.formState.errors.template && (
            <p className="text-sm text-destructive">{form.formState.errors.template.message}</p>
          )}
        </div>
        {submitError && <p className="text-sm text-destructive">{submitError}</p>}
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting ? 'Creating…' : 'Create workflow'}
          </Button>
        </DialogFooter>
      </form>
    </>
  )
}

function WorkflowsPage() {
  const [data, setData] = React.useState<ReminderWorkflow[]>([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)
  const [newOpen, setNewOpen] = React.useState(false)

  const fetchWorkflows = React.useCallback(() => {
    setLoading(true)
    setError(null)
    api
      .getReminderWorkflows()
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false))
  }, [])

  React.useEffect(() => {
    fetchWorkflows()
  }, [fetchWorkflows])

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  })

  return (
    <>
      <Header title="Reminder Workflows" />
      <Main>
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Reminder Workflows</h2>
            <p className="text-muted-foreground">Automate reminders before appointments</p>
          </div>
          <Dialog open={newOpen} onOpenChange={setNewOpen}>
            <DialogTrigger asChild>
              <Button size="sm">New Workflow</Button>
            </DialogTrigger>
            <DialogContent showClose>
              <NewWorkflowDialog
                onSuccess={() => {
                  setNewOpen(false)
                  fetchWorkflows()
                }}
                onCancel={() => setNewOpen(false)}
              />
            </DialogContent>
          </Dialog>
        </div>

        {error && (
          <div className="mt-4 rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive">
            <p>{error}</p>
            <Button variant="secondary" size="sm" className="mt-2" onClick={fetchWorkflows}>
              Retry
            </Button>
          </div>
        )}

        <div className="mt-6 rounded-xl border border-border">
          {loading ? (
            <div className="space-y-2 p-4">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : data.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              No workflows yet. Create one to get started.
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

export const Route = workflowsRoute
