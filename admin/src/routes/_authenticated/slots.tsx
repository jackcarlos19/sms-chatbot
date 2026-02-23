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
import { Skeleton } from '../../components/ui/Skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/Select'
import { api } from '../../api'
import type { Slot } from '../../api'

export const slotsRoute = createRoute({
  getParentRoute: () => _authenticatedRoute,
  path: '/slots',
  component: SlotsPage,
})

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, { dateStyle: 'short' })
  } catch {
    return iso
  }
}

function formatTime(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      timeStyle: 'short',
    })
  } catch {
    return iso
  }
}

function durationMinutes(start: string, end: string): number {
  try {
    const a = new Date(start).getTime()
    const b = new Date(end).getTime()
    return Math.round((b - a) / 60000)
  } catch {
    return 0
  }
}

const DAYS_AHEAD_OPTIONS = [
  { value: 7, label: 'Next 7 Days' },
  { value: 14, label: 'Next 14 Days' },
  { value: 30, label: 'Next 30 Days' },
]

const columnHelper = createColumnHelper<Slot>()

const columns = [
  columnHelper.accessor('start_time', {
    header: 'Date',
    cell: (info) => formatDate(info.getValue()),
  }),
  columnHelper.accessor('start_time', {
    id: 'time',
    header: 'Time',
    cell: (info) => formatTime(info.getValue()),
  }),
  columnHelper.accessor(
    (row) => durationMinutes(row.start_time, row.end_time),
    {
      id: 'duration',
      header: 'Duration',
      cell: (info) => `${info.getValue()} min`,
    }
  ),
  columnHelper.accessor('is_available', {
    header: 'Status',
    cell: (info) => (
      <Badge variant={info.getValue() ? 'success' : 'secondary'}>
        {info.getValue() ? 'Available' : 'Unavailable'}
      </Badge>
    ),
  }),
  columnHelper.accessor('slot_type', {
    header: 'Type',
    cell: (info) => info.getValue() || '—',
  }),
]

function SlotsPage() {
  const [data, setData] = React.useState<Slot[]>([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)
  const [daysAhead, setDaysAhead] = React.useState(14)

  const fetchSlots = React.useCallback(() => {
    setLoading(true)
    setError(null)
    api
      .getSlots(daysAhead)
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false))
  }, [daysAhead])

  React.useEffect(() => {
    fetchSlots()
  }, [fetchSlots])

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  })

  return (
    <>
      <Header title="Slot Inventory" />
      <Main>
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Slot Inventory</h2>
            <p className="text-muted-foreground">Available slots for scheduling</p>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-4">
          <Select
            value={String(daysAhead)}
            onValueChange={(v) => setDaysAhead(Number(v))}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Time range" />
            </SelectTrigger>
            <SelectContent>
              {DAYS_AHEAD_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={String(opt.value)}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="secondary" size="sm" onClick={fetchSlots}>
            Apply
          </Button>
        </div>

        {error && (
          <div className="mt-4 rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive">
            <p>{error}</p>
            <Button variant="secondary" size="sm" className="mt-2" onClick={fetchSlots}>
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
              No slots found.
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

export const Route = slotsRoute
