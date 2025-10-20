"""Phase 2B Markdown Export Tests"""
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from export_manager import MarkdownExporter
from db_manager import DatabaseManager


def test_export_single_analysis():
    """単一分析結果のMarkdownエクスポートテスト"""
    print("\n" + "=" * 60)
    print("Test 1: 単一分析結果のMarkdownエクスポート")
    print("=" * 60)

    exporter = MarkdownExporter()
    db = DatabaseManager()

    # データベースから既存の分析結果を取得
    results = db.get_analysis_results(limit=10)

    if not results:
        print("❌ テストデータが存在しません")
        return False

    success_count = 0
    total_count = 0

    # 各分析タイプ（timeseries, histogram, pareto）をテスト
    analysis_types = {}
    for result in results:
        analysis_type = result['analysis_type']
        if analysis_type not in analysis_types:
            analysis_types[analysis_type] = result['id']

    for analysis_type, analysis_id in analysis_types.items():
        total_count += 1
        try:
            markdown = exporter.export_analysis(analysis_id)

            # 基本的な内容チェック
            if not markdown:
                print(f"❌ {analysis_type}: Markdown出力が空です")
                continue

            # 必須要素の確認
            required_elements = ['分析ID', 'セッションID', '実行日時', '実行時間']
            missing_elements = [elem for elem in required_elements if elem not in markdown]

            if missing_elements:
                print(f"❌ {analysis_type}: 必須要素が不足 - {missing_elements}")
                continue

            # 分析タイプ固有の確認
            if analysis_type == 'timeseries' and '時系列分析' not in markdown:
                print(f"❌ {analysis_type}: タイプ固有の要素が不足")
                continue

            if analysis_type == 'histogram' and 'ヒストグラム分析' not in markdown:
                print(f"❌ {analysis_type}: タイプ固有の要素が不足")
                continue

            if analysis_type == 'pareto' and 'ABC分類' not in markdown:
                print(f"❌ {analysis_type}: タイプ固有の要素が不足")
                continue

            print(f"✅ {analysis_type}: Markdownエクスポート成功 (ID={analysis_id}, {len(markdown)}文字)")
            success_count += 1

            # サンプル出力（最初の5行のみ）
            lines = markdown.split('\n')[:5]
            print(f"   サンプル出力:")
            for line in lines:
                print(f"   {line}")

        except Exception as e:
            print(f"❌ {analysis_type}: エラー - {e}")

    if success_count == total_count and success_count > 0:
        print(f"✅ Test 1: 合格 ({success_count}/{total_count})")
        return True
    else:
        print(f"❌ Test 1: 不合格 ({success_count}/{total_count})")
        return False


def test_export_session():
    """セッション全体のMarkdownエクスポートテスト"""
    print("\n" + "=" * 60)
    print("Test 2: セッション全体のMarkdownエクスポート")
    print("=" * 60)

    exporter = MarkdownExporter()
    db = DatabaseManager()

    # テストセッションを取得
    results = db.get_analysis_results(limit=1)

    if not results:
        print("❌ テストデータが存在しません")
        return False

    session_id = results[0]['session_id']

    try:
        markdown = exporter.export_session(session_id)

        # 基本的な内容チェック
        if not markdown:
            print("❌ Markdown出力が空です")
            return False

        # 必須要素の確認
        required_elements = [
            'Q-Storm 分析レポート',
            'セッションID',
            '店舗',
            '分析件数',
            'レポート生成日時'
        ]

        missing_elements = [elem for elem in required_elements if elem not in markdown]

        if missing_elements:
            print(f"❌ 必須要素が不足: {missing_elements}")
            return False

        # 複数分析が含まれているか確認
        if '分析 #' not in markdown:
            print("❌ 分析結果が含まれていません")
            return False

        print(f"✅ セッションMarkdownエクスポート成功 (session_id={session_id}, {len(markdown)}文字)")

        # サンプル出力（最初の10行）
        lines = markdown.split('\n')[:10]
        print("   サンプル出力:")
        for line in lines:
            print(f"   {line}")

        print("✅ Test 2: 合格")
        return True

    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def test_error_handling():
    """エラーハンドリングテスト"""
    print("\n" + "=" * 60)
    print("Test 3: エラーハンドリング")
    print("=" * 60)

    exporter = MarkdownExporter()

    # 存在しないanalysis_id
    try:
        exporter.export_analysis(99999)
        print("❌ 存在しないanalysis_idでエラーが発生しませんでした")
        return False
    except ValueError as e:
        print(f"✅ 存在しないanalysis_id: 正しくValueErrorが発生 - {e}")

    # 存在しないsession_id
    try:
        exporter.export_session("nonexistent_session_999")
        print("❌ 存在しないsession_idでエラーが発生しませんでした")
        return False
    except ValueError as e:
        print(f"✅ 存在しないsession_id: 正しくValueErrorが発生 - {e}")

    print("✅ Test 3: 合格")
    return True


def test_markdown_file_export():
    """Markdownファイル出力テスト"""
    print("\n" + "=" * 60)
    print("Test 4: Markdownファイル出力")
    print("=" * 60)

    exporter = MarkdownExporter()
    db = DatabaseManager()

    # テストセッションを取得
    results = db.get_analysis_results(limit=1)

    if not results:
        print("❌ テストデータが存在しません")
        return False

    session_id = results[0]['session_id']

    try:
        markdown = exporter.export_session(session_id)

        # outputsディレクトリに保存
        output_dir = Path(__file__).parent.parent / 'outputs'
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f'session_{session_id}_export.md'
        output_file.write_text(markdown, encoding='utf-8')

        # ファイル存在確認
        if not output_file.exists():
            print(f"❌ ファイルが作成されませんでした")
            return False

        file_size = output_file.stat().st_size
        print(f"✅ Markdownファイル出力成功")
        print(f"   - ファイルパス: {output_file}")
        print(f"   - ファイルサイズ: {file_size:,} bytes")

        print("✅ Test 4: 合格")
        return True

    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def run_all_tests():
    """全テスト実行"""
    print("\n" + "=" * 60)
    print("Phase 2B Markdownエクスポート機能テスト")
    print("=" * 60)

    tests = [
        ("単一分析結果エクスポート", test_export_single_analysis),
        ("セッション全体エクスポート", test_export_session),
        ("エラーハンドリング", test_error_handling),
        ("Markdownファイル出力", test_markdown_file_export),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name}: 例外発生 - {e}")
            results[test_name] = False

    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)

    total = len(results)
    passed = sum(results.values())
    failed = total - passed

    for test_name, result in results.items():
        status = "✅ 合格" if result else "❌ 不合格"
        print(f"{status}: {test_name}")

    print(f"\n合計: {total}件 | 合格: {passed}件 | 不合格: {failed}件")

    if failed == 0:
        print("\n🎉 すべてのテストに合格しました！")
        print("✅ Phase 2B動作確認完了")
        print("✅ Phase 2C（API認証）実装開始可能")
    else:
        print(f"\n⚠️  {failed}件のテストが不合格です。")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
