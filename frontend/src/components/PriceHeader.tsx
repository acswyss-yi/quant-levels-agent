import type { TaData } from '../types'

interface Props {
  symbol: string
  timeframe: string
  taData: TaData
  klineCount: number
  latestTs: string
}

export default function PriceHeader({ symbol, timeframe, taData, klineCount, latestTs }: Props) {
  const current   = taData.current_price
  const ma20pct   = taData.indicators.price_vs_ma20_pct
  const isUp      = (ma20pct ?? 0) >= 0
  const pctStr    = ma20pct != null ? `${ma20pct > 0 ? '+' : ''}${ma20pct.toFixed(2)}% vs MA20` : ''
  const arrow     = isUp ? '▲' : '▼'
  const pctColor  = isUp ? '#24A148' : '#DA1E28'

  const fmt = (v: number) =>
    v >= 10000 ? v.toLocaleString('en-US', { maximumFractionDigits: 2 })
               : String(parseFloat(v.toPrecision(6)))

  return (
    <div style={styles.row}>
      <span style={styles.symbol}>{symbol}</span>
      <span style={styles.tf}>{timeframe}</span>
      <span style={styles.price}>{fmt(current)}</span>
      {pctStr && (
        <span style={{ ...styles.pct, color: pctColor }}>
          {arrow} {pctStr}
        </span>
      )}
      <span style={styles.right}>
        {klineCount} 根K线 · 最新 {latestTs}
      </span>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  row: {
    display: 'flex',
    alignItems: 'center',
    gap: 0,
    padding: '10px 0',
    borderBottom: '1px solid #E0E0E0',
    marginBottom: 10,
    flexWrap: 'wrap',
  },
  symbol: { fontSize: 18, fontWeight: 700, color: '#161616', marginRight: 8 },
  tf:     { fontSize: 13, color: '#999',   marginRight: 16 },
  price:  { fontSize: 28, fontWeight: 700, color: '#161616', fontVariantNumeric: 'tabular-nums', marginRight: 10 },
  pct:    { fontSize: 13, fontWeight: 600, marginRight: 24 },
  right:  { marginLeft: 'auto', fontSize: 12, color: '#999', whiteSpace: 'nowrap' },
}
