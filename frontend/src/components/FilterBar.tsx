import type { PlaceFilters, SortMode } from '../types'

type Props = {
  filters: PlaceFilters
  onChange: (filters: PlaceFilters) => void
  intersectionReady: boolean
  intersectionCount: number
  sortMode: SortMode
  onSortChange: (mode: SortMode) => void
}

export function FilterBar({ filters, onChange, intersectionReady, intersectionCount, sortMode, onSortChange }: Props) {
  return (
    <div className="filter-bar">
      <label>排序
        <select value={sortMode} onChange={(event) => onSortChange(event.target.value as SortMode)}>
          <option value="distance">離我最近</option><option value="availability">剩餘車位</option><option value="name">名稱</option>
        </select>
      </label>
      <label>汽車格至少
        <select value={filters.minCarSpaces} onChange={(event) => onChange({ ...filters, minCarSpaces: Number(event.target.value) })}>
          <option value="0">不限</option><option value="20">20</option><option value="50">50</option><option value="100">100</option>
        </select>
      </label>
      <label>機車格至少
        <select value={filters.minMotorcycleSpaces} onChange={(event) => onChange({ ...filters, minMotorcycleSpaces: Number(event.target.value) })}>
          <option value="0">不限</option><option value="20">20</option><option value="50">50</option><option value="100">100</option>
        </select>
      </label>
      <label className="check-filter"><input type="checkbox" checked={filters.accessibleOnly} onChange={(event) => onChange({ ...filters, accessibleOnly: event.target.checked })}/>無障礙</label>
      <label className="check-filter"><input type="checkbox" checked={filters.open24hOnly} onChange={(event) => onChange({ ...filters, open24hOnly: event.target.checked })}/>24 小時</label>
      <label className="check-filter"><input type="checkbox" checked={filters.evOnly} onChange={(event) => onChange({ ...filters, evOnly: event.target.checked })}/>電動車充電</label>
      <label className="check-filter"><input type="checkbox" checked={filters.parentChildOnly} onChange={(event) => onChange({ ...filters, parentChildOnly: event.target.checked })}/>親子友善</label>
      <label className="check-filter"><input type="checkbox" checked={filters.favoritesOnly} onChange={(event) => onChange({ ...filters, favoritesOnly: event.target.checked })}/>僅收藏</label>
      <label className="check-filter"><input type="checkbox" checked={filters.recentOnly} onChange={(event) => onChange({ ...filters, recentOnly: event.target.checked })}/>最近瀏覽</label>
      <span className={`intersection-chip ${intersectionReady ? 'ready' : ''}`}>{intersectionReady ? `停車＋公廁生活圈 ${intersectionCount} 組` : '開啟兩類可分析交集'}</span>
    </div>
  )
}
