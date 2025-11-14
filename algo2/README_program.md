# /frontendで
## 依存関係インストール（pnpm 推奨）
pnpm install

## 開発サーバー起動 (http://localhost:3000)
pnpm dev

### npm を使う場合:
npm install
npm run dev

# /backendで
## 依存関係インストール
pip install fastapi uvicorn[standard] requests rtree

## サーバー起動 (http://localhost:8000)
uvicorn main:app --reload --port 8000

↓↓↓

http://localhost:3000　
を開けばok

