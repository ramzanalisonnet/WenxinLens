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
  const rootRef = useRef<Group>(null)
  const weight = visemeWeight(visemeCode, visemeLevel)
  const mouthScaleY = state === 'SPEAKING' ? 0.12 + weight * 0.42 : 0.1
  const mouthScaleX = state === 'SPEAKING' ? 0.16 + weight * 0.2 : 0.17
  const jacketColor = state === 'THINKING' ? '#22355E' : state === 'LISTENING' ? '#1F4E4A' : '#1F2B45'
  const accentColor = state === 'SPEAKING' ? '#FF6B6D' : '#00D1B2'

  useFrame(({ clock }) => {
    if (!rootRef.current) return
    const t = clock.getElapsedTime()
    rootRef.current.rotation.y = Math.sin(t * 0.55) * 0.06
    rootRef.current.position.y = -0.46 + Math.sin(t * 1.4) * 0.016
  })

  return (
    <group ref={rootRef} position={[0, -0.46, 0]}>
      <mesh position={[0, 1.26, -0.5]}>
        <torusGeometry args={[0.98, 0.026, 24, 96]} />
        <meshStandardMaterial color={accentColor} emissive={accentColor} emissiveIntensity={0.3} transparent opacity={0.28} />
      </mesh>

      <mesh position={[0, 1.1, 0]} scale={[0.94, 1.0, 0.94]}>
        <sphereGeometry args={[0.47, 44, 44]} />
        <meshStandardMaterial color={'#F5C9A8'} metalness={0.02} roughness={0.62} />
      </mesh>

      <mesh position={[0, 1.31, -0.02]} scale={[0.96, 0.66, 1.0]}>
        <sphereGeometry args={[0.5, 44, 44]} />
        <meshStandardMaterial color={'#1A2134'} metalness={0.18} roughness={0.38} />
      </mesh>

      <mesh position={[0, 0.78, 0.03]} scale={[0.22, 0.3, 0.22]}>
        <capsuleGeometry args={[0.24, 0.55, 8, 24]} />
        <meshStandardMaterial color={'#E9B590'} roughness={0.65} />
      </mesh>

      <mesh position={[0, 0.18, 0]} scale={[0.96, 1.05, 0.84]}>
        <capsuleGeometry args={[0.52, 0.92, 8, 32]} />
        <meshStandardMaterial color={jacketColor} metalness={0.08} roughness={0.52} />
      </mesh>

      <mesh position={[0, 0.38, 0.34]} scale={[0.34, 0.42, 0.08]}>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color={'#F4F7FF'} roughness={0.36} />
      </mesh>

      <mesh position={[0, 0.2, 0.39]} scale={[0.09, 0.27, 0.07]}>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color={'#2C6FD6'} metalness={0.14} roughness={0.4} />
      </mesh>

      <mesh position={[-0.2, 1.11, 0.4]} scale={[0.11, 0.075, 0.07]}>
        <sphereGeometry args={[1, 20, 20]} />
        <meshStandardMaterial color={'#FFFFFF'} roughness={0.22} />
      </mesh>
      <mesh position={[0.2, 1.11, 0.4]} scale={[0.11, 0.075, 0.07]}>
        <sphereGeometry args={[1, 20, 20]} />
        <meshStandardMaterial color={'#FFFFFF'} roughness={0.22} />
      </mesh>

      <mesh position={[-0.2, 1.11, 0.46]} scale={[0.04, 0.04, 0.04]}>
        <sphereGeometry args={[1, 16, 16]} />
        <meshStandardMaterial color={'#1E2C45'} roughness={0.25} />
      </mesh>
      <mesh position={[0.2, 1.11, 0.46]} scale={[0.04, 0.04, 0.04]}>
        <sphereGeometry args={[1, 16, 16]} />
        <meshStandardMaterial color={'#1E2C45'} roughness={0.25} />
      </mesh>

      <mesh position={[0, 1.01, 0.45]} rotation={[Math.PI / 2.2, 0, 0]} scale={[0.03, 0.07, 0.03]}>
        <coneGeometry args={[1, 1, 16]} />
        <meshStandardMaterial color={'#D4A17D'} roughness={0.62} />
      </mesh>

      <mesh position={[0, 0.92, 0.46]} scale={[mouthScaleX, mouthScaleY, 0.04]}>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color={'#8B3942'} metalness={0.05} roughness={0.45} />
      </mesh>

      <mesh position={[-0.58, 0.2, -0.01]} scale={[0.29, 0.4, 0.48]}>
        <sphereGeometry args={[1, 20, 20]} />
        <meshStandardMaterial color={jacketColor} metalness={0.08} roughness={0.52} />
      </mesh>
      <mesh position={[0.58, 0.2, -0.01]} scale={[0.29, 0.4, 0.48]}>
        <sphereGeometry args={[1, 20, 20]} />
        <meshStandardMaterial color={jacketColor} metalness={0.08} roughness={0.52} />
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
        <Canvas camera={{ position: [0, 0.95, 3.15], fov: 34 }}>
          <ambientLight intensity={0.45} />
          <hemisphereLight intensity={0.7} color={'#f1f5ff'} groundColor={'#1e293b'} />
          <directionalLight position={[4, 5, 3]} intensity={1.15} />
          <directionalLight position={[-3, 2, -2]} intensity={0.42} />
          <Suspense fallback={fallback}>
            {hasModel ? <GLBAvatar state={state} visemeLevel={visemeLevel} visemeCode={visemeCode} /> : fallback}
          </Suspense>
          <OrbitControls
            enablePan={false}
            enableDamping
            target={[0, 0.62, 0]}
            minDistance={2.5}
            maxDistance={3.8}
            maxPolarAngle={1.7}
          />
        </Canvas>
      </div>
    </div>
  )
}
