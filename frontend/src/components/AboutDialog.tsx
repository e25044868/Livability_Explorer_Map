import { CloseIcon } from './Icons'
import { useI18n } from '../i18n'

type Props = {
  onClose: () => void
}

const sources = [
  { key: 'parkingSource', href: 'https://tdx.transportdata.tw/' },
  { key: 'toiletSource', href: 'https://data.gov.tw/dataset/30794' },
  { key: 'aedSource', href: 'https://data.gov.tw/dataset/12063' },
  { key: 'waterSource', href: 'https://data.gov.tw/dataset/177893' },
  { key: 'shelterSource', href: 'https://data.gov.tw/dataset/73242' },
  { key: 'wifiSource', href: 'https://data.gov.tw/dataset/5962' },
  { key: 'tourismFacilitySource', href: 'https://data.gov.tw/dataset/113960' },
] as const

export function AboutDialog({ onClose }: Props) {
  const { t } = useI18n()

  return (
    <div className="about-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="about-dialog" role="dialog" aria-modal="true" aria-labelledby="about-title" onMouseDown={(event) => event.stopPropagation()}>
        <div className="about-header">
          <div><p className="eyebrow">{t('aboutEyebrow')}</p><h2 id="about-title">{t('aboutTitle')}</h2></div>
          <button className="drawer-close" onClick={onClose} aria-label={t('closeAbout')}><CloseIcon /></button>
        </div>
        <p className="about-intro">{t('aboutIntro')}</p>
        <h3>{t('officialSources')}</h3>
        <ul className="about-source-list">
          {sources.map((source) => <li key={source.key}><a href={source.href} target="_blank" rel="noreferrer">{t(source.key)} <span aria-hidden="true">↗</span></a></li>)}
        </ul>
        <p className="about-note">{t('aboutNote')}</p>
      </section>
    </div>
  )
}
