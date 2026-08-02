export type Coordinates = { lat: number; lng: number }

export type ViewportBounds = {
  north: number
  south: number
  east: number
  west: number
}

export type ParkingProperties = {
  facility_type?: string
  fee_description?: string
  large_vehicle_spaces?: number
  car_spaces?: number
  motorcycle_spaces?: number
  operator?: string
  contract_period_raw?: string
  parent_name?: string
  zone_label?: string
  toilet_type?: string
  accessible?: boolean
  location_description?: string
  available_hours?: string
  site_name?: string
  grade?: string
  facility_category?: string
  administration?: string
  diaper?: boolean
  place_category?: string
  total_spaces?: number
  available_spaces?: number
  service_status?: number
  live_updated_at?: string
  operation_time?: string
  ev_spaces?: number
  accessible_spaces?: number
  parent_child_spaces?: number
  height_limit?: number
  monthly_pass?: string
  opening_hours?: string
  gender_friendly?: boolean
  parent_child?: boolean
  available_24h?: boolean
  indoor?: boolean
  outdoor?: boolean
  air_conditioning?: boolean
  restroom?: boolean
  seats?: boolean
  station_type?: string
  capacity?: number
  disaster_types?: string
  vulnerable_friendly?: boolean
  service_villages?: string
  agency?: string
  venue_type?: string
  co_located_with_fire_station?: boolean
  english_name?: string
  unit_type?: string
}

export type CategoryKey = 'parking' | 'toilet' | 'aed' | 'pharmacy' | 'medical' | 'motorcycle_charging' | 'drinking_water' | 'shelter' | 'public_wifi' | 'rescue_unit' | 'police'

export type Place = {
  public_id: string
  name: string
  category: CategoryKey
  subcategory: string | null
  address: string | null
  phone: string | null
  city: string | null
  district: string | null
  latitude: number | null
  longitude: number | null
  distance_meters: number | null
  location_accuracy: string
  properties: ParkingProperties
  nearby_features: unknown[]
}

export type PlaceListResponse = {
  items: Place[]
  count: number
  limit: number
  data_version: string
}

export type QueryMode = 'radius' | 'viewport' | 'city'
export type ViewMode = 'map' | 'list'
export type SortMode = 'distance' | 'name' | 'availability'

export type PlaceFilters = {
  minCarSpaces: number
  minMotorcycleSpaces: number
  accessibleOnly: boolean
  favoritesOnly: boolean
  open24hOnly: boolean
  evOnly: boolean
  parentChildOnly: boolean
  recentOnly: boolean
}

export type AdministrativeArea = { city: string; district: string | null }
export type GeocodeResult = { name: string; address: string; latitude: number; longitude: number; city: string | null; district: string | null }
