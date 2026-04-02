'use client'

import dynamic from 'next/dynamic'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, useReducedMotion } from 'framer-motion'
import { ArrowLeft, Check, ChevronDown, Clock3, Landmark, MapPin } from 'lucide-react'
import { Navbar } from '@/components/Navbar'
import { knowledgeApi } from '@/services/api'
import type { DynastyPlace } from '@/types'

const DynastyPlacesMap = dynamic(() => import('@/components/DynastyPlacesMap'), { ssr: false })

function normalizePlace(place: any, index: number): DynastyPlace {
  return {
    id: place.id ?? `place-${index}`,
    name: place.name ?? 'Unknown Place',
    name_zh: place.name_zh ?? '',
    location: place.location ?? 'Unknown',
    coordinates: place.coordinates ?? null,
    architecture_type: place.architecture_type ?? place.architectural_style ?? 'Unknown',
    year_built: place.year_built ?? 'Unknown',
    image_url: place.image_url ?? '/images/hero-architecture.svg',
    description: place.description ?? 'No description available.',
    details: Array.isArray(place.details) ? place.details : [],
  }
}

export default function DynastyDetailPage() {
  const reduceMotion = useReducedMotion()
  const router = useRouter()
  const dropdownRef = useRef<HTMLDivElement | null>(null)
  const params = useParams<{ name: string }>()
  const rawName = Array.isArray(params.name) ? params.name[0] : params.name
  const dynastyName = decodeURIComponent(rawName ?? '')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['dynasty-detail', dynastyName],
    queryFn: () => knowledgeApi.getDynastyBuildings(dynastyName),
    enabled: dynastyName.length > 0,
  })

  const { data: dynasties } = useQuery({
    queryKey: ['dynasty-list'],
    queryFn: () => knowledgeApi.listDynasties(),
  })

  const dynastyOptions = useMemo(() => {
    if (!Array.isArray(dynasties)) return [] as string[]
    return dynasties
      .map((item: any) => item?.name)
      .filter((name: unknown): name is string => typeof name === 'string' && name.length > 0)
  }, [dynasties])

  const places = useMemo(() => (Array.isArray(data) ? data.map(normalizePlace) : []), [data])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)

  useEffect(() => {
    const onPointerDown = (event: MouseEvent) => {
      if (!dropdownRef.current) return
      if (!dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false)
      }
    }

    window.addEventListener('mousedown', onPointerDown)
    return () => window.removeEventListener('mousedown', onPointerDown)
  }, [])

  const selected = useMemo(() => {
    if (!selectedId) return places[0] ?? null
    return places.find((place) => place.id === selectedId) ?? places[0] ?? null
  }, [places, selectedId])

  return (
    <main className="app-shell min-h-screen">
      <Navbar />

      <div className="app-content container-1200 py-12 space-y-6">
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: reduceMotion ? 0.01 : 0.42 }}
          className="panel-elevated rounded-2xl p-6"
        >
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <p className="text-caption" style={{ color: '#D4AC0D' }}>Dynasty Atlas</p>
              <h1 className="title-section mt-2">{dynastyName}</h1>
              <p className="text-body mt-2">Explore architecture places with geolocation pins and full details cards.</p>
            </div>
            <div className="flex items-center gap-2 flex-wrap justify-end">
              <span className="text-caption">Dynasty</span>
              <div ref={dropdownRef} className="relative min-w-[220px]">
                <button
                  type="button"
                  onClick={() => setIsDropdownOpen((prev) => !prev)}
                  className="w-full rounded-lg px-3 py-2 text-sm flex items-center justify-between"
                  style={{
                    background: 'rgba(255,255,255,0.06)',
                    border: '1px solid rgba(255,255,255,0.18)',
                    color: 'rgba(255,255,255,0.92)',
                  }}
                  aria-haspopup="listbox"
                  aria-expanded={isDropdownOpen}
                >
                  <span>{dynastyName}</span>
                  <ChevronDown size={16} style={{ color: 'rgba(255,255,255,0.72)' }} />
                </button>

                {isDropdownOpen && (
                  <div
                    className="absolute left-0 right-0 mt-2 rounded-lg overflow-hidden z-20"
                    style={{
                      background: '#ffffff',
                      border: '1px solid rgba(255,255,255,0.18)',
                      boxShadow: '0 12px 24px rgba(0,0,0,0.35)',
                    }}
                    role="listbox"
                    aria-label="Dynasty selector"
                  >
                    {(dynastyOptions.length > 0 ? dynastyOptions : [dynastyName]).map((name) => {
                      const active = name === dynastyName
                      return (
                        <button
                          key={name}
                          type="button"
                          className="w-full px-3 py-2 text-sm flex items-center justify-between"
                          style={{
                            background: active ? '#7a7a7a' : '#ffffff',
                            color: active ? '#ffffff' : '#0f172a',
                            borderTop: '1px solid rgba(15,23,42,0.08)',
                          }}
                          onClick={() => {
                            setIsDropdownOpen(false)
                            if (name === dynastyName) return
                            router.push(`/knowledge/dynasty/${encodeURIComponent(name)}`)
                          }}
                          role="option"
                          aria-selected={active}
                        >
                          <span>{name}</span>
                          {active && <Check size={14} style={{ color: '#ffffff' }} />}
                        </button>
                      )
                    })}
                  </div>
                )}
              </div>

              <Link href="/knowledge" className="btn btn-secondary">
                <ArrowLeft size={14} />
                Back to Knowledge
              </Link>
            </div>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
          <div className="lg:col-span-3 rounded-2xl overflow-hidden panel-elevated" style={{ height: 520, border: '1px solid rgba(255,255,255,0.12)' }}>
            <DynastyPlacesMap places={places} selectedPlaceId={selected?.id ?? null} onSelectPlace={(place) => setSelectedId(place.id)} />
          </div>

          <div className="lg:col-span-2 rounded-2xl p-4 panel-soft" style={{ maxHeight: 520, overflowY: 'auto' }}>
            {isLoading && <p className="text-body">Loading places...</p>}
            {isError && <p className="text-body">Failed to load dynasty data.</p>}
            {!isLoading && !isError && places.length === 0 && <p className="text-body">No places found for this dynasty.</p>}

            <div className="space-y-3">
              {places.map((place) => {
                const active = selected?.id === place.id
                return (
                  <button
                    key={place.id}
                    className="w-full text-left rounded-xl p-3 transition-all"
                    style={{
                      background: active ? 'rgba(212,172,13,0.14)' : 'rgba(255,255,255,0.05)',
                      border: `1px solid ${active ? 'rgba(212,172,13,0.35)' : 'rgba(255,255,255,0.1)'}`,
                    }}
                    onClick={() => setSelectedId(place.id)}
                  >
                    <p className="text-sm font-semibold text-white">{place.name}</p>
                    {place.name_zh && <p className="text-xs font-chinese mt-1" style={{ color: '#D4AC0D' }}>{place.name_zh}</p>}
                    <p className="text-[11px] mt-2 text-white/55">{place.location}</p>
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        {selected && (
          <motion.article
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: reduceMotion ? 0.01 : 0.36 }}
            className="panel-elevated rounded-2xl overflow-hidden"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-0">
              <div>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={selected.image_url} alt={selected.name} className="w-full h-full min-h-[260px] object-cover" />
              </div>

              <div className="p-6 space-y-4">
                <div>
                  <h2 className="title-card">{selected.name}</h2>
                  {selected.name_zh && <p className="font-chinese mt-1" style={{ color: '#D4AC0D' }}>{selected.name_zh}</p>}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="panel-soft p-3">
                    <p className="text-white/40 mb-1">Location</p>
                    <p className="text-white/85 flex items-center gap-1"><MapPin size={12} />{selected.location}</p>
                  </div>
                  <div className="panel-soft p-3">
                    <p className="text-white/40 mb-1">Built</p>
                    <p className="text-white/85 flex items-center gap-1"><Clock3 size={12} />{selected.year_built}</p>
                  </div>
                  <div className="panel-soft p-3 sm:col-span-2">
                    <p className="text-white/40 mb-1">Architecture Type</p>
                    <p className="text-white/85 flex items-center gap-1"><Landmark size={12} />{selected.architecture_type}</p>
                  </div>
                </div>

                <p className="text-body">{selected.description}</p>

                {selected.details.length > 0 && (
                  <div>
                    <p className="text-caption mb-2" style={{ color: '#00D1B2' }}>Key Details</p>
                    <ul className="list-disc pl-5 space-y-1 text-sm text-white/75">
                      {selected.details.map((detail) => (
                        <li key={detail}>{detail}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </motion.article>
        )}
      </div>
    </main>
  )
}
