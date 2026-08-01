import { useCallback, useEffect, useMemo, useState } from 'react'
import { detectAdministrativeArea, fetchPlacesByCity, fetchPlacesByRadius, fetchPlacesByViewport } from './api'
import { AnalysisPanel } from './components/AnalysisPanel'
import { DetailDrawer } from './components/DetailDrawer'
import { CITY_CENTERS, CitySelector } from './components/CitySelector'
import { FilterBar } from './components/FilterBar'
import { ListIcon, MapPinIcon, MoonIcon, SunIcon } from './components/Icons'
import { MapView } from './components/MapView'
import { PlaceList } from './components/PlaceList'
import { SearchBar } from './components/SearchBar'
import { createI18n, I18nProvider, interpolate, type Language } from './i18n'
import type { CategoryKey, Coordinates, Place, PlaceFilters, QueryMode, SortMode, ViewMode, ViewportBounds } from './types'

const INITIAL_CENTER: Coordinates = { lat: 22.6273, lng: 120.3014 }
const DEFAULT_FILTERS: PlaceFilters = { minCarSpaces: 0, minMotorcycleSpaces: 0, accessibleOnly: false, favoritesOnly: false, open24hOnly: false, evOnly: false, parentChildOnly: false, recentOnly: false }
type Theme = 'light' | 'dark'

function sharedState() {
  const params = new URLSearchParams(window.location.search)
  const latValue = params.get('lat'); const lngValue = params.get('lng'); const radiusValue = params.get('radius')
  const lat = latValue == null ? Number.NaN : Number(latValue)
  const lng = lngValue == null ? Number.NaN : Number(lngValue)
  const radius = radiusValue == null ? Number.NaN : Number(radiusValue)
  const validTaiwanCenter = Number.isFinite(lat) && Number.isFinite(lng) && lat >= 20 && lat <= 27 && lng >= 118 && lng <= 123
  const categories = (params.get('categories') ?? '').split(',').filter((value): value is CategoryKey => ['parking', 'toilet', 'aed', 'pharmacy', 'medical', 'motorcycle_charging', 'drinking_water', 'shelter'].includes(value))
  return {
    center: validTaiwanCenter ? { lat, lng } : INITIAL_CENTER,
    radius: Number.isInteger(radius) && radius >= 500 && radius <= 3000 && radius % 100 === 0 ? radius : 1000,
    categories: categories.length ? categories : ['parking', 'toilet', 'aed', 'drinking_water', 'shelter'] as CategoryKey[],
    city: params.get('city'),
  }
}

function getInitialTheme(): Theme {
  const stored = localStorage.getItem('livability-map-theme')
  if (stored === 'light' || stored === 'dark') return stored
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function getInitialLanguage(): Language {
  return localStorage.getItem('livability-map-language') === 'en' ? 'en' : 'zh-TW'
}

function getFavorites() {
  try { return new Set<string>(JSON.parse(localStorage.getItem('livability-map-favorites') ?? '[]')) }
  catch { return new Set<string>() }
}

function getRecentIds() {
  try { return JSON.parse(localStorage.getItem('livability-map-recents') ?? '[]') as string[] }
  catch { return [] }
}

export default function App() {
  const initial = useMemo(sharedState, [])
  const [center, setCenter] = useState(initial.center)
  const [radius, setRadius] = useState(initial.radius)
  const [places, setPlaces] = useState<Place[]>([])
  const [activeCategories, setActiveCategories] = useState<CategoryKey[]>(initial.categories)
  const [cityFilter, setCityFilter] = useState<string | null>(initial.city)
  const [detectedCity, setDetectedCity] = useState<string | null>('高雄市')
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [favoriteIds, setFavoriteIds] = useState<Set<string>>(getFavorites)
  const [recentIds, setRecentIds] = useState<string[]>(getRecentIds)
  const [sortMode, setSortMode] = useState<SortMode>('distance')
  const [dataVersion, setDataVersion] = useState('empty')
  const [queryMode, setQueryMode] = useState<QueryMode>('radius')
  const [viewMode, setViewMode] = useState<ViewMode>('map')
  const [bounds, setBounds] = useState<ViewportBounds | null>(null)
  const [showSearchArea, setShowSearchArea] = useState(false)
  const [selectedPlace, setSelectedPlace] = useState<Place | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [theme, setTheme] = useState<Theme>(getInitialTheme)
  const [language, setLanguage] = useState<Language>(getInitialLanguage)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.documentElement.style.colorScheme = theme
    localStorage.setItem('livability-map-theme', theme)
  }, [theme])
  useEffect(() => {
    document.documentElement.lang = language
    localStorage.setItem('livability-map-language', language)
  }, [language])

  const runRadiusQuery = useCallback(async (nextCenter: Coordinates, nextRadius: number, categories: CategoryKey[], signal?: AbortSignal) => {
    setLoading(true); setError(null)
    try {
      const response = await fetchPlacesByRadius(nextCenter, nextRadius, categories, signal)
      setPlaces(response.items); setDataVersion(response.data_version); setQueryMode('radius'); setShowSearchArea(false)
      const city = mostCommonCity(response.items)
      if (city) setDetectedCity(city)
    } catch (reason) {
      if ((reason as Error).name !== 'AbortError') setError((reason as Error).message)
    } finally { if (!signal?.aborted) setLoading(false) }
  }, [])

  const runCityQuery = useCallback(async (city: string, categories: CategoryKey[], signal?: AbortSignal) => {
    setLoading(true); setError(null)
    try {
      const response = await fetchPlacesByCity(city, categories, signal)
      setPlaces(response.items); setDataVersion(response.data_version); setQueryMode('city'); setShowSearchArea(false)
    } catch (reason) {
      if ((reason as Error).name !== 'AbortError') setError((reason as Error).message)
    } finally { if (!signal?.aborted) setLoading(false) }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    if (cityFilter) void runCityQuery(cityFilter, activeCategories, controller.signal)
    else void runRadiusQuery(center, radius, activeCategories, controller.signal)
    return () => controller.abort()
  }, [center, radius, activeCategories, cityFilter, runCityQuery, runRadiusQuery])

  const filteredPlaces = useMemo(() => places.filter((place) => {
    if (filters.favoritesOnly && !favoriteIds.has(place.public_id)) return false
    if (filters.recentOnly && !recentIds.includes(place.public_id)) return false
    if (filters.accessibleOnly && place.properties.accessible !== true) return false
    if (filters.open24hOnly && place.properties.available_24h !== true && !String(place.properties.operation_time ?? place.properties.opening_hours ?? '').match(/24\s*(小時|H)/i)) return false
    if (filters.evOnly && (place.properties.ev_spaces ?? 0) < 1) return false
    if (filters.parentChildOnly && place.properties.parent_child !== true && (place.properties.parent_child_spaces ?? 0) < 1 && place.properties.diaper !== true) return false
    if ((place.properties.car_spaces ?? 0) < filters.minCarSpaces) return false
    if ((place.properties.motorcycle_spaces ?? 0) < filters.minMotorcycleSpaces) return false
    return true
  }).sort((a, b) => {
    if (sortMode === 'name') return a.name.localeCompare(b.name, 'zh-TW')
    if (sortMode === 'availability') return (b.properties.available_spaces ?? -1) - (a.properties.available_spaces ?? -1)
    return placeDistance(a, center) - placeDistance(b, center)
  }), [center, favoriteIds, filters, places, recentIds, sortMode])

  const intersectionCount = useMemo(() => {
    const toilets = places.filter((place) => place.category === 'toilet' && place.latitude != null && place.longitude != null)
    return places.filter((parking) => parking.category === 'parking' && parking.latitude != null && parking.longitude != null && toilets.some((toilet) => distanceMeters(parking, toilet) <= 300)).length
  }, [places])

  const handleBoundsChange = useCallback((nextBounds: ViewportBounds) => { setBounds(nextBounds); setShowSearchArea(true) }, [])

  async function handleSearchArea() {
    if (!bounds) return
    setLoading(true); setError(null)
    try {
      const response = await fetchPlacesByViewport(bounds, activeCategories)
      setPlaces(response.items); setDataVersion(response.data_version); setQueryMode('viewport'); setShowSearchArea(false); setSelectedPlace(null)
    } catch (reason) { setError((reason as Error).message) }
    finally { setLoading(false) }
  }

  function handleSetCenter(nextCenter: Coordinates) {
    setCityFilter(null); setCenter(nextCenter); setQueryMode('radius'); setSelectedPlace(null)
    void detectAdministrativeArea(nextCenter).then(({ city }) => setDetectedCity(city)).catch(() => undefined)
  }

  function handleSearchSelect(place: Place) {
    if (place.latitude == null || place.longitude == null) return
    setCityFilter(null); setCenter({ lat: place.latitude, lng: place.longitude }); setSelectedPlace(place); setQueryMode('radius')
  }

  function handleToggleCategory(category: CategoryKey) {
    setActiveCategories((current) => current.includes(category) ? (current.length > 1 ? current.filter((key) => key !== category) : current) : [...current, category])
  }

  function handleLocate() {
    if (!navigator.geolocation) { setError(t('locationUnsupported')); return }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => handleSetCenter({ lat: coords.latitude, lng: coords.longitude }),
      () => setError(t('locationUnavailable')),
      { enableHighAccuracy: true, timeout: 8000 },
    )
  }

  function handleCityChange(city: string) {
    setCityFilter(city); setDetectedCity(city); setCenter(CITY_CENTERS[city]); setSelectedPlace(null)
  }

  function toggleFavorite(publicId: string) {
    setFavoriteIds((current) => {
      const next = new Set(current)
      if (next.has(publicId)) next.delete(publicId); else next.add(publicId)
      localStorage.setItem('livability-map-favorites', JSON.stringify([...next]))
      return next
    })
  }

  function selectPlace(place: Place | null) {
    setSelectedPlace(place)
    if (!place || place.public_id.startsWith('geocode-')) return
    setRecentIds((current) => {
      const next = [place.public_id, ...current.filter((id) => id !== place.public_id)].slice(0, 12)
      localStorage.setItem('livability-map-recents', JSON.stringify(next))
      return next
    })
  }

  async function shareMap() {
    const url = new URL(window.location.href)
    url.search = new URLSearchParams({ lat: center.lat.toFixed(6), lng: center.lng.toFixed(6), radius: String(radius), categories: activeCategories.join(','), ...(cityFilter ? { city: cityFilter } : {}) }).toString()
    const payload = { title: t('shareTitle'), text: t('shareText'), url: url.toString() }
    if (navigator.share) await navigator.share(payload).catch(() => undefined)
    else await navigator.clipboard.writeText(payload.url).then(() => setError(t('linkCopied'))).catch(() => setError(t('copyFailed')))
  }

  const i18n = createI18n(language, setLanguage)
  const { t, cityLabel } = i18n

  return (
    <I18nProvider value={i18n}>
    <main className="app-shell">
      <header className="topbar">
        <div className="brand"><span className="brand-mark"><MapPinIcon size={21} /></span><div><strong>{t('appName')}</strong><span>KAOHSIUNG LIVABILITY ATLAS</span></div></div>
        <SearchBar onSelect={handleSearchSelect} />
        <div className="topbar-actions">
          <CitySelector value={cityFilter ?? detectedCity ?? '高雄市'} detectedCity={cityFilter ? null : detectedCity} onChange={handleCityChange} />
          <button className="share-button" onClick={() => void shareMap()} aria-label={t('share')}>{t('share')}</button>
          <nav className="view-switch" aria-label={t('map')}>
            <button className={viewMode === 'map' ? 'active' : ''} onClick={() => setViewMode('map')}><MapPinIcon size={17}/>{t('map')}</button>
            <button className={viewMode === 'list' ? 'active' : ''} onClick={() => setViewMode('list')}><ListIcon size={17}/>{t('list')}</button>
          </nav>
          <button className="language-toggle" onClick={() => setLanguage((current) => current === 'zh-TW' ? 'en' : 'zh-TW')} aria-label={language === 'zh-TW' ? 'Switch to English' : '切換為中文'}>{language === 'zh-TW' ? 'EN' : '中文'}</button>
          <button className="theme-toggle" onClick={() => setTheme((current) => current === 'light' ? 'dark' : 'light')} aria-label={interpolate(t('switchTheme'), { theme: theme === 'light' ? t('darkTheme') : t('lightTheme') })}>{theme === 'light' ? <MoonIcon /> : <SunIcon />}</button>
        </div>
      </header>

      <div className="workspace">
        <AnalysisPanel center={center} radius={radius} queryMode={queryMode} places={places} loading={loading} dataVersion={dataVersion} onRadiusChange={(value) => { setRadius(value); setQueryMode('radius') }} onLocate={handleLocate} activeCategories={activeCategories} onToggleCategory={handleToggleCategory} />
        <section className={`results-area ${viewMode}`}>
          <div className="results-heading"><div><p className="eyebrow">{t('resultsHint')}</p><h1>{queryMode === 'radius' ? interpolate(t('withinRadius'), { radius: formatRadius(radius, language) }) : queryMode === 'city' ? interpolate(t('cityData'), { city: cityLabel(cityFilter) }) : t('currentMapArea')}</h1></div><span>{loading ? t('updating') : `${filteredPlaces.length} ${t('matchingResults')}`}</span></div>
          <FilterBar filters={filters} onChange={setFilters} sortMode={sortMode} onSortChange={setSortMode} intersectionReady={activeCategories.includes('parking') && activeCategories.includes('toilet')} intersectionCount={intersectionCount} />
          <div className="map-view"><MapView center={center} radius={radius} queryMode={queryMode} places={filteredPlaces} selectedPlace={selectedPlace} loading={loading} showSearchArea={showSearchArea} onBoundsChange={handleBoundsChange} onSearchArea={handleSearchArea} onSelect={selectPlace} onSetCenter={handleSetCenter} /></div>
          <div className="list-view"><PlaceList places={filteredPlaces} selectedId={selectedPlace?.public_id ?? null} loading={loading} error={error} onSelect={(place) => { selectPlace(place); if (window.innerWidth < 760) setViewMode('map') }} favoriteIds={favoriteIds} /></div>
          {selectedPlace && <DetailDrawer place={selectedPlace} favorite={favoriteIds.has(selectedPlace.public_id)} dataVersion={dataVersion} onClose={() => setSelectedPlace(null)} onToggleFavorite={() => toggleFavorite(selectedPlace.public_id)} />}
          {error && viewMode === 'map' && <div className="map-error">{error}</div>}
        </section>
      </div>
    </main>
    </I18nProvider>
  )
}

function formatRadius(radius: number, language: Language) {
  if (language === 'en') return radius < 1000 ? `${radius} m` : `${radius / 1000} km`
  return radius < 1000 ? `${radius} 公尺` : `${radius / 1000} 公里`
}

function distanceMeters(a: Place, b: Place) {
  const radians = (value: number) => value * Math.PI / 180
  const dLat = radians(b.latitude! - a.latitude!); const dLng = radians(b.longitude! - a.longitude!)
  const value = Math.sin(dLat / 2) ** 2 + Math.cos(radians(a.latitude!)) * Math.cos(radians(b.latitude!)) * Math.sin(dLng / 2) ** 2
  return 6371000 * 2 * Math.atan2(Math.sqrt(value), Math.sqrt(1 - value))
}

function mostCommonCity(places: Place[]) {
  const counts = new Map<string, number>()
  for (const place of places) {
    if (place.city) counts.set(place.city, (counts.get(place.city) ?? 0) + 1)
  }
  return [...counts].sort((a, b) => b[1] - a[1])[0]?.[0] ?? null
}

function placeDistance(place: Place, center: Coordinates) {
  if (place.distance_meters != null) return place.distance_meters
  if (place.latitude == null || place.longitude == null) return Number.MAX_SAFE_INTEGER
  return distanceMeters(place, { ...place, latitude: center.lat, longitude: center.lng })
}
