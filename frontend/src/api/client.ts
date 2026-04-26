import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'X-API-Key': localStorage.getItem('api_key') || 'dev-api-key-change-me',
    'Content-Type': 'application/json',
  },
})

export function setApiKey(key: string) {
  localStorage.setItem('api_key', key)
  api.defaults.headers['X-API-Key'] = key
}

export function getApiKey(): string {
  return localStorage.getItem('api_key') || 'dev-api-key-change-me'
}

export interface TaskCreateRequest {
  url: string
  language?: string
  output_format?: 'txt' | 'srt' | 'vtt' | 'json'
  use_local?: boolean
  model_size?: 'tiny' | 'base' | 'small' | 'medium' | 'large-v3'
  device?: 'cpu' | 'cuda'
}

export interface TaskInfo {
  id: string
  status: 'pending' | 'downloading' | 'extracting_audio' | 'transcribing' | 'completed' | 'failed'
  url: string
  language: string
  output_format: string
  use_local: boolean
  model_size: string
  created_at: string
  updated_at: string | null
  completed_at: string | null
  error_message: string | null
  result_url: string | null
  progress: number
}

export interface TaskResult {
  id: string
  status: string
  language: string | null
  duration: number | null
  segments: Array<{
    id: number
    start: number
    end: number
    text: string
    speaker?: string
  }> | null
  full_text: string | null
  output_file: string | null
  error_message: string | null
}

export const tasksApi = {
  create: (data: TaskCreateRequest) => api.post<TaskInfo>('/api/tasks', data),
  list: (skip = 0, limit = 20) => api.get<TaskInfo[]>(`/api/tasks?skip=${skip}&limit=${limit}`),
  get: (id: string) => api.get<TaskInfo>(`/api/tasks/${id}`),
  getResult: (id: string) => api.get<TaskResult>(`/api/tasks/${id}/result`),
  download: (id: string) => {
    const base = API_BASE || window.location.origin
    return `${base}/api/tasks/${id}/download?api_key=${getApiKey()}`
  },
}

export const healthApi = {
  check: () => api.get('/api/health'),
}

export function wsUrl(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const base = API_BASE ? API_BASE.replace(/^http/, 'ws') : `${protocol}//${host}`
  return `${base}/ws/tasks?api_key=${getApiKey()}`
}
