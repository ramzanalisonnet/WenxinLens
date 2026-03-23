'use client'

import type { CulturalDnaData } from '@/types'

interface Props {
  data?: CulturalDnaData
}

const labels: Array<{ key: keyof CulturalDnaData['scores']; label: string }> = [
  { key: 'confucian_influence', label: 'Confucianism' },
  { key: 'taoist_symbolism', label: 'Taoism' },
  { key: 'buddhist_influence', label: 'Buddhism' },
  { key: 'imperial_authority', label: 'Imperial Authority' },
  { key: 'regional_influence', label: 'Regional Influence' },
  { key: 'symbolism_density', label: 'Symbolism Density' },
]

export function CulturalDnaDashboard({ data }: Props) {
  return (
    <section className="panel p-6">
      <h3 className="title-card">Cultural DNA Analysis</h3>
      <p className="text-body mt-2">Quantified influence profile with explainable narrative grounding.</p>

      {!data && <p className="text-caption mt-4">Run analysis to generate cultural DNA scoring.</p>}

      {data && (
        <>
          <div className="mt-4" style={{ display: 'grid', gap: '10px' }}>
            {labels.map((item) => {
              const value = data.scores[item.key]
              return (
                <div key={item.key}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span className="text-caption">{item.label}</span>
                    <span className="text-caption">{value}%</span>
                  </div>
                  <div style={{ height: '8px', background: 'rgba(255,255,255,0.08)', borderRadius: '999px', overflow: 'hidden' }}>
                    <div style={{ width: `${value}%`, height: '100%', background: 'linear-gradient(90deg, var(--highlight), var(--accent))' }} />
                  </div>
                </div>
              )
            })}
          </div>
          <article className="surface-soft mt-4 p-4" style={{ borderRadius: '12px' }}>
            <p className="text-body">{data.analysis}</p>
          </article>
        </>
      )}
    </section>
  )
}
