import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, type Appointment, type ContactDetail as ContactDetailType, type Message } from '../api'
import { displayName, formatDate } from '../utils'

function statusColor(status: string): string {
  if (status === 'delivered') return 'text-green-600'
  if (status === 'failed') return 'text-red-600'
  if (status === 'simulated') return 'text-gray-500'
  return 'text-gray-500'
}

function appointmentBadge(status: string): string {
  if (status === 'confirmed') return 'bg-green-100 text-green-800'
  if (status === 'cancelled') return 'bg-red-100 text-red-800'
  if (status === 'rescheduled') return 'bg-yellow-100 text-yellow-800'
  return 'bg-gray-100 text-gray-800'
}

export default function ContactDetail() {
  const { id } = useParams<{ id: string }>()
  const [contact, setContact] = useState<ContactDetailType | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const bottomRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const load = async () => {
      if (!id) return
      try {
        setError('')
        const [contactData, messagesData, appointmentData] = await Promise.all([
          api.getContact(id),
          api.getMessages(id),
          api.getContactAppointments(id),
        ])
        setContact(contactData)
        setMessages(messagesData)
        setAppointments(
          [...appointmentData].sort(
            (a, b) => new Date(b.booked_at).getTime() - new Date(a.booked_at).getTime(),
          ),
        )
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load contact')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  const orderedMessages = useMemo(() => [...messages].reverse(), [messages])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [orderedMessages.length])

  if (loading) {
    return <div className="animate-pulse text-gray-500">Loading contact details...</div>
  }

  if (error || !contact) {
    return <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">{error || 'Contact not found'}</div>
  }

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <Link to="/contacts" className="text-sm text-blue-600 hover:underline">
          ← Contacts
        </Link>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-bold text-gray-900">{displayName(contact)}</h1>
          <span className="text-gray-600">{contact.phone_number}</span>
          <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700">
            {contact.opt_in_status}
          </span>
          <span className="text-sm text-gray-500">{contact.timezone}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <section className="rounded-lg border border-gray-200 bg-white p-4 lg:col-span-2">
          <h2 className="text-lg font-semibold text-gray-900">Conversation History</h2>
          <div className="mt-4 max-h-[520px] space-y-3 overflow-y-auto rounded-md border border-gray-100 bg-gray-50 p-3">
            {orderedMessages.map((message) => {
              const outbound = message.direction === 'outbound'
              return (
                <div key={message.id} className={outbound ? 'text-right' : 'text-left'}>
                  <div
                    className={`inline-block max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
                      outbound ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    {message.body}
                  </div>
                  {outbound && (
                    <p className={`mt-1 text-xs ${statusColor(message.status)}`}>
                      {message.status}
                      {message.error_code ? ` (${message.error_code})` : ''}
                    </p>
                  )}
                  <p className="mt-1 text-xs text-gray-400">{formatDate(message.created_at)}</p>
                </div>
              )
            })}
            <div ref={bottomRef} />
          </div>
        </section>

        <aside className="space-y-4">
          <section className="rounded-lg border border-gray-200 bg-white p-4">
            <h3 className="text-lg font-semibold text-gray-900">Conversation State</h3>
            <span className="mt-3 inline-flex rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-800">
              {contact.conversation_state}
            </span>
            <p className="mt-2 text-sm text-gray-500">Last message: {formatDate(contact.last_message_at)}</p>
          </section>

          <section className="rounded-lg border border-gray-200 bg-white p-4">
            <h3 className="text-lg font-semibold text-gray-900">Appointments</h3>
            {appointments.length === 0 ? (
              <p className="mt-2 text-sm text-gray-500">No appointments</p>
            ) : (
              <ul className="mt-3 space-y-3">
                {appointments.map((appointment) => (
                  <li key={appointment.id} className="rounded-md border border-gray-100 p-3">
                    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${appointmentBadge(appointment.status)}`}>
                      {appointment.status}
                    </span>
                    <p className="mt-2 text-sm text-gray-700">Booked: {formatDate(appointment.booked_at)}</p>
                    {appointment.cancelled_at && (
                      <p className="text-sm text-gray-500">Cancelled: {formatDate(appointment.cancelled_at)}</p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </aside>
      </div>
    </div>
  )
}
