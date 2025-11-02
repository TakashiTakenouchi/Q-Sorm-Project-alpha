Q-Storm LangChain Development Plan

## Purpose & Context
- 最新方針「LangChainを活用した自然言語解説」を最優先し、恵比寿店と横浜元町店のパレート分析結果を自動説明する機能を Phase 3 へ向けて準備する。
- 分析対象ドキュメントから開発履歴・既知課題を整理し、Flask + React 構成の現状を把握した上で、LangChain導入の技術計画を提示する。

## Document Highlights
- **docs/README.md**: ドキュメント体系と更新フローを定義。DM_LOG 更新義務や現行サーバー稼働状況、修復済みバグ一覧が Phase 2 完了点を示す。
- **CLAUDE.md**: アーキテクチャ概要とモジュール構成（Flaskモノリス、Reactフロント、SQLite永続化）を記載。テストコマンドや既存Analyzerクラスの責務が明確。
- **docs/KNOWN_ISSUES.md**: セッション揮発性、パフォーマンス低下、API仕様欠如、V1/V2混在、認証未完成など Phase 3 以前からの懸念を列挙。エクスポート/PDF欠如や将来の機能要望も整理。
- **docs/TROUBLESHOOTING.md**: バックエンド・フロントエンドの起動失敗、API 500系、データアップロード不整合などの再発時対応を提示。既存修復箇所の検証方法も含む。

## Architecture Readiness Assessment
| Component | Current Readiness | Observations | Outstanding Gaps |
|-----------|------------------|--------------|------------------|
| Backend (Flask) | Phase 2完了・安定運用 | V1/V2分析エンドポイントとAnalyzer群が稼働、APIキー枠組みあり | `/api/v1/analysis/*` 系の設計一貫性欠如、LangChain用 `/api/v2/analysis/langchain` 未実装、OpenAPI未整備 |
| Frontend (React) | 核機能完備 | アップロード→分析→可視化のフロー定着 | LangChain解説UIが未設計、自然言語結果表示領域不在 |
| Database (SQLite) | 安定だが拡張余地 | 分析結果履歴は保存済み | セッションがメモリのみ、LangChainログ/プロンプト履歴用テーブル未整備 |
| Export/Reporting | Markdownのみ部分完了 | ExportManagerでMarkdown生成可能 | LangChain説明のレポート連携不可、PDF/Excel未対応 |
| API Surface | ハイブリッド | V1直返却 + V2強化版の混在 | LangChain専用APIとOpenAPIドキュメント不足、比較分析APIの再利用設計が必要 |
| Documentation | 豊富 | 開発判断・障害対応は充実 | LangChain導入手順やLLM運用ガイドが未作成、API仕様書未整備 |

## LangChain Integration Strategy
### Objectives
- 恵比寿店と横浜元町店のパレート分析結果を取り込み、Q-Storm Lang Agent が自然言語で差異を説明するワークフローを構築。
- Flaskの `/api/v2/analysis/langchain` を介して LangChain パイプラインを呼び出し、React から取得できるようにする。
- 既存Analyzer/DB/Export資産を再利用し、Phase 3 へ拡張可能なモジュール境界を整備。

### Module Structure (Q-Storm Lang Agent)
- `lang_agent/__init__.py`: LangChainエントリーポイント、RunnableSequence定義。
- `lang_agent/data_loader.py`: SQLiteの `analysis_results` やオンデマンドAnalyzer呼び出しから恵比寿/横浜のParetoデータを取得。
- `lang_agent/prompt_builder.py`: テンプレートに分析指標（売上・累積寄与・ABC分類）とトーン設定を埋め込み、比較対象を明示。
- `lang_agent/chains.py`: LangChain Expression Languageで `PromptTemplate → LLM → StructuredOutputParser` を構成。LLM応答を `summary`, `insights`, `recommendations` などのフィールドにマッピング。
- `lang_agent/post_processor.py`: LLM応答をJSONフレンドリーな形に整形し、Markdown生成やFront表示用に変換。
- `lang_agent/config.py`: モデル名、温度、システムプロンプト、出力フォーマット、タイムアウト設定を集中管理。

### Flask Integration Points
- Blueprint拡張: `app_improved.py` に `from lang_agent import get_langchain_response` を追加し、`/api/v2/analysis/langchain` POST を新設。
  - Payload例: `{ "session_id": "...", "store_a": "恵比寿店", "store_b": "横浜元町店", "metric": "Total_Sales" }`
  - 処理フロー: セッション確認 → `data_loader` で各店舗Paretoデータ取得 → LangChain実行 → レスポンス（自然言語説明 + メタ情報）返却。
- 既存エンドポイント連携: 必要に応じて `/api/v2/analysis/pareto` を内部呼び出し。または `DatabaseManager` から最新Pareto履歴を検索して再利用。
- エラーハンドリング: LLM失敗時はフォールバックメッセージ＋HTTP 502。`docs/TROUBLESHOOTING.md` にLangChain節を追加予定。

### LangChain Flow Overview
1. **Input Assembly**: 恵比寿・横浜のPareto結果（トップカテゴリ、累積貢献、ABCランク）を取得し、比較用構造体を作成。
2. **Prompt Crafting**: システムメッセージで「店舗比較アナリスト」ロールを設定、ユーザー指示で「違いと共通点、改善提案」を要求。
3. **LLM Execution**: LangChain `ChatOpenAI`（GPT系）または将来のAzureエンドポイントを呼び出し。
4. **Structured Output Parsing**: JSON Schemaベースで `overall_summary`, `key_differences`, `risk_watchpoints`, `action_items` を抽出。
5. **Response Delivery**: FlaskがJSONレスポンスで返却し、フロントがテキストパネルやMarkdownエクスポートに組み込む。
6. **Audit Logging (Phase 3+)**: 応答・プロンプトをSQLite/将来のPostgreSQLに保存し、再現性担保。

### Model Selection Rationale
- **Primary**: `gpt-4o`（高品質自然言語生成 + コストバランス + 最新化）。
- **Fallback**: `gpt-4-turbo`（レイテンシ短縮や制限時に使用）。
- **Future-ready**: `gpt-5`（条件: プロダクション安定版提供後にスイッチ、LangChainのリトライ/マルチモデル対応で段階導入）。
- モデル切替は `lang_agent/config.py` の環境変数（`QSTORM_LLM_MODEL`）で制御し、A/B検証を容易にする。

### API Key & Configuration Management
- 既存 `config.py` に `OPENAI_API_KEY`, `QSTORM_LLM_MODEL`, `LANGCHAIN_CALLBACKS` を追加し、`os.getenv` で読み込む。
- `.env` やホスト環境でAPIキー設定 (`export OPENAI_API_KEY=...`)。本番ではVaultやAzure Key Vaultを想定。
- LangChainのTracing/Callback機能はオプトイン設定とし、開発時のみ `LANGCHAIN_TRACING_V2=true` を許可。
- SecretはFlaskアプリ起動時に検証し、未設定なら起動ログで警告 → `/health` で `llm_configured` フラグを返却。

### Data & Prompt Governance (Phase 3 Considerations)
- 入力データはカテゴリ名・売上値などの統計情報のみ使用し、個人情報は取り扱わない。
- 出力検証のため `docs/KNOWN_ISSUES.md` に LLM関連リスク（幻覚、API失敗時の対応）を追記予定。
- Promptテンプレートは `docs/DECISIONS.md` にADRとして記録し、重要な変更はレビュー対象にする。

## Development Phase Plan
| Phase | 内容 | 主要タスク | 完了条件 | 担当Agent |
|--------|------|------------|-----------|------------|
| 1 | 文書解析とナレッジ統合 | docs読込, 既知課題整理 | 計画文書作成 | Codex |
| 2 | LangChain基盤構築 | Flask統合, LLM接続 | API応答成功 | LangAgent |
| 3 | 自然言語解説生成 | 恵比寿vs横浜比較テキスト生成 | 出力例生成 | LangAgent |
| 4 | テストと展開 | CLI／UI統合 | レポート出力成功 | Q-Storm CLI |

## Next Steps Toward Phase 3
- LangChainモジュールの初期スケルトンを作成し、既存Pareto Analyzerとのデータインターフェースを定義。
- `/api/v2/analysis/langchain` のスキーマとOpenAPIドラフトを整備し、フロントエンドのUI/UX要件を定義。
- LLM応答の品質評価指標（例: 差異検出率、提案の具体性）を策定し、Phase 3の自動回帰テスト戦略に組み込む。

## CHANGE SUMMARY
- `lang_agent` パッケージを追加し、`generate_store_comparison` で店舗別カテゴリ集計とLangChain呼び出しの骨格を実装（`lang_agent/chain.py`, `lang_agent/prompt.md`）。
- Flaskに `/api/v2/analysis/langchain` を追加し、セッションデータをフィルタして Lang Agent を呼び出すV2エンドポイントを提供。
- 依存パッケージ・環境変数・OpenAPIドラフト・テスト・フロントエンドクライアントを更新し、呼び出し準備を整備。
- `.env` に OPENAI_API_KEY を保管し、`tests/test_langchain.py` が自動読込するようセキュリティ対策を反映。
- フロントエンドに「AI解説」タブを追加し、店舗セレクタ＋ボタンから LangChain 呼び出しを行う UX を実装。

### 呼び出し例（開発環境）
```bash
curl -X POST http://127.0.0.1:5004/api/v2/analysis/langchain \
  -H "Content-Type: application/json" \
  -d '{
        "session_id": "<SESSION_ID>",
        "store_a": "恵比寿店",
        "store_b": "横浜元町店"
      }'
```

本番環境では `-H "X-API-Key: $QSTORM_API_KEY"` を追加し、OPENAI_API_KEY を設定してLangChain呼び出しを有効化する。

## ✅ LangChain Verified (2025-11-02)
- 実行コマンド: `OPENAI_API_KEY=<redacted> pytest tests/test_langchain.py -v`（6.48s / 1件成功）
- Live API: Flask test client で `/api/v2/analysis/langchain` を実行し、`langchain_openai.ChatOpenAI` → OpenAI Chat Completions へ到達（HTTP 200）
- モデル応答抜粋: 「両店舗で『レディース トップス』と『メンズ パンツ』が主要カテゴリとして共通」「横浜元町ではレディース トップスの比率が高く、恵比寿ではメンズパンツ・ジャケットが相対的に強い」
- 差異サマリー: メンズパンツ +92,000円（恵比寿優位）／レディーストップス −60,000円（横浜元町優位）／メンズジャケット +60,000円（恵比寿優位）／レディースボトムス +26,000円
- 推奨施策例（LLM出力）: 横浜元町でメンズパンツ販促、レディーストップスの在庫最適化、恵比寿のメンズジャケット施策横展開、セット購入促進
- エビデンス: 恵比寿=1,070,000円・横浜元町=952,000円、各店舗トップカテゴリ（最大5件）と差分上位4件をJSONで保存済み
- セキュリティ: OPENAI_API_KEY は `.env` 管理とし、コミット対象から除外。利用後は速やかなキーのローテーションを推奨（既に最新キーへ更新済み）。
