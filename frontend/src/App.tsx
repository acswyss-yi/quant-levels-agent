import { useRef, useState } from 'react'
import ApiKeyModal      from './components/ApiKeyModal'
import Sidebar          from './components/Sidebar'
import PriceHeader      from './components/PriceHeader'
import CandlestickChart from './components/CandlestickChart'
import MetricCards      from './components/MetricCards'
import AgentProgress    from './components/AgentProgress'
import ReportPanel      from './components/ReportPanel'
import DingTalkPush     from './components/DingTalkPush'
import RawDataViewer    from './components/RawDataViewer'
import { fetchAnalysis, streamAgent } from './api/client'
import type { AnalysisResponse, ToolCallStep } from './types'

function getStoredKey(): string {
  return localStorage.getItem('qwen_api_key') ?? ''
}

export default function App() {
  const [apiKey,    setApiKey]    = useState<string>(getStoredKey)
  const [loading,   setLoading]   = useState(false)
  const [error,     setError]     = useState('')
  const [result,    setResult]    = useState<AnalysisResponse | null>(null)
  const [steps,     setSteps]     = useState<ToolCallStep[]>([])
  const [agentBusy, setAgentBusy] = useState(false)
  const [report,    setReport]    = useState('')
  const [curSymbol, setCurSymbol] = useState('')
  const [curTf,     setCurTf]     = useState('')
  const abortRef = useRef<AbortController | null>(null)

  if (!apiKey) {
    return <ApiKeyModal onConfirm={setApiKey} />
  }

  async function handleRun(params: { symbol: string; timeframe: string; limit: number; model: string }) {
    abortRef.current?.abort()
    abortRef.current = new AbortController()

    setLoading(true)
    setError('')
    setResult(null)
    setSteps([])
    setReport('')
    setAgentBusy(false)
    setCurSymbol(params.symbol)
    setCurTf(params.timeframe)

    // Phase 1: 数据获取 + TA 计算（立即渲染图表）
    let analysis: AnalysisResponse
    try {
      analysis = await fetchAnalysis({ ...params, api_key: apiKey })
      setResult(analysis)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '数据获取失败')
      setLoading(false)
      return
    }

    // Phase 2: Agent SSE 流式分析
    setAgentBusy(true)
    try {
      await streamAgent(
        { ...params, api_key: apiKey },
        {
          onToolCall: step => setSteps(prev => [...prev, step]),
          onReport:   content => setReport(content),
          onDone:     () => { setAgentBusy(false); setLoading(false) },
          onError:    msg => { setError(msg); setAgentBusy(false); setLoading(false) },
        },
        abortRef.current.signal,
      )
    } catch {
      setAgentBusy(false)
      setLoading(false)
    }
  }

  return (
    <div style={styles.app}>
      <Sidebar loading={loading} onRun={handleRun} />

      <main style={styles.main}>
        {!result && !loading && (
          <div style={styles.empty}>
            <div style={styles.emptyTitle}>Quant Levels Agent</div>
            <div style={styles.emptyHint}>← 在左侧设置参数后点击「开始分析」</div>
          </div>
        )}

        {loading && !result && (
          <div style={styles.loadingWrap}>
            <span style={styles.loadingSpinner} />
            <span style={styles.loadingText}>
              正在获取 {curSymbol} {curTf} 行情数据...
            </span>
          </div>
        )}

        {error && <div style={styles.errorBanner}>{error}</div>}

        {result && (
          <>
            <PriceHeader
              symbol={result.symbol}
              timeframe={result.timeframe}
              taData={result.ta_data}
              klineCount={result.kline_count}
              latestTs={result.latest_ts}
            />

            <CandlestickChart ohlcv={result.ohlcv} taData={result.ta_data} />

            <MetricCards indicators={result.ta_data.indicators} />

            <hr style={styles.divider} />

            <AgentProgress steps={steps} loading={agentBusy} />

            <ReportPanel report={report} />

            {report && (
              <>
                <hr style={styles.divider} />
                <div style={styles.bottomRow}>
                  <div style={styles.codeWrap}>
                    <pre style={styles.code}>{report}</pre>
                  </div>
                  <div style={styles.actions}>
                    <DingTalkPush report={report} symbol={curSymbol} timeframe={curTf} />
                  </div>
                </div>
                <RawDataViewer data={result.ta_data} />
              </>
            )}
          </>
        )}
      </main>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  app: {
    display: 'flex', minHeight: '100vh',
    fontFamily: 'Inter, system-ui, sans-serif',
    background: '#fff', color: '#161616',
  },
  main:       { flex: 1, padding: '20px 24px', overflowY: 'auto', minWidth: 0 },
  empty:      { paddingTop: 80, textAlign: 'center' },
  emptyTitle: { fontSize: 22, fontWeight: 700, marginBottom: 8 },
  emptyHint:  { fontSize: 13, color: '#999' },
  errorBanner: {
    background: '#FFF1F1', border: '1px solid #FFCDD2',
    borderRadius: 4, padding: '10px 14px',
    color: '#DA1E28', fontSize: 13, marginBottom: 12,
  },
  loadingWrap: {
    display: 'flex', alignItems: 'center', gap: 10,
    padding: '60px 0', justifyContent: 'center',
  },
  loadingSpinner: {
    display: 'inline-block', width: 18, height: 18,
    border: '2px solid #E0E0E0', borderTopColor: '#0068FF',
    borderRadius: '50%', animation: 'spin 0.8s linear infinite',
  },
  loadingText: { fontSize: 14, color: '#666' },
  divider:  { border: 'none', borderTop: '1px solid #E0E0E0', margin: '16px 0' },
  bottomRow: { display: 'flex', gap: 16, alignItems: 'flex-start' },
  codeWrap: {
    flex: 4,
    background: '#F9FAFB', border: '1px solid #E0E0E0',
    borderRadius: 4, overflow: 'hidden',
  },
  code: {
    margin: 0, padding: '12px 14px',
    fontSize: 12, color: '#555', overflowX: 'auto',
    lineHeight: 1.5, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
  },
  actions: { flex: 1.5, minWidth: 180 },
}
