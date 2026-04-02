'use client'

import { useRef, useState } from 'react'

interface VoiceInputProps {
  onAudioReady: (audioBlob: Blob) => Promise<void>
  disabled?: boolean
}

export function VoiceInput({ onAudioReady, disabled = false }: VoiceInputProps) {
  const [recording, setRecording] = useState(false)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])

  const startRecording = async () => {
    if (disabled || recording) return
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const recorder = new MediaRecorder(stream)
    chunksRef.current = []

    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunksRef.current.push(event.data)
      }
    }

    recorder.onstop = async () => {
      const audio = new Blob(chunksRef.current, { type: 'audio/webm' })
      try {
        await onAudioReady(audio)
      } finally {
        stream.getTracks().forEach((track) => track.stop())
      }
    }

    mediaRecorderRef.current = recorder
    recorder.start()
    setRecording(true)
  }

  const stopRecording = () => {
    const recorder = mediaRecorderRef.current
    if (!recorder || recorder.state === 'inactive') return
    recorder.stop()
    setRecording(false)
  }

  return (
    <button
      className="btn btn-secondary"
      onClick={recording ? stopRecording : startRecording}
      disabled={disabled}
      aria-label={recording ? 'Stop recording' : 'Start recording'}
    >
      {recording ? 'Stop Voice Input' : 'Voice Input'}
    </button>
  )
}
