import { ChevronIcon, ParkingIcon } from './Icons'
import type { Place } from '../types'
import { useI18n } from '../i18n'

type Props = {
  places: Place[]
  selectedId: string | null
  loading: boolean
  error: string | null
  onSelect: (place: Place) => void
  favoriteIds: Set<string>
}

export function PlaceList({ places, selectedId, loading, error, onSelect, favoriteIds }: Props) {
  const { t, language } = useI18n()
  if (loading) {
    return <div className="place-list-state"><span className="loader" />{t('loadingPlaces')}</div>
  }
  if (error) {
    return <div className="place-list-state error"><strong>{t('unableToLoad')}</strong><span>{error}</span></div>
  }
  if (!places.length) {
    return <div className="place-list-state"><ParkingIcon size={34}/><strong>{t('noPlaces')}</strong><span>{t('tryMoveMap')}</span></div>
  }

  return (
    <div className="place-list" aria-live="polite">
      {places.map((place, index) => (
        <button
          className={`place-card ${selectedId === place.public_id ? 'selected' : ''}`}
          key={place.public_id}
          onClick={() => onSelect(place)}
        >
          <span className={`place-rank ${place.category}`}>{place.category === 'parking' ? String(index + 1).padStart(2, '0') : place.category === 'aed' ? 'AED' : place.category === 'toilet' ? 'WC' : place.category === 'drinking_water' ? '水' : place.category === 'public_wifi' ? 'WiFi' : place.category === 'rescue_unit' ? '119' : place.category === 'police' ? '警' : '安'}</span>
          <span className="place-card-main">
            <span className="place-title-row">
              <strong>{favoriteIds.has(place.public_id) ? '★ ' : ''}{place.name}</strong>
              {place.distance_meters != null && <em>{formatDistance(place.distance_meters, language)}</em>}
            </span>
            <span className="place-address">{place.address ?? t('addressUnavailable')}</span>
            <span className="place-tags">
              {place.properties.car_spaces != null && <small>{t('carSpaces')} {place.properties.car_spaces}</small>}
              {place.properties.available_spaces != null && <small>{t('availability')} {place.properties.available_spaces}</small>}
              {(place.properties.ev_spaces ?? 0) > 0 && <small>⚡ {t('evCharging')} {place.properties.ev_spaces}</small>}
              {place.properties.motorcycle_spaces != null && <small>{t('motorcycleSpaces')} {place.properties.motorcycle_spaces}</small>}
              {place.properties.facility_type && <small>{place.properties.facility_type}</small>}
              {place.properties.toilet_type && <small>{place.properties.toilet_type}</small>}
              {place.properties.capacity != null && <small>{place.properties.capacity} {t('placesUnit')}</small>}
              {place.properties.opening_hours && <small>{place.properties.opening_hours}</small>}
            </span>
          </span>
          <ChevronIcon className="card-chevron" />
        </button>
      ))}
    </div>
  )
}

function formatDistance(meters: number, language: string) {
  return meters < 1000 ? `${Math.round(meters).toLocaleString(language)} m` : `${(meters / 1000).toLocaleString(language, { maximumFractionDigits: 1 })} km`
}
