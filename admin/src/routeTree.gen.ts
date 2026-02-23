import { __rootRoute } from './routes/__root'
import { signInRoute } from './routes/sign-in'
import { _authenticatedRoute } from './routes/_authenticated'
import { indexRoute } from './routes/_authenticated/index'

__rootRoute.addChildren([signInRoute, _authenticatedRoute])
_authenticatedRoute.addChildren([indexRoute])

export const routeTree = __rootRoute
