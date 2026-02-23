import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, type Conversation } from '../api'
import { formatDate } from '../utils'

function stateBadgeClass(state: string): string {
  if (state === 'idle') return 'bg-gray-100 text-gray-800'
  if (state === 'greeting') return 'bg-blue-100 text-blue-800'
  if (state === 'showing_slots') return 'bg-purple-100 text-purple-800'
  if (state === 'confirming_booking') return 'bg-yellow-100 text-yellow-800'
  if (state === 'confirmed') return 'bg-green-100 text-green-800'
  if (state === 'cancelling') return 'bg-orange-100 text-orange-800'
  if (state === 'rescheduling') return 'bg-yellow-100 text-yellow-800'
  return 'bg-gray-100 text-gray-800'
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
    return <div className="animate-pulse text-gray-500">Loading conversations...</div>
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="flex items-center justify-between rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
          <span>{error}</span>
          <button
            type="button"
            onClick={loadRows}
            className="rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      )}

      <label className="inline-flex items-center gap-2 text-sm text-gray-700">
        <input
          type="checkbox"
          checked={showIdle}
          onChange={(event) => setShowIdle(event.target.checked)}
        />
        Show idle
      </label>

      {visibleRows.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-500">
          No conversations found
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="bg-gray-50 text-xs uppercase text-gray-500">
                <th className="px-4 py-3">Contact</th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">State</th>
                <th className="px-4 py-3">Last Message</th>
                <th className="px-4 py-3">Updated</th>
              </tr>
            </thead>
            <tbody>
              {visibleRows.map((row) => (
                <tr
                  key={row.id}
                  className="cursor-pointer border-b border-gray-100 hover:bg-gray-50"
                  onClick={() => navigate(`/contacts/${row.contact_id}`)}
                >
                  <td className="px-4 py-3">{row.contact_phone}</td>
                  <td className="px-4 py-3">{row.contact_name}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${stateBadgeClass(row.current_state)}`}>
                      {row.current_state}
                    </span>
                  </td>
                  <td className="px-4 py-3">{formatDate(row.last_message_at)}</td>
                  <td className="px-4 py-3">{formatDate(row.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
