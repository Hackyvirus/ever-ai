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
          if (r.status === 'processing') setTimeout(poll, 2500)
          else setLoading(false)
        }
      } catch(e) { if(!cancelled){ setError('Report not found.'); setLoading(false) } }
    }
    poll()
    return () => { cancelled = true }
  }, [id])

  return (
    <div className="container" style={{ padding:'1.5rem 1rem' }}>
      <div style={{ display:'flex', alignItems:'center', gap:'.8rem', marginBottom:'1.2rem', flexWrap:'wrap' }}>
        <Link to="/" className="btn btn-ghost btn-sm">← Back</Link>
        <div>
          <div style={{ fontFamily:'var(--font-mono)', fontSize:'.65rem', color:'var(--grey)', letterSpacing:'.08em' }}>REPORT ID</div>
          <div style={{ fontFamily:'var(--font-mono)', fontSize:'.78rem', wordBreak:'break-all' }}>{id}</div>
        </div>
        {result?.aggregated && <VerdictBadge verdict={result.aggregated.final_verdict} />}
      </div>

      {loading && (
        <div style={{ textAlign:'center', padding:'3rem' }}>
          <span className="spinner" style={{ width:36,height:36,borderWidth:3 }} />
          <p style={{ marginTop:'.8rem', fontFamily:'var(--font-mono)', color:'var(--grey)', fontSize:'.85rem' }}>
            {result?.status==='processing' ? 'Analysis in progress…' : 'Loading report…'}
          </p>
        </div>
      )}
      {error && <div className="card" style={{ border:'2px solid var(--red)', background:'var(--red-light)' }}><strong style={{ color:'var(--red)' }}>❌ {error}</strong></div>}
      {result && !loading && <ReportDashboard result={result} />}
    </div>
  )
}
