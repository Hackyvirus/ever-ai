import { Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import HomePage from './pages/HomePage'
import ReportPage from './pages/ReportPage'
import HistoryPage from './pages/HistoryPage'
import FeedbackPage from './pages/FeedbackPage'
import WhatsAppReportPage from './pages/WhatsAppReportPage'
import DisclaimerPage from './pages/DisclaimerPage'
import { useLang } from './lib/LanguageContext'
import { useTranslation } from './lib/i18n'
import { Link } from 'react-router-dom'

export default function App() {
  const { lang } = useLang()
  const t = useTranslation(lang)
  return (
    <div style={{ minHeight:'100vh', display:'flex', flexDirection:'column' }}>
      <Header />
      <main style={{ flex:1 }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/report/:id" element={<ReportPage />} />
          <Route path="/wa-report/:id" element={<WhatsAppReportPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/feedback" element={<FeedbackPage />} />
          <Route path="/disclaimer" element={<DisclaimerPage />} />
        </Routes>
      </main>

      {/* Footer */}
      <footer style={{
        borderTop:'2px solid var(--ink)', padding:'.9rem 1.5rem',
        background:'var(--paper-dark)', fontFamily:'var(--font-mono)',
        fontSize:'.68rem', color:'var(--grey)',
      }}>
        <div style={{ maxWidth:1100, margin:'0 auto', display:'flex', justifyContent:'space-between', alignItems:'center', flexWrap:'wrap', gap:'.5rem' }}>
          <span>EVERAI © {new Date().getFullYear()} · AI-POWERED FACT CHECKER</span>
          <div style={{ display:'flex', gap:'1.2rem', flexWrap:'wrap' }}>
            <Link to="/disclaimer" style={{ color:'#686060', textDecoration:'none', fontWeight:600, letterSpacing:'.05em' }}>
              ⚠ DISCLAIMER
            </Link>
            <Link to="/feedback" style={{ color:'var(--grey)', textDecoration:'none' }}>FEEDBACK</Link>
            <Link to="/history" style={{ color:'var(--grey)', textDecoration:'none' }}>HISTORY</Link>
          </div>
          <span style={{ color:'#aaa' }}>{t.poweredBy}</span>
        </div>
      </footer>
    </div>
  )
}
