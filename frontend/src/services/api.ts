// API client for WenxinLens backend
import axios, { AxiosInstance } from 'axios'
import type {
  RecognitionResult,
  ChatResponse,
  SiteInfo,
  BuildingKnowledge,
  DynastyCatalogItem,
  AdvancedFeaturesResponse,
  AvatarChatResponse,
  AvatarLipSyncResponse,
} from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: `${API_URL}/api/v1`,
    timeout: 60000,
    headers: { 'Content-Type': 'application/json' },
  })

  client.interceptors.request.use((config) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('wl_token') : null
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  client.interceptors.response.use(
    (response) => response,
    (error) => {
      const rawMessage = String(error?.message || '')
      if (error?.code === 'ECONNABORTED' || /timeout/i.test(rawMessage)) {
        return Promise.reject(
          new Error('Recognition is taking longer than expected. Please try again or switch Detail to Tourist.')
        )
      }
      const message = error.response?.data?.detail || rawMessage || 'An error occurred'
      return Promise.reject(new Error(message))
    }
  )

  return client
}

const api = createApiClient()

// ── Recognition ──────────────────────────────────────────────
export const recognitionApi = {
  analyzeImage: async (
    imageFile: File,
    language: string = 'en',
    detailLevel: string = 'standard'
  ): Promise<RecognitionResult> => {
    const form = new FormData()
    form.append('image', imageFile)
    const { data } = await api.post<RecognitionResult>(
      '/recognition/analyze',
      form,
      { params: { language, detail_level: detailLevel }, headers: { 'Content-Type': 'multipart/form-data' }, timeout: 180000 }
    )
    return data
  },

  listStyles: async () => {
    const { data } = await api.get('/recognition/styles')
    return data
  },
}

// ── Chat ─────────────────────────────────────────────────────
export const chatApi = {
  createSession: async (language: string = 'en'): Promise<{ session_id: string }> => {
    const { data } = await api.post('/chat/session', null, { params: { language } })
    return data
  },

  sendMessage: async (
    sessionId: string,
    message: string,
    language: string = 'en',
    buildingContext?: string
  ): Promise<ChatResponse> => {
    const { data } = await api.post<ChatResponse>('/chat/message', {
      session_id: sessionId,
      message,
      language,
      building_context: buildingContext,
      stream: false,
    })
    return data
  },

  getSession: async (sessionId: string) => {
    const { data } = await api.get(`/chat/session/${sessionId}`)
    return data
  },

  deleteSession: async (sessionId: string) => {
    await api.delete(`/chat/session/${sessionId}`)
  },
}

// ── Tour ─────────────────────────────────────────────────────
export const tourApi = {
  getNearbySites: async (
    lat: number,
    lon: number,
    radiusKm: number = 20
  ): Promise<{ sites: SiteInfo[]; total: number }> => {
    const { data } = await api.get('/tour/nearby', { params: { lat, lon, radius_km: radiusKm } })
    return data
  },

  getSite: async (siteId: string): Promise<SiteInfo> => {
    const { data } = await api.get(`/tour/site/${siteId}`)
    return data
  },

  planRoute: async (siteIds: string[]) => {
    const { data } = await api.get('/tour/route', { params: { sites: siteIds.join(',') } })
    return data
  },
}

// ── Knowledge ────────────────────────────────────────────────
export const knowledgeApi = {
  getBuilding: async (name: string, language = 'en'): Promise<BuildingKnowledge> => {
    const { data } = await api.get(`/knowledge/building/${encodeURIComponent(name)}`, {
      params: { language },
    })
    return data
  },

  search: async (query: string, dynasty?: string, limit = 10): Promise<any[]> => {
    const { data } = await api.get('/knowledge/search', {
      params: { q: query, dynasty, limit },
    })
    return data
  },

  getDynastyBuildings: async (dynasty: string): Promise<any[]> => {
    const { data } = await api.get(`/knowledge/dynasty/${encodeURIComponent(dynasty)}`)
    return data
  },

  getGraphRelations: async (buildingName: string, depth = 2) => {
    const { data } = await api.get('/knowledge/graph/relations', {
      params: { building_name: buildingName, depth },
    })
    return data
  },

  listDynasties: async () => {
    const { data } = await api.get('/knowledge/dynasties')
    return data
  },

  getDynastyCatalog: async (): Promise<DynastyCatalogItem[]> => {
    const { data } = await api.get('/knowledge/dynasty-catalog')
    return data
  },
}

// ── Voice ────────────────────────────────────────────────────
export const voiceApi = {
  synthesize: async (
    text: string,
    language: string = 'en',
    voiceId: string = 'default'
  ): Promise<Blob> => {
    const response = await api.post(
      '/voice/synthesize',
      { text, language, voice_id: voiceId },
      { responseType: 'blob' }
    )
    return response.data
  },

  listVoices: async (language?: string) => {
    const { data } = await api.get('/voice/voices', { params: { language } })
    return data
  },
}

// ── Advanced Features ───────────────────────────────────────
export const advancedApi = {
  runAll: async (payload: {
    building_name: string
    dynasty: string
    architecture_style: string
    structural_features: string[]
    language?: 'en' | 'zh'
    user_message?: string
  }): Promise<AdvancedFeaturesResponse> => {
    const { data } = await api.post<AdvancedFeaturesResponse>('/advanced/all', payload)
    return data
  },

  historicalCharacterChat: async (payload: {
    building_name: string
    dynasty: string
    character_type: string
    message: string
    language?: 'en' | 'zh'
  }): Promise<{ character: string; persona_name: string; reply: string }> => {
    const { data } = await api.post('/advanced/historical-character', payload)
    return data
  },
}

// ── Avatar ───────────────────────────────────────────────────
export const avatarApi = {
  chat: async (payload: {
    building_name: string
    dynasty: string
    character_type: string
    message: string
    language?: 'en' | 'zh'
  }): Promise<AvatarChatResponse> => {
    const { data } = await api.post<AvatarChatResponse>('/avatar/chat', payload)
    return data
  },

  tts: async (payload: {
    text: string
    character_type: string
    language?: 'en' | 'zh'
  }): Promise<Blob> => {
    const response = await api.post('/avatar/tts', payload, { responseType: 'blob' })
    return response.data
  },

  stt: async (audioFile: Blob, language?: 'en' | 'zh'): Promise<{ text: string }> => {
    const form = new FormData()
    form.append('audio', audioFile, 'voice.webm')
    const { data } = await api.post('/avatar/stt', form, {
      params: language ? { language } : undefined,
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    })
    return data
  },

  lipsync: async (payload: {
    text: string
    duration_ms?: number
  }): Promise<AvatarLipSyncResponse> => {
    const { data } = await api.post<AvatarLipSyncResponse>('/avatar/lipsync', payload)
    return data
  },

  websocketUrl: () => {
    const normalized = API_URL.replace(/\/$/, '')
    const wsBase = normalized.startsWith('https://')
      ? normalized.replace('https://', 'wss://')
      : normalized.replace('http://', 'ws://')
    return `${wsBase}/api/v1/avatar/ws`
  },
}

export default api
