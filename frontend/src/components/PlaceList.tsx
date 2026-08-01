import { ChevronIcon, ParkingIcon } from './Icons'
import type { Place } from '../types'

type Props = {
  places: Place[]
  selectedId: string | null
  loading: boolean
  error: string | null
  onSelect: (place: Place) => void
  favoriteIds: Set<string>
}

export function PlaceList({ places, selectedId, loading, error, onSelect, favoriteIds }: Props) {
  if (loading) {
    return <div className="place-list-state"><span className="loader" />正在查詢停車場…</div>
  }
  if (error) {
    return <div className="place-list-state error"><strong>無法取得資料</strong><span>{error}</span></div>
  }
  if (!places.length) {
    return <div className="place-list-state"><ParkingIcon size={34}/><strong>這個範圍目前沒有停車場</strong><span>移動地圖或放大搜尋半徑再試一次。</span></div>
  }

  return (
    <div className="place-list" aria-live="polite">
      {places.map((place, index) => (
        <button
          className={`place-card ${selectedId === place.public_id ? 'selected' : ''}`}
          key={place.public_id}
          onClick={() => onSelect(place)}
        >
          <span className={`place-rank ${place.category}`}>{place.category === 'parking' ? String(index + 1).padStart(2, '0') : place.category === 'aed' ? 'AED' : place.category === 'toilet' ? 'WC' : place.category === 'drinking_water' ? '水' : '安'}</span>
          <span className="place-card-main">
            <span className="place-title-row">
              <strong>{favoriteIds.has(place.public_id) ? '★ ' : ''}{place.name}</strong>
              {place.distance_meters != null && <em>{formatDistance(place.distance_meters)}</em>}
            </span>
            <span className="place-address">{place.address ?? '地址未提供'}</span>
            <span className="place-tags">
              {place.properties.car_spaces != null && <small>汽車 {place.properties.car_spaces} 格</small>}
              {place.properties.available_spaces != null && <small>剩餘 {place.properties.available_spaces} 格</small>}
              {(place.properties.ev_spaces ?? 0) > 0 && <small>⚡ 充電 {place.properties.ev_spaces} 格</small>}
              {place.properties.motorcycle_spaces != null && <small>機車 {place.properties.motorcycle_spaces} 格</small>}
              {place.properties.facility_type && <small>{place.properties.facility_type}</small>}
              {place.properties.toilet_type && <small>{place.properties.toilet_type}</small>}
              {place.properties.capacity != null && <small>容納 {place.properties.capacity} 人</small>}
              {place.properties.opening_hours && <small>{place.properties.opening_hours}</small>}
            </span>
          </span>
          <ChevronIcon className="card-chevron" />
        </button>
      ))}
    </div>
  )
}

function formatDistance(meters: number) {
  return meters < 1000 ? `${Math.round(meters)} m` : `${(meters / 1000).toFixed(1)} km`
}
