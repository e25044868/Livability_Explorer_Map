import { useI18n } from '../i18n'

export const CITY_CENTERS: Record<string, { lat: number; lng: number }> = {
  臺北市: { lat: 25.0375, lng: 121.5637 }, 新北市: { lat: 25.012, lng: 121.465 },
  桃園市: { lat: 24.9937, lng: 121.301 }, 臺中市: { lat: 24.1477, lng: 120.6736 },
  臺南市: { lat: 22.9999, lng: 120.227 }, 高雄市: { lat: 22.6273, lng: 120.3014 },
  基隆市: { lat: 25.1276, lng: 121.7392 }, 新竹市: { lat: 24.8138, lng: 120.9675 },
  新竹縣: { lat: 24.8387, lng: 121.0177 }, 苗栗縣: { lat: 24.5602, lng: 120.8214 },
  彰化縣: { lat: 24.0756, lng: 120.544 }, 南投縣: { lat: 23.9609, lng: 120.9719 },
  雲林縣: { lat: 23.7092, lng: 120.4313 }, 嘉義市: { lat: 23.4801, lng: 120.4491 },
  嘉義縣: { lat: 23.4518, lng: 120.2555 }, 屏東縣: { lat: 22.5519, lng: 120.5488 },
  宜蘭縣: { lat: 24.7021, lng: 121.7378 }, 花蓮縣: { lat: 23.9911, lng: 121.6112 },
  臺東縣: { lat: 22.7554, lng: 121.1501 }, 澎湖縣: { lat: 23.5712, lng: 119.5793 },
  金門縣: { lat: 24.4321, lng: 118.3171 }, 連江縣: { lat: 26.1604, lng: 119.9517 },
}

export function CitySelector({
  value, district, districts, detectedCity, onChange, onDistrictChange,
}: {
  value: string
  district: string | null
  districts: string[]
  detectedCity: string | null
  onChange: (city: string) => void
  onDistrictChange: (district: string | null) => void
}) {
  const { t, cityLabel } = useI18n()
  return (
    <div className="area-selectors">
      <label className="city-selector">
        <span>{t('city')}</span>
        <select value={value} onChange={(event) => onChange(event.target.value)} aria-label={t('selectCity')}>
          {Object.keys(CITY_CENTERS).map((city) => <option key={city} value={city}>{cityLabel(city)}</option>)}
        </select>
      </label>
      <label className="city-selector district-selector">
        <span>{t('district')}</span>
        <select value={district ?? ''} onChange={(event) => onDistrictChange(event.target.value || null)} aria-label={t('selectDistrict')}>
          <option value="">{t('allDistricts')}</option>
          {districts.map((item) => <option key={item} value={item}>{item}</option>)}
        </select>
      </label>
      {detectedCity && <small className="detected-city">{t('detected')}{cityLabel(detectedCity)}</small>}
    </div>
  )
}
