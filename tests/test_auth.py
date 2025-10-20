"""Phase 2C API Authentication Tests"""
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import generate_api_key, is_auth_required, get_current_environment


def test_generate_api_key():
    """APIキー生成テスト"""
    print("\n" + "=" * 60)
    print("Test 1: APIキー生成機能")
    print("=" * 60)

    # 2つのキーを生成
    key1 = generate_api_key()
    key2 = generate_api_key()

    # 長さ確認（URL-safe base64の32バイトは43文字程度）
    if len(key1) < 20:
        print(f"❌ APIキーが短すぎます: {len(key1)}文字")
        return False

    print(f"✅ APIキー生成成功: {len(key1)}文字")
    print(f"   サンプルキー1: {key1[:20]}...")
    print(f"   サンプルキー2: {key2[:20]}...")

    # ユニーク性確認
    if key1 == key2:
        print(f"❌ 生成されたキーが同一です")
        return False

    print(f"✅ ユニーク性確認: キーは異なっています")

    # URL-safeな文字のみ使用しているか確認
    import string
    allowed_chars = string.ascii_letters + string.digits + '-_'
    for char in key1:
        if char not in allowed_chars:
            print(f"❌ 不正な文字が含まれています: {char}")
            return False

    print(f"✅ URL-safe文字のみ使用")

    print("✅ Test 1: 合格")
    return True


def test_environment_detection():
    """環境検出テスト"""
    print("\n" + "=" * 60)
    print("Test 2: 環境検出機能")
    print("=" * 60)

    # 現在の環境を保存
    original_env = os.environ.get('FLASK_ENV')

    try:
        # 開発環境テスト
        os.environ['FLASK_ENV'] = 'development'
        env = get_current_environment()
        auth_required = is_auth_required()

        if env != 'development':
            print(f"❌ 開発環境の検出に失敗: {env}")
            return False

        if auth_required:
            print(f"❌ 開発環境で認証が必須になっています")
            return False

        print(f"✅ 開発環境検出: env={env}, auth_required={auth_required}")

        # 本番環境テスト
        os.environ['FLASK_ENV'] = 'production'
        env = get_current_environment()
        auth_required = is_auth_required()

        if env != 'production':
            print(f"❌ 本番環境の検出に失敗: {env}")
            return False

        if not auth_required:
            print(f"❌ 本番環境で認証が不要になっています")
            return False

        print(f"✅ 本番環境検出: env={env}, auth_required={auth_required}")

        # デフォルト環境テスト（FLASK_ENVが未設定）
        if 'FLASK_ENV' in os.environ:
            del os.environ['FLASK_ENV']
        env = get_current_environment()

        if env != 'development':
            print(f"❌ デフォルト環境の検出に失敗: {env}（期待: development）")
            return False

        print(f"✅ デフォルト環境検出: env={env}（FLASK_ENV未設定時）")

        print("✅ Test 2: 合格")
        return True

    finally:
        # 元の環境を復元
        if original_env:
            os.environ['FLASK_ENV'] = original_env
        elif 'FLASK_ENV' in os.environ:
            del os.environ['FLASK_ENV']


def test_auth_decorator_development():
    """開発環境での認証デコレータテスト"""
    print("\n" + "=" * 60)
    print("Test 3: 開発環境での認証スキップ")
    print("=" * 60)

    # 開発環境に設定
    original_env = os.environ.get('FLASK_ENV')
    os.environ['FLASK_ENV'] = 'development'

    try:
        from app_improved import app

        with app.test_client() as client:
            # APIキーなしでアクセス（開発環境では成功するはず）
            # データが不足しているため、認証エラー以外のエラーになることを確認
            response = client.post('/api/v1/analysis/timeseries',
                                    json={'session_id': 'test'})

            # 401/403であれば認証エラー（失敗）
            if response.status_code in [401, 403]:
                print(f"❌ 開発環境で認証が要求されています: {response.status_code}")
                return False

            print(f"✅ 開発環境で認証がスキップされました（status={response.status_code}）")
            print("✅ Test 3: 合格")
            return True

    finally:
        # 元の環境を復元
        if original_env:
            os.environ['FLASK_ENV'] = original_env
        elif 'FLASK_ENV' in os.environ:
            del os.environ['FLASK_ENV']


def test_auth_decorator_production():
    """本番環境での認証デコレータテスト"""
    print("\n" + "=" * 60)
    print("Test 4: 本番環境での認証機能")
    print("=" * 60)

    # 本番環境に設定
    original_env = os.environ.get('FLASK_ENV')
    original_key = os.environ.get('QSTORM_API_KEY')

    valid_api_key = "test-api-key-12345678901234567890"
    os.environ['FLASK_ENV'] = 'production'
    os.environ['QSTORM_API_KEY'] = valid_api_key

    try:
        from app_improved import app

        with app.test_client() as client:
            # 4-1: APIキーなしでアクセス → 401
            response = client.post('/api/v1/analysis/timeseries',
                                    json={'session_id': 'test'})

            if response.status_code != 401:
                print(f"❌ APIキーなしで401が返されませんでした: {response.status_code}")
                return False

            data = response.get_json()
            if data.get('code') != 'AUTH_MISSING_API_KEY':
                print(f"❌ 正しいエラーコードが返されませんでした: {data.get('code')}")
                return False

            print(f"✅ APIキーなし → 401 Unauthorized (code: {data.get('code')})")

            # 4-2: 無効なAPIキー → 403
            response = client.post('/api/v1/analysis/timeseries',
                                    headers={'X-API-Key': 'invalid-key'},
                                    json={'session_id': 'test'})

            if response.status_code != 403:
                print(f"❌ 無効なAPIキーで403が返されませんでした: {response.status_code}")
                return False

            data = response.get_json()
            if data.get('code') != 'AUTH_INVALID_API_KEY':
                print(f"❌ 正しいエラーコードが返されませんでした: {data.get('code')}")
                return False

            print(f"✅ 無効なAPIキー → 403 Forbidden (code: {data.get('code')})")

            # 4-3: 有効なAPIキー → 認証成功（別のエラーになるが401/403ではない）
            response = client.post('/api/v1/analysis/timeseries',
                                    headers={'X-API-Key': valid_api_key},
                                    json={'session_id': 'test'})

            if response.status_code in [401, 403]:
                print(f"❌ 有効なAPIキーで認証エラーが発生しました: {response.status_code}")
                return False

            print(f"✅ 有効なAPIキー → 認証成功（status={response.status_code}）")

            print("✅ Test 4: 合格")
            return True

    finally:
        # 元の環境を復元
        if original_env:
            os.environ['FLASK_ENV'] = original_env
        elif 'FLASK_ENV' in os.environ:
            del os.environ['FLASK_ENV']

        if original_key:
            os.environ['QSTORM_API_KEY'] = original_key
        elif 'QSTORM_API_KEY' in os.environ:
            del os.environ['QSTORM_API_KEY']


def test_all_endpoints_protected():
    """すべての保護されたエンドポイントのテスト"""
    print("\n" + "=" * 60)
    print("Test 5: エンドポイント保護の確認")
    print("=" * 60)

    # 本番環境に設定
    original_env = os.environ.get('FLASK_ENV')
    original_key = os.environ.get('QSTORM_API_KEY')

    os.environ['FLASK_ENV'] = 'production'
    os.environ['QSTORM_API_KEY'] = "test-key-123456789012345678901234"

    try:
        from app_improved import app

        with app.test_client() as client:
            # テスト対象エンドポイント
            protected_endpoints = [
                ('POST', '/api/v1/analysis/timeseries', {'session_id': 'test'}),
                ('POST', '/api/v1/analysis/histogram', {'session_id': 'test'}),
                ('POST', '/api/v1/analysis/pareto', {'session_id': 'test'}),
                ('GET', '/api/v1/export/markdown/1', None),
                ('GET', '/api/v1/export/session/test', None),
            ]

            all_passed = True

            for method, endpoint, json_data in protected_endpoints:
                if method == 'POST':
                    response = client.post(endpoint, json=json_data)
                else:
                    response = client.get(endpoint)

                if response.status_code != 401:
                    print(f"❌ {method} {endpoint}: 認証なしで401が返されませんでした（{response.status_code}）")
                    all_passed = False
                else:
                    print(f"✅ {method} {endpoint}: 認証保護されています（401）")

            if all_passed:
                print("✅ Test 5: 合格")
                return True
            else:
                print("❌ Test 5: 不合格")
                return False

    finally:
        # 元の環境を復元
        if original_env:
            os.environ['FLASK_ENV'] = original_env
        elif 'FLASK_ENV' in os.environ:
            del os.environ['FLASK_ENV']

        if original_key:
            os.environ['QSTORM_API_KEY'] = original_key
        elif 'QSTORM_API_KEY' in os.environ:
            del os.environ['QSTORM_API_KEY']


def run_all_tests():
    """全テスト実行"""
    print("\n" + "=" * 60)
    print("Phase 2C API認証機能テスト")
    print("=" * 60)

    tests = [
        ("APIキー生成機能", test_generate_api_key),
        ("環境検出機能", test_environment_detection),
        ("開発環境での認証スキップ", test_auth_decorator_development),
        ("本番環境での認証機能", test_auth_decorator_production),
        ("エンドポイント保護の確認", test_all_endpoints_protected),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name}: 例外発生 - {e}")
            import traceback
            traceback.print_exc()
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
        print("✅ Phase 2C動作確認完了")
        print("✅ Phase 2D（Render deploy）実装開始可能")
    else:
        print(f"\n⚠️  {failed}件のテストが不合格です。")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
