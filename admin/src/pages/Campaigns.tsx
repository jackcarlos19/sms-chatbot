import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { api, type Campaign } from '../api'
import { formatDate } from '../utils'

function statusClass(status: string): string {
  if (status === 'scheduled') return 'bg-blue-100 text-blue-800'
  if (status === 'active') return 'bg-green-100 text-green-800'
  if (status === 'paused') return 'bg-yellow-100 text-yellow-800'
  if (status === 'completed') return 'bg-gray-700 text-white'
  return 'bg-gray-100 text-gray-800'
}

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [name, setName] = useState('')
  const [template, setTemplate] = useState('')
  const [showForm, setShowForm] = useState(true)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [scheduleMap, setScheduleMap] = useState<Record<string, string>>({})

  const loadCampaigns = async () => {
    try {
      setError('')
      const rows = await api.getCampaigns(100, 0)
      setCampaigns(rows)
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
      <div className="space-y-3 rounded-lg border border-gray-200 bg-white p-6">
        <div className="h-6 w-44 animate-pulse rounded bg-gray-200" />
        <div className="h-20 w-full animate-pulse rounded bg-gray-200" />
        <div className="h-20 w-full animate-pulse rounded bg-gray-200" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="flex items-center justify-between rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
          <span>{error}</span>
          <button
            type="button"
            onClick={loadCampaigns}
            className="rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      )}

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Campaigns</h1>
        <button
          type="button"
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          onClick={() => setShowForm((open) => !open)}
        >
          New Campaign
        </button>
      </div>

      {showForm && (
        <form className="space-y-3 rounded-lg border border-gray-200 bg-white p-4" onSubmit={onCreate}>
          <input
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Campaign name"
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900"
            required
          />
          <textarea
            value={template}
            onChange={(event) => setTemplate(event.target.value)}
            placeholder="Message template"
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900"
            rows={4}
            required
          />
          <p className="text-xs text-gray-500">Use {'{first_name}'} and {'{last_name}'} for personalization</p>
          <button
            type="submit"
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Create Campaign
          </button>
        </form>
      )}

      {campaigns.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-500">
          No campaigns yet. Create one above.
        </div>
      ) : (
        <div className="space-y-4">
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
              <article key={campaign.id} className="rounded-lg border border-gray-200 bg-white p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h2 className="text-lg font-semibold text-gray-900">{campaign.name}</h2>
                  <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${statusClass(campaign.status)}`}>
                    {campaign.status}
                  </span>
                </div>
                <p className="mt-1 text-sm text-gray-500">Created {formatDate(campaign.created_at)}</p>
                <p className="mt-3 text-sm text-gray-700">
                  Recipients: {campaign.total_recipients} | Sent: {campaign.sent_count} | Delivered:{' '}
                  {campaign.delivered_count} | Failed: {campaign.failed_count} | Replies:{' '}
                  {campaign.reply_count}
                </p>

                {campaign.total_recipients > 0 && (
                  <div className="mt-3 h-3 w-full overflow-hidden rounded bg-gray-100">
                    <div className="flex h-full">
                      <div className="bg-green-500" style={{ width: `${deliveredWidth}%` }} />
                      <div className="bg-blue-500" style={{ width: `${sentPendingWidth}%` }} />
                      <div className="bg-red-500" style={{ width: `${failedWidth}%` }} />
                    </div>
                  </div>
                )}

                <div className="mt-4 flex flex-wrap items-center gap-2">
                  {campaign.status === 'draft' && (
                    <>
                      <input
                        type="datetime-local"
                        value={scheduleMap[campaign.id] || ''}
                        onChange={(event) =>
                          setScheduleMap((prev) => ({ ...prev, [campaign.id]: event.target.value }))
                        }
                        className="rounded-md border border-gray-300 px-3 py-2 text-sm"
                      />
                      <button
                        type="button"
                        className="rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
                        onClick={() =>
                          transitionCampaign(
                            campaign.id,
                            'scheduled',
                            scheduleMap[campaign.id] ? new Date(scheduleMap[campaign.id]).toISOString() : undefined,
                          )
                        }
                      >
                        Schedule
                      </button>
                    </>
                  )}
                  {campaign.status === 'scheduled' && (
                    <button
                      type="button"
                      className="rounded-md bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700"
                      onClick={() => transitionCampaign(campaign.id, 'active')}
                    >
                      Activate
                    </button>
                  )}
                  {campaign.status === 'active' && (
                    <button
                      type="button"
                      className="rounded-md bg-yellow-600 px-3 py-2 text-sm font-medium text-white hover:bg-yellow-700"
                      onClick={() => transitionCampaign(campaign.id, 'paused')}
                    >
                      Pause
                    </button>
                  )}
                  {campaign.status === 'paused' && (
                    <button
                      type="button"
                      className="rounded-md bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700"
                      onClick={() => transitionCampaign(campaign.id, 'active')}
                    >
                      Resume
                    </button>
                  )}
                </div>
              </article>
            )
          })}
        </div>
      )}
    </div>
  )
}
