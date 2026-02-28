import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getHistory } from '../lib/api'
import VerdictBadge from '../components/ui/VerdictBadge'
import { useLang } from '../lib/LanguageContext'
import { useTranslation } from '../lib/i18n'

export default function HistoryPage() {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const { lang } = useLang()
  const t = useTranslation(lang)

  useEffect(() => {
    getHistory().then(h => { setHistory(h); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  return (
    <div className="container" style={{ padding:'1.5rem 1rem' }}>
      <div className="fade-up" style={{ marginBottom:'1.5rem' }}>
        <div style={{ fontFamily:'var(--font-mono)', fontSize:'.68rem', letterSpacing:'.12em', color:'var(--grey)', marginBottom:'.4rem' }}>{t.analysisLog}</div>
        <h2>{t.recentAnalyses}</h2>
      </div>
      <hr className="rule" />

      {loading && <div style={{ textAlign:'center', padding:'3rem' }}><span className="spinner" style={{ width:32,height:32 }} /></div>}

      {!loading && history.length === 0 && (
        <div style={{ textAlign:'center', padding:'4rem 1rem', color:'var(--grey)' }}>
          <p style={{ fontFamily:'var(--font-display)', fontSize:'clamp(1.2rem,4vw,2rem)', marginBottom:'.5rem' }}>{t.noAnalysesYet}</p>
          <Link to="/" className="btn" style={{ marginTop:'1rem', display:'inline-flex' }}>{t.startAnalyzing}</Link>
        </div>
      )}

      {history.map((item) => (
        <Link key={item.query_id} to={`/report/${item.query_id}`} className="fade-up"
          style={{ display:'block', textDecoration:'none', color:'inherit', border:'2px solid var(--border-light)', borderLeft:'4px solid var(--ink)', padding:'.9rem 1rem', marginBottom:'.7rem', background:'white', transition:'box-shadow .15s,transform .15s' }}
          onMouseEnter={e=>{e.currentTarget.style.boxShadow='var(--shadow)';e.currentTarget.style.transform='translate(-2px,-2px)'}}
          onMouseLeave={e=>{e.currentTarget.style.boxShadow='none';e.currentTarget.style.transform='none'}}
        >
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap:'.8rem', flexWrap:'wrap' }}>
            <div style={{ flex:1, minWidth:0 }}>
              <p style={{ fontSize:'.88rem', marginBottom:'.35rem', lineHeight:1.5, wordBreak:'break-word' }}>{item.preview}</p>
              <div style={{ fontFamily:'var(--font-mono)', fontSize:'.68rem', color:'var(--grey)' }}>
                {new Date(item.created_at).toLocaleString()} · {item.query_id.slice(0,8)}…
              </div>
            </div>
            <div style={{ display:'flex', flexDirection:'column', alignItems:'flex-end', gap:'.3rem', flexShrink:0 }}>
              {item.final_verdict
                ? <><VerdictBadge verdict={item.final_verdict} size="sm" /><span style={{ fontFamily:'var(--font-display)', fontSize:'1.1rem' }}>{Math.round(item.final_score)}<span style={{ fontSize:'.65rem', color:'var(--grey)' }}>/100</span></span></>
                : <span className="tag">{item.status}</span>}
            </div>
          </div>
        </Link>
      ))}
    </div>
  )
}
