import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, type Appointment, type ContactDetail as ContactDetailType, type Message } from '../api'
import { displayName, formatDate } from '../utils'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'

function statusColor(status: string): string {
  if (status === 'delivered') return 'text-green-600 dark:text-green-400'
  if (status === 'failed') return 'text-destructive'
  return 'text-muted-foreground'
}

function getAppointmentBadgeVariant(status: string): "success" | "destructive" | "warning" | "secondary" {
  if (status === 'confirmed') return 'success'
  if (status === 'cancelled') return 'destructive'
  if (status === 'rescheduled') return 'warning'
  return 'secondary'
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
    return (
      <div className="space-y-6">
        <Card className="animate-pulse">
          <CardContent className="p-6">
            <div className="h-4 w-20 rounded bg-muted mb-4" />
            <div className="h-8 w-64 rounded bg-muted" />
          </CardContent>
        </Card>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2 animate-pulse">
            <CardContent className="p-6 h-[400px]" />
          </Card>
          <div className="space-y-6">
            <Card className="animate-pulse"><CardContent className="p-6 h-32" /></Card>
            <Card className="animate-pulse"><CardContent className="p-6 h-48" /></Card>
          </div>
        </div>
      </div>
    )
  }

  if (error || !contact) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm font-medium text-destructive">
        {error || 'Contact not found'}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="p-4 sm:p-6">
          <Link to="/contacts" className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground mb-4 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-1">
              <path d="m15 18-6-6 6-6"/>
            </svg>
            Back to Contacts
          </Link>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">{displayName(contact)}</h1>
            <span className="text-muted-foreground">{contact.phone_number}</span>
            <Badge variant={contact.opt_in_status === 'opted_in' ? 'success' : 'destructive'}>
              {contact.opt_in_status.replace('_', ' ')}
            </Badge>
            <span className="text-xs font-medium text-muted-foreground bg-muted px-2 py-1 rounded-md">{contact.timezone}</span>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="flex flex-col lg:col-span-2">
          <CardHeader className="border-b border-border py-4">
            <CardTitle className="text-lg">Conversation History</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 p-0">
            <div className="h-[500px] overflow-y-auto bg-muted/20 p-4 sm:p-6 scroll-smooth">
              {orderedMessages.length === 0 ? (
                <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                  No messages yet
                </div>
              ) : (
                <div className="space-y-4">
                  {orderedMessages.map((message) => {
                    const outbound = message.direction === 'outbound'
                    return (
                      <div key={message.id} className={`flex w-full flex-col ${outbound ? 'items-end' : 'items-start'}`}>
                        <div
                          className={`relative max-w-[85%] sm:max-w-[75%] px-4 py-2.5 text-sm shadow-sm ${
                            outbound 
                              ? 'rounded-2xl rounded-br-sm bg-blue-600 text-white dark:bg-blue-600' 
                              : 'rounded-2xl rounded-bl-sm bg-muted text-foreground'
                          }`}
                        >
                          {message.body}
                        </div>
                        <div className="mt-1 flex items-center gap-2 px-1">
                          <span className="text-[11px] font-medium text-muted-foreground">
                            {formatDate(message.created_at)}
                          </span>
                          {outbound && (
                            <span className={`text-[11px] font-medium ${statusColor(message.status)}`}>
                              • {message.status}
                              {message.error_code ? ` (${message.error_code})` : ''}
                            </span>
                          )}
                        </div>
                      </div>
                    )
                  })}
                  <div ref={bottomRef} className="h-2" />
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Current State</CardTitle>
            </CardHeader>
            <CardContent>
              <Badge variant={contact.conversation_state === 'idle' ? 'secondary' : 'default'} className="mb-3 text-sm px-3 py-1">
                {contact.conversation_state.replace('_', ' ')}
              </Badge>
              <p className="text-xs text-muted-foreground">
                <span className="font-medium text-foreground">Last activity:</span><br/>
                {contact.last_message_at ? formatDate(contact.last_message_at) : 'Never'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Appointments</CardTitle>
            </CardHeader>
            <CardContent>
              {appointments.length === 0 ? (
                <p className="text-sm text-muted-foreground">No appointments history.</p>
              ) : (
                <div className="space-y-3">
                  {appointments.map((appointment) => (
                    <div key={appointment.id} className="rounded-lg border border-border bg-card p-3 shadow-sm transition-colors hover:bg-muted/50">
                      <div className="mb-2 flex items-center justify-between">
                        <Badge variant={getAppointmentBadgeVariant(appointment.status)}>
                          {appointment.status}
                        </Badge>
                      </div>
                      <p className="text-sm font-medium text-foreground">
                        {formatDate(appointment.booked_at)}
                      </p>
                      {appointment.cancelled_at && (
                        <p className="mt-1 text-xs text-destructive">
                          Cancelled: {formatDate(appointment.cancelled_at)}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
