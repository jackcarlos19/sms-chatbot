import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, type Contact } from '../api'
import { displayName, formatDate } from '../utils'

const PAGE_SIZE = 50

function statusBadge(status: string): string {
  if (status === 'opted_in') return 'bg-green-100 text-green-800'
  if (status === 'opted_out') return 'bg-red-100 text-red-800'
  if (status === 'pending') return 'bg-yellow-100 text-yellow-800'
  return 'bg-gray-100 text-gray-800'
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

  const loadContacts = async (nextOffset: number, reset = false) => {
    try {
      setError('')
      const rows = await api.getContacts(PAGE_SIZE, nextOffset)
      setHasMore(rows.length === PAGE_SIZE)
      setOffset(nextOffset + rows.length)
      if (reset) {
        setContacts(rows)
      } else {
        setContacts((prev) => [...prev, ...rows])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load contacts')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadContacts(0, true)
  }, [])

  const filteredContacts = useMemo(() => {
    return contacts.filter((contact) => {
      const phoneMatch = contact.phone_number.toLowerCase().includes(search.toLowerCase())
      const statusMatch = status === 'all' ? true : contact.opt_in_status === status
      return phoneMatch && statusMatch
    })
  }, [contacts, search, status])

  if (loading) {
    return (
      <div className="space-y-3 rounded-lg border border-gray-200 bg-white p-6">
        <div className="h-6 w-40 animate-pulse rounded bg-gray-200" />
        <div className="h-10 w-full animate-pulse rounded bg-gray-200" />
        <div className="h-10 w-full animate-pulse rounded bg-gray-200" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="flex items-center justify-between rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
          <span>{error}</span>
          <button
            type="button"
            onClick={() => loadContacts(0, true)}
            className="rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      )}

      <div className="flex flex-col gap-3 rounded-lg border border-gray-200 bg-white p-4 md:flex-row">
        <input
          type="text"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search by phone number..."
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 md:max-w-sm"
        />
        <select
          value={status}
          onChange={(event) => setStatus(event.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 md:w-52"
        >
          <option value="all">All</option>
          <option value="opted_in">Opted In</option>
          <option value="opted_out">Opted Out</option>
          <option value="pending">Pending</option>
        </select>
      </div>

      {filteredContacts.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-500">
          No contacts found
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="bg-gray-50 text-xs font-medium uppercase text-gray-500">
                <th className="px-4 py-3">Phone Number</th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Timezone</th>
                <th className="px-4 py-3">Created</th>
              </tr>
            </thead>
            <tbody>
              {filteredContacts.map((contact) => (
                <tr
                  key={contact.id}
                  className="cursor-pointer border-b border-gray-100 hover:bg-gray-50"
                  onClick={() => navigate(`/contacts/${contact.id}`)}
                >
                  <td className="px-4 py-3">{contact.phone_number}</td>
                  <td className="px-4 py-3">{displayName(contact)}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${statusBadge(contact.opt_in_status)}`}>
                      {contact.opt_in_status}
                    </span>
                  </td>
                  <td className="px-4 py-3">{contact.timezone}</td>
                  <td className="px-4 py-3">{formatDate(contact.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <button
        type="button"
        onClick={() => loadContacts(offset)}
        disabled={!hasMore}
        className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
      >
        Load More
      </button>
    </div>
  )
}
