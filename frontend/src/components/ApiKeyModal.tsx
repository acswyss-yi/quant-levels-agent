import { useState } from 'react'

interface Props {
  onConfirm: (key: string) => void
}

export default function ApiKeyModal({ onConfirm }: Props) {
  const [value, setValue] = useState('')
  const [error, setError] = useState('')

  function handleSubmit() {
    const clean = value.trim()
    if (!clean) {
      setError('API Key 不能为空')
      return
    }
    localStorage.setItem('qwen_api_key', clean)
    onConfirm(clean)
  }

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        <div style={styles.title}>Quant Levels Agent</div>
        <p style={styles.desc}>请输入<strong>阿里云百炼 API Key</strong> 以继续使用。</p>
        <input
          type="password"
          placeholder="sk-xxxxxxxxxxxx"
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSubmit()}
          style={styles.input}
          autoFocus
        />
        {error && <div style={styles.error}>{error}</div>}
        <button onClick={handleSubmit} style={styles.btn}>确认</button>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed', inset: 0,
    background: 'rgba(0,0,0,0.45)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    zIndex: 1000,
  },
  modal: {
    background: '#fff',
    borderRadius: 6,
    padding: '32px 28px',
    width: 380,
    boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
    display: 'flex', flexDirection: 'column', gap: 12,
  },
  title: { fontSize: 18, fontWeight: 700, color: '#161616' },
  desc:  { fontSize: 14, color: '#555', margin: 0 },
  input: {
    padding: '10px 12px',
    border: '1px solid #E0E0E0',
    borderRadius: 4,
    fontSize: 14,
    outline: 'none',
    width: '100%',
    boxSizing: 'border-box',
  },
  error: { color: '#DA1E28', fontSize: 13 },
  btn: {
    padding: '10px 0',
    background: '#0068FF',
    color: '#fff',
    border: 'none',
    borderRadius: 4,
    fontSize: 15,
    fontWeight: 600,
    cursor: 'pointer',
  },
}
