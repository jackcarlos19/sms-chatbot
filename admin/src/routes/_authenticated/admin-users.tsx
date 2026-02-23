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
import type { AdminUser } from '../../api'
import { adminUserCreateSchema } from '../../lib/schemas'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import type { z } from 'zod'

type AdminUserCreateForm = z.infer<typeof adminUserCreateSchema>

export const adminUsersRoute = createRoute({
  getParentRoute: () => _authenticatedRoute,
  path: '/admin-users',
  component: AdminUsersPage,
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

const ROLE_OPTIONS = [
  { value: 'super_admin', label: 'Super Admin' },
  { value: 'admin', label: 'Admin' },
  { value: 'viewer', label: 'Viewer' },
]

const columnHelper = createColumnHelper<AdminUser>()

const columns = [
  columnHelper.accessor('username', { header: 'Username', cell: (info) => info.getValue() }),
  columnHelper.accessor('role', {
    header: 'Role',
    cell: (info) => <Badge variant="secondary">{info.getValue()}</Badge>,
  }),
  columnHelper.accessor('created_at', {
    header: 'Created at',
    cell: (info) => formatDate(info.getValue()),
  }),
]

function AddUserDialog({
  onSuccess,
  onCancel,
}: {
  onSuccess: () => void
  onCancel: () => void
}) {
  const [submitting, setSubmitting] = React.useState(false)
  const [submitError, setSubmitError] = React.useState<string | null>(null)

  const form = useForm<AdminUserCreateForm>({
    resolver: zodResolver(adminUserCreateSchema),
    defaultValues: {
      username: '',
      role: 'viewer',
      is_active: true,
    },
  })

  const onSubmit = form.handleSubmit(async (data) => {
    setSubmitting(true)
    setSubmitError(null)
    try {
      await api.createAdminUser({
        username: data.username,
        role: data.role ?? 'viewer',
        is_active: data.is_active,
      })
      toast.success('Admin user added')
      onSuccess()
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : String(err))
    } finally {
      setSubmitting(false)
    }
  })

  const roleValue = form.watch('role') ?? 'viewer'

  return (
    <>
      <DialogHeader>
        <DialogTitle>Add user</DialogTitle>
        <DialogDescription>
          Create a new admin user. They can sign in with the username (and password set by your backend).
        </DialogDescription>
      </DialogHeader>
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Username</label>
          <Input {...form.register('username')} placeholder="jane" />
          {form.formState.errors.username && (
            <p className="text-sm text-destructive">{form.formState.errors.username.message}</p>
          )}
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Role</label>
          <Select value={roleValue} onValueChange={(v) => form.setValue('role', v as 'super_admin' | 'admin' | 'viewer')}>
            <SelectTrigger>
              <SelectValue placeholder="Select role" />
            </SelectTrigger>
            <SelectContent>
              {ROLE_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {form.formState.errors.role && (
            <p className="text-sm text-destructive">{form.formState.errors.role.message}</p>
          )}
        </div>
        {submitError && <p className="text-sm text-destructive">{submitError}</p>}
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting ? 'Adding…' : 'Add user'}
          </Button>
        </DialogFooter>
      </form>
    </>
  )
}

function AdminUsersPage() {
  const [data, setData] = React.useState<AdminUser[]>([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)
  const [addOpen, setAddOpen] = React.useState(false)

  const fetchUsers = React.useCallback(() => {
    setLoading(true)
    setError(null)
    api
      .getAdminUsers()
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false))
  }, [])

  React.useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  })

  return (
    <>
      <Header title="Admin Users" />
      <Main>
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Admin Users</h2>
            <p className="text-muted-foreground">Manage admin accounts</p>
          </div>
          <Dialog open={addOpen} onOpenChange={setAddOpen}>
            <DialogTrigger asChild>
              <Button size="sm">Add User</Button>
            </DialogTrigger>
            <DialogContent showClose>
              <AddUserDialog
                onSuccess={() => {
                  setAddOpen(false)
                  fetchUsers()
                }}
                onCancel={() => setAddOpen(false)}
              />
            </DialogContent>
          </Dialog>
        </div>

        {error && (
          <div className="mt-4 rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive">
            <p>{error}</p>
            <Button variant="secondary" size="sm" className="mt-2" onClick={fetchUsers}>
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
              No admin users yet. Add one to get started.
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

export const Route = adminUsersRoute
