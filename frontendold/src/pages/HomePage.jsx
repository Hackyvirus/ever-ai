import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyzeText } from '../lib/api'
import AgentStatus from '../components/AgentStatus'
import ReportDashboard from '../components/ReportDashboard'

const EXAMPLES = [
  {
    label: 'WhatsApp Forward',
    text: `BREAKING: Scientists at Harvard have confirmed that drinking warm lemon water every morning cures cancer within 3 months. Big Pharma doesn't want you to know this! Share before they delete it. Dr. John Smith from Harvard Medical School published this in Nature journal last week. Over 10,000 patients cured. Forward to save lives!`,
  },
  {
    label: 'News Claim',
    text: `According to a report by Reuters, the World Health Organization announced that global vaccination rates have reached 78% as of March 2024, the highest level ever recorded. WHO Director Dr. Jane Doe stated that this represents a major milestone in global public health. The report also noted that polio has been eradicated in 5 new countries.`,
  },
  {
    label: 'Political Claim',
    text: `The government released data showing unemployment dropped to 3.2% last quarter, the lowest rate in 50 years. Finance Minister Carlos Mendez attributed this to new economic policies implemented in 2023. Opposition parties disputed the methodology used in the calculations, claiming the real figure is closer to 6.8% when accounting for underemployment.`,
  },
]

export default function HomePage() {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const handleAnalyze = async () => {
    if (!text.trim() || text.length < 20) return
    setLoading(true)
    setResult(null)
    setError(null)

    try {
      const r = await analyzeText(text)
      setResult(r)
      // Optionally navigate to report page
      // navigate(`/report/${r.query_id}`)
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Analysis failed. Check your API key.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container" style={{ padding: '2rem 1.5rem' }}>
      {/* Page header */}
      <div className="fade-up" style={{ marginBottom: '2rem' }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', letterSpacing: '0.15em', color: 'var(--grey)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
          5-Agent AI System
        </div>
        <h2 style={{ marginBottom: '0.5rem' }}>PASTE NEWS TO VERIFY</h2>
        <p style={{ color: 'var(--grey)', maxWidth: 600 }}>
          Submit any news article, WhatsApp forward, or social media post. Our 5 AI agents will analyze author credibility, publisher reputation, and verify each claim against evidence.
        </p>
      </div>

      <hr className="rule" />

      {/* Input area */}
      <div className="fade-up-1" style={{ marginBottom: '1.5rem' }}>
        <textarea
          className="news-input"
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Paste news text, WhatsApp message, or social media post here…&#10;&#10;Example: 'BREAKING: Scientists confirm that...' or paste a full article."
          disabled={loading}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.8rem', flexWrap: 'wrap', gap: '0.8rem' }}>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {EXAMPLES.map(ex => (
              <button
                key={ex.label}
                className="btn btn-ghost"
                style={{ fontSize: '0.8rem', padding: '0.3rem 0.8rem' }}
                onClick={() => setText(ex.text)}
                disabled={loading}
              >
                {ex.label}
              </button>
            ))}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: text.length < 20 ? 'var(--red)' : 'var(--grey)' }}>
              {text.length} chars {text.length < 20 && '(min 20)'}
            </span>
            <button
              className="btn"
              onClick={handleAnalyze}
              disabled={loading || text.length < 20}
              style={{ opacity: text.length < 20 ? 0.5 : 1 }}
            >
              {loading ? <><span className="spinner" style={{ width: 18, height: 18, borderColor: 'rgba(255,255,255,0.3)', borderTopColor: 'white' }} /> ANALYZING…</> : '🔍 ANALYZE'}
            </button>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="card" style={{ border: '2px solid var(--red)', background: 'var(--red-light)', marginBottom: '1.5rem' }}>
          <strong style={{ color: 'var(--red)' }}>❌ Error:</strong> {error}
        </div>
      )}

      {/* Agent progress during loading */}
      {loading && (
        <div className="fade-up" style={{ marginBottom: '2rem' }}>
          <h3 style={{ marginBottom: '1rem' }}>RUNNING ANALYSIS PIPELINE</h3>
          <AgentStatus result={null} />
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <div className="fade-up">
          <div className="rule-double" />
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
            <h2>ANALYSIS REPORT</h2>
            <a
              href={`/report/${result.query_id}`}
              style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--blue)' }}
            >
              Permalink →
            </a>
          </div>
          <ReportDashboard result={result} />
        </div>
      )}
    </div>
  )
}
