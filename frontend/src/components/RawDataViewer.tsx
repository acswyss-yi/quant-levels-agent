interface Props {
  data: object
}

export default function RawDataViewer({ data }: Props) {
  return (
    <details style={styles.details}>
      <summary style={styles.summary}>🔬 查看原始 TA 数据</summary>
      <pre style={styles.pre}>{JSON.stringify(data, null, 2)}</pre>
    </details>
  )
}

const styles: Record<string, React.CSSProperties> = {
  details: { background: '#F9FAFB', border: '1px solid #E0E0E0', borderRadius: 4, marginTop: 12 },
  summary: { padding: '10px 14px', cursor: 'pointer', fontSize: 13, fontWeight: 600, color: '#161616' },
  pre:     { margin: 0, padding: '0 14px 14px', fontSize: 12, color: '#555', overflowX: 'auto', lineHeight: 1.5 },
}
