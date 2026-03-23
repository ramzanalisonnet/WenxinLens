// API client for WenxinLens backend
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'
import type {
  RecognitionResult,
  ChatResponse,
  SiteInfo,
  BuildingKnowledge,
  AdvancedFeaturesResponse,
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
      const message = error.response?.data?.detail || error.message || 'An error occurred'
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
      `/recognition/analyze?language=${language}&detail_level=${detailLevel}`,
      form,
      { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 90000 }
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
    const { data } = await api.post(`/chat/session?language=${language}`)
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

export default api
