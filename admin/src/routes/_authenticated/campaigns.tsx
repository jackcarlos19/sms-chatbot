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
import { api } from '../../api'
import type { Campaign } from '../../api'
import { campaignCreateSchema } from '../../lib/schemas'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import type { z } from 'zod'

type CampaignCreateForm = z.infer<typeof campaignCreateSchema>

export const campaignsRoute = createRoute({
  getParentRoute: () => _authenticatedRoute,
  path: '/campaigns',
  component: CampaignsPage,
})

function formatDate(iso: string | null) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: 'short',
      timeStyle: 'short',
    })
  } catch {
    return iso
  }
}

const columnHelper = createColumnHelper<Campaign>()

const columns = [
  columnHelper.accessor('name', { header: 'Name', cell: (info) => info.getValue() }),
  columnHelper.accessor('total_recipients', {
    header: 'Target',
    cell: (info) => (info.getValue() != null ? String(info.getValue()) : '—'),
  }),
  columnHelper.accessor('scheduled_at', {
    header: 'Scheduled for',
    cell: (info) => formatDate(info.getValue()),
  }),
  columnHelper.accessor('status', {
    header: 'Status',
    cell: (info) => <Badge variant="secondary">{info.getValue()}</Badge>,
  }),
  columnHelper.accessor(
    (row) => `${row.sent_count ?? 0} / ${row.total_recipients ?? 0}`,
    { id: 'sent_total', header: 'Sent / Total', cell: (info) => info.getValue() }
  ),
]

function NewCampaignDialog({
  onSuccess,
  onCancel,
}: {
  onSuccess: () => void
  onCancel: () => void
}) {
  const [submitting, setSubmitting] = React.useState(false)
  const [submitError, setSubmitError] = React.useState<string | null>(null)

  const form = useForm<CampaignCreateForm>({
    resolver: zodResolver(campaignCreateSchema),
    defaultValues: {
      name: '',
      message_template: '',
      recipient_filter: undefined,
    },
  })

  const onSubmit = form.handleSubmit(async (data) => {
    setSubmitting(true)
    setSubmitError(null)
    try {
      await api.createCampaign({
        name: data.name,
        message_template: data.message_template,
        recipient_filter: data.recipient_filter ?? {},
      })
      toast.success('Campaign created')
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
        <DialogTitle>New campaign</DialogTitle>
        <DialogDescription>
          Create a broadcast campaign. You can schedule and set the target audience after creation.
        </DialogDescription>
      </DialogHeader>
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Name</label>
          <Input {...form.register('name')} placeholder="e.g. Summer promo" />
          {form.formState.errors.name && (
            <p className="text-sm text-destructive">{form.formState.errors.name.message}</p>
          )}
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Message</label>
          <Textarea
            {...form.register('message_template')}
            rows={5}
            placeholder="Your message with optional {{placeholders}}…"
          />
          {form.formState.errors.message_template && (
            <p className="text-sm text-destructive">
              {form.formState.errors.message_template.message}
            </p>
          )}
        </div>
        {submitError && <p className="text-sm text-destructive">{submitError}</p>}
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting ? 'Creating…' : 'Create campaign'}
          </Button>
        </DialogFooter>
      </form>
    </>
  )
}

function CampaignsPage() {
  const [data, setData] = React.useState<Campaign[]>([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)
  const [newOpen, setNewOpen] = React.useState(false)

  const fetchCampaigns = React.useCallback(() => {
    setLoading(true)
    setError(null)
    api
      .getCampaigns(50, 0)
      .then((res) => setData(res.data ?? []))
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false))
  }, [])

  React.useEffect(() => {
    fetchCampaigns()
  }, [fetchCampaigns])

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  })

  return (
    <>
      <Header title="Broadcast Campaigns" />
      <Main>
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Broadcast Campaigns</h2>
            <p className="text-muted-foreground">Create and manage broadcast campaigns</p>
          </div>
          <Dialog open={newOpen} onOpenChange={setNewOpen}>
            <DialogTrigger asChild>
              <Button size="sm">New Campaign</Button>
            </DialogTrigger>
            <DialogContent showClose>
              <NewCampaignDialog
                onSuccess={() => {
                  setNewOpen(false)
                  fetchCampaigns()
                }}
                onCancel={() => setNewOpen(false)}
              />
            </DialogContent>
          </Dialog>
        </div>

        {error && (
          <div className="mt-4 rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive">
            <p>{error}</p>
            <Button variant="secondary" size="sm" className="mt-2" onClick={fetchCampaigns}>
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
              No campaigns yet. Create one to get started.
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

export const Route = campaignsRoute
