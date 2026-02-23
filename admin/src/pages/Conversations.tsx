import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, type Conversation } from '../api'
import { formatDate } from '../utils'
import { Card, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'

function getStateBadgeVariant(state: string): "secondary" | "success" | "destructive" | "warning" {
  if (state === 'idle') return 'secondary'
  if (state === 'confirmed') return 'success'
  if (state === 'cancelling') return 'destructive'
  return 'warning'
}

export default function Conversations() {
  const navigate = useNavigate()
  const [rows, setRows] = useState<Conversation[]>([])
  const [showIdle, setShowIdle] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadRows = async () => {
    try {
      setError('')
      const data = await api.getConversations(100, 0)
      setRows(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load conversations')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRows()
    const timer = window.setInterval(loadRows, 10000)
    return () => window.clearInterval(timer)
  }, [])

  const visibleRows = useMemo(
    () => rows.filter((row) => (showIdle ? true : row.current_state !== 'idle')),
    [rows, showIdle],
  )

  if (loading) {
    return (
      <div className="space-y-6">
        <Card className="animate-pulse"><CardContent className="p-6 h-[400px]" /></Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Conversations</h1>
      </div>

      {error && (
        <div className="flex items-center justify-between rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-destructive">
          <span className="text-sm font-medium">{error}</span>
          <Button variant="danger" size="sm" onClick={loadRows}>
            Retry
          </Button>
        </div>
      )}

      <Card>
        <CardContent className="p-4 sm:p-6 border-b border-border flex justify-between items-center">
          <label className="inline-flex items-center gap-2 text-sm font-medium text-foreground cursor-pointer">
            <input
              type="checkbox"
              checked={showIdle}
              onChange={(event) => setShowIdle(event.target.checked)}
              className="rounded border-input text-primary focus:ring-ring h-4 w-4"
            />
            Show idle conversations
          </label>
        </CardContent>

        <CardContent className="px-0 py-0">
          {visibleRows.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 text-center text-muted-foreground">
              <p className="text-sm font-medium">No conversations found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/50 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    <th className="px-6 py-4">Contact</th>
                    <th className="px-6 py-4">Name</th>
                    <th className="px-6 py-4">State</th>
                    <th className="px-6 py-4">Last Message</th>
                    <th className="px-6 py-4">Updated</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {visibleRows.map((row) => (
                    <tr
                      key={row.id}
                      className="cursor-pointer transition-colors hover:bg-muted/50"
                      onClick={() => navigate(`/contacts/${row.contact_id}`)}
                    >
                      <td className="whitespace-nowrap px-6 py-4 font-medium text-foreground">{row.contact_phone}</td>
                      <td className="whitespace-nowrap px-6 py-4 text-muted-foreground">{row.contact_name}</td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <Badge variant={getStateBadgeVariant(row.current_state)}>
                          {row.current_state.replace('_', ' ')}
                        </Badge>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-muted-foreground">{formatDate(row.last_message_at)}</td>
                      <td className="whitespace-nowrap px-6 py-4 text-muted-foreground">{formatDate(row.updated_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
