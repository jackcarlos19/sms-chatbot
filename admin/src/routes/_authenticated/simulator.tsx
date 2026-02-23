import * as React from 'react'
import { createRoute } from '@tanstack/react-router'
import { _authenticatedRoute } from '../_authenticated'
import { Header } from '../../components/layout/header'
import { Main } from '../../components/layout/main'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { Textarea } from '../../components/ui/Textarea'
import { ScrollArea } from '../../components/ui/ScrollArea'
import { toast } from 'sonner'
import { api } from '../../api'
import { simulateInboundSchema } from '../../lib/schemas'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import type { z } from 'zod'

type SimulateForm = z.infer<typeof simulateInboundSchema>

export const simulatorRoute = createRoute({
  getParentRoute: () => _authenticatedRoute,
  path: '/simulator',
  component: SimulatorPage,
})

type LogEntry =
  | { type: 'sent'; phone: string; message: string }
  | { type: 'response'; state: string; responses: string[]; context?: Record<string, unknown> }

function SimulatorPage() {
  const [logs, setLogs] = React.useState<LogEntry[]>([])
  const [submitting, setSubmitting] = React.useState(false)
  const [submitError, setSubmitError] = React.useState<string | null>(null)

  const form = useForm<SimulateForm>({
    resolver: zodResolver(simulateInboundSchema),
    defaultValues: { phone_number: '', message: '' },
  })

  const onSubmit = form.handleSubmit(async (data) => {
    setSubmitting(true)
    setSubmitError(null)
    setLogs((prev) => [
      ...prev,
      { type: 'sent', phone: data.phone_number, message: data.message },
    ])
    try {
      const res = await api.simulate(data.phone_number, data.message)
      setLogs((prev) => [
        ...prev,
        {
          type: 'response',
          state: res.conversation_state,
          responses: res.responses ?? [],
          context: res.context,
        },
      ])
      toast.success('Message sent')
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      setSubmitError(msg)
      toast.error(msg)
    } finally {
      setSubmitting(false)
    }
  })

  return (
    <>
      <Header title="Inbound Simulator" />
      <Main>
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Inbound Simulator</h2>
            <p className="text-muted-foreground">Simulate inbound SMS and view bot responses</p>
          </div>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          {/* Left: Form */}
          <Card>
            <CardHeader>
              <CardTitle>Simulate Inbound SMS</CardTitle>
              <CardDescription>Send a test message as a contact</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={onSubmit} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">From number</label>
                  <Input
                    {...form.register('phone_number')}
                    placeholder="+15551234567"
                  />
                  {form.formState.errors.phone_number && (
                    <p className="text-sm text-destructive">
                      {form.formState.errors.phone_number.message}
                    </p>
                  )}
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Message</label>
                  <Textarea
                    {...form.register('message')}
                    placeholder="Type your message…"
                    rows={4}
                  />
                  {form.formState.errors.message && (
                    <p className="text-sm text-destructive">
                      {form.formState.errors.message.message}
                    </p>
                  )}
                </div>
                {submitError && (
                  <p className="text-sm text-destructive">{submitError}</p>
                )}
                <Button type="submit" disabled={submitting}>
                  {submitting ? 'Sending…' : 'Send'}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Right: Logs / Bot Response */}
          <Card>
            <CardHeader>
              <CardTitle>Simulator Logs</CardTitle>
              <CardDescription>Bot response and conversation state</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[320px] w-full rounded-md border border-border p-3">
                <div className="space-y-3 text-sm">
                  {logs.length === 0 ? (
                    <p className="text-muted-foreground">Send a message to see logs.</p>
                  ) : (
                    logs.map((entry, i) =>
                      entry.type === 'sent' ? (
                        <div key={i} className="rounded-lg border border-primary/20 bg-primary/5 p-2">
                          <div className="font-medium text-muted-foreground">Sent</div>
                          <div className="text-xs text-muted-foreground">{entry.phone}</div>
                          <p className="mt-1">{entry.message}</p>
                        </div>
                      ) : (
                        <div key={i} className="rounded-lg border border-border bg-muted/30 p-2">
                          <div className="font-medium text-muted-foreground">Bot response</div>
                          <div className="text-xs text-muted-foreground">
                            State: {entry.state}
                          </div>
                          {entry.responses.length > 0 ? (
                            <ul className="mt-1 list-inside list-disc space-y-0.5">
                              {entry.responses.map((r, j) => (
                                <li key={j}>{r}</li>
                              ))}
                            </ul>
                          ) : (
                            <p className="mt-1 text-muted-foreground">(no reply text)</p>
                          )}
                        </div>
                      )
                    )
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </Main>
    </>
  )
}

export const Route = simulatorRoute
