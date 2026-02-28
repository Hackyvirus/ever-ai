export default function ScoreBar({ score, label, size = 'md' }) {
  const color =
    score >= 70 ? 'var(--green)' :
    score >= 45 ? 'var(--amber)' :
    'var(--red)'

  const h = size === 'lg' ? 18 : 12

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', alignItems: 'baseline' }}>
        {label && <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--grey)' }}>{label}</span>}
        <span style={{ fontFamily: 'var(--font-display)', fontSize: size === 'lg' ? '2rem' : '1.4rem', color }}>{Math.round(score)}<span style={{ fontSize: '0.6em', color: 'var(--grey)' }}>/100</span></span>
      </div>
      <div className="score-bar-track" style={{ height: h }}>
        <div
          className="score-bar-fill"
          style={{ width: `${score}%`, background: color }}
        />
      </div>
    </div>
  )
}
