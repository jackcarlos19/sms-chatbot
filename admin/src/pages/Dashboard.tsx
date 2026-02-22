import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type AppointmentFull, type Conversation, type DashboardStats } from '../api'
import { formatDate, formatTime } from '../utils'

function statusBadge(status: string): string {
  if (status === 'confirmed') return 'bg-green-100 text-green-800'
  if (status === 'cancelled') return 'bg-red-100 text-red-800'
  if (status === 'rescheduled') return 'bg-yellow-100 text-yellow-800'
  return 'bg-gray-100 text-gray-800'
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [appointments, setAppointments] = useState<AppointmentFull[]>([])
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const loadData = useCallback(async () => {
    try {
      setError('')
      const [statsData, appointmentData, conversationData] = await Promise.all([
        api.getDashboardStats(),
        api.getAllAppointments(5, 0, 'confirmed'),
        api.getConversations(10, 0),
      ])
      setStats(statsData)
      setAppointments(appointmentData)
      setConversations(conversationData.filter((item) => item.current_state !== 'idle'))
      setLastUpdated(new Date())
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load dashboard'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
    const timer = window.setInterval(loadData, 15000)
    return () => window.clearInterval(timer)
  }, [loadData])

  const cardBase = 'rounded-lg border bg-white p-5 shadow-sm'

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className={`${cardBase} animate-pulse`}>
              <div className="h-5 w-32 rounded bg-gray-200" />
              <div className="mt-4 h-10 w-20 rounded bg-gray-200" />
              <div className="mt-3 h-4 w-24 rounded bg-gray-200" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="flex items-center justify-between rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
          <span>{error}</span>
          <button
            type="button"
            onClick={loadData}
            className="rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <div className={`${cardBase} border-l-4 border-l-blue-500`}>
          <p className="text-sm text-gray-500">Today's Appointments</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{stats?.appointments_today ?? 0}</p>
          <p className="mt-2 text-sm text-gray-500">Upcoming: {stats?.appointments_upcoming ?? 0}</p>
        </div>
        <div className={`${cardBase} border-l-4 border-l-orange-500`}>
          <p className="text-sm text-gray-500">Active Conversations</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{stats?.conversations_active ?? 0}</p>
          <p className="mt-2 text-sm text-gray-500">Total campaigns: {stats?.campaigns_total ?? 0}</p>
        </div>
        <div className={`${cardBase} border-l-4 border-l-purple-500`}>
          <p className="text-sm text-gray-500">Messages Today</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{stats?.messages_today ?? 0}</p>
          <p className="mt-2 text-sm text-gray-500">
            ↑{stats?.messages_inbound_today ?? 0} ↓{stats?.messages_outbound_today ?? 0}
          </p>
        </div>
        <div className={`${cardBase} border-l-4 border-l-green-500`}>
          <p className="text-sm text-gray-500">Total Contacts</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{stats?.contacts_total ?? 0}</p>
          <p className="mt-2 text-sm text-gray-500">{stats?.contacts_opted_in ?? 0} active</p>
        </div>
      </div>

      <p className="text-sm text-gray-500">
        Last updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : '—'}
      </p>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className={cardBase}>
          <h2 className="text-lg font-semibold text-gray-900">Upcoming Appointments</h2>
          {appointments.length === 0 ? (
            <p className="mt-4 text-sm text-gray-500">No upcoming appointments</p>
          ) : (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="bg-gray-50 text-xs uppercase text-gray-500">
                    <th className="px-3 py-2">Contact</th>
                    <th className="px-3 py-2">Time</th>
                    <th className="px-3 py-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {appointments.map((item) => (
                    <tr key={item.id} className="border-b border-gray-100">
                      <td className="px-3 py-2">
                        <Link to={`/contacts/${item.contact_id}`} className="text-blue-600 hover:underline">
                          {item.contact_name || item.contact_phone}
                        </Link>
                      </td>
                      <td className="px-3 py-2">
                        {formatDate(item.slot_start)} ({formatTime(item.slot_start)})
                      </td>
                      <td className="px-3 py-2">
                        <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${statusBadge(item.status)}`}>
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className={cardBase}>
          <h2 className="text-lg font-semibold text-gray-900">Active Conversations</h2>
          {conversations.length === 0 ? (
            <p className="mt-4 text-sm text-gray-500">No active conversations</p>
          ) : (
            <ul className="mt-4 space-y-3">
              {conversations.map((item) => (
                <li key={item.id} className="rounded-md border border-gray-200 px-3 py-2">
                  <div className="flex items-center justify-between gap-3">
                    <Link to={`/contacts/${item.contact_id}`} className="text-sm font-medium text-blue-600 hover:underline">
                      {item.contact_phone}
                    </Link>
                    <span className="rounded-full bg-orange-100 px-2.5 py-0.5 text-xs font-medium text-orange-800">
                      {item.current_state}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-gray-500">Last message: {formatDate(item.last_message_at)}</p>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}
