'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { Building2, Star, ChevronDown, Sparkles, Clock } from 'lucide-react'
import { useState } from 'react'
import type { RecognitionResult } from '@/types'

interface RecognitionCardProps {
  result: RecognitionResult
}

const dynastyColors: Record<string, { bg: string; text: string; border: string }> = {
  Tang:  { bg: 'rgba(212,172,13,0.12)', text: '#D4AC0D', border: 'rgba(212,172,13,0.25)' },
  Song:  { bg: 'rgba(30,107,154,0.12)', text: '#4DA6D4', border: 'rgba(30,107,154,0.25)' },
  Ming:  { bg: 'rgba(192,57,43,0.12)',  text: '#E05C4A', border: 'rgba(192,57,43,0.25)' },
  Qing:  { bg: 'rgba(26,107,58,0.12)',  text: '#4DB87A', border: 'rgba(26,107,58,0.25)' },
  Han:   { bg: 'rgba(130,80,20,0.12)',  text: '#C8892A', border: 'rgba(130,80,20,0.25)' },
  Zhou:  { bg: 'rgba(90,60,140,0.12)',  text: '#9B7AC8', border: 'rgba(90,60,140,0.25)' },
}

function getDynastyStyle(dynasty?: string) {
  if (!dynasty) return dynastyColors.Ming
  const key = Object.keys(dynastyColors).find(k => dynasty.includes(k))
  return key ? dynastyColors[key] : { bg: 'rgba(212,172,13,0.12)', text: '#D4AC0D', border: 'rgba(212,172,13,0.25)' }
}

export function RecognitionCard({ result }: RecognitionCardProps) {
  const [expanded, setExpanded] = useState(false)
  const confidencePct = Math.round(result.confidence_score * 100)
  const dynastyStyle = getDynastyStyle(result.dynasty)

  return (
    <motion.div
      initial={{ opacity: 0, y: 24, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="rounded-2xl overflow-hidden panel-elevated"
      style={{ background: 'linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.03))', border: '1px solid rgba(255,255,255,0.11)' }}
    >
      {/* Gradient header band */}
      <div className="relative px-6 pt-6 pb-5 border-b" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
        <div
          className="absolute inset-0 opacity-40 pointer-events-none"
          style={{ background: `radial-gradient(ellipse at top right, ${dynastyStyle.bg.replace('0.12', '0.3')} 0%, transparent 60%)` }}
        />
        <div className="relative z-10 flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2.5 mb-1 flex-wrap">
              {result.dynasty && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wide"
                  style={{ background: dynastyStyle.bg, color: dynastyStyle.text, border: `1px solid ${dynastyStyle.border}` }}>
                  <Clock size={9} />
                  {result.dynasty} Dynasty
                </span>
              )}
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold"
                style={{ background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.5)', border: '1px solid rgba(255,255,255,0.08)' }}>
                <Sparkles size={9} />
                AI Identified
              </span>
            </div>
            <h2 className="title-card text-white leading-tight">{result.building_name}</h2>
            <p className="font-chinese text-lg mt-0.5" style={{ color: dynastyStyle.text }}>{result.building_name_zh}</p>
          </div>
          <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: dynastyStyle.bg, border: `1px solid ${dynastyStyle.border}` }}>
            <Building2 size={22} style={{ color: dynastyStyle.text }} />
          </div>
        </div>
      </div>

      <div className="px-6 py-5 space-y-5">
        {/* Confidence bar */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs text-white/40 uppercase tracking-wider font-medium">Recognition Confidence</span>
            <span className="text-sm font-semibold tabular-nums"
              style={{ color: confidencePct >= 80 ? '#4DB87A' : confidencePct >= 60 ? '#D4AC0D' : '#E05C4A' }}>
              {confidencePct}%
            </span>
          </div>
          <div className="confidence-track">
            <motion.div
              className="confidence-fill"
              initial={{ width: 0 }}
              animate={{ width: `${confidencePct}%` }}
              transition={{ duration: 1.2, ease: [0.4, 0, 0.2, 1] }}
            />
          </div>
        </div>

        {/* Structural features */}
        {result.structural_features?.length > 0 && (
          <div>
            <p className="text-xs text-white/35 uppercase tracking-wider font-medium mb-2.5">Structural Features</p>
            <div className="flex flex-wrap gap-1.5">
              {result.structural_features.map((f) => (
                <span
                  key={f}
                  className="px-2.5 py-1 rounded-lg text-xs font-medium transition-all"
                  style={{ background: 'rgba(212,172,13,0.08)', color: '#D4AC0D', border: '1px solid rgba(212,172,13,0.15)' }}
                >
                  {f}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Description */}
        {result.description && (
          <div>
            <p className="text-white/65 text-sm leading-relaxed line-clamp-4">{result.description}</p>
          </div>
        )}

        {/* Cultural significance accordion */}
        {result.cultural_significance && (
          <div className="rounded-xl overflow-hidden" style={{ border: '1px solid rgba(255,255,255,0.06)' }}>
            <button
              onClick={() => setExpanded(!expanded)}
              className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium transition-colors hover:bg-white/[0.05]"
            >
              <span className="flex items-center gap-2 text-white/60">
                <Star size={13} style={{ color: '#D4AC0D' }} />
                Cultural Significance
              </span>
              <motion.div animate={{ rotate: expanded ? 180 : 0 }} transition={{ duration: 0.2 }}>
                <ChevronDown size={14} className="text-white/30" />
              </motion.div>
            </button>
            <AnimatePresence initial={false}>
              {expanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.25, ease: 'easeOut' }}
                  className="overflow-hidden"
                >
                  <div className="px-4 pb-4 pt-1" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                    <p className="text-white/60 text-sm leading-relaxed">{result.cultural_significance}</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* Follow-up questions */}
        {result.follow_up_questions && result.follow_up_questions.length > 0 && (
          <div>
            <p className="text-xs text-white/35 uppercase tracking-wider font-medium mb-2.5">Ask More</p>
            <div className="space-y-1.5">
              {result.follow_up_questions.map((q) => (
                <button
                  key={q}
                  className="w-full text-left text-xs px-3 py-2.5 rounded-lg transition-all"
                  style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.11)', color: 'rgba(255,255,255,0.62)' }}
                  onMouseEnter={e => {
                    (e.currentTarget as HTMLElement).style.borderColor = 'rgba(212,172,13,0.2)'
                    ;(e.currentTarget as HTMLElement).style.color = 'rgba(255,255,255,0.85)'
                  }}
                  onMouseLeave={e => {
                    (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.11)'
                    ;(e.currentTarget as HTMLElement).style.color = 'rgba(255,255,255,0.62)'
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  )
}

