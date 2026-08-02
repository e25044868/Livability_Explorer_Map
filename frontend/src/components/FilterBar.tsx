import { useState } from 'react'
import type { PlaceFilters, SortMode } from '../types'
import { interpolate, useI18n } from '../i18n'

type Props = {
  filters: PlaceFilters
  onChange: (filters: PlaceFilters) => void
  intersectionReady: boolean
  intersectionCount: number
  sortMode: SortMode
  onSortChange: (mode: SortMode) => void
}

export function FilterBar({ filters, onChange, intersectionReady, intersectionCount, sortMode, onSortChange }: Props) {
  const { t } = useI18n()
  const [mobileOpen, setMobileOpen] = useState(false)
  return (
    <div className={`filter-bar ${mobileOpen ? 'expanded' : ''}`}>
      <button className="mobile-filter-toggle" onClick={() => setMobileOpen((current) => !current)} aria-expanded={mobileOpen}>{t('filters')}</button>
      <div className="filter-controls">
      <label>{t('sort')}
        <select value={sortMode} onChange={(event) => onSortChange(event.target.value as SortMode)}>
          <option value="distance">{t('closest')}</option><option value="availability">{t('availability')}</option><option value="name">{t('name')}</option>
        </select>
      </label>
      <label>{t('carSpacesAtLeast')}
        <select value={filters.minCarSpaces} onChange={(event) => onChange({ ...filters, minCarSpaces: Number(event.target.value) })}>
          <option value="0">{t('unlimited')}</option><option value="20">20</option><option value="50">50</option><option value="100">100</option>
        </select>
      </label>
      <label>{t('motorcycleSpacesAtLeast')}
        <select value={filters.minMotorcycleSpaces} onChange={(event) => onChange({ ...filters, minMotorcycleSpaces: Number(event.target.value) })}>
          <option value="0">{t('unlimited')}</option><option value="20">20</option><option value="50">50</option><option value="100">100</option>
        </select>
      </label>
      <label className="check-filter"><input type="checkbox" checked={filters.accessibleOnly} onChange={(event) => onChange({ ...filters, accessibleOnly: event.target.checked })}/>{t('accessible')}</label>
      <label className="check-filter"><input type="checkbox" checked={filters.open24hOnly} onChange={(event) => onChange({ ...filters, open24hOnly: event.target.checked })}/>{t('hours24')}</label>
      <label className="check-filter"><input type="checkbox" checked={filters.evOnly} onChange={(event) => onChange({ ...filters, evOnly: event.target.checked })}/>{t('evCharging')}</label>
      <label className="check-filter"><input type="checkbox" checked={filters.parentChildOnly} onChange={(event) => onChange({ ...filters, parentChildOnly: event.target.checked })}/>{t('familyFriendly')}</label>
      <label className="check-filter"><input type="checkbox" checked={filters.favoritesOnly} onChange={(event) => onChange({ ...filters, favoritesOnly: event.target.checked })}/>{t('favoritesOnly')}</label>
      <label className="check-filter"><input type="checkbox" checked={filters.recentOnly} onChange={(event) => onChange({ ...filters, recentOnly: event.target.checked })}/>{t('recentOnly')}</label>
      <span className={`intersection-chip ${intersectionReady ? 'ready' : ''}`}>{intersectionReady ? interpolate(t('parkingToilet'), { count: intersectionCount }) : t('enableTwoCategories')}</span>
      </div>
    </div>
  )
}
