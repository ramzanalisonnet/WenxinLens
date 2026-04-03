'use client'

import { useState, useCallback, useRef } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { Camera, Upload, Loader2, ZoomIn, Globe, BookOpen, Volume2, Wand2, MessageCircle } from 'lucide-react'
import { recognitionApi, voiceApi } from '@/services/api'
import type { RecognitionResult, Language, DetailLevel } from '@/types'
import { RecognitionCard } from '@/components/RecognitionCard'
import { ChatPanel } from '@/components/ChatPanel'
import { Navbar } from '@/components/Navbar'

export default function RecognizePage() {
  const reduceMotion = useReducedMotion()
  const [image, setImage] = useState<string | null>(null)
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [result, setResult] = useState<RecognitionResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [language, setLanguage] = useState<Language>('en')
  const [detailLevel, setDetailLevel] = useState<DetailLevel>('standard')
  const [showChat, setShowChat] = useState(false)
  const [playingAudio, setPlayingAudio] = useState(false)
  const [isAudioPaused, setIsAudioPaused] = useState(false)
  const [narrationLoading, setNarrationLoading] = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const narrationModeRef = useRef<'audio' | 'browser' | null>(null)

  const speakWithBrowserTts = useCallback((text: string) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return false

    try {
      window.speechSynthesis.cancel()
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = language === 'zh' ? 'zh-CN' : 'en-US'
      utterance.rate = 1
      utterance.onend = () => {
        narrationModeRef.current = null
        setPlayingAudio(false)
        setIsAudioPaused(false)
      }
      utterance.onerror = () => {
        narrationModeRef.current = null
        setPlayingAudio(false)
        setIsAudioPaused(false)
      }
      window.speechSynthesis.speak(utterance)
      narrationModeRef.current = 'browser'
      return true
    } catch {
      return false
    }
  }, [language])

  const onDrop = useCallback((files: File[]) => {
    const file = files[0]
    if (!file) return
    setImageFile(file)
    setImage(URL.createObjectURL(file))
    setResult(null)
    setError(null)
    setShowChat(false)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
  })

  const handleAnalyze = async () => {
    if (!imageFile) return
    setLoading(true)
    setError(null)
    try {
      const res = await recognitionApi.analyzeImage(imageFile, language, detailLevel)
      setResult(res)
      setShowChat(false)
    } catch (err: any) {
      setError(err.message || 'Recognition failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handlePlayNarration = async () => {
    if (!result) return

    if (playingAudio) {
      if (narrationModeRef.current === 'audio' && audioRef.current) {
        if (isAudioPaused) {
          await audioRef.current.play()
          setIsAudioPaused(false)
        } else {
          audioRef.current.pause()
          setIsAudioPaused(true)
        }
        return
      }

      if (narrationModeRef.current === 'browser' && typeof window !== 'undefined' && 'speechSynthesis' in window) {
        if (isAudioPaused) {
          window.speechSynthesis.resume()
          setIsAudioPaused(false)
        } else {
          window.speechSynthesis.pause()
          setIsAudioPaused(true)
        }
        return
      }
    }

    setError(null)

    const text = (language === 'zh' ? result.description_zh : result.description)?.trim()
      || result.cultural_significance?.trim()
      || result.building_name

    if (!text) {
      setError('No narration text available for this result.')
      return
    }

    setNarrationLoading(true)
    setPlayingAudio(true)
    setIsAudioPaused(false)

    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }

    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel()
    }

    try {
      const blob = await voiceApi.synthesize(text, language)
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      audioRef.current = audio
      narrationModeRef.current = 'audio'

      audio.onended = () => {
        URL.revokeObjectURL(url)
        narrationModeRef.current = null
        setPlayingAudio(false)
        setIsAudioPaused(false)
      }
      audio.onerror = () => {
        URL.revokeObjectURL(url)
        narrationModeRef.current = null
        setPlayingAudio(false)
        setIsAudioPaused(false)
      }

      await audio.play()
      setNarrationLoading(false)
    } catch {
      const fallbackStarted = speakWithBrowserTts(text)
      if (!fallbackStarted) {
        narrationModeRef.current = null
        setError('Narration failed. Please verify audio permissions or TTS provider settings.')
        setPlayingAudio(false)
        setIsAudioPaused(false)
      }
      setNarrationLoading(false)
    }
  }

  return (
    <div className="app-shell min-h-screen">
      <Navbar />

      <div className="app-content container-1200 py-12">
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: reduceMotion ? 0.01 : 0.55, ease: [0.22, 1, 0.36, 1] }}
          className="panel p-6 md:p-8 mb-8"
        >
          <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
            <div className="max-w-2xl">
              <p className="text-caption" style={{ letterSpacing: '0.09em', color: 'var(--highlight)' }}>
                AI RECOGNITION LAB
              </p>
              <h1 className="title-section mt-3">Recognize Ancient Chinese Architecture</h1>
              <p className="text-body mt-4">
                Upload one building photo and get era clues, structural features, and cultural context in seconds.
              </p>
            </div>
            <div className="flex flex-wrap gap-3 text-xs sm:text-sm">
              <div className="px-3 py-2 rounded-lg" style={{ background: 'rgba(0, 209, 178, 0.09)', border: '1px solid rgba(0, 209, 178, 0.28)', color: 'var(--highlight)' }}>
                Up to 10 MB
              </div>
              <div className="px-3 py-2 rounded-lg" style={{ background: 'rgba(255, 77, 79, 0.09)', border: '1px solid rgba(255, 77, 79, 0.32)', color: 'var(--accent)' }}>
                JPG PNG WebP
              </div>
            </div>
          </div>
        </motion.section>

        <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.45fr)_minmax(0,1fr)] gap-6 items-start">
          <motion.section
            initial={{ opacity: 0, x: -16 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: reduceMotion ? 0.01 : 0.5, delay: reduceMotion ? 0 : 0.1, ease: [0.22, 1, 0.36, 1] }}
            className="w-full min-w-0 panel p-5 md:p-6"
          >
            <div className="flex flex-wrap items-center gap-3 mb-5">
              <div
                className="inline-flex items-center gap-2 px-3 py-2 rounded-xl"
                style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(230, 234, 242, 0.18)' }}
              >
                <Globe size={14} style={{ color: 'var(--highlight)' }} />
                <span className="text-caption">Language</span>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value as Language)}
                  className="wl-select text-sm font-semibold cursor-pointer px-2 py-1"
                  aria-label="Choose language"
                >
                  <option value="en">English</option>
                  <option value="zh">中文</option>
                </select>
              </div>

              <div
                className="inline-flex items-center gap-2 px-3 py-2 rounded-xl"
                style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(230, 234, 242, 0.18)' }}
              >
                <BookOpen size={14} style={{ color: 'var(--accent)' }} />
                <span className="text-caption">Detail</span>
                <select
                  value={detailLevel}
                  onChange={(e) => setDetailLevel(e.target.value as DetailLevel)}
                  className="wl-select text-sm font-semibold cursor-pointer px-2 py-1"
                  aria-label="Choose detail level"
                >
                  <option value="tourist">Tourist</option>
                  <option value="standard">Standard</option>
                  <option value="academic">Academic</option>
                </select>
              </div>
            </div>

            <div
              {...getRootProps()}
              className={`relative rounded-2xl overflow-hidden cursor-pointer transition-all duration-300 ${isDragActive ? 'scale-[1.01]' : ''}`}
              style={{
                minHeight: 360,
                border: `2px dashed ${isDragActive ? 'rgba(0, 209, 178, 0.8)' : image ? 'rgba(230, 234, 242, 0.22)' : 'rgba(230, 234, 242, 0.26)'}`,
                background: isDragActive
                  ? 'linear-gradient(145deg, rgba(0, 209, 178, 0.1), rgba(255, 77, 79, 0.08))'
                  : 'linear-gradient(160deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02))',
              }}
            >
              <input {...getInputProps()} />

              {image ? (
                <div className="relative w-full" style={{ minHeight: 360 }}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={image} alt="Uploaded architecture" className="w-full object-cover" style={{ minHeight: 360, maxHeight: 520 }} />

                  {loading && (
                    <div className="absolute inset-0" style={{ background: 'rgba(8, 12, 22, 0.62)' }}>
                      <div className="scan-overlay">
                        <div className="scan-line" />
                      </div>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="flex flex-col items-center gap-3">
                          <div className="w-12 h-12 rounded-full flex items-center justify-center"
                            style={{ border: '2px solid rgba(255,77,79,0.64)', boxShadow: '0 0 24px rgba(255,77,79,0.35)' }}>
                            <Wand2 size={20} style={{ color: 'var(--accent)' }} />
                          </div>
                          <p className="text-white text-sm font-semibold">Analyzing architecture</p>
                          <div className="flex items-center gap-1">
                            <span className="typing-dot" />
                            <span className="typing-dot" />
                            <span className="typing-dot" />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {!loading && <div className="absolute inset-0 bg-gradient-to-t from-black/65 via-transparent to-transparent" />}
                  {!loading && (
                    <div className="absolute bottom-4 right-4">
                      <span className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full"
                        style={{ background: 'rgba(8, 12, 22, 0.8)', border: '1px solid rgba(230, 234, 242, 0.2)', color: 'var(--text)' }}>
                        <ZoomIn size={11} /> Click to replace image
                      </span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center gap-5 text-center px-8 py-16">
                  <motion.div
                    animate={{ y: [0, -6, 0] }}
                    transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
                    className="w-16 h-16 rounded-2xl flex items-center justify-center"
                    style={{ background: 'rgba(0, 209, 178, 0.09)', border: '1px solid rgba(0, 209, 178, 0.28)' }}
                  >
                    <Upload size={24} style={{ color: 'var(--highlight)' }} />
                  </motion.div>
                  <div>
                    <p className="text-white font-semibold mb-1 text-sm">Drop an architecture photo here</p>
                    <p className="text-caption">or click to browse. Supports JPG, PNG, WebP.</p>
                  </div>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {['Temple', 'Pagoda', 'Palace', 'Garden'].map((tag) => (
                      <span
                        key={tag}
                        className="text-[10px] px-2 py-1 rounded-full font-medium"
                        style={{ background: 'rgba(255,255,255,0.04)', color: 'var(--text-muted)', border: '1px solid rgba(230, 234, 242, 0.18)' }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                className="px-4 py-3 rounded-xl text-sm mt-4"
                style={{ background: 'rgba(255, 77, 79, 0.12)', border: '1px solid rgba(255, 77, 79, 0.34)', color: '#FFB3B4' }}
              >
                {error}
              </motion.div>
            )}

            <button
              onClick={handleAnalyze}
              disabled={!imageFile || loading}
              className="w-full mt-4 flex items-center justify-center gap-2.5 py-3.5 rounded-xl font-semibold text-sm transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed subtle-shine"
              style={{
                background: imageFile && !loading ? 'linear-gradient(135deg, #FF4D4F, #D93E40)' : 'rgba(255,255,255,0.08)',
                color: '#fff',
                border: imageFile && !loading ? '1px solid rgba(255, 77, 79, 0.55)' : '1px solid rgba(230, 234, 242, 0.18)',
              }}
            >
              {loading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Analyzing architecture...
                </>
              ) : (
                <>
                  <Camera size={18} />
                  Analyze Building
                </>
              )}
            </button>
          </motion.section>

          <AnimatePresence mode="wait">
            {result ? (
              <motion.section
                key="result"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: reduceMotion ? 0.01 : 0.42, ease: [0.22, 1, 0.36, 1] }}
                className="w-full min-w-0 space-y-4"
              >
                <RecognitionCard result={result} />

                <div className="panel p-3">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <button
                      onClick={handlePlayNarration}
                      disabled={narrationLoading}
                      className="flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold transition-all disabled:opacity-50"
                      style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(230, 234, 242, 0.2)', color: 'var(--text)' }}
                    >
                      <Volume2 size={16} className={playingAudio && !isAudioPaused ? 'animate-pulse' : ''} style={{ color: playingAudio ? 'var(--highlight)' : undefined }} />
                      {narrationLoading ? 'Starting...' : playingAudio ? (isAudioPaused ? 'Resume' : 'Pause') : 'Play'}
                    </button>
                    <button
                      onClick={() => setShowChat((v) => !v)}
                      className="flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold transition-all"
                      style={{
                        background: showChat ? 'rgba(255, 77, 79, 0.12)' : 'linear-gradient(135deg, #FF4D4F, #D93E40)',
                        border: showChat ? '1px solid rgba(255, 77, 79, 0.35)' : '1px solid rgba(255, 77, 79, 0.58)',
                        color: '#fff',
                      }}
                    >
                      <MessageCircle size={16} />
                      {showChat ? 'Hide Chat' : 'Ask Questions'}
                    </button>
                  </div>
                </div>

                {showChat && (
                  <ChatPanel
                    buildingContext={result.result_id}
                    buildingName={result.building_name}
                    language={language}
                  />
                )}
              </motion.section>
            ) : (
              <motion.section
                key="placeholder"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="w-full min-w-0 panel p-8"
                style={{ minHeight: 420 }}
              >
                <div className="h-full rounded-2xl flex flex-col items-center justify-center gap-5 text-center"
                  style={{ background: 'rgba(255,255,255,0.02)', border: '1px dashed rgba(230, 234, 242, 0.24)' }}>
                  <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
                    style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(230, 234, 242, 0.16)' }}>
                    <Camera size={24} style={{ color: 'rgba(230, 234, 242, 0.45)' }} />
                  </div>
                  <div className="px-6">
                    <p className="text-white font-medium text-sm mb-1">Recognition insights will appear here</p>
                    <p className="text-caption max-w-[260px] mx-auto">
                      Upload one building image to unlock dynasty clues, architectural features, and Q&A context.
                    </p>
                  </div>
                </div>
              </motion.section>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}




