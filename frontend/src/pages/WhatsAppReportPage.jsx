import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getReport } from '../lib/api'
import VerdictBadge from '../components/ui/VerdictBadge'
import ScoreBar from '../components/ui/ScoreBar'

// Full detailed WhatsApp report page
export default function WhatsAppReportPage() {
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

  if (loading) return (
    <div style={{ textAlign:'center', padding:'4rem 1rem' }}>
      <span className="spinner" style={{ width:36,height:36,borderWidth:3 }} />
      <p style={{ marginTop:'1rem', fontFamily:'var(--font-mono)', color:'var(--grey)', fontSize:'.85rem' }}>
        {result?.status === 'processing' ? '🔄 Analysis in progress… please wait.' : 'Loading report…'}
      </p>
    </div>
  )

  if (error) return (
    <div className="container" style={{ padding:'2rem 1rem' }}>
      <div className="card" style={{ border:'2px solid var(--red)', background:'var(--red-light)' }}>
        <strong style={{ color:'var(--red)' }}>❌ {error}</strong>
      </div>
    </div>
  )

  if (!result) return null

  const { aggregated:agg, claim_extraction:ce, claim_verifications:cvs,
          author_verification:av, publisher_verification:pv, evidence_gathering:eg } = result

  const verdictColor = {
    'True':'var(--green)','False':'var(--red)',
    'Partially True':'var(--amber)','Insufficient Evidence':'var(--grey)'
  }[agg?.final_verdict] || 'var(--grey)'

  const verdictEmoji = { 'True':'✅','False':'❌','Partially True':'⚠️','Insufficient Evidence':'❓' }[agg?.final_verdict] || '❓'

  return (
    <div className="container" style={{ padding:'1.2rem 1rem', maxWidth:720 }}>
      {/* WhatsApp style header */}
      <div style={{ background:'#075e54', color:'white', padding:'1rem 1.2rem', marginBottom:'1.2rem', borderRadius:0, display:'flex', alignItems:'center', gap:'1rem' }}>
        <span style={{ fontSize:'1.8rem' }}>🔍</span>
        <div>
          <div style={{ fontFamily:'var(--font-display)', fontSize:'1.4rem', letterSpacing:'.05em' }}>EverAI</div>
          <div style={{ fontSize:'.75rem', opacity:.8 }}>WhatsApp Fact Check Report</div>
        </div>
        <Link to="/" style={{ marginLeft:'auto', color:'white', fontSize:'.75rem', fontFamily:'var(--font-mono)', textDecoration:'none', border:'1px solid rgba(255,255,255,.4)', padding:'.25rem .6rem' }}>
          Full Site →
        </Link>
      </div>

      {/* Original text */}
      <div style={{ background:'#dcf8c6', border:'1px solid #b2dfdb', padding:'.9rem 1rem', marginBottom:'1rem', fontSize:'.88rem', borderRadius:0 }}>
        <div style={{ fontFamily:'var(--font-mono)', fontSize:'.62rem', color:'#555', marginBottom:'.3rem', textTransform:'uppercase' }}>Message Analyzed</div>
        <p style={{ lineHeight:1.6, wordBreak:'break-word' }}>{result.input_text}</p>
      </div>

      {/* VERDICT CARD — big and clear */}
      {agg && (
        <div style={{ background:'var(--ink)', color:'var(--paper)', padding:'1.3rem', marginBottom:'1rem' }}>
          <div style={{ fontFamily:'var(--font-mono)', fontSize:'.62rem', color:'#999', marginBottom:'.4rem', letterSpacing:'.12em' }}>FINAL VERDICT</div>
          <div style={{ display:'flex', alignItems:'center', gap:'.8rem', flexWrap:'wrap', marginBottom:'.8rem' }}>
            <span style={{ fontSize:'2rem' }}>{verdictEmoji}</span>
            <div>
              <div style={{ fontFamily:'var(--font-display)', fontSize:'clamp(1.6rem,5vw,2.5rem)', color:verdictColor, lineHeight:1 }}>{agg.final_verdict.toUpperCase()}</div>
              <div style={{ fontFamily:'var(--font-mono)', fontSize:'.7rem', color:'#aaa', marginTop:'.2rem' }}>
                Score: {Math.round(agg.final_score)}/100 &nbsp;·&nbsp; Confidence: {Math.round(agg.confidence)}%
              </div>
            </div>
          </div>
          <p style={{ fontSize:'.85rem', color:'#ccc', lineHeight:1.6 }}>{agg.explanation}</p>
        </div>
      )}

      {/* Claims with verdicts */}
      {cvs?.length > 0 && (
        <div className="card" style={{ marginBottom:'1rem' }}>
          <div style={{ fontFamily:'var(--font-display)', fontSize:'1.2rem', marginBottom:'.8rem', borderBottom:'2px solid var(--ink)', paddingBottom:'.5rem' }}>
            CLAIM ANALYSIS
          </div>
          {cvs.map((cv, i) => (
            <div key={cv.claim_id} style={{
              padding:'.8rem', marginBottom:'.6rem',
              borderLeft:`4px solid ${{'True':'var(--green)','False':'var(--red)','Partially True':'var(--amber)'}[cv.verdict]||'var(--grey)'}`,
              background:'#fafaf8'
            }}>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap:'.5rem', flexWrap:'wrap', marginBottom:'.4rem' }}>
                <p style={{ fontWeight:500, fontSize:'.88rem', flex:1, wordBreak:'break-word' }}>{cv.claim_text}</p>
                <VerdictBadge verdict={cv.verdict} size="sm" />
              </div>
              <p style={{ fontSize:'.82rem', color:'var(--grey)', lineHeight:1.5 }}>{cv.reasoning}</p>
              <div style={{ fontFamily:'var(--font-mono)', fontSize:'.68rem', color:'#888', marginTop:'.3rem' }}>
                Confidence: {Math.round(cv.confidence)}%
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Evidence summary */}
      {eg?.length > 0 && (
        <div className="card" style={{ marginBottom:'1rem' }}>
          <div style={{ fontFamily:'var(--font-display)', fontSize:'1.2rem', marginBottom:'.8rem', borderBottom:'2px solid var(--ink)', paddingBottom:'.5rem' }}>
            EVIDENCE FOUND
          </div>
          {eg.map((ev, i) => (
            <div key={ev.claim_id} style={{ marginBottom:'1rem' }}>
              <div style={{ display:'flex', gap:'.6rem', marginBottom:'.4rem', flexWrap:'wrap' }}>
                <span className="tag tag-green">✅ {ev.supporting_count} Supporting</span>
                <span className="tag tag-red">❌ {ev.contradicting_count} Contradicting</span>
                <span className="tag">⬜ {ev.neutral_count} Neutral</span>
              </div>
              <p style={{ fontSize:'.85rem', color:'var(--grey)', fontStyle:'italic', marginBottom:'.6rem' }}>{ev.evidence_summary}</p>
              {/* Top 3 relevant articles only */}
              {ev.articles
                ?.filter(a => a.relevance_score > 0.3 && a.url?.startsWith('http') && !a.url.includes('tavily.com/direct'))
                .sort((a,b) => b.relevance_score - a.relevance_score)
                .slice(0,3)
                .map((a,j) => (
                  <div key={j} style={{ padding:'.55rem .8rem', borderBottom:'1px solid var(--border-light)', display:'flex', gap:'.7rem' }}>
                    <span style={{ color:a.stance==='supporting'?'var(--green)':a.stance==='contradicting'?'var(--red)':'var(--grey)', fontSize:'.9rem', minWidth:20 }}>
                      {a.stance==='supporting'?'✅':a.stance==='contradicting'?'❌':'⬜'}
                    </span>
                    <div>
                      <a href={a.url} target="_blank" rel="noopener noreferrer" style={{ fontSize:'.83rem', color:'var(--blue)', textDecoration:'none', display:'block', marginBottom:'.15rem' }}>{a.title}</a>
                      <span style={{ fontFamily:'var(--font-mono)', fontSize:'.65rem', color:'var(--grey)' }}>{a.publisher}</span>
                    </div>
                  </div>
                ))}
            </div>
          ))}
        </div>
      )}

      {/* Author + Publisher */}
      <div className="grid-2" style={{ marginBottom:'1rem' }}>
        {av && (
          <div className="card">
            <div style={{ fontFamily:'var(--font-mono)', fontSize:'.62rem', color:'var(--grey)', marginBottom:'.4rem', textTransform:'uppercase' }}>Author</div>
            <div style={{ fontWeight:600, fontSize:'.9rem', marginBottom:'.5rem', wordBreak:'break-word' }}>{av.author_name}</div>
            <ScoreBar score={av.credibility_score} />
          </div>
        )}
        {pv && (
          <div className="card">
            <div style={{ fontFamily:'var(--font-mono)', fontSize:'.62rem', color:'var(--grey)', marginBottom:'.4rem', textTransform:'uppercase' }}>Publisher</div>
            <div style={{ fontWeight:600, fontSize:'.9rem', marginBottom:'.5rem', wordBreak:'break-word' }}>{pv.publisher_name}</div>
            <ScoreBar score={pv.credibility_score} />
            {pv.in_fake_news_db && <div className="tag tag-red" style={{ marginTop:'.4rem' }}>⚠ Known Fake News Source</div>}
          </div>
        )}
      </div>

      {/* Footer */}
      <div style={{ textAlign:'center', padding:'1rem', borderTop:'2px solid var(--ink)', fontFamily:'var(--font-mono)', fontSize:'.68rem', color:'var(--grey)' }}>
        Analyzed by EverAI · Report ID: {id?.slice(0,8)}…
        <br />
        <Link to="/" style={{ color:'var(--blue)' }}>Try EverAI yourself →</Link>
      </div>
    </div>
  )
}
