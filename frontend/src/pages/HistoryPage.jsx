import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getHistory } from '../lib/api'
import VerdictBadge from '../components/ui/VerdictBadge'

export default function HistoryPage() {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getHistory().then(h => { setHistory(h); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  return (
    <div className="container" style={{ padding: '2rem 1.5rem' }}>
      <div className="fade-up" style={{ marginBottom: '2rem' }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', letterSpacing: '0.15em', color: 'var(--grey)', marginBottom: '0.5rem' }}>ANALYSIS LOG</div>
        <h2>RECENT ANALYSES</h2>
      </div>
      <hr className="rule" />

      {loading && (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <span className="spinner" style={{ width: 32, height: 32 }} />
        </div>
      )}

      {!loading && history.length === 0 && (
        <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--grey)' }}>
          <p style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', marginBottom: '0.5rem' }}>NO ANALYSES YET</p>
          <Link to="/" className="btn" style={{ marginTop: '1rem', display: 'inline-flex' }}>Start Analyzing →</Link>
        </div>
      )}

      {history.map((item, i) => (
        <Link
          key={item.query_id}
          to={`/report/${item.query_id}`}
          className={`fade-up`}
          style={{
            display: 'block',
            textDecoration: 'none',
            color: 'inherit',
            border: '2px solid var(--border-light)',
            borderLeft: '4px solid var(--ink)',
            padding: '1rem 1.2rem',
            marginBottom: '0.8rem',
            background: 'white',
            transition: 'box-shadow 0.15s, transform 0.15s',
          }}
          onMouseEnter={e => { e.currentTarget.style.boxShadow = 'var(--shadow)'; e.currentTarget.style.transform = 'translate(-2px,-2px)' }}
          onMouseLeave={e => { e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'none' }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ flex: 1 }}>
              <p style={{ fontSize: '0.9rem', marginBottom: '0.4rem', lineHeight: 1.5 }}>{item.preview}</p>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--grey)' }}>
                {new Date(item.created_at).toLocaleString()} · ID: {item.query_id.slice(0, 8)}…
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.4rem' }}>
              {item.final_verdict ? (
                <>
                  <VerdictBadge verdict={item.final_verdict} size="sm" />
                  <span style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem' }}>
                    {Math.round(item.final_score)}<span style={{ fontSize: '0.7rem', color: 'var(--grey)' }}>/100</span>
                  </span>
                </>
              ) : (
                <span className="tag">{item.status}</span>
              )}
            </div>
          </div>
        </Link>
      ))}
    </div>
  )
}
