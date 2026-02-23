import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { api, type Contact, type WaitlistEntry } from '../api'
import { formatDate } from '../utils'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'

export default function Waitlist() {
  const [entries, setEntries] = useState<WaitlistEntry[]>([])
  const [contacts, setContacts] = useState<Contact[]>([])
  const [contactId, setContactId] = useState('')
  const [notes, setNotes] = useState('')
  const [desiredStart, setDesiredStart] = useState('')
  const [desiredEnd, setDesiredEnd] = useState('')
  const [statusFilter, setStatusFilter] = useState('open')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async (status = statusFilter) => {
    try {
      setError('')
      const [waitlistData, contactData] = await Promise.all([
        api.getWaitlist(status),
        api.getContacts(100, 0, '', 'all'),
      ])
      setEntries(waitlistData)
      setContacts(contactData.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load waitlist')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter])

  const onCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!contactId) return
    try {
      await api.createWaitlist({
        contact_id: contactId,
        desired_start: desiredStart ? new Date(desiredStart).toISOString() : undefined,
        desired_end: desiredEnd ? new Date(desiredEnd).toISOString() : undefined,
        notes: notes || undefined
      })
      setContactId('')
      setNotes('')
      setDesiredStart('')
      setDesiredEnd('')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create waitlist entry')
    }
  }

  const setStatus = async (id: string, status: string) => {
    try {
      await api.updateWaitlist(id, { status })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update waitlist')
    }
  }

  if (loading) {
    return <Card className="animate-pulse"><CardContent className="p-6 h-48" /></Card>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Waitlist</h1>
      </div>

      {error && <div className="rounded border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</div>}

      <Card>
        <CardHeader><CardTitle className="text-base">Add Waitlist Entry</CardTitle></CardHeader>
        <CardContent>
          <form className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-5" onSubmit={onCreate}>
            <Select
              value={contactId}
              onChange={(event) => setContactId(event.target.value)}
              required
            >
              <option value="">Select contact</option>
              {contacts.map((contact) => (
                <option key={contact.id} value={contact.id}>
                  {contact.phone_number} {contact.first_name || contact.last_name ? `(${[contact.first_name, contact.last_name].filter(Boolean).join(' ')})` : ''}
                </option>
              ))}
            </Select>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted-foreground">Desired Start (Optional)</label>
              <Input type="datetime-local" value={desiredStart} onChange={(event) => setDesiredStart(event.target.value)} />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted-foreground">Desired End (Optional)</label>
              <Input type="datetime-local" value={desiredEnd} onChange={(event) => setDesiredEnd(event.target.value)} />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted-foreground invisible">Notes</label>
              <Input value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Notes" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted-foreground invisible">Action</label>
              <Button type="submit">Add</Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Entries</CardTitle>
          <Select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            className="w-[150px]"
          >
            <option value="open">Open</option>
            <option value="notified">Notified</option>
            <option value="closed">Closed</option>
          </Select>
        </CardHeader>
        <CardContent className="space-y-3">
          {entries.length === 0 ? (
            <p className="text-sm text-muted-foreground">No waitlist entries.</p>
          ) : (
            entries.map((entry) => (
              <div key={entry.id} className="flex flex-wrap items-center justify-between gap-3 rounded border border-border p-3">
                <div>
                  <p className="text-sm font-medium">{entry.contact_name || entry.contact_phone}</p>
                  <p className="text-xs text-muted-foreground">{entry.contact_phone}</p>
                  {entry.desired_start && <p className="text-xs text-muted-foreground mt-1">From: {formatDate(entry.desired_start)}</p>}
                  {entry.desired_end && <p className="text-xs text-muted-foreground">Until: {formatDate(entry.desired_end)}</p>}
                  {entry.notes && <p className="text-xs mt-1 text-foreground">Notes: {entry.notes}</p>}
                  <p className="text-[10px] mt-1 text-muted-foreground">Created {formatDate(entry.created_at)}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={entry.status === 'open' ? 'warning' : entry.status === 'closed' ? 'secondary' : 'default'}>
                    {entry.status}
                  </Badge>
                  {entry.status !== 'notified' && <Button size="sm" variant="secondary" onClick={() => setStatus(entry.id, 'notified')}>Notify</Button>}
                  {entry.status !== 'closed' && <Button size="sm" variant="secondary" onClick={() => setStatus(entry.id, 'closed')}>Close</Button>}
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  )
}
