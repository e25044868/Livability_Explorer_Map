import type { AdministrativeArea, CategoryKey, Coordinates, GeocodeResult, PlaceListResponse, ViewportBounds } from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''
const PLACE_CACHE_TTL_MS = 90_000
const PLACE_CACHE_MAX_ENTRIES = 40
const placeCache = new Map<string, { expiresAt: number; response: PlaceListResponse }>()

async function getPlaces(params: URLSearchParams, signal?: AbortSignal) {
  const key = params.toString()
  const cached = placeCache.get(key)
  if (cached && cached.expiresAt > Date.now()) return cached.response

  const response = await fetch(`${API_BASE}/api/places?${params}`, { signal })
  if (!response.ok) {
    const detail = await response.json().catch(() => null)
    throw new Error(detail?.message ?? `資料載入失敗（${response.status}）`)
  }
  const payload = (await response.json()) as PlaceListResponse
  if (!signal?.aborted) {
    placeCache.set(key, { expiresAt: Date.now() + PLACE_CACHE_TTL_MS, response: payload })
    if (placeCache.size > PLACE_CACHE_MAX_ENTRIES) placeCache.delete(placeCache.keys().next().value!)
  }
  return payload
}

export function fetchPlacesByRadius(
  center: Coordinates,
  radius: number,
  categories: CategoryKey[],
  signal?: AbortSignal,
) {
  const params = new URLSearchParams({
    lat: center.lat.toString(),
    lng: center.lng.toString(),
    radius: radius.toString(),
    categories: categories.join(','),
    limit: '300',
  })
  return getPlaces(params, signal)
}

export function fetchPlacesByViewport(bounds: ViewportBounds, categories: CategoryKey[], signal?: AbortSignal) {
  const params = new URLSearchParams({
    north: bounds.north.toString(),
    south: bounds.south.toString(),
    east: bounds.east.toString(),
    west: bounds.west.toString(),
    categories: categories.join(','),
    limit: '300',
  })
  return getPlaces(params, signal)
}

export function fetchPlacesByCity(city: string, categories: CategoryKey[], signal?: AbortSignal) {
  const params = new URLSearchParams({
    city,
    categories: categories.join(','),
    limit: '500',
  })
  return getPlaces(params, signal)
}

export function fetchPlacesByDistrict(city: string, district: string, categories: CategoryKey[], signal?: AbortSignal) {
  const params = new URLSearchParams({ city, district, categories: categories.join(','), limit: '500' })
  return getPlaces(params, signal)
}

export async function fetchDistricts(city: string, signal?: AbortSignal) {
  const response = await fetch(`${API_BASE}/api/districts?city=${encodeURIComponent(city)}`, { signal })
  if (!response.ok) return []
  return (await response.json()) as string[]
}

export function searchPlaces(keyword: string, signal?: AbortSignal) {
  const params = new URLSearchParams({ keyword, limit: '30' })
  const response = fetch(`${API_BASE}/api/search?${params}`, { signal })
  return response.then(async (result) => {
    if (!result.ok) throw new Error((await result.json().catch(() => null))?.message ?? '搜尋失敗')
    return (await result.json()) as PlaceListResponse
  })
}

export async function detectAdministrativeArea(point: Coordinates) {
  const response = await fetch(`${API_BASE}/api/administrative-area?lat=${point.lat}&lng=${point.lng}`)
  if (!response.ok) throw new Error('無法判斷行政區')
  return (await response.json()) as AdministrativeArea
}

export async function geocodeLandmarks(keyword: string, signal?: AbortSignal) {
  const response = await fetch(`${API_BASE}/api/geocode?keyword=${encodeURIComponent(keyword)}`, { signal })
  if (!response.ok) return []
  return (await response.json()) as GeocodeResult[]
}
