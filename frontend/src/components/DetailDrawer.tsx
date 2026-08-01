import type { Place } from '../types'

type Props = {
  place: Place
  favorite: boolean
  onClose: () => void
  onToggleFavorite: () => void
  dataVersion: string
}

const labels: Record<string, string> = {
  facility_type: '停車場型式', fee_description: '收費方式', car_spaces: '汽車格',
  motorcycle_spaces: '機車格', large_vehicle_spaces: '大型車格', operator: '管理業者',
  contract_period_raw: '履約期間', toilet_type: '公廁類型', accessible: '無障礙設施',
  grade: '公廁等級', facility_category: '場所類別', administration: '主管機關',
  diaper: '尿布檯', location_description: 'AED 放置位置', available_hours: '開放時間',
  place_category: '場所分類',
  total_spaces: '總車位', available_spaces: '即時剩餘車位', operation_time: '營業時間',
  ev_spaces: '充電車位', accessible_spaces: '無障礙車位', parent_child_spaces: '親子車位',
  height_limit: '限高', monthly_pass: '月租資訊', live_updated_at: '即時資料更新',
  opening_hours: '開放時間', gender_friendly: '性別友善', parent_child: '親子友善',
  available_24h: '全天可取用', floor: '設置樓層',
  indoor: '室內', outdoor: '室外', air_conditioning: '冷氣', restroom: '廁所', seats: '座位',
  station_type: '設施類型', capacity: '預計容納人數', disaster_types: '適用災害',
  vulnerable_friendly: '適合避難弱者', service_villages: '服務村里',
}

export function DetailDrawer({ place, favorite, onClose, onToggleFavorite, dataVersion }: Props) {
  const properties = Object.entries(place.properties).filter(([key, value]) => labels[key] && value != null)
  return (
    <aside className="detail-drawer" aria-label={`${place.name}詳細資訊`}>
      <div className="detail-actions">
        <span className={`detail-category ${place.category}`}>{place.category === 'parking' ? 'P' : place.category === 'aed' ? 'AED' : place.category === 'toilet' ? 'WC' : place.category === 'drinking_water' ? '水' : '安'}</span>
        <div>
          <button className={`favorite-button ${favorite ? 'active' : ''}`} onClick={onToggleFavorite} aria-label={favorite ? '取消收藏' : '加入收藏'}>{favorite ? '★' : '☆'}</button>
          <button className="drawer-close" onClick={onClose} aria-label="關閉詳細資訊">×</button>
        </div>
      </div>
      <p className="eyebrow">{place.category === 'parking' ? '路外停車場' : place.category === 'aed' ? 'AED' : place.category === 'toilet' ? '公共廁所' : place.category === 'drinking_water' ? '公共飲水機' : '避難收容處所'}</p>
      <h2>{place.name}</h2>
      <p className="detail-address">{place.address ?? '地址未提供'}</p>
      {place.phone && <a href={`tel:${place.phone}`} className="detail-phone">{place.phone}</a>}
      {place.latitude != null && place.longitude != null && <div className="navigation-actions" aria-label="導航方式">
        <a href={navigationUrl(place, 'walking')} target="_blank" rel="noreferrer">步行</a>
        <a href={navigationUrl(place, 'bicycling')} target="_blank" rel="noreferrer">騎車</a>
        <a href={navigationUrl(place, 'driving')} target="_blank" rel="noreferrer">開車</a>
      </div>}
      <dl className="detail-grid">
        {properties.map(([key, value]) => <div key={key}><dt>{labels[key]}</dt><dd>{typeof value === 'boolean' ? (value ? '有' : '未標示') : String(value)}</dd></div>)}
      </dl>
      <p className="detail-source">資料來源：{sourceLabel(place)}。資料版本：{formatVersion(dataVersion)}。</p>
      <a className="report-link" href={`mailto:?subject=${encodeURIComponent(`生活機能探索地圖資料回報：${place.name}`)}&body=${encodeURIComponent(`設施：${place.name}\n地址：${place.address ?? '未提供'}\n問題說明：`)}`}>回報資訊錯誤</a>
    </aside>
  )
}

function sourceLabel(place: Place) {
  if (place.category === 'parking') return '地方政府／交通部 TDX'
  if (place.category === 'aed') return '衛生福利部全國 AED 開放資料'
  if (place.category === 'toilet') return '環境部全國公廁資料'
  if (place.category === 'drinking_water') return '環境部 Cool map 涼適點'
  if (place.category === 'shelter') return '內政部消防署避難收容處所資料'
  return '政府開放資料'
}

function navigationUrl(place: Place, mode: 'walking' | 'bicycling' | 'driving') {
  return `https://www.google.com/maps/dir/?api=1&destination=${place.latitude},${place.longitude}&travelmode=${mode}`
}

function formatVersion(value: string) {
  if (!value || value === 'empty') return '未提供'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('zh-TW', { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}
