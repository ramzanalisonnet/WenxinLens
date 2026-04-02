'use client'

import { Suspense, useEffect, useMemo, useRef, useState } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, useAnimations, useGLTF } from '@react-three/drei'
import type { Group, Mesh } from 'three'
import type { AvatarState } from '@/types'

interface AvatarViewerProps {
  state: AvatarState
  visemeLevel: number
  visemeCode: string
}

const VISEME_OPENNESS: Record<string, number> = {
  A: 1.0,
  B: 0.8,
  C: 0.7,
  D: 0.45,
  E: 0.55,
  F: 0.35,
  G: 0.3,
  H: 0.25,
  X: 0.08,
}

function visemeWeight(code: string, level: number): number {
  const base = VISEME_OPENNESS[(code || 'X').toUpperCase()] ?? 0.2
  return Math.max(0.05, Math.min(1.0, base * (0.6 + level * 0.7)))
}

function findClipName(available: string[], state: AvatarState): string | null {
  const low = available.map((name) => name.toLowerCase())
  const pick = (tokens: string[]) => {
    const index = low.findIndex((n) => tokens.some((token) => n.includes(token)))
    return index >= 0 ? available[index] : null
  }

  if (state === 'SPEAKING') return pick(['talk', 'speak'])
  if (state === 'THINKING') return pick(['think'])
  if (state === 'LISTENING') return pick(['listen'])
  return pick(['idle'])
}

function GLBAvatar({ state, visemeLevel, visemeCode }: { state: AvatarState; visemeLevel: number; visemeCode: string }) {
  const group = useRef<Group>(null)
  const { scene, animations } = useGLTF('/models/avatar.glb') as any
  const { actions } = useAnimations(animations, group)
  const visemeMeshesRef = useRef<Array<{ mesh: Mesh; dict: Record<string, number> }>>([])

  useEffect(() => {
    const meshes: Array<{ mesh: Mesh; dict: Record<string, number> }> = []
    scene.traverse((node: any) => {
      if (node?.isMesh && node.morphTargetDictionary && node.morphTargetInfluences) {
        meshes.push({ mesh: node as Mesh, dict: node.morphTargetDictionary as Record<string, number> })
      }
    })
    visemeMeshesRef.current = meshes
  }, [scene])

  useEffect(() => {
    if (!actions) return
    const keys = Object.keys(actions)
    if (keys.length === 0) return

    const clip = findClipName(keys, state) || keys[0]
    keys.forEach((name) => {
      const action = actions[name]
      if (!action) return
      if (name === clip) {
        action.reset().fadeIn(0.2).play()
      } else {
        action.fadeOut(0.2)
      }
    })
  }, [actions, state])

  useFrame(() => {
    const targets = visemeMeshesRef.current
    if (targets.length === 0) return

    const w = visemeWeight(visemeCode, visemeLevel)
    const code = (visemeCode || 'X').toUpperCase()

    const tokenMap: Record<string, string[]> = {
      A: ['aa', 'ah', 'mouthopen', 'jawopen', 'viseme_aa'],
      B: ['ee', 'ih', 'viseme_e'],
      C: ['oh', 'ou', 'oo', 'viseme_o'],
      D: ['l', 'dd', 'nn', 'rr'],
      E: ['ch', 'sh', 'j', 'zh'],
      F: ['ff', 'vv', 'f', 'v'],
      G: ['kk', 'gg', 'k', 'g'],
      H: ['pp', 'bb', 'mm', 'p', 'b', 'm'],
      X: ['sil', 'rest'],
    }

    const selectedTokens = tokenMap[code] || tokenMap.X

    for (const item of targets) {
      const meshAny: any = item.mesh
      const influences: number[] = meshAny.morphTargetInfluences || []
      for (let i = 0; i < influences.length; i++) {
        influences[i] *= 0.82
      }

      Object.entries(item.dict).forEach(([name, idx]) => {
        const low = name.toLowerCase()
        if (selectedTokens.some((token) => low.includes(token))) {
          influences[idx] = Math.max(influences[idx] || 0, w)
        }
      })
    }
  })

  return <primitive ref={group} object={scene} scale={1.65} position={[0, -1.55, 0]} />
}

function PlaceholderAvatar({ state, visemeLevel, visemeCode }: { state: AvatarState; visemeLevel: number; visemeCode: string }) {
  const weight = visemeWeight(visemeCode, visemeLevel)
  const mouthScaleY = state === 'SPEAKING' ? 0.3 + weight * 1.6 : 0.45
  const mouthScaleX = state === 'SPEAKING' ? 0.2 + weight * 0.6 : 0.24
  const bodyColor =
    state === 'THINKING' ? '#3B4D7A' : state === 'LISTENING' ? '#305D58' : state === 'SPEAKING' ? '#6D3D3D' : '#2E3550'

  return (
    <group position={[0, -0.25, 0]}>
      <mesh position={[0, 1.0, 0]}>
        <sphereGeometry args={[0.52, 32, 32]} />
        <meshStandardMaterial color={bodyColor} metalness={0.2} roughness={0.5} />
      </mesh>

      <mesh position={[0, 0.9, 0.47]} scale={[mouthScaleX, mouthScaleY, 0.1]}>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color={'#BFC8DF'} metalness={0.1} roughness={0.6} />
      </mesh>

      <mesh position={[0, 0.1, 0]}>
        <capsuleGeometry args={[0.48, 1.0, 6, 16]} />
        <meshStandardMaterial color={'#1E2640'} metalness={0.2} roughness={0.6} />
      </mesh>
    </group>
  )
}

export function AvatarViewer({ state, visemeLevel, visemeCode }: AvatarViewerProps) {
  const [hasModel, setHasModel] = useState<boolean | null>(null)

  useEffect(() => {
    let cancelled = false
    fetch('/models/avatar.glb', { method: 'HEAD' })
      .then((res) => {
        if (!cancelled) setHasModel(res.ok)
      })
      .catch(() => {
        if (!cancelled) setHasModel(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const fallback = useMemo(
    () => <PlaceholderAvatar state={state} visemeLevel={visemeLevel} visemeCode={visemeCode} />,
    [state, visemeLevel, visemeCode]
  )

  return (
    <div className="panel p-4" style={{ minHeight: 420 }}>
      <div className="surface-soft" style={{ height: 380, borderRadius: 14, overflow: 'hidden' }}>
        <Canvas camera={{ position: [0, 1.2, 2.4], fov: 40 }}>
          <ambientLight intensity={0.7} />
          <directionalLight position={[4, 5, 3]} intensity={1.0} />
          <directionalLight position={[-3, 2, -2]} intensity={0.35} />
          <Suspense fallback={fallback}>
            {hasModel ? <GLBAvatar state={state} visemeLevel={visemeLevel} visemeCode={visemeCode} /> : fallback}
          </Suspense>
          <OrbitControls enablePan={false} enableDamping minDistance={1.6} maxDistance={3.0} maxPolarAngle={1.8} />
        </Canvas>
      </div>
    </div>
  )
}
