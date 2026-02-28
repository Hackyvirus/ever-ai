import { useLang } from '../../lib/LanguageContext'
import { useTranslation } from '../../lib/i18n'

export default function VerdictBadge({ verdict, size = 'md' }) {
  const { lang } = useLang()
  const t = useTranslation(lang)
  const CONFIG = {
    'True':                 { cls:'verdict-true',         icon:'✅', label: t.verdictTrue },
    'False':                { cls:'verdict-false',         icon:'❌', label: t.verdictFalse },
    'Partially True':       { cls:'verdict-partial',       icon:'⚠️', label: t.verdictPartial },
    'Insufficient Evidence':{ cls:'verdict-insufficient',  icon:'❓', label: t.verdictInsufficient },
  }
  const cfg = CONFIG[verdict] || CONFIG['Insufficient Evidence']
  const fs = size==='lg' ? '1.4rem' : size==='sm' ? '.75rem' : '.9rem'
  const px = size==='lg' ? '1.2rem' : '.7rem'
  const py = size==='lg' ? '.45rem' : '.25rem'
  return (
    <span className={`verdict ${cfg.cls}`} style={{ fontSize:fs, padding:`${py} ${px}` }}>
      {cfg.icon} {cfg.label}
    </span>
  )
}
