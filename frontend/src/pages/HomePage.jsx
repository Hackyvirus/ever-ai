import { useState } from 'react'
import { analyzeText } from '../lib/api'
import AgentStatus from '../components/AgentStatus'
import ReportDashboard from '../components/ReportDashboard'
import { useLang } from '../lib/LanguageContext'
import { useTranslation } from '../lib/i18n'

const EXAMPLES = {
  en: [
    { label:'WhatsApp Forward', text:`BREAKING: Scientists at Harvard confirmed drinking lemon water cures cancer. Dr. John Smith published this in Nature journal. Big Pharma is hiding this cure! Forward to save lives!` },
    { label:'News Claim', text:`According to Reuters, the World Health Organization announced global vaccination rates reached 78% as of March 2024. WHO Director stated this is the highest level ever recorded.` },
    { label:'Political Claim', text:`Narendra Modi is the Prime Minister of India and has been serving since 2014. He leads the BJP party and won the 2024 general elections.` },
  ],
  hi: [
    { label:'WhatsApp फ़ॉरवर्ड', text:`ब्रेकिंग: हार्वर्ड के वैज्ञानिकों ने पुष्टि की है कि नींबू पानी पीने से कैंसर ठीक हो जाता है। डॉ. जॉन स्मिथ ने यह नेचर जर्नल में प्रकाशित किया है। इसे शेयर करें!` },
    { label:'समाचार दावा', text:`रिपोर्ट के अनुसार नरेंद्र मोदी भारत के प्रधानमंत्री हैं और 2014 से सेवा कर रहे हैं। वे भाजपा पार्टी के नेता हैं।` },
    { label:'राजनीतिक दावा', text:`सुशांत अत्राम भारत के प्रधानमंत्री हैं। उन्होंने 2024 के चुनाव में जीत हासिल की।` },
  ],
  mr: [
    { label:'WhatsApp फॉरवर्ड', text:`ब्रेकिंग: हार्वर्डच्या शास्त्रज्ञांनी पुष्टी केली की लिंबू पाणी पिल्याने कर्करोग बरा होतो. हे शेअर करा!` },
    { label:'बातमी दावा', text:`नरेंद्र मोदी भारताचे पंतप्रधान आहेत आणि 2014 पासून सेवा करत आहेत. ते भाजप पक्षाचे नेते आहेत.` },
    { label:'राजकीय दावा', text:`सुशांत अत्राम भारताचे पंतप्रधान आहेत. त्यांनी 2024 च्या निवडणुकीत विजय मिळवला.` },
  ],
}

export default function HomePage() {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const { lang } = useLang()
  const t = useTranslation(lang)

  const handleAnalyze = async () => {
    if (!text.trim() || text.length < 20) return
    setLoading(true); setResult(null); setError(null)
    try {
      const r = await analyzeText(text)
      setResult(r)
    } catch(e) {
      setError(e.response?.data?.detail || e.message || 'Analysis failed. Check your API key.')
    } finally { setLoading(false) }
  }

  const examples = EXAMPLES[lang] || EXAMPLES.en

  return (
    <div className="container" style={{ padding:'1.5rem 1rem' }}>
      <div className="fade-up" style={{ marginBottom:'1.5rem' }}>
        <div style={{ fontFamily:'var(--font-mono)', fontSize:'.68rem', letterSpacing:'.12em', color:'var(--grey)', textTransform:'uppercase', marginBottom:'.4rem' }}>5-Agent AI System</div>
        <h2 style={{ marginBottom:'.4rem' }}>{t.pageTitle}</h2>
        <p style={{ color:'var(--grey)', maxWidth:600, fontSize:'.9rem' }}>{t.pageDesc}</p>
      </div>

      <hr className="rule" />

      <div className="fade-up-1" style={{ marginBottom:'1.2rem' }}>
        <textarea className="news-input" value={text} onChange={e=>setText(e.target.value)}
          placeholder={t.inputPlaceholder} disabled={loading} />

        {/* Controls row — responsive */}
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginTop:'.7rem', flexWrap:'wrap', gap:'.6rem' }}>
          <div style={{ display:'flex', gap:'.4rem', flexWrap:'wrap' }}>
            {examples.map(ex => (
              <button key={ex.label} className="btn btn-ghost btn-sm" onClick={()=>setText(ex.text)} disabled={loading}>{ex.label}</button>
            ))}
          </div>
          <div style={{ display:'flex', alignItems:'center', gap:'.8rem', flexWrap:'wrap' }}>
            <span style={{ fontFamily:'var(--font-mono)', fontSize:'.72rem', color:text.length<20?'var(--red)':'var(--grey)' }}>
              {text.length} chars {text.length<20 && t.minChars}
            </span>
            <button className="btn" onClick={handleAnalyze} disabled={loading||text.length<20} style={{ opacity:text.length<20?.5:1 }}>
              {loading
                ? <><span className="spinner" style={{ width:16,height:16,borderColor:'rgba(255,255,255,.3)',borderTopColor:'white' }}/> {t.analyzingBtn}</>
                : `🔍 ${t.analyzeBtn}`}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="card" style={{ border:'2px solid var(--red)', background:'var(--red-light)', marginBottom:'1.2rem', fontSize:'.9rem' }}>
          <strong style={{ color:'var(--red)' }}>❌ Error:</strong> {error}
        </div>
      )}

      {loading && (
        <div className="fade-up" style={{ marginBottom:'1.5rem' }}>
          <h3 style={{ marginBottom:'.8rem', fontSize:'clamp(1rem,2.5vw,1.5rem)' }}>RUNNING ANALYSIS PIPELINE</h3>
          <AgentStatus result={null} />
        </div>
      )}

      {result && !loading && (
        <div className="fade-up">
          <div className="rule-double" />
          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:'1.2rem', flexWrap:'wrap', gap:'.5rem' }}>
            <h2>{t.analysisReport}</h2>
            <a href={`/report/${result.query_id}`} style={{ fontFamily:'var(--font-mono)', fontSize:'.72rem', color:'var(--blue)', whiteSpace:'nowrap' }}>
              {t.permalink}
            </a>
          </div>
          <ReportDashboard result={result} />
        </div>
      )}
    </div>
  )
}
