import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getReport } from '../lib/api'
import ReportDashboard from '../components/ReportDashboard'
import VerdictBadge from '../components/ui/VerdictBadge'

export default function ReportPage() {
  const { id } = useParams()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    const poll = async () => {
      try {
        const r = await getReport(id)
        if (!cancelled) {
          setResult(r)
          if (r.status === 'processing') {
            setTimeout(poll, 2500)
          } else {
            setLoading(false)
          }
        }
      } catch (e) {
        if (!cancelled) {
          setError('Report not found.')
          setLoading(false)
        }
      }
    }
    poll()
    return () => { cancelled = true }
  }, [id])

  return (
    <div className="container" style={{ padding: '2rem 1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
        <Link to="/" className="btn btn-ghost" style={{ fontSize: '0.85rem', padding: '0.3rem 0.8rem' }}>← Back</Link>
        <div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--grey)', letterSpacing: '0.1em' }}>REPORT ID</div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{id}</div>
        </div>
        {result?.aggregated && <VerdictBadge verdict={result.aggregated.final_verdict} />}
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '4rem' }}>
          <span className="spinner" style={{ width: 40, height: 40, borderWidth: 4 }} />
          <p style={{ marginTop: '1rem', fontFamily: 'var(--font-mono)', color: 'var(--grey)' }}>
            {result?.status === 'processing' ? 'Analysis in progress…' : 'Loading report…'}
          </p>
        </div>
      )}

      {error && (
        <div className="card" style={{ border: '2px solid var(--red)', background: 'var(--red-light)' }}>
          <strong style={{ color: 'var(--red)' }}>❌ {error}</strong>
        </div>
      )}

      {result && !loading && <ReportDashboard result={result} />}
    </div>
  )
}
