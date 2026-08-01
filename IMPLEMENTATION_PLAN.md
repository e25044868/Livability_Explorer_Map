# 生活機能探索地圖：第一階段分析與實作計畫

更新日期：2026-07-20（Asia/Taipei）

> 2026-08-01 進度更新：六個高雄市政府候選 JSON 端點均已實測回應 HTTP 200。詳細筆數、欄位與品質問題見 `DATA_SOURCE_REVIEW.md`；桌機／手機資訊架構與互動規格見 `PAGE_LAYOUT_PLAN.md`。
>
> 2026-08-01 開發更新：已完成後端資料核心第一切片，包括停車場 YAML、正規化、座標驗證、證據式設施關聯、公開 schema、PostGIS 初始 SQL、ADR 與 10 項單元測試。下一步為安全 downloader、raw／staging transaction 與受限 API 骨架。
>
> 2026-08-01 第二階段更新：已完成安全 downloader、content-addressed raw snapshot、品質閘門、SQLAlchemy transaction publisher、PostGIS read repository，以及 places／detail／categories／nearby-summary／search API。33 項測試通過。正式 PostgreSQL 整合與本機 TLS CA 問題仍待部署環境驗證。
>
> 2026-08-01 整合更新：本機 PostGIS 16／PostGIS 3.4 已建立並套用 migration；官方停車場 261 筆已通過品質閘門並正式發布，261 筆 geography 全部有效。真實半徑、viewport、摘要與 API 防護驗證通過，專案可以開始 React／Leaflet 前端切片。

## 1. 現況分析

- Git 儲存庫尚無 commit，工作區沒有追蹤檔案。
- 未發現 `README.md`、`AGENTS.md` 或 `agent.md`，因此沒有可沿用的前端、後端、資料庫、部署設定或專案規範。
- 本階段只完成資料目錄分析與設計文件；未下載候選政府資料、未以假資料代替正式資料，也未建立完整應用程式。
- 建議新專案採 monorepo：`frontend/`（React/Vite/TypeScript）、`backend/`（FastAPI/SQLAlchemy/Alembic）、`data_sources/`（YAML 映射）、`tests/` 與 `docs/`。

## 2. 政府資料目錄分析

分析來源：`C:\Users\User\Downloads\export1784468586.csv`（需求中的 `/mnt/data/export1784468586.csv` 在此 Windows 環境不存在）。

### 2.1 檔案概況

- 檔案大小：68,447,902 bytes。
- 原始檔最後修改時間：2026-07-19 21:43:06（本機時間）。
- 編碼：UTF-8 with BOM（位元組開頭 `EF BB BF`）；以 UTF-8 可完整解碼，CP950/Big5 不可完整解碼。
- CSV 紀錄數：53,207 筆（不含標題列）。
- 欄位數：22。
- 解析方式：Python 標準 `csv.DictReader`，支援引號與欄位內換行。
- 2026-07-20 再以 PowerShell `Import-Csv -Encoding utf8` 獨立核驗，仍得到 53,207 筆、22 欄；並直接檢查前三個位元組確認 BOM 為 `EF BB BF`。

### 2.2 欄位與推定型態

| 欄位 | 推定型態 | 說明 |
|---|---|---|
| 資料集識別碼 | string | 雖多為數字，應保留字串語意 |
| 資料集名稱 | string | 候選搜尋主欄位 |
| 資料提供屬性 | string/category | 類別值 |
| 服務分類 | string/multi-value | 分類文字 |
| 品質檢測 | string/category | 目錄品質資訊 |
| 檔案格式 | string/multi-value | 常以分號對應多個資源 |
| 資料下載網址 | string/multi-value URL | 常以分號對應格式；不可假設只有一個 URL |
| 編碼格式 | string/multi-value | 常與資源順序相對應 |
| 資資料集上架方式 | string/category | 原始標題即含重複「資」字 |
| 資料集描述 | text | 可能含換行 |
| 主要欄位說明 | text/multi-value | 多以分號分隔欄位 |
| 提供機關 | string | 機關名稱 |
| 更新頻率 | string/category | 例如不定期、每月、每日 |
| 授權方式 | string/category | 候選多為政府資料開放授權條款第 1 版 |
| 相關網址 | string/URL | 可為空 |
| 計費方式 | string/category | 目錄使用條件 |
| 提供機關聯絡人姓名 | string | 不應進入公開 places API |
| 提供機關聯絡人電話 | string | 不應進入公開 places API |
| 上架日期 | datetime/string | 匯入時嚴格解析，失敗保留原文 |
| 詮釋資料更新時間 | datetime/string | 是目錄 metadata 時間，不等同來源資料更新時間 |
| 備註 | text | 可為空 |
| 資料量 | string/multi-value integer | 例如 `875;875`；須依資源拆解，不能直接當單一整數 |

格式分布前幾名為 CSV 23,234 筆、JSON+CSV 3,612 筆、JSON 2,402 筆；更新頻率以「不定期更新」34,051 筆最多，其次「每1年」9,513 筆及「每1月」3,116 筆。目錄確實包含大量地理與生活設施資料，但關鍵字命中也包含統計表、預算表等非點位資料，不能只靠關鍵字自動納入。

## 3. 六類候選資料集

下表是第一版候選短名單。地址／座標判定只依目錄的「主要欄位說明」，尚未下載來源內容驗證。

候選搜尋同時比對資料集名稱、描述、主要欄位與提供機關；再人工排除「停車場作業基金」「公廁座數」「醫療人次」等統計資料。關鍵字命中本身不代表可作為地圖點位來源。

| 類別 | ID／資料集 | 提供機關 | 格式／更新 | 地址 | 經緯度 | MVP | 主要問題 |
|---|---|---|---|---|---|---|---|
| 停車 | 46944 高雄市公有路外停車場一覽表 | 高雄市政府交通局 | JSON, CSV／不定期 | 是（位置） | 是 | **首選** | 目錄資料量為 `0;0`，端點可用性與座標品質待驗證 |
| 停車 | 47055 高雄市民營路外停車場一覽表 | 高雄市政府交通局 | JSON, CSV／不定期 | 尚待下載確認 | 未由 metadata 確認 | 第二批 | 欄位被列成 Column1…Column12，需人工辨識表頭；資料量 `0;0` |
| 公廁 | 34868 建檔公廁明細-高雄市 | 環境部環境管理署 | CSV, JSON, XML／不定期 | 是 | 是 | **首選** | API URL 內含目錄所列 key；limit=1000 可能需分頁，且須確認 key 使用條款 |
| 公廁 | 87157 高雄市公廁位置 | 高雄市政府環保局 | JSON, CSV／不定期 | 是 | 是 | 備援 | 目錄資料量 `1;1` 明顯可疑，可能是包裝層計數而非實際筆數 |
| AED | 128664 高雄市AED裝設地點 | 高雄市政府衛生局 | JSON, CSV／不定期 | 是 | 否 | **首批可用** | 875 筆，但需地址地理編碼；位置描述須保留在 properties |
| 藥局 | 143427 高雄市藥局資料 | 高雄市政府衛生局 | JSON, CSV／不定期 | 是 | 否 | **首批可用** | 955 筆；地址拆成縣市、區、街道，需組合與標準化；「姓名」可能屬個資，不公開 |
| 醫療 | 43821 高雄市醫療院所資料 | 高雄市政府衛生局 | JSON, CSV／不定期 | 是 | 否 | **首批可用** | 科別欄位多且適合 JSONB；目錄資料量 `1;1` 可疑；需地理編碼 |
| 充電 | 138245 高雄市電動機車充電站名稱及充電站地址 | 高雄市政府環保局 | JSON, CSV／不定期 | 是 | 否 | 條件式採用 | 136 筆；只有機車站、無汽車站且無座標，不能代表完整「電動車充電站」 |
| 公廁備援 | 30794 全國公廁建檔資料 | 環境部環境管理署 | CSV, JSON, XML／每月 | 是 | 是 | 可篩高雄 | 全國 API 必須在同步端分頁並篩縣市，不可把全量暴露給公開 API |

### 3.1 官方資源 URL

- 46944：`https://openapi.kcg.gov.tw/Api/Service/Get/30c58c88-4f53-45a0-8393-e655feaaa65b`（JSON）；`https://data.kcg.gov.tw/File/DirectDownload/30c58c88-4f53-45a0-8393-e655feaaa65b`（CSV）。
- 47055：`https://openapi.kcg.gov.tw/Api/Service/Get/aeb8ba3c-8eec-49f6-8768-91218c819909`；`https://data.kcg.gov.tw/File/DirectDownload/aeb8ba3c-8eec-49f6-8768-91218c819909`。
- 34868：`https://data.moenv.gov.tw/api/v2/fac_p_17?...&limit=1000&sort=ImportDate%20desc&format=JSON`（實際 key 與分頁方式在串接前確認，不把 key 寫入公開前端或 log）。
- 87157：`https://openapi.kcg.gov.tw/Api/Service/Get/55079b00-e25e-4494-ad2c-30c0ec91d327`；`https://data.kcg.gov.tw/File/DirectDownload/55079b00-e25e-4494-ad2c-30c0ec91d327`。
- 128664：`https://openapi.kcg.gov.tw/Api/Service/Get/55afa833-a9ba-408d-9ba2-fcc31aa86709`；`https://data.kcg.gov.tw/File/DirectDownload/55afa833-a9ba-408d-9ba2-fcc31aa86709`。
- 143427：`https://openapi.kcg.gov.tw/Api/Service/Get/90c492ab-cc42-402b-91ea-dfd868015d10`；`https://data.kcg.gov.tw/File/DirectDownload/90c492ab-cc42-402b-91ea-dfd868015d10`。
- 43821：`https://openapi.kcg.gov.tw/Api/Service/Get/1b381cc4-7da0-42b6-b9be-b49edf87775d`；`https://data.kcg.gov.tw/File/DirectDownload/1b381cc4-7da0-42b6-b9be-b49edf87775d`。
- 138245：`https://openapi.kcg.gov.tw/Api/Service/Get/877e2cbe-293f-447d-8e3f-bf32733191ce`；`https://data.kcg.gov.tw/File/DirectDownload/877e2cbe-293f-447d-8e3f-bf32733191ce`。

以上候選的目錄授權均標示「政府資料開放授權條款-第1版」。正式上線仍要在同步時保存每個資料集的授權快照與官方頁面，避免目錄異動後無法稽核。

## 4. 第一批選擇與優先順序

第一個完整串接確定使用 **46944 高雄市公有路外停車場一覽表**：2026-08-01 實測回應 261 筆，座標皆可解析且落在台灣合理範圍，並包含名稱、行政區、位置、收費、車位數、業者與電話，可在不先依賴地理編碼服務的情況下驗證 downloader → parser → normalizer → coordinate validator → staging → places 全流程。需先處理 6 筆以 `-` 表示延續上一場站的分區資料。

第二個來源使用 **87157 高雄市公廁位置**：實測回應 1,000 筆，其中 841 筆有可信座標、159 筆缺少或無效座標。API 沒有總筆數與分頁欄位，因此 1,000 筆視為疑似截斷。後續順序：AED → 藥局 → 醫療 → 機車充電 → 民營停車場。只有地址的資料先保存、排入受控地理編碼佇列，未取得可信座標前不顯示在地圖。

## 5. 系統架構

```text
政府 API/CSV/JSON/XML/ZIP
  -> SSRF-safe downloader（allowlist、timeout、大小/壓縮比限制）
  -> raw_imports（不可變原始快照與 hash）
  -> dataset YAML mapping + parser
  -> normalizer / coordinate validator / deduplicator
  -> staging_places + 品質閘門
  -> transaction upsert places / deactivate missing records
  -> PostGIS 查詢服務
  -> FastAPI 公開 DTO（不暴露 raw/internal id）
  -> React 分析面板 + Leaflet 地圖
```

資料來源設定採 YAML，至少包含 `dataset_key`、官方 metadata URL、允許的下載 host、格式、encoding、更新頻率、欄位映射、座標系統、清理規則與 properties 映射。secret 或 API key 僅由環境變數注入，不進設定檔。

## 6. 建議資料庫 Schema（PostgreSQL + PostGIS）

### `data_sources`

- `id uuid PK`、`dataset_key text UNIQUE`、`name`、`category`、`source_agency`、`public_metadata_url`、`update_frequency`、`license_name`、`license_url`、`config_version`、`is_enabled`、timestamps。
- 不儲存可公開取回的 secret；下載 URL 若含憑證應存 secret reference 或淨化版本。

### `raw_imports`

- `id uuid PK`、`data_source_id FK`、`fetched_at`、`source_updated_at`、`content_hash`、`raw_data jsonb` 或受控 object-storage key、`http_metadata jsonb`、`record_count`、`import_status`、`error_code`、`error_message`。
- `UNIQUE(data_source_id, content_hash)`；公開 API 完全不可存取。

### `import_runs`

- `id uuid PK`、`data_source_id FK`、`started_at`、`finished_at`、`status`、下載/解析/有效/無效/寫入/停用筆數、品質指標、錯誤摘要與 `config_version`。

### `places`

- `id uuid PK`（內部）、`public_id uuid UNIQUE`、`external_id text`、`name text NOT NULL`、`normalized_name text`。
- `category text NOT NULL`、`subcategory text`、`address`、`normalized_address`、`city`、`district`、`phone`、`opening_hours`。
- `latitude double precision`、`longitude double precision`、`geom geography(Point,4326)`；由受信任座標產生並以 constraint 確保一致。
- `location_accuracy enum/examined text`：`exact_coordinate`、`converted_coordinate`、`address_geocoded`、`district_only`、`invalid`。
- `properties jsonb NOT NULL DEFAULT '{}'`、`source_agency`、`source_dataset`、`source_record_url`（僅允許公開官方 URL）、`source_updated_at`、`last_synced_at`、`is_active`。
- `canonical_place_id uuid NULL FK places`、`duplicate_group_id uuid NULL`、timestamps。
- `UNIQUE(data_source_id, external_id)`；若來源無 ID，使用經版本化正規化欄位產生穩定 source key。
- 索引：`GIST(geom)`（partial: active 且 geom 非空）、`(category, city, district, is_active)`、`GIN(properties)`、`GIN(to_tsvector(...))` 或 `pg_trgm` 名稱/地址索引。

### `staging_places`

- 與匯入必要欄位對齊，另含 `import_run_id`、`source_row_number`、`validation_errors jsonb`。品質閘門通過後才在 transaction 中 upsert 正式表。

### 擴充表

- `place_relations(id, from_place_id, to_place_id, relation_type, confidence, evidence jsonb, created_at)`；不因同名直接刪除。
- `location_scores(id, subject_type, subject_key, center geography, radius_meters, scenario, score, category_summary jsonb, computed_at, algorithm_version)`。
- `administrative_statistics(id, area_code, category, place_count, completeness, computed_at, source_version)`。

`category` 第一版以受驗證字串/lookup table 管理（parking、toilet、aed、pharmacy、medical、charging_station），避免 PostgreSQL enum 阻礙未來便利商店服務擴充。

## 7. API 規格與防護

- `GET /api/places`：必須具有 viewport、中心點+半徑、縣市/行政區或有效 keyword 之一；預設 300、最高 500；限制 viewport 面積與半徑；只回傳 public DTO。
- `GET /api/places/{public_id}`：回傳特殊屬性、官方來源/更新、本站同步及導航 URL；不存在用一致 problem JSON。
- `GET /api/categories`：回傳設定檔驅動的分類及可用筆數/更新狀態。
- `GET /api/nearby-summary`：PostGIS `ST_DWithin` 聚合各類數量，限制最大半徑。
- `GET /api/search`：名稱、地址、行政區與類別搜尋；設定最小關鍵字長度與 limit。
- 使用 Pydantic 驗證、CORS allowlist、環境控制 docs、可信 proxy 設定、rate limit、request ID、結構化 log；正式環境不回傳 traceback。

## 8. 前端頁面

- 首頁採「生活機能分析面板 + 地圖」，非商家目錄模式：搜尋、情境入口、多類複選、半徑、符合度/缺項、各類最近距離、來源狀態。
- Leaflet marker clustering、搜尋此區域、地圖/清單切換、定位權限與錯誤狀態。
- 手機先顯示需求/情境，結果用 bottom sheet；地圖是分析結果視圖。
- 設施詳情與資料來源頁完整呈現政府特有欄位、metadata 更新時間（明確標示）及本站同步時間。
- 預留雙地點/區域比較路由與資料型別，第一版不實作完整評分。

## 9. 分階段實作

1. 建立 monorepo、環境設定、PostGIS migration、公開/內部 schema 邊界與 CI。
2. 驗證 46944 端點及實際欄位；建立 YAML、受限 downloader、raw/import log、parser、normalizer、座標驗證、staging transaction 與測試。
3. 建立受條件約束的 places/detail/categories/nearby-summary/search API，加入索引、rate limit 與安全測試。
4. 建立 React 分析面板、Leaflet、聚合標記、清單/資訊卡、定位、響應式與狀態畫面。
5. 依序擴充公廁、AED、藥局、醫療與充電來源；地址地理編碼須具快取、配額、人工抽驗與 attribution。
6. 建立資料來源頁、同步排程、監控、部署文件與回復策略。

## 10. 重大風險與需確認事項

不因下列事項停止第一階段，但進入實作/上線前需要決策或驗證：

1. **官方端點真實內容**：目錄資料量 `0;0` 或 `1;1` 與欄位資訊矛盾；下一階段只下載首選資料的小型回應做 schema/筆數/座標抽驗。
2. **地址地理編碼服務**：四類高價值資料缺座標。需確認供應者、授權、配額、個資/資料落地條件與費用；未確認前不批量 geocode。
3. **充電站產品範圍**：高雄候選是電動機車站，無法代表汽車快慢充。需確認 MVP 是否接受機車限定，或另核准中央/民間來源研究。
4. **環境部 API key**：目錄 URL 看似含 key，不能假設可長期或公開使用；需依官方規範申請/輪替，後端 secret 管理。
5. **來源更新語意**：「詮釋資料更新時間」不是設施資料的官方更新日；UI 必須分開呈現，來源沒有資料更新日則顯示「未提供」。
6. **地理編碼與 OSM 使用政策**：不可用公開 Nominatim 做無限制批次；地址搜尋與批次 geocode 需各自合規方案。
7. **部署責任**：需確認 Supabase PostGIS、Render、Vercel 的專案與 secrets；在確認前先保持 provider-neutral Docker/環境變數設計。

## 11. 驗收條件

- 第一個來源的原始快照可重現、hash 去重、錯誤不破壞正式資料。
- 座標僅在通過台灣合理範圍與欄位/座標系統驗證後上圖。
- `/api/places` 無條件查詢為 400，limit 永不超過 500，大 viewport/半徑被拒絕。
- raw_data、內部 ID、secret/internal URL 不出現在 OpenAPI 或 response。
- 半徑/viewport 空間查詢使用 PostGIS 索引並有整合測試。
- 前端在桌面與手機完成多類複選、機能摘要、符合/缺項及來源狀態；具 loading/empty/error。
- backend tests、migration、frontend typecheck/lint/build 與基本安全測試全數通過。
