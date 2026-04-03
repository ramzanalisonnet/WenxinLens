'use client'

import ReactMarkdown from 'react-markdown'
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
            <div className="text-body" style={{ lineHeight: 1.75 }}>
              <ReactMarkdown
                components={{
                  h4: ({ children }) => <h4 className="text-caption" style={{ marginTop: 12, marginBottom: 8, color: 'var(--highlight)' }}>{children}</h4>,
                  p: ({ children }) => <p className="text-body" style={{ marginBottom: 10 }}>{children}</p>,
                  ul: ({ children }) => <ul style={{ paddingLeft: 18, marginBottom: 10 }}>{children}</ul>,
                  li: ({ children }) => <li className="text-body" style={{ marginBottom: 6 }}>{children}</li>,
                  strong: ({ children }) => <strong style={{ color: 'var(--text)' }}>{children}</strong>,
                }}
              >
                {data.narrative}
              </ReactMarkdown>
            </div>
          </article>
        </>
      )}
    </section>
  )
}
