# Q-Storm Platform

小売店舗データ分析プラットフォーム（Phase 1 + Phase 2A + Phase 2B + Phase 2C）

## 概要

Q-Storm Platformは、小売店舗の売上データを分析するためのFlaskベースのAPIプラットフォームです。
時系列分析、ヒストグラム分析、パレート分析（ABC分類）などの統計分析機能を提供します。

## 実装済み機能

### Phase 1: コア分析機能
- ✅ 時系列分析（/api/v1/analysis/timeseries）
- ✅ ヒストグラム分析（/api/v1/analysis/histogram）
- ✅ パレート分析（/api/v1/analysis/pareto）
- ✅ CORS設定（React frontend対応）
- ✅ レート制限（30req/min per endpoint）
- ✅ 環境変数検証

### Phase 2A: データベース永続化
- ✅ SQLiteデータベース統合
- ✅ セッション管理
- ✅ 分析結果の保存・取得
- ✅ 履歴API（/api/v1/history/session/<session_id>）

### Phase 2B: Markdownエクスポート
- ✅ 単一分析結果のMarkdownエクスポート（/api/v1/export/markdown/<analysis_id>）
- ✅ セッション全体のMarkdownエクスポート（/api/v1/export/session/<session_id>）
- ✅ 3つの分析タイプ対応（timeseries, histogram, pareto）

### Phase 2C: API認証
- ✅ 環境変数ベースのAPIキー認証
- ✅ 開発/本番環境の自動切り替え
- ✅ シンプルな認証ミドルウェア
- ✅ セキュリティエラーハンドリング（401, 403, 500）

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

```bash
# .env.example をコピーして .env を作成
cp .env.example .env

# .env ファイルを編集
nano .env
```

#### 開発環境（デフォルト）

```bash
FLASK_ENV=development
# 開発環境では認証は自動的にスキップされます
```

#### 本番環境

```bash
FLASK_ENV=production

# APIキーを生成
python3 -c "from auth import generate_api_key; print(generate_api_key())"
# 出力例: Xa7K9mP3nQ2vR8tY5wZ1aB4cD6eF0gH2iJ4kL6mN8oP0

# 生成されたAPIキーを設定
QSTORM_API_KEY=Xa7K9mP3nQ2vR8tY5wZ1aB4cD6eF0gH2iJ4kL6mN8oP0
```

### 3. データベース初期化

データベースは初回起動時に自動的に作成されます。

```bash
python3 app_improved.py
```

### 4. サンプルデータの準備

```bash
# テストデータ生成
python3 tests/generate_test_data.py

# uploads/session_test_integration/test_data.csv が生成されます
# - 2店舗（恵比寿、横浜元町）
# - 365日分のデータ
# - 41列の小売店舗データスキーマ
```

## Phase 2C: API認証

### 開発環境

開発環境（`FLASK_ENV=development`）では認証は**不要**です。
すべてのエンドポイントに認証なしでアクセスできます。

```bash
# 開発環境での起動
export FLASK_ENV=development
python3 app_improved.py

# 認証なしでアクセス可能
curl -X POST http://localhost:5000/api/v1/analysis/timeseries \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "metric": "売上金額", "time_unit": "月"}'
```

### 本番環境

本番環境（`FLASK_ENV=production`）では認証が**必須**です。

#### APIキー生成

```bash
python3 -c "from auth import generate_api_key; print(generate_api_key())"
# 出力: Xa7K9mP3nQ2vR8tY5wZ1aB4cD6eF0gH2iJ4kL6mN8oP0
```

#### 環境変数設定

```bash
export FLASK_ENV=production
export QSTORM_API_KEY="Xa7K9mP3nQ2vR8tY5wZ1aB4cD6eF0gH2iJ4kL6mN8oP0"
```

#### APIリクエスト例

すべての分析・エクスポートエンドポイントには `X-API-Key` ヘッダーが必要です。

```bash
# 時系列分析（認証あり）
curl -X POST http://localhost:5000/api/v1/analysis/timeseries \
  -H "Content-Type: application/json" \
  -H "X-API-Key: Xa7K9mP3nQ2vR8tY5wZ1aB4cD6eF0gH2iJ4kL6mN8oP0" \
  -d '{
    "session_id": "session_001",
    "metric": "売上金額",
    "time_unit": "月",
    "store": "恵比寿"
  }'

# Markdownエクスポート（認証あり）
curl -X GET http://localhost:5000/api/v1/export/markdown/1 \
  -H "X-API-Key: Xa7K9mP3nQ2vR8tY5wZ1aB4cD6eF0gH2iJ4kL6mN8oP0" \
  -o analysis_report.md
```

#### 認証エラーレスポンス

**401 Unauthorized** - APIキーが提供されていない場合

```json
{
  "success": false,
  "error": "API key required",
  "message": "Include X-API-Key header in your request",
  "code": "AUTH_MISSING_API_KEY"
}
```

**403 Forbidden** - 無効なAPIキーが提供された場合

```json
{
  "success": false,
  "error": "Invalid API key",
  "message": "The provided API key is not valid",
  "code": "AUTH_INVALID_API_KEY"
}
```

**500 Internal Server Error** - サーバー側でAPIキーが未設定の場合

```json
{
  "success": false,
  "error": "Server configuration error",
  "message": "API key not configured on server",
  "code": "AUTH_SERVER_CONFIG_ERROR"
}
```

### セキュリティのベストプラクティス

1. **HTTPS環境での使用**
   - 本番環境では必ずHTTPS環境で運用してください
   - APIキーは平文で送信されるため、HTTPでは盗聴のリスクがあります

2. **APIキーの管理**
   - APIキーをコードにハードコードしないでください
   - 環境変数または秘密管理サービス（AWS Secrets Manager等）を使用してください
   - `.env` ファイルは `.gitignore` に追加してください

3. **APIキーのローテーション**
   - 定期的にAPIキーを再生成してください
   - 漏洩の疑いがある場合は即座に更新してください

4. **アクセスログの監視**
   - 401/403エラーの頻度を監視してください
   - 異常なアクセスパターンを検出してください

## API仕様

### 分析エンドポイント

#### POST /api/v1/analysis/timeseries

時系列分析を実行します。

**リクエスト:**
```json
{
  "session_id": "session_001",
  "metric": "売上金額",
  "time_unit": "月",
  "store": "恵比寿"
}
```

**レスポンス:**
```json
{
  "success": true,
  "analysis_id": 42,
  "session_id": "session_001",
  "execution_time": 0.234,
  "chart": { "data": [...], "layout": {...} },
  "statistics": {
    "sum": 12345678,
    "mean": 456789,
    "max": 987654,
    "min": 123456,
    "std": 234567,
    "count": 27
  }
}
```

#### POST /api/v1/analysis/histogram

ヒストグラム分析を実行します。

**リクエスト:**
```json
{
  "session_id": "session_001",
  "metric": "売上金額",
  "bins": 20,
  "store": "横浜元町"
}
```

#### POST /api/v1/analysis/pareto

パレート分析（ABC分類）を実行します。

**リクエスト:**
```json
{
  "session_id": "session_001",
  "metric": "売上金額",
  "category_column": "Mens_KNIT",
  "top_n": 20,
  "store": "恵比寿"
}
```

**レスポンス:**
```json
{
  "success": true,
  "analysis_id": 43,
  "abc_classification": {
    "A": {"count": 5, "percentage": 25.0},
    "B": {"count": 3, "percentage": 15.0},
    "C": {"count": 12, "percentage": 60.0}
  },
  "statistics": {
    "total_categories": 20,
    "total_value": 9876543,
    "categories_for_80_percent": 5,
    "ratio_for_80_percent": 25.0
  }
}
```

### エクスポートエンドポイント

#### GET /api/v1/export/markdown/<analysis_id>

単一の分析結果をMarkdown形式でエクスポートします。

**レスポンス:**
- Content-Type: `text/markdown; charset=utf-8`
- Content-Disposition: `attachment; filename="analysis_{id}.md"`

#### GET /api/v1/export/session/<session_id>

セッション全体の分析結果をMarkdown形式でエクスポートします。

**レスポンス:**
- Content-Type: `text/markdown; charset=utf-8`
- Content-Disposition: `attachment; filename="session_{session_id}.md"`

### 履歴エンドポイント（認証不要）

#### GET /api/v1/history/session/<session_id>

セッションの分析履歴を取得します。

#### GET /api/v1/history/recent?limit=50&type=timeseries

最近の分析結果を取得します。

## テスト

### 統合テスト（Phase 1 + Phase 2A）

```bash
python3 tests/test_integration.py
```

**テスト内容:**
- データベース初期化
- セッション管理
- 分析結果保存・取得
- テストデータ生成

### Markdownエクスポートテスト（Phase 2B）

```bash
python3 tests/test_markdown_export.py
```

**テスト内容:**
- 単一分析結果エクスポート
- セッション全体エクスポート
- エラーハンドリング
- ファイル出力

### 認証テスト（Phase 2C）

```bash
python3 tests/test_auth.py
```

**テスト内容:**
- APIキーなしでアクセス → 401
- 無効なAPIキー → 403
- 有効なAPIキー → アクセス可能
- 開発環境で認証スキップ
- APIキー生成機能

## プロジェクト構成

```
Q-Sorm-Project-α/
├── app_improved.py              # メインFlaskアプリケーション
├── auth.py                      # Phase 2C: API認証
├── db_manager.py                # Phase 2A: データベース管理
├── export_manager.py            # Phase 2B: Markdownエクスポート
├── config.py                    # 環境変数・設定管理
├── requirements.txt             # Python依存パッケージ
├── .env.example                 # 環境変数テンプレート
├── README.md                    # このファイル
├── data/
│   └── qstorm.db               # SQLiteデータベース
├── uploads/                     # アップロードファイル格納
├── outputs/                     # エクスポートファイル出力
└── tests/
    ├── test_integration.py     # Phase 1+2A 統合テスト
    ├── test_markdown_export.py # Phase 2B エクスポートテスト
    ├── test_auth.py            # Phase 2C 認証テスト
    └── generate_test_data.py  # テストデータ生成
```

## データスキーマ

41列の小売店舗データスキーマ:

| 列名 | 説明 |
|------|------|
| 店舗名 | 店舗名（恵比寿、横浜元町） |
| shop | 店舗コード |
| 年, 月, 日 | 日付要素 |
| 営業日付 | YYYY-MM-DD形式 |
| 売上金額 | 総売上金額 |
| 粗利額, 粗利率 | 粗利関連 |
| 売上数量, 客数, 客単価 | 売上指標 |
| Mens_*, WOMEN'S_* | 商品カテゴリ別売上 |
| 坪売上, 人時売上, 在庫金額 | 店舗運営指標 |

## 今後の開発予定

### Phase 3: 高度な機能
- [ ] PostgreSQL移行
- [ ] Redis統合
- [ ] Celeryバックグラウンドタスク
- [ ] JWT/OAuth認証
- [ ] 本格的なユーザー管理

### Phase 4: フロントエンド
- [ ] React.js フロントエンド
- [ ] リアルタイムダッシュボード
- [ ] グラフの対話的操作

## ライセンス

Internal Use Only

## 技術スタック

- **バックエンド**: Flask 2.3.0
- **データベース**: SQLite 3
- **分析**: pandas 2.0.0, numpy 1.24.0
- **可視化**: plotly 5.14.0
- **認証**: シンプルなAPIキー認証（Phase 2C）
- **セキュリティ**: Flask-CORS, Flask-Limiter

## サポート

問題が発生した場合は、Issueを作成してください。
