# AGENTS.md

## Project overview

「生活機能探索地圖」是以臺灣政府開放資料為核心的互動地圖。前端使用
React 19、Vite、TypeScript、Leaflet；後端使用 FastAPI、SQLAlchemy、
PostgreSQL/PostGIS。資料流程包含安全下載、raw snapshot、正規化、品質閘門、
transactional publish 與空間查詢。

這不是純前端專案。若移入另一個 repository，必須一併保留 `backend/`、
`data_sources/`、`compose.yaml` 與 migration，或讓新前端連到獨立部署的 FastAPI。

## Repository layout

- `frontend/`: React/Vite UI，主要入口為 `src/App.tsx`。
- `backend/app/main.py`: FastAPI 路由與 runtime app。
- `backend/app/domain/`: 共用 Place、分類、座標準確度與關聯模型。
- `backend/app/importers/`: 各來源正規化、snapshot、品質檢查與 pipeline。
- `backend/app/sources/`: YAML source config、安全下載及 TDX client。
- `backend/app/db/`: SQLAlchemy publisher 與 PostGIS read repository。
- `backend/app/cli/`: 資料發布與驗證命令。
- `backend/migrations/001_initial_postgis.sql`: 目前唯一 schema migration。
- `backend/tests/`: 不連網單元與 API 測試。
- `data_sources/`: 官方資料來源 YAML 設定。
- `docs/decisions/`: 架構決策；不要在未讀取 ADR 前改變資料語意。

## Current handoff state

- 全國公廁已發布約 45,720 筆。
- 全國 AED 已發布約 15,718 筆；無效座標資料保留稽核但不上圖。
- 全國公共飲水機已發布 4,767 筆，只納入來源明確標示有飲水機的點位。
- 全國避難收容處所已發布 5,973 筆。
- 高雄停車場已可查詢；TDX 全國停車場與即時剩餘車位轉接器已完成，但必須由
  使用者提供 `TDX_CLIENT_ID` 與 `TDX_CLIENT_SECRET` 才能發布。
- 醫療院所與藥局中央清冊缺少全國一致的官方座標，目前按鈕維持停用；在完成
  可稽核的批次地理編碼前，不得把地址資料假裝成精準地圖標記。
- 前端已具備深淺色、縣市切換、目前位置、行政區判定、半徑與 viewport 查詢、
  地址/地標搜尋、標記聚合、清單、進階篩選、收藏、最近瀏覽、導航與分享狀態。
- repository 已初始化 Git，但尚無 commit、GitHub remote 或 CI/CD。

## Initial setup (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
Set-Location frontend
npm install
```

Python 需求為 3.12 以上。前端目前已有 `pnpm-lock.yaml`；保留既有 lockfile，
不要在沒有理由時更換 package manager 或重建專案骨架。

## Database setup

```powershell
docker compose -p livability-map -f compose.yaml up -d postgis
docker compose -p livability-map -f compose.yaml exec -T postgis `
  psql -v ON_ERROR_STOP=1 -U livability -d livability_map `
  -f /migrations/001_initial_postgis.sql
```

本機預設連線為：

```text
postgresql+psycopg://livability:local_dev_only@127.0.0.1:54329/livability_map?connect_timeout=5
```

這組帳密只允許本機容器。停止資料庫使用
`docker compose -p livability-map -f compose.yaml stop postgis`。不要執行
`docker compose down -v`，除非使用者明確同意刪除 PostGIS volume。

## Development workflow

啟動 API：

```powershell
$env:DATABASE_URL='postgresql+psycopg://livability:local_dev_only@127.0.0.1:54329/livability_map?connect_timeout=5'
python backend/run_api.py
```

API 預設位於 `http://127.0.0.1:8000`。另開終端機啟動前端：

```powershell
Set-Location frontend
npm run dev
```

Vite 預設位於 `http://127.0.0.1:5173`，並將 `/api` 代理到 8000。部署時使用
`VITE_API_BASE_URL` 指向 FastAPI origin。若 API 回傳空資料，先確認啟動 API 的
process 確實帶有 `DATABASE_URL`，不要以假資料掩蓋連線問題。

## Tests and required checks

從 repository root 執行：

```powershell
pytest
python -m ruff check backend
Set-Location frontend
npm run typecheck
npm run build
```

目前完整後端測試基準為 39 passed。新增或修改 normalizer、公開 schema、query
驗證或 downloader 時必須補測試。前端目前沒有獨立測試 runner，`npm run build`
同時執行 TypeScript compilation，必須通過。

## Data publishing

所有 CLI 從 repository root 執行，並先設定：

```powershell
$env:PYTHONPATH=(Resolve-Path '.\backend').Path
$env:DATABASE_URL='postgresql+psycopg://livability:local_dev_only@127.0.0.1:54329/livability_map?connect_timeout=5'
```

主要命令：

```powershell
python -m app.cli.publish_parking_source
python -m app.cli.publish_national_sources
python -m app.cli.publish_amenities
python -m app.cli.verify_postgis_api
```

TDX 指定縣市發布範例：

```powershell
python -m app.cli.publish_tdx_parking Taipei
python -m app.cli.publish_tdx_parking NewTaipei
```

正式發布只能在下載、snapshot 與品質閘門成功後執行。保留 `city`、`district`、
WGS84 座標、`category` 與 `properties` 的共用模型；新增來源通常不需要重做網站或
建立分類專用資料表。

## Data and API invariants

- 未通過臺灣 WGS84 範圍驗證的資料不得建立 `geom` 或顯示為地圖標記。
- `GET /api/places` 必須有 viewport、中心點加半徑、城市/行政區或至少兩字關鍵字。
- 半徑上限 3 公里、viewport 經緯跨度上限 0.5 度、回傳上限 500 筆。
- 公開 API 只能輸出 `PUBLIC_PROPERTY_KEYS` allowlist 中的 properties。
- 不公開 raw payload、內部資料庫 ID、秘密下載 URL 或藥局負責人個資。
- 「附近有充電」或「同址有充電」不得改寫成「場內提供充電」。
- 資料來源停用或替換時，避免同一設施重複顯示；全國公廁/AED 已取代高雄限定來源。
- 行政區與地標服務失敗時要保留可理解的 fallback，不得讓中心座標退回 `(0, 0)`。

## Security boundaries

- `.env`、TDX credentials、production DB URL 與任何 API secret 不得 commit 或送到前端。
- raw snapshots 位於 `data/raw/` 且已 gitignore；不要提交大型政府原始檔。
- 下載器必須使用 HTTPS、host allowlist、公開 IP 檢查、大小限制、timeout 與系統 CA。
- 禁止以 `verify=False`、停用 hostname validation 或任意跟隨 redirect 解決下載問題。
- 新增公開 properties 時，同步更新 Pydantic schema/TypeScript type、allowlist 與測試。

## Code style and editing

- Python 使用 100 字元行長、Python 3.12 typing、Ruff 規則 `E,F,I,UP,B,ANN`。
- FastAPI response 使用 Pydantic model；不要直接回傳 SQLAlchemy row 或 raw JSON。
- normalizer 接受來源 row 並輸出 `PlaceDraft`，不要在前端補救來源資料語意。
- React 使用 function components、hooks 與既有 CSS variables；維持淺色/深色及
  760px 手機 breakpoint。
- 地圖類別必須同步更新 `PlaceCategory`、API label、公開 property allowlist、前端
  `CategoryKey`、AnalysisPanel、MapView、PlaceList、DetailDrawer 與樣式。
- 修改公開資料語意或架構決策時更新 `docs/decisions/`；一般進度記錄於
  `CHANGELOG_DEV.md`。

## Git and handoff notes

- 上傳前確認 `.test-runs*`、`data/raw/`、`frontend/dist/`、`node_modules/`、logs 與
  `.env` 未被 staged。
- 不要複製 `.git/` 到另一個 repository。若整合進既有專案，優先使用子資料夾、
  monorepo package 或讓另一前端共用 FastAPI；避免複製兩份可獨立漂移的資料庫。
- 建立第一個 commit 前先執行完整 pytest、Ruff、typecheck 與 production build。
