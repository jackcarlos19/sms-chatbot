import { useEffect, useMemo, useState } from 'react'
import { api, type Slot } from '../api'

function startOfWeek(date: Date): Date {
  const d = new Date(date)
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diff)
  d.setHours(0, 0, 0, 0)
  return d
}

function dayKey(date: Date): string {
  return date.toISOString().slice(0, 10)
}

export default function Slots() {
  const [allSlots, setAllSlots] = useState<Slot[]>([])
  const [weekStart, setWeekStart] = useState(startOfWeek(new Date()))
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const weekEnd = useMemo(() => {
    const end = new Date(weekStart)
    end.setDate(end.getDate() + 6)
    return end
  }, [weekStart])

  const daysAhead = useMemo(() => {
    const diff = weekEnd.getTime() - new Date().getTime()
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24))
    return Math.max(7, days + 1)
  }, [weekEnd])

  const loadSlots = async () => {
    try {
      setError('')
      const rows = await api.getSlots(daysAhead)
      setAllSlots(rows)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load slots')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSlots()
  }, [daysAhead])

  const weekDays = useMemo(() => {
    return Array.from({ length: 7 }).map((_, index) => {
      const day = new Date(weekStart)
      day.setDate(day.getDate() + index)
      return day
    })
  }, [weekStart])

  const grouped = useMemo(() => {
    const map: Record<string, Slot[]> = {}
    for (const slot of allSlots) {
      const key = dayKey(new Date(slot.start_time))
      map[key] = map[key] ? [...map[key], slot] : [slot]
    }
    return map
  }, [allSlots])

  const weekSlots = useMemo(() => {
    return weekDays.flatMap((day) => grouped[dayKey(day)] ?? [])
  }, [grouped, weekDays])

  const availableCount = weekSlots.filter((slot) => slot.is_available).length
  const bookedCount = weekSlots.filter((slot) => !slot.is_available).length
  const canGoPrev = weekStart > startOfWeek(new Date())

  if (loading) {
    return <div className="animate-pulse text-gray-500">Loading slots...</div>
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="flex items-center justify-between rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
          <span>{error}</span>
          <button
            type="button"
            onClick={loadSlots}
            className="rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-gray-200 bg-white p-4">
        <button
          type="button"
          disabled={!canGoPrev}
          onClick={() => {
            const next = new Date(weekStart)
            next.setDate(next.getDate() - 7)
            setWeekStart(next)
          }}
          className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
        >
          ← Previous Week
        </button>
        <p className="text-sm font-medium text-gray-700">
          {weekStart.toLocaleDateString()} - {weekEnd.toLocaleDateString()}
        </p>
        <button
          type="button"
          onClick={() => {
            const next = new Date(weekStart)
            next.setDate(next.getDate() + 7)
            setWeekStart(next)
          }}
          className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
        >
          Next Week →
        </button>
      </div>

      <p className="text-sm text-gray-600">
        {availableCount} available / {bookedCount} booked / {weekSlots.length} total this week
      </p>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-7">
        {weekDays.map((day) => {
          const key = dayKey(day)
          const slots = grouped[key] ?? []
          return (
            <div key={key} className="rounded-lg border border-gray-200 bg-white p-3">
              <h3 className="mb-2 text-sm font-semibold text-gray-900">
                {day.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })}
              </h3>
              {slots.length === 0 ? (
                <p className="text-xs italic text-gray-400">No slots</p>
              ) : (
                <div className="space-y-2">
                  {slots.map((slot) => (
                    <div
                      key={slot.id}
                      className={`rounded-md border-l-4 p-2 text-xs ${
                        slot.is_available
                          ? 'border-l-green-500 bg-white text-gray-800'
                          : 'border-l-red-500 bg-gray-100 text-gray-500 line-through'
                      }`}
                    >
                      {new Date(slot.start_time).toLocaleTimeString([], {
                        hour: 'numeric',
                        minute: '2-digit',
                      })}{' '}
                      -{' '}
                      {new Date(slot.end_time).toLocaleTimeString([], {
                        hour: 'numeric',
                        minute: '2-digit',
                      })}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
