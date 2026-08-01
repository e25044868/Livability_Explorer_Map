import { LocateIcon } from './Icons'
import type { CategoryKey, Coordinates, Place, QueryMode } from '../types'

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
}

const categoryOptions: { key: CategoryKey; label: string; symbol: string; available: boolean }[] = [
  { key: 'parking', label: '路外停車場', symbol: 'P', available: true },
  { key: 'toilet', label: '公共廁所', symbol: 'WC', available: true },
  { key: 'aed', label: 'AED', symbol: 'AED', available: true },
  { key: 'drinking_water', label: '公共飲水機', symbol: '水', available: true },
  { key: 'shelter', label: '避難收容處所', symbol: '安', available: true },
  { key: 'pharmacy', label: '藥局', symbol: '藥', available: false },
  { key: 'medical', label: '醫療院所', symbol: '醫', available: false },
  { key: 'motorcycle_charging', label: '機車充電', symbol: '⚡', available: false },
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
}: Props) {
  const carSpaces = places.reduce((sum, place) => sum + (place.properties.car_spaces ?? 0), 0)
  const motorcycleSpaces = places.reduce(
    (sum, place) => sum + (place.properties.motorcycle_spaces ?? 0),
    0,
  )

  return (
    <aside className="analysis-panel" aria-label="分析條件與摘要">
      <section className="panel-section location-section">
        <p className="eyebrow">分析中心</p>
        <div className="location-row">
          <div>
            <strong>高雄市中心</strong>
            <span>{center.lat.toFixed(4)}, {center.lng.toFixed(4)}</span>
          </div>
          <button className="icon-button" onClick={onLocate} title="使用目前位置" aria-label="使用目前位置">
            <LocateIcon />
          </button>
        </div>
      </section>

      <section className="panel-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">探索範圍</p>
            <h2>{queryMode === 'radius' ? '中心點半徑' : queryMode === 'city' ? '縣市瀏覽' : '目前地圖區域'}</h2>
          </div>
          {queryMode === 'viewport' && <span className="status-chip">區域搜尋</span>}
        </div>
        <div className="radius-switch" aria-label="選擇搜尋半徑">
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
      </section>

      <section className="panel-section category-section">
        <p className="eyebrow">資料類別</p>
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
                <span><strong>{option.label}</strong><small>{option.available ? '全國政府開放資料' : '待地理編碼'}</small></span>
                <span className="category-count">{option.available ? (loading ? '—' : count) : '—'}</span>
              </button>
            )
          })}
        </div>
        <div className="coming-soon">無可信座標的類別不會顯示成地圖標記。</div>
      </section>

      <section className="panel-section summary-section">
        <div className="section-heading">
          <div><p className="eyebrow">區域摘要</p><h2>停車供給概況</h2></div>
        </div>
        <div className="metrics-grid">
          <div className="metric primary"><span>設施總數</span><strong>{loading ? '—' : places.length}</strong><small>處</small></div>
          <div className="metric"><span>汽車格</span><strong>{loading ? '—' : carSpaces.toLocaleString()}</strong><small>格</small></div>
          <div className="metric"><span>機車格</span><strong>{loading ? '—' : motorcycleSpaces.toLocaleString()}</strong><small>格</small></div>
        </div>
      </section>

      <footer className="data-note">
        <span className="live-dot" />
        <span>{dataVersion === 'empty' ? '等待資料' : `資料更新 ${formatDate(dataVersion)}`}</span>
      </footer>
    </aside>
  )
}

function formatDate(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('zh-TW')
}
