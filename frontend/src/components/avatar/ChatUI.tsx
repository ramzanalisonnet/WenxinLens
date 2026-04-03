'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import type { AvatarMessage } from '@/types'

interface ChatUIProps {
  messages: AvatarMessage[]
  onSend: (text: string) => Promise<void>
  disabled?: boolean
}

export function ChatUI({ messages, onSend, disabled = false }: ChatUIProps) {
  const [draft, setDraft] = useState('')

  const submit = async () => {
    const text = draft.trim()
    if (!text || disabled) return
    setDraft('')
    await onSend(text)
  }

  return (
    <section className="panel p-5" style={{ display: 'grid', gap: 12 }}>
      <h3 className="title-card">Conversation</h3>

      <div className="surface-soft" style={{ borderRadius: 12, minHeight: 240, maxHeight: 280, overflowY: 'auto', padding: 12 }}>
        {messages.length === 0 && <p className="text-caption">Ask your first question to start the conversation.</p>}
        {messages.map((item) => (
          <article
            key={item.id}
            style={{
              marginBottom: 10,
              display: 'grid',
              justifyItems: item.role === 'user' ? 'end' : 'start',
            }}
          >
            <div
              style={{
                maxWidth: '86%',
                padding: '10px 12px',
                borderRadius: 10,
                background: item.role === 'user' ? 'rgba(0, 209, 178, 0.14)' : 'rgba(255, 255, 255, 0.06)',
                border: '1px solid rgba(230, 234, 242, 0.16)',
              }}
            >
              {item.role === 'assistant' ? (
                <div style={{ fontSize: 14, lineHeight: 1.6 }}>
                  <ReactMarkdown
                    components={{
                      p: ({ children }) => <p style={{ margin: '0 0 8px 0' }}>{children}</p>,
                      ul: ({ children }) => <ul style={{ margin: '0 0 8px 0', paddingLeft: 16 }}>{children}</ul>,
                      li: ({ children }) => <li style={{ marginBottom: 4 }}>{children}</li>,
                      strong: ({ children }) => <strong style={{ color: 'var(--text)' }}>{children}</strong>,
                    }}
                  >
                    {item.content}
                  </ReactMarkdown>
                </div>
              ) : (
                <p style={{ margin: 0, fontSize: 14 }}>{item.content}</p>
              )}
            </div>
          </article>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 10 }}>
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask about architecture, symbolism, materials..."
          className="surface-soft"
          style={{ padding: '12px 14px', color: 'var(--text)' }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') submit()
          }}
          disabled={disabled}
        />
        <button onClick={submit} className="btn btn-primary" disabled={disabled || !draft.trim()}>
          Send
        </button>
      </div>
    </section>
  )
}
