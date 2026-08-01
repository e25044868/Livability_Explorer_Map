import { useEffect, useState } from 'react'
import { geocodeLandmarks, searchPlaces } from '../api'
import type { Place } from '../types'

export function SearchBar({ onSelect }: { onSelect: (place: Place) => void }) {
  const [keyword, setKeyword] = useState('')
  const [results, setResults] = useState<Place[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (keyword.trim().length < 2) {
      setResults([])
      return
    }
    const controller = new AbortController()
    const timer = window.setTimeout(async () => {
      setLoading(true)
      try {
        const [response, landmarks] = await Promise.all([
          searchPlaces(keyword.trim(), controller.signal), geocodeLandmarks(keyword.trim(), controller.signal),
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
    }, 350)
    return () => { window.clearTimeout(timer); controller.abort() }
  }, [keyword])

  return (
    <div className="search-box">
      <span aria-hidden="true">⌕</span>
      <input
        value={keyword}
        onChange={(event) => setKeyword(event.target.value)}
        onFocus={() => results.length && setOpen(true)}
        placeholder="搜尋地址、地標或設施"
        aria-label="搜尋地址、地標或設施"
      />
      {loading && <span className="search-loading">搜尋中</span>}
      {open && keyword.trim().length >= 2 && (
        <div className="search-results">
          {results.length ? results.map((place) => (
            <button key={place.public_id} onClick={() => { onSelect(place); setKeyword(place.name); setOpen(false) }}>
              <strong>{place.name}</strong><small>{place.address ?? '地址未提供'}</small>
            </button>
          )) : <div className="search-empty">找不到具可信座標的設施</div>}
        </div>
      )}
    </div>
  )
}
