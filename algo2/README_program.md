# algo2 - 中間地点推薦システム

2地点間の中間地点、または矩形範囲内の施設を検索・保存できるWebアプリケーションです。

## 起動方法

### フロントエンド (Next.js)
`/frontend` ディレクトリで:

```powershell
# 依存関係インストール（pnpm 推奨）
pnpm install

# 開発サーバー起動 (http://localhost:3000)
pnpm dev
```

npm を使う場合:
```powershell
npm install
npm run dev
```

### バックエンド (FastAPI)
`/backend` ディレクトリで:

```powershell
# 仮想環境作成・有効化（初回のみ）
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# 依存関係インストール
pip install fastapi uvicorn[standard] requests rtree pyyaml

# サーバー起動 (http://localhost:8000)
uvicorn main:app --reload --port 8000
```

**起動後**: http://localhost:3000 を開く

## 主な機能

### 1. 検索モード
- **中間地点モード**: 2地点(A・B)の中間地点付近の施設を最大10件推薦
- **矩形(BBOX)モード**: 2地点を中心に指定した幅・高さの矩形範囲内の施設を**全件**取得

### 2. 検索結果の保存
- **JSON保存** / **YAML保存**ボタンで検索結果をサーバーに保存
- ファイル名に件数を含む（例: `bbox_20408items_20251101T112006.json`）
- 保存先: `backend/data/`（Git管理外）
- 保存時にトーストと画面に件数を表示

### 3. 保存データの管理
バックエンドAPI経由で保存済みファイルを操作:
- **一覧取得**: `GET http://127.0.0.1:8000/data/list`
- **ファイル取得**: `GET http://127.0.0.1:8000/data/{filename}`
  - 例: `http://127.0.0.1:8000/data/bbox_20408items_20251101T112006.json`

### 4. 地図表示
- **ベースマップ切替**: OpenStreetMap / 地理院地図
- **鉄道レイヤー**: ON/OFF切替可能
- **クラスタリング**: BBOX時は大量マーカーを自動クラスタ化（地図が軽快）
- **ドラッグ操作**: 地図上のA・Bマーカーをドラッグで移動 → 自動再検索

### 5. URL共有
- 検索条件（座標・カテゴリ・モード等）がURLクエリに自動反映
- URLをコピーして共有すれば、同じ検索条件を復元可能

## API エンドポイント

### 検索API
- `GET /recommend` - 中間地点推薦（最大10件）
  - パラメータ: `lat1`, `lon1`, `lat2`, `lon2`, `category`
  - オプション: `save=true`, `fmt=json|yaml`, `name=カスタム名`
- `GET /search_bbox` - 矩形範囲検索（全件）
  - パラメータ: `lat1`, `lon1`, `lat2`, `lon2`, `category`, `width_m`, `height_m`
  - オプション: `save=true`, `fmt=json|yaml`, `name=カスタム名`

### 保存データAPI
- `POST /data/save` - 任意のJSONを保存
  - Body: `{ data: {...}, format: "json"|"yaml", name: "ファイル名" }`
- `GET /data/list` - 保存済みファイル一覧
- `GET /data/{file}` - 保存済みファイルの取得

### その他
- `GET /docs` - API仕様（Swagger UI）

## 保存ファイルの読み取り例

Pythonで保存されたJSONを読み込む:

```python
import json

with open("backend/data/bbox_20408items_20251101T112006.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"検索タイプ: {data['type']}")
print(f"件数: {len(data['result']['recommendations'])}")
for item in data['result']['recommendations'][:5]:  # 最初の5件
    print(f"  {item['name']} ({item['lat']}, {item['lon')})")
```

YAMLの場合:
```python
import yaml

with open("backend/data/bbox_20408items_20251101T112006.yaml", "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)
```

## 注意事項
- `backend/data/` ディレクトリはGit管理外（.gitignore に追加済み）
- rtree のインストールで失敗する場合はPythonバージョンを確認してください
- BBOX時は件数制限なしのため、広範囲指定では取得に時間がかかる場合がある．
