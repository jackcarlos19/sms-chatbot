import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type AppointmentFull } from '../api'
import { formatDate } from '../utils'

const PAGE_SIZE = 50

function formatSlot(slotStart: string): string {
  return new Date(slotStart).toLocaleString([], {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

function durationMinutes(startIso: string, endIso: string): number {
  const start = new Date(startIso).getTime()
  const end = new Date(endIso).getTime()
  return Math.max(0, Math.round((end - start) / 60000))
}

function badgeClass(status: string): string {
  if (status === 'confirmed') return 'bg-green-100 text-green-800'
  if (status === 'cancelled') return 'bg-red-100 text-red-800'
  if (status === 'rescheduled') return 'bg-yellow-100 text-yellow-800'
  return 'bg-gray-100 text-gray-800'
}

export default function Appointments() {
  const [rows, setRows] = useState<AppointmentFull[]>([])
  const [statusFilter, setStatusFilter] = useState('all')
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadRows = async (nextOffset: number, reset = false, selectedStatus = statusFilter) => {
    try {
      setError('')
      const status = selectedStatus === 'all' ? undefined : selectedStatus
      const data = await api.getAllAppointments(PAGE_SIZE, nextOffset, status)
      setHasMore(data.length === PAGE_SIZE)
      setOffset(nextOffset + data.length)
      if (reset) {
        setRows(data)
      } else {
        setRows((prev) => [...prev, ...data])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load appointments')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRows(0, true)
  }, [])

  const onStatusChange = async (value: string) => {
    setStatusFilter(value)
    setLoading(true)
    await loadRows(0, true, value)
  }

  if (loading) {
    return <div className="animate-pulse text-gray-500">Loading appointments...</div>
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="flex items-center justify-between rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
          <span>{error}</span>
          <button
            type="button"
            onClick={() => loadRows(0, true)}
            className="rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      )}

      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <select
          value={statusFilter}
          onChange={(event) => onStatusChange(event.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 md:w-56"
        >
          <option value="all">All</option>
          <option value="confirmed">Confirmed</option>
          <option value="cancelled">Cancelled</option>
          <option value="rescheduled">Rescheduled</option>
        </select>
      </div>

      {rows.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-500">
          No appointments found
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="bg-gray-50 text-xs uppercase text-gray-500">
                <th className="px-4 py-3">Contact</th>
                <th className="px-4 py-3">Date/Time</th>
                <th className="px-4 py-3">Duration</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Booked</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((appointment) => (
                <tr key={appointment.id} className="border-b border-gray-100">
                  <td className="px-4 py-3">
                    <Link to={`/contacts/${appointment.contact_id}`} className="text-blue-600 hover:underline">
                      {appointment.contact_name}
                    </Link>
                    <p className="text-xs text-gray-500">{appointment.contact_phone}</p>
                  </td>
                  <td className="px-4 py-3">{formatSlot(appointment.slot_start)}</td>
                  <td className="px-4 py-3">
                    {durationMinutes(appointment.slot_start, appointment.slot_end)} min
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${badgeClass(appointment.status)}`}>
                      {appointment.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">{formatDate(appointment.booked_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <button
        type="button"
        disabled={!hasMore}
        onClick={() => loadRows(offset)}
        className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
      >
        Load More
      </button>
    </div>
  )
}
