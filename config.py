import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / 'uploads'
OUTPUT_DIR = BASE_DIR / 'outputs'
SAMPLE_DATA_DIR = BASE_DIR / 'data' / 'sample'

# Environment configuration
MAX_FILE_SIZE_MB = int(os.environ.get('MAX_FILE_SIZE_MB', 200))
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Phase 2C: Authentication configuration
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
QSTORM_API_KEY = os.environ.get('QSTORM_API_KEY', '')

# 認証が必要な環境（本番環境のみ）
REQUIRE_AUTH = (FLASK_ENV == 'production')

# Valid metrics derived from the 41-column retail schema
VALID_METRICS = [
    '売上金額', '粗利額', '売上数量', '客数', '客単価',
    '粗利率', '坪売上', '人時売上', '在庫金額'
]

# Supported time aggregation units
VALID_TIME_UNITS = ['日', '週', '月', '年']


def validate_env_config():
    """
    環境変数の検証（Appendix G.2準拠）

    Phase 1スコープ:
    - MAX_FILE_SIZE_MB: 範囲チェック（1-1000MB）
    - OPENAI_API_KEY: 存在確認とフォーマット検証（sk-で始まる）

    Phase 2Cスコープ:
    - QSTORM_API_KEY: 本番環境では必須、長さチェック（20文字以上）
    """
    if not isinstance(MAX_FILE_SIZE_MB, int):
        raise ValueError(f"MAX_FILE_SIZE_MB must be integer, got {type(MAX_FILE_SIZE_MB).__name__}")

    if not (1 <= MAX_FILE_SIZE_MB <= 1000):
        raise ValueError(f"MAX_FILE_SIZE_MB must be 1-1000, got {MAX_FILE_SIZE_MB}")

    if OPENAI_API_KEY:
        if not isinstance(OPENAI_API_KEY, str):
            raise ValueError("OPENAI_API_KEY must be string")
        if not OPENAI_API_KEY.startswith('sk-'):
            raise ValueError("OPENAI_API_KEY format invalid (must start with 'sk-')")

    # Phase 2C: 本番環境ではAPIキー必須
    if REQUIRE_AUTH:
        if not QSTORM_API_KEY:
            raise ValueError(
                "QSTORM_API_KEY is required in production environment. "
                "Generate a key with: python3 -c \"from auth import generate_api_key; print(generate_api_key())\""
            )
        if len(QSTORM_API_KEY) < 20:
            raise ValueError(
                "QSTORM_API_KEY is too short (minimum 20 characters). "
                "Use a secure random key generated with generate_api_key()"
            )

    return True


# アプリケーション起動時に自動実行
try:
    validate_env_config()
except ValueError as e:
    import sys
    print(f"[ERROR] Environment configuration invalid: {e}", file=sys.stderr)
    sys.exit(1)
