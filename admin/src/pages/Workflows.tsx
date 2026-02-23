import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { api, type ReminderWorkflow } from '../api'
import { formatDate } from '../utils'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Input } from '../components/ui/Input'

export default function Workflows() {
  const [workflows, setWorkflows] = useState<ReminderWorkflow[]>([])
  const [name, setName] = useState('')
  const [minutesBefore, setMinutesBefore] = useState('60')
  const [template, setTemplate] = useState('')
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const load = async () => {
    try {
      setError('')
      setWorkflows(await api.getReminderWorkflows())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load workflows')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const onCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!name.trim() || !template.trim()) return
    try {
      await api.createReminderWorkflow({
        name: name.trim(),
        appointment_status: status || undefined,
        minutes_before: Number(minutesBefore),
        template: template.trim(),
      })
      setName('')
      setMinutesBefore('60')
      setTemplate('')
      setStatus('')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create workflow')
    }
  }

  const toggle = async (workflow: ReminderWorkflow) => {
    try {
      await api.updateReminderWorkflow(workflow.id, { is_active: !workflow.is_active })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update workflow')
    }
  }

  if (loading) {
    return <Card className="animate-pulse"><CardContent className="p-6 h-40" /></Card>
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight text-foreground">Reminder Workflows</h1>
      {error && <div className="rounded border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</div>}

      <Card>
        <CardHeader><CardTitle className="text-base">Create Workflow</CardTitle></CardHeader>
        <CardContent>
          <form className="grid grid-cols-1 gap-3 md:grid-cols-4" onSubmit={onCreate}>
            <Input value={name} onChange={(event) => setName(event.target.value)} placeholder="Name" required />
            <Input value={minutesBefore} onChange={(event) => setMinutesBefore(event.target.value)} placeholder="Minutes before" type="number" required />
            <Input value={status} onChange={(event) => setStatus(event.target.value)} placeholder="Appointment status (optional)" />
            <Button type="submit">Create</Button>
            <textarea
              value={template}
              onChange={(event) => setTemplate(event.target.value)}
              placeholder="Reminder template"
              className="md:col-span-4 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              rows={3}
              required
            />
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base">Existing Workflows</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          {workflows.length === 0 ? (
            <p className="text-sm text-muted-foreground">No workflows configured.</p>
          ) : workflows.map((workflow) => (
            <div key={workflow.id} className="flex flex-wrap items-center justify-between gap-2 rounded border border-border px-3 py-2">
              <div>
                <p className="text-sm font-medium">{workflow.name}</p>
                <p className="text-xs text-muted-foreground">
                  {workflow.minutes_before} min before · {workflow.appointment_status || 'all statuses'} · Created {formatDate(workflow.created_at)}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={workflow.is_active ? 'success' : 'secondary'}>
                  {workflow.is_active ? 'active' : 'inactive'}
                </Badge>
                <Button size="sm" variant="secondary" onClick={() => toggle(workflow)}>
                  {workflow.is_active ? 'Disable' : 'Enable'}
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
