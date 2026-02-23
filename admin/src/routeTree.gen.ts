import { __rootRoute } from './routes/__root'
import { signInRoute } from './routes/sign-in'
import { _authenticatedRoute } from './routes/_authenticated'
import { indexRoute } from './routes/_authenticated/index'
import { contactsRoute } from './routes/_authenticated/contacts'
import { contactsContactIdRoute } from './routes/_authenticated/contacts.$contactId'
import { appointmentsIndexRoute } from './routes/_authenticated/appointments.index'
import { appointmentsAppointmentIdRoute } from './routes/_authenticated/appointments.$appointmentId'
import { slotsRoute } from './routes/_authenticated/slots'
import { waitlistRoute } from './routes/_authenticated/waitlist'

__rootRoute.addChildren([signInRoute, _authenticatedRoute])
_authenticatedRoute.addChildren([
  indexRoute,
  contactsRoute,
  contactsContactIdRoute,
  appointmentsIndexRoute,
  appointmentsAppointmentIdRoute,
  slotsRoute,
  waitlistRoute,
])

export const routeTree = __rootRoute
