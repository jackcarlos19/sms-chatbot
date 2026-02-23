import { useEffect, useState } from 'react'
import { api, type AdminUser } from '../api'
import { formatDate } from '../utils'
import { Badge } from '../components/ui/Badge'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'

export default function AdminUsers() {
  const [rows, setRows] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
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
    load()
  }, [])

  if (loading) {
    return <Card className="animate-pulse"><CardContent className="p-6 h-40" /></Card>
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight text-foreground">Admin Users</h1>
      {error && <div className="rounded border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</div>}
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
