'use client'

import ReactMarkdown from 'react-markdown'
import type { CinematicStoryData } from '@/types'

interface Props {
  data?: CinematicStoryData
}

export function CinematicStoryMode({ data }: Props) {
  return (
    <section className="panel p-6">
      <h3 className="title-card">Cinematic Story Mode</h3>
      <p className="text-body mt-2">Documentary-style script, scenes, and narration output plan.</p>

      {!data && <p className="text-caption mt-4">Run analysis to generate cinematic narrative output.</p>}

      {data && (
        <>
          <div className="mt-4" style={{ display: 'grid', gap: '10px' }}>
            {data.scene_plan.map((scene) => (
              <article key={scene.scene} className="surface-soft p-4" style={{ borderRadius: '12px' }}>
                <p style={{ fontWeight: 700 }}>Scene {scene.scene}: {scene.title}</p>
                <p className="text-body mt-1">{scene.focus}</p>
              </article>
            ))}
          </div>

          <article className="surface-soft mt-4 p-4" style={{ borderRadius: '12px' }}>
            <p className="text-caption">Narration Provider: {data.audio.provider}</p>
            <p className="text-caption">Audio Asset: {data.audio.audio_url}</p>
            <div className="text-body mt-3" style={{ lineHeight: 1.75 }}>
              <ReactMarkdown
                components={{
                  h4: ({ children }) => <h4 className="text-caption" style={{ marginTop: 12, marginBottom: 8, color: 'var(--highlight)' }}>{children}</h4>,
                  p: ({ children }) => <p className="text-body" style={{ marginBottom: 8 }}>{children}</p>,
                  ul: ({ children }) => <ul style={{ paddingLeft: 18, marginBottom: 8 }}>{children}</ul>,
                  li: ({ children }) => <li className="text-body" style={{ marginBottom: 4 }}>{children}</li>,
                  strong: ({ children }) => <strong style={{ color: 'var(--text)' }}>{children}</strong>,
                }}
              >
                {data.script}
              </ReactMarkdown>
            </div>
          </article>
        </>
      )}
    </section>
  )
}
