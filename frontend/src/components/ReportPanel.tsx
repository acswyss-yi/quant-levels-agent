import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Props {
  report: string
}

export default function ReportPanel({ report }: Props) {
  if (!report) return null

  return (
    <div style={styles.wrap}>
      <div style={styles.heading}>🤖 千问分析报告</div>
      <div style={styles.content}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{report}</ReactMarkdown>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  wrap:    { marginTop: 16 },
  heading: { fontSize: 16, fontWeight: 700, color: '#161616', marginBottom: 8 },
  content: { fontSize: 14, lineHeight: 1.7, color: '#161616' },
}
