import VerdictBadge from './ui/VerdictBadge'
import ScoreBar from './ui/ScoreBar'
import { useLang } from '../lib/LanguageContext'
import { useTranslation } from '../lib/i18n'

function Section({ title, number, children }) {
  return (
    <div className="card fade-up" style={{ marginBottom:'1.2rem' }}>
      <div style={{ display:'flex', alignItems:'center', gap:'.8rem', marginBottom:'1rem', paddingBottom:'.7rem', borderBottom:'2px solid var(--ink)', flexWrap:'wrap' }}>
        <div style={{ fontFamily:'var(--font-display)', fontSize:'2rem', color:'var(--paper-dark)', lineHeight:1 }}>{number}</div>
        <h3 style={{ fontFamily:'var(--font-display)', letterSpacing:'.05em', fontSize:'clamp(1rem,2.5vw,1.5rem)' }}>{title}</h3>
      </div>
      {children}
    </div>
  )
}

// Fix broken/invalid links — only show real http URLs
function SafeLink({ url, title }) {
  const isValid = url && (url.startsWith('http://') || url.startsWith('https://')) && !url.includes('tavily.com/direct')
  if (!isValid) return <span style={{ color:'var(--grey)', fontSize:'.85rem' }}>{title}</span>
  return (
    <a href={url} target="_blank" rel="noopener noreferrer"
      style={{ color:'var(--blue)', fontWeight:500, fontSize:'.85rem', textDecoration:'none', wordBreak:'break-all' }}
      onMouseEnter={e=>e.target.style.textDecoration='underline'}
      onMouseLeave={e=>e.target.style.textDecoration='none'}
    >{title || url}</a>
  )
}

export default function ReportDashboard({ result }) {
  const { lang } = useLang()
  const t = useTranslation(lang)

  if (!result || result.status !== 'completed') return null
  const { claim_extraction:ce, author_verification:av, publisher_verification:pv,
          evidence_gathering:eg, claim_verifications:cvs, aggregated:agg } = result

  const verdictColor = {
    'True':'var(--green)','False':'var(--red)',
    'Partially True':'var(--amber)','Insufficient Evidence':'var(--grey)'
  }[agg?.final_verdict] || 'var(--grey)'

  return (
    <div>
      {/* ── HERO ── */}
      {agg && (
        <div className="card fade-up" style={{ background:'var(--ink)', color:'var(--paper)', marginBottom:'1.5rem', padding:'1.5rem', boxShadow:'var(--shadow-lg)' }}>
          <div style={{ fontFamily:'var(--font-mono)', fontSize:'.65rem', letterSpacing:'.15em', color:'#999', marginBottom:'.4rem' }}>{t.finalVerdict}</div>

          {/* Mobile-friendly verdict row */}
          <div style={{ display:'flex', alignItems:'center', gap:'1rem', flexWrap:'wrap', marginBottom:'1rem' }}>
            <h2 style={{ fontSize:'clamp(1.6rem,5vw,3rem)', color:verdictColor, lineHeight:1 }}>
              {agg.final_verdict.toUpperCase()}
            </h2>
            <div>
              <div style={{ fontFamily:'var(--font-mono)', fontSize:'.62rem', color:'#aaa', marginBottom:'.2rem' }}>{t.credibilityScore}</div>
              <div style={{ fontFamily:'var(--font-display)', fontSize:'clamp(1.8rem,4vw,2.8rem)', color:verdictColor, lineHeight:1 }}>
                {Math.round(agg.final_score)}<span style={{ fontSize:'.7em', color:'#aaa' }}>/100</span>
              </div>
            </div>
            <div>
              <div style={{ fontFamily:'var(--font-mono)', fontSize:'.62rem', color:'#aaa', marginBottom:'.2rem' }}>{t.confidence}</div>
              <div style={{ fontFamily:'var(--font-display)', fontSize:'clamp(1.4rem,3vw,2rem)', color:'#fff', lineHeight:1 }}>{Math.round(agg.confidence)}%</div>
            </div>
          </div>

          {/* Score breakdown — responsive grid */}
          <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(140px,1fr))', gap:'1rem', marginBottom:'1rem' }}>
            {[
              { label:t.author,     score:agg.score_breakdown?.author_score??0,    weight:'10%' },
              { label:t.publisher,  score:agg.score_breakdown?.publisher_score??0,  weight:'15%' },
              { label:'Claims',     score:agg.score_breakdown?.claims_score??0,     weight:'75%' },
            ].map(({label,score,weight}) => (
              <div key={label}>
                <div style={{ display:'flex', justifyContent:'space-between', marginBottom:'.3rem' }}>
                  <span style={{ fontFamily:'var(--font-mono)', fontSize:'.65rem', color:'#aaa' }}>{label} <span style={{ color:'#555' }}>({weight})</span></span>
                  <span style={{ fontFamily:'var(--font-display)', color:score>=60?'#4ade80':score>=40?'#fbbf24':'#f87171' }}>{Math.round(score)}</span>
                </div>
                <div style={{ height:7, background:'#333', border:'1px solid #555' }}>
                  <div style={{ height:'100%', width:`${score}%`, background:score>=60?'#4ade80':score>=40?'#fbbf24':'#f87171', transition:'width 1s ease' }} />
                </div>
              </div>
            ))}
          </div>

          <p style={{ fontSize:'.85rem', color:'#ccc', lineHeight:1.6, borderTop:'1px solid #333', paddingTop:'.9rem' }}>{agg.explanation}</p>
        </div>
      )}

      {/* ── Claims ── */}
      {ce && (
        <Section title={t.extractedClaims} number="01">
          <div style={{ display:'flex', gap:'1.2rem', flexWrap:'wrap', marginBottom:'.8rem' }}>
            {ce.author_name && <div><span style={{ fontFamily:'var(--font-mono)', fontSize:'.65rem', color:'var(--grey)', textTransform:'uppercase' }}>{t.author}</span><br /><strong style={{ fontSize:'.9rem' }}>{ce.author_name}</strong></div>}
            {ce.publisher_name && <div><span style={{ fontFamily:'var(--font-mono)', fontSize:'.65rem', color:'var(--grey)', textTransform:'uppercase' }}>{t.publisher}</span><br /><strong style={{ fontSize:'.9rem' }}>{ce.publisher_name}</strong></div>}
            {ce.language && <div><span style={{ fontFamily:'var(--font-mono)', fontSize:'.65rem', color:'var(--grey)', textTransform:'uppercase' }}>{t.language}</span><br /><strong style={{ fontSize:'.9rem' }}>{ce.language.toUpperCase()}</strong></div>}
          </div>
          <div className="rule-thin" />
          <p style={{ fontSize:'.88rem', color:'var(--grey)', marginBottom:'.9rem', fontStyle:'italic' }}>{ce.summary}</p>

          {ce.claims.map((claim) => {
            const cv = cvs?.find(c => c.claim_id === claim.id)
            const borderColor = cv ? {
              'True':'var(--green)','False':'var(--red)',
              'Partially True':'var(--amber)','Insufficient Evidence':'var(--grey)'
            }[cv.verdict] : 'var(--border-light)'
            return (
              <div key={claim.id} style={{ padding:'.9rem', borderLeft:`4px solid ${borderColor}`, background:'#fafaf8', marginBottom:'.7rem' }}>
                <div style={{ display:'flex', gap:'.5rem', alignItems:'flex-start', justifyContent:'space-between', flexWrap:'wrap', marginBottom:'.4rem' }}>
                  <div style={{ flex:1, minWidth:0 }}>
                    <div style={{ display:'flex', gap:'.4rem', marginBottom:'.3rem', flexWrap:'wrap' }}>
                      <span className="tag">{claim.claim_type}</span>
                      <span style={{ fontFamily:'var(--font-mono)', fontSize:'.65rem', color:'var(--grey)' }}>{Math.round(claim.confidence*100)}%</span>
                    </div>
                    <p style={{ fontWeight:500, marginBottom:'.3rem', fontSize:'.9rem', lineHeight:1.5, wordBreak:'break-word' }}>{claim.claim_text}</p>
                    <p style={{ fontFamily:'var(--font-mono)', fontSize:'.7rem', color:'var(--grey)', wordBreak:'break-word' }}>
                      <strong>{claim.subject}</strong> → {claim.predicate} → <strong>{claim.object}</strong>
                    </p>
                  </div>
                  {cv && <div style={{ flexShrink:0 }}><VerdictBadge verdict={cv.verdict} size="sm" /></div>}
                </div>
                {cv && <p style={{ fontSize:'.82rem', color:'var(--grey)', marginTop:'.4rem', paddingTop:'.4rem', borderTop:'1px solid var(--border-light)' }}>{cv.reasoning}</p>}
                {/* Key evidence links — only valid URLs */}
                {cv?.key_evidence?.filter(u => u && u.startsWith('http') && !u.includes('tavily.com/direct')).length > 0 && (
                  <div style={{ marginTop:'.4rem', display:'flex', flexWrap:'wrap', gap:'.3rem' }}>
                    {cv.key_evidence.filter(u => u && u.startsWith('http') && !u.includes('tavily.com/direct')).slice(0,3).map((url,i) => (
                      <a key={i} href={url} target="_blank" rel="noopener noreferrer"
                        style={{ fontFamily:'var(--font-mono)', fontSize:'.65rem', color:'var(--blue)', borderBottom:'1px solid var(--blue)', textDecoration:'none', wordBreak:'break-all' }}>
                        [{i+1}] Source ↗
                      </a>
                    ))}
                  </div>
                )}
              </div>
            )
          })}

          {ce.named_entities?.length > 0 && (
            <div style={{ marginTop:'.8rem' }}>
              <div style={{ fontFamily:'var(--font-mono)', fontSize:'.65rem', color:'var(--grey)', marginBottom:'.4rem', textTransform:'uppercase' }}>{t.namedEntities}</div>
              <div style={{ display:'flex', flexWrap:'wrap', gap:'.3rem' }}>
                {ce.named_entities.map((e,i) => (
                  <span key={i} className="tag" title={`${e.label} — ${Math.round(e.confidence*100)}%`}>{e.text} <span style={{ color:'var(--grey)' }}>({e.label})</span></span>
                ))}
              </div>
            </div>
          )}
        </Section>
      )}

      {/* ── Author + Publisher (responsive) ── */}
      <div className="grid-2" style={{ marginBottom:'1.2rem' }}>
        {av && (
          <div className="card fade-up-1">
            <div style={{ fontFamily:'var(--font-mono)', fontSize:'.65rem', color:'var(--grey)', marginBottom:'.4rem', textTransform:'uppercase', letterSpacing:'.08em' }}>02 — {t.authorCredibility}</div>
            <h3 style={{ marginBottom:'.8rem', fontSize:'clamp(.95rem,2.5vw,1.3rem)', wordBreak:'break-word' }}>{av.author_name}</h3>
            <ScoreBar score={av.credibility_score} label={t.credibilityScore} />
            <div className="rule-thin" />
            <div style={{ display:'flex', gap:'.3rem', flexWrap:'wrap', marginBottom:'.6rem' }}>
              {av.found_in_journalist_db && <span className="tag tag-green">{t.inJournalistDB}</span>}
              {av.public_profile_found && <span className="tag tag-green">{t.publicProfile}</span>}
              {av.flags?.map(f => <span key={f} className="tag tag-red">{f}</span>)}
            </div>
            {av.known_outlets?.length > 0 && <div style={{ fontFamily:'var(--font-mono)', fontSize:'.72rem', color:'var(--grey)', marginBottom:'.4rem' }}>{t.knownOutlets}: {av.known_outlets.join(', ')}</div>}
            <p style={{ fontSize:'.82rem', color:'var(--grey)' }}>{av.reasoning}</p>
          </div>
        )}
        {pv && (
          <div className="card fade-up-2">
            <div style={{ fontFamily:'var(--font-mono)', fontSize:'.65rem', color:'var(--grey)', marginBottom:'.4rem', textTransform:'uppercase', letterSpacing:'.08em' }}>03 — {t.publisherCredibility}</div>
            <h3 style={{ marginBottom:'.8rem', fontSize:'clamp(.95rem,2.5vw,1.3rem)', wordBreak:'break-word' }}>{pv.publisher_name}</h3>
            <ScoreBar score={pv.credibility_score} label={t.credibilityScore} />
            <div className="rule-thin" />
            <div style={{ display:'flex', gap:'.3rem', flexWrap:'wrap', marginBottom:'.6rem' }}>
              {pv.domain && <span className="tag">{pv.domain}</span>}
              {pv.domain_age_years && <span className="tag">{pv.domain_age_years}y</span>}
              {pv.country && <span className="tag">{pv.country}</span>}
              {pv.in_fake_news_db && <span className="tag tag-red">⚠ Fake News DB</span>}
              {pv.flags?.map(f => <span key={f} className="tag tag-red">{f}</span>)}
            </div>
            <p style={{ fontSize:'.82rem', color:'var(--grey)' }}>{pv.reasoning}</p>
          </div>
        )}
      </div>

      {/* ── Evidence ── */}
      {eg?.length > 0 && (
        <Section title={t.evidenceAnalysis} number="04">
          {eg.map((ev) => (
            <div key={ev.claim_id} style={{ marginBottom:'1.3rem' }}>
              <div style={{ padding:'.55rem .9rem', background:'var(--paper-dark)', border:'1px solid var(--border-light)', marginBottom:'.6rem', fontFamily:'var(--font-mono)', fontSize:'.78rem', wordBreak:'break-word' }}>
                <strong>{t.claim}:</strong> {ev.claim_text}
              </div>
              <div style={{ display:'flex', gap:'.8rem', marginBottom:'.6rem', flexWrap:'wrap' }}>
                <span className="tag tag-green">✅ {ev.supporting_count} {t.supporting}</span>
                <span className="tag tag-red">❌ {ev.contradicting_count} {t.contradicting}</span>
                <span className="tag">⬜ {ev.neutral_count} {t.neutral}</span>
              </div>
              <p style={{ fontSize:'.83rem', color:'var(--grey)', marginBottom:'.7rem', fontStyle:'italic' }}>{ev.evidence_summary}</p>

              <div style={{ border:'1px solid var(--border-light)' }}>
                {ev.articles
                  ?.filter(a => a.relevance_score > 0.05) // hide irrelevant
                  .sort((a,b) => b.relevance_score - a.relevance_score)
                  .slice(0,6)
                  .map((a,j) => (
                    <div key={j} className="evidence-item" style={{ flexWrap:'nowrap' }}>
                      <span style={{ fontSize:'1rem', minWidth:22, color: a.stance==='supporting'?'var(--green)':a.stance==='contradicting'?'var(--red)':'var(--grey)' }}>
                        {a.stance==='supporting'?'✅':a.stance==='contradicting'?'❌':'⬜'}
                      </span>
                      <div style={{ flex:1, minWidth:0 }}>
                        <SafeLink url={a.url} title={a.title} />
                        <div style={{ fontFamily:'var(--font-mono)', fontSize:'.65rem', color:'var(--grey)', marginTop:'.15rem' }}>
                          {a.publisher}{a.published_date?` · ${a.published_date}`:''} · {t.relevance}: {Math.round(a.relevance_score*100)}%
                        </div>
                        <p style={{ fontSize:'.8rem', color:'var(--grey)', marginTop:'.25rem', lineHeight:1.5 }}>{a.summary}</p>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </Section>
      )}
    </div>
  )
}
