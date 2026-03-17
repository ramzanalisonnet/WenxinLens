'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { Search, BookOpen, Network, Clock } from 'lucide-react'
import { Navbar } from '@/components/Navbar'
import { knowledgeApi } from '@/services/api'

const DYNASTIES = ['All', 'Zhou', 'Han', 'Tang', 'Song', 'Ming', 'Qing']

const dynastyAccents: Record<string, { bg: string; text: string; border: string }> = {
  All:  { bg: 'rgba(212,172,13,0.1)',  text: '#D4AC0D', border: 'rgba(212,172,13,0.25)' },
  Zhou: { bg: 'rgba(130,80,160,0.1)',  text: '#B47FD4', border: 'rgba(130,80,160,0.25)' },
  Han:  { bg: 'rgba(180,100,20,0.1)',  text: '#D48A30', border: 'rgba(180,100,20,0.25)' },
  Tang: { bg: 'rgba(212,172,13,0.1)',  text: '#D4AC0D', border: 'rgba(212,172,13,0.25)' },
  Song: { bg: 'rgba(30,107,154,0.1)',  text: '#4DA6D4', border: 'rgba(30,107,154,0.25)' },
  Ming: { bg: 'rgba(192,57,43,0.1)',   text: '#E05C4A', border: 'rgba(192,57,43,0.25)' },
  Qing: { bg: 'rgba(26,107,58,0.1)',   text: '#4DB87A', border: 'rgba(26,107,58,0.25)' },
}

export default function KnowledgePage() {
  const reduceMotion = useReducedMotion()
  const [query,   setQuery]   = useState('')
  const [dynasty, setDynasty] = useState('All')

  const { data: searchResults, isLoading: searching } = useQuery({
    queryKey: ['kg-search', query],
    queryFn:  () => knowledgeApi.search(query),
    enabled:  query.length > 1,
  })

  const { data: dynastyBuildings } = useQuery({
    queryKey: ['kg-dynasty', dynasty],
    queryFn:  () => knowledgeApi.getDynastyBuildings(dynasty),
    enabled:  dynasty !== 'All',
  })

  const buildings = query.length > 1 ? searchResults : dynastyBuildings
  const activeDynastyStyle = dynastyAccents[dynasty] ?? dynastyAccents.All

  return (
    <main className="app-shell min-h-screen">
      <Navbar />

      <div className="app-content container-1200 py-12 space-y-8">
        {/* Page header */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: reduceMotion ? 0.01 : 0.55, ease: [0.22, 1, 0.36, 1] }}
          className="space-y-2 panel-elevated rounded-2xl p-6"
        >
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold tracking-[0.2em] uppercase" style={{ color: '#D4AC0D' }}>Knowledge</span>
            <span className="font-chinese text-xs" style={{ color: 'rgba(212,172,13,0.5)' }}>知识库</span>
          </div>
          <h1 className="title-section text-white flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'rgba(212,172,13,0.1)', border: '1px solid rgba(212,172,13,0.2)' }}>
              <BookOpen size={20} style={{ color: '#D4AC0D' }} />
            </div>
            Cultural Knowledge Base
          </h1>
          <p className="text-body">Explore Chinese ancient architectural heritage by dynasty, style, and symbolism</p>
          <div className="flex flex-wrap gap-2 pt-2">
            <span className="px-3 py-1 rounded-full text-[11px] font-semibold" style={{ background: activeDynastyStyle.bg, border: `1px solid ${activeDynastyStyle.border}`, color: activeDynastyStyle.text }}>
              Active Filter: {dynasty}
            </span>
            <span className="px-3 py-1 rounded-full text-[11px] font-semibold" style={{ background: 'rgba(77,166,212,0.14)', border: '1px solid rgba(77,166,212,0.24)', color: '#8BC9EA' }}>
              Semantic Search
            </span>
          </div>
        </motion.div>

        {/* Search bar */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: reduceMotion ? 0.01 : 0.42, delay: reduceMotion ? 0 : 0.08, ease: [0.22, 1, 0.36, 1] }}
          className="relative group"
        >
          <Search
            className="absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none transition-colors"
            size={16}
            style={{ color: 'rgba(212,172,13,0.5)' }}
          />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search buildings, dynasties, styles…"
            className="w-full rounded-2xl pl-11 pr-4 py-3.5 text-sm outline-none transition-all"
            style={{
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.12)',
              color: 'rgba(255,255,255,0.85)',
            }}
            onFocus={e => (e.currentTarget as HTMLElement).style.borderColor = 'rgba(212,172,13,0.3)'}
            onBlur={e  => (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.08)'}
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-white/25 hover:text-white/60 text-xs"
            >
              Clear
            </button>
          )}
        </motion.div>

        {/* Dynasty filter pills */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: reduceMotion ? 0.01 : 0.42, delay: reduceMotion ? 0 : 0.12, ease: [0.22, 1, 0.36, 1] }}
          className="flex flex-wrap gap-2"
        >
          {DYNASTIES.map((d) => {
            const style = dynastyAccents[d] ?? dynastyAccents.All
            const isActive = dynasty === d && !query
            return (
              <button
                key={d}
                onClick={() => { setDynasty(d); setQuery('') }}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 hover-rise"
                style={{
                  background: isActive ? style.bg : 'rgba(255,255,255,0.04)',
                  color: isActive ? style.text : 'rgba(255,255,255,0.45)',
                  border: `1px solid ${isActive ? style.border : 'rgba(255,255,255,0.07)'}`,
                  boxShadow: isActive ? `0 0 12px ${style.bg}` : 'none',
                }}
              >
                {d !== 'All' && <Clock size={10} />}
                {d}
              </button>
            )
          })}
        </motion.div>

        {/* Loading */}
        {searching && (
          <div className="text-center py-16 text-white/30 text-sm">
            <div className="flex items-center justify-center gap-2">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="ml-2">Searching knowledge graph…</span>
            </div>
          </div>
        )}

        {/* Results grid */}
        <AnimatePresence mode="wait">
          {buildings && buildings.length > 0 && (
            <motion.div
              key="results"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="grid sm:grid-cols-2 gap-4"
            >
              {buildings.map((b: any, i: number) => {
                const ds = dynastyAccents[b.dynasty] ?? dynastyAccents.All
                return (
                  <motion.div
                    key={b.name ?? i}
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: reduceMotion ? 0 : i * 0.04, duration: reduceMotion ? 0.01 : 0.38, ease: [0.22, 1, 0.36, 1] }}
                    className="group rounded-2xl p-5 space-y-3 transition-all duration-300 cursor-pointer panel-soft"
                    style={{
                      background: 'rgba(255,255,255,0.06)',
                      border: '1px solid rgba(255,255,255,0.12)',
                    }}
                    onMouseEnter={e => {
                      const el = e.currentTarget as HTMLElement
                      el.style.background = ds.bg
                      el.style.borderColor = ds.border
                      el.style.transform = 'translateY(-2px)'
                      el.style.boxShadow = '0 12px 40px rgba(0,0,0,0.3)'
                    }}
                    onMouseLeave={e => {
                      const el = e.currentTarget as HTMLElement
                      el.style.background = 'rgba(255,255,255,0.06)'
                      el.style.borderColor = 'rgba(255,255,255,0.12)'
                      el.style.transform = ''
                      el.style.boxShadow = ''
                    }}
                  >
                    {/* Dynasty badge */}
                    <div className="flex items-center justify-between">
                      {b.dynasty && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold"
                          style={{ background: ds.bg, color: ds.text, border: `1px solid ${ds.border}` }}>
                          <Clock size={8} />
                          {b.dynasty} Dynasty
                        </span>
                      )}
                      {b.style && (
                        <span className="text-[10px] text-white/35 font-medium">{b.style}</span>
                      )}
                    </div>

                    {/* Name */}
                    <div>
                      <h3 className="font-bold text-white text-base leading-tight">{b.name_en ?? b.name}</h3>
                      {b.name_zh && (
                        <p className="font-chinese mt-0.5 text-sm" style={{ color: ds.text, opacity: 0.8 }}>{b.name_zh}</p>
                      )}
                    </div>

                    {/* Description */}
                    {b.description && (
                      <p className="text-white/50 text-xs leading-relaxed line-clamp-3">{b.description}</p>
                    )}
                  </motion.div>
                )
              })}
            </motion.div>
          )}

          {buildings && buildings.length === 0 && (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-16"
              style={{ color: 'rgba(255,255,255,0.3)' }}
            >
              <p className="text-sm">No results found for your query.</p>
            </motion.div>
          )}

          {!query && dynasty === 'All' && (
            <motion.div
              key="idle"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-2xl p-12 text-center space-y-4 panel-elevated"
              style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)' }}
            >
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto"
                style={{ background: 'rgba(212,172,13,0.08)', border: '1px solid rgba(212,172,13,0.15)' }}>
                <Network size={26} style={{ color: 'rgba(212,172,13,0.6)' }} />
              </div>
              <div>
                <p className="text-white/50 text-sm font-medium mb-1">Explore the Knowledge Graph</p>
                <p className="text-white/25 text-xs max-w-sm mx-auto">
                  Select a dynasty above or type in the search bar to discover Chinese ancient architecture.
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  )
}

