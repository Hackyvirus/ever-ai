import VerdictBadge from './ui/VerdictBadge'
import ScoreBar from './ui/ScoreBar'

function Flag({ text, color = 'red' }) {
  return <span className={`tag tag-${color}`}>{text}</span>
}

function Section({ title, number, children }) {
  return (
    <div className="card fade-up" style={{ marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem', paddingBottom: '0.8rem', borderBottom: '2px solid var(--ink)' }}>
        <div style={{
          fontFamily: 'var(--font-display)',
          fontSize: '2.5rem',
          color: 'var(--paper-dark)',
          lineHeight: 1,
          userSelect: 'none',
        }}>{number}</div>
        <h3 style={{ fontFamily: 'var(--font-display)', letterSpacing: '0.05em' }}>{title}</h3>
      </div>
      {children}
    </div>
  )
}

export default function ReportDashboard({ result }) {
  if (!result || result.status !== 'completed') return null

  const { claim_extraction: ce, author_verification: av, publisher_verification: pv,
          evidence_gathering: eg, claim_verifications: cvs, aggregated: agg } = result

  const verdictColor = {
    'True': 'var(--green)', 'False': 'var(--red)',
    'Partially True': 'var(--amber)', 'Insufficient Evidence': 'var(--grey)'
  }[agg?.final_verdict] || 'var(--grey)'

  return (
    <div>
      {/* ── HERO: Final Verdict ── */}
      {agg && (
        <div className="card fade-up" style={{
          background: 'var(--ink)',
          color: 'var(--paper)',
          marginBottom: '2rem',
          padding: '2rem',
          boxShadow: 'var(--shadow-lg)',
        }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', letterSpacing: '0.15em', color: '#999', marginBottom: '0.5rem' }}>FINAL VERDICT</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '1.2rem' }}>
            <h2 style={{ fontSize: 'clamp(2rem, 5vw, 3.5rem)', color: verdictColor, lineHeight: 1 }}>{agg.final_verdict.toUpperCase()}</h2>
            <div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: '#aaa', marginBottom: '0.3rem' }}>CREDIBILITY SCORE</div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: '3rem', color: verdictColor, lineHeight: 1 }}>
                {Math.round(agg.final_score)}<span style={{ fontSize: '1.2rem', color: '#aaa' }}>/100</span>
              </div>
            </div>
            <div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: '#aaa', marginBottom: '0.3rem' }}>CONFIDENCE</div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', color: '#fff', lineHeight: 1 }}>{Math.round(agg.confidence)}%</div>
            </div>
          </div>

          {/* Score breakdown bars */}
          <div className="grid-3" style={{ gap: '1.5rem', marginBottom: '1.2rem' }}>
            {[
              { label: 'Author', score: agg.score_breakdown?.author_score ?? 0, weight: '15%' },
              { label: 'Publisher', score: agg.score_breakdown?.publisher_score ?? 0, weight: '25%' },
              { label: 'Claims', score: agg.score_breakdown?.claims_score ?? 0, weight: '60%' },
            ].map(({ label, score, weight }) => (
              <div key={label}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: '#aaa', letterSpacing: '0.1em' }}>{label.toUpperCase()} <span style={{ color: '#666' }}>({weight})</span></span>
                  <span style={{ fontFamily: 'var(--font-display)', color: score >= 60 ? '#4ade80' : score >= 40 ? '#fbbf24' : '#f87171' }}>{Math.round(score)}</span>
                </div>
                <div style={{ height: 8, background: '#333', border: '1px solid #555' }}>
                  <div style={{ height: '100%', width: `${score}%`, background: score >= 60 ? '#4ade80' : score >= 40 ? '#fbbf24' : '#f87171', transition: 'width 1s ease' }} />
                </div>
              </div>
            ))}
          </div>

          <p style={{ fontSize: '0.9rem', color: '#ccc', lineHeight: 1.6, borderTop: '1px solid #333', paddingTop: '1rem' }}>{agg.explanation}</p>
        </div>
      )}

      {/* ── Claims ── */}
      {ce && (
        <Section title="EXTRACTED CLAIMS" number="01">
          <div style={{ marginBottom: '1rem', display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
            {ce.author_name && <div><span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--grey)', textTransform: 'uppercase' }}>Author</span><br /><strong>{ce.author_name}</strong></div>}
            {ce.publisher_name && <div><span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--grey)', textTransform: 'uppercase' }}>Publisher</span><br /><strong>{ce.publisher_name}</strong></div>}
            {ce.language && <div><span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--grey)', textTransform: 'uppercase' }}>Language</span><br /><strong>{ce.language.toUpperCase()}</strong></div>}
          </div>

          <div className="rule-thin" />
          <p style={{ fontSize: '0.9rem', color: 'var(--grey)', marginBottom: '1rem', fontStyle: 'italic' }}>{ce.summary}</p>

          {ce.claims.map((claim, i) => {
            const cv = cvs?.find(c => c.claim_id === claim.id)
            return (
              <div key={claim.id} style={{
                padding: '1rem',
                borderLeft: '4px solid',
                borderLeftColor: cv ? {
                  'True': 'var(--green)', 'False': 'var(--red)',
                  'Partially True': 'var(--amber)', 'Insufficient Evidence': 'var(--grey)'
                }[cv.verdict] : 'var(--border-light)',
                background: '#fafaf8',
                marginBottom: '0.8rem',
              }}>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.4rem', flexWrap: 'wrap' }}>
                      <span className="tag">{claim.claim_type}</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--grey)' }}>Confidence: {Math.round(claim.confidence * 100)}%</span>
                    </div>
                    <p style={{ fontWeight: 500, marginBottom: '0.4rem' }}>{claim.claim_text}</p>
                    <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--grey)' }}>
                      <strong>{claim.subject}</strong> → {claim.predicate} → <strong>{claim.object}</strong>
                    </p>
                  </div>
                  {cv && <VerdictBadge verdict={cv.verdict} size="sm" />}
                </div>
                {cv && <p style={{ fontSize: '0.82rem', color: 'var(--grey)', marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid var(--border-light)' }}>{cv.reasoning}</p>}
              </div>
            )
          })}

          {/* Named entities */}
          {ce.named_entities?.length > 0 && (
            <div style={{ marginTop: '1rem' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--grey)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>Named Entities</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                {ce.named_entities.map((e, i) => (
                  <span key={i} className="tag" title={`${e.label} — ${Math.round(e.confidence * 100)}%`}>
                    {e.text} <span style={{ color: 'var(--grey)' }}>({e.label})</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </Section>
      )}

      {/* ── Author + Publisher ── */}
      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {av && (
          <div className="card fade-up-1">
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--grey)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.1em' }}>02 — Author Credibility</div>
            <h3 style={{ marginBottom: '1rem' }}>{av.author_name}</h3>
            <ScoreBar score={av.credibility_score} label="Credibility Score" />
            <div className="rule-thin" />
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.8rem' }}>
              {av.found_in_journalist_db && <span className="tag tag-green">✓ In Journalist DB</span>}
              {av.public_profile_found && <span className="tag tag-green">✓ Public Profile</span>}
              {av.flags?.map(f => <span key={f} className="tag tag-red">{f}</span>)}
            </div>
            {av.known_outlets?.length > 0 && <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--grey)' }}>Known outlets: {av.known_outlets.join(', ')}</div>}
            <p style={{ fontSize: '0.85rem', color: 'var(--grey)', marginTop: '0.8rem' }}>{av.reasoning}</p>
          </div>
        )}

        {pv && (
          <div className="card fade-up-2">
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--grey)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.1em' }}>03 — Publisher Credibility</div>
            <h3 style={{ marginBottom: '1rem' }}>{pv.publisher_name}</h3>
            <ScoreBar score={pv.credibility_score} label="Credibility Score" />
            <div className="rule-thin" />
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.8rem' }}>
              {pv.domain && <span className="tag">{pv.domain}</span>}
              {pv.domain_age_years && <span className="tag">{pv.domain_age_years}y old domain</span>}
              {pv.country && <span className="tag">{pv.country}</span>}
              {pv.in_fake_news_db && <span className="tag tag-red">⚠ Fake News DB</span>}
              {pv.flags?.map(f => <span key={f} className="tag tag-red">{f}</span>)}
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--grey)', marginTop: '0.8rem' }}>{pv.reasoning}</p>
          </div>
        )}
      </div>

      {/* ── Evidence ── */}
      {eg?.length > 0 && (
        <Section title="EVIDENCE ANALYSIS" number="04">
          {eg.map((ev, i) => (
            <div key={ev.claim_id} style={{ marginBottom: '1.5rem' }}>
              <div style={{ padding: '0.6rem 1rem', background: 'var(--paper-dark)', border: '1px solid var(--border-light)', marginBottom: '0.8rem', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                <strong>Claim:</strong> {ev.claim_text}
              </div>
              <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '0.8rem' }}>
                <span className="tag tag-green">✅ {ev.supporting_count} Supporting</span>
                <span className="tag tag-red">❌ {ev.contradicting_count} Contradicting</span>
                <span className="tag">⬜ {ev.neutral_count} Neutral</span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--grey)', marginBottom: '0.8rem', fontStyle: 'italic' }}>{ev.evidence_summary}</p>

              <div style={{ border: '1px solid var(--border-light)' }}>
                {ev.articles?.slice(0, 6).map((a, j) => (
                  <div key={j} className="evidence-item">
                    <span style={{
                      fontSize: '1.1rem', minWidth: 24,
                      color: a.stance === 'supporting' ? 'var(--green)' : a.stance === 'contradicting' ? 'var(--red)' : 'var(--grey)'
                    }}>
                      {a.stance === 'supporting' ? '✅' : a.stance === 'contradicting' ? '❌' : '⬜'}
                    </span>
                    <div style={{ flex: 1 }}>
                      <a href={a.url} target="_blank" rel="noopener" style={{ color: 'var(--blue)', fontWeight: 500, fontSize: '0.9rem', textDecoration: 'none' }}>{a.title}</a>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--grey)', marginTop: '0.2rem' }}>
                        {a.publisher} {a.published_date && `· ${a.published_date}`} · Relevance: {Math.round(a.relevance_score * 100)}%
                      </div>
                      <p style={{ fontSize: '0.82rem', color: 'var(--grey)', marginTop: '0.3rem' }}>{a.summary}</p>
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
