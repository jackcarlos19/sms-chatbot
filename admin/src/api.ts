type ApiFetchOptions = RequestInit

function getCookie(name: string): string {
  const escaped = name.replace(/[-[\]/{}()*+?.\\^$|]/g, '\\$&')
  const match = document.cookie.match(new RegExp(`(?:^|; )${escaped}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : ''
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  const headers = new Headers(options.headers ?? {})
  const method = (options.method || 'GET').toUpperCase()

  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  if (method !== 'GET' && method !== 'HEAD') {
    const csrf = getCookie('admin_csrf')
    if (csrf) headers.set('X-CSRF-Token', csrf)
  }

  const response = await fetch(`/api${normalizedPath}`, {
    ...options,
    headers,
    credentials: 'include',
  })

  if (response.status === 401) {
    throw new Error('401 Unauthorized')
  }

  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`)
  }

  return (await response.json()) as T
}

export interface DashboardStats {
  contacts_total: number;
  contacts_opted_in: number;
  contacts_opted_out: number;
  appointments_today: number;
  appointments_upcoming: number;
  appointments_total: number;
  messages_today: number;
  messages_inbound_today: number;
  messages_outbound_today: number;
  conversations_active: number;
  campaigns_active: number;
  campaigns_total: number;
}

export interface Contact {
  id: string;
  phone_number: string;
  first_name: string | null;
  last_name: string | null;
  timezone: string;
  opt_in_status: string;
  created_at: string;
}

export interface ContactDetail extends Contact {
  updated_at: string;
  conversation_state: string;
  last_message_at: string | null;
}

export interface Appointment {
  id: string;
  contact_id: string;
  slot_id: string;
  status: string;
  booked_at: string;
  cancelled_at: string | null;
  rescheduled_from_id: string | null;
}

export interface AppointmentFull {
  id: string;
  contact_id: string;
  contact_phone: string;
  contact_name: string;
  slot_start: string;
  slot_end: string;
  status: string;
  booked_at: string;
}

export interface AppointmentDetail {
  id: string;
  tenant_id: string | null;
  contact_id: string;
  contact_name: string;
  contact_phone: string;
  slot_id: string;
  slot_start: string;
  slot_end: string;
  status: string;
  booked_at: string;
  cancelled_at: string | null;
  cancellation_reason: string | null;
  notes: string | null;
  rescheduled_from_id: string | null;
  version: number;
}

export interface Message {
  id: string;
  contact_id: string | null;
  direction: string;
  body: string;
  sms_sid: string | null;
  status: string;
  error_code: string | null;
  campaign_id: string | null;
  created_at: string;
}

export interface Conversation {
  id: string;
  contact_id: string;
  contact_phone: string;
  contact_name: string;
  current_state: string;
  last_message_at: string | null;
  updated_at: string;
}

export interface Campaign {
  id: string;
  name: string;
  status: string;
  scheduled_at: string | null;
  total_recipients: number;
  sent_count: number;
  delivered_count: number;
  failed_count: number;
  reply_count: number;
  created_at: string;
}

export interface CampaignCreateResponse {
  id: string;
  name: string;
  status: string;
  total_recipients: number;
}

export interface CampaignUpdateResponse {
  id: string;
  name: string;
  status: string;
  scheduled_at: string | null;
}

export interface Slot {
  id: string;
  start_time: string;
  end_time: string;
  is_available: boolean;
  slot_type: string;
}

export interface AuditEvent {
  id: string;
  entity_type: string;
  entity_id: string | null;
  action: string;
  actor_username: string;
  before_json: Record<string, unknown>;
  after_json: Record<string, unknown>;
  created_at: string;
}

export interface WaitlistEntry {
  id: string;
  contact_id: string;
  contact_name: string;
  contact_phone: string;
  status: string;
  desired_start: string | null;
  desired_end: string | null;
  notes: string | null;
  created_at: string;
}

export interface ReminderWorkflow {
  id: string;
  name: string;
  appointment_status: string | null;
  minutes_before: number;
  channel: string;
  template: string;
  is_active: boolean;
  created_at: string;
}

export interface AdminUser {
  id: string;
  username: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface HealthStatus {
  status: string;
  db: string;
  redis: string;
}

export interface SimulateResponse {
  responses: string[];
  conversation_state: string;
  context: Record<string, unknown>;
}

export interface AdminSessionLoginRequest {
  username: string
  password: string
}

export interface AdminSessionStatus {
  authenticated: boolean
}

export interface CampaignCreateRequest {
  name: string
  message_template: string
  recipient_filter: Record<string, unknown>
}

export interface CampaignUpdateRequest {
  status?: string
  scheduled_at?: string
}

export interface ContactUpdateRequest {
  first_name?: string | null
  last_name?: string | null
  timezone?: string
  opt_in_status?: string
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

export const api = {
  login: (payload: AdminSessionLoginRequest) =>
    apiFetch<{ ok: boolean; username: string }>('/admin/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  logout: () =>
    apiFetch<{ ok: boolean }>('/admin/auth/logout', {
      method: 'POST',
    }),
  me: () => apiFetch<AdminSessionStatus>('/admin/auth/me'),
  getDashboardStats: () => apiFetch<DashboardStats>('/dashboard/stats'),
  getContacts: (limit = 50, offset = 0, search = '', status = '') => {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
    if (search) params.set('search', search)
    if (status && status !== 'all') params.set('status', status)
    return apiFetch<PaginatedResponse<Contact>>(`/contacts?${params.toString()}`)
  },
  getContact: (id: string) => apiFetch<ContactDetail>(`/contacts/${id}`),
  updateContact: (id: string, data: ContactUpdateRequest) =>
    apiFetch<ContactDetail>(`/contacts/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  getAllAppointments: (limit = 50, offset = 0, status?: string) => {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    })
    if (status) params.set('status', status)
    return apiFetch<PaginatedResponse<AppointmentFull>>(`/appointments/all?${params.toString()}`)
  },
  getAllAppointmentsFiltered: (params: {
    limit?: number
    offset?: number
    status?: string
    search?: string
    date_from?: string
    date_to?: string
  }) => {
    const query = new URLSearchParams({
      limit: String(params.limit ?? 50),
      offset: String(params.offset ?? 0),
    })
    if (params.status) query.set('status', params.status)
    if (params.search) query.set('search', params.search)
    if (params.date_from) query.set('date_from', params.date_from)
    if (params.date_to) query.set('date_to', params.date_to)
    return apiFetch<PaginatedResponse<AppointmentFull>>(`/appointments/all?${query.toString()}`)
  },
  getAppointment: (id: string) => apiFetch<AppointmentDetail>(`/appointments/${id}`),
  cancelAppointment: (id: string, reason: string) =>
    apiFetch<{ id: string; status: string; cancelled_at: string | null; cancellation_reason: string | null }>(
      `/appointments/${id}/cancel`,
      {
        method: 'POST',
        body: JSON.stringify({ reason }),
      },
    ),
  rescheduleAppointment: (id: string, newSlotId: string) =>
    apiFetch<{ id: string; slot_id: string; status: string; rescheduled_from_id: string | null }>(
      `/appointments/${id}/reschedule`,
      {
        method: 'POST',
        body: JSON.stringify({ new_slot_id: newSlotId }),
      },
    ),
  updateAppointmentNotes: (id: string, notes: string) =>
    apiFetch<{ id: string; notes: string }>(`/appointments/${id}/notes`, {
      method: 'PATCH',
      body: JSON.stringify({ notes }),
    }),
  bookAppointment: (contactId: string, slotId: string) =>
    apiFetch<{ id: string; contact_id: string; slot_id: string; status: string; booked_at: string }>(
      '/appointments/book',
      {
        method: 'POST',
        body: JSON.stringify({ contact_id: contactId, slot_id: slotId }),
      },
    ),
  getContactAppointments: (contactId: string) =>
    apiFetch<Appointment[]>(`/appointments?contact_id=${contactId}`),
  getMessages: (contactId: string) => apiFetch<Message[]>(`/messages?contact_id=${contactId}`),
  getAuditEvents: (entityType: string, entityId: string, limit = 50) =>
    apiFetch<AuditEvent[]>(
      `/audit-events?entity_type=${encodeURIComponent(entityType)}&entity_id=${encodeURIComponent(entityId)}&limit=${limit}`,
    ),
  getConversations: (limit = 50, offset = 0) =>
    apiFetch<PaginatedResponse<Conversation>>(`/conversations?limit=${limit}&offset=${offset}`),
  getCampaigns: (limit = 50, offset = 0) =>
    apiFetch<PaginatedResponse<Campaign>>(`/campaigns?limit=${limit}&offset=${offset}`),
  createCampaign: (data: CampaignCreateRequest) =>
    apiFetch<CampaignCreateResponse>('/campaigns', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateCampaign: (id: string, data: CampaignUpdateRequest) =>
    apiFetch<CampaignUpdateResponse>(`/campaigns/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  getSlots: (daysAhead = 7) => apiFetch<Slot[]>(`/slots?days_ahead=${daysAhead}`),
  getWaitlist: (status = 'open') => apiFetch<WaitlistEntry[]>(`/waitlist?status=${encodeURIComponent(status)}`),
  createWaitlist: (data: { contact_id: string; desired_start?: string; desired_end?: string; notes?: string }) =>
    apiFetch<{ id: string; status: string }>('/waitlist', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateWaitlist: (id: string, data: { status?: string; notes?: string }) =>
    apiFetch<{ id: string; status: string; notes: string | null }>(`/waitlist/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  getReminderWorkflows: () => apiFetch<ReminderWorkflow[]>('/reminder-workflows'),
  createReminderWorkflow: (data: {
    name: string
    appointment_status?: string
    minutes_before: number
    channel?: string
    template: string
    is_active?: boolean
  }) =>
    apiFetch<{ id: string; name: string }>('/reminder-workflows', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateReminderWorkflow: (
    id: string,
    data: Partial<{
      name: string
      appointment_status: string
      minutes_before: number
      channel: string
      template: string
      is_active: boolean
    }>,
  ) =>
    apiFetch<{ id: string; name: string; minutes_before: number; is_active: boolean }>(
      `/reminder-workflows/${id}`,
      {
        method: 'PATCH',
        body: JSON.stringify(data),
      },
    ),
  getAdminUsers: () => apiFetch<AdminUser[]>('/admin-users'),
  getHealth: () => apiFetch<HealthStatus>('/health'),
  simulate: (phone: string, message: string) =>
    apiFetch<SimulateResponse>('/simulate/inbound', {
      method: 'POST',
      body: JSON.stringify({ phone_number: phone, message }),
    }),
}
