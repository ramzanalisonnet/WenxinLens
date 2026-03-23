'use client'

import type { CrossCivilizationData } from '@/types'

interface Props {
  data?: CrossCivilizationData
}

export function ComparisonPanel({ data }: Props) {
  return (
    <section className="panel p-6">
      <h3 className="title-card">Cross-Civilization Comparison</h3>
      <p className="text-body mt-2">Global style matching with structural and symbolic contrast.</p>

      {!data && <p className="text-caption mt-4">Run analysis to compare with global architecture traditions.</p>}

      {data && (
        <>
          <div className="mt-4" style={{ display: 'grid', gap: '10px' }}>
            {data.comparisons.map((item) => (
              <article key={`${item.civilization}-${item.building}`} className="surface-soft p-4" style={{ borderRadius: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px' }}>
                  <p style={{ fontWeight: 700 }}>{item.building}</p>
                  <span className="text-caption">{item.similarity}% similarity</span>
                </div>
                <p className="text-caption mt-1">{item.civilization}</p>
                <p className="text-body mt-2">{item.style}</p>
              </article>
            ))}
          </div>
          <article className="surface-soft mt-4 p-4" style={{ borderRadius: '12px' }}>
            <p className="text-body">{data.narrative}</p>
          </article>
        </>
      )}
    </section>
  )
}
