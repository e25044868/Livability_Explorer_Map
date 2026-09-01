import { useEffect, useMemo, useState } from 'react'
import L from 'leaflet'
import { Circle, MapContainer, Marker, Popup, TileLayer, useMap, useMapEvents } from 'react-leaflet'
import { SearchAreaIcon } from './Icons'
import type { Coordinates, Place, QueryMode, ViewportBounds } from '../types'
import { useI18n } from '../i18n'

type Props = {
  center: Coordinates
  radius: number
  queryMode: QueryMode
  places: Place[]
  selectedPlace: Place | null
  loading: boolean
  showSearchArea: boolean
  onBoundsChange: (bounds: ViewportBounds) => void
  onSearchArea: () => void
  onSelect: (place: Place) => void
  onSetCenter: (center: Coordinates) => void
}

const parkingIcon = L.divIcon({
  className: 'parking-marker-wrap',
  html: '<span class="parking-marker"><b>P</b></span>',
  iconSize: [34, 42],
  iconAnchor: [17, 40],
  popupAnchor: [0, -38],
})

const evParkingIcon = L.divIcon({ className: 'parking-marker-wrap ev', html: '<span class="parking-marker"><b>⚡</b></span>', iconSize: [34, 42], iconAnchor: [17, 40], popupAnchor: [0, -38] })

const selectedParkingIcon = L.divIcon({
  className: 'parking-marker-wrap selected',
  html: '<span class="parking-marker"><b>P</b></span>',
  iconSize: [40, 48],
  iconAnchor: [20, 46],
  popupAnchor: [0, -44],
})

const toiletIcon = L.divIcon({ className: 'facility-marker-wrap toilet', html: '<span>WC</span>', iconSize: [34, 34], iconAnchor: [17, 17], popupAnchor: [0, -18] })
const aedIcon = L.divIcon({ className: 'facility-marker-wrap aed', html: '<span>AED</span>', iconSize: [36, 36], iconAnchor: [18, 18], popupAnchor: [0, -20] })
const waterIcon = L.divIcon({ className: 'facility-marker-wrap water', html: '<span>水</span>', iconSize: [36, 36], iconAnchor: [18, 18], popupAnchor: [0, -20] })
const shelterIcon = L.divIcon({ className: 'facility-marker-wrap shelter', html: '<span>安</span>', iconSize: [36, 36], iconAnchor: [18, 18], popupAnchor: [0, -20] })
const wifiIcon = L.divIcon({ className: 'facility-marker-wrap wifi', html: '<span>WiFi</span>', iconSize: [40, 36], iconAnchor: [20, 18], popupAnchor: [0, -20] })
const rescueIcon = L.divIcon({ className: 'facility-marker-wrap rescue', html: '<span>119</span>', iconSize: [38, 36], iconAnchor: [19, 18], popupAnchor: [0, -20] })
const policeIcon = L.divIcon({ className: 'facility-marker-wrap police', html: '<span>警</span>', iconSize: [36, 36], iconAnchor: [18, 18], popupAnchor: [0, -20] })
const libraryIcon = L.divIcon({ className: 'facility-marker-wrap library', html: '<span>書</span>', iconSize: [36, 36], iconAnchor: [18, 18], popupAnchor: [0, -20] })
const publicBicycleIcon = L.divIcon({ className: 'facility-marker-wrap public-bicycle', html: '<span>車</span>', iconSize: [36, 36], iconAnchor: [18, 18], popupAnchor: [0, -20] })
const tourismFacilityIcon = L.divIcon({ className: 'facility-marker-wrap tourism-facility', html: '<span>景</span>', iconSize: [36, 36], iconAnchor: [18, 18], popupAnchor: [0, -20] })
const centerIcon = L.divIcon({ className: 'analysis-center-marker', html: '<span></span>', iconSize: [26, 26], iconAnchor: [13, 13] })

function clusterIcon(count: number) {
  return L.divIcon({ className: 'cluster-marker', html: `<span>${count}</span>`, iconSize: [42, 42], iconAnchor: [21, 21] })
}

export function MapView(props: Props) {
  const { t, categoryLabel } = useI18n()
  const [zoom, setZoom] = useState(14)
  const mappablePlaces = useMemo(
    () => props.places.filter((place) => place.latitude != null && place.longitude != null),
    [props.places],
  )
  const clusters = useMemo(() => clusterPlaces(mappablePlaces, zoom), [mappablePlaces, zoom])

  return (
    <div className="map-shell">
      <MapContainer center={[props.center.lat, props.center.lng]} zoom={14} zoomControl={false} className="map-container">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapEvents onBoundsChange={props.onBoundsChange} onSetCenter={props.onSetCenter} onZoom={setZoom} />
        <MapController center={props.center} selectedPlace={props.selectedPlace} queryMode={props.queryMode} places={mappablePlaces} />
        {props.queryMode === 'radius' && (
          <Circle center={[props.center.lat, props.center.lng]} radius={props.radius} pathOptions={{ color: '#156d62', weight: 1.5, fillColor: '#39a99a', fillOpacity: 0.08 }} />
        )}
        <Marker position={[props.center.lat, props.center.lng]} icon={centerIcon} interactive={false} zIndexOffset={1000} />
        {clusters.map((cluster) => cluster.places.length > 1 ? (
          <Cluster key={cluster.key} places={cluster.places} position={cluster.position} />
        ) : (
          <Marker
            key={cluster.places[0].public_id}
            position={cluster.position}
            icon={placeIcon(cluster.places[0], props.selectedPlace?.public_id === cluster.places[0].public_id)}
            eventHandlers={{ click: () => props.onSelect(cluster.places[0]) }}
          >
            <Popup>
              <div className="map-popup">
                <span className="popup-label">{categoryLabel(cluster.places[0].category)}</span>
                <strong>{cluster.places[0].name}</strong>
                <span>{cluster.places[0].address ?? t('addressUnavailable')}</span>
                <div>
                  {cluster.places[0].properties.car_spaces != null && <small>{t('carSpaces')} {cluster.places[0].properties.car_spaces}</small>}
                  {cluster.places[0].properties.toilet_type && <small>{cluster.places[0].properties.toilet_type}</small>}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {props.showSearchArea && (
        <button className="search-area-button" onClick={props.onSearchArea} disabled={props.loading}>
          <SearchAreaIcon size={18} />
          {props.loading ? t('searching') : t('searchThisArea')}
        </button>
      )}
      <div className="map-result-badge"><strong>{props.places.length}</strong> {t('facilities')}</div>
    </div>
  )
}

function MapEvents({ onBoundsChange, onSetCenter, onZoom }: { onBoundsChange: (bounds: ViewportBounds) => void; onSetCenter: (center: Coordinates) => void; onZoom: (zoom: number) => void }) {
  const map = useMapEvents({
    moveend: () => {
      const bounds = map.getBounds()
      onBoundsChange({ north: bounds.getNorth(), south: bounds.getSouth(), east: bounds.getEast(), west: bounds.getWest() })
    },
    zoomend: () => onZoom(map.getZoom()),
    click: (event) => onSetCenter({ lat: event.latlng.lat, lng: event.latlng.lng }),
  })
  useEffect(() => {
    const bounds = map.getBounds()
    onBoundsChange({ north: bounds.getNorth(), south: bounds.getSouth(), east: bounds.getEast(), west: bounds.getWest() })
  }, [map, onBoundsChange])
  return null
}

function Cluster({ places, position }: { places: Place[]; position: [number, number] }) {
  const map = useMap()
  return <Marker position={position} icon={clusterIcon(places.length)} eventHandlers={{ click: () => map.fitBounds(L.latLngBounds(places.map((place) => [place.latitude!, place.longitude!] as [number, number])), { padding: [50, 50], maxZoom: 17 }) }} />
}

function clusterPlaces(places: Place[], zoom: number) {
  const cell = zoom >= 17 ? 0 : zoom >= 15 ? 0.0025 : zoom >= 13 ? 0.008 : 0.02
  const groups = new Map<string, Place[]>()
  for (const place of places) {
    const key = cell === 0 ? place.public_id : `${Math.round(place.latitude! / cell)}:${Math.round(place.longitude! / cell)}`
    groups.set(key, [...(groups.get(key) ?? []), place])
  }
  return [...groups.entries()].map(([key, members]) => ({
    key,
    places: members,
    position: [members.reduce((sum, place) => sum + place.latitude!, 0) / members.length, members.reduce((sum, place) => sum + place.longitude!, 0) / members.length] as [number, number],
  }))
}

function MapController({ center, selectedPlace, queryMode, places }: { center: Coordinates; selectedPlace: Place | null; queryMode: QueryMode; places: Place[] }) {
  const map = useMap()
  useEffect(() => {
    map.flyTo([center.lat, center.lng], Math.max(map.getZoom(), 14), { duration: 0.8 })
  }, [center, map])
  useEffect(() => {
    if (selectedPlace?.latitude != null && selectedPlace.longitude != null) {
      map.flyTo([selectedPlace.latitude, selectedPlace.longitude], Math.max(map.getZoom(), 16), { duration: 0.6 })
    }
  }, [map, selectedPlace])
  useEffect(() => {
    if (queryMode === 'city' && places.length) {
      map.fitBounds(L.latLngBounds(places.map((place) => [place.latitude!, place.longitude!] as [number, number])), { padding: [30, 30] })
    }
  }, [map, places, queryMode])
  return null
}

function placeIcon(place: Place, selected: boolean) {
  if (place.category === 'toilet') return toiletIcon
  if (place.category === 'aed') return aedIcon
  if (place.category === 'drinking_water') return waterIcon
  if (place.category === 'shelter') return shelterIcon
  if (place.category === 'public_wifi') return wifiIcon
  if (place.category === 'rescue_unit') return rescueIcon
  if (place.category === 'police') return policeIcon
  if (place.category === 'library') return libraryIcon
  if (place.category === 'public_bicycle') return publicBicycleIcon
  if (place.category === 'tourism_facility') return tourismFacilityIcon
  if ((place.properties.ev_spaces ?? 0) > 0) return evParkingIcon
  return selected ? selectedParkingIcon : parkingIcon
}
