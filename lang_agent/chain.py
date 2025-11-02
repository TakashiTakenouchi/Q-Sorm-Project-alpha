"""LangChain pipeline skeleton for Q-Storm Lang Agent."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

import numpy as np
import pandas as pd

try:
    from langchain_openai import ChatOpenAI  # type: ignore
except ImportError:  # pragma: no cover - compatibility shim
    try:
        from langchain.chat_models import ChatOpenAI  # type: ignore
    except ImportError:  # pragma: no cover - optional dependency during scaffold
        ChatOpenAI = None  # type: ignore

try:
    from langchain.prompts import ChatPromptTemplate  # type: ignore
except ImportError:  # pragma: no cover - compatibility shim
    try:
        from langchain_core.prompts import ChatPromptTemplate  # type: ignore
    except ImportError:  # pragma: no cover - optional dependency during scaffold
        ChatPromptTemplate = None  # type: ignore

LOGGER = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).with_name('prompt.md')
STORE_COLUMNS = ['shop', '店舗名']
DEFAULT_CATEGORY_COLUMNS = [
    'Mens_JACKETS&OUTER2',
    'Mens_KNIT',
    'Mens_PANTS',
    "WOMEN'S_JACKETS2",
    "WOMEN'S_TOPS",
    "WOMEN'S_ONEPIECE",
    "WOMEN'S_bottoms",
    "WOMEN'S_SCARF & STOLES",
]
CATEGORY_LABELS = {
    'Mens_JACKETS&OUTER2': 'メンズ ジャケット・アウター',
    'Mens_KNIT': 'メンズ ニット',
    'Mens_PANTS': 'メンズ パンツ',
    "WOMEN'S_JACKETS2": 'レディース ジャケット',
    "WOMEN'S_TOPS": 'レディース トップス',
    "WOMEN'S_ONEPIECE": 'レディース ワンピース',
    "WOMEN'S_bottoms": 'レディース ボトムス',
    "WOMEN'S_SCARF & STOLES": 'レディース スカーフ・ストール',
}
PREAGGREGATED_CANDIDATES: Tuple[Tuple[str, str], ...] = (
    ('pareto_category', 'pareto_value'),
    ('category', 'value'),
    ('category', 'total'),
)


def generate_store_comparison(df: pd.DataFrame, store_a: str, store_b: str) -> Dict[str, Any]:
    """Create a natural language comparison between two stores.

    Args:
        df: Upload session dataframe (may contain raw or pre-aggregated Pareto values).
        store_a: Primary store name.
        store_b: Comparison target store name.

    Returns:
        Dict with "summary" (Japanese narrative) and "evidence" (structured metrics).
    """
    if df is None or df.empty:
        raise ValueError('分析対象のデータフレームが空です')

    store_col = _detect_store_column(df)
    working_df = df.copy()
    stores = [store_a, store_b]

    working_df = working_df[working_df[store_col].isin(stores)]
    if working_df.empty:
        raise ValueError('指定された店舗のデータが見つかりません')

    category_totals = _collect_category_totals(working_df, store_col, stores)
    if not category_totals.get(store_a) or not category_totals.get(store_b):
        raise ValueError('店舗ごとのカテゴリ集計に失敗しました')

    evidence = _build_evidence_payload(category_totals, stores)
    summary = _generate_narrative(stores, evidence)

    return {'summary': summary, 'evidence': evidence}


def _detect_store_column(df: pd.DataFrame) -> str:
    for candidate in STORE_COLUMNS:
        if candidate in df.columns:
            return candidate
    raise ValueError('店舗を識別するカラムが見つかりません (shop/店舗名)')


def _collect_category_totals(df: pd.DataFrame, store_col: str, stores: Iterable[str]) -> Dict[str, Dict[str, float]]:
    preaggregated = _extract_preaggregated(df, store_col, stores)
    if preaggregated:
        return preaggregated
    return _aggregate_from_columns(df, store_col, stores)


def _extract_preaggregated(df: pd.DataFrame, store_col: str, stores: Iterable[str]) -> Optional[Dict[str, Dict[str, float]]]:
    for category_col, value_col in PREAGGREGATED_CANDIDATES:
        if {store_col, category_col, value_col}.issubset(df.columns):
            subset = df[df[store_col].isin(stores)]
            if subset.empty:
                continue
            grouped = (
                subset.groupby([store_col, category_col])[value_col]
                .sum(min_count=1)
                .reset_index()
            )
            results: Dict[str, Dict[str, float]] = {}
            for store, group_df in grouped.groupby(store_col):
                results[store] = {
                    str(row[category_col]): float(row[value_col])
                    for _, row in group_df.iterrows()
                    if pd.notna(row[value_col]) and float(row[value_col]) > 0
                }
            if any(results.values()):
                return results
    return None


def _aggregate_from_columns(df: pd.DataFrame, store_col: str, stores: Iterable[str]) -> Dict[str, Dict[str, float]]:
    category_candidates: List[str] = list(df.attrs.get('category_columns', [])) or DEFAULT_CATEGORY_COLUMNS
    available_columns = [col for col in category_candidates if col in df.columns]

    if not available_columns:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        available_columns = [col for col in numeric_cols if col not in {store_col, 'Date'}]

    results: Dict[str, Dict[str, float]] = {}
    for store in stores:
        store_df = df[df[store_col] == store]
        metrics: Dict[str, float] = {}
        for column in available_columns:
            try:
                values = pd.to_numeric(store_df[column], errors='coerce')
            except Exception:  # pragma: no cover - defensive branch
                continue
            total = float(np.nansum(values))
            if total > 0:
                label = CATEGORY_LABELS.get(column, column)
                metrics[label] = round(total, 2)
        results[store] = dict(sorted(metrics.items(), key=lambda item: item[1], reverse=True))
    return results


def _build_evidence_payload(category_totals: Mapping[str, Mapping[str, float]], stores: Iterable[str]) -> Dict[str, Any]:
    evidence = {'stores': {}, 'differences': []}
    store_list = list(stores)
    for store in store_list:
        totals = category_totals.get(store, {})
        total_sum = sum(totals.values())
        top_categories = []
        for category, value in list(totals.items())[:5]:
            share = (value / total_sum * 100) if total_sum else 0
            top_categories.append({
                'category': category,
                'value': round(value, 2),
                'share_pct': round(share, 1),
            })
        evidence['stores'][store] = {
            'total': round(total_sum, 2),
            'top_categories': top_categories,
        }

    if len(store_list) == 2:
        store_a, store_b = store_list
        categories = set(category_totals.get(store_a, {}).keys()) | set(category_totals.get(store_b, {}).keys())
        for category in categories:
            value_a = float(category_totals.get(store_a, {}).get(category, 0.0))
            value_b = float(category_totals.get(store_b, {}).get(category, 0.0))
            evidence['differences'].append({
                'category': category,
                'store_a': round(value_a, 2),
                'store_b': round(value_b, 2),
                'difference': round(value_a - value_b, 2),
            })
        evidence['differences'].sort(key=lambda item: abs(item['difference']), reverse=True)
        evidence['differences'] = evidence['differences'][:5]
    return evidence


def _generate_narrative(stores: Iterable[str], evidence: Dict[str, Any]) -> str:
    store_a, store_b = list(stores)
    data_summary = json.dumps(evidence, ensure_ascii=False)

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        LOGGER.warning('OPENAI_API_KEY が未設定のため、フォールバック説明を返します')
        return _fallback_summary(store_a, store_b, evidence)

    if ChatOpenAI is None or ChatPromptTemplate is None:
        LOGGER.warning('LangChain関連パッケージが未インポートのためフォールバック説明を返します')
        return _fallback_summary(store_a, store_b, evidence)

    try:
        prompts = _load_prompt_sections()
        system_prompt = prompts.get('system', '')
        user_prompt = prompts.get('user', '')
        prompt = ChatPromptTemplate.from_messages([
            ('system', system_prompt),
            ('human', user_prompt),
        ])
        model_name = os.getenv('QSTORM_LLM_MODEL', 'gpt-4o')
        temperature = float(os.getenv('QSTORM_LLM_TEMPERATURE', '0.3'))
        llm = ChatOpenAI(model=model_name, temperature=temperature)
        messages = prompt.format_messages(store_a=store_a, store_b=store_b, data_summary=data_summary)
        response = llm.invoke(messages)
        content = (response.content or '').strip()
        if not content:
            LOGGER.warning('LLM応答が空のためフォールバック説明を利用します')
            return _fallback_summary(store_a, store_b, evidence)
        return content
    except Exception as exc:  # pragma: no cover - runtime safeguard
        LOGGER.warning('LangChain呼び出しに失敗しました: %s', exc)
        return _fallback_summary(store_a, store_b, evidence)


def _load_prompt_sections() -> Dict[str, str]:
    if not PROMPT_PATH.exists():
        raise FileNotFoundError('lang_agent/prompt.md が見つかりません')
    sections: Dict[str, List[str]] = {}
    current_key: Optional[str] = None
    for line in PROMPT_PATH.read_text(encoding='utf-8').splitlines():
        if line.startswith('# '):
            current_key = line[2:].strip().lower()
            sections[current_key] = []
            continue
        if current_key:
            sections[current_key].append(line)
    return {key: '\n'.join(value).strip() for key, value in sections.items()}


def _fallback_summary(store_a: str, store_b: str, evidence: Dict[str, Any]) -> str:
    stores_info = evidence.get('stores', {})
    def describe_store(store: str) -> str:
        info = stores_info.get(store, {})
        categories = info.get('top_categories', [])
        if not categories:
            return f"- {store}: 十分なカテゴリ情報がありません"
        top_parts = [f"{item['category']} ({item['share_pct']}%)" for item in categories[:3]]
        return f"- {store}: 上位カテゴリは {', '.join(top_parts)}"

    differences = evidence.get('differences', [])
    diff_lines = []
    for item in differences[:3]:
        label = item['category']
        diff_lines.append(
            f"- {label}: {store_a} {item['store_a']} 対 {store_b} {item['store_b']} (差分 {item['difference']})"
        )
    if not diff_lines:
        diff_lines.append('- 双方のカテゴリ構成に顕著な差は確認できません')

    recommendations = [
        '- 主要カテゴリで差が大きい領域は原因分析と在庫計画の見直しを検討してください',
        '- 共通して強いカテゴリは販促施策を連携してスケールさせる余地があります',
    ]

    lines = [
        '## 傾向',
        describe_store(store_a),
        describe_store(store_b),
        '## 差異',
        *diff_lines,
        '## 改善提案',
        *recommendations,
    ]
    return '\n'.join(lines)
