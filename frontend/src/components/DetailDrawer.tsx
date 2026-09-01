import type { Place } from '../types'
import { interpolate, useI18n } from '../i18n'

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
  vulnerable_friendly: '適合避難弱者', service_villages: '服務村里', agency: '提供機關', venue_type: '場所類型', co_located_with_fire_station: '與消防隊同址', english_name: '英文單位名稱', unit_type: '機關類型', facility_subtype: '設施子類別', management_office: '管理處', facility_status: '設施狀態', facility_description: '設施說明', landscape_area: '景觀分區',
}

const englishLabels: Record<string, string> = {
  facility_type: 'Facility type', fee_description: 'Fee details', car_spaces: 'Car spaces', motorcycle_spaces: 'Motorcycle spaces', large_vehicle_spaces: 'Large-vehicle spaces', operator: 'Operator', contract_period_raw: 'Contract period', toilet_type: 'Restroom type', accessible: 'Accessible', grade: 'Restroom grade', facility_category: 'Facility category', administration: 'Administration', diaper: 'Diaper-changing station', location_description: 'AED location', available_hours: 'Hours', place_category: 'Place category', total_spaces: 'Total spaces', available_spaces: 'Available spaces', operation_time: 'Operating hours', ev_spaces: 'EV spaces', accessible_spaces: 'Accessible spaces', parent_child_spaces: 'Family spaces', height_limit: 'Height limit', monthly_pass: 'Monthly pass', live_updated_at: 'Live update', opening_hours: 'Opening hours', gender_friendly: 'Gender friendly', parent_child: 'Family friendly', available_24h: 'Available 24 hours', floor: 'Floor', indoor: 'Indoor', outdoor: 'Outdoor', air_conditioning: 'Air conditioning', restroom: 'Restroom', seats: 'Seats', station_type: 'Facility type', capacity: 'Capacity', disaster_types: 'Disaster types', vulnerable_friendly: 'Vulnerable-person friendly', service_villages: 'Service villages', agency: 'Providing agency', venue_type: 'Venue type', co_located_with_fire_station: 'Co-located with fire station', english_name: 'English unit name', unit_type: 'Unit type', facility_subtype: 'Facility subtype', management_office: 'Management office', facility_status: 'Facility status', facility_description: 'Facility description', landscape_area: 'Landscape area',
}

export function DetailDrawer({ place, favorite, onClose, onToggleFavorite, dataVersion }: Props) {
  const { language, t, categoryLabel } = useI18n()
  const properties = Object.entries(place.properties).filter(([key, value]) => labels[key] && value != null)
  return (
    <aside className="detail-drawer" aria-label={interpolate(t('details'), { name: place.name })}>
      <div className="detail-actions">
        <span className={`detail-category ${place.category}`}>{place.category === 'parking' ? 'P' : place.category === 'aed' ? 'AED' : place.category === 'toilet' ? 'WC' : place.category === 'drinking_water' ? '水' : place.category === 'public_wifi' ? 'WiFi' : place.category === 'rescue_unit' ? '119' : place.category === 'police' ? '警' : place.category === 'library' ? '書' : place.category === 'public_bicycle' ? '車' : place.category === 'tourism_facility' ? '景' : '安'}</span>
        <div>
          <button className={`favorite-button ${favorite ? 'active' : ''}`} onClick={onToggleFavorite} aria-label={favorite ? t('removeFavorite') : t('addFavorite')}>{favorite ? '★' : '☆'}</button>
          <button className="drawer-close" onClick={onClose} aria-label={t('closeDetails')}>×</button>
        </div>
      </div>
      <p className="eyebrow">{categoryLabel(place.category)}</p>
      <h2>{place.name}</h2>
      <p className="detail-address">{place.address ?? t('addressUnavailable')}</p>
      {place.phone && <a href={`tel:${place.phone}`} className="detail-phone">{place.phone}</a>}
      {place.latitude != null && place.longitude != null && <div className="navigation-actions" aria-label={t('navigation')}>
        <a href={navigationUrl(place, 'walking')} target="_blank" rel="noreferrer">{t('walking')}</a>
        <a href={navigationUrl(place, 'bicycling')} target="_blank" rel="noreferrer">{t('cycling')}</a>
        <a href={navigationUrl(place, 'driving')} target="_blank" rel="noreferrer">{t('driving')}</a>
      </div>}
      <dl className="detail-grid">
        {properties.map(([key, value]) => <div key={key}><dt>{language === 'en' ? englishLabels[key] : labels[key]}</dt><dd>{typeof value === 'boolean' ? (value ? t('yes') : t('notSpecified')) : String(value)}</dd></div>)}
      </dl>
      <p className="detail-source">{interpolate(t('source'), { source: sourceLabel(place, t), version: formatVersion(dataVersion, language) })}</p>
      <a className="report-link" href={`mailto:?subject=${encodeURIComponent(`${t('appName')}：${place.name}`)}&body=${encodeURIComponent(`${place.name}\n${place.address ?? t('addressUnavailable')}\n`)}`}>{t('reportError')}</a>
    </aside>
  )
}

function sourceLabel(place: Place, t: (key: never) => string) {
  if (place.category === 'parking') return t('localGovernment' as never)
  if (place.category === 'aed') return t('nationalAed' as never)
  if (place.category === 'toilet') return t('nationalToilet' as never)
  if (place.category === 'drinking_water') return t('coolMap' as never)
  if (place.category === 'shelter') return t('nationalShelter' as never)
  if (place.category === 'public_wifi') return t('nationalWifi' as never)
  if (place.category === 'rescue_unit') return t('nationalRescue' as never)
  if (place.category === 'police') return t('nationalPolice' as never)
  if (place.category === 'library') return t('nationalLibrary' as never)
  if (place.category === 'public_bicycle') return t('nationalPublicBicycle' as never)
  if (place.category === 'tourism_facility') return t('nationalTourismFacility' as never)
  return t('governmentData' as never)
}

function navigationUrl(place: Place, mode: 'walking' | 'bicycling' | 'driving') {
  return `https://www.google.com/maps/dir/?api=1&destination=${place.latitude},${place.longitude}&travelmode=${mode}`
}

function formatVersion(value: string, language: string) {
  if (!value || value === 'empty') return language === 'en' ? 'Not provided' : '未提供'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat(language, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}
