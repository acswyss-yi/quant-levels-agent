import axios from 'axios'
import { fetchEventSource } from '@microsoft/fetch-event-source'
import type { AnalysisResponse, ToolCallStep } from '../types'

const http = axios.create({ baseURL: '' })

export async function fetchAnalysis(params: {
  symbol: string
  timeframe: string
  limit: number
  api_key: string
}): Promise<AnalysisResponse> {
  const { data } = await http.post<AnalysisResponse>('/api/analysis', params)
  return data
}

export interface AgentStreamHandlers {
  onToolCall: (step: ToolCallStep) => void
  onReport: (content: string) => void
  onDone: () => void
  onError: (message: string) => void
}

export async function streamAgent(
  params: {
    symbol: string
    timeframe: string
    limit: number
    model: string
    api_key: string
  },
  handlers: AgentStreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  await fetchEventSource('/api/agent/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
    signal,
    onmessage(ev) {
      // ping 心跳和空数据直接忽略（done 除外）
      if (!ev.data || ev.data === '{}') {
        if (ev.event === 'done') handlers.onDone()
        return
      }
      if (ev.event === 'ping') return
      const payload = JSON.parse(ev.data)
      switch (ev.event) {
        case 'tool_call':
          handlers.onToolCall(payload as ToolCallStep)
          break
        case 'report':
          handlers.onReport(payload.content as string)
          break
        case 'error':
          handlers.onError(payload.message as string)
          break
        case 'done':
          handlers.onDone()
          break
      }
    },
    onerror(err) {
      // AbortError 是主动取消，不作为错误上报
      if (err instanceof DOMException && err.name === 'AbortError') {
        throw err
      }
      handlers.onError(String(err))
      throw err
    },
  })
}

export async function pushDingTalk(params: {
  webhook_token: string
  report: string
  symbol: string
  timeframe: string
  secret?: string
}): Promise<{ success: boolean; error?: string }> {
  const { data } = await http.post('/api/dingtalk', params)
  return data
}
