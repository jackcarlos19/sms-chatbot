/**
 * Centralized API client: credentials, CSRF, 401 handling.
 * Set redirectOnUnauthorized from the router so 401s redirect to sign-in.
 */

export const UNAUTHORIZED_ERR = '401 Unauthorized'

let redirectOnUnauthorized: (() => void) | null = null

export function setRedirectOnUnauthorized(fn: () => void) {
  redirectOnUnauthorized = fn
}

function getCookie(name: string): string {
  const escaped = name.replace(/[-[\]/{}()*+?.\\^$|]/g, '\\$&')
  const match = document.cookie.match(new RegExp(`(?:^|; )${escaped}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : ''
}

export type ApiFetchOptions = RequestInit

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
    if (redirectOnUnauthorized) redirectOnUnauthorized()
    throw new Error(UNAUTHORIZED_ERR)
  }

  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`)
  }

  return (await response.json()) as T
}
