"""Integration tests for Phase 1 + Phase 2A"""
import sys
import time
import json
import sqlite3
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from db_manager import DatabaseManager
from generate_test_data import generate_sample_store_data


def test_database_initialization():
    """データベース初期化テスト"""
    print("\n" + "=" * 60)
    print("Test 1: データベース初期化")
    print("=" * 60)

    db = DatabaseManager()

    # テーブル存在確認
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

    expected_tables = ['sessions', 'analysis_results']

    for table in expected_tables:
        if table in tables:
            print(f"✅ テーブル '{table}' 存在")
        else:
            print(f"❌ テーブル '{table}' が存在しません")
            return False

    # インデックス確認
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]

    expected_indexes = ['idx_session_id', 'idx_analysis_type', 'idx_created_at']

    for index in expected_indexes:
        if index in indexes:
            print(f"✅ インデックス '{index}' 存在")
        else:
            print(f"⚠️  インデックス '{index}' が存在しません")

    print("✅ Test 1: 合格")
    return True


def test_session_management():
    """セッション管理テスト"""
    print("\n" + "=" * 60)
    print("Test 2: セッション管理")
    print("=" * 60)

    db = DatabaseManager()

    # セッション保存
    session_id = "test_session_001"
    db.save_session(session_id, store="恵比寿", user_id="test_user", metadata={"test": True})
    print(f"✅ セッション保存: {session_id}")

    # セッションサマリー取得
    summary = db.get_session_summary(session_id)

    if summary and summary['session_id'] == session_id:
        print(f"✅ セッションサマリー取得成功")
        print(f"   - session_id: {summary['session_id']}")
        print(f"   - store: {summary['store']}")
        print(f"   - created_at: {summary['created_at']}")
    else:
        print(f"❌ セッションサマリー取得失敗")
        return False

    print("✅ Test 2: 合格")
    return True


def test_analysis_result_storage():
    """分析結果保存テスト"""
    print("\n" + "=" * 60)
    print("Test 3: 分析結果保存・取得")
    print("=" * 60)

    db = DatabaseManager()

    # テスト用セッションIDをクリーンアップ（前回のテストデータを削除）
    session_id = "test_session_002"
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM analysis_results WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    print(f"✅ テストセッション '{session_id}' のクリーンアップ完了")

    # テスト用分析結果
    analysis_types = ['timeseries', 'histogram', 'pareto']

    for analysis_type in analysis_types:
        analysis_id = db.save_analysis_result(
            session_id=session_id,
            analysis_type=analysis_type,
            store="横浜元町",
            target_column="売上金額",
            parameters={'test': True, 'type': analysis_type},
            results={'chart': {}, 'statistics': {}},
            execution_time=0.5 + len(analysis_type) * 0.1
        )
        print(f"✅ {analysis_type}分析結果保存: ID={analysis_id}")

    # 分析結果取得
    results = db.get_analysis_results(session_id=session_id)

    if len(results) == 3:
        print(f"✅ 分析結果取得成功: {len(results)}件")
        for r in results:
            print(f"   - {r['analysis_type']}: execution_time={r['execution_time']}s")
    else:
        print(f"❌ 分析結果取得失敗: 期待3件、実際{len(results)}件")
        return False

    # 分析タイプフィルタリング
    ts_results = db.get_analysis_results(session_id=session_id, analysis_type='timeseries')
    if len(ts_results) == 1:
        print(f"✅ 分析タイプフィルタリング成功: timeseries={len(ts_results)}件")
    else:
        print(f"❌ 分析タイプフィルタリング失敗")
        return False

    print("✅ Test 3: 合格")
    return True


def test_data_generation():
    """テストデータ生成確認"""
    print("\n" + "=" * 60)
    print("Test 4: テストデータ生成")
    print("=" * 60)

    try:
        data_path = generate_sample_store_data()

        if Path(data_path).exists():
            file_size = Path(data_path).stat().st_size
            print(f"✅ テストデータ生成成功")
            print(f"   - ファイルパス: {data_path}")
            print(f"   - ファイルサイズ: {file_size:,} bytes")
        else:
            print(f"❌ テストデータファイルが存在しません")
            return False

        print("✅ Test 4: 合格")
        return True
    except Exception as e:
        print(f"❌ Test 4: 失敗 - {e}")
        return False


def run_all_tests():
    """全テスト実行"""
    print("\n" + "=" * 60)
    print("Q-Storm Phase 1 + Phase 2A 統合テスト")
    print("=" * 60)

    tests = [
        ("データベース初期化", test_database_initialization),
        ("セッション管理", test_session_management),
        ("分析結果保存・取得", test_analysis_result_storage),
        ("テストデータ生成", test_data_generation),
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
        print("✅ Phase 2A動作確認完了")
        print("✅ Phase 2B（Markdownエクスポート）実装開始可能")
    else:
        print(f"\n⚠️  {failed}件のテストが不合格です。")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
