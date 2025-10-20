"""Q-Storm Platform - Phase 1 implementation (Flask monolith)."""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import time

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException

import config
from db_manager import DatabaseManager
from export_manager import MarkdownExporter
from auth import require_api_key


# Flask application setup -----------------------------------------------------
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['MAX_CONTENT_LENGTH'] = config.MAX_FILE_SIZE_MB * 1024 * 1024
app.config['UPLOAD_FOLDER'] = str(config.UPLOAD_DIR)
app.config['OUTPUT_FOLDER'] = str(config.OUTPUT_DIR)

# Database initialization (Phase 2A)
db = DatabaseManager()

# Markdown exporter initialization (Phase 2B)
exporter = MarkdownExporter()

# CORS configuration
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:5000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": False
    }
})

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"],
    storage_uri="memory://"
)


# Logging configuration -------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('qstorm-app')


# Security validation helpers -------------------------------------------------
SESSION_ID_PATTERN = re.compile(r'^session_[A-Za-z0-9_-]+$')
STORE_PATTERN = re.compile(r'^[\w\-ァ-ヺ一-龥ぁ-ゔァ-ヴー・\s]+$')


def sanitize_error_message(message: str) -> str:
    """Remove potentially sensitive details from error messages."""
    sanitized = message.replace('..', '').replace('\\', '')
    sanitized = sanitized.replace('\n', ' ').replace('\r', ' ')
    return sanitized.strip() or 'Unhandled error occurred'


def validate_session_id(session_id: Optional[str]) -> str:
    """Validate session ID format and prevent path traversal."""
    if not session_id:
        raise ValueError('session_id is required')
    if '..' in session_id or '/' in session_id or '\\' in session_id:
        raise ValueError('Invalid session_id: path traversal detected')
    if not SESSION_ID_PATTERN.match(session_id):
        raise ValueError('Invalid session_id format')
    return session_id


def validate_metric(metric: Optional[str]) -> str:
    """Validate requested metric against the allowed schema."""
    metric = metric or '売上金額'
    if metric not in config.VALID_METRICS:
        allowed = ', '.join(config.VALID_METRICS)
        raise ValueError(f"Invalid metric. Must be one of: {allowed}")
    return metric


def validate_time_unit(time_unit: Optional[str]) -> str:
    """Ensure requested aggregation unit is supported."""
    time_unit = time_unit or '月'
    if time_unit not in config.VALID_TIME_UNITS:
        allowed = ', '.join(config.VALID_TIME_UNITS)
        raise ValueError(f"Invalid time_unit. Must be one of: {allowed}")
    return time_unit


def validate_bins(bins: Optional[Any]) -> int:
    """Validate histogram bin count."""
    if bins is None:
        return 20
    try:
        bins_int = int(bins)
    except (TypeError, ValueError) as exc:
        raise ValueError('bins must be an integer value') from exc
    if not 2 <= bins_int <= 200:
        raise ValueError('bins must be between 2 and 200')
    return bins_int


def validate_store(store: Optional[str]) -> Optional[str]:
    """Validate store name string when provided."""
    if store is None:
        return None
    store = store.strip()
    if not store:
        return None
    if len(store) > 100:
        raise ValueError('store value is too long')
    if not STORE_PATTERN.match(store):
        raise ValueError('store contains invalid characters')
    return store


# Session utilities -----------------------------------------------------------


def get_session_upload_dir(session_id: str) -> Path:
    return config.UPLOAD_DIR / session_id


def get_session_output_dir(session_id: str) -> Path:
    path = config.OUTPUT_DIR / session_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def locate_session_data_file(session_dir: Path) -> Path:
    """Locate the first supported dataset file inside the session directory."""
    preferred_names = [
        'cleaned_data.parquet',
        'analysis_ready.parquet',
        'prepared_dataset.parquet',
        'dataframe.parquet',
        'cleaned_data.csv',
        'analysis_ready.csv',
        'dataset.csv',
        'data.csv',
        'original_file.csv',
        'original_file.xlsx',
        'original_file.xls',
    ]
    for name in preferred_names:
        candidate = session_dir / name
        if candidate.exists():
            return candidate
    for pattern in ('*.parquet', '*.feather', '*.csv', '*.xlsx', '*.xls'):
        matches = sorted(session_dir.glob(pattern))
        if matches:
            return matches[0]
    raise FileNotFoundError('Analysis dataset not found for session')


def load_session_dataframe(session_id: str) -> pd.DataFrame:
    """Load the session's dataset into a DataFrame."""
    session_dir = get_session_upload_dir(session_id)
    if not session_dir.exists() or not session_dir.is_dir():
        raise FileNotFoundError('Session directory not found')
    data_file = locate_session_data_file(session_dir)

    try:
        if data_file.suffix.lower() == '.parquet':
            df = pd.read_parquet(data_file)
        elif data_file.suffix.lower() in {'.csv'}:
            df = pd.read_csv(data_file)
        elif data_file.suffix.lower() in {'.xlsx', '.xls'}:
            df = pd.read_excel(data_file)
        elif data_file.suffix.lower() == '.feather':
            df = pd.read_feather(data_file)
        else:
            raise ValueError('Unsupported data file format')
    except Exception as exc:
        raise ValueError('Failed to load session dataset') from exc

    if df.empty:
        raise ValueError('Session dataset is empty')
    return df


# Analysis helpers ------------------------------------------------------------


def filter_store(df: pd.DataFrame, store: Optional[str]) -> pd.DataFrame:
    if store is None:
        return df
    store_columns = ['店舗名', 'shop']
    available = [col for col in store_columns if col in df.columns]
    if not available:
        raise ValueError('Store column not present in dataset')
    filtered = df[df[available[0]] == store]
    if filtered.empty:
        raise ValueError('No records found for specified store')
    return filtered


def prepare_datetime_index(df: pd.DataFrame) -> pd.Series:
    date_columns = ['営業日付', 'Date', 'date']
    for column in date_columns:
        if column in df.columns:
            series = pd.to_datetime(df[column], errors='coerce')
            if series.notna().any():
                return series
    if {'年', '月', '日'}.issubset(df.columns):
        try:
            constructed = pd.to_datetime(
                df[['年', '月', '日']].astype(int)
                .rename(columns={'年': 'year', '月': 'month', '日': 'day'})
            )
            return constructed
        except Exception as exc:
            raise ValueError('Failed to construct datetime from year/month/day columns') from exc
    raise ValueError('Datetime column not found in dataset')


class TimeSeriesAnalyzer:
    """Execute time series aggregations for the requested metric."""

    _TIME_UNIT_TO_FREQ = {
        '日': 'D',
        '週': 'W',
        '月': 'M',
        '年': 'Y',
    }

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def analyze(self, metric: str = '売上金額', time_unit: str = '月', store: Optional[str] = None) -> Dict[str, Any]:
        metric_series = self._prepare_metric_series(metric, store)
        resampled = metric_series.resample(self._TIME_UNIT_TO_FREQ[time_unit]).sum().dropna()
        if resampled.empty:
            raise ValueError('No data points available after resampling')
        chart = self._build_chart(resampled, metric, time_unit)
        stats = self._build_statistics(resampled)
        return {'chart': chart, 'statistics': stats}

    def _prepare_metric_series(self, metric: str, store: Optional[str]) -> pd.Series:
        df = filter_store(self.df, store)
        if metric not in df.columns:
            raise ValueError(f"Metric column '{metric}' not found in dataset")
        time_index = prepare_datetime_index(df)
        series = pd.to_numeric(df[metric], errors='coerce')
        metric_series = pd.Series(series.values, index=time_index)
        metric_series = metric_series[metric_series.notna()].sort_index()
        if metric_series.empty:
            raise ValueError('Metric column contains no valid numeric data')
        return metric_series

    @staticmethod
    def _build_chart(series: pd.Series, metric: str, time_unit: str) -> Dict[str, Any]:
        x_values = [ts.to_pydatetime().isoformat() for ts in series.index]
        chart = {
            'data': [
                {
                    'type': 'scatter',
                    'mode': 'lines+markers',
                    'name': metric,
                    'x': x_values,
                    'y': [float(v) for v in series.values],
                }
            ],
            'layout': {
                'title': f'{metric} ({time_unit}別)',
                'xaxis': {'title': '日時'},
                'yaxis': {'title': metric, 'rangemode': 'tozero'},
                'hovermode': 'x unified',
            },
        }
        return chart

    @staticmethod
    def _build_statistics(series: pd.Series) -> Dict[str, Any]:
        values = series.values
        return {
            'count': int(series.count()),
            'total': float(np.sum(values)),
            'mean': float(np.mean(values)),
            'median': float(np.median(values)),
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'std': float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
            'latest_timestamp': series.index.max().to_pydatetime().isoformat(),
        }


class HistogramAnalyzer:
    """Execute histogram analysis for the requested metric."""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def analyze(self, metric: str = '売上金額', bins: int = 20, store: Optional[str] = None) -> Dict[str, Any]:
        df = filter_store(self.df, store)
        if metric not in df.columns:
            raise ValueError(f"Metric column '{metric}' not found in dataset")
        values = pd.to_numeric(df[metric], errors='coerce').dropna().to_numpy()
        if values.size == 0:
            raise ValueError('Metric column contains no valid numeric data')
        counts, bin_edges = np.histogram(values, bins=bins)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        chart = self._build_chart(metric, counts, bin_edges, bin_centers)
        stats = self._build_statistics(values)
        return {'chart': chart, 'statistics': stats}

    @staticmethod
    def _build_chart(metric: str, counts: np.ndarray, bin_edges: np.ndarray, bin_centers: np.ndarray) -> Dict[str, Any]:
        chart = {
            'data': [
                {
                    'type': 'bar',
                    'name': metric,
                    'x': [float(x) for x in bin_centers],
                    'y': [int(c) for c in counts],
                    'marker': {'color': '#1f77b4'},
                }
            ],
            'layout': {
                'title': f'{metric} ヒストグラム',
                'xaxis': {'title': metric},
                'yaxis': {'title': '度数', 'rangemode': 'tozero'},
            },
            'bin_edges': [float(edge) for edge in bin_edges],
        }
        return chart

    @staticmethod
    def _build_statistics(values: np.ndarray) -> Dict[str, Any]:
        return {
            'count': int(values.size),
            'mean': float(np.mean(values)),
            'median': float(np.median(values)),
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'std': float(np.std(values, ddof=1)) if values.size > 1 else 0.0,
        }


class ParetoAnalyzer:
    """Execute Pareto analysis (80/20 rule) for the requested metric."""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def analyze(self, metric: str = '売上金額', category_column: Optional[str] = None,
                store: Optional[str] = None, top_n: int = 20) -> Dict[str, Any]:
        """
        Pareto分析を実行（ABC分類、80/20ルール）

        Args:
            metric: 分析対象の指標（例: 売上金額）
            category_column: カテゴリ列名（Noneの場合は商品カテゴリを自動検出）
            store: 店舗名フィルタ
            top_n: 上位N件を表示（デフォルト: 20）

        Returns:
            dict: Plotlyグラフデータと統計情報（ABC分類含む）
        """
        df = filter_store(self.df, store)

        if category_column is None:
            category_column = self._detect_category_column(df)

        if category_column not in df.columns:
            raise ValueError(f"Category column '{category_column}' not found in dataset")

        if metric not in df.columns:
            raise ValueError(f"Metric column '{metric}' not found in dataset")

        category_totals = self._aggregate_by_category(df, category_column, metric)

        if category_totals.empty:
            raise ValueError('No valid data for Pareto analysis')

        category_totals = category_totals.sort_values(ascending=False)
        total = category_totals.sum()
        ratios = (category_totals / total * 100).round(2)  # パーセント
        cumulative_ratios = ratios.cumsum().round(2)

        categories = category_totals.head(top_n).index.tolist()
        values = category_totals.head(top_n).values.tolist()
        ratio_values = ratios.head(top_n).values.tolist()
        cumulative_values = cumulative_ratios.head(top_n).values.tolist()

        abc_classification = self._classify_abc(cumulative_ratios)

        chart = self._build_chart(categories, values, ratio_values, cumulative_values, metric)

        stats = self._build_statistics(
            total,
            len(category_totals),
            abc_classification,
            cumulative_ratios
        )

        return {'chart': chart, 'statistics': stats, 'abc_classification': abc_classification}

    def _detect_category_column(self, df: pd.DataFrame) -> str:
        """
        商品カテゴリ列を自動検出

        優先順位:
        1. 'カテゴリ', 'category', 'product_category'
        2. Mens_*, Womens_*, WOMEN'S_* 等の商品列
        """
        priority_columns = ['カテゴリ', 'category', 'product_category', 'カテゴリ名']
        for col in priority_columns:
            if col in df.columns:
                return col

        product_columns = [col for col in df.columns
                           if col.startswith(('Mens_', 'Womens_', "WOMEN'S_", 'LADIES_'))]

        if product_columns:
            # 最初の商品列を使用（または全商品列を集計）
            # ここでは簡易的に最初の列を返す
            # 実際には全商品列を集計する方が適切
            return '商品カテゴリ（集計）'  # 特殊キー

        for col in df.columns:
            if col not in ['店舗名', 'shop', 'year', 'month', 'day', '年', '月', '日']:
                if df[col].dtype == 'object' or df[col].dtype == 'string':
                    return col

        raise ValueError('No suitable category column found in dataset')

    def _aggregate_by_category(self, df: pd.DataFrame, category_column: str,
                               metric: str) -> pd.Series:
        """カテゴリ別に集計"""
        if category_column == '商品カテゴリ（集計）':
            product_columns = [col for col in df.columns
                               if col.startswith(('Mens_', 'Womens_', "WOMEN'S_", 'LADIES_'))]

            if not product_columns:
                raise ValueError('No product category columns found')

            category_totals = df[product_columns].sum()
            category_totals = pd.to_numeric(category_totals, errors='coerce').dropna()
            return category_totals
        else:
            grouped = df.groupby(category_column)[metric].sum()
            return pd.to_numeric(grouped, errors='coerce').dropna()

    @staticmethod
    def _classify_abc(cumulative_ratios: pd.Series) -> Dict[str, list]:
        """
        ABC分類

        A: 累積80%まで
        B: 累積80%-95%
        C: 累積95%-100%
        """
        a_items = cumulative_ratios[cumulative_ratios <= 80].index.tolist()
        b_items = cumulative_ratios[(cumulative_ratios > 80) & (cumulative_ratios <= 95)].index.tolist()
        c_items = cumulative_ratios[cumulative_ratios > 95].index.tolist()

        return {
            'A': a_items,
            'B': b_items,
            'C': c_items
        }

    @staticmethod
    def _build_chart(categories: list, values: list, ratios: list,
                     cumulative: list, metric: str) -> Dict[str, Any]:
        """Plotlyパレート図データを生成"""
        chart = {
            'data': [
                {
                    'type': 'bar',
                    'name': metric,
                    'x': categories,
                    'y': values,
                    'yaxis': 'y1',
                    'marker': {'color': '#1f77b4'},
                    'text': [f'{r}%' for r in ratios],
                    'textposition': 'outside'
                },
                {
                    'type': 'scatter',
                    'mode': 'lines+markers',
                    'name': '累積比率',
                    'x': categories,
                    'y': cumulative,
                    'yaxis': 'y2',
                    'line': {'color': '#ff7f0e', 'width': 2},
                    'marker': {'size': 8}
                }
            ],
            'layout': {
                'title': f'{metric} パレート図（ABC分析）',
                'xaxis': {'title': 'カテゴリ', 'tickangle': -45},
                'yaxis': {
                    'title': metric,
                    'rangemode': 'tozero',
                    'side': 'left'
                },
                'yaxis2': {
                    'title': '累積比率 (%)',
                    'rangemode': 'tozero',
                    'side': 'right',
                    'overlaying': 'y',
                    'range': [0, 100]
                },
                'hovermode': 'x unified',
                'showlegend': True
            }
        }
        return chart

    @staticmethod
    def _build_statistics(total: float, category_count: int,
                          abc_classification: Dict[str, list],
                          cumulative_ratios: pd.Series) -> Dict[str, Any]:
        """統計情報を生成"""
        vital_few_count = len(abc_classification['A'])
        vital_few_ratio = (vital_few_count / category_count * 100) if category_count > 0 else 0

        return {
            'total': float(total),
            'category_count': int(category_count),
            'vital_few_count': vital_few_count,
            'vital_few_ratio': round(vital_few_ratio, 2),
            'abc_counts': {
                'A': len(abc_classification['A']),
                'B': len(abc_classification['B']),
                'C': len(abc_classification['C'])
            },
            'pareto_rule_achieved': vital_few_ratio <= 30  # 20%ルールの妥当性判定
        }

# Response helpers ------------------------------------------------------------

def build_success_response(data: Dict[str, Any]) -> Any:
    return jsonify({'success': True, 'data': data})


def build_error_response(message: str, status_code: int = 400, code: Optional[str] = None) -> Any:
    response_body = {
        'success': False,
        'error': sanitize_error_message(message),
        'timestamp': datetime.utcnow().isoformat() + 'Z',
    }
    if code:
        response_body['code'] = code
    return jsonify(response_body), status_code


# API endpoints ---------------------------------------------------------------


@app.route('/health', methods=['GET'])
def health_check() -> Any:
    """
    Health check endpoint for monitoring and deployment verification.

    Returns:
        200 OK with status information if service is healthy
        503 Service Unavailable if critical components are failing

    Used by:
        - Render.com deployment health checks
        - Load balancers and monitoring systems
        - Uptime monitoring services
    """
    try:
        # Check database connectivity
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()

        # Check critical directories
        required_dirs = [
            config.UPLOAD_DIR,
            config.OUTPUT_DIR,
            config.BASE_DIR / 'data'
        ]
        for directory in required_dirs:
            if not directory.exists():
                return jsonify({
                    'status': 'unhealthy',
                    'error': f'Required directory missing: {directory.name}',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }), 503

        # All checks passed
        return jsonify({
            'status': 'healthy',
            'service': 'qstorm-platform',
            'version': '1.0.0',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'checks': {
                'database': 'ok',
                'filesystem': 'ok'
            }
        }), 200

    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': 'Service unavailable',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503


@app.route('/api/v1/analysis/timeseries', methods=['POST'])
@require_api_key
@limiter.limit("30 per minute")
def analyze_timeseries() -> Any:
    """Time series analysis endpoint."""
    start_time = time.time()  # 追加: 実行時間計測開始

    try:
        payload = request.get_json(force=True)
        session_id = validate_session_id(payload.get('session_id'))
        metric = validate_metric(payload.get('metric'))
        time_unit = validate_time_unit(payload.get('time_unit'))
        store = validate_store(payload.get('store'))

        # セッション保存（追加）
        db.save_session(session_id, store=store)

        df = load_session_dataframe(session_id)
        analyzer = TimeSeriesAnalyzer(df)
        analysis_result = analyzer.analyze(metric=metric, time_unit=time_unit, store=store)

        # 実行時間計測（追加）
        execution_time = time.time() - start_time

        # 分析結果をデータベースに保存（追加）
        analysis_id = db.save_analysis_result(
            session_id=session_id,
            analysis_type='timeseries',
            store=store,
            target_column=metric,
            parameters={
                'metric': metric,
                'time_unit': time_unit,
                'store': store
            },
            results=analysis_result,
            execution_time=execution_time
        )

        # レスポンスにメタデータ追加（追加）
        response_data = {
            'analysis_id': analysis_id,
            'session_id': session_id,
            'execution_time': round(execution_time, 3),
            **analysis_result
        }

        return build_success_response(response_data)
    except FileNotFoundError as exc:
        logger.warning('Time series analysis failed: %s', exc)
        return build_error_response(str(exc), status_code=404, code='SESSION_NOT_FOUND')
    except ValueError as exc:
        logger.warning('Time series validation error: %s', exc)
        return build_error_response(str(exc), status_code=400, code='VALIDATION_ERROR')
    except Exception as exc:  # pylint: disable=broad-except
        logger.error('Unexpected time series error: %s', exc, exc_info=True)
        return build_error_response('Internal server error', status_code=500, code='INTERNAL_ERROR')


@app.route('/api/v1/analysis/histogram', methods=['POST'])
@require_api_key
@limiter.limit("30 per minute")
def analyze_histogram() -> Any:
    """Histogram analysis endpoint."""
    start_time = time.time()

    try:
        payload = request.get_json(force=True)
        session_id = validate_session_id(payload.get('session_id'))
        metric = validate_metric(payload.get('metric'))
        bins = validate_bins(payload.get('bins'))
        store = validate_store(payload.get('store'))

        # セッション保存
        db.save_session(session_id, store=store)

        df = load_session_dataframe(session_id)
        analyzer = HistogramAnalyzer(df)
        analysis_result = analyzer.analyze(metric=metric, bins=bins, store=store)

        # 実行時間計測
        execution_time = time.time() - start_time

        # データベース保存
        analysis_id = db.save_analysis_result(
            session_id=session_id,
            analysis_type='histogram',
            store=store,
            target_column=metric,
            parameters={'metric': metric, 'bins': bins, 'store': store},
            results=analysis_result,
            execution_time=execution_time
        )

        # レスポンス
        response_data = {
            'analysis_id': analysis_id,
            'session_id': session_id,
            'execution_time': round(execution_time, 3),
            **analysis_result
        }

        return build_success_response(response_data)
    except FileNotFoundError as exc:
        logger.warning('Histogram analysis failed: %s', exc)
        return build_error_response(str(exc), status_code=404, code='SESSION_NOT_FOUND')
    except ValueError as exc:
        logger.warning('Histogram validation error: %s', exc)
        return build_error_response(str(exc), status_code=400, code='VALIDATION_ERROR')
    except Exception as exc:  # pylint: disable=broad-except
        logger.error('Unexpected histogram error: %s', exc, exc_info=True)
        return build_error_response('Internal server error', status_code=500, code='INTERNAL_ERROR')


@app.route('/api/v1/analysis/pareto', methods=['POST'])
@require_api_key
@limiter.limit("30 per minute")
def analyze_pareto() -> Any:
    """Pareto analysis endpoint (80/20 rule, ABC classification)."""
    start_time = time.time()

    try:
        payload = request.get_json(force=True)
        session_id = validate_session_id(payload.get('session_id'))
        metric = validate_metric(payload.get('metric'))
        category_column = payload.get('category_column')
        store = validate_store(payload.get('store'))
        top_n = payload.get('top_n', 20)

        if not isinstance(top_n, int) or not (5 <= top_n <= 100):
            top_n = 20

        # セッション保存
        db.save_session(session_id, store=store)

        df = load_session_dataframe(session_id)
        analyzer = ParetoAnalyzer(df)
        analysis_result = analyzer.analyze(
            metric=metric,
            category_column=category_column,
            store=store,
            top_n=top_n
        )

        # 実行時間計測
        execution_time = time.time() - start_time

        # データベース保存
        analysis_id = db.save_analysis_result(
            session_id=session_id,
            analysis_type='pareto',
            store=store,
            target_column=metric,
            parameters={
                'metric': metric,
                'category_column': category_column,
                'store': store,
                'top_n': top_n
            },
            results=analysis_result,
            execution_time=execution_time
        )

        # レスポンス
        response_data = {
            'analysis_id': analysis_id,
            'session_id': session_id,
            'execution_time': round(execution_time, 3),
            **analysis_result
        }

        return build_success_response(response_data)
    except FileNotFoundError as exc:
        logger.warning('Pareto analysis failed: %s', exc)
        return build_error_response(str(exc), status_code=404, code='SESSION_NOT_FOUND')
    except ValueError as exc:
        logger.warning('Pareto validation error: %s', exc)
        return build_error_response(str(exc), status_code=400, code='VALIDATION_ERROR')
    except Exception as exc:  # pylint: disable=broad-except
        logger.error('Unexpected Pareto error: %s', exc, exc_info=True)
        return build_error_response('Internal server error', status_code=500, code='INTERNAL_ERROR')


# History API endpoints -------------------------------------------------------

@app.route('/api/v1/history/session/<session_id>', methods=['GET'])
def get_session_history(session_id: str) -> Any:
    """セッションの分析履歴取得"""
    try:
        session_id = validate_session_id(session_id)

        results = db.get_analysis_results(session_id=session_id)
        summary = db.get_session_summary(session_id)

        return jsonify({
            'success': True,
            'session': summary,
            'analyses': results,
            'count': len(results)
        }), 200
    except ValueError as exc:
        return build_error_response(str(exc), status_code=400, code='VALIDATION_ERROR')
    except Exception as exc:  # pylint: disable=broad-except
        logger.error('Session history error: %s', exc, exc_info=True)
        return build_error_response('Internal server error', status_code=500, code='INTERNAL_ERROR')


@app.route('/api/v1/history/recent', methods=['GET'])
def get_recent_analyses() -> Any:
    """最近の分析取得"""
    try:
        limit = request.args.get('limit', 50, type=int)
        analysis_type = request.args.get('type')

        if not (1 <= limit <= 500):
            limit = 50

        results = db.get_analysis_results(
            analysis_type=analysis_type,
            limit=limit
        )

        return jsonify({
            'success': True,
            'analyses': results,
            'count': len(results)
        }), 200
    except Exception as exc:  # pylint: disable=broad-except
        logger.error('Recent analyses error: %s', exc, exc_info=True)
        return build_error_response('Internal server error', status_code=500, code='INTERNAL_ERROR')


# Markdown Export Endpoints (Phase 2B) ----------------------------------------


@app.route('/api/v1/export/markdown/<int:analysis_id>', methods=['GET'])
@require_api_key
def export_analysis_markdown(analysis_id: int) -> Any:
    """
    単一の分析結果をMarkdown形式でエクスポート

    Args:
        analysis_id: 分析結果ID

    Returns:
        Markdown形式のテキスト (Content-Type: text/markdown)

    Example:
        GET /api/v1/export/markdown/42
    """
    try:
        markdown_content = exporter.export_analysis(analysis_id)

        # レスポンスヘッダー設定
        response = app.make_response(markdown_content)
        response.headers['Content-Type'] = 'text/markdown; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename="analysis_{analysis_id}.md"'

        return response

    except ValueError as exc:
        return build_error_response(str(exc), status_code=404, code='NOT_FOUND')
    except Exception as exc:  # pylint: disable=broad-except
        logger.error('Markdown export error for analysis %s: %s', analysis_id, exc, exc_info=True)
        return build_error_response('Internal server error', status_code=500, code='INTERNAL_ERROR')


@app.route('/api/v1/export/session/<session_id>', methods=['GET'])
@require_api_key
def export_session_markdown(session_id: str) -> Any:
    """
    セッション全体の分析結果をMarkdown形式でエクスポート

    Args:
        session_id: セッションID

    Returns:
        Markdown形式のテキスト (Content-Type: text/markdown)

    Example:
        GET /api/v1/export/session/test_session_001
    """
    try:
        session_id = validate_session_id(session_id)
        markdown_content = exporter.export_session(session_id)

        # レスポンスヘッダー設定
        response = app.make_response(markdown_content)
        response.headers['Content-Type'] = 'text/markdown; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename="session_{session_id}.md"'

        return response

    except ValueError as exc:
        return build_error_response(str(exc), status_code=404, code='NOT_FOUND')
    except Exception as exc:  # pylint: disable=broad-except
        logger.error('Markdown export error for session %s: %s', session_id, exc, exc_info=True)
        return build_error_response('Internal server error', status_code=500, code='INTERNAL_ERROR')


# Error handling --------------------------------------------------------------


@app.errorhandler(HTTPException)
def handle_http_exception(error: HTTPException) -> Any:
    message = error.description or error.name
    code = f"HTTP_{error.code}" if error.code else "HTTP_ERROR"
    return build_error_response(message, status_code=error.code or 500, code=code)


@app.errorhandler(Exception)
def handle_unexpected_exception(error: Exception) -> Any:  # pylint: disable=broad-except
    logger.error('Unhandled exception: %s', error, exc_info=True)
    return build_error_response('Internal server error', status_code=500, code='INTERNAL_ERROR')


# Application entry point -----------------------------------------------------


if __name__ == '__main__':
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info('Starting Q-Storm Platform (improved app)')
    app.run(host='0.0.0.0', port=5000, debug=False)
