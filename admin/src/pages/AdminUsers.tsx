import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { api, type AdminUser } from '../api'
import { formatDate } from '../utils'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'

export default function AdminUsers() {
  const [rows, setRows] = useState<AdminUser[]>([])
  const [username, setUsername] = useState('')
  const [role, setRole] = useState('admin')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    try {
      setError('')
      setRows(await api.getAdminUsers())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load admin users')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const onCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!username.trim()) return
    try {
      await api.createAdminUser({
        username: username.trim(),
        role: role.trim(),
      })
      setUsername('')
      setRole('admin')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create admin user')
    }
  }

  if (loading) {
    return <Card className="animate-pulse"><CardContent className="p-6 h-40" /></Card>
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight text-foreground">Admin Users</h1>
      {error && <div className="rounded border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</div>}

      <Card>
        <CardHeader><CardTitle className="text-base">Create Admin User</CardTitle></CardHeader>
        <CardContent>
          <form className="grid grid-cols-1 gap-3 md:grid-cols-3" onSubmit={onCreate}>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted-foreground">Username</label>
              <Input value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Username" required />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted-foreground">Role</label>
              <Select value={role} onChange={(event) => setRole(event.target.value)} required>
                <option value="super_admin">Super Admin</option>
                <option value="admin">Admin</option>
                <option value="viewer">Viewer</option>
              </Select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted-foreground invisible">Action</label>
              <Button type="submit">Create</Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base">Role Assignments</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {rows.length === 0 ? (
            <p className="text-sm text-muted-foreground">No admin users found.</p>
          ) : rows.map((row) => (
            <div key={row.id} className="flex items-center justify-between rounded border border-border px-3 py-2">
              <div>
                <p className="text-sm font-medium">{row.username}</p>
                <p className="text-xs text-muted-foreground">Created {formatDate(row.created_at)}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={row.is_active ? 'success' : 'secondary'}>{row.is_active ? 'active' : 'inactive'}</Badge>
                <Badge variant="outline">{row.role}</Badge>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
