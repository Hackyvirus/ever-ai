const STEPS = [
  { id: 'extract',   label: 'Extracting Claims',       icon: '📋', agent: 'Agent 1' },
  { id: 'author',    label: 'Verifying Author',         icon: '✍️', agent: 'Agent 2' },
  { id: 'publisher', label: 'Verifying Publisher',      icon: '📰', agent: 'Agent 3' },
  { id: 'evidence',  label: 'Gathering Evidence',       icon: '🔍', agent: 'Agent 4' },
  { id: 'verify',    label: 'Verifying Claims',         icon: '⚖️', agent: 'Agent 5' },
  { id: 'aggregate', label: 'Computing Final Verdict',  icon: '🧮', agent: 'Aggregator' },
]

export default function AgentStatus({ result }) {
  const getStep = () => {
    if (!result) return -1
    if (result.status === 'completed') return 6
    if (!result.claim_extraction) return 0
    if (!result.author_verification) return 1
    if (!result.publisher_verification) return 2
    if (!result.evidence_gathering?.length) return 3
    if (!result.claim_verifications?.length) return 4
    if (!result.aggregated) return 5
    return 6
  }

  const step = getStep()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
      {STEPS.map((s, i) => {
        const done = step > i
        const active = step === i
        const pending = step < i

        return (
          <div key={s.id} style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            padding: '0.7rem 1rem',
            border: `2px solid ${active ? 'var(--ink)' : done ? 'var(--green)' : 'var(--border-light)'}`,
            background: done ? 'var(--green-light)' : active ? 'white' : 'transparent',
            transition: 'all 0.3s',
            opacity: pending ? 0.45 : 1,
          }}>
            <span style={{ fontSize: '1.2rem', minWidth: 28 }}>
              {done ? '✓' : active ? <span className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} /> : s.icon}
            </span>
            <div style={{ flex: 1 }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', color: 'var(--grey)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>{s.agent}</div>
              <div style={{ fontWeight: 500, fontSize: '0.9rem' }}>{s.label}</div>
            </div>
            <span style={{
              fontFamily: 'var(--font-display)',
              fontSize: '0.85rem',
              letterSpacing: '0.06em',
              color: done ? 'var(--green)' : active ? 'var(--ink)' : 'var(--grey)',
            }}>
              {done ? 'DONE' : active ? 'RUNNING' : 'PENDING'}
            </span>
          </div>
        )
      })}
    </div>
  )
}
