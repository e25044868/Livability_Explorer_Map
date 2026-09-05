import { createContext, useContext } from 'react'
import type { ReactNode } from 'react'
import type { CategoryKey } from './types'

export type Language = 'zh-TW' | 'en'

type I18nValue = {
  language: Language
  setLanguage: (language: Language) => void
  t: (key: keyof typeof messages['zh-TW']) => string
  cityLabel: (city: string | null | undefined) => string
  districtLabel: (district: string | null | undefined) => string
  categoryLabel: (category: CategoryKey) => string
}

const messages = {
  'zh-TW': {
    appName: '生活機能探索地圖', search: '搜尋', map: '地圖', list: '清單', share: '分享', home: '回首頁', about: '關於', platformAbout: '關於平台', menu: '選單',
    city: '縣市', district: '行政區', allDistricts: '所有行政區', selectCity: '選擇縣市', selectDistrict: '選擇行政區', detected: '定位：', analysisCenter: '分析中心', searchAndBrowse: '搜尋與區域瀏覽',
    kaohsiungCenter: '高雄市中心', useLocation: '使用目前位置', exploreRange: '探索範圍',
    centerRadius: '中心點半徑', cityBrowse: '縣市瀏覽', mapArea: '目前地圖區域', areaSearch: '區域搜尋',
    chooseRadius: '選擇搜尋半徑', adjustRadius: '拖曳調整中心搜尋半徑', dataCategories: '資料類別',
    openData: '全國政府開放資料', pendingGeocode: '待地理編碼', noVerifiedCoordinates: '無可信座標的類別不會顯示成地圖標記。',
    areaSummary: '區域摘要', parkingSummary: '停車供給概況', facilities: '設施總數', placesUnit: '處',
    carSpaces: '汽車格', motorcycleSpaces: '機車格', spacesUnit: '格', waitingData: '等待資料', dataUpdated: '資料更新 ',
    resultsHint: '探索結果 · 點地圖可更換中心', updating: '更新中', matchingResults: '筆符合條件',
    withinRadius: '中心點 {radius} 內', cityData: '{city}資料', districtData: '{city} · {district}資料', currentMapArea: '目前地圖區域',
    switchTheme: '切換為{theme}模式', darkTheme: '深色', lightTheme: '淺色',
    locationUnsupported: '此瀏覽器不支援定位功能', locationUnavailable: '無法取得目前位置，請確認瀏覽器定位權限',
    shareTitle: '生活機能探索地圖', shareText: '查看這個生活機能搜尋範圍', linkCopied: '分享連結已複製', copyFailed: '無法複製分享連結',
    searchPlaceholder: '輸入完整地址、地標或設施', searchLoading: '搜尋中', noSearchResults: '找不到具可信座標的設施', openInGoogleMaps: '在 Google 地圖開啟',
    addressUnavailable: '地址未提供', loadingPlaces: '正在查詢設施…', unableToLoad: '無法取得資料',
    noPlaces: '這個範圍目前沒有設施', tryMoveMap: '移動地圖或放大搜尋半徑再試一次。',
    filters: '篩選', mobilePanel: '篩選與資料', sort: '排序', closest: '離我最近', availability: '剩餘車位', name: '名稱', carSpacesAtLeast: '汽車格至少',
    motorcycleSpacesAtLeast: '機車格至少', unlimited: '不限', accessible: '無障礙', hours24: '24 小時',
    evCharging: '電動車充電', familyFriendly: '親子友善', favoritesOnly: '僅收藏', recentOnly: '最近瀏覽',
    parkingToilet: '停車＋公廁生活圈 {count} 組', enableTwoCategories: '開啟兩類可分析交集',
    searchThisArea: '搜尋此區域', searching: '搜尋中…', facilitiesCount: '{count} 個設施',
    details: '{name}詳細資訊', addFavorite: '加入收藏', removeFavorite: '取消收藏', closeDetails: '關閉詳細資訊',
    navigation: '導航方式', walking: '步行', cycling: '騎車', driving: '開車', yes: '有', notSpecified: '未標示',
    source: '資料來源：{source}。資料版本：{version}。', reportError: '回報資訊錯誤',
    localGovernment: '地方政府／交通部 TDX', nationalAed: '衛生福利部全國 AED 開放資料', nationalToilet: '環境部全國公廁資料',
    coolMap: '環境部 Cool map 涼適點', nationalShelter: '內政部消防署避難收容處所資料', nationalWifi: '數位發展部 iTaiwan 公共免費 Wi-Fi 資料', nationalRescue: '內政部消防署消防／救援據點資料', nationalPolice: '內政部警政署警察機關資料', nationalLibrary: '國立公共資訊圖書館公共圖書館資料', nationalPublicBicycle: '交通部 TDX 公共自行車資料', governmentData: '政府開放資料',
    aboutEyebrow: 'ABOUT THE MAP', aboutTitle: '關於生活機能探索地圖', closeAbout: '關閉平台說明',
    aboutIntro: '本平台將具備可信座標的公共設施整合到同一張地圖，協助你依地點、距離與需求快速探索生活機能。',
    officialSources: '官方資料來源', parkingSource: '交通部 TDX：路外停車場資料', toiletSource: '環境部環境管理署：全國公廁建檔資料',
    aedSource: '衛生福利部醫事司：全國公共場所 AED 位置資訊', waterSource: '環境部氣候變遷署：Cool map 涼適點－飲水機',
    shelterSource: '內政部消防署：避難收容處所點位檔', wifiSource: '數位發展部：iTaiwan 公共區域免費無線上網熱點', rescueSource: '內政部消防署：消防／救援據點位置', policeSource: '內政部警政署：警察機關地址與座標資料', librarySource: '國立公共資訊圖書館：公共圖書館基本資料', publicBicycleSource: '交通部 TDX：公共自行車站點與即時車位資料', tourismFacilitySource: '交通部觀光署：風景區民眾關心公共設施', aboutNote: '資料會依各官方來源的公開更新情況整理發布；平台僅呈現具可信座標的項目，實際服務狀態請以主管機關公告為準。',
    nationalTourismFacility: '交通部觀光署風景區公共設施資料', parking: '路外停車場', toilet: '公共廁所', aed: 'AED', drinking_water: '公共飲水機', shelter: '避難收容處所', public_wifi: '公共免費 Wi-Fi', rescue_unit: '消防／救援據點', police: '警察機關／派出所', library: '公共圖書館', public_bicycle: '公共自行車站', tourism_facility: '風景區友善設施', pharmacy: '藥局', medical: '醫療院所', motorcycle_charging: '機車充電',
  },
  en: {
    appName: 'Livability Explorer Map', search: 'Search', map: 'Map', list: 'List', share: 'Share', home: 'Home', about: 'About', platformAbout: 'About platform', menu: 'Menu',
    city: 'City', district: 'District', allDistricts: 'All districts', selectCity: 'Select city', selectDistrict: 'Select district', detected: 'Located: ', analysisCenter: 'ANALYSIS CENTER', searchAndBrowse: 'SEARCH & AREA BROWSE',
    kaohsiungCenter: 'Kaohsiung City Center', useLocation: 'Use current location', exploreRange: 'SEARCH RANGE',
    centerRadius: 'Radius from center', cityBrowse: 'Browse by city', mapArea: 'Current map area', areaSearch: 'Area search',
    chooseRadius: 'Choose search radius', adjustRadius: 'Drag to adjust the search radius', dataCategories: 'DATA CATEGORIES',
    openData: 'Government open data', pendingGeocode: 'Awaiting geocoding', noVerifiedCoordinates: 'Categories without verified coordinates are not plotted on the map.',
    areaSummary: 'AREA SUMMARY', parkingSummary: 'Parking overview', facilities: 'Facilities', placesUnit: 'places',
    carSpaces: 'Car spaces', motorcycleSpaces: 'Motorcycle spaces', spacesUnit: 'spaces', waitingData: 'Waiting for data', dataUpdated: 'Updated ',
    resultsHint: 'RESULTS · Click the map to set a new center', updating: 'Updating', matchingResults: 'matching',
    withinRadius: 'Within {radius} of center', cityData: '{city} data', districtData: '{city} · {district} data', currentMapArea: 'Current map area',
    switchTheme: 'Switch to {theme} mode', darkTheme: 'dark', lightTheme: 'light',
    locationUnsupported: 'This browser does not support location services', locationUnavailable: 'Unable to get your location. Check browser permissions.',
    shareTitle: 'Livability Explorer Map', shareText: 'View this livability search area', linkCopied: 'Share link copied', copyFailed: 'Unable to copy the share link',
    searchPlaceholder: 'Enter an address, landmark, or facility', searchLoading: 'Searching', noSearchResults: 'No facility with verified coordinates found', openInGoogleMaps: 'Open in Google Maps',
    addressUnavailable: 'Address not provided', loadingPlaces: 'Loading facilities…', unableToLoad: 'Unable to load data',
    noPlaces: 'No facilities in this area', tryMoveMap: 'Move the map or increase the search radius and try again.',
    filters: 'Filters', mobilePanel: 'Filters & data', sort: 'Sort', closest: 'Nearest', availability: 'Available spaces', name: 'Name', carSpacesAtLeast: 'Minimum car spaces',
    motorcycleSpacesAtLeast: 'Minimum motorcycle spaces', unlimited: 'Any', accessible: 'Accessible', hours24: '24 hours',
    evCharging: 'EV charging', familyFriendly: 'Family friendly', favoritesOnly: 'Favorites only', recentOnly: 'Recently viewed',
    parkingToilet: 'Parking + restroom pairs: {count}', enableTwoCategories: 'Enable both categories to analyse overlap',
    searchThisArea: 'Search this area', searching: 'Searching…', facilitiesCount: '{count} facilities',
    details: '{name} details', addFavorite: 'Add favorite', removeFavorite: 'Remove favorite', closeDetails: 'Close details',
    navigation: 'Directions', walking: 'Walk', cycling: 'Cycle', driving: 'Drive', yes: 'Yes', notSpecified: 'Not specified',
    source: 'Source: {source}. Data version: {version}.', reportError: 'Report data issue',
    localGovernment: 'Local government / MOTC TDX', nationalAed: 'National AED open data', nationalToilet: 'National public restroom data',
    coolMap: 'MOENV Cool Map', nationalShelter: 'National Fire Agency shelter data', nationalWifi: 'MODA iTaiwan free public Wi-Fi data', nationalRescue: 'National Fire Agency fire and rescue unit data', nationalPolice: 'National Police Agency police facility data', nationalLibrary: 'National Library of Public Information public library data', nationalPublicBicycle: 'MOTC TDX public bicycle data', governmentData: 'Government open data',
    aboutEyebrow: 'ABOUT THE MAP', aboutTitle: 'About Livability Explorer Map', closeAbout: 'Close about panel',
    aboutIntro: 'This map brings public facilities with verified coordinates into one place, helping you explore nearby everyday services by location, distance, and needs.',
    officialSources: 'Official data sources', parkingSource: 'MOTC TDX: Off-street parking data', toiletSource: 'MOENV Environmental Management Administration: National public restroom registry',
    aedSource: 'MOHW Department of Medical Affairs: National public AED locations', waterSource: 'MOENV Climate Change Administration: Cool Map drinking water points',
    shelterSource: 'National Fire Agency: Emergency shelter locations', wifiSource: 'MODA: iTaiwan public free Wi-Fi hotspots', rescueSource: 'National Fire Agency: Fire and rescue unit locations', policeSource: 'National Police Agency: Police facility addresses and coordinates', librarySource: 'National Library of Public Information: Public library basic data', publicBicycleSource: 'MOTC TDX: Public bicycle stations and live availability', tourismFacilitySource: 'Tourism Administration: Visitor-focused scenic-area facilities', aboutNote: 'Data is organised according to each official source’s public updates. Only records with verified coordinates are plotted; always confirm service status with the responsible authority.',
    nationalTourismFacility: 'Tourism Administration scenic-area facility data', parking: 'Off-street parking', toilet: 'Public restroom', aed: 'AED', drinking_water: 'Drinking water', shelter: 'Emergency shelter', public_wifi: 'Free public Wi-Fi', rescue_unit: 'Fire and rescue unit', police: 'Police station', library: 'Public library', public_bicycle: 'Public bicycle station', tourism_facility: 'Scenic-area friendly facilities', pharmacy: 'Pharmacy', medical: 'Medical facility', motorcycle_charging: 'Motorcycle charging',
  },
} as const

const cities: Record<string, string> = {
  臺北市: 'Taipei City', 新北市: 'New Taipei City', 桃園市: 'Taoyuan City', 臺中市: 'Taichung City', 臺南市: 'Tainan City', 高雄市: 'Kaohsiung City',
  基隆市: 'Keelung City', 新竹市: 'Hsinchu City', 新竹縣: 'Hsinchu County', 苗栗縣: 'Miaoli County', 彰化縣: 'Changhua County', 南投縣: 'Nantou County',
  雲林縣: 'Yunlin County', 嘉義市: 'Chiayi City', 嘉義縣: 'Chiayi County', 屏東縣: 'Pingtung County', 宜蘭縣: 'Yilan County', 花蓮縣: 'Hualien County',
  臺東縣: 'Taitung County', 澎湖縣: 'Penghu County', 金門縣: 'Kinmen County', 連江縣: 'Lienchiang County',
}

const districts: Record<string, string> = {
  // Kaohsiung City
  三民區: 'Sanmin Dist.', 仁武區: 'Renwu Dist.', 內門區: 'Neimen Dist.', 六龜區: 'Liugui Dist.', 前金區: 'Qianjin Dist.', 前鎮區: 'Qianzhen Dist.', 大寮區: 'Daliao Dist.', 大樹區: 'Dashu Dist.', 大社區: 'Dashe Dist.', 小港區: 'Xiaogang Dist.', 岡山區: 'Gangshan Dist.', 左營區: 'Zuoying Dist.', 林園區: 'Linyuan Dist.', 田寮區: 'Tianliao Dist.', 甲仙區: 'Jiaxian Dist.', 旗山區: 'Qishan Dist.', 旗津區: 'Qijin Dist.', 杉林區: 'Shanlin Dist.', 梓官區: 'Ziguan Dist.', 茂林區: 'Maolin Dist.', 桃源區: 'Taoyuan Dist.', 楠梓區: 'Nanzih Dist.', 湖內區: 'Hunei Dist.', 新興區: 'Xinxing Dist.', 鼓山區: 'Gushan Dist.', 路竹區: 'Luzhu Dist.', 鳥松區: 'Niaosong Dist.', 鳳山區: 'Fengshan Dist.', 橋頭區: 'Qiaotou Dist.', 燕巢區: 'Yanchao Dist.', 彌陀區: 'Mituo Dist.', 鹽埕區: 'Yancheng Dist.', 阿蓮區: 'Alian Dist.', 美濃區: 'Meinong Dist.', 苓雅區: 'Lingya Dist.', 茄萣區: 'Qieding Dist.', 永安區: 'Yongan Dist.', 那瑪夏區: 'Namaxia Dist.',
  // Pingtung County
  屏東市: 'Pingtung City', 潮州鎮: 'Chaozhou Township', 東港鎮: 'Donggang Township', 恆春鎮: 'Hengchun Township', 萬丹鄉: 'Wandan Township', 長治鄉: 'Changzhi Township', 麟洛鄉: 'Linluo Township', 九如鄉: 'Jiuru Township', 里港鄉: 'Ligang Township', 鹽埔鄉: 'Yanpu Township', 高樹鄉: 'Gaoshu Township', 萬巒鄉: 'Wanluan Township', 內埔鄉: 'Neipu Township', 竹田鄉: 'Zhutian Township', 新埤鄉: 'Xinpi Township', 枋寮鄉: 'Fangliao Township', 新園鄉: 'Xinyuan Township', 崁頂鄉: 'Kanding Township', 林邊鄉: 'Linbian Township', 南州鄉: 'Nanzhou Township', 佳冬鄉: 'Jiadong Township', 琉球鄉: 'Liuqiu Township', 車城鄉: 'Checheng Township', 滿州鄉: 'Manzhou Township', 枋山鄉: 'Fangshan Township', 三地門鄉: 'Sandimen Township', 霧臺鄉: 'Wutai Township', 瑪家鄉: 'Majia Township', 泰武鄉: 'Taiwu Township', 來義鄉: 'Laiyi Township', 春日鄉: 'Chunri Township', 獅子鄉: 'Shizi Township', 牡丹鄉: 'Mudan Township',
}

const I18nContext = createContext<I18nValue | null>(null)

export function I18nProvider({ value, children }: { value: I18nValue; children: ReactNode }) {
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function createI18n(language: Language, setLanguage: (language: Language) => void): I18nValue {
  const t = (key: keyof typeof messages['zh-TW']) => messages[language][key] as string
  return {
    language,
    setLanguage,
    t,
    cityLabel: (city) => language === 'en' && city ? (cities[city] ?? city) : city ?? '',
    districtLabel: (district) => language === 'en' && district ? (districts[district] ?? district) : district ?? '',
    categoryLabel: (category) => t(category),
  }
}

export function useI18n() {
  const value = useContext(I18nContext)
  if (!value) throw new Error('useI18n must be used within I18nProvider')
  return value
}

export function interpolate(template: string, values: Record<string, string | number>) {
  return template.replace(/\{(\w+)\}/g, (_, key: string) => String(values[key] ?? ''))
}
