import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, type Contact } from '../api'
import { displayName, formatDate } from '../utils'
import { Card, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Input } from '../components/ui/Input'
import { Button } from '../components/ui/Button'

const PAGE_SIZE = 50

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delay)
    return () => window.clearTimeout(timer)
  }, [value, delay])
  return debounced
}

function getStatusBadgeVariant(status: string): "success" | "destructive" | "warning" | "secondary" {
  if (status === 'opted_in') return 'success'
  if (status === 'opted_out') return 'destructive'
  if (status === 'pending') return 'warning'
  return 'secondary'
}

export default function Contacts() {
  const navigate = useNavigate()
  const [contacts, setContacts] = useState<Contact[]>([])
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('all')
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const debouncedSearch = useDebounce(search, 300)

  const loadContacts = async (
    nextOffset: number,
    reset = false,
    searchValue = debouncedSearch,
    statusValue = status,
  ) => {
    try {
      setError('')
      const response = await api.getContacts(PAGE_SIZE, nextOffset, searchValue, statusValue)
      setHasMore(response.has_more)
      setOffset(nextOffset + response.data.length)
      if (reset) {
        setContacts(response.data)
      } else {
        setContacts((prev) => [...prev, ...response.data])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load contacts')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    setLoading(true)
    loadContacts(0, true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch, status])

  if (loading) {
    return (
      <div className="space-y-6">
        <Card className="animate-pulse">
          <CardContent className="p-6">
            <div className="h-10 w-full rounded bg-muted" />
          </CardContent>
        </Card>
        <Card className="animate-pulse">
          <CardContent className="p-6 h-[400px]" />
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Contacts</h1>
      </div>

      {error && (
        <div className="flex items-center justify-between rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-destructive">
          <span className="text-sm font-medium">{error}</span>
          <Button variant="danger" size="sm" onClick={() => loadContacts(0, true)}>
            Retry
          </Button>
        </div>
      )}

      <Card>
        <CardContent className="p-4 sm:p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
            <div className="flex-1">
              <Input
                type="text"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search by phone number..."
                className="max-w-md bg-background"
              />
            </div>
            <select
              value={status}
              onChange={(event) => setStatus(event.target.value)}
              className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:w-[180px]"
            >
              <option value="all">All Statuses</option>
              <option value="opted_in">Opted In</option>
              <option value="opted_out">Opted Out</option>
              <option value="pending">Pending</option>
            </select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="px-0 py-0">
          {contacts.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 text-center text-muted-foreground">
              <p className="text-sm font-medium">No contacts found</p>
              <p className="text-xs mt-1">Try adjusting your filters</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/50 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    <th className="px-6 py-4">Phone Number</th>
                    <th className="px-6 py-4">Name</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4">Timezone</th>
                    <th className="px-6 py-4">Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {contacts.map((contact) => (
                    <tr
                      key={contact.id}
                      className="cursor-pointer transition-colors hover:bg-muted/50"
                      onClick={() => navigate(`/contacts/${contact.id}`)}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter' || event.key === ' ') {
                          event.preventDefault()
                          navigate(`/contacts/${contact.id}`)
                        }
                      }}
                      tabIndex={0}
                      role="link"
                    >
                      <td className="whitespace-nowrap px-6 py-4 font-medium text-foreground">{contact.phone_number}</td>
                      <td className="whitespace-nowrap px-6 py-4 text-muted-foreground">{displayName(contact)}</td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <Badge variant={getStatusBadgeVariant(contact.opt_in_status)}>
                          {contact.opt_in_status.replace('_', ' ')}
                        </Badge>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-muted-foreground">{contact.timezone}</td>
                      <td className="whitespace-nowrap px-6 py-4 text-muted-foreground">{formatDate(contact.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-center">
        <Button
          variant="secondary"
          onClick={() => loadContacts(offset)}
          disabled={!hasMore}
          className="w-full sm:w-auto"
        >
          Load More
        </Button>
      </div>
    </div>
  )
}
