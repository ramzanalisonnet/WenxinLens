'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { SendHorizontal, MessageCircle, Bot } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { chatApi } from '@/services/api'
import type { ChatMessage } from '@/types'

interface ChatPanelProps {
  buildingContext?: string
  buildingName?: string
  language?: 'en' | 'zh'
}

export function ChatPanel({ buildingContext, buildingName, language = 'en' }: ChatPanelProps) {
  const [sessionId, setSessionId]   = useState<string | null>(null)
  const [messages,  setMessages]    = useState<ChatMessage[]>([])
  const [input,     setInput]       = useState('')
  const [loading,   setLoading]     = useState(false)
  const bottomRef   = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let cancelled = false
    chatApi.createSession(language).then((s) => {
      if (!cancelled) setSessionId(s.session_id)
    }).catch(console.error)
    return () => { cancelled = true }
  }, [buildingContext, language])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    const text = input.trim()
    if (!text || !sessionId || loading) return
    setInput('')

    const userMsg: ChatMessage = { id: Date.now().toString(), role: 'user', content: text, timestamp: new Date().toISOString() }
    setMessages((prev) => [...prev, userMsg])
    setLoading(true)

    try {
      const res = await chatApi.sendMessage(sessionId, text, language)
      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: res.message,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch {
      setMessages((prev) => [
        ...prev,
        { id: (Date.now() + 1).toString(), role: 'assistant', content: 'Sorry, an error occurred. Please try again.', timestamp: new Date().toISOString() },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="flex flex-col h-[480px] rounded-2xl overflow-hidden panel-elevated"
      style={{ background: 'rgba(8,8,15,0.76)', border: '1px solid rgba(255,255,255,0.11)', backdropFilter: 'blur(20px)' }}
    >
      {/* Header */}
      <div className="flex items-center gap-2.5 px-4 py-3.5 flex-shrink-0"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', background: 'rgba(17,17,34,0.5)' }}>
        <div className="w-7 h-7 rounded-lg flex items-center justify-center"
          style={{ background: 'rgba(212,172,13,0.12)', border: '1px solid rgba(212,172,13,0.2)' }}>
          <MessageCircle size={14} style={{ color: '#D4AC0D' }} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="type-body font-semibold text-white truncate">
            {buildingName ? `Ask about ${buildingName}` : 'Cultural Guide'}
          </p>
          <p className="text-[10px] text-white/30 font-medium">AI-powered · {language === 'zh' ? '中文' : 'English'}</p>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[10px] text-white/30">Active</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        {messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center h-full gap-3 text-center"
          >
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center"
              style={{ background: 'rgba(212,172,13,0.08)', border: '1px solid rgba(212,172,13,0.15)' }}>
              <Bot size={22} style={{ color: 'rgba(212,172,13,0.6)' }} />
            </div>
            <p className="text-white/25 text-xs leading-relaxed max-w-[200px]">
              {language === 'zh' ? '有什么想了解的？' : 'Ask me anything about this architectural site!'}
            </p>
          </motion.div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} gap-2.5`}
            >
              {msg.role === 'assistant' && (
                <div className="w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center mt-0.5"
                  style={{ background: 'rgba(212,172,13,0.12)', border: '1px solid rgba(212,172,13,0.2)' }}>
                  <Bot size={12} style={{ color: '#D4AC0D' }} />
                </div>
              )}
              <div
                className="max-w-[85%] px-3.5 py-2.5 text-sm leading-relaxed"
                style={msg.role === 'user' ? {
                  background: 'linear-gradient(135deg, #C0392B, #A93226)',
                  borderRadius: '1rem 1rem 0.25rem 1rem',
                  color: '#fff',
                  boxShadow: '0 4px 16px rgba(192,57,43,0.25)',
                } : {
                  background: 'rgba(255,255,255,0.06)',
                  border: '1px solid rgba(255,255,255,0.11)',
                  borderRadius: '1rem 1rem 1rem 0.25rem',
                  color: 'rgba(255,255,255,0.75)',
                }}
              >
                {msg.role === 'assistant' ? (
                  <ReactMarkdown
                    components={{
                      p: ({ children }) => <p style={{ margin: '0 0 8px 0' }}>{children}</p>,
                      ul: ({ children }) => <ul style={{ margin: '0 0 8px 0', paddingLeft: 16 }}>{children}</ul>,
                      li: ({ children }) => <li style={{ marginBottom: 4 }}>{children}</li>,
                      strong: ({ children }) => <strong style={{ color: '#fff' }}>{children}</strong>,
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                ) : (
                  msg.content
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {loading && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-start gap-2.5"
          >
            <div className="w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center mt-0.5"
              style={{ background: 'rgba(212,172,13,0.12)', border: '1px solid rgba(212,172,13,0.2)' }}>
              <Bot size={12} style={{ color: '#D4AC0D' }} />
            </div>
            <div className="px-3.5 py-3" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '1rem 1rem 1rem 0.25rem' }}>
              <div className="flex items-center gap-1">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
            </div>
          </motion.div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-3 flex-shrink-0" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="flex items-center gap-2 rounded-xl px-3 py-2 transition-all"
          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)' }}
          onFocusCapture={(e: React.FocusEvent<HTMLDivElement>) => (e.currentTarget as HTMLElement).style.borderColor = 'rgba(212,172,13,0.25)'}
          onBlurCapture={(e: React.FocusEvent<HTMLDivElement>) => (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.12)'}
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()}
            placeholder={language === 'zh' ? '输入问题…' : 'Ask a question…'}
            disabled={!sessionId}
            className="flex-1 bg-transparent text-sm outline-none min-w-0 disabled:opacity-40"
            style={{ color: 'rgba(255,255,255,0.85)' }}
          />
          <button
            onClick={send}
            disabled={!input.trim() || !sessionId || loading}
            className="w-7 h-7 flex items-center justify-center rounded-lg flex-shrink-0 transition-all disabled:opacity-30"
            style={{ background: input.trim() ? 'linear-gradient(135deg, #C0392B, #A93226)' : 'rgba(255,255,255,0.05)' }}
          >
            <SendHorizontal size={14} className="text-white" />
          </button>
        </div>
      </div>
    </div>
  )
}
