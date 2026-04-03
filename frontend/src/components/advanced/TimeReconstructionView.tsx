'use client'

import ReactMarkdown from 'react-markdown'
import type { TimeReconstructionData } from '@/types'

interface Props {
  data?: TimeReconstructionData
}

export function TimeReconstructionView({ data }: Props) {
  return (
    <section className="panel p-6">
      <h3 className="title-card">Time-Reconstruction AI</h3>
      <p className="text-body mt-2">Timeline snapshots grounded by retrieved historical records.</p>

      {!data && <p className="text-caption mt-4">Run analysis to render historical reconstruction snapshots.</p>}

      {data && (
        <div className="mt-5" style={{ display: 'grid', gap: '12px' }}>
          {data.snapshots.map((snap) => (
            <article key={snap.dynasty} className="surface-soft p-4" style={{ borderRadius: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'center' }}>
                <p style={{ fontWeight: 700 }}>{snap.dynasty}</p>
                <span className="text-caption">Generated</span>
              </div>
              <p className="text-caption mt-2">Prompt: {snap.prompt}</p>
              <div className="text-body mt-2" style={{ lineHeight: 1.75 }}>
                <ReactMarkdown
                  components={{
                    p: ({ children }) => <p className="text-body" style={{ marginBottom: 8 }}>{children}</p>,
                    ul: ({ children }) => <ul style={{ paddingLeft: 18, marginBottom: 8 }}>{children}</ul>,
                    li: ({ children }) => <li className="text-body" style={{ marginBottom: 4 }}>{children}</li>,
                  }}
                >
                  {snap.explanation}
                </ReactMarkdown>
              </div>
              <p className="text-caption mt-2">Image asset: {snap.image_url}</p>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
