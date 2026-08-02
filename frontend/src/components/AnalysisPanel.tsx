import { useRef, useState, type CSSProperties } from 'react'
import { LocateIcon } from './Icons'
import { CitySelector } from './CitySelector'
import { SearchBar } from './SearchBar'
import type { CategoryKey, Coordinates, Place, QueryMode } from '../types'
import { useI18n } from '../i18n'

type Props = {
  center: Coordinates
  radius: number
  queryMode: QueryMode
  places: Place[]
  loading: boolean
  dataVersion: string
  onRadiusChange: (radius: number) => void
  onLocate: () => void
  activeCategories: CategoryKey[]
  onToggleCategory: (category: CategoryKey) => void
  city: string
  district: string | null
  districts: string[]
  detectedCity: string | null
  onCityChange: (city: string) => void
  onDistrictChange: (district: string | null) => void
  onSearchSelect: (place: Place) => void
}

const categoryOptions: { key: CategoryKey; symbol: string; available: boolean }[] = [
  { key: 'parking', symbol: 'P', available: true },
  { key: 'toilet', symbol: 'WC', available: true },
  { key: 'aed', symbol: 'AED', available: true },
  { key: 'drinking_water', symbol: '水', available: true },
  { key: 'shelter', symbol: '安', available: true },
  { key: 'public_wifi', symbol: 'WiFi', available: true },
  { key: 'rescue_unit', symbol: '119', available: true },
  { key: 'police', symbol: '警', available: true },
  { key: 'library', symbol: '書', available: true },
  { key: 'public_bicycle', symbol: '車', available: true },
  { key: 'pharmacy', symbol: '藥', available: false },
  { key: 'medical', symbol: '醫', available: false },
  { key: 'motorcycle_charging', symbol: '⚡', available: false },
]

const radii = [500, 1000, 3000]

export function AnalysisPanel({
  center,
  radius,
  queryMode,
  places,
  loading,
  dataVersion,
  onRadiusChange,
  onLocate,
  activeCategories,
  onToggleCategory,
  city,
  district,
  districts,
  detectedCity,
  onCityChange,
  onDistrictChange,
  onSearchSelect,
}: Props) {
  const { language, t, categoryLabel } = useI18n()
  const [mobileCategoriesOpen, setMobileCategoriesOpen] = useState(false)
  const [mobileSheetOpen, setMobileSheetOpen] = useState(false)
  const sheetTouchStart = useRef<number | null>(null)
  const suppressSheetClick = useRef(false)
  const carSpaces = places.reduce((sum, place) => sum + (place.properties.car_spaces ?? 0), 0)
  const motorcycleSpaces = places.reduce(
    (sum, place) => sum + (place.properties.motorcycle_spaces ?? 0),
    0,
  )

  return (
    <aside className={`analysis-panel ${mobileSheetOpen ? 'mobile-sheet-open' : ''}`} aria-label={t('analysisCenter')}>
      <button
        className="mobile-sheet-handle"
        onClick={() => {
          if (suppressSheetClick.current) { suppressSheetClick.current = false; return }
          setMobileSheetOpen((current) => !current)
        }}
        onPointerDown={(event) => { sheetTouchStart.current = event.clientY }}
        onPointerUp={(event) => {
          if (sheetTouchStart.current == null) return
          const movement = event.clientY - sheetTouchStart.current
          if (Math.abs(movement) > 28) suppressSheetClick.current = true
          if (movement < -28) setMobileSheetOpen(true)
          if (movement > 28) setMobileSheetOpen(false)
          sheetTouchStart.current = null
        }}
        aria-expanded={mobileSheetOpen}
      >
        <span aria-hidden="true" />
        <strong>{t('mobilePanel')}</strong>
        <small>{activeCategories.length}</small>
      </button>
      <div className="mobile-sheet-content">
      <section className="panel-section location-section">
        <p className="eyebrow">{t('analysisCenter')}</p>
        <div className="location-row">
          <div>
            <strong>{district ? `${city} · ${district}` : city}</strong>
            <span>{center.lat.toFixed(4)}, {center.lng.toFixed(4)}</span>
          </div>
          <button className="icon-button" onClick={onLocate} title={t('useLocation')} aria-label={t('useLocation')}>
            <LocateIcon />
          </button>
        </div>
      </section>

      <section className="panel-section search-section">
        <p className="eyebrow">{t('searchAndBrowse')}</p>
        <div className="panel-search"><SearchBar onSelect={onSearchSelect} /></div>
        <CitySelector value={city} district={district} districts={districts} detectedCity={detectedCity} onChange={onCityChange} onDistrictChange={onDistrictChange} />
      </section>

      <section className="panel-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">{t('exploreRange')}</p>
            <h2>{queryMode === 'radius' ? t('centerRadius') : queryMode === 'city' ? t('cityBrowse') : t('mapArea')}</h2>
          </div>
          {queryMode === 'viewport' && <span className="status-chip">{t('areaSearch')}</span>}
        </div>
        <div className="radius-ticks" aria-label={t('chooseRadius')}>
          {radii.map((value) => (
            <button
              key={value}
              className={radius === value && queryMode === 'radius' ? 'active' : ''}
              onClick={() => onRadiusChange(value)}
            >
              {value < 1000 ? `${value} m` : `${value / 1000} km`}
            </button>
          ))}
        </div>
        <div className="radius-slider">
          <span className="sr-only">{t('adjustRadius')}</span>
          <input
            type="range"
            min="500"
            max="3000"
            step="100"
            value={radius}
            style={{ '--radius-progress': `${((radius - 500) / 2500) * 100}%` } as CSSProperties}
            onChange={(event) => onRadiusChange(Number(event.target.value))}
            aria-valuetext={formatRadius(radius, language)}
          />
          <span className="radius-slider-scale"><span>500 m</span><strong>{formatRadius(radius, language)}</strong><span>3 km</span></span>
        </div>
      </section>

      <section className={`panel-section category-section ${mobileCategoriesOpen ? 'mobile-open' : ''}`}>
        <p className="eyebrow">{t('dataCategories')}</p>
        <button className="mobile-category-toggle" onClick={() => setMobileCategoriesOpen((current) => !current)} aria-expanded={mobileCategoriesOpen}>
          <span>{t('dataCategories')}</span><strong>{activeCategories.length}</strong><span aria-hidden="true">{mobileCategoriesOpen ? '−' : '+'}</span>
        </button>
        <div className="category-list">
          {categoryOptions.map((option) => {
            const active = activeCategories.includes(option.key)
            const count = places.filter((place) => place.category === option.key).length
            return (
              <button
                key={option.key}
                className={`category-card category-${option.key} ${active ? 'active' : ''}`}
                disabled={!option.available}
                onClick={() => onToggleCategory(option.key)}
              >
                <span className="category-icon">{option.symbol}</span>
                <span><strong>{categoryLabel(option.key)}</strong><small>{option.available ? t('openData') : t('pendingGeocode')}</small></span>
                <span className="category-count">{option.available ? (loading ? '—' : count) : '—'}</span>
              </button>
            )
          })}
        </div>
        <div className="coming-soon">{t('noVerifiedCoordinates')}</div>
      </section>

      <section className="panel-section summary-section">
        <div className="section-heading">
          <div><p className="eyebrow">{t('areaSummary')}</p><h2>{t('parkingSummary')}</h2></div>
        </div>
        <div className="metrics-grid">
          <div className="metric primary"><span>{t('facilities')}</span><strong>{loading ? '—' : places.length}</strong><small>{t('placesUnit')}</small></div>
          <div className="metric"><span>{t('carSpaces')}</span><strong>{loading ? '—' : carSpaces.toLocaleString()}</strong><small>{t('spacesUnit')}</small></div>
          <div className="metric"><span>{t('motorcycleSpaces')}</span><strong>{loading ? '—' : motorcycleSpaces.toLocaleString()}</strong><small>{t('spacesUnit')}</small></div>
        </div>
      </section>

      <footer className="data-note">
        <span className="live-dot" />
        <span>{dataVersion === 'empty' ? t('waitingData') : `${t('dataUpdated')}${formatDate(dataVersion, language)}`}</span>
      </footer>
      </div>
    </aside>
  )
}

function formatDate(value: string, language: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString(language)
}

function formatRadius(value: number, language: string) {
  const label = value < 1000 ? `${value} m` : `${(value / 1000).toFixed(1).replace('.0', '')} km`
  return language === 'zh-TW' && value >= 1000 ? label.replace('km', '公里') : label
}
