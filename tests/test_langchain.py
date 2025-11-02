"""Tests for the LangChain narrative endpoint."""
import os
import sys
from pathlib import Path

import pandas as pd
import pytest
import werkzeug

if not hasattr(werkzeug, '__version__'):
    werkzeug.__version__ = '3.1.3'


def _load_env() -> None:
    if os.getenv('OPENAI_API_KEY'):
        return
    env_path = Path(__file__).resolve().parent.parent / '.env'
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        if key.strip() == 'OPENAI_API_KEY' and value.strip():
            os.environ.setdefault('OPENAI_API_KEY', value.strip())
            break


_load_env()

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from app_improved import app, data_storage  # noqa: E402

pytestmark = pytest.mark.skipif(
    not os.getenv('OPENAI_API_KEY'),
    reason='OPENAI_API_KEY not set'
)


def _build_fixture_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            'shop': ['恵比寿店', '恵比寿店', '横浜元町店', '横浜元町店'],
            'Date': pd.date_range('2024-01-01', periods=4, freq='D'),
            'Mens_JACKETS&OUTER2': [120000, 98000, 76000, 82000],
            'Mens_PANTS': [150000, 142000, 99000, 101000],
            "WOMEN'S_TOPS": [180000, 175000, 210000, 205000],
            "WOMEN'S_bottoms": [110000, 95000, 87000, 92000],
            'Total_Sales': [560000, 510000, 472000, 480000],
            'Number_of_guests': [400, 380, 360, 355],
            'Price_per_customer': [1400, 1342, 1311, 1352],
        }
    )


def test_langchain_endpoint_returns_summary():
    session_id = 'session_test_langchain'
    data_storage[session_id] = _build_fixture_dataframe()

    try:
        client = app.test_client()
        payload = {
            'session_id': session_id,
            'store_a': '恵比寿店',
            'store_b': '横浜元町店',
        }
        response = client.post('/api/v2/analysis/langchain', json=payload)
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        body = data['data']
        assert body['stores'] == ['恵比寿店', '横浜元町店']
        assert isinstance(body['summary'], str) and body['summary'].strip()
        assert 'evidence' in body and body['evidence']
    finally:
        data_storage.pop(session_id, None)
