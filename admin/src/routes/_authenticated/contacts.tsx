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
import { Input } from '../../components/ui/Input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/Select'
import { Button } from '../../components/ui/Button'
import { Skeleton } from '../../components/ui/Skeleton'
import { api } from '../../api'
import type { Contact } from '../../api'

export const contactsRoute = createRoute({
  getParentRoute: () => _authenticatedRoute,
  path: '/contacts',
  component: ContactsPage,
})

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: 'short',
    })
  } catch {
    return iso
  }
}

const columnHelper = createColumnHelper<Contact>()

const columns = [
  columnHelper.accessor('phone_number', {
    header: 'Phone',
    cell: (info) => {
      const contact = info.row.original
      return (
        <Link
          to="/contacts/$contactId"
          params={{ contactId: contact.id }}
          className="font-medium text-primary hover:underline"
        >
          {info.getValue()}
        </Link>
      )
    },
  }),
  columnHelper.accessor(
    (row) =>
      [row.first_name, row.last_name].filter(Boolean).join(' ') || '—',
    {
      id: 'name',
      header: 'Name',
      cell: (info) => info.getValue(),
    }
  ),
  columnHelper.accessor('timezone', {
    header: 'Timezone',
    cell: (info) => info.getValue(),
  }),
  columnHelper.accessor('opt_in_status', {
    header: 'Opt-in status',
    cell: (info) => {
      const v = info.getValue()
      const variant =
        v === 'opted_in'
          ? 'success'
          : v === 'opted_out'
            ? 'destructive'
            : 'secondary'
      return <Badge variant={variant}>{v}</Badge>
    },
  }),
  columnHelper.accessor('created_at', {
    header: 'Created',
    cell: (info) => formatDate(info.getValue()),
  }),
]

function ContactsPage() {
  const navigate = useNavigate()
  const [data, setData] = React.useState<Contact[]>([])
  const [total, setTotal] = React.useState(0)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)
  const [search, setSearch] = React.useState('')
  const [statusFilter, setStatusFilter] = React.useState('all')
  const [limit] = React.useState(50)
  const [offset] = React.useState(0)

  const fetchContacts = React.useCallback(() => {
    setLoading(true)
    setError(null)
    api
      .getContacts(limit, offset, search, statusFilter === 'all' ? '' : statusFilter)
      .then((res) => {
        setData(res.data)
        setTotal(res.total)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : String(err))
      })
      .finally(() => setLoading(false))
  }, [limit, offset, search, statusFilter])

  React.useEffect(() => {
    fetchContacts()
  }, [fetchContacts])

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  })

  return (
    <>
      <Header title="Contacts" />
      <Main>
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Contacts</h2>
            <p className="text-muted-foreground">
              Search and filter contacts
            </p>
          </div>
        </div>

        {/* Toolbar */}
        <div className="mt-6 flex flex-wrap items-center gap-4">
          <Input
            placeholder="Search by phone or name"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-xs"
          />
          <Select
            value={statusFilter}
            onValueChange={(v) => setStatusFilter(v)}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="opted_in">Opted in</SelectItem>
              <SelectItem value="opted_out">Opted out</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="secondary" size="sm" onClick={fetchContacts}>
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
              onClick={fetchContacts}
            >
              Retry
            </Button>
          </div>
        )}

        <div className="mt-4 rounded-xl border border-border">
          {loading ? (
            <div className="space-y-2 p-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : data.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              No contacts found.
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
                    onClick={() => navigate({ to: '/contacts/$contactId', params: { contactId: row.original.id } })}
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

        {!loading && total > 0 && (
          <p className="mt-2 text-sm text-muted-foreground">
            Showing {data.length} of {total} contacts
          </p>
        )}
      </Main>
    </>
  )
}

export const Route = contactsRoute
