import { useEffect, useRef, useState, type FormEvent } from 'react'
import { geocodeLandmarks, searchPlaces } from '../api'
import type { CategoryKey, Place } from '../types'
import { useI18n } from '../i18n'

export function SearchBar({ onSelect, categories }: { onSelect: (place: Place) => void; categories: CategoryKey[] }) {
  const { t } = useI18n()
  const [keyword, setKeyword] = useState('')
  const [results, setResults] = useState<Place[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [searchTick, setSearchTick] = useState(0)
  const searchImmediately = useRef(false)
  const mapSearchUrl = keyword.trim()
    ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(keyword.trim())}`
    : null

  function showResults(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (keyword.trim().length >= 2) {
      if (mapSearchUrl && looksLikeAddress(keyword)) {
        window.open(mapSearchUrl, '_blank', 'noopener,noreferrer')
        return
      }
      searchImmediately.current = true
      setSearchTick((current) => current + 1)
    }
  }

  useEffect(() => {
    if (keyword.trim().length < 2) {
      setResults([])
      return
    }
    const controller = new AbortController()
    const delay = searchImmediately.current ? 0 : 350
    searchImmediately.current = false
    const timer = window.setTimeout(async () => {
      setLoading(true)
      try {
        const [response, landmarks] = await Promise.all([
          searchPlaces(keyword.trim(), categories, controller.signal), geocodeLandmarks(keyword.trim(), controller.signal),
        ])
        const external: Place[] = landmarks.map((item, index) => ({
          public_id: `geocode-${index}-${item.latitude}-${item.longitude}`, name: item.name,
          category: 'medical', subcategory: '地址或地標', address: item.address, phone: null,
          city: item.city, district: item.district, latitude: item.latitude, longitude: item.longitude,
          distance_meters: null, location_accuracy: 'geocoded', properties: {}, nearby_features: [],
        }))
        setResults([...response.items.filter((place) => place.latitude != null && place.longitude != null), ...external].slice(0, 20))
        setOpen(true)
      } catch (error) {
        if ((error as Error).name !== 'AbortError') setResults([])
      } finally {
        setLoading(false)
      }
    }, delay)
    return () => { window.clearTimeout(timer); controller.abort() }
  }, [categories, keyword, searchTick])

  return (
    <form className="search-box" onSubmit={showResults}>
      <span aria-hidden="true">⌕</span>
      <input
        type="search"
        value={keyword}
        onChange={(event) => setKeyword(event.target.value)}
        onFocus={() => results.length && setOpen(true)}
        placeholder={t('searchPlaceholder')}
        aria-label={t('searchPlaceholder')}
        autoComplete="street-address"
      />
      <button type="submit" className="search-submit" disabled={keyword.trim().length < 2 || loading}>{t('search')}</button>
      {loading && <span className="search-loading">{t('searchLoading')}</span>}
      {open && keyword.trim().length >= 2 && (
        <div className="search-results">
          {results.length ? results.map((place) => (
            <button key={place.public_id} onClick={() => { onSelect(place); setKeyword(place.name); setOpen(false) }}>
              <strong>{place.name}</strong><small>{place.address ?? t('addressUnavailable')}</small>
            </button>
          )) : <div className="search-empty">{t('noSearchResults')}</div>}
          {mapSearchUrl && <a className="search-external-map" href={mapSearchUrl} target="_blank" rel="noreferrer">{t('openInGoogleMaps')}</a>}
        </div>
      )}
    </form>
  )
}

function looksLikeAddress(value: string) {
  return /[縣市區鄉鎮村里路街段巷弄號]/.test(value)
}
