import * as React from 'react'
import { createRoute, redirect } from '@tanstack/react-router'
import { __rootRoute } from './__root'
import { api } from '../api'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { loginSchema } from '../lib/schemas'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import type { z } from 'zod'

type LoginForm = z.infer<typeof loginSchema>

async function ensureUnauthenticated() {
  try {
    const res = await api.me()
    if (res.authenticated) throw redirect({ to: '/' })
  } catch (e) {
    if (e && typeof e === 'object' && 'to' in e) throw e
    // not authenticated, stay on sign-in
  }
}

const signInRoute = createRoute({
  getParentRoute: () => __rootRoute,
  path: '/sign-in',
  beforeLoad: ensureUnauthenticated,
  component: SignInPage,
})

function SignInPage() {
  const [error, setError] = React.useState('')
  const [loading, setLoading] = React.useState(false)

  const form = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: '', password: '' },
  })

  const onSubmit = async (data: LoginForm) => {
    setError('')
    setLoading(true)
    try {
      await api.login({ username: data.username, password: data.password })
      window.location.href = '/admin/'
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      if (msg.includes('401')) setError('Invalid credentials')
      else if (msg.includes('fetch') || msg.includes('Network')) setError('Cannot reach server. Check that the app is running at this URL and try again.')
      else setError(msg || 'Cannot reach server')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">SMS Chatbot</h1>
          <p className="text-sm text-muted-foreground">Sign in to your admin account</p>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
            <div className="space-y-1">
              <label className="text-sm font-medium text-foreground">Username</label>
              <Input
                {...form.register('username')}
                type="text"
                placeholder="Username"
                autoComplete="username"
              />
              {form.formState.errors.username && (
                <p className="text-sm text-destructive">{form.formState.errors.username.message}</p>
              )}
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium text-foreground">Password</label>
              <Input
                {...form.register('password')}
                type="password"
                placeholder="Password"
                autoComplete="current-password"
              />
              {form.formState.errors.password && (
                <p className="text-sm text-destructive">{form.formState.errors.password.message}</p>
              )}
            </div>
            {error && <p className="text-sm font-medium text-destructive">{error}</p>}
            <Button type="submit" disabled={loading} className="w-full" size="md">
              {loading ? 'Connecting...' : 'Connect'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

export { signInRoute }
