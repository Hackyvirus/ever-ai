import { Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import HomePage from './pages/HomePage'
import ReportPage from './pages/ReportPage'
import HistoryPage from './pages/HistoryPage'

export default function App() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header />
      <main style={{ flex: 1 }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/report/:id" element={<ReportPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
      </main>
      <footer style={{
        borderTop: '2px solid var(--ink)',
        padding: '1.2rem 1.5rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'var(--paper-dark)',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.75rem',
        color: 'var(--grey)'
      }}>
        <span>EverAI © {new Date().getFullYear()}</span>
        <span>MULTI-AGENT FAKE NEWS DETECTOR</span>
        <span>POWERED BY EVERSITY TECH LLP</span>
      </footer>
    </div>
  )
}
