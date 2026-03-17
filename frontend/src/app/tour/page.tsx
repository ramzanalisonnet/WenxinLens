'use client'

import { useState, useEffect } from 'react'
import { MapPin, Navigation, Clock, ChevronRight, X, Filter } from 'lucide-react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { tourApi } from '@/services/api'
import type { SiteInfo } from '@/types'
import { Navbar } from '@/components/Navbar'
import dynamic from 'next/dynamic'

const TourMap = dynamic(() => import('@/components/TourMap'), { ssr: false })

const DYNASTY_FILTERS = ['All', 'Han Dynasty', 'Tang Dynasty', 'Song Dynasty', 'Ming Dynasty', 'Qing Dynasty']

const dynastyColors: Record<string, { text: string; bg: string; border: string }> = {
  'Han Dynasty':  { text: '#D48A30', bg: 'rgba(180,100,20,0.1)',  border: 'rgba(180,100,20,0.25)' },
  'Tang Dynasty': { text: '#D4AC0D', bg: 'rgba(212,172,13,0.1)',  border: 'rgba(212,172,13,0.25)' },
  'Song Dynasty': { text: '#4DA6D4', bg: 'rgba(30,107,154,0.1)',  border: 'rgba(30,107,154,0.25)' },
  'Ming Dynasty': { text: '#E05C4A', bg: 'rgba(192,57,43,0.1)',   border: 'rgba(192,57,43,0.25)' },
  'Qing Dynasty': { text: '#4DB87A', bg: 'rgba(26,107,58,0.1)',   border: 'rgba(26,107,58,0.25)' },
  'All':          { text: '#D4AC0D', bg: 'rgba(212,172,13,0.1)',  border: 'rgba(212,172,13,0.25)' },
}

function getDynastyStyle(dynasty: string) {
  const key = Object.keys(dynastyColors).find(k => k !== 'All' && dynasty.includes(k.replace(' Dynasty', '')))
  return key ? dynastyColors[key] : dynastyColors['Tang Dynasty']
}

export default function TourPage() {
  const reduceMotion = useReducedMotion()
  const [sites, setSites] = useState<SiteInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedSite, setSelectedSite] = useState<SiteInfo | null>(null)
  const [dynastyFilter, setDynastyFilter] = useState('All')
  const [center] = useState({ lat: 39.9163, lon: 116.3972 })

  useEffect(() => {
    const fetchSites = async () => {
      try {
        const { sites: data } = await tourApi.getNearbySites(center.lat, center.lon, 50)
        setSites(data)
      } catch (err) {
        console.error('Failed to load sites:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchSites()
  }, [center])

  const filtered = dynastyFilter === 'All'
    ? sites
    : sites.filter((s) => s.dynasty.includes(dynastyFilter.replace(' Dynasty', '')))

  return (
    <div className="app-shell min-h-screen">
      <Navbar />

      <div className="app-content container-1200 py-12">
        {/* Page header */}
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: reduceMotion ? 0.01 : 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="mb-8 panel-elevated rounded-2xl p-6"
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold tracking-[0.2em] uppercase" style={{ color: '#D4AC0D' }}>Tour Guide</span>
            <span className="font-chinese text-xs" style={{ color: 'rgba(212,172,13,0.5)' }}>智能游览</span>
          </div>
          <h1 className="title-section text-white mb-2">Smart Tour Guide</h1>
          <p className="text-body">Discover ancient architecture sites and plan your cultural journey</p>
          <div className="flex flex-wrap gap-2 mt-4">
            <span className="px-3 py-1 rounded-full text-[11px] font-semibold" style={{ background: 'rgba(212,172,13,0.14)', border: '1px solid rgba(212,172,13,0.24)', color: '#E5C758' }}>
              Interactive Map Journey
            </span>
            <span className="px-3 py-1 rounded-full text-[11px] font-semibold" style={{ background: 'rgba(77,184,122,0.14)', border: '1px solid rgba(77,184,122,0.24)', color: '#8BD9AB' }}>
              Dynasty-aware Discovery
            </span>
          </div>
        </motion.div>

        {/* Dynasty filters */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: reduceMotion ? 0.01 : 0.42, delay: reduceMotion ? 0 : 0.08, ease: [0.22, 1, 0.36, 1] }}
          className="flex flex-wrap items-center gap-2 mb-6"
        >
          <Filter size={14} style={{ color: 'rgba(255,255,255,0.3)' }} />
          {DYNASTY_FILTERS.map((d) => {
            const style = dynastyColors[d] ?? dynastyColors['Tang Dynasty']
            const active = dynastyFilter === d
            return (
              <button
                key={d}
                onClick={() => setDynastyFilter(d)}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 hover-rise"
                style={{
                  background: active ? style.bg : 'rgba(255,255,255,0.04)',
                  color: active ? style.text : 'rgba(255,255,255,0.45)',
                  border: `1px solid ${active ? style.border : 'rgba(255,255,255,0.07)'}`,
                }}
              >
                {d !== 'All' && <Clock size={9} />}
                {d}
              </button>
            )
          })}
        </motion.div>

        {/* Main grid: Map + Site List */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: reduceMotion ? 0.01 : 0.48, delay: reduceMotion ? 0 : 0.12, ease: [0.22, 1, 0.36, 1] }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-5"
        >
          {/* Map */}
          <div className="rounded-2xl overflow-hidden panel-elevated" style={{ height: 500, border: '1px solid rgba(255,255,255,0.12)' }}>
            <TourMap sites={filtered} selectedSite={selectedSite} onSelectSite={setSelectedSite} />
          </div>

          {/* Site list */}
          <div className="space-y-2.5 overflow-y-auto pr-1" style={{ maxHeight: 500 }}>
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="rounded-xl p-4 shimmer-bg" style={{ border: '1px solid rgba(255,255,255,0.05)' }}>
                  <div className="h-4 rounded mb-2 w-3/4" style={{ background: 'rgba(255,255,255,0.07)' }} />
                  <div className="h-3 rounded w-1/2" style={{ background: 'rgba(255,255,255,0.04)' }} />
                </div>
              ))
            ) : filtered.length === 0 ? (
              <div className="text-center py-16 text-white/30 text-sm rounded-2xl"
                style={{ border: '1px dashed rgba(255,255,255,0.06)' }}>
                No sites found for this dynasty filter.
              </div>
            ) : (
              filtered.map((site) => {
                const ds = getDynastyStyle(site.dynasty)
                const isSelected = selectedSite?.site_id === site.site_id
                return (
                  <button
                    key={site.site_id}
                    onClick={() => setSelectedSite(site)}
                    className="w-full text-left rounded-xl px-4 py-3.5 transition-all duration-200 panel-soft"
                    style={{
                      background: isSelected ? ds.bg : 'rgba(255,255,255,0.06)',
                      border: `1px solid ${isSelected ? ds.border : 'rgba(255,255,255,0.12)'}`,
                    }}
                    onMouseEnter={e => {
                      if (!isSelected) (e.currentTarget as HTMLElement).style.borderColor = 'rgba(212,172,13,0.2)'
                    }}
                    onMouseLeave={e => {
                      if (!isSelected) (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.08)'
                    }}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                          <h3 className="font-semibold text-white text-sm">{site.name}</h3>
                          <span className="font-chinese text-xs" style={{ color: ds.text, opacity: 0.8 }}>{site.name_zh}</span>
                        </div>
                        <div className="flex flex-wrap items-center gap-2.5 mb-2">
                          <span className="flex items-center gap-1 text-[10px] font-medium" style={{ color: ds.text }}>
                            <Clock size={9} />
                            {site.dynasty}
                          </span>
                          {site.distance_km !== null && (
                            <span className="flex items-center gap-1 text-[10px]" style={{ color: 'rgba(255,255,255,0.35)' }}>
                              <Navigation size={9} />
                              {site.distance_km} km
                            </span>
                          )}
                        </div>
                        <p className="text-xs line-clamp-2" style={{ color: 'rgba(255,255,255,0.45)' }}>{site.short_description}</p>
                        {site.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {site.tags.slice(0, 3).map((tag) => (
                              <span key={tag} className="text-[10px] px-2 py-0.5 rounded-full"
                                style={{ background: ds.bg, color: ds.text, border: `1px solid ${ds.border}` }}>
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      <ChevronRight size={14} className="flex-shrink-0 mt-1 transition-transform"
                        style={{ color: isSelected ? ds.text : 'rgba(255,255,255,0.2)' }} />
                    </div>
                  </button>
                )
              })
            )}
          </div>
        </motion.div>

        {/* Selected site detail panel */}
        <AnimatePresence>
          {selectedSite && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              transition={{ duration: 0.35, ease: 'easeOut' }}
              className="mt-6 rounded-2xl overflow-hidden panel-elevated"
              style={{ border: '1px solid rgba(255,255,255,0.11)' }}
            >
              {/* Header band */}
              {(() => {
                const ds = getDynastyStyle(selectedSite.dynasty)
                return (
                  <>
                    <div className="px-6 py-5 relative overflow-hidden" style={{ background: ds.bg, borderBottom: `1px solid ${ds.border}` }}>
                      <div className="absolute inset-0 pointer-events-none" style={{ background: `radial-gradient(ellipse at top right, ${ds.bg.replace('0.1', '0.25')} 0%, transparent 60%)` }} />
                      <div className="relative z-10 flex items-start justify-between gap-4">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full"
                              style={{ background: ds.bg, color: ds.text, border: `1px solid ${ds.border}` }}>
                              <Clock size={9} />
                              {selectedSite.dynasty}
                            </span>
                            {selectedSite.architecture_style && (
                              <span className="text-[10px]" style={{ color: 'rgba(255,255,255,0.4)' }}>{selectedSite.architecture_style}</span>
                            )}
                          </div>
                          <h2 className="text-xl font-bold text-white">{selectedSite.name}</h2>
                          <p className="font-chinese mt-0.5" style={{ color: ds.text }}>{selectedSite.name_zh}</p>
                        </div>
                        <button
                          onClick={() => setSelectedSite(null)}
                          className="w-8 h-8 flex items-center justify-center rounded-lg transition-colors flex-shrink-0"
                          style={{ background: 'rgba(255,255,255,0.07)', color: 'rgba(255,255,255,0.5)' }}
                        >
                          <X size={15} />
                        </button>
                      </div>
                    </div>

                    <div className="px-6 py-5" style={{ background: 'rgba(8,8,15,0.6)' }}>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4 text-sm">
                        <div>
                          <p className="text-xs text-white/30 mb-1 font-medium uppercase tracking-wide">Dynasty</p>
                          <p className="font-semibold text-white/85 text-sm" style={{ color: ds.text }}>{selectedSite.dynasty}</p>
                        </div>
                        <div>
                          <p className="text-xs text-white/30 mb-1 font-medium uppercase tracking-wide">Style</p>
                          <p className="font-semibold text-white/85 text-sm">{selectedSite.architecture_style}</p>
                        </div>
                        {selectedSite.distance_km !== null && (
                          <div>
                            <p className="text-xs text-white/30 mb-1 font-medium uppercase tracking-wide">Distance</p>
                            <p className="font-semibold text-white/85 text-sm flex items-center gap-1">
                              <MapPin size={12} style={{ color: ds.text }} />
                              {selectedSite.distance_km} km away
                            </p>
                          </div>
                        )}
                      </div>
                      <p className="text-white/55 text-sm leading-relaxed">{selectedSite.short_description}</p>
                    </div>
                  </>
                )
              })()}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}


