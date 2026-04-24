import { useState } from 'react'

const PRESET_SYMBOLS = ['BTC', 'ETH', 'SOL', 'AAPL', 'NVDA', 'TSLA', '600519', '00700']
const TIMEFRAMES     = ['15min', '1h', '4h', '日线']
const MODELS         = ['qwen-max', 'qwen-plus', 'qwen-turbo']

interface Props {
  loading: boolean
  onRun: (params: { symbol: string; timeframe: string; limit: number; model: string }) => void
}

export default function Sidebar({ loading, onRun }: Props) {
  const [symbolSelect, setSymbolSelect] = useState('BTC')
  const [customSymbol, setCustomSymbol] = useState('')
  const [timeframe, setTimeframe]       = useState('4h')
  const [limit, setLimit]               = useState(300)
  const [model, setModel]               = useState('qwen-max')

  const symbol = symbolSelect === '自定义...' ? customSymbol : symbolSelect

  function handleRun() {
    if (!symbol.trim()) return
    onRun({ symbol: symbol.trim().toUpperCase(), timeframe, limit, model })
  }

  return (
    <aside style={styles.sidebar}>
      <div style={styles.title}>Quant Levels Agent</div>
      <hr style={styles.divider} />

      <label style={styles.label}>标的</label>
      <select value={symbolSelect} onChange={e => setSymbolSelect(e.target.value)} style={styles.select}>
        {PRESET_SYMBOLS.map(s => <option key={s}>{s}</option>)}
        <option>自定义...</option>
      </select>
      {symbolSelect === '自定义...' && (
        <input
          placeholder="如 MSFT / 000001"
          value={customSymbol}
          onChange={e => setCustomSymbol(e.target.value)}
          style={styles.input}
        />
      )}

      <label style={styles.label}>K 线周期</label>
      <div style={styles.radioGroup}>
        {TIMEFRAMES.map(tf => (
          <label key={tf} style={styles.radioLabel}>
            <input
              type="radio"
              name="tf"
              value={tf}
              checked={timeframe === tf}
              onChange={() => setTimeframe(tf)}
            />
            {tf}
          </label>
        ))}
      </div>

      <label style={styles.label}>K 线数量：{limit}</label>
      <input
        type="range"
        min={100} max={500} step={50}
        value={limit}
        onChange={e => setLimit(Number(e.target.value))}
        style={{ width: '100%' }}
      />
      <div style={styles.rangeHint}>
        <span>100</span><span>500</span>
      </div>

      <label style={styles.label}>千问模型</label>
      <select value={model} onChange={e => setModel(e.target.value)} style={styles.select}>
        {MODELS.map(m => <option key={m}>{m}</option>)}
      </select>

      <div style={{ flex: 1 }} />
      <hr style={styles.divider} />
      <button
        onClick={handleRun}
        disabled={loading || !symbol.trim()}
        style={{ ...styles.runBtn, opacity: (loading || !symbol.trim()) ? 0.6 : 1 }}
      >
        {loading ? '分析中...' : '▶  开始分析'}
      </button>
    </aside>
  )
}

const styles: Record<string, React.CSSProperties> = {
  sidebar: {
    width: 220,
    minWidth: 220,
    background: '#F9FAFB',
    borderRight: '1px solid #E0E0E0',
    padding: '20px 16px',
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
    height: '100vh',
    boxSizing: 'border-box',
    position: 'sticky',
    top: 0,
    overflowY: 'auto',
  },
  title:   { fontSize: 15, fontWeight: 700, color: '#161616' },
  divider: { border: 'none', borderTop: '1px solid #E0E0E0', margin: '4px 0' },
  label:   { fontSize: 12, color: '#666', marginTop: 4 },
  select: {
    width: '100%',
    padding: '6px 8px',
    border: '1px solid #E0E0E0',
    borderRadius: 4,
    fontSize: 13,
    background: '#fff',
  },
  input: {
    width: '100%',
    padding: '6px 8px',
    border: '1px solid #E0E0E0',
    borderRadius: 4,
    fontSize: 13,
    boxSizing: 'border-box',
  },
  radioGroup: { display: 'flex', flexWrap: 'wrap', gap: 6 },
  radioLabel: { fontSize: 13, display: 'flex', alignItems: 'center', gap: 3, cursor: 'pointer' },
  rangeHint: { display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#999' },
  runBtn: {
    padding: '10px 0',
    background: '#0068FF',
    color: '#fff',
    border: 'none',
    borderRadius: 4,
    fontSize: 15,
    fontWeight: 600,
    cursor: 'pointer',
    width: '100%',
  },
}
