type ApiFetchOptions = RequestInit

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  const headers = new Headers(options.headers ?? {})

  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
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
  getAllAppointments: (limit = 50, offset = 0, status?: string) => {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    })
    if (status) params.set('status', status)
    return apiFetch<PaginatedResponse<AppointmentFull>>(`/appointments/all?${params.toString()}`)
  },
  getContactAppointments: (contactId: string) =>
    apiFetch<Appointment[]>(`/appointments?contact_id=${contactId}`),
  getMessages: (contactId: string) => apiFetch<Message[]>(`/messages?contact_id=${contactId}`),
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
  getHealth: () => apiFetch<HealthStatus>('/health'),
  simulate: (phone: string, message: string) =>
    apiFetch<SimulateResponse>('/simulate/inbound', {
      method: 'POST',
      body: JSON.stringify({ phone_number: phone, message }),
    }),
}
