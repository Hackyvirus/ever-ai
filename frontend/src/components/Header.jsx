import { Link, useLocation } from 'react-router-dom'
import { useLang } from '../lib/LanguageContext'
import { useTranslation, LANGUAGES } from '../lib/i18n'

export default function Header() {
  const loc = useLocation()
  const { lang, setLang } = useLang()
  const t = useTranslation(lang)

  const nav = [
    { to: '/',          label: t.analyzeNav },
    { to: '/history',   label: t.historyNav },
    { to: '/feedback',  label: t.feedbackNav },
    { to: '/disclaimer',label: 'Disclaimer', },
  ]

  return (
    <header style={{ borderBottom:'4px double var(--ink)', background:'var(--paper)', position:'sticky', top:0, zIndex:100 }}>
      {/* Top strip */}
      <div style={{ background:'var(--ink)', color:'var(--paper)', fontFamily:'var(--font-mono)', fontSize:'.62rem', letterSpacing:'.1em', padding:'.28rem 1rem', display:'flex', justifyContent:'space-between', flexWrap:'wrap', gap:'.3rem' }}>
        <span>AI-POWERED · 5-AGENT SYSTEM</span>
        <span style={{ color:'#fff' }}>AI results may be inaccurate — always verify independently</span>
      </div>

      {/* Masthead */}
      <div className="container" style={{ padding:'.7rem 1rem', display:'flex', alignItems:'center', justifyContent:'space-between', gap:'.8rem', flexWrap:'wrap' }}>
        <Link to="/" style={{ textDecoration:'none', color:'inherit' }}>
          <div style={{ display:'flex', alignItems:'baseline', gap:'.4rem' }}>
            <h1 style={{ fontSize:'clamp(1.6rem,4vw,2.8rem)', lineHeight:1 }}>
              EVER<span style={{ color:'var(--red)' }}>AI</span>
            </h1>
            <span style={{ fontFamily:'var(--font-mono)', fontSize:'.6rem', color:'var(--grey)', letterSpacing:'.08em' }}>v1.0</span>
          </div>
          <p style={{ fontFamily:'var(--font-mono)', fontSize:'.62rem', color:'var(--grey)', letterSpacing:'.08em', marginTop:'.05rem' }}>{t.tagline}</p>
        </Link>

        <div style={{ display:'flex', gap:'.4rem', alignItems:'center', flexWrap:'wrap' }}>
          {/* Language switcher */}
          <div style={{ display:'flex', gap:'.2rem', marginRight:'.4rem' }}>
            {LANGUAGES.map(l => (
              <button key={l.code} className={`lang-btn ${lang===l.code?'active':''}`} onClick={()=>setLang(l.code)} title={l.name}>{l.label}</button>
            ))}
          </div>
          {/* Nav links */}
          {nav.map(n => (
            <Link key={n.to} to={n.to} style={{
              fontFamily:'var(--font-display)', fontSize:'.85rem', letterSpacing:'.05em',
              color: n.warn ? 'var(--red)' : loc.pathname===n.to ? 'var(--paper)' : 'var(--ink)',
              background: loc.pathname===n.to ? 'var(--ink)' : 'transparent',
              border:`2px solid ${n.warn ? 'var(--red)' : 'var(--ink)'}`,
              padding:'.28rem .75rem', textDecoration:'none',
              transition:'all .15s', whiteSpace:'nowrap',
            }}>{n.label}</Link>
          ))}
        </div>
      </div>
      <div style={{ borderTop:'1px solid var(--border-light)' }} />
    </header>
  )
}
