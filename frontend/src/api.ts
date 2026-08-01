import type { AdministrativeArea, CategoryKey, Coordinates, GeocodeResult, PlaceListResponse, ViewportBounds } from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

async function getPlaces(params: URLSearchParams, signal?: AbortSignal) {
  const response = await fetch(`${API_BASE}/api/places?${params}`, { signal })
  if (!response.ok) {
    const detail = await response.json().catch(() => null)
    throw new Error(detail?.message ?? `資料載入失敗（${response.status}）`)
  }
  return (await response.json()) as PlaceListResponse
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
