# Render 與 Supabase 部署

本專案以兩個 Render service 與既有 `convenience-map` Supabase Postgres 專案組成：

```text
Render Static Site
  taiwan-livability-explorer-map
        |
        | VITE_API_BASE_URL
        v
Render Web Service
  taiwan-livability-explorer-map-api
        |
        | DATABASE_URL (Render secret)
        v
既有 convenience-map Supabase Postgres + PostGIS
```

`render.yaml` 預設將 Static Site 與 API Web Service 設為 free，避免自動增加費用。
free Web Service 可能在閒置後休眠，第一次 API 請求會較慢；若日後有流量或效能需求，
再由使用者主動升級即可。

## 1. 使用既有 convenience-map Supabase 專案

此部署刻意共用既有 `convenience-map` Supabase project，以維持 Free plan 成本為零。兩個
應用程式使用不同資料表：既有服務地圖使用 `brands`、`stores`、`services`、
`store_services`；本專案使用 `data_sources`、`import_runs`、`raw_imports`、`places`、
`place_relations`。

在 Supabase 的 SQL Editor 先執行下列唯讀檢查。預期結果應為 0 筆；若出現任何資料表，
先停止並確認該表不是其他系統正在使用：

```sql
select tablename
from pg_tables
where schemaname = 'public'
  and tablename in (
    'data_sources', 'import_runs', 'raw_imports', 'places', 'place_relations'
  );
```

確認沒有衝突後，在同一個 SQL Editor 開啟並執行：

```sql
-- 貼上 backend/migrations/001_initial_postgis.sql 的完整內容。
```

此 migration 會啟用 `postgis`、`pg_trgm`、`pgcrypto`，並建立本專案需要的資料表與索引。

## 2. 以 Blueprint 建立 Render services

1. 在 Render Dashboard 選擇 **New → Blueprint**。
2. 選擇 `e25044868/Livability_Explorer_Map` 的 `main` 分支。
3. Render 讀取 repository 根目錄的 `render.yaml` 後，會列出 Static Site 與 API Web Service。
4. 設定 API 的 `DATABASE_URL` secret：從 Supabase **Connect → Session pooler** 複製 URI，
   並將前綴 `postgresql://` 改成 `postgresql+psycopg://` 後貼入。
5. 確認服務名稱未被占用，再建立 Blueprint。

`DATABASE_URL` 僅能填入 Render 的 Environment 頁面，禁止放入 `.env.example`、
`render.yaml`、Git commit 或前端環境變數。

## 3. 發布可信資料

Render 初次部署只會建立網站與 API，不會自行下載或發布資料。完成 Supabase schema 後，
在本機將 `DATABASE_URL` 暫時設為既有 `convenience-map` 的同一個 Session Pooler URI，
再依資料來源執行既有 publish CLI。只有通過下載、snapshot 與品質閘門的資料才能發布。

## 4. 驗證

- 開啟 API 的 `/api/categories`，應回傳分類 JSON。
- 開啟 Static Site，確認能載入地圖與分類。
- API 無資料時，先檢查 Render `DATABASE_URL`、Supabase migration 與資料發布是否完成；
  不要用前端假資料掩蓋連線問題。

## 入口網站串接

Static Site 成功後，其網址會是：

```text
https://taiwan-livability-explorer-map.onrender.com
```

將此網址提供給便利商店／加油站入口網站，即可把輪播第 2 張卡片改為本專案的預覽與連結。
