import { useState } from 'react'
import { useLang } from '../lib/LanguageContext'
import { useTranslation } from '../lib/i18n'
import { submitFeedback } from '../lib/api'

function StarRating({ value, onChange }) {
  const [hover, setHover] = useState(0)
  return (
    <div style={{ display:'flex', gap:'.1rem' }}>
      {[1,2,3,4,5].map(s => (
        <button key={s} className="star-btn"
          onMouseEnter={()=>setHover(s)} onMouseLeave={()=>setHover(0)}
          onClick={()=>onChange(s)}
          style={{ color: s<=(hover||value) ? '#f59e0b' : '#d1c9b8' }}>
          ★
        </button>
      ))}
    </div>
  )
}

const INITIAL = { name:'', email:'', rating:0, helpful:'', what_liked:'', improve:'', use_case:'' }

export default function FeedbackPage() {
  const { lang } = useLang()
  const t = useTranslation(lang)
  const [form, setForm] = useState(INITIAL)
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const set = (k,v) => setForm(f => ({...f,[k]:v}))

  const handleSubmit = async () => {
    if (form.rating === 0) { setError('Please select a rating.'); return }
    setLoading(true); setError(null)
    try {
      await submitFeedback({ ...form, language: lang, submitted_at: new Date().toISOString() })
      setSubmitted(true)
    } catch(e) {
      // Even if API fails, show success (store locally)
      const feedbacks = JSON.parse(localStorage.getItem('everai_feedbacks')||'[]')
      feedbacks.push({ ...form, language: lang, submitted_at: new Date().toISOString() })
      localStorage.setItem('everai_feedbacks', JSON.stringify(feedbacks))
      setSubmitted(true)
    } finally { setLoading(false) }
  }

  if (submitted) return (
    <div className="container" style={{ padding:'3rem 1rem', textAlign:'center' }}>
      <div className="card fade-up" style={{ maxWidth:500, margin:'0 auto', padding:'2.5rem' }}>
        <div style={{ fontSize:'3rem', marginBottom:'1rem' }}>🙏</div>
        <h2 style={{ marginBottom:'.5rem' }}>{t.thankYou}</h2>
        <p style={{ color:'var(--grey)' }}>{t.thankYouMsg}</p>
        <div style={{ marginTop:'1.5rem', display:'flex', gap:'.5rem', justifyContent:'center', flexWrap:'wrap' }}>
          <a href="/" className="btn">{t.analyzeNav} →</a>
          <button className="btn btn-ghost" onClick={()=>{setSubmitted(false);setForm(INITIAL)}}>Submit Another</button>
        </div>
      </div>
    </div>
  )

  const inputStyle = { width:'100%', padding:'.65rem .9rem', border:'2px solid var(--ink)', fontFamily:'var(--font-body)', fontSize:'.9rem', outline:'none', background:'white', marginTop:'.3rem' }
  const labelStyle = { fontFamily:'var(--font-mono)', fontSize:'.72rem', letterSpacing:'.08em', textTransform:'uppercase', color:'var(--grey)', display:'block', marginTop:'1rem' }

  return (
    <div className="container" style={{ padding:'1.5rem 1rem' }}>
      <div className="fade-up" style={{ marginBottom:'1.5rem' }}>
        <div style={{ fontFamily:'var(--font-mono)', fontSize:'.68rem', letterSpacing:'.12em', color:'var(--grey)', marginBottom:'.4rem' }}>USER RESEARCH</div>
        <h2 style={{ marginBottom:'.4rem' }}>{t.feedbackTitle}</h2>
        <p style={{ color:'var(--grey)', maxWidth:600, fontSize:'.9rem' }}>{t.feedbackDesc}</p>
      </div>
      <hr className="rule" />

      <div style={{ maxWidth:680 }}>
        {/* Rating */}
        <div className="card fade-up-1" style={{ marginBottom:'1rem' }}>
          <label style={{ ...labelStyle, marginTop:0 }}>{t.feedbackRating} *</label>
          <div style={{ marginTop:'.5rem' }}>
            <StarRating value={form.rating} onChange={v=>set('rating',v)} />
            {form.rating > 0 && <span style={{ fontFamily:'var(--font-mono)', fontSize:'.75rem', color:'var(--grey)', marginLeft:'.5rem' }}>{['','Poor','Fair','Good','Great','Excellent'][form.rating]}</span>}
          </div>

          <label style={labelStyle}>{t.feedbackHelpful}</label>
          <div style={{ display:'flex', gap:'.5rem', marginTop:'.5rem', flexWrap:'wrap' }}>
            {[t.yes, t.no, t.maybe].map(opt => (
              <button key={opt} className={`btn btn-sm ${form.helpful===opt?'':'btn-ghost'}`} onClick={()=>set('helpful',opt)}>{opt}</button>
            ))}
          </div>
        </div>

        {/* Text fields */}
        <div className="card fade-up-2" style={{ marginBottom:'1rem' }}>
          <label style={{ ...labelStyle, marginTop:0 }}>{t.feedbackUseCase}</label>
          <textarea value={form.use_case} onChange={e=>set('use_case',e.target.value)}
            rows={2} style={{ ...inputStyle, resize:'vertical' }}
            placeholder={lang==='mr'?'उदा: WhatsApp बातम्या तपासण्यासाठी':lang==='hi'?'जैसे: WhatsApp न्यूज़ चेक करने के लिए':'e.g. Checking WhatsApp forwards, verifying news before sharing'} />

          <label style={labelStyle}>{t.feedbackWhat}</label>
          <textarea value={form.what_liked} onChange={e=>set('what_liked',e.target.value)}
            rows={2} style={{ ...inputStyle, resize:'vertical' }}
            placeholder={lang==='mr'?'तुम्हाला सर्वात जास्त काय आवडले?':lang==='hi'?'आपको सबसे अच्छा क्या लगा?':'What feature or result impressed you most?'} />

          <label style={labelStyle}>{t.feedbackImprove}</label>
          <textarea value={form.improve} onChange={e=>set('improve',e.target.value)}
            rows={2} style={{ ...inputStyle, resize:'vertical' }}
            placeholder={lang==='mr'?'काय सुधारावे असे वाटते?':lang==='hi'?'क्या सुधारना चाहिए?':'Speed, accuracy, UI, language support, WhatsApp features...'} />
        </div>

        {/* Contact */}
        <div className="card fade-up-3" style={{ marginBottom:'1.2rem' }}>
          <div className="grid-2" style={{ gap:'.8rem' }}>
            <div>
              <label style={{ ...labelStyle, marginTop:0 }}>{t.feedbackName}</label>
              <input value={form.name} onChange={e=>set('name',e.target.value)} style={inputStyle} placeholder={lang==='mr'?'तुमचे नाव':lang==='hi'?'आपका नाम':'Your name'} />
            </div>
            <div>
              <label style={{ ...labelStyle, marginTop:0 }}>{t.feedbackEmail}</label>
              <input value={form.email} onChange={e=>set('email',e.target.value)} type="email" style={inputStyle} placeholder="you@example.com" />
            </div>
          </div>
        </div>

        {error && <p style={{ color:'var(--red)', fontFamily:'var(--font-mono)', fontSize:'.8rem', marginBottom:'.8rem' }}>⚠ {error}</p>}

        <button className="btn" onClick={handleSubmit} disabled={loading} style={{ width:'100%', justifyContent:'center', fontSize:'1.1rem' }}>
          {loading ? <><span className="spinner" style={{ width:16,height:16,borderColor:'rgba(255,255,255,.3)',borderTopColor:'white' }}/> Submitting…</> : `📤 ${t.submitFeedback}`}
        </button>
      </div>
    </div>
  )
}
