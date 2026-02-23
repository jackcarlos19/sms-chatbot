import * as React from 'react'
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from '@tanstack/react-table'
import { Link, createRoute, useNavigate } from '@tanstack/react-router'
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
import { Skeleton } from '../../components/ui/Skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/Select'
import { api } from '../../api'
import type { AppointmentFull } from '../../api'

export const appointmentsIndexRoute = createRoute({
  getParentRoute: () => _authenticatedRoute,
  path: '/appointments',
  component: AppointmentsListPage,
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

const columnHelper = createColumnHelper<AppointmentFull>()

const columns = [
  columnHelper.accessor('slot_start', {
    header: 'Date / Time',
    cell: (info) => formatDate(info.getValue()),
  }),
  columnHelper.accessor((row) => row.contact_name || row.contact_phone, {
    id: 'contact',
    header: 'Contact',
    cell: (info) => {
      const row = info.row.original
      return (
        <Link
          to="/contacts/$contactId"
          params={{ contactId: row.contact_id }}
          className="font-medium text-primary hover:underline"
        >
          {row.contact_name || row.contact_phone}
        </Link>
      )
    },
  }),
  columnHelper.accessor('status', {
    header: 'Status',
    cell: (info) => (
      <Badge
        variant={info.getValue() === 'cancelled' ? 'destructive' : 'secondary'}
      >
        {info.getValue()}
      </Badge>
    ),
  }),
  columnHelper.display({
    id: 'actions',
    header: 'Actions',
    cell: (info) => (
      <Link
        to="/appointments/$appointmentId"
        params={{ appointmentId: info.row.original.id }}
        className="text-primary hover:underline"
      >
        View
      </Link>
    ),
  }),
]

const STATUS_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'pending', label: 'Pending' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'rescheduled', label: 'Rescheduled' },
  { value: 'completed', label: 'Completed' },
]

function AppointmentsListPage() {
  const navigate = useNavigate()
  const [data, setData] = React.useState<AppointmentFull[]>([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)
  const [statusFilter, setStatusFilter] = React.useState('all')

  const fetchAppointments = React.useCallback(() => {
    setLoading(true)
    setError(null)
    api
      .getAllAppointmentsFiltered({
        limit: 50,
        offset: 0,
        status: statusFilter === 'all' ? undefined : statusFilter,
      })
      .then((res) => setData(res.data))
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false))
  }, [statusFilter])

  React.useEffect(() => {
    fetchAppointments()
  }, [fetchAppointments])

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  })

  return (
    <>
      <Header title="Appointments" />
      <Main>
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Appointments</h2>
            <p className="text-muted-foreground">All appointments</p>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-4">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[180px]">
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
          <Button variant="secondary" size="sm" onClick={fetchAppointments}>
            Apply
          </Button>
        </div>

        {error && (
          <div className="mt-4 rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive">
            <p>{error}</p>
            <Button
              variant="secondary"
              size="sm"
              className="mt-2"
              onClick={fetchAppointments}
            >
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
              No appointments found.
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
                  <TableRow
                    key={row.id}
                    className="cursor-pointer"
                    onClick={() =>
                      navigate({
                        to: '/appointments/$appointmentId',
                        params: { appointmentId: row.original.id },
                      })
                    }
                  >
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

export const Route = appointmentsIndexRoute
