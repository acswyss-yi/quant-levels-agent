import { useState } from 'react'
import { pushDingTalk } from '../api/client'

interface Props {
  report: string
  symbol: string
  timeframe: string
}

export default function DingTalkPush({ report, symbol, timeframe }: Props) {
  const [open,    setOpen]    = useState(false)
  const [token,   setToken]   = useState('')
  const [loading, setLoading] = useState(false)
  const [status,  setStatus]  = useState<'idle' | 'ok' | 'err'>('idle')
  const [errMsg,  setErrMsg]  = useState('')

  async function handleSend() {
    if (!token.trim()) return
    setLoading(true)
    setStatus('idle')
    const res = await pushDingTalk({ webhook_token: token.trim(), report, symbol, timeframe })
    setLoading(false)
    if (res.success) {
      setStatus('ok')
    } else {
      setStatus('err')
      setErrMsg(res.error ?? '未知错误')
    }
  }

  return (
    <div style={styles.wrap}>
      <button onClick={() => setOpen(v => !v)} style={styles.toggle}>
        📨 推送到钉钉 {open ? '▲' : '▼'}
      </button>
      {open && (
        <div style={styles.body}>
          <input
            type="password"
            placeholder="粘贴 access_token"
            value={token}
            onChange={e => setToken(e.target.value)}
            style={styles.input}
          />
          <button
            onClick={handleSend}
            disabled={loading || !report || !token.trim()}
            style={{ ...styles.btn, opacity: (loading || !report || !token.trim()) ? 0.6 : 1 }}
          >
            {loading ? '推送中...' : '发送'}
          </button>
          {status === 'ok'  && <div style={{ color: '#24A148', fontSize: 13 }}>推送成功！</div>}
          {status === 'err' && <div style={{ color: '#DA1E28', fontSize: 13 }}>推送失败：{errMsg}</div>}
        </div>
      )}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  wrap:   { border: '1px solid #E0E0E0', borderRadius: 4, overflow: 'hidden', marginTop: 12 },
  toggle: { width: '100%', padding: '10px 14px', background: '#F9FAFB', border: 'none', textAlign: 'left', cursor: 'pointer', fontSize: 13, fontWeight: 600 },
  body:   { padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 8 },
  input:  { padding: '8px 10px', border: '1px solid #E0E0E0', borderRadius: 4, fontSize: 13 },
  btn:    { padding: '8px 0', background: '#0068FF', color: '#fff', border: 'none', borderRadius: 4, fontSize: 13, fontWeight: 600, cursor: 'pointer' },
}
