'use client'

import dynamic from 'next/dynamic'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Navbar } from '@/components/Navbar'
import { ChatUI } from '@/components/avatar/ChatUI'
import { VoiceInput } from '@/components/avatar/VoiceInput'
import { avatarApi } from '@/services/api'
import type { AvatarLipSyncCue, AvatarMessage, AvatarState, Language } from '@/types'

const AvatarViewer = dynamic(
  () => import('@/components/avatar/AvatarViewer').then((m) => m.AvatarViewer),
  { ssr: false }
)

const CHARACTER_OPTIONS = [
  { value: 'guide', label: 'Guide' },
  { value: 'architect', label: 'Architect' },
  { value: 'scholar', label: 'Scholar' },
  { value: 'emperor', label: 'Emperor' },
] as const

export default function AvatarPage() {
  const [avatarState, setAvatarState] = useState<AvatarState>('IDLE')
  const [language, setLanguage] = useState<Language>('en')
  const [character, setCharacter] = useState('architect')
  const [buildingName, setBuildingName] = useState('Temple of Heaven')
  const [dynasty, setDynasty] = useState('Ming')
  const [visemeLevel, setVisemeLevel] = useState(0)
  const [visemeCode, setVisemeCode] = useState('X')
  const [busy, setBusy] = useState(false)
  const [messages, setMessages] = useState<AvatarMessage[]>([])

  const wsRef = useRef<WebSocket | null>(null)
  const rafRef = useRef<number | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const audioCtxRef = useRef<AudioContext | null>(null)

  const sendWs = (type: string, payload: Record<string, unknown>) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return
    ws.send(JSON.stringify({ type, payload }))
  }

  useEffect(() => {
    const ws = new WebSocket(avatarApi.websocketUrl())
    wsRef.current = ws
    ws.onmessage = (event) => {
      try {
        const packet = JSON.parse(event.data)
        if (packet?.type === 'listening') setAvatarState('LISTENING')
        if (packet?.type === 'thinking') setAvatarState('THINKING')
        if (packet?.type === 'speaking') setAvatarState('SPEAKING')
      } catch {
        // ignore malformed event payloads
      }
    }

    return () => {
      ws.close()
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      if (audioCtxRef.current) audioCtxRef.current.close()
    }
  }, [])

  const addMessage = (role: 'user' | 'assistant', content: string) => {
    setMessages((prev) => [
      ...prev,
      {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        role,
        content,
        timestamp: new Date().toISOString(),
      },
    ])
  }

  const playSpeech = async (text: string) => {
    const [blob, lipsync] = await Promise.all([
      avatarApi.tts({ text, character_type: character, language }),
      avatarApi.lipsync({ text }),
    ])

    const url = URL.createObjectURL(blob)
    const cues: AvatarLipSyncCue[] = lipsync.visemes || []

    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }

    const audio = new Audio(url)
    audioRef.current = audio
    setAvatarState('SPEAKING')
    sendWs('audio_ready', { state: 'SPEAKING' })

    const audioCtx = audioCtxRef.current ?? new AudioContext()
    audioCtxRef.current = audioCtx
    const source = audioCtx.createMediaElementSource(audio)
    const analyser = audioCtx.createAnalyser()
    analyser.fftSize = 64
    source.connect(analyser)
    analyser.connect(audioCtx.destination)

    const data = new Uint8Array(analyser.frequencyBinCount)
    const tick = () => {
      analyser.getByteFrequencyData(data)
      const avg = data.reduce((sum, value) => sum + value, 0) / data.length

      const elapsedMs = audio.currentTime * 1000
      const cue = cues.find((item) => elapsedMs >= item.start_ms && elapsedMs <= item.end_ms) || null
      const cueBoost = cue && cue.viseme !== 'X' ? 0.25 : 0
      setVisemeCode(cue?.viseme || 'X')
      setVisemeLevel(Math.min(1, avg / 80 + cueBoost))

      rafRef.current = requestAnimationFrame(tick)
    }

    audio.onplay = () => {
      if (audioCtx.state === 'suspended') {
        void audioCtx.resume()
      }
      tick()
    }

    audio.onended = () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      setVisemeLevel(0)
      setVisemeCode('X')
      setAvatarState('IDLE')
      URL.revokeObjectURL(url)
    }

    await audio.play()
  }

  const sendMessage = async (text: string) => {
    const clean = text.trim()
    if (!clean || busy) return

    setBusy(true)
    addMessage('user', clean)
    setAvatarState('THINKING')
    sendWs('user_input', { text: clean })

    try {
      const reply = await avatarApi.chat({
        building_name: buildingName,
        dynasty,
        character_type: character,
        message: clean,
        language,
      })
      addMessage('assistant', reply.reply)
      await playSpeech(reply.reply)
    } catch (err: any) {
      addMessage('assistant', err?.message || 'Avatar chat is temporarily unavailable.')
      setAvatarState('IDLE')
    } finally {
      setBusy(false)
    }
  }

  const onVoiceInput = async (audioBlob: Blob) => {
    setAvatarState('LISTENING')
    try {
      const result = await avatarApi.stt(audioBlob, language)
      if (!result.text) {
        setAvatarState('IDLE')
        return
      }
      await sendMessage(result.text)
    } catch (err: any) {
      addMessage('assistant', err?.message || 'Voice transcription failed.')
      setAvatarState('IDLE')
    }
  }

  const stateLabel = useMemo(() => {
    if (avatarState === 'THINKING') return 'Thinking'
    if (avatarState === 'LISTENING') return 'Listening'
    if (avatarState === 'SPEAKING') return 'Speaking'
    return 'Idle'
  }, [avatarState])

  return (
    <div className="app-shell min-h-screen">
      <Navbar />
      <main className="app-content container-1200 py-10" style={{ display: 'grid', gap: 16 }}>
        <section className="panel p-6" style={{ display: 'grid', gap: 12 }}>
          <h1 className="title-section">Real-Time AI Avatar</h1>
          <p className="text-body">
            Interactive 3D cultural guide with text and voice conversation, character personality mapping, and speech-synced animation states.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10 }}>
            <input value={buildingName} onChange={(e) => setBuildingName(e.target.value)} className="surface-soft" style={{ padding: '10px 12px', color: 'var(--text)' }} />
            <input value={dynasty} onChange={(e) => setDynasty(e.target.value)} className="surface-soft" style={{ padding: '10px 12px', color: 'var(--text)' }} />
            <select value={character} onChange={(e) => setCharacter(e.target.value)} className="surface-soft wl-select" style={{ padding: '10px 12px', color: 'var(--text)' }}>
              {CHARACTER_OPTIONS.map((item) => (
                <option key={item.value} value={item.value}>{item.label}</option>
              ))}
            </select>
            <select value={language} onChange={(e) => setLanguage(e.target.value as Language)} className="surface-soft wl-select" style={{ padding: '10px 12px', color: 'var(--text)' }}>
              <option value="en">English</option>
              <option value="zh">中文</option>
            </select>
          </div>

          <p className="text-caption">Avatar state: {stateLabel}</p>
        </section>

        <section style={{ display: 'grid', gap: 16, gridTemplateColumns: 'minmax(300px, 1fr) minmax(340px, 1fr)' }}>
          <AvatarViewer state={avatarState} visemeLevel={visemeLevel} visemeCode={visemeCode} />

          <div style={{ display: 'grid', gap: 12 }}>
            <ChatUI messages={messages} onSend={sendMessage} disabled={busy} />
            <section className="panel p-5" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap' }}>
              <p className="text-caption">Use microphone for speech input and let the avatar respond with voice.</p>
              <VoiceInput onAudioReady={onVoiceInput} disabled={busy} />
            </section>
          </div>
        </section>
      </main>
    </div>
  )
}
