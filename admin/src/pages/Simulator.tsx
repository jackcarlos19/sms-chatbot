import { useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { api } from '../api'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Input } from '../components/ui/Input'
import { Button } from '../components/ui/Button'

type ChatMessage = {
  id: string
  role: 'user' | 'bot' | 'system'
  body: string
  ts: string
}

export default function Simulator() {
  const [phone, setPhone] = useState('+15551234567')
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [conversationState, setConversationState] = useState('idle')
  const [sending, setSending] = useState(false)
  const bottomRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, sending])

  const nowIso = () => new Date().toISOString()

  const typingMessage = useMemo<ChatMessage | null>(
    () =>
      sending
        ? { id: 'typing', role: 'bot', body: '...', ts: nowIso() }
        : null,
    [sending],
  )

  const onSend = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!input.trim() || sending) return

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      body: input.trim(),
      ts: nowIso(),
    }
    const textToSend = input.trim()
    setInput('')
    setMessages((prev) => [...prev, userMsg])
    setSending(true)

    try {
      const response = await api.simulate(phone, textToSend)
      setConversationState(response.conversation_state || 'idle')
      const responses = response.responses || []
      const botMessages: ChatMessage[] = responses.map((body) => ({
        id: crypto.randomUUID(),
        role: 'bot',
        body,
        ts: nowIso(),
      }))
      if (botMessages.length === 0) {
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: 'system',
            body: 'No response returned from simulator.',
            ts: nowIso(),
          },
        ])
      } else {
        setMessages((prev) => [...prev, ...botMessages])
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Simulator request failed'
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'system',
          body: message,
          ts: nowIso(),
        },
      ])
    } finally {
      setSending(false)
    }
  }

  const renderMessage = (message: ChatMessage) => {
    if (message.role === 'system') {
      return (
        <div key={message.id} className="text-center my-4">
          <div className="inline-block rounded-lg bg-destructive/10 px-3 py-1.5 text-xs font-medium text-destructive">
            {message.body}
          </div>
          <p className="mt-1 text-[10px] text-muted-foreground">{new Date(message.ts).toLocaleTimeString()}</p>
        </div>
      )
    }

    const isUser = message.role === 'user'
    return (
      <div key={message.id} className={`flex w-full flex-col ${isUser ? 'items-end' : 'items-start'} my-2`}>
        <div
          className={`relative max-w-[80%] px-4 py-2.5 text-sm shadow-sm ${
            isUser
              ? 'rounded-2xl rounded-br-sm bg-blue-600 text-white dark:bg-blue-600'
              : 'rounded-2xl rounded-bl-sm bg-muted text-foreground'
          }`}
        >
          {message.body}
        </div>
        <p className="mt-1.5 px-1 text-[11px] font-medium text-muted-foreground">
          {new Date(message.ts).toLocaleTimeString()}
        </p>
      </div>
    )
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] items-center justify-center pt-2 pb-6">
      <Card className="flex h-full w-full max-w-lg flex-col overflow-hidden shadow-lg border-border">
        <CardHeader className="border-b border-border bg-card/50 p-4 backdrop-blur-sm">
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1">
              <Input
                type="text"
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                className="h-8 w-full max-w-[180px] bg-background text-sm"
              />
            </div>
            <div className="flex items-center gap-3">
              <Badge variant={conversationState === 'idle' ? 'secondary' : 'default'} className="hidden sm:inline-flex">
                {conversationState.replace('_', ' ')}
              </Badge>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setMessages([])}
                className="h-8 text-xs font-medium text-muted-foreground"
              >
                Clear
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="flex-1 overflow-y-auto bg-background/50 p-4 scroll-smooth">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center text-muted-foreground">
              <div className="mb-3 rounded-full bg-muted p-3">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                  <path d="M3.27 6.96 12 12.01l8.73-5.05" />
                  <path d="M12 22.08V12" />
                </svg>
              </div>
              <p className="text-sm font-medium">Simulator Ready</p>
              <p className="text-xs">Type a message below to start</p>
            </div>
          ) : (
            <>
              <div className="space-y-1">
                {messages.map(renderMessage)}
                {typingMessage && renderMessage(typingMessage)}
              </div>
              <div ref={bottomRef} className="h-4" />
            </>
          )}
        </CardContent>

        <div className="border-t border-border bg-card p-4">
          <form className="flex items-center gap-2" onSubmit={onSend}>
            <Input
              type="text"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Type a message..."
              disabled={sending}
              className="flex-1 rounded-full bg-muted/50 px-4 focus-visible:bg-background"
            />
            <Button
              type="submit"
              disabled={sending || !input.trim()}
              className="rounded-full px-5 shadow-none"
            >
              Send
            </Button>
          </form>
        </div>
      </Card>
    </div>
  )
}
