import { useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { api } from '../api'

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
        <div key={message.id} className="text-center">
          <div className="inline-block rounded-xl bg-red-100 px-3 py-2 text-sm text-red-700">
            {message.body}
          </div>
          <p className="mt-1 text-xs text-gray-400">{new Date(message.ts).toLocaleTimeString()}</p>
        </div>
      )
    }

    const isUser = message.role === 'user'
    return (
      <div key={message.id} className={isUser ? 'text-right' : 'text-left'}>
        <div
          className={`inline-block max-w-[80%] px-4 py-2 text-sm ${
            isUser
              ? 'rounded-2xl rounded-br-sm bg-blue-500 text-white'
              : 'rounded-2xl rounded-bl-sm bg-gray-200 text-gray-900'
          }`}
        >
          {message.body}
        </div>
        <p className="mt-1 text-xs text-gray-400">{new Date(message.ts).toLocaleTimeString()}</p>
      </div>
    )
  }

  return (
    <div className="flex min-h-[calc(100vh-9rem)] items-center justify-center p-2">
      <div className="flex h-[80vh] w-full max-w-lg flex-col overflow-hidden rounded-2xl border border-gray-300 bg-white shadow-sm">
        <div className="space-y-3 border-b border-gray-200 p-4">
          <div className="flex items-center justify-between gap-2">
            <input
              type="text"
              value={phone}
              onChange={(event) => setPhone(event.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
            <span className="rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-800">
              {conversationState}
            </span>
          </div>
          <button
            type="button"
            onClick={() => setMessages([])}
            className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
          >
            Clear Chat
          </button>
        </div>

        <div className="flex-1 space-y-3 overflow-y-auto bg-gray-50 p-4">
          {messages.map(renderMessage)}
          {typingMessage && renderMessage(typingMessage)}
          <div ref={bottomRef} />
        </div>

        <form className="flex items-center gap-2 border-t border-gray-200 p-4" onSubmit={onSend}>
          <input
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            placeholder="Type a message..."
            disabled={sending}
          />
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  )
}
