'use client'

import { useState } from 'react'
import { advancedApi } from '@/services/api'
import type { HistoricalCharacterData, Language } from '@/types'

interface Props {
  seed?: HistoricalCharacterData
  buildingName: string
  dynasty: string
  language: Language
}

export function HistoricalCharacterChat({ seed, buildingName, dynasty, language }: Props) {
  const [character, setCharacter] = useState('architect')
  const [message, setMessage] = useState('Why was this structure built?')
  const [reply, setReply] = useState(seed?.reply || '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const send = async () => {
    if (!buildingName || !dynasty || !message.trim()) return
    setLoading(true)
    setError('')
    try {
      const res = await advancedApi.historicalCharacterChat({
        building_name: buildingName,
        dynasty,
        character_type: character,
        message,
        language,
      })
      setReply(res.reply)
    } catch (err: any) {
      setError(err?.message || 'Historical character service is temporarily unavailable.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="panel p-6">
      <h3 className="title-card">AI Historical Characters</h3>
      <p className="text-body mt-2">Persona-grounded dialogue with historical role simulation.</p>

      <div className="mt-4" style={{ display: 'grid', gap: '10px' }}>
        <label className="text-caption">Character Role</label>
        <select value={character} onChange={(e) => setCharacter(e.target.value)} className="surface-soft wl-select" style={{ padding: '10px 12px', color: 'var(--text)' }}>
          <option value="emperor">Emperor</option>
          <option value="architect">Architect</option>
          <option value="worker">Worker</option>
          <option value="scholar">Scholar</option>
        </select>

        <label className="text-caption">Question</label>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          rows={3}
          className="surface-soft"
          style={{ padding: '10px 12px', color: 'var(--text)', resize: 'vertical' }}
        />

        <button className="btn btn-primary" disabled={loading} onClick={send}>
          {loading ? 'Thinking...' : 'Ask Character'}
        </button>
      </div>

      {reply && (
        <article className="surface-soft mt-4 p-4" style={{ borderRadius: '12px' }}>
          <p className="text-body">{reply}</p>
        </article>
      )}

      {error && (
        <p className="mt-4" style={{ color: '#FFB3B4' }}>{error}</p>
      )}
    </section>
  )
}
