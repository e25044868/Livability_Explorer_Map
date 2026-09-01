# 開發工作紀錄

## 2026-08-21（風景區友善設施來源）

- 新增觀光署「風景區民眾關心公共設施」精選來源，只納入具官方 WGS84 座標的遊客中心、哺集乳室、無障礙設施／坡道、急救箱與穆斯林禱告室。
- 新增 `tourism_facility` 類別、公開 properties allowlist、地圖標記、清單與詳細資訊中英文標籤。
- 既有無障礙／親子篩選可同時套用於新來源；公共廁所既有友善欄位不重複匯入。
- 新增來源設定、正規化單元測試與 ADR 0003；尚未發布至 Supabase。

## 2026-08-01（全國版核心體驗）

- TDX 發布流程加入即時剩餘車位合併，並保留充電、無障礙、親子、限高與月租欄位。
- 目前位置與地圖點選改由國土測繪中心座標行政區服務判定縣市／行政區。
- 搜尋框合併資料庫設施、臺灣地址與地標搜尋。
- 標記依縮放層級聚合，充電停車場使用紫色閃電標記。
- 新增 24 小時、電動車充電、無障礙與親子友善篩選。
- 新增距離／名稱／剩餘車位排序與最近瀏覽篩選。
- 詳細資訊加入步行、騎車、開車導航及資料錯誤回報入口。
- 分享連結會保存中心點、半徑、類別與縣市，開啟後可還原探索狀態。
- 手機詳細資訊改為帶有拖曳把手視覺提示的底部面板。
- 新增環境部全國飲水機 4,767 筆與消防署避難收容處所 5,973 筆。
- 新增飲水機藍色與避難處所橘色標記、類別按鈕、清單摘要及詳細設施欄位。

## 2026-08-01（全國資料與縣市切換）

### 完成內容

- 正式發布環境部全國公廁 45,720 筆，取代高雄限定公廁來源。
- 正式發布衛福部全國 AED 15,718 筆；184 筆無效座標保留但不上圖。
- 新增 22 縣市選擇器、縣市整體瀏覽與定位後依附近資料判斷縣市。
- API 公開 `city`、`district`，沿用既有 Place/PostGIS 模型。
- 建立 TDX OAuth 停車場轉接器、正規化器與指定縣市發布 CLI；等待專案金鑰即可發布。
- 大量資料 publisher 改為每批 1,000 筆 upsert，避免 PostgreSQL 參數上限。

### 驗證結果

- 臺北市查詢可同時回傳 AED 與公廁，且所有回傳項目具縣市與可信座標。
- 臺南中心 3 公里回傳 500 筆上限資料；花蓮中心 3 公里回傳 386 筆。
- TDX 正規化測試確認仍輸出共用 Place 模型。

## 2026-08-01（多圖層與探索工具）

### 完成內容

- 正式匯入高雄公廁 1,000 筆；841 筆可信座標可上圖，159 筆保留但不冒充可定位資料。
- 支援點地圖更換分析中心、設施名稱／地址搜尋與獨立中心點標記。
- 新增停車場／公廁圖層切換、Marker 聚合及分類標記。
- 新增詳細資訊抽屜、裝置本機收藏、車位／無障礙篩選。
- 新增 300 公尺內「停車＋公廁」生活圈交集統計。
- AED、藥局、醫療與機車充電保留待地理編碼狀態，無可信座標前不上圖。

### 驗證結果

- 3 公里多類別查詢回傳 160 筆：停車場 47、公廁 113，全部具有效座標。
- 名稱／地址搜尋正常回傳資料。
- 前端 production build 成功；後端 36 tests passed。

## 2026-08-01（React／Leaflet 第一版）

### 完成內容

- 建立 React 19、Vite 7、TypeScript 5 與 React Leaflet 前端。
- 完成桌機雙欄分析面板與手機直向響應式配置。
- 串接 PostGIS 真實停車場 API，不使用前端假資料。
- 支援 500 公尺、1 公里與 3 公里中心點半徑查詢。
- 地圖移動後可用「搜尋此區域」執行 viewport 查詢。
- 支援地圖／清單模式、Marker 選取、目前位置及停車格摘要。
- 公開 API 摘要新增 `distance_meters`，清單可顯示真實距離。
- 新增 Windows-safe API 啟動入口，避免 Uvicorn Proactor event loop 與 psycopg async 衝突。
- 新增淺色／深色模式切換，首次依系統偏好選擇，之後記住裝置設定。

### 驗證結果

- `npm run build` 成功，79 個模組完成 production build。
- API schema／endpoint 測試 8 passed。
- 真實 PostGIS：半徑 47 筆、viewport 76 筆、summary parking 47。

## 2026-08-01（本機 PostGIS 真實整合）

### 修改目的

建立本機 PostGIS、套用 migration、正式發布高雄停車場資料並驗證真實空間 API。

### 修改檔案

- `compose.yaml`
- `.env.example`
- `pyproject.toml`
- `backend/migrations/001_initial_postgis.sql`
- `backend/app/sources/downloader.py`
- `backend/app/db/publisher.py`
- `backend/app/cli/publish_parking_source.py`
- `backend/app/cli/verify_postgis_api.py`
- `backend/tests/test_tls_context.py`
- `README.md`
- `CHANGELOG_DEV.md`
- `IMPLEMENTATION_PLAN.md`

### 完成內容

- 啟動 `postgis/postgis:16-3.4` 本機容器，綁定 `127.0.0.1:54329` 與獨立 named volume。
- 套用初始 migration，啟用 PostGIS 3.4.3、pg_trgm 1.6 與 pgcrypto 1.3。
- 下載器改用 Windows 系統 CA store，未關閉 TLS 驗證。
- 成功下載 90,701 bytes 官方停車場 payload，保存 SHA-256 raw snapshot。
- 品質閘門通過：261 筆、0 筆無效座標。
- 正式 transaction 建立 data source、import run、raw import、261 筆 places 與 geography。
- geography 261 筆全部有效；緯度 22.22691–23.082862、經度 120.184924–120.587988。
- 將逐筆 upsert 改為批次 upsert，並支援從既有可信 snapshot idempotent 重跑。
- 修正 Windows `localhost` 偶發解析卡住，改用 `127.0.0.1` 與 5 秒 connect timeout。
- Windows async Postgres 驗證 CLI 使用 Selector event loop，符合 psycopg async 要求。

### 測試結果

- migration 成功；12 個 places／relations 必要索引存在。
- import run 狀態 `published`，downloaded／valid／published 均為 261，invalid 為 0。
- 半徑查詢：高雄中心 3 公里回傳 47 筆，HTTP 200。
- viewport 查詢回傳 76 筆，HTTP 200。
- nearby summary 回傳 parking 47，與半徑結果一致。
- 所有 API 結果都有 public ID，未暴露 database ID。
- 無條件 `/api/places` 與 `limit=501` 均回傳 HTTP 400。
- `pytest`：34 passed；Ruff 與 compileall 通過。

### 尚未完成

- migration 目前是單一 SQL，尚未建立 Alembic revision tracking。
- 尚未加入公廁等第二資料來源。
- 尚未建立 React／Leaflet 前端。
- 本機 PostGIS 容器目前保持啟動，以供後續前端與 API 開發。

### 下一步

專案已達到開始 React／Leaflet 頁面的條件；下一切片建立前端響應式分析面板、地圖、類別選擇、半徑與真實停車場 marker／清單。

## 2026-08-01（匯入與受限 API 階段）

### 修改目的

建立安全下載器、raw snapshot、staging 品質閘門、transaction 正式匯入邊界及受條件限制的 FastAPI 查詢端點。

### 修改檔案

- `backend/app/sources/config.py`
- `backend/app/sources/downloader.py`
- `backend/app/importers/snapshots.py`
- `backend/app/importers/quality.py`
- `backend/app/importers/pipeline.py`
- `backend/app/cli/validate_parking_source.py`
- `backend/app/db/models.py`
- `backend/app/db/publisher.py`
- `backend/app/db/read_repository.py`
- `backend/app/api/queries.py`
- `backend/app/api/repository.py`
- `backend/app/api/schemas.py`
- `backend/app/main.py`
- `backend/app/settings.py`
- `backend/migrations/001_initial_postgis.sql`
- `backend/tests/`
- `.env.example`
- `.gitignore`
- `README.md`

### 完成內容

- YAML 設定強制 HTTPS、host allowlist、逾時、最大下載量與品質門檻。
- 下載器解析 DNS 並拒絕 private、loopback、link-local 等非公開 IP；禁止未驗證 redirect，串流超限立即中止，拒絕非 JSON 回應。
- raw snapshot 以 SHA-256 content address 保存，採原子寫入且同內容不覆寫。
- staging 品質閘門檢查最小筆數、無效座標比例及與前版筆數變動比例；未通過不呼叫 publisher。
- SQLAlchemy publisher 在單一 transaction 建立 import run、raw import、upsert places、產生 geography 並停用來源中消失的紀錄。
- PostGIS read repository 使用 `ST_DWithin`、`ST_MakeEnvelope`、分類／行政區／關鍵字條件及公開 properties allowlist。
- FastAPI 建立 places、detail、categories、nearby-summary、search；無條件查詢、大半徑、大 viewport、過短 keyword 與超量 limit 均拒絕。
- 加入 CORS allowlist、request ID、統一 HTTP／validation 錯誤 JSON，以及環境控制 API docs。
- 新增安全演練 CLI，預設只驗證並保存 raw，不發布正式資料。

### 測試結果

- `pytest`：33 passed。
- `ruff check backend`：通過。
- `compileall backend`：通過。
- `.env.example` 解析通過。
- 真實高雄 API 曾以 PowerShell 驗證 HTTP 200；新 Python CLI 在本機因 CA／OpenSSL 信任鏈問題安全失敗，沒有關閉 TLS 驗證或寫入不可信 snapshot。

### 尚未完成

- 尚無可用 PostgreSQL／PostGIS 連線，因此 migration、transaction publisher 與 PostGIS SQL 尚未做實際資料庫整合測試。
- 尚未建立 Alembic runtime 與失敗 import run 的獨立持久化機制。
- 尚未加入多執行個體適用的 Redis rate limit；目前只完成查詢條件與回傳量限制。
- FastAPI TestClient 由 Starlette 回報 `httpx` 即將遷移至 `httpx2` 的相依套件警告，不影響本次測試。

### 下一步

取得 Supabase／本機 PostGIS 測試連線，套用 migration，完成真正的停車場 dry-run → publish → viewport／半徑查詢整合測試；成功後開始 React／Leaflet 頁面骨架。

## 2026-08-01（資料核心第一切片）

### 修改目的

將「主類別＋政府特有屬性＋跨資料集關聯證據」落成可測試的第一個後端資料核心。

### 修改檔案

- `.gitignore`
- `.env.example`
- `pyproject.toml`
- `README.md`
- `backend/app/domain/models.py`
- `backend/app/services/coordinates.py`
- `backend/app/services/relations.py`
- `backend/app/importers/parking.py`
- `backend/app/api/schemas.py`
- `backend/migrations/001_initial_postgis.sql`
- `backend/tests/test_coordinates.py`
- `backend/tests/test_parking_normalizer.py`
- `backend/tests/test_relations.py`
- `backend/tests/test_api_schemas.py`
- `data_sources/parking_kaohsiung.yaml`
- `docs/decisions/0001-place-attributes-and-evidence-relations.md`

### 完成內容

- 建立 Python 後端套件與開發依賴設定。
- 建立六類設施、座標可信度、關聯類型及證據方法的領域模型。
- 實作 WGS84 台灣合理範圍驗證與 Haversine 距離。
- 實作高雄公有停車場正規化，支援 `-` 場名的上一場站分區繼承、穩定 external ID 與特殊屬性。
- 實作停車場與機車充電站的同址／附近關聯；公開文字不把推定關聯冒充官方場內設施。
- 建立安全公開摘要 schema，禁止額外內部欄位。
- 建立 raw imports、import runs、places、place relations 及 PostGIS／文字索引初始 SQL。
- 建立停車場 YAML 來源設定、下載 allowlist、大小／逾時限制與品質閘門。
- 以 ADR 記錄統一 places、JSONB 特殊屬性與證據式關聯的設計理由。

### 測試結果

- `pytest`：10 passed，核心模組總覆蓋率 96%。
- `ruff check backend`：通過。
- `compileall backend`：通過。
- 停車場 YAML 可解析，資料集 ID、官方 host allowlist 與欄位映射檢查通過。

### 尚未完成

- 尚未建立 FastAPI application、SQLAlchemy models、Alembic 執行環境或實際 PostgreSQL 資料庫。
- 尚未實作安全 downloader、raw snapshot、staging transaction 與正式匯入 CLI。
- 機車充電資料尚未地理編碼，因此目前只有關聯模型，沒有正式關聯結果。
- 尚未建立 React／Leaflet 前端。

### 下一步

建立設定載入器與 SSRF-safe downloader，實際抓取停車場 payload 至 raw snapshot，通過品質閘門後寫入 staging；接著建立 SQLAlchemy model 與 FastAPI 的受限查詢骨架。

## 2026-08-01（Asia/Taipei）

### 修改目的

正式啟動專案前的資料來源實測與頁面配置規劃。

### 修改檔案

- `DATA_SOURCE_REVIEW.md`
- `PAGE_LAYOUT_PLAN.md`
- `IMPLEMENTATION_PLAN.md`
- `CHANGELOG_DEV.md`

### 完成內容

- 實際連線驗證六個高雄市政府 JSON 端點，皆回應 HTTP 200。
- 計算回應筆數、欄位、地址缺值、座標合理性、重複群組與明顯字元問題。
- 確認停車場為第一來源、公廁為第二來源；AED 與藥局作為地理編碼後的第三、第四類。
- 發現醫療與公廁均恰好回傳 1,000 筆且無分頁資訊，標記為疑似截斷。
- 完成桌機／手機首頁、設施詳情、資料來源頁、路由、元件、互動流程、狀態、API 對應與無障礙基線。

### 測試結果

- 停車場 261 筆，座標合理性檢查 0 筆異常；6 筆場名為 `-`，需做分區繼承。
- 公廁回應 1,000 筆，841 筆座標可信、159 筆缺少或異常；存在共址與重複紀錄。
- AED 875 筆、藥局 955 筆、醫療 1,000 筆、機車充電 136 筆；本次地址必填欄位皆無空白。
- 藥局資料有 12 筆包含 `?` 字元；醫療有 39 個科別欄位；機車充電沒有汽車接頭、功率或即時狀態。

### 尚未完成

- 尚未找到醫療與公廁完整資料的分頁或下載方式。
- 尚未決定地址地理編碼供應者與汽車充電資料來源。
- 尚未建立前後端程式碼；本次交付為可開發規格與資料決策。

### 下一步

建立 monorepo 骨架、PostGIS Schema 與停車場來源 YAML，先完成停車場 downloader → staging → places 的垂直切片及測試。

## 2026-07-20 20:12（Asia/Taipei）

### 修改目的

依專案公版 DOCX 製作「生活機能探索地圖」事前企畫書，不進入網站實作。

### 修改檔案

- `生活機能探索地圖_事前企畫書.docx`
- `CHANGELOG_DEV.md`

### 完成內容

- 保留 `專案企劃書＿公版.docx` 原檔不變，沿用其 A4 版面、章節結構與時程表。
- 填入專案主題、動機、目標、使用者、政府資料候選、MVP 範圍、技術與資料架構、安全要求、風險、驗收條件及八週規劃。
- 未知的執行者、諮詢講師與部署決策保留為待填／待確認，未自行杜撰。
- 修正公版原有 Heading 1 直接跳至 Heading 3 的層級問題。

### 測試結果

- DOCX 封裝測試通過，1 個 A4 章節、34 個段落、1 張 13×3 時程表且無空白儲存格。
- 無障礙檢查為 high 0、medium 0、low 0。
- 原始公版 SHA-256 維持 `68F1AED477CEBADAB74D0A9E9F7B3158B4D84DA55C508C8A293E1DECAF3D47DF`。
- 本機缺少 LibreOffice／soffice，無法執行 DOCX 頁面 PNG 渲染檢查；已依文件技能備援規則完成結構 QA。

### 尚未完成

- 執行者與諮詢講師姓名尚待填寫。
- 八週時程目前以週次表示，待確認實際起訖日後可換成日期。

### 下一步

由使用者確認企畫內容、姓名與實際日期；確認前不進行網站開發。

## 2026-07-20 20:15（Asia/Taipei）

### 修改目的

獨立核驗第一階段文件引用的政府資料目錄，避免沿用未經本次工作確認的分析結論。

### 修改檔案

- `IMPLEMENTATION_PLAN.md`
- `CHANGELOG_DEV.md`

### 完成內容

- 重新定位並以唯讀方式開啟 `C:\Users\User\Downloads\export1784468586.csv`。
- 直接檢查檔案 BOM、欄位名稱、資料筆數與高雄／全國候選資料列。
- 補記原始檔修改時間、第二種 CSV 解析方式及候選人工排除原則。
- 再次確認工作區只有兩份規劃文件，沒有可沿用或應避免覆蓋的應用程式碼。

### 測試結果

- BOM 為 `EF BB BF`，即 UTF-8 with BOM。
- PowerShell `Import-Csv -Encoding utf8` 成功解析 53,207 筆、22 欄，與原文件的 Python `csv.DictReader` 結果一致。
- 停車、公廁、AED、藥局、醫療院所與充電站短名單中的資料集 ID 均可在目錄中找到。
- `git status --short` 顯示兩份文件皆為未追蹤檔案；未修改或刪除其他功能。

### 尚未完成

- 尚未連線驗證任何候選資料端點，也未下載候選資料內容。
- 地址／經緯度判定仍以目錄 metadata 為依據，須在下一階段抽樣驗證 payload。

### 下一步

受限探查資料集 46944 的官方 JSON/CSV 端點，驗證實際 schema、座標與資料量後，再建立第一個來源設定與匯入測試。

## 2026-07-20 20:00（Asia/Taipei）

### 修改目的

完成「生活機能探索地圖」第一階段的專案盤點、政府資料目錄分析、候選資料評估與實作設計。

### 修改檔案

- `IMPLEMENTATION_PLAN.md`
- `CHANGELOG_DEV.md`

### 完成內容

- 確認儲存庫目前為無 commit、無追蹤檔案的空白專案。
- 確認未發現 `README.md`、`AGENTS.md` 或 `agent.md`，沒有既有架構可沿用。
- 定位並分析 `C:\Users\User\Downloads\export1784468586.csv`。
- 確認 CSV 為 UTF-8 with BOM、22 欄、53,207 筆資料。
- 盤點六類高雄優先候選，記錄格式、URL、地址/座標可用性、授權、更新頻率與風險。
- 建議以「高雄市公有路外停車場一覽表」（ID 46944）作為第一個完整匯入流程；公廁高雄明細（ID 34868）為失敗切換來源。
- 提出 raw、staging、unified、analysis 三層資料模型、PostGIS 索引、API 防護、前端頁面與分階段驗收條件。

### 測試結果

- 使用 Python `csv.DictReader` 完整走訪 CSV 成功，共讀取 53,207 筆。
- UTF-8/UTF-8-SIG 完整解碼成功；CP950 與 Big5 完整解碼失敗，符合 UTF-8 BOM 判定。
- Git 與檔案盤點成功；未對外下載任何候選資料。
- 本階段只有 Markdown 文件，無可執行程式、migration、前端 build 或單元測試可執行。

### 尚未完成

- 尚未驗證候選官方端點的 HTTP 狀態、實際 payload、筆數與欄位。
- 尚未建立應用程式骨架、資料庫 migration、匯入器、API 或前端。
- 尚未確定批次地址地理編碼與電動汽車充電站的合規資料來源。

### 下一步

只針對 ID 46944 進行受限端點探查與小規模下載，確認 schema 與座標後建立第一個 YAML mapping、匯入垂直切片及測試；若來源不可用則改用 ID 34868。
