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
from scipy import stats

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename

import config
from db_manager import DatabaseManager
from export_manager import MarkdownExporter
from auth import require_api_key
from lang_agent.chain import DEFAULT_CATEGORY_COLUMNS as LANGCHAIN_DEFAULT_CATEGORIES
from lang_agent.chain import generate_store_comparison


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
        "origins": ["http://localhost:3001", "http://localhost:5004"],
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


# データストレージ（メモリベース）
data_storage = {}

# アップロード設定
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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


def filter_dataframe_by_date(df: pd.DataFrame, start_date_str: Optional[str], end_date_str: Optional[str]) -> pd.DataFrame:
    """Apply date range filters to the DataFrame if dates are provided."""
    if not start_date_str and not end_date_str:
        return df

    try:
        date_series = prepare_datetime_index(df)
    except ValueError:
        logger.warning("Date filter requested but no valid date column found.")
        return df

    df_filtered = df.copy()
    df_filtered['__temp_date__'] = date_series

    if start_date_str:
        try:
            start_ts = pd.to_datetime(start_date_str)
            start_ts = start_ts.normalize()
            df_filtered = df_filtered[df_filtered['__temp_date__'] >= start_ts]
        except Exception:
            pass

    if end_date_str:
        try:
            end_ts = pd.to_datetime(end_date_str)
            end_ts = end_ts.normalize() + pd.Timedelta(days=1, microseconds=-1)
            df_filtered = df_filtered[df_filtered['__temp_date__'] <= end_ts]
        except Exception:
            pass

    return df_filtered.drop(columns=['__temp_date__'])


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


def get_dataframe_for_analysis(session_id: str) -> pd.DataFrame:
    """Fetch dataframe from in-memory storage or fall back to disk."""
    df = data_storage.get(session_id)
    if df is not None:
        return df.copy()
    return load_session_dataframe(session_id)


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

        # Frontend expects: dates, values, trend_values, statistics
        dates = [ts.to_pydatetime().isoformat() for ts in resampled.index]
        values = [float(v) for v in resampled.values]

        # Calculate trend line using scipy.stats.linregress
        x_numeric = np.arange(len(values))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_numeric, values)
        trend_values = [float(slope * x + intercept) for x in x_numeric]

        statistics = self._build_statistics(resampled, slope, intercept, r_value ** 2)

        return {
            'dates': dates,
            'values': values,
            'trend_values': trend_values,
            'statistics': statistics
        }

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
    def _build_statistics(series: pd.Series, slope: float, intercept: float, r_squared: float) -> Dict[str, Any]:
        values = series.values
        return {
            'mean': float(np.mean(values)),
            'median': float(np.median(values)),
            'std': float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'trend_slope': float(slope),
            'trend_intercept': float(intercept),
            'r_squared': float(r_squared),
        }


class HistogramAnalyzer:
    """Execute histogram analysis for the requested metric."""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def analyze(self, metric: str = '売上金額', bins: int = 20, store: Optional[str] = None) -> Dict[str, Any]:
        df = filter_store(self.df, store)
        if metric not in df.columns:
            raise ValueError(f"Metric column '{metric}' not found in dataset")

        # pd.to_numeric は validate_upload で実行済みだが、安全のため再度実行
        # np.isfinite を使い、NaN と inf の両方を除外する
        series = pd.to_numeric(df[metric], errors='coerce')
        values = series[np.isfinite(series)].to_numpy()

        if values.size == 0:
            raise ValueError('Metric column contains no valid numeric data')

        # ヒストグラム計算（エッジケース対応）
        try:
            counts, bin_edges = np.histogram(values, bins=bins)
        except Exception as e:
            # データが1件しかない場合や、すべて同じ値の場合のビニング失敗をキャッチ
            logger.warning(f"np.histogram failed: {e}. Using single bin.")
            min_val = np.min(values)
            max_val = np.max(values)
            counts = np.array([values.size])
            bin_edges = np.array([min_val, max_val]) if max_val > min_val else np.array([min_val, min_val + 1])

        # Frontend expects: bin_edges, frequencies, statistics
        statistics = self._build_statistics(values)

        return {
            'bin_edges': [float(edge) for edge in bin_edges],
            'frequencies': [int(c) for c in counts],
            'statistics': statistics
        }

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
        # Calculate basic statistics
        mean_val = float(np.mean(values))
        median_val = float(np.median(values))
        std_val = float(np.std(values, ddof=1)) if values.size > 1 else 0.0
        min_val = float(np.min(values))
        max_val = float(np.max(values))

        # Calculate skewness and kurtosis using scipy.stats
        from scipy.stats import skew, kurtosis, shapiro

        # エッジケース対応: すべて同じ値、または極端な値の場合に例外が発生する
        try:
            skewness = float(skew(values))
        except Exception as e:
            logger.warning(f"Skewness calculation failed: {e}. Setting to 0.0")
            skewness = 0.0

        try:
            kurt = float(kurtosis(values))
        except Exception as e:
            logger.warning(f"Kurtosis calculation failed: {e}. Setting to 0.0")
            kurt = 0.0

        # Shapiro-Wilk test for normality
        if values.size >= 3:
            try:
                shapiro_stat, shapiro_p = shapiro(values)
                is_normal = shapiro_p > 0.05
            except Exception as e:
                logger.warning(f"Shapiro-Wilk test failed: {e}. Setting defaults.")
                shapiro_stat, shapiro_p = 0.0, 1.0
                is_normal = False
        else:
            shapiro_stat, shapiro_p = 0.0, 1.0
            is_normal = False

        return {
            'mean': mean_val,
            'median': median_val,
            'std': std_val,
            'min': min_val,
            'max': max_val,
            'skewness': skewness,
            'kurtosis': kurt,
            'shapiro_statistic': float(shapiro_stat),
            'shapiro_pvalue': float(shapiro_p),
            'is_normal': bool(is_normal),  # JSON serialization のため明示的に bool 変換
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


@app.route('/api/v2/upload/validate', methods=['POST'])
def validate_upload():
    """ファイルアップロードの検証"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'ファイルがありません'}), 400

        file = request.files['file']

        if not file or file.filename == '':
            return jsonify({'error': 'ファイルが選択されていません'}), 400

        # ファイル名のサニタイズ
        filename = secure_filename(file.filename)

        # 拡張子チェック
        if not allowed_file(filename):
            return jsonify({'error': f'許可されていないファイル形式です。許可: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

        # ファイルサイズチェック
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'error': f'ファイルサイズが大きすぎます (最大: {MAX_FILE_SIZE/1024/1024:.0f}MB)',
                'file_size': f'{file_size/1024/1024:.1f}MB'
            }), 400

        # ファイル内容の検証
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(file, encoding='utf-8-sig')
            else:
                df = pd.read_excel(file)

            # 必須カラムチェック
            required_columns = ['shop', 'Date']
            missing = [col for col in required_columns if col not in df.columns]

            if missing:
                return jsonify({'error': f'必須カラムが不足: {missing}'}), 400

            # データ検証結果
            validation_result = {
                'valid': True,
                'rows': len(df),
                'columns': list(df.columns),
                'numeric_columns': list(df.select_dtypes(include=[np.number]).columns),
                'date_columns': [],
                'shops': [],
                'date_range': {}
            }

            # 店舗情報の抽出
            if 'shop' in df.columns:
                validation_result['shops'] = df['shop'].unique().tolist()

            # 日付情報の抽出
            if 'Date' in df.columns:
                try:
                    df['Date'] = pd.to_datetime(df['Date'])
                    validation_result['date_columns'].append('Date')
                    validation_result['date_range'] = {
                        'min': df['Date'].min().strftime('%Y-%m-%d'),
                        'max': df['Date'].max().strftime('%Y-%m-%d')
                    }
                except Exception:  # pylint: disable=broad-except
                    pass

            # 主要なメトリックカラムをあらかじめ数値型に変換
            # これにより、V2 APIでの 'sum()' TypeError を防ぐ
            metrics_to_convert = [
                'Total_Sales', 'gross_profit', 'Operating_profit',
                'Number_of_guests', 'Price_per_customer',
                'Mens_JACKETS&OUTER2', 'Mens_KNIT', 'Mens_PANTS',
                "WOMEN'S_JACKETS2", "WOMEN'S_TOPS", "WOMEN'S_ONEPIECE",
                "WOMEN'S_bottoms", "WOMEN'S_SCARF & STOLES"
            ]
            for col in metrics_to_convert:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # セッションにデータを保存
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            data_storage[session_id] = df

            # フロントエンド(api.ts UploadResponse)が要求する形式でレスポンスを構築
            response_payload = {
                'session_id': session_id,
                'filename': filename,
                'columns': validation_result['columns'],
                'row_count': validation_result['rows'],
                'available_shops': validation_result.get('shops', []),
                'date_range': {
                    'start': validation_result.get('date_range', {}).get('min', ''),
                    'end': validation_result.get('date_range', {}).get('max', '')
                }
            }

            # データベースにセッションを保存
            try:
                db.create_session(
                    session_id=session_id,
                    file_path=filename,
                    file_name=filename,
                    file_size=file_size,
                    metadata={
                        'rows': len(df),
                        'columns': list(df.columns),
                        'shops': validation_result.get('shops', []),
                        'date_range': validation_result.get('date_range', {})
                    }
                )
            except Exception as db_error:  # pylint: disable=broad-except
                logger.warning(f"Database session creation warning: {db_error}")

            logger.info(
                "Upload validation succeeded | session_id=%s rows=%s columns=%s",
                session_id,
                len(df),
                len(df.columns)
            )

            return jsonify(response_payload)

        except Exception as e:  # pylint: disable=broad-except
            return jsonify({'error': f'ファイル読み込みエラー: {str(e)}'}), 400

    except Exception as e:  # pylint: disable=broad-except
        logger.error(f'Upload error: {e}')
        return jsonify({'error': f'アップロードエラー: {str(e)}'}), 500


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

        # 先にデータフレームを取得
        df = get_dataframe_for_analysis(session_id)

        # データセットに存在する数値カラムを取得
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        logger.info(f'[Timeseries] Available numeric columns: {numeric_cols}')

        # metricが指定されていない、または存在しない場合、最初の数値カラムを使用
        requested_metric = payload.get('metric')
        if not requested_metric or requested_metric not in df.columns:
            metric = numeric_cols[0] if numeric_cols else 'value'
            logger.info(f'[Timeseries] Auto-selected metric: {metric} (requested: {requested_metric})')
        else:
            metric = requested_metric
            logger.info(f'[Timeseries] Using requested metric: {metric}')

        time_unit = validate_time_unit(payload.get('time_unit'))
        store = validate_store(payload.get('store'))

        # Date filters (NEW)
        start_date = payload.get('start_date')
        end_date = payload.get('end_date')

        # Apply date filters (NEW)
        df = filter_dataframe_by_date(df, start_date, end_date)

        # セッション保存（追加）
        db.save_session(session_id, store=store)
        analyzer = TimeSeriesAnalyzer(df)
        analysis_result = analyzer.analyze(metric=metric, time_unit=time_unit, store=store)

        # Return results directly without wrapper (CHANGED)
        return jsonify(analysis_result)
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

        # 先にデータフレームを取得
        df = get_dataframe_for_analysis(session_id)

        # データセットに存在する数値カラムを取得
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()

        # metricが指定されていない、または存在しない場合、最初の数値カラムを使用
        requested_metric = payload.get('metric')
        if not requested_metric or requested_metric not in df.columns:
            metric = numeric_cols[0] if numeric_cols else 'value'
        else:
            metric = requested_metric

        bins = validate_bins(payload.get('bins'))
        store = validate_store(payload.get('store'))

        # Date filters (NEW)
        start_date = payload.get('start_date')
        end_date = payload.get('end_date')

        # Apply date filters (NEW)
        df = filter_dataframe_by_date(df, start_date, end_date)

        # セッション保存
        db.save_session(session_id, store=store)
        analyzer = HistogramAnalyzer(df)
        analysis_result = analyzer.analyze(metric=metric, bins=bins, store=store)

        # Return results directly without wrapper (CHANGED)
        return jsonify(analysis_result)
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

        # 先にデータフレームを取得
        df = get_dataframe_for_analysis(session_id)

        # データセットに存在する数値カラムを取得
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()

        # metricが指定されていない、または存在しない場合、最初の数値カラムを使用
        requested_metric = payload.get('metric')
        if not requested_metric or requested_metric not in df.columns:
            metric = numeric_cols[0] if numeric_cols else 'value'
        else:
            metric = requested_metric

        # category_columnが指定されていない、または存在しない場合、非数値カラムから選択
        requested_category = payload.get('category_column')
        if not requested_category or requested_category not in df.columns:
            non_numeric_cols = df.select_dtypes(exclude=['int64', 'float64']).columns.tolist()
            category_column = non_numeric_cols[0] if non_numeric_cols else None
        else:
            category_column = requested_category

        store = validate_store(payload.get('store'))
        top_n = payload.get('top_n', 20)

        if not isinstance(top_n, int) or not (5 <= top_n <= 100):
            top_n = 20

        # セッション保存
        db.save_session(session_id, store=store)
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


# ============================================================
# Pareto Analysis V2 - Product Category Support
# ============================================================

@app.route('/api/v2/analysis/pareto', methods=['POST'])
def analyze_pareto_v2() -> Any:
    """
    パレート分析API V2（商品カテゴリ対応版）

    Request Body:
    {
        "session_id": "session_20251027_120922",
        "category_type": "product_category" | "shop",
        "metric": "Total_Sales",
        "shop": "恵比寿" (optional),
        "start_date": "2019-04-30" (optional),
        "end_date": "2024-12-31" (optional)
    }
    """
    try:
        payload = request.get_json(force=True)
        session_id = validate_session_id(payload.get('session_id'))
        category_type = payload.get('category_type', 'product_category')
        metric = payload.get('metric', 'Total_Sales')
        shop_filter = payload.get('shop')
        start_date = payload.get('start_date')
        end_date = payload.get('end_date')

        logger.info(f'[Pareto V2] Request: session={session_id}, category_type={category_type}, metric={metric}')

        # Get dataframe
        df = get_dataframe_for_analysis(session_id)

        # Apply filters
        if shop_filter and 'shop' in df.columns:
            df = df[df['shop'] == shop_filter]

        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            if start_date:
                # タイムゾーン情報を削除して tz-naive な datetime として比較
                start_ts = pd.to_datetime(start_date)
                if start_ts.tzinfo is not None:
                    start_ts = start_ts.tz_localize(None)
                df = df[df['Date'] >= start_ts]
            if end_date:
                # タイムゾーン情報を削除して tz-naive な datetime として比較
                end_ts = pd.to_datetime(end_date)
                if end_ts.tzinfo is not None:
                    end_ts = end_ts.tz_localize(None)
                df = df[df['Date'] <= end_ts]

        if len(df) == 0:
            return build_error_response('フィルタ条件に一致するデータがありません', status_code=400)

        # ============================================================
        # 商品カテゴリベースのパレート分析
        # ============================================================
        if category_type == 'product_category':
            category_columns = [
                'Mens_JACKETS&OUTER2',
                'Mens_KNIT',
                'Mens_PANTS',
                "WOMEN'S_JACKETS2",
                "WOMEN'S_TOPS",
                "WOMEN'S_ONEPIECE",
                "WOMEN'S_bottoms",
                "WOMEN'S_SCARF & STOLES"
            ]

            category_labels = {
                'Mens_JACKETS&OUTER2': 'メンズ ジャケット・アウター',
                'Mens_KNIT': 'メンズ ニット',
                'Mens_PANTS': 'メンズ パンツ',
                "WOMEN'S_JACKETS2": 'レディース ジャケット',
                "WOMEN'S_TOPS": 'レディース トップス',
                "WOMEN'S_ONEPIECE": 'レディース ワンピース',
                "WOMEN'S_bottoms": 'レディース ボトムス',
                "WOMEN'S_SCARF & STOLES": 'レディース スカーフ・ストール'
            }

            # Calculate totals for each category
            category_sales = {}
            for col in category_columns:
                if col in df.columns:
                    # validate_uploadで変換済みだが、二重チェックとして
                    # 文字列カラムをsum()すると500エラーになるため、数値に変換
                    try:
                        total = pd.to_numeric(df[col], errors='coerce').sum()
                    except Exception:
                        total = 0.0
                    if pd.notna(total) and total > 0:
                        category_sales[category_labels.get(col, col)] = total

            if len(category_sales) == 0:
                return build_error_response('商品カテゴリデータが見つかりません', status_code=400)

            # Sort descending
            sorted_data = sorted(category_sales.items(), key=lambda x: x[1], reverse=True)
            categories = [item[0] for item in sorted_data]
            values = [item[1] for item in sorted_data]

        # ============================================================
        # 店舗ベースのパレート分析
        # ============================================================
        elif category_type == 'shop':
            if 'shop' not in df.columns:
                return build_error_response('shop列が見つかりません', status_code=400)

            shop_sales = df.groupby('shop')[metric].sum().sort_values(ascending=False)
            categories = shop_sales.index.tolist()
            values = shop_sales.values.tolist()

        else:
            return build_error_response(f'未対応のcategory_type: {category_type}', status_code=400)

        # ============================================================
        # Calculate cumulative percentage and ABC classification
        # ============================================================
        total = sum(values)

        # エッジケース対応: フィルタリング後に合計が0になる場合のゼロ除算を防ぐ
        if total == 0:
            return build_error_response(
                'フィルタ条件に一致するデータの合計が0です。フィルタ条件を変更してください。',
                status_code=400
            )

        cumulative_sum = np.cumsum(values)
        cumulative_percentage = (cumulative_sum / total * 100).tolist()

        # ABC classification
        abc_classification = {}
        for i, category in enumerate(categories):
            cumulative = cumulative_percentage[i]
            if cumulative <= 80:
                abc_classification[category] = 'A'
            elif cumulative <= 95:
                abc_classification[category] = 'B'
            else:
                abc_classification[category] = 'C'

        # Statistics
        a_count = sum(1 for v in abc_classification.values() if v == 'A')
        b_count = sum(1 for v in abc_classification.values() if v == 'B')
        c_count = sum(1 for v in abc_classification.values() if v == 'C')

        result = {
            'categories': categories,
            'values': values,
            'cumulative_percentage': cumulative_percentage,
            'abc_classification': abc_classification,
            'statistics': {
                'total': float(total),
                'a_items': a_count,
                'b_items': b_count,
                'c_items': c_count
            }
        }

        logger.info(f'[Pareto V2] Success: {len(categories)} categories processed')
        return jsonify(result)

    except FileNotFoundError as exc:
        logger.warning('Pareto V2 failed: %s', exc)
        return build_error_response(str(exc), status_code=404, code='SESSION_NOT_FOUND')
    except ValueError as exc:
        logger.warning('Pareto V2 validation error: %s', exc)
        return build_error_response(str(exc), status_code=400, code='VALIDATION_ERROR')
    except Exception as exc:  # pylint: disable=broad-except
        logger.error('Unexpected Pareto V2 error: %s', exc, exc_info=True)
        return build_error_response('Internal server error', status_code=500, code='INTERNAL_ERROR')


# ============================================================
# LangChain Narrative API (Phase 3 scaffold)
# ============================================================


@app.route('/api/v2/analysis/langchain', methods=['POST'])
@require_api_key
def analyze_langchain_narrative() -> Any:
    """Generate a LangChain-based narrative comparing two stores."""
    try:
        payload = request.get_json(force=True)
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning('Invalid JSON payload for LangChain endpoint: %s', exc)
        return build_error_response('Invalid JSON payload', status_code=400, code='INVALID_JSON')

    try:
        session_id = validate_session_id(payload.get('session_id'))
        store_a = payload.get('store_a')
        store_b = payload.get('store_b')
        if not store_a or not store_b:
            raise ValueError('store_a と store_b は必須です')

        category_columns = payload.get('category_columns') or list(LANGCHAIN_DEFAULT_CATEGORIES)
        if not isinstance(category_columns, list):
            raise ValueError('category_columns はリストで指定してください')

        df = get_dataframe_for_analysis(session_id)

        store_columns = ['shop', '店舗名']
        store_column = next((col for col in store_columns if col in df.columns), None)
        if store_column is None:
            raise ValueError('店舗判別用のカラム(shop/店舗名)が見つかりません')

        filtered_df = df[df[store_column].isin([store_a, store_b])].copy()
        if filtered_df.empty:
            return build_error_response('指定された店舗のデータが見つかりません', status_code=404, code='STORE_NOT_FOUND')

        numeric_targets = set(category_columns)
        numeric_targets.update({
            'Total_Sales',
            'gross_profit',
            'Operating_profit',
            'Number_of_guests',
            'Price_per_customer'
        })

        for column in numeric_targets:
            if column in filtered_df.columns:
                filtered_df[column] = pd.to_numeric(filtered_df[column], errors='coerce')

        filtered_df.attrs['category_columns'] = category_columns

        comparison_result = generate_store_comparison(filtered_df, store_a, store_b)

        response_payload = {
            'summary': comparison_result.get('summary', ''),
            'stores': [store_a, store_b],
            'evidence': comparison_result.get('evidence', {}),
        }

        return build_success_response(response_payload)
    except ValueError as exc:
        logger.warning('LangChain narrative validation error: %s', exc)
        return build_error_response(str(exc), status_code=400, code='VALIDATION_ERROR')
    except FileNotFoundError as exc:
        logger.warning('LangChain narrative session not found: %s', exc)
        return build_error_response(str(exc), status_code=404, code='SESSION_NOT_FOUND')
    except Exception as exc:  # pylint: disable=broad-except
        logger.error('LangChain narrative unexpected error: %s', exc, exc_info=True)
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
    app.run(host='0.0.0.0', port=5004, debug=False)
