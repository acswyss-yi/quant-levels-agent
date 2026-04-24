import type { ToolCallStep } from '../types'

interface Props {
  steps: ToolCallStep[]
  loading: boolean
}

export default function AgentProgress({ steps, loading }: Props) {
  if (steps.length === 0 && !loading) return null

  const summary = loading
    ? '🤖 Agent 分析中...'
    : `分析完成（共调用 ${steps.length} 次工具${steps.length > 1 ? '，多周期共振' : ''}）`

  return (
    <div style={styles.wrap}>
      <div style={styles.header}>
        {loading && <span style={styles.spinner} />}
        <span style={{ fontWeight: 600, fontSize: 14 }}>{summary}</span>
      </div>
      {loading && steps.length > 0 && (
        <ul style={styles.list}>
          {steps.map(s => (
            <li key={s.step} style={styles.item}>
              📊 获取 <strong>{s.symbol}</strong> <code style={styles.code}>{s.timeframe}</code> 数据并计算技术指标
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  wrap: {
    background: '#F9FAFB',
    border: '1px solid #E0E0E0',
    borderRadius: 4,
    padding: '12px 16px',
    marginBottom: 12,
  },
  header: { display: 'flex', alignItems: 'center', gap: 8 },
  spinner: {
    display: 'inline-block',
    width: 14, height: 14,
    border: '2px solid #E0E0E0',
    borderTopColor: '#0068FF',
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite',
  },
  list: { margin: '8px 0 0 0', padding: '0 0 0 20px', listStyle: 'none' },
  item: { fontSize: 13, color: '#555', padding: '3px 0' },
  code: { background: '#eee', padding: '1px 5px', borderRadius: 3, fontSize: 12 },
}
