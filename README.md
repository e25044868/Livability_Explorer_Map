# 生活機能探索地圖

整合政府公共設施資料，分析指定位置周圍是否同時具備停車場、公廁、AED、藥局、醫療院所與機車充電站。產品重點是判斷生活圈是否符合多項需求，不是複製一般店家地圖。

## 目前進度

- 已完成六類高雄官方資料來源實測與頁面配置規劃。
- 已建立安全下載、raw snapshot、停車場正規化、品質閘門、transaction publisher、設施關聯證據模型及 PostGIS Schema。
- 已建立受限 FastAPI 查詢端點與真正使用 PostGIS 空間函式的 read repository。
- 已完成 React／Vite／TypeScript／Leaflet 互動介面：全國公廁與 AED、縣市切換、定位判斷、停車場、半徑／viewport 查詢、搜尋、篩選、收藏、交集分析、詳細資訊及 Marker 聚合。

## 專案結構

```text
backend/
  app/domain/       統一資料與關聯模型
  app/importers/    正規化與資料來源匯入邏輯
  app/sources/      YAML 設定、SSRF 防護與有界下載
  app/db/           SQLAlchemy publisher 與 PostGIS 查詢 repository
  app/services/     座標與空間關聯服務
  app/api/          公開 API schema 邊界
  migrations/       PostgreSQL/PostGIS Schema
  tests/            不連網核心測試
frontend/           React、Vite、TypeScript 與 Leaflet 互動介面
data_sources/       YAML 資料來源設定
docs/decisions/     架構決策紀錄
```

## 本機準備

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
pytest
```

## 本機 PostGIS

啟動隔離的 PostGIS 16／PostGIS 3.4 測試資料庫：

```powershell
docker compose -p livability-map -f compose.yaml up -d postgis
docker compose -p livability-map -f compose.yaml exec -T postgis `
  psql -v ON_ERROR_STOP=1 -U livability -d livability_map `
  -f /migrations/001_initial_postgis.sql
```

本機連線：

```text
postgresql+psycopg://livability:local_dev_only@127.0.0.1:54329/livability_map?connect_timeout=5
```

此帳密只供綁定 `127.0.0.1:54329` 的本機開發容器，不得用於部署環境。

安全下載並保存 raw snapshot：

```powershell
$env:PYTHONPATH=(Resolve-Path '.\backend').Path
python -m app.cli.validate_parking_source
```

正式發布最新來源，或從既有可信 snapshot 重跑：

```powershell
$env:DATABASE_URL='postgresql+psycopg://livability:local_dev_only@127.0.0.1:54329/livability_map?connect_timeout=5'
python -m app.cli.publish_parking_source
python -m app.cli.publish_parking_source --snapshot <raw-json-path>
python -m app.cli.publish_toilet_source
python -m app.cli.publish_national_sources
```

全國公廁與 AED 發布成功後，匯入程式會停用高雄限定的同類來源，避免重複顯示。

TDX 停車場需先在 `.env` 設定 `TDX_CLIENT_ID` 與 `TDX_CLIENT_SECRET`，再依 TDX 英文縣市代碼發布：

```powershell
python -m app.cli.publish_tdx_parking Taipei
python -m app.cli.publish_tdx_parking NewTaipei
```

發布器會同步取得停車場基本資料與即時剩餘車位，並以 `CarParkID` 合併總車位、
剩餘車位、營業時間、費率、充電／無障礙／親子車位、限高與月租欄位。
定位後的縣市／行政區使用國土測繪中心單一座標行政區服務判定；搜尋框則會
合併既有設施以及臺灣地址、地標結果。

轉接器使用 OAuth client credentials，金鑰只存在後端環境變數，不會送到瀏覽器。

執行真實 PostGIS 半徑、viewport、摘要與 API 防護驗證：

```powershell
python -m app.cli.verify_postgis_api
```

停止容器但保留資料：

```powershell
docker compose -p livability-map -f compose.yaml stop postgis
```

不要隨意使用 `down -v`，因為 `-v` 會刪除本機測試資料 volume。

啟動 API：

```powershell
$env:DATABASE_URL='postgresql+psycopg://livability:local_dev_only@127.0.0.1:54329/livability_map?connect_timeout=5'
python backend/run_api.py
```

`backend/run_api.py` 會在 Windows 使用 psycopg async 相容的 Selector event loop。

啟動前端（另開一個終端機）：

```powershell
Set-Location frontend
npm install
npm run dev
```

開啟 `http://127.0.0.1:5173`。Vite 開發伺服器會將 `/api` 代理到 `http://127.0.0.1:8000`；部署時可用 `VITE_API_BASE_URL` 指定 API origin。正式建置使用 `npm run build`。

安全下載並驗證停車場來源，但不發布正式資料：

```powershell
$env:PYTHONPATH=(Resolve-Path '.\backend').Path
python -m app.cli.validate_parking_source
```

下載器透過 `truststore` 使用 Windows 系統 CA store，同時保留憑證與 hostname 驗證；不得使用 `verify=False`。

目前 `backend/migrations/001_initial_postgis.sql` 是可審查的初始 SQL，尚未建立 Alembic runtime。正式發布需先套用 Schema 並設定 `DATABASE_URL`。

## API 查詢限制

- `GET /api/places` 必須提供 viewport、中心點＋半徑、城市／行政區或至少 2 字元的關鍵字。
- 半徑最高 3 公里，viewport 經緯跨度最高 0.5 度。
- 預設 300 筆、最高 500 筆；`GET /api/search` 最高 100 筆。
- `GET /api/categories`、`GET /api/places/{public_id}`、`GET /api/nearby-summary` 與 `GET /api/search` 已建立。
- production 可用 `ENABLE_API_DOCS=false` 關閉 docs、redoc 與 OpenAPI。
- CORS 只接受 `CORS_ALLOWED_ORIGINS` allowlist；錯誤回應與 `X-Request-ID` 使用一致格式。

## 全國生活設施

- 飲水機使用環境部 `GIS_P_82` 涼適點資料，只發布 `waterdispenser=1` 且通過座標檢查的點位。
- 避難收容處所使用消防署全國點位檔，公開容量、適用災害、室內外與弱者安置資訊。
- 重新發布：`python -m app.cli.publish_amenities`。
- 中央醫療院所與藥局清冊目前只有地址、沒有全國一致的官方座標；在完成可稽核的批次地理編碼前不會假裝成精準地圖點位。

## 文件

- `DATA_SOURCE_REVIEW.md`：官方端點實測與品質決策。
- `PAGE_LAYOUT_PLAN.md`：桌機／手機資訊架構與互動規格。
- `IMPLEMENTATION_PLAN.md`：整體實作計畫。
- `docs/decisions/0001-place-attributes-and-evidence-relations.md`：統一地點與關聯證據模型決策。
- `docs/DEPLOYMENT_RENDER.md`：Render Static Site、FastAPI Web Service 與既有 convenience-map Supabase PostGIS 的部署流程。

## 重要資料規則

- 未通過座標驗證的資料不上圖。
- 「同址有充電」與「附近有充電」不得宣稱為「場內提供充電」。
- 充電資料目前只涵蓋電動機車，公開名稱使用「機車充電」。
- 藥局負責人姓名不進公開 API。
- 原始資料、內部流水號及秘密 URL 不進公開 schema。
