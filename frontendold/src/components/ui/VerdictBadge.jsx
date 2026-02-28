const CONFIG = {
  'True':                 { cls: 'verdict-true',         icon: '✅', label: 'TRUE' },
  'False':                { cls: 'verdict-false',         icon: '❌', label: 'FALSE' },
  'Partially True':       { cls: 'verdict-partial',       icon: '⚠️', label: 'PARTIALLY TRUE' },
  'Insufficient Evidence':{ cls: 'verdict-insufficient',  icon: '❓', label: 'INSUFFICIENT EVIDENCE' },
}

export default function VerdictBadge({ verdict, size = 'md' }) {
  const cfg = CONFIG[verdict] || CONFIG['Insufficient Evidence']
  const fs = size === 'lg' ? '1.6rem' : size === 'sm' ? '0.8rem' : '1rem'
  const px = size === 'lg' ? '1.4rem' : '0.8rem'
  const py = size === 'lg' ? '0.5rem' : '0.3rem'

  return (
    <span className={`verdict ${cfg.cls}`} style={{ fontSize: fs, padding: `${py} ${px}` }}>
      {cfg.icon} {cfg.label}
    </span>
  )
}
