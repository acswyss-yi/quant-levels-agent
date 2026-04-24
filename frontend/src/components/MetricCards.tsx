import type { Indicators } from '../types'

interface Props {
  indicators: Indicators
}

interface CardProps {
  label: string
  value: string
  delta: string
  deltaColor: string
}

function Card({ label, value, delta, deltaColor }: CardProps) {
  return (
    <div style={styles.card}>
      <div style={styles.cardLabel}>{label}</div>
      <div style={styles.cardValue}>{value}</div>
      <div style={{ ...styles.cardDelta, color: deltaColor }}>{delta}</div>
    </div>
  )
}

export default function MetricCards({ indicators }: Props) {
  const { rsi, macd_histogram, volume_ratio_5_20, price_vs_ma20_pct } = indicators

  const rsiLabel  = rsi > 70 ? '⚠ 超买' : rsi < 30 ? '⚠ 超卖' : '中性'
  const rsiColor  = rsi > 70 ? '#DA1E28' : rsi < 30 ? '#0068FF' : '#999'
  const macdLabel = macd_histogram > 0 ? '多头' : '空头'
  const macdColor = macd_histogram > 0 ? '#24A148' : '#DA1E28'
  const volLabel  = volume_ratio_5_20 > 1.2 ? '放量' : volume_ratio_5_20 < 0.8 ? '缩量' : '正常'
  const volColor  = volume_ratio_5_20 > 1.2 ? '#24A148' : volume_ratio_5_20 < 0.8 ? '#DA1E28' : '#999'
  const maLabel   = price_vs_ma20_pct != null ? `${price_vs_ma20_pct > 0 ? '↑' : '↓'} MA20` : 'N/A'
  const maColor   = price_vs_ma20_pct != null ? (price_vs_ma20_pct > 0 ? '#24A148' : '#DA1E28') : '#999'

  return (
    <div style={styles.row}>
      <Card label="RSI (14)"  value={String(rsi)}
            delta={rsiLabel}  deltaColor={rsiColor} />
      <Card label="MACD 柱"   value={`${macd_histogram > 0 ? '+' : ''}${macd_histogram.toFixed(4)}`}
            delta={macdLabel} deltaColor={macdColor} />
      <Card label="量比 5/20" value={`${volume_ratio_5_20}x`}
            delta={volLabel}  deltaColor={volColor} />
      <Card label="MA20 偏离" value={price_vs_ma20_pct != null ? `${price_vs_ma20_pct > 0 ? '+' : ''}${price_vs_ma20_pct.toFixed(2)}%` : 'N/A'}
            delta={maLabel}   deltaColor={maColor} />
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  row:        { display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12, margin: '12px 0' },
  card:       { background: '#F9FAFB', border: '1px solid #E0E0E0', borderRadius: 4, padding: '12px 16px' },
  cardLabel:  { fontSize: 12, color: '#999', marginBottom: 4 },
  cardValue:  { fontSize: 22, fontWeight: 700, color: '#161616', fontVariantNumeric: 'tabular-nums' },
  cardDelta:  { fontSize: 12, marginTop: 2 },
}
