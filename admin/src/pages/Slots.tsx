import { useEffect, useMemo, useState } from 'react'
import { api, type Slot } from '../api'
import { Card, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'

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
    return (
      <div className="space-y-6">
        <Card className="animate-pulse"><CardContent className="p-6 h-16" /></Card>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-7">
          {Array.from({ length: 7 }).map((_, i) => (
            <Card key={i} className="animate-pulse"><CardContent className="p-4 h-64" /></Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Availability</h1>
      </div>

      {error && (
        <div className="flex items-center justify-between rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-destructive">
          <span className="text-sm font-medium">{error}</span>
          <Button variant="danger" size="sm" onClick={loadSlots}>
            Retry
          </Button>
        </div>
      )}

      <Card>
        <CardContent className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              disabled={!canGoPrev}
              onClick={() => {
                const next = new Date(weekStart)
                next.setDate(next.getDate() - 7)
                setWeekStart(next)
              }}
            >
              ← Previous
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setWeekStart(startOfWeek(new Date()))
              }}
            >
              Today
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                const next = new Date(weekStart)
                next.setDate(next.getDate() + 7)
                setWeekStart(next)
              }}
            >
              Next →
            </Button>
          </div>
          
          <div className="text-sm font-medium text-foreground">
            {weekStart.toLocaleDateString([], { month: 'long', day: 'numeric', year: 'numeric' })} -{' '}
            {weekEnd.toLocaleDateString([], { month: 'long', day: 'numeric', year: 'numeric' })}
          </div>
          
          <div className="flex items-center gap-3 text-xs font-medium text-muted-foreground">
            <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-green-500"></div> {availableCount} Available</span>
            <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-muted-foreground"></div> {bookedCount} Booked</span>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-7">
        {weekDays.map((day) => {
          const key = dayKey(day)
          const slots = grouped[key] ?? []
          const isToday = dayKey(new Date()) === key
          
          return (
            <Card key={key} className={`border ${isToday ? 'border-primary shadow-sm' : 'border-border'}`}>
              <div className={`p-3 text-center border-b border-border ${isToday ? 'bg-primary/5 text-primary' : 'bg-muted/30 text-foreground'}`}>
                <h3 className="text-sm font-semibold">
                  {day.toLocaleDateString([], { weekday: 'short' })}
                </h3>
                <p className="text-xs mt-0.5 opacity-80">
                  {day.toLocaleDateString([], { month: 'short', day: 'numeric' })}
                </p>
              </div>
              <CardContent className="p-2 space-y-2 max-h-[600px] overflow-y-auto min-h-[100px]">
                {slots.length === 0 ? (
                  <div className="flex h-full items-center justify-center py-4">
                    <p className="text-xs text-muted-foreground italic">No slots</p>
                  </div>
                ) : (
                  slots.map((slot) => (
                    <div
                      key={slot.id}
                      className={`rounded-md p-2 text-xs font-medium border-l-2 transition-colors ${
                        slot.is_available
                          ? 'border-l-green-500 bg-green-500/5 text-foreground hover:bg-green-500/10'
                          : 'border-l-muted-foreground bg-muted text-muted-foreground line-through opacity-70'
                      }`}
                    >
                      {new Date(slot.start_time).toLocaleTimeString([], {
                        hour: 'numeric',
                        minute: '2-digit',
                      })}
                      <span className="opacity-50 mx-1">-</span>
                      {new Date(slot.end_time).toLocaleTimeString([], {
                        hour: 'numeric',
                        minute: '2-digit',
                      })}
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
