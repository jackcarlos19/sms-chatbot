import { z } from 'zod'

/** Auth */
export const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
})

/** Contact edit (PATCH /api/contacts/:id) */
export const contactPatchSchema = z.object({
  first_name: z.string().nullable(),
  last_name: z.string().nullable(),
  timezone: z.string(),
  opt_in_status: z.enum(['opted_in', 'opted_out', 'pending']),
})

/** Waitlist */
export const waitlistCreateSchema = z.object({
  contact_id: z.string().uuid(),
  desired_start: z.string().datetime().optional(),
  desired_end: z.string().datetime().optional(),
  notes: z.string().optional(),
})
export const waitlistPatchSchema = z.object({
  status: z.enum(['open', 'notified', 'closed']).optional(),
  notes: z.string().optional(),
})

/** Workflows */
export const reminderWorkflowCreateSchema = z.object({
  name: z.string().min(1),
  minutes_before: z.number().int().positive(),
  template: z.string().min(1),
  appointment_status: z.string().optional(),
  channel: z.enum(['sms', 'email', 'voice']).default('sms'),
})
export const reminderWorkflowPatchSchema = z.object({
  name: z.string().optional(),
  minutes_before: z.number().int().positive().optional(),
  template: z.string().optional(),
  is_active: z.boolean().optional(),
  appointment_status: z.string().optional(),
  channel: z.enum(['sms', 'email', 'voice']).optional(),
})

/** Campaigns */
export const campaignCreateSchema = z.object({
  name: z.string().min(1),
  message_template: z.string().min(1),
  recipient_filter: z.record(z.string(), z.unknown()).optional(),
})
export const campaignUpdateSchema = z.object({
  status: z.string().optional(),
  scheduled_at: z.string().datetime().optional(),
})

/** Appointment actions */
export const appointmentCancelSchema = z.object({
  reason: z.string().min(1),
})
export const appointmentRescheduleSchema = z.object({
  new_slot_id: z.string().uuid(),
})
export const appointmentNotesSchema = z.object({
  notes: z.string(),
})

/** Admin users */
export const adminUserCreateSchema = z.object({
  username: z.string().min(1),
  role: z.enum(['super_admin', 'admin', 'viewer']).optional(),
  is_active: z.boolean().optional(),
})

/** Simulator */
export const simulateInboundSchema = z.object({
  phone_number: z.string().min(1),
  message: z.string(),
})
