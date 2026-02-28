import { Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import HomePage from './pages/HomePage'
import ReportPage from './pages/ReportPage'
import HistoryPage from './pages/HistoryPage'
import FeedbackPage from './pages/FeedbackPage'
import WhatsAppReportPage from './pages/WhatsAppReportPage'
import { useLang } from './lib/LanguageContext'
import { useTranslation } from './lib/i18n'

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
        </Routes>
      </main>
      <footer style={{
        borderTop:'2px solid var(--ink)', padding:'1rem 1.5rem',
        display:'flex', justifyContent:'space-between', alignItems:'center',
        flexWrap:'wrap', gap:'.5rem',
        background:'var(--paper-dark)', fontFamily:'var(--font-mono)',
        fontSize:'.7rem', color:'var(--grey)'
      }}>
        <span>EVERAI © {new Date().getFullYear()}</span>
        <span style={{display:'none'}}>MULTI-AGENT FAKE NEWS DETECTOR</span>
        <span>{t.poweredBy}</span>
      </footer>
    </div>
  )
}
