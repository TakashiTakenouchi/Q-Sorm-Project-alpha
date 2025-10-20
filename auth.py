"""Q-Storm Platform - Simple API Key Authentication (Phase 2C)"""
import os
import secrets
from functools import wraps
from flask import request, jsonify
from typing import Any, Callable


def generate_api_key() -> str:
    """
    APIキー生成（初回セットアップ用）

    Returns:
        32文字のランダムなURL-safe文字列

    Example:
        >>> python3 -c "from auth import generate_api_key; print(generate_api_key())"
        Xa7K9mP3nQ2vR8tY5wZ1aB4cD6eF0gH2
    """
    return secrets.token_urlsafe(32)


def require_api_key(f: Callable) -> Callable:
    """
    APIキー認証デコレータ

    開発環境（FLASK_ENV=development）では認証をスキップ
    本番環境（FLASK_ENV=production）では X-API-Key ヘッダーでの認証を必須とする

    Args:
        f: デコレート対象の関数

    Returns:
        認証処理を含むラップされた関数

    HTTP Status Codes:
        401: APIキーが提供されていない
        403: 無効なAPIキーが提供された
        500: サーバー側でAPIキーが設定されていない

    Example:
        @app.route('/api/v1/protected', methods=['POST'])
        @require_api_key
        def protected_endpoint():
            return jsonify({'message': 'Access granted'})
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # 開発環境では認証をスキップ
        flask_env = os.environ.get('FLASK_ENV', 'development')
        if flask_env == 'development':
            return f(*args, **kwargs)

        # APIキー取得（X-API-Keyヘッダーから）
        api_key = request.headers.get('X-API-Key')

        # APIキーが提供されていない場合
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'API key required',
                'message': 'Include X-API-Key header in your request',
                'code': 'AUTH_MISSING_API_KEY'
            }), 401

        # 環境変数からサーバー側のAPIキーを取得
        valid_api_key = os.environ.get('QSTORM_API_KEY')

        # サーバー側でAPIキーが設定されていない場合（サーバー設定エラー）
        if not valid_api_key:
            return jsonify({
                'success': False,
                'error': 'Server configuration error',
                'message': 'API key not configured on server',
                'code': 'AUTH_SERVER_CONFIG_ERROR'
            }), 500

        # APIキーの検証
        if api_key != valid_api_key:
            return jsonify({
                'success': False,
                'error': 'Invalid API key',
                'message': 'The provided API key is not valid',
                'code': 'AUTH_INVALID_API_KEY'
            }), 403

        # 認証成功 - 元の関数を実行
        return f(*args, **kwargs)

    return decorated_function


def get_current_environment() -> str:
    """
    現在の実行環境を取得

    Returns:
        'development' または 'production'
    """
    return os.environ.get('FLASK_ENV', 'development')


def is_auth_required() -> bool:
    """
    現在の環境で認証が必要かどうかを判定

    Returns:
        True: 本番環境（認証必須）
        False: 開発環境（認証スキップ）
    """
    return get_current_environment() == 'production'


def validate_auth_config() -> bool:
    """
    認証設定の妥当性を検証

    Returns:
        True: 設定が妥当

    Raises:
        ValueError: 本番環境でAPIキーが設定されていない場合
    """
    if is_auth_required():
        api_key = os.environ.get('QSTORM_API_KEY')
        if not api_key:
            raise ValueError(
                "QSTORM_API_KEY is required in production environment. "
                "Generate a key with: python3 -c \"from auth import generate_api_key; print(generate_api_key())\""
            )
        if len(api_key) < 20:
            raise ValueError(
                "QSTORM_API_KEY is too short. "
                "Use a secure random key generated with generate_api_key()"
            )

    return True
