'use client'

import { useState } from 'react'
import { Navbar } from '@/components/Navbar'
import { advancedApi } from '@/services/api'
import type { AdvancedFeaturesResponse, Language } from '@/types'
import { TimeReconstructionView } from '@/components/advanced/TimeReconstructionView'
import { HistoricalCharacterChat } from '@/components/advanced/HistoricalCharacterChat'
import { CulturalDnaDashboard } from '@/components/advanced/CulturalDnaDashboard'
import { ComparisonPanel } from '@/components/advanced/ComparisonPanel'
import { CinematicStoryMode } from '@/components/advanced/CinematicStoryMode'

export default function AdvancedLabPage() {
  const [language, setLanguage] = useState<Language>('en')
  const [buildingName, setBuildingName] = useState('Temple of Heaven')
  const [dynasty, setDynasty] = useState('Ming')
  const [style, setStyle] = useState('imperial temple architecture')
  const [features, setFeatures] = useState('axial symmetry, timber frame, ceremonial altar')
  const [question, setQuestion] = useState('What made this building culturally influential?')
  const [data, setData] = useState<AdvancedFeaturesResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const run = async () => {
    if (!buildingName.trim()) return
    setLoading(true)
    setError('')
    try {
      const res = await advancedApi.runAll({
        building_name: buildingName,
        dynasty,
        architecture_style: style,
        structural_features: features.split(',').map((s) => s.trim()).filter(Boolean),
        user_message: question,
        language,
      })
      setData(res)
    } catch (e: any) {
      setError(e?.message || 'Failed to run advanced feature pipeline')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell min-h-screen">
      <Navbar />
      <main className="app-content container-1200 py-10">
        <section className="panel p-6 md:p-8">
          <h1 className="title-section">Advanced Research Lab</h1>
          <p className="text-body mt-3">
            Time reconstruction, historical characters, cultural DNA, civilization comparison, and cinematic storytelling.
          </p>

          <div className="mt-6" style={{ display: 'grid', gap: '12px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
              <input className="surface-soft" style={{ padding: '12px', color: 'var(--text)' }} value={buildingName} onChange={(e) => setBuildingName(e.target.value)} placeholder="Building Name" />
              <input className="surface-soft" style={{ padding: '12px', color: 'var(--text)' }} value={dynasty} onChange={(e) => setDynasty(e.target.value)} placeholder="Dynasty" />
              <input className="surface-soft" style={{ padding: '12px', color: 'var(--text)' }} value={style} onChange={(e) => setStyle(e.target.value)} placeholder="Architectural Style" />
            </div>

            <textarea className="surface-soft" style={{ padding: '12px', color: 'var(--text)', resize: 'vertical' }} rows={2} value={features} onChange={(e) => setFeatures(e.target.value)} placeholder="Structural features, comma separated" />
            <textarea className="surface-soft" style={{ padding: '12px', color: 'var(--text)', resize: 'vertical' }} rows={2} value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Research question for historical persona" />

            <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
              <select value={language} onChange={(e) => setLanguage(e.target.value as Language)} className="surface-soft" style={{ padding: '10px 12px', color: 'var(--text)' }}>
                <option value="en">English</option>
                <option value="zh">中文</option>
              </select>
              <button className="btn btn-primary" onClick={run} disabled={loading}>
                {loading ? 'Running full advanced pipeline...' : 'Run Advanced Pipeline'}
              </button>
            </div>
          </div>

          {error && (
            <p className="mt-4" style={{ color: '#FFB3B4' }}>{error}</p>
          )}

          {data?.summary && (
            <article className="surface-soft mt-5 p-4" style={{ borderRadius: '12px' }}>
              <p className="text-body">{data.summary}</p>
            </article>
          )}
        </section>

        <section className="mt-8" style={{ display: 'grid', gap: '16px' }}>
          <TimeReconstructionView data={data?.time_reconstruction} />
          <HistoricalCharacterChat
            seed={data?.historical_character}
            buildingName={buildingName}
            dynasty={dynasty}
            language={language}
          />
          <CulturalDnaDashboard data={data?.cultural_dna} />
          <ComparisonPanel data={data?.cross_civilization} />
          <CinematicStoryMode data={data?.cinematic_story} />
        </section>
      </main>
    </div>
  )
}
