import * as React from 'react'
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from '@tanstack/react-table'
import { createRoute, useNavigate } from '@tanstack/react-router'
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
import { api } from '../../api'
import type { Conversation } from '../../api'

export const conversationsRoute = createRoute({
  getParentRoute: () => _authenticatedRoute,
  path: '/conversations',
  component: ConversationsPage,
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

const columnHelper = createColumnHelper<Conversation>()

const columns = [
  columnHelper.accessor(
    (row) => row.contact_name || row.contact_phone,
    {
      id: 'contact',
      header: 'Contact (Name / Phone)',
      cell: (info) => info.getValue(),
    }
  ),
  columnHelper.accessor('last_message_at', {
    header: 'Last Message',
    cell: (info) => {
      const v = info.getValue()
      return v ? formatDate(v) : '—'
    },
  }),
  columnHelper.accessor('current_state', {
    header: 'State',
    cell: (info) => (
      <Badge variant="secondary">{info.getValue()}</Badge>
    ),
  }),
  columnHelper.accessor('updated_at', {
    header: 'Last Updated',
    cell: (info) => formatDate(info.getValue()),
  }),
]

function ConversationsPage() {
  const navigate = useNavigate()
  const [data, setData] = React.useState<Conversation[]>([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  const fetchConversations = React.useCallback(() => {
    setLoading(true)
    setError(null)
    api
      .getConversations(50, 0)
      .then((res) => setData(res.data ?? []))
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false))
  }, [])

  React.useEffect(() => {
    fetchConversations()
  }, [fetchConversations])

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  })

  return (
    <>
      <Header title="Active Conversations" />
      <Main>
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Active Conversations</h2>
            <p className="text-muted-foreground">Latest conversation activity</p>
          </div>
        </div>

        {error && (
          <div className="mt-4 rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive">
            <p>{error}</p>
            <Button variant="secondary" size="sm" className="mt-2" onClick={fetchConversations}>
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
              No active conversations.
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
                        to: '/contacts/$contactId',
                        params: { contactId: row.original.contact_id },
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

export const Route = conversationsRoute
