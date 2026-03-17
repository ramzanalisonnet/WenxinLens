// Global TypeScript types for WenxinLens

export interface RecognitionResult {
  result_id: string
  building_name: string
  building_name_zh: string
  architecture_style: string
  dynasty: string
  dynasty_zh: string
  confidence_score: number
  structural_features: string[]
  location: string | null
  coordinates: { lat: number; lon: number } | null
  description: string
  description_zh: string
  cultural_significance: string
  image_url: string | null
  follow_up_questions?: string[]
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: Array<{ text: string; source: string }>
}

export interface ChatSession {
  session_id: string
  language: string
  created_at: string
  messages: ChatMessage[]
}

export interface ChatResponse {
  session_id: string
  message: string
  follow_up_questions: string[]
  sources: Array<{ text: string; source: string }>
  language: string
}

export interface SiteInfo {
  site_id: string
  name: string
  name_zh: string
  dynasty: string
  architecture_style: string
  distance_km: number | null
  coordinates: { lat: number; lon: number } | null
  thumbnail_url: string | null
  short_description: string
  tags: string[]
}

export interface BuildingKnowledge {
  building_id: string
  name: string
  name_zh: string
  dynasty: string
  architect: string | null
  location: string
  year_built: string | null
  architectural_style: string
  materials: string[]
  symbolism: string[]
  historical_events: string[]
  related_buildings: string[]
  description: string
  description_zh: string
}

export interface GraphNode {
  id: string
  label: string
  name: string
}

export interface GraphEdge {
  source: string
  target: string
  relation: string
}

export type Language = 'en' | 'zh'
export type DetailLevel = 'tourist' | 'standard' | 'academic'
