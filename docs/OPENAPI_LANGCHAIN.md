# LangChain Narrative API (Draft)

最新のLangChain自然言語解説エンドポイント `/api/v2/analysis/langchain` の最小スキーマ定義です。正式なOpenAPI 3.0仕様に統合する際の叩き台として使用してください。

## Path
`POST /api/v2/analysis/langchain`

## Authentication
- 開発環境: 認証不要
- 本番環境: `X-API-Key` ヘッダーで `QSTORM_API_KEY` を指定

## Request Body
```json
{
  "session_id": "session_20251028_130000",
  "store_a": "恵比寿店",
  "store_b": "横浜元町店",
  "category_columns": [
    "Mens_JACKETS&OUTER2",
    "Mens_KNIT",
    "Mens_PANTS",
    "WOMEN'S_JACKETS2",
    "WOMEN'S_TOPS",
    "WOMEN'S_ONEPIECE",
    "WOMEN'S_bottoms",
    "WOMEN'S_SCARF & STOLES"
  ]
}
```

### Field Notes
- `session_id` *(string, required)*: `/api/v2/upload/validate` が返すセッションID。
- `store_a`, `store_b` *(string, required)*: 比較対象の店舗名。`shop` または `店舗名` カラムに一致している必要あり。
- `category_columns` *(array of string, optional)*: 集計対象の数値カラム。省略時はパレート分析で使用する既定カテゴリを採用。

## Successful Response (200)
```json
{
  "success": true,
  "data": {
    "summary": "## 傾向\n- ...",
    "stores": ["恵比寿店", "横浜元町店"],
    "evidence": {
      "stores": {
        "恵比寿店": {
          "total": 1234567.8,
          "top_categories": [
            {"category": "メンズ パンツ", "value": 345678.9, "share_pct": 28.0}
          ]
        },
        "横浜元町店": {
          "total": 1123456.7,
          "top_categories": [
            {"category": "レディース トップス", "value": 312345.6, "share_pct": 27.8}
          ]
        }
      },
      "differences": [
        {
          "category": "メンズ パンツ",
          "store_a": 345678.9,
          "store_b": 212345.6,
          "difference": 133333.3
        }
      ]
    }
  }
}
```

## Error Responses
- `400 VALIDATION_ERROR`: 入力不足、カテゴリ配列が不正など
- `404 SESSION_NOT_FOUND`: セッションが存在しない・期限切れ
- `404 STORE_NOT_FOUND`: 指定店舗のデータがセッション内に存在しない
- `500 INTERNAL_ERROR`: LangChain実行失敗などサーバー側エラー

## Curl Sample
```bash
curl -X POST http://127.0.0.1:5004/api/v2/analysis/langchain \
  -H "Content-Type: application/json" \
  -d '{
        "session_id": "session_20251028_130000",
        "store_a": "恵比寿店",
        "store_b": "横浜元町店"
      }'
```

> NOTE: 本番環境では `-H "X-API-Key: $QSTORM_API_KEY"` を追加してください。
