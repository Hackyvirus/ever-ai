import { Link, useLocation } from 'react-router-dom'

export default function Header() {
  const loc = useLocation()
  const nav = [
    { to: '/', label: 'Analyze' },
    { to: '/history', label: 'History' },
  ]

  return (
    <header style={{
      borderBottom: '4px double var(--ink)',
      background: 'var(--paper)',
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      {/* Top strip */}
      <div style={{
        background: 'var(--ink)',
        color: 'var(--paper)',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.65rem',
        letterSpacing: '0.12em',
        padding: '0.3rem 1.5rem',
        display: 'flex',
        justifyContent: 'space-between',
      }}>
        <span>AI-POWERED • 5-AGENT SYSTEM • OPENAI GPT-4O</span>
        <span>MULTI-AGENT FAKE NEWS DETECTION</span>
      </div>

      {/* Masthead */}
      <div className="container" style={{
        padding: '0.8rem 1.5rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem',
      }}>
        <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
            <h1 style={{ fontSize: 'clamp(1.8rem, 4vw, 3rem)', lineHeight: 1 }}>
              FAKE<span style={{ color: 'var(--red)' }}>SHIELD</span>
            </h1>
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.65rem',
              color: 'var(--grey)',
              letterSpacing: '0.1em',
              paddingBottom: '0.2rem',
              borderBottom: '1px solid var(--grey)'
            }}>v1.0 MVP</span>
          </div>
          <p style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.7rem',
            color: 'var(--grey)',
            letterSpacing: '0.1em',
            marginTop: '0.1rem'
          }}>THE TRUTH VERIFICATION ENGINE</p>
        </Link>

        <nav style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          {nav.map(n => (
            <Link
              key={n.to}
              to={n.to}
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: '1rem',
                letterSpacing: '0.06em',
                color: loc.pathname === n.to ? 'var(--paper)' : 'var(--ink)',
                background: loc.pathname === n.to ? 'var(--ink)' : 'transparent',
                border: '2px solid var(--ink)',
                padding: '0.3rem 1rem',
                textDecoration: 'none',
                transition: 'all 0.15s',
              }}
            >{n.label}</Link>
          ))}
        </nav>
      </div>

      <div className="rule" style={{ margin: 0, borderTopWidth: '1px', borderColor: 'var(--border-light)' }} />
    </header>
  )
}
