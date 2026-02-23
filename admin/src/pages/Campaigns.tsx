import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { api, type Campaign } from '../api'
import { formatDate } from '../utils'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Textarea } from '../components/ui/Textarea'

function getStatusVariant(status: string): "default" | "success" | "warning" | "secondary" | "outline" {
  if (status === 'scheduled') return 'default'
  if (status === 'active') return 'success'
  if (status === 'paused') return 'warning'
  if (status === 'completed') return 'secondary'
  return 'outline'
}

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [name, setName] = useState('')
  const [template, setTemplate] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [scheduleMap, setScheduleMap] = useState<Record<string, string>>({})

  const loadCampaigns = async () => {
    try {
      setError('')
      const response = await api.getCampaigns(100, 0)
      setCampaigns(response.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load campaigns')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCampaigns()
  }, [])

  const onCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!name.trim() || !template.trim()) return
    try {
      setError('')
      await api.createCampaign({
        name: name.trim(),
        message_template: template.trim(),
        recipient_filter: {},
      })
      setName('')
      setTemplate('')
      setShowForm(false)
      await loadCampaigns()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create campaign')
    }
  }

  const transitionCampaign = async (campaignId: string, status: string, scheduled_at?: string) => {
    try {
      setError('')
      await api.updateCampaign(campaignId, { status, scheduled_at })
      await loadCampaigns()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update campaign')
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-full animate-pulse rounded bg-muted max-w-[200px]" />
        <Card className="animate-pulse"><CardContent className="p-6 h-32" /></Card>
        <Card className="animate-pulse"><CardContent className="p-6 h-32" /></Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Campaigns</h1>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : 'New Campaign'}
        </Button>
      </div>

      {error && (
        <div className="flex items-center justify-between rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-destructive">
          <span className="text-sm font-medium">{error}</span>
          <Button variant="danger" size="sm" onClick={loadCampaigns}>
            Retry
          </Button>
        </div>
      )}

      {showForm && (
        <Card className="border-primary/20 bg-primary/5">
          <CardHeader>
            <CardTitle className="text-lg">Create New Campaign</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={onCreate}>
              <div className="space-y-1">
                <label className="text-sm font-medium text-foreground">Campaign Name</label>
                <Input
                  type="text"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="e.g. Spring Promo"
                  className="bg-background"
                  required
                />
              </div>
              <div className="space-y-1">
                <div className="flex justify-between">
                  <label className="text-sm font-medium text-foreground">Message Template</label>
                  <span
                    className={`text-xs ${
                      template.length > 320 ? 'font-semibold text-destructive' : 'text-muted-foreground'
                    }`}
                  >
                    {template.length}/320
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">Use {'{first_name}'}, {'{last_name}'}</p>
                <Textarea
                  value={template}
                  onChange={(event) => setTemplate(event.target.value)}
                  placeholder="Hi {first_name}, time for your spring tune-up!"
                  rows={4}
                  required
                />
              </div>
              <div className="flex justify-end pt-2">
                <Button type="submit">Create Campaign</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {campaigns.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center p-12 text-center text-muted-foreground">
            <p className="text-sm font-medium">No campaigns yet</p>
            <p className="text-xs mt-1">Create one using the button above</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6">
          {campaigns.map((campaign) => {
            const deliveredWidth =
              campaign.total_recipients > 0
                ? (campaign.delivered_count / campaign.total_recipients) * 100
                : 0
            const failedWidth =
              campaign.total_recipients > 0
                ? (campaign.failed_count / campaign.total_recipients) * 100
                : 0
            const sentPending = Math.max(
              0,
              campaign.sent_count - campaign.delivered_count - campaign.failed_count,
            )
            const sentPendingWidth =
              campaign.total_recipients > 0 ? (sentPending / campaign.total_recipients) * 100 : 0

            return (
              <Card key={campaign.id}>
                <CardContent className="p-6">
                  <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border pb-4">
                    <div>
                      <h2 className="text-lg font-semibold text-foreground flex items-center gap-3">
                        {campaign.name}
                        <Badge variant={getStatusVariant(campaign.status)}>
                          {campaign.status}
                        </Badge>
                      </h2>
                      <p className="mt-1 text-xs text-muted-foreground">Created {formatDate(campaign.created_at)}</p>
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                      {campaign.status === 'draft' && (
                        <div className="flex items-center gap-2">
                          <Input
                            type="datetime-local"
                            value={scheduleMap[campaign.id] || ''}
                            onChange={(event) =>
                              setScheduleMap((prev) => ({ ...prev, [campaign.id]: event.target.value }))
                            }
                            className="h-9 w-auto text-xs"
                          />
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() =>
                              transitionCampaign(
                                campaign.id,
                                'scheduled',
                                scheduleMap[campaign.id] ? new Date(scheduleMap[campaign.id]).toISOString() : undefined,
                              )
                            }
                          >
                            Schedule
                          </Button>
                        </div>
                      )}
                      {campaign.status === 'scheduled' && (
                        <Button variant="secondary" size="sm" onClick={() => transitionCampaign(campaign.id, 'active')}>
                          Activate Now
                        </Button>
                      )}
                      {campaign.status === 'active' && (
                        <Button variant="secondary" size="sm" onClick={() => transitionCampaign(campaign.id, 'paused')}>
                          Pause
                        </Button>
                      )}
                      {campaign.status === 'paused' && (
                        <Button variant="primary" size="sm" onClick={() => transitionCampaign(campaign.id, 'active')}>
                          Resume
                        </Button>
                      )}
                    </div>
                  </div>

                  <div className="pt-4">
                    <div className="flex justify-between text-sm font-medium mb-2">
                      <span className="text-foreground">{campaign.total_recipients} Recipients</span>
                      <span className="text-muted-foreground">{campaign.reply_count} Replies</span>
                    </div>

                    {campaign.total_recipients > 0 ? (
                      <div className="h-2 w-full overflow-hidden rounded-full bg-muted flex">
                        <div className="bg-green-500 transition-all duration-500" style={{ width: `${deliveredWidth}%` }} />
                        <div className="bg-blue-500 transition-all duration-500" style={{ width: `${sentPendingWidth}%` }} />
                        <div className="bg-red-500 transition-all duration-500" style={{ width: `${failedWidth}%` }} />
                      </div>
                    ) : (
                      <div className="h-2 w-full rounded-full bg-muted" />
                    )}
                    
                    <div className="flex justify-between text-xs text-muted-foreground mt-2">
                      <span>{campaign.delivered_count} Delivered</span>
                      <span>{campaign.failed_count} Failed</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
