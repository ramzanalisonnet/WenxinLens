'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Plus, Globe } from 'lucide-react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { chatApi } from '@/services/api'
import type { ChatMessage, Language } from '@/types'
import { Navbar } from '@/components/Navbar'

export default function ChatPage() {
  const reduceMotion = useReducedMotion()
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [language, setLanguage] = useState<Language>('en')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const initSession = async () => {
    const { session_id } = await chatApi.createSession(language)
    setSessionId(session_id)
    setMessages([])
  }

  useEffect(() => {
    initSession()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const sendMessage = async () => {
    if (!input.trim() || loading || !sessionId) return
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const response = await chatApi.sendMessage(sessionId, userMsg.content, language)
      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date().toISOString(),
        sources: response.sources,
      }
      setMessages((prev) => [...prev, aiMsg])
    } catch {
      const errMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errMsg])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearSession = async () => {
    if (sessionId) await chatApi.deleteSession(sessionId)
    await initSession()
  }

  const suggestedQuestions = language === 'zh'
    ? ['天坛为什么是圆形的？', '故宫的黄色屋顶有何象征？', '斗拱是什么？', '什么是风水？']
    : [
        'Why is the Temple of Heaven circular?',
        'What does the yellow roof of the Forbidden City symbolize?',
        'What are dougong brackets?',
        'How does feng shui influence Chinese architecture?',
      ]

  return (
    <div className="app-shell min-h-screen flex flex-col">
      <Navbar />

      <div className="app-content flex-1 flex flex-col container-1200 py-12">
        {/* Page header */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: reduceMotion ? 0.01 : 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6 panel-elevated rounded-2xl p-5"
        >
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold tracking-[0.2em] uppercase" style={{ color: '#D4AC0D' }}>AI Guide</span>
              <span className="font-chinese text-xs" style={{ color: 'rgba(212,172,13,0.5)' }}>导游</span>
            </div>
            <h1 className="title-section text-white">Cultural AI Guide</h1>
            <p className="text-body">Ask anything about Chinese ancient architecture</p>
            <div className="flex flex-wrap gap-2 mt-3">
              <span className="px-3 py-1 rounded-full text-[11px] font-semibold" style={{ background: 'rgba(212,172,13,0.15)', border: '1px solid rgba(212,172,13,0.25)', color: '#E4C857' }}>
                Context-aware Answers
              </span>
              <span className="px-3 py-1 rounded-full text-[11px] font-semibold" style={{ background: 'rgba(77,166,212,0.15)', border: '1px solid rgba(77,166,212,0.25)', color: '#87C6E8' }}>
                Bilingual Conversation
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 px-3 py-2 rounded-xl"
              style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.14)' }}>
              <Globe size={13} style={{ color: '#D4AC0D' }} />
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value as Language)}
                className="bg-transparent text-white/80 text-xs focus:outline-none cursor-pointer font-medium"
              >
                <option value="en" style={{ background: '#111122' }}>EN</option>
                <option value="zh" style={{ background: '#111122' }}>中文</option>
              </select>
            </div>
            <button
              onClick={clearSession}
              className="w-9 h-9 flex items-center justify-center rounded-xl transition-all"
              style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.14)', color: 'rgba(255,255,255,0.6)' }}
              title="New conversation"
            >
              <Plus size={16} />
            </button>
          </div>
        </motion.div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto space-y-5 pr-2 min-h-0 pb-4 rounded-2xl panel-elevated p-4" style={{ maxHeight: 'calc(100vh - 320px)' }}>
          {messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: reduceMotion ? 0 : 0.15, duration: reduceMotion ? 0.01 : 0.45, ease: [0.22, 1, 0.36, 1] }}
              className="flex flex-col items-center text-center pt-8 pb-4"
            >
              {/* Bot avatar */}
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5"
                style={{ background: 'rgba(212,172,13,0.08)', border: '1px solid rgba(212,172,13,0.15)' }}>
                <Bot size={28} style={{ color: 'rgba(212,172,13,0.7)' }} />
              </div>
              <p className="text-white/60 text-sm mb-1 font-medium">
                {language === 'zh' ? '您好！我是文心镜AI文化导览员。' : "Hello! I'm your WenxinLens AI cultural guide."}
              </p>
              <p className="text-white/30 text-xs mb-8 max-w-xs">
                {language === 'zh' ? '请问您想了解哪座古建筑？' : 'What ancient architecture would you like to explore?'}
              </p>

              {/* Suggested questions */}
              <div className="flex flex-wrap gap-2 justify-center max-w-xl">
                {suggestedQuestions.map((q) => (
                  <button
                    key={q}
                    onClick={() => setInput(q)}
                    className="text-xs px-3.5 py-2 rounded-xl transition-all text-left hover-rise"
                    style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.12)', color: 'rgba(255,255,255,0.6)' }}
                    onMouseEnter={e => {
                      (e.currentTarget as HTMLElement).style.borderColor = 'rgba(212,172,13,0.25)'
                      ;(e.currentTarget as HTMLElement).style.color = 'rgba(255,255,255,0.85)'
                    }}
                    onMouseLeave={e => {
                      (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.09)'
                      ;(e.currentTarget as HTMLElement).style.color = 'rgba(255,255,255,0.55)'
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: reduceMotion ? 0.01 : 0.32, ease: [0.22, 1, 0.36, 1] }}
                className={`flex items-start gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                {/* Avatar */}
                <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                  msg.role === 'user' ? '' : ''
                }`}
                  style={msg.role === 'user' ? {
                    background: 'linear-gradient(135deg, #C0392B, #A93226)',
                  } : {
                    background: 'rgba(212,172,13,0.12)',
                    border: '1px solid rgba(212,172,13,0.2)',
                  }}>
                  {msg.role === 'user'
                    ? <User size={13} className="text-white" />
                    : <Bot size={13} style={{ color: '#D4AC0D' }} />
                  }
                </div>

                {/* Bubble */}
                <div
                  className="max-w-[80%] px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap"
                  style={msg.role === 'user' ? {
                    background: 'linear-gradient(135deg, #C0392B, #A93226)',
                    borderRadius: '1rem 1rem 0.25rem 1rem',
                    color: '#fff',
                    boxShadow: '0 4px 16px rgba(192,57,43,0.2)',
                  } : {
                    background: 'rgba(255,255,255,0.08)',
                    border: '1px solid rgba(255,255,255,0.12)',
                    borderRadius: '1rem 1rem 1rem 0.25rem',
                    color: 'rgba(255,255,255,0.8)',
                  }}
                >
                  {msg.content}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2 pt-2" style={{ borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                      <p className="text-[10px]" style={{ color: 'rgba(255,255,255,0.3)' }}>
                        Sources: {msg.sources.map(s => s.source).join(', ')}
                      </p>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {loading && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-start gap-3"
            >
              <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0"
                style={{ background: 'rgba(212,172,13,0.12)', border: '1px solid rgba(212,172,13,0.2)' }}>
                <Bot size={13} style={{ color: '#D4AC0D' }} />
              </div>
              <div className="px-4 py-3.5" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '1rem 1rem 1rem 0.25rem' }}>
                <div className="flex items-center gap-1">
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input bar */}
        <div className="mt-4 rounded-2xl overflow-hidden transition-all panel-elevated"
          style={{ background: 'rgba(17,17,34,0.85)', border: '1px solid rgba(255,255,255,0.12)', backdropFilter: 'blur(18px)' }}
          onFocusCapture={e => (e.currentTarget as HTMLElement).style.borderColor = 'rgba(212,172,13,0.2)'}
          onBlurCapture={e => (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.12)'}
        >
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={language === 'zh' ? '提问关于中国古代建筑…' : 'Ask about Chinese ancient architecture…'}
            rows={2}
            className="w-full bg-transparent text-sm resize-none focus:outline-none px-4 pt-3.5 pb-1 leading-relaxed"
            style={{ color: 'rgba(255,255,255,0.85)', caretColor: '#D4AC0D' }}
          />
          <div className="flex items-center justify-between px-4 pb-3">
            <span className="text-[10px] text-white/20">Enter to send · Shift+Enter for new line</span>
            <button
              onClick={sendMessage}
              disabled={!input.trim() || loading}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold transition-all disabled:opacity-30 subtle-shine"
              style={{
                background: input.trim() ? 'linear-gradient(135deg, #C0392B, #A93226)' : 'rgba(255,255,255,0.06)',
                color: '#fff',
              }}
            >
              <Send size={13} />
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}


