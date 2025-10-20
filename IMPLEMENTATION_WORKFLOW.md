# Q-Storm Platform - Agile Implementation Workflow

**Workflow Version**: 1.0
**Strategy**: Agile (2-week sprints)
**Duration**: 18 weeks (9 sprints)
**Team Size**: 4-6 (Backend, Frontend, DevOps, QA)
**Generated**: 2025-10-18
**Based on**: SYSTEM_ARCHITECTURE_SPECIFICATION.md v3.0

---

## Executive Summary

### Implementation Overview

This workflow provides a comprehensive, sprint-based implementation plan for the Q-Storm Platform, transforming the current state (app.py v2.0 and app_improved.py v3.0 with partial features) into a production-ready AI-powered QC Story analysis system with complete backend APIs, integrated frontend, persistent storage, and intelligent analysis capabilities.

### Key Deliverables

| Phase | Duration | Primary Deliverable | Production Status |
|-------|----------|-------------------|------------------|
| **Phase 1 - Foundation** | Weeks 1-6 (Sprints 1-3) | Complete API coverage, integrated frontend, security hardening | ✅ Production v1.0 |
| **Phase 2 - Infrastructure** | Weeks 7-12 (Sprints 4-6) | PostgreSQL persistence, Redis caching, Celery background tasks, JWT auth | ✅ Production v2.0 |
| **Phase 3 - Intelligence** | Weeks 13-18 (Sprints 7-9) | AI agent integration (現状把握, 原因特定, 効果予測), knowledge system | ✅ Production v3.0 |

### Success Metrics

| Metric | Phase 1 Target | Phase 2 Target | Phase 3 Target |
|--------|---------------|---------------|---------------|
| **API Coverage** | 100% (all endpoints implemented) | 100% + background processing | 100% + AI insights |
| **Response Time** | <5s (10 concurrent users) | <3s (50 concurrent users) | <3s with AI analysis |
| **Uptime** | 99% | 99.5% | 99.9% |
| **User Satisfaction** | 80% | 85% | 90% |
| **Test Coverage** | >70% | >80% | >85% |

---

## Phase 1: EDA機能 + LangChain統合 (Weeks 1-6)

**⚠️ 重要**: Phase 1のみ実装を行い、Phase 2（原因特定機能）は着手しないでください。

**Goal**: EDAモード選択機能とLangChain統合による日本語洞察生成の実装

**Phase 1 Success Criteria**:
- ✅ ユーザーが「自動EDA」と「マニュアル分析」を選択可能
- ✅ Sweetvizによる包括的なEDAレポート自動生成  
- ✅ LangChainによる日本語ビジネス洞察の自動生成
- ✅ OpenAI APIエラー時のグレースフルフォールバック（テンプレートベース）
- ✅ フロントエンドからのEDA実行とレポート表示
- ✅ 単体テスト・統合テストの完備

### Sprint 1: バックエンド EDAモード選択機能 (Week 1-2)

**Sprint Goal**: 分析モード選択API + Sweetviz統合 + 統計サマリー生成

**Total Story Points**: 18

#### User Stories

**US1.1 - 分析モード選択エンドポイント** (Story Points: 5)

```
As a data analyst
I want to select between "Auto EDA" and "Manual Analysis" modes
So that I can choose the appropriate analysis approach for my workflow
```

**Acceptance Criteria**:
- ✅ Endpoint `POST /api/v1/analysis/mode` implemented (Section 4.2.6)
- ✅ Validates mode parameter (`"auto_eda"` or `"manual"`)
- ✅ Saves configuration to `uploads/<session_id>/analysis_config.json`
- ✅ Returns success response with next step guidance
- ✅ Error handling for invalid modes and missing session

**Implementation Tasks**:
```python
# app_improved.py (maintain single-file architecture)

@app.route('/api/v1/analysis/mode', methods=['POST'])
def save_analysis_mode():
    """
    Save user's analysis mode selection
    Request: {session_id, mode, target_column?, options?}
    Response: {status, config_saved, config_path, next_step}
    """
    # Task 1.1.1: Validate request parameters
    # Task 1.1.2: Validate session_id exists
    # Task 1.1.3: Create analysis_config.json with mode, timestamp, options
    # Task 1.1.4: Return success with next_step guidance
    
    data = request.get_json()
    session_id = data.get('session_id')
    mode = data.get('mode')
    
    if mode not in ['auto_eda', 'manual']:
        return jsonify({
            'status': 'error',
            'code': 'INVALID_MODE',
            'message': '無効な分析モードです',
            'allowed_values': ['auto_eda', 'manual']
        }), 400
    
    config_path = os.path.join('uploads', session_id, 'analysis_config.json')
    config = {
        'mode': mode,
        'target_column': data.get('target_column'),
        'timestamp': datetime.now().isoformat(),
        'options': data.get('options', {})
    }
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return jsonify({
        'status': 'success',
        'session_id': session_id,
        'mode': mode,
        'config_saved': True,
        'config_path': f'/uploads/{session_id}/analysis_config.json',
        'next_step': {
            'endpoint': '/api/v1/analysis/eda/execute',
            'method': 'POST',
            'description': 'EDA分析を実行してください'
        }
    })
```

**Testing Requirements**:
- Unit test: `test_analysis_mode_endpoint()` validates mode selection and config saving
- Integration test: Upload data → select mode → verify config file created
- Error test: Invalid mode returns 400 with proper error message

**Dependencies**: None (uses existing session storage)

---

**US1.2 - Sweetviz統合** (Story Points: 8)

```
As a data analyst
I want automated EDA reports generated with Sweetviz
So that I can quickly understand data distributions and relationships
```

**Acceptance Criteria**:
- ✅ Sweetviz library integrated and configured
- ✅ Function `execute_sweetviz_analysis(df, session_id, target_column)` implemented
- ✅ HTML report generated in `outputs/<session_id>/eda_report.html`
- ✅ Handles target column specification (optional)
- ✅ Execution completes within 30 seconds for typical datasets (<10,000 rows)
- ✅ Error handling for Sweetviz failures

**Implementation Tasks**:
```python
import sweetviz as sv

def execute_sweetviz_analysis(df: pd.DataFrame, session_id: str, 
                               target_column: str = None) -> str:
    """
    Execute Sweetviz EDA analysis
    
    Args:
        df: DataFrame to analyze
        session_id: Session ID for output path
        target_column: Optional target feature for supervised analysis
        
    Returns:
        Path to generated HTML report
    """
    # Task 1.2.1: Create outputs directory if not exists
    output_dir = os.path.join('outputs', session_id)
    os.makedirs(output_dir, exist_ok=True)
    
    # Task 1.2.2: Generate Sweetviz report
    try:
        if target_column and target_column in df.columns:
            report = sv.analyze(df, target_feat=target_column)
        else:
            report = sv.analyze(df)
        
        # Task 1.2.3: Save HTML report
        report_path = os.path.join(output_dir, 'eda_report.html')
        report.show_html(filepath=report_path, open_browser=False)
        
        logger.info(f'Sweetviz report generated: {report_path}')
        return report_path
        
    except Exception as e:
        logger.error(f'Sweetviz analysis failed: {e}', exc_info=True)
        raise
```

**Testing Requirements**:
- Unit test: `test_sweetviz_execution()` generates report for test DataFrame
- Integration test: Real store data → Sweetviz → verify HTML file exists and has content
- Performance test: 5,000 rows complete within 30 seconds
- Error test: Invalid target column handled gracefully

**Dependencies**:
- `pip install sweetviz==2.3.1`
- Requires matplotlib, pandas (already installed)

---

**US1.3 - 統計サマリー生成** (Story Points: 5)

```
As a data analyst
I want key statistical summaries extracted from my data
So that I can quickly identify important numeric patterns
```

**Acceptance Criteria**:
- ✅ Function `generate_stats_summary(df)` returns mean, std, min, max, median, quartiles
- ✅ Function `extract_high_correlations(df, threshold=0.7)` returns correlated pairs
- ✅ Function `detect_outliers_count(df)` counts outliers using IQR method
- ✅ All numeric columns processed
- ✅ Results returned as JSON-safe dictionary

**Implementation Tasks**:
```python
def generate_stats_summary(df: pd.DataFrame) -> dict:
    """Generate statistical summary for numeric columns"""
    # Task 1.3.1: Select numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    stats = {}
    for col in numeric_cols:
        stats[col] = {
            'mean': float(df[col].mean()),
            'std': float(df[col].std()),
            'min': float(df[col].min()),
            'max': float(df[col].max()),
            'median': float(df[col].median()),
            'q25': float(df[col].quantile(0.25)),
            'q75': float(df[col].quantile(0.75)),
            'missing': int(df[col].isnull().sum())
        }
    
    return stats

def extract_high_correlations(df: pd.DataFrame, threshold: float = 0.7) -> list:
    """Extract high correlation pairs"""
    # Task 1.3.2: Calculate correlation matrix
    corr_matrix = df.select_dtypes(include=[np.number]).corr()
    
    high_corrs = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            corr_value = corr_matrix.iloc[i, j]
            if abs(corr_value) > threshold:
                high_corrs.append({
                    'col1': corr_matrix.columns[i],
                    'col2': corr_matrix.columns[j],
                    'correlation': round(float(corr_value), 3)
                })
    
    return high_corrs

def detect_outliers_count(df: pd.DataFrame) -> dict:
    """Count outliers using IQR method"""
    # Task 1.3.3: Detect outliers for each numeric column
    outlier_counts = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        outliers = df[(df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)]
        if len(outliers) > 0:
            outlier_counts[col] = len(outliers)
    
    return outlier_counts
```

**Testing Requirements**:
- Unit test: `test_stats_summary()` validates summary calculations
- Unit test: `test_high_correlations()` detects known correlations
- Unit test: `test_outlier_detection()` counts outliers correctly
- Edge case test: Empty DataFrame, single column, all NaN values

**Dependencies**: None (uses pandas, numpy already installed)

---

**Sprint 1 Definition of Done**:
- [ ] All 3 user stories completed and tested
- [ ] Code review completed (maintain single-file architecture)
- [ ] Unit tests pass with >70% coverage
- [ ] Integration tests pass
- [ ] Documentation updated in CLAUDE.md
- [ ] No regressions in existing Pareto analysis functionality

---

### Sprint 2: LangChain統合 (Week 3-4)

**Sprint Goal**: LangChain + OpenAI GPT-3.5-turbo integration for Japanese business insights generation with fallback

**Total Story Points**: 21

#### User Stories

**US2.1 - LangChain基盤セットアップ** (Story Points: 3)

```
As a developer
I want LangChain properly configured with OpenAI API
So that we can generate natural language insights
```

**Acceptance Criteria**:
- ✅ Dependencies installed: `langchain==0.1.0`, `openai==1.12.0`
- ✅ Environment variable `OPENAI_API_KEY` validation at startup
- ✅ Function `validate_openai_api_key()` returns (bool, str) tuple
- ✅ API key masking in logs (sk-xxx***xxx)
- ✅ LangChain ChatOpenAI model initialized with proper config

**Implementation Tasks**:
```python
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
import os
import re

def validate_openai_api_key() -> tuple[bool, str]:
    """Validate OpenAI API key configuration"""
    # Task 2.1.1: Check environment variable
    api_key = os.environ.get('OPENAI_API_KEY', '')
    
    if not api_key:
        return False, 'OPENAI_API_KEY環境変数が設定されていません'
    
    # Task 2.1.2: Validate format
    if not api_key.startswith('sk-'):
        return False, 'APIキーの形式が不正です（sk-で始まる必要があります）'
    
    if len(api_key) < 20:
        return False, 'APIキーが短すぎます'
    
    # Task 2.1.3: Log with masking
    masked_key = api_key[:7] + '*' * (len(api_key) - 11) + api_key[-4:]
    logger.info(f'OpenAI APIキー検証成功: {masked_key}')
    
    return True, 'OK'

# Initialize at app startup
def init_langchain():
    """Initialize LangChain components"""
    is_valid, message = validate_openai_api_key()
    
    if not is_valid:
        logger.warning(f'LangChain機能が無効化されます: {message}')
        return None
    
    try:
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            openai_api_key=os.environ.get('OPENAI_API_KEY'),
            request_timeout=30
        )
        logger.info('LangChain ChatOpenAI initialized successfully')
        return llm
    except Exception as e:
        logger.error(f'LangChain initialization failed: {e}')
        return None
```

**Testing Requirements**:
- Unit test: `test_api_key_validation()` tests valid/invalid keys
- Integration test: Real API key → successful LLM initialization
- Error test: Missing/invalid key → proper warning and None return

**Dependencies**:
```bash
pip install langchain==0.1.0 openai==1.12.0
```

---

**US2.2 - プロンプトテンプレート設計** (Story Points: 5)

```
As a system designer
I want well-structured prompt templates for EDA insights
So that we generate consistent, high-quality Japanese explanations
```

**Acceptance Criteria**:
- ✅ Class `PromptTemplateManager` with `EDA_INSIGHTS_TEMPLATE` and `PARETO_EXPLANATION_TEMPLATE`
- ✅ Template includes dataset info, stats summary, correlations, outliers
- ✅ Variables dynamically injected via `.format()`
- ✅ Output format guides LLM to structured Japanese response
- ✅ Templates tested with mock data

**Implementation** (see SYSTEM_ARCHITECTURE_SPECIFICATION.md Section 8.3.3 for full code)

**Testing Requirements**:
- Unit test: `test_prompt_template_building()` validates variable injection
- Unit test: `test_stats_formatting()` checks formatted output
- Unit test: `test_correlation_extraction()` verifies correlation pairs
- Edge case test: Empty DataFrame, no correlations, no outliers

**Dependencies**: None (pure Python string formatting)

---

**US2.3 - EDA洞察生成関数** (Story Points: 8)

```
As a data analyst
I want LangChain to generate Japanese business insights from EDA
So that I can understand data patterns in business context
```

**Acceptance Criteria**:
- ✅ Class `LangChainInsightGenerator` with `generate_eda_insights(df, stats_summary)` method
- ✅ Returns dict with `{insights, source, model, warning}`
- ✅ LRU cache (max 100 entries, TTL 1 hour) for API responses
- ✅ Retry logic (max 3 attempts) with exponential backoff
- ✅ Automatic fallback to `_generate_template_insights()` on API error
- ✅ Warning message when using template fallback

**Implementation** (see SYSTEM_ARCHITECTURE_SPECIFICATION.md Section 8.3.4 for full code)

**Testing Requirements**:
- Unit test: `test_langchain_insights_generation()` with mocked LLM
- Unit test: `test_cache_hit()` validates caching behavior
- Unit test: `test_api_error_fallback()` verifies template fallback
- Unit test: `test_retry_logic()` confirms 3-attempt retry
- Integration test: Real API → Japanese insights generation

**Dependencies**: LangChain, OpenAI API (from US2.1)

---

**US2.4 - EDA実行エンドポイント** (Story Points: 5)

```
As a data analyst
I want a single endpoint to execute EDA with Sweetviz and LangChain
So that I can get comprehensive analysis results in one API call
```

**Acceptance Criteria**:
- ✅ Endpoint `POST /api/v1/analysis/eda/execute` implemented (Section 4.2.7)
- ✅ Integrates Sweetviz execution + LangChain insights generation
- ✅ Returns `{status, report_path, insights, key_findings, stats_summary, execution_time}`
- ✅ Handles optional filters (shop, start_date, end_date, remove_outliers)
- ✅ Graceful error handling with proper HTTP status codes

**Implementation**:
```python
class EDAAnalysisEngine:
    """EDA analysis engine integrating Sweetviz + LangChain"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.upload_dir = os.path.join('uploads', session_id)
        self.output_dir = os.path.join('outputs', session_id)
        self.langchain_generator = LangChainInsightGenerator()
        os.makedirs(self.output_dir, exist_ok=True)
    
    def execute_eda(self, df: pd.DataFrame, target_column: str = None) -> dict:
        """Execute complete EDA analysis"""
        start_time = time.time()
        
        try:
            # Step 1: Sweetviz report
            report = sv.analyze(df, target_feat=target_column) if target_column else sv.analyze(df)
            report_path = os.path.join(self.output_dir, 'eda_report.html')
            report.show_html(filepath=report_path, open_browser=False)
            
            # Step 2: Stats summary
            stats_summary = generate_stats_summary(df)
            
            # Step 3: LangChain insights
            insights_result = self.langchain_generator.generate_eda_insights(df, stats_summary)
            
            # Step 4: Key findings
            key_findings = self._extract_key_findings(df, stats_summary)
            
            execution_time = time.time() - start_time
            
            return {
                'status': 'success',
                'report_path': f'/outputs/{self.session_id}/eda_report.html',
                'insights': insights_result['insights'],
                'insights_source': insights_result['source'],
                'insights_model': insights_result['model'],
                'warning': insights_result.get('warning'),
                'key_findings': key_findings,
                'stats_summary': stats_summary,
                'execution_time': round(execution_time, 2)
            }
        except Exception as e:
            logger.error(f'EDA execution error: {e}', exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'execution_time': round(time.time() - start_time, 2)
            }

@app.route('/api/v1/analysis/eda/execute', methods=['POST'])
def execute_eda_analysis():
    """EDA execution endpoint"""
    data = request.get_json()
    session_id = data['session_id']
    
    # Load session data
    df = load_session_data(session_id)
    
    # Apply filters if provided
    if 'filters' in data:
        df = apply_filters(df, data['filters'])
    
    # Execute EDA
    engine = EDAAnalysisEngine(session_id)
    result = engine.execute_eda(df, data.get('target_column'))
    
    if result['status'] == 'error':
        return jsonify(result), 500
    
    return jsonify(result)
```

**Testing Requirements**:
- Integration test: Upload → mode selection → EDA execution → validate response structure
- Integration test: With LangChain mock → verify insights generation
- Integration test: Without API key → verify template fallback
- Performance test: 5,000 rows complete within 30 seconds
- Error test: Invalid session_id → 404 response

**Dependencies**: Sweetviz (US1.2), LangChain (US2.3)

---

**Sprint 2 Definition of Done**:
- [ ] All 4 user stories completed and tested
- [ ] LangChain integration documented in CLAUDE.md
- [ ] Environment setup guide created (Appendix E)
- [ ] Unit + integration tests pass
- [ ] Performance benchmarks met (<30s EDA execution)
- [ ] Fallback mechanism validated (works without OPENAI_API_KEY)

---

### Sprint 3: フロントエンド統合 (Week 5-6)

**Sprint Goal**: Frontend components for mode selection, EDA execution, and results display

**Total Story Points**: 16

#### User Stories

**US3.1 - AnalysisModeSelector コンポーネント** (Story Points: 8)

```
As a data analyst
I want a UI to select between Auto EDA and Manual Analysis modes
So that I can choose my analysis workflow before proceeding
```

**Acceptance Criteria**:
- ✅ React component `AnalysisModeSelector.tsx` created
- ✅ Radio buttons for "自動EDA" and "マニュアル分析" modes
- ✅ Target column dropdown (optional for Auto EDA)
- ✅ Analysis options checkboxes (correlations, outliers, max categories)
- ✅ "次へ進む" button calls `/api/v1/analysis/mode` endpoint
- ✅ Success → navigates to EDA execution screen or manual analysis dashboard
- ✅ Error → displays error message

**Implementation**:
```typescript
// frontend/src/components/AnalysisModeSelector.tsx

import React, { useState } from 'react';
import { analysisAPI } from '../services/analysisAPI';

interface AnalysisMode {
  mode: 'auto_eda' | 'manual';
  targetColumn?: string;
  options?: {
    includeCorrelations: boolean;
    includeOutliers: boolean;
    maxCategories: number;
  };
}

export const AnalysisModeSelector: React.FC<{ sessionId: string }> = ({ sessionId }) => {
  const [mode, setMode] = useState<'auto_eda' | 'manual'>('auto_eda');
  const [targetColumn, setTargetColumn] = useState<string>('');
  const [includeCorrelations, setIncludeCorrelations] = useState(true);
  const [includeOutliers, setIncludeOutliers] = useState(true);
  const [maxCategories, setMaxCategories] = useState(30);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      const config: AnalysisMode = {
        mode,
        targetColumn: mode === 'auto_eda' ? targetColumn : undefined,
        options: {
          includeCorrelations,
          includeOutliers,
          maxCategories
        }
      };

      const response = await analysisAPI.saveMode(sessionId, config);

      if (response.status === 'success') {
        // Navigate to next step
        if (mode === 'auto_eda') {
          window.location.href = `/eda-execution?session=${sessionId}`;
        } else {
          window.location.href = `/manual-analysis?session=${sessionId}`;
        }
      }
    } catch (err: any) {
      setError(err.message || '分析モードの保存に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="analysis-mode-selector">
      <h2>分析モードを選択してください</h2>

      <div className="mode-options">
        <label>
          <input
            type="radio"
            value="auto_eda"
            checked={mode === 'auto_eda'}
            onChange={(e) => setMode('auto_eda')}
          />
          自動EDA（Sweetviz）- 包括的な統計分析レポート自動生成
        </label>

        <label>
          <input
            type="radio"
            value="manual"
            checked={mode === 'manual'}
            onChange={(e) => setMode('manual')}
          />
          マニュアル分析 - パレート図、時系列、ヒストグラムを個別選択
        </label>
      </div>

      {mode === 'auto_eda' && (
        <div className="eda-options">
          <label>
            ターゲットカラム（オプション）:
            <select value={targetColumn} onChange={(e) => setTargetColumn(e.target.value)}>
              <option value="">-- 選択なし --</option>
              <option value="Total_Sales">Total_Sales</option>
              <option value="Operating_profit">Operating_profit</option>
              {/* ... 動的に列を追加 */}
            </select>
          </label>

          <label>
            <input
              type="checkbox"
              checked={includeCorrelations}
              onChange={(e) => setIncludeCorrelations(e.target.checked)}
            />
            高相関ペアの抽出
          </label>

          <label>
            <input
              type="checkbox"
              checked={includeOutliers}
              onChange={(e) => setIncludeOutliers(e.target.checked)}
            />
            外れ値の検出
          </label>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      <button onClick={handleSubmit} disabled={loading}>
        {loading ? '保存中...' : '次へ進む'}
      </button>
    </div>
  );
};
```

**API Service**:
```typescript
// frontend/src/services/analysisAPI.ts

export const analysisAPI = {
  async saveMode(sessionId: string, config: any) {
    const response = await fetch('/api/v1/analysis/mode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, ...config })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message);
    }

    return await response.json();
  },

  async executeEDA(sessionId: string, filters?: any) {
    const response = await fetch('/api/v1/analysis/eda/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, filters })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message);
    }

    return await response.json();
  }
};
```

**Testing Requirements**:
- Unit test (Jest): Component renders correctly
- Unit test: Radio button selection changes mode
- Unit test: Target column dropdown populates
- Integration test (Cypress): Full flow - upload → mode selection → EDA execution

**Dependencies**: React, TypeScript (assumed existing frontend)

---

**US3.2 - Dashboard統合** (Story Points: 5)

```
As a data analyst
I want EDA results displayed in the main dashboard
So that I can view insights alongside Pareto charts and other analyses
```

**Acceptance Criteria**:
- ✅ Component `EdaResultsPanel.tsx` displays EDA insights
- ✅ Shows Sweetviz HTML report in iframe
- ✅ Displays LangChain-generated Japanese insights (formatted markdown)
- ✅ Shows key findings as list items with severity icons
- ✅ Displays stats summary table
- ✅ "Export PDF" button (future enhancement - placeholder for now)

**Implementation**:
```typescript
// frontend/src/components/EdaResultsPanel.tsx

import React from 'react';
import ReactMarkdown from 'react-markdown';

interface EdaResult {
  status: string;
  report_path: string;
  insights: {
    source: 'langchain' | 'template';
    model: string | null;
    content: string;
    warning: string | null;
  };
  key_findings: Array<{
    type: string;
    severity?: string;
    message: string;
    details?: string[];
  }>;
  stats_summary: any;
  execution_time: number;
}

export const EdaResultsPanel: React.FC<{ result: EdaResult }> = ({ result }) => {
  return (
    <div className="eda-results-panel">
      <h2>📊 EDA Analysis Results</h2>

      {/* LangChain Insights */}
      <section className="insights-section">
        <h3>💡 ビジネス洞察 ({result.insights.source === 'langchain' ? 'AI生成' : 'テンプレート'})</h3>
        {result.insights.warning && (
          <div className="warning-banner">⚠️ {result.insights.warning}</div>
        )}
        <div className="markdown-content">
          <ReactMarkdown>{result.insights.content}</ReactMarkdown>
        </div>
      </section>

      {/* Key Findings */}
      <section className="key-findings-section">
        <h3>🔍 主要発見事項</h3>
        <ul>
          {result.key_findings.map((finding, idx) => (
            <li key={idx} className={`finding-${finding.severity || 'info'}`}>
              {finding.severity === 'warning' && '⚠️ '}
              {finding.message}
              {finding.details && (
                <ul>
                  {finding.details.map((detail, dIdx) => (
                    <li key={dIdx}>{detail}</li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      </section>

      {/* Sweetviz Report */}
      <section className="report-section">
        <h3>📄 Sweetviz EDA Report</h3>
        <iframe
          src={result.report_path}
          width="100%"
          height="800px"
          style={{ border: '1px solid #ccc' }}
          title="EDA Report"
        />
      </section>

      {/* Stats Summary Table */}
      <section className="stats-section">
        <h3>📈 統計サマリー</h3>
        <table className="stats-table">
          <thead>
            <tr>
              <th>カラム</th>
              <th>平均</th>
              <th>標準偏差</th>
              <th>最小値</th>
              <th>最大値</th>
              <th>中央値</th>
              <th>欠損値</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(result.stats_summary).map(([col, stats]: [string, any]) => (
              <tr key={col}>
                <td>{col}</td>
                <td>{stats.mean.toFixed(2)}</td>
                <td>{stats.std.toFixed(2)}</td>
                <td>{stats.min.toFixed(2)}</td>
                <td>{stats.max.toFixed(2)}</td>
                <td>{stats.median.toFixed(2)}</td>
                <td>{stats.missing}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <div className="execution-info">
        ⏱️ 実行時間: {result.execution_time.toFixed(2)}秒
      </div>
    </div>
  );
};
```

**Dashboard Integration**:
```typescript
// frontend/src/components/StoreAnalyticsDashboard.tsx

import { AnalysisModeSelector } from './AnalysisModeSelector';
import { EdaResultsPanel } from './EdaResultsPanel';

export const StoreAnalyticsDashboard: React.FC = () => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [edaResult, setEdaResult] = useState<any | null>(null);

  // ... existing code ...

  return (
    <div className="dashboard">
      {!sessionId && <FileUpload onUploadSuccess={(sid) => setSessionId(sid)} />}
      {sessionId && !edaResult && <AnalysisModeSelector sessionId={sessionId} />}
      {edaResult && <EdaResultsPanel result={edaResult} />}
    </div>
  );
};
```

**Testing Requirements**:
- Unit test: Component renders with mock EDA result
- Unit test: Markdown insights displayed correctly
- Unit test: Stats table populates from summary object
- Visual test: Screenshot comparison for UI consistency

**Dependencies**: `react-markdown` for insights rendering

---

**US3.3 - エラーハンドリングとローディング状態** (Story Points: 3)

```
As a user
I want clear feedback during EDA execution
So that I know the system is working and understand any errors
```

**Acceptance Criteria**:
- ✅ Loading spinner during EDA execution (typical 10-30 seconds)
- ✅ Progress indicator or estimated time display
- ✅ Error boundary catches frontend errors and displays user-friendly message
- ✅ Timeout handling (60 seconds) with retry option
- ✅ Network error detection and offline message

**Implementation**:
```typescript
// frontend/src/components/EdaExecutionLoader.tsx

import React, { useState, useEffect } from 'react';

export const EdaExecutionLoader: React.FC<{ sessionId: string }> = ({ sessionId }) => {
  const [progress, setProgress] = useState(0);
  const [estimatedTime, setEstimatedTime] = useState(25);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const executeEDA = async () => {
      const startTime = Date.now();
      const timeout = setTimeout(() => {
        setError('タイムアウト: EDA実行が60秒を超えました。データサイズが大きすぎる可能性があります。');
      }, 60000); // 60 second timeout

      try {
        // Simulate progress updates
        const progressInterval = setInterval(() => {
          setProgress((prev) => Math.min(prev + 5, 90));
        }, 1500);

        const result = await analysisAPI.executeEDA(sessionId);

        clearInterval(progressInterval);
        clearTimeout(timeout);
        setProgress(100);

        // Pass result to parent component
        props.onComplete(result);
      } catch (err: any) {
        clearTimeout(timeout);

        if (err.message.includes('Failed to fetch')) {
          setError('ネットワークエラー: サーバーに接続できません');
        } else {
          setError(err.message);
        }
      }
    };

    executeEDA();
  }, [sessionId]);

  if (error) {
    return (
      <div className="error-container">
        <h3>❌ エラーが発生しました</h3>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>リトライ</button>
      </div>
    );
  }

  return (
    <div className="eda-loader">
      <div className="spinner"></div>
      <h3>🔍 EDA分析を実行中...</h3>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${progress}%` }}></div>
      </div>
      <p>{progress}% 完了 (推定残り時間: {Math.max(0, estimatedTime - (progress / 100 * estimatedTime)).toFixed(0)}秒)</p>
      <ul className="task-list">
        <li className={progress > 30 ? 'completed' : 'pending'}>✓ Sweetviz分析</li>
        <li className={progress > 60 ? 'completed' : 'pending'}>✓ 統計サマリー抽出</li>
        <li className={progress > 90 ? 'completed' : 'pending'}>✓ LangChain洞察生成</li>
      </ul>
    </div>
  );
};
```

**Error Boundary**:
```typescript
// frontend/src/components/ErrorBoundary.tsx

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error boundary caught:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>申し訳ございません、エラーが発生しました</h2>
          <details>
            <summary>詳細情報</summary>
            <pre>{this.state.error?.toString()}</pre>
          </details>
          <button onClick={() => window.location.reload()}>ページを再読み込み</button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

**Testing Requirements**:
- Unit test: Error boundary catches errors
- Unit test: Timeout triggers after 60 seconds
- Integration test: Network failure displays proper message
- UX test: Loading indicators visible during execution

**Dependencies**: None (pure React)

---

**Sprint 3 Definition of Done**:
- [ ] All 3 user stories completed and tested
- [ ] Frontend components integrated into main dashboard
- [ ] End-to-end user flow tested: Upload → Mode Select → EDA Execute → View Results
- [ ] Error states handled gracefully
- [ ] UI/UX reviewed and approved
- [ ] Performance validated (<30s EDA execution, responsive UI)

---

## ⚠️ Phase 2: 原因特定機能 - NOT TO BE STARTED YET

**Important**: Phase 2（要因解析・原因特定機能）はPhase 1完了後にのみ着手してください。

Phase 1の完了条件:
- ✅ 全3スプリント完了（18ユーザーストーリー）
- ✅ 統合テスト合格
- ✅ Production環境デプロイ成功
- ✅ ユーザー受入テスト完了

**Phase 2 Preview** (実装は Phase 1 完了後):
- Sprint 4-6: 要因解析AI Agent統合
- Why-Why分析、フィッシュボーン図、散布図分析
- LangChain Agent with Tools (pandas analysis, statistical tests)
- 因果推論ライブラリ統合

---

## Phase 2: Infrastructure (Weeks 7-12)

**Goal**: Scale system with persistent storage, distributed caching, and background task processing

### Sprint 4: Persistent Database (Week 7-8)

**Sprint Goal**: Migrate from session-based file storage to PostgreSQL with knowledge base foundation

#### User Stories

**US4.1 - PostgreSQL Database Setup** (Story Points: 5)
```
As a DevOps engineer
I want PostgreSQL database for persistent storage
So that data survives server restarts
```

**Acceptance Criteria**:
- ✅ PostgreSQL 14+ installed and configured
- ✅ Database schema created with migrations
- ✅ Connection pooling configured (pgbouncer or SQLAlchemy pool)
- ✅ Backup and restore procedures documented
- ✅ Automated backup schedule (daily, 30-day retention)

**Implementation Tasks**:
```python
# Task 4.1.1: Install PostgreSQL
# sudo apt-get install postgresql-14

# Task 4.1.2: Create database and user
# CREATE DATABASE qstorm_db;
# CREATE USER qstorm_user WITH PASSWORD 'secure_password';
# GRANT ALL PRIVILEGES ON DATABASE qstorm_db TO qstorm_user;

# Task 4.1.3: Add SQLAlchemy to app_improved.py
from flask_sqlalchemy import SQLAlchemy

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
db = SQLAlchemy(app)

# Task 4.1.4: Create migration framework (Alembic)
# alembic init migrations
# alembic revision --autogenerate -m "Initial schema"
# alembic upgrade head

# Task 4.1.5: Configure automated backups
# pg_dump qstorm_db > backup_$(date +%Y%m%d).sql
```

**Testing Requirements**:
- Connection test: App connects to PostgreSQL successfully
- Migration test: Schema migrations run without errors
- Backup test: Backup/restore procedure validated
- Failover test: App handles database unavailability gracefully

**Dependencies**: None

---

**US4.2 - Database Schema Implementation** (Story Points: 8)
```
As a developer
I want database models for sessions, analyses, and knowledge base
So that I can persist application data
```

**Acceptance Criteria**:
- ✅ `users` table (id, username, password_hash, role, created_at)
- ✅ `sessions` table (session_id, user_id, filename, upload_time, metadata JSON)
- ✅ `analysis_results` table (id, session_id, analysis_type, config JSON, result JSON, created_at)
- ✅ `knowledge_base` table (id, category, problem_type, insight, effectiveness_score, usage_count)
- ✅ Indexes on frequently queried columns
- ✅ Foreign key constraints for referential integrity

**Implementation Tasks**:
```python
# app_improved.py - Database models

from datetime import datetime

class User(db.Model):
    """User authentication and authorization"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='analyst')  # admin, analyst, viewer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sessions = db.relationship('Session', backref='user', lazy=True)

class Session(db.Model):
    """Upload session tracking"""
    __tablename__ = 'sessions'

    session_id = db.Column(db.String(20), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    file_size = db.Column(db.Integer)
    rows = db.Column(db.Integer)
    columns = db.Column(db.Integer)
    metadata = db.Column(db.JSON)  # Store date_range, stores, etc.

    analysis_results = db.relationship('AnalysisResult', backref='session', lazy=True)

class AnalysisResult(db.Model):
    """Persistent analysis results"""
    __tablename__ = 'analysis_results'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(20), db.ForeignKey('sessions.session_id'), nullable=False)
    analysis_type = db.Column(db.String(50), nullable=False)  # pareto, histogram, timeseries, etc.
    config = db.Column(db.JSON)  # ParetoConfig, filters, etc.
    result = db.Column(db.JSON)  # Complete ParetoResult as JSON
    execution_time_ms = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_session_type', 'session_id', 'analysis_type'),
    )

class KnowledgeBase(db.Model):
    """Self-evolving knowledge system (QC Story insights)"""
    __tablename__ = 'knowledge_base'

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)  # quality, cost, leadtime, other
    problem_type = db.Column(db.String(100))  # High inventory, low sales, etc.
    insight = db.Column(db.Text, nullable=False)  # Natural language insight
    effectiveness_score = db.Column(db.Float, default=0.0)  # 0-1 score
    usage_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_category_score', 'category', 'effectiveness_score'),
    )

# Task 4.2.1: Define models above
# Task 4.2.2: Create migration
# Task 4.2.3: Apply migration to database
# Task 4.2.4: Implement CRUD operations for each model
# Task 4.2.5: Add data access layer functions
```

**Testing Requirements**:
- Model test: All models create/read/update/delete successfully
- Relationship test: Foreign keys enforce referential integrity
- Index test: Queries use indexes (EXPLAIN ANALYZE)
- Migration test: Schema can be upgraded and downgraded

**Dependencies**: US4.1 (PostgreSQL Setup)

---

**US4.3 - Dual-Write Migration Strategy** (Story Points: 5)
```
As a system
I want to write to both file storage and database during migration
So that I can safely transition without data loss
```

**Acceptance Criteria**:
- ✅ File upload writes to both `uploads/` directory and `sessions` table
- ✅ Analysis results written to both in-memory cache and `analysis_results` table
- ✅ Read operations check database first, fallback to file storage
- ✅ Migration complete flag to switch to database-only mode
- ✅ File cleanup job to archive old session files

**Implementation Tasks**:
```python
# app_improved.py - Dual-write pattern

@app.route('/api/v1/upload', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
def upload_file():
    """Upload file with dual-write to disk and database"""
    user_id = get_jwt_identity()

    # Existing file storage logic (app_improved.py:500-550)
    session_id = generate_session_id()
    filepath = save_uploaded_file(file, session_id)

    # NEW: Write to database (dual-write)
    session = Session(
        session_id=session_id,
        user_id=user_id,
        filename=file.filename,
        file_size=os.path.getsize(filepath),
        rows=len(df),
        columns=len(df.columns),
        metadata={
            'date_range': {'start': min_date, 'end': max_date},
            'stores': df['shop'].unique().tolist()
        }
    )
    db.session.add(session)
    db.session.commit()

    # Return session_id as before

# Task 4.3.1: Implement dual-write for uploads
# Task 4.3.2: Implement dual-write for analysis results
# Task 4.3.3: Add database-first read logic with file fallback
# Task 4.3.4: Create migration_complete flag
# Task 4.3.5: Implement file cleanup job (move old files to archive/)
```

**Testing Requirements**:
- Dual-write test: Both storage mechanisms updated
- Fallback test: Database unavailable → file storage works
- Migration test: Existing sessions accessible after migration
- Cleanup test: Old files moved to archive correctly

**Dependencies**: US4.2 (Database Schema)

---

**US4.4 - Knowledge Base Foundation** (Story Points: 3)
```
As an AI agent
I want to store and retrieve QC Story insights from knowledge base
So that the system learns from previous analyses
```

**Acceptance Criteria**:
- ✅ CRUD operations for `knowledge_base` table
- ✅ Insight search by category and problem type
- ✅ Effectiveness score update mechanism
- ✅ Top insights retrieval (by effectiveness score)
- ✅ API endpoint `/api/v2/knowledge/insights` for retrieval

**Implementation Tasks**:
```python
# Task 4.4.1: Implement knowledge base CRUD operations
def add_insight(category, problem_type, insight_text):
    """Add new insight to knowledge base"""
    insight = KnowledgeBase(
        category=category,
        problem_type=problem_type,
        insight=insight_text,
        effectiveness_score=0.5  # Initial neutral score
    )
    db.session.add(insight)
    db.session.commit()
    return insight.id

def get_insights(category=None, min_score=0.7, limit=10):
    """Retrieve top insights by effectiveness score"""
    query = KnowledgeBase.query
    if category:
        query = query.filter_by(category=category)
    query = query.filter(KnowledgeBase.effectiveness_score >= min_score)
    query = query.order_by(KnowledgeBase.effectiveness_score.desc())
    return query.limit(limit).all()

def update_effectiveness_score(insight_id, feedback_score):
    """Update effectiveness score based on user feedback"""
    insight = KnowledgeBase.query.get(insight_id)
    # Exponential moving average: new_score = 0.8 * old_score + 0.2 * feedback
    insight.effectiveness_score = 0.8 * insight.effectiveness_score + 0.2 * feedback_score
    insight.usage_count += 1
    insight.last_used = datetime.utcnow()
    db.session.commit()

# Task 4.4.2: Create API endpoint for insights
@app.route('/api/v2/knowledge/insights', methods=['GET'])
@jwt_required()
def get_knowledge_insights():
    """Retrieve insights from knowledge base"""
    category = request.args.get('category')
    insights = get_insights(category=category)
    return jsonify({
        'insights': [
            {
                'id': i.id,
                'category': i.category,
                'problem_type': i.problem_type,
                'insight': i.insight,
                'effectiveness_score': i.effectiveness_score,
                'usage_count': i.usage_count
            }
            for i in insights
        ]
    })

# Task 4.4.3: Seed knowledge base with initial QC Story insights
# Task 4.4.4: Implement feedback endpoint for score updates
```

**Testing Requirements**:
- CRUD test: All knowledge base operations work
- Search test: Insights filtered correctly by category
- Score test: Effectiveness score updates correctly
- API test: Endpoint returns valid JSON

**Dependencies**: US4.2 (Database Schema)

---

#### Sprint 4 Deliverables

- ✅ PostgreSQL database operational with complete schema
- ✅ Dual-write migration strategy implemented
- ✅ Knowledge base foundation ready for AI agent integration
- ✅ Database backup and restore procedures validated
- ✅ All data persists across server restarts

#### Sprint 4 Definition of Done

- [ ] All database migrations applied successfully
- [ ] Database performance tested (>1000 TPS)
- [ ] Backup/restore procedure validated
- [ ] Data retention policy documented
- [ ] Database monitoring configured (pg_stat_statements)
- [ ] No data loss during migration from file storage

---

### Sprint 5: Caching & Background Tasks (Week 9-10)

**Sprint Goal**: Implement Redis for distributed caching and Celery for asynchronous task processing

#### User Stories

**US5.1 - Redis Caching Infrastructure** (Story Points: 5)
```
As a system
I want Redis for distributed caching and session management
So that analysis results are shared across server instances
```

**Acceptance Criteria**:
- ✅ Redis 6+ installed and configured
- ✅ Session storage migrated from file system to Redis
- ✅ Analysis result caching in Redis with TTL
- ✅ Cache invalidation on new uploads
- ✅ Redis monitoring and health checks

**Implementation Tasks**:
```python
# Task 5.1.1: Install Redis
# sudo apt-get install redis-server

# Task 5.1.2: Configure Redis connection
import redis
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    'CACHE_DEFAULT_TIMEOUT': 3600  # 1 hour
})

# Task 5.1.3: Migrate session storage to Redis
from flask_session import Session

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url(os.environ.get('REDIS_URL'))
Session(app)

# Task 5.1.4: Implement cache decorators for analysis functions
@cache.memoize(timeout=3600)
def cached_pareto_analysis(data_hash, config_hash):
    """Cache Pareto analysis results for 1 hour"""
    # Existing ParetoAnalysisEngine.analyze() logic
    pass

# Task 5.1.5: Add cache invalidation on upload
@app.route('/api/v1/upload', methods=['POST'])
def upload_file():
    # Existing upload logic
    # Clear all cached analyses for this user
    cache.delete_memoized(cached_pareto_analysis)

# Task 5.1.6: Implement Redis health check
@app.route('/api/v2/health', methods=['GET'])
def health_check():
    redis_status = "healthy" if cache.cache._client.ping() else "unhealthy"
    return jsonify({'redis': redis_status})
```

**Testing Requirements**:
- Connection test: App connects to Redis successfully
- Cache test: Analysis results cached and retrieved correctly
- Invalidation test: Cache cleared on new uploads
- Failover test: App handles Redis unavailability (fallback to database)
- Performance test: Cache hit rate >80% for repeated analyses

**Dependencies**: None

---

**US5.2 - Celery Task Queue Setup** (Story Points: 8)
```
As a system
I want Celery for background task processing
So that long-running analyses don't block API responses
```

**Acceptance Criteria**:
- ✅ Celery 5+ configured with Redis broker
- ✅ Task result backend configured (Redis)
- ✅ Worker process running and monitored
- ✅ Task retry logic with exponential backoff
- ✅ Task monitoring dashboard (Flower)

**Implementation Tasks**:
```python
# Task 5.2.1: Install Celery
# pip install celery[redis] flower

# Task 5.2.2: Configure Celery
from celery import Celery

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    )
    celery.conf.update(app.config)
    return celery

celery = make_celery(app)

# Task 5.2.3: Define background tasks
@celery.task(bind=True, max_retries=3)
def async_pareto_analysis(self, session_id, config):
    """Background Pareto analysis task"""
    try:
        # Load session data
        df = load_session_data(session_id)

        # Perform analysis
        engine = ParetoAnalysisEngine()
        result = engine.analyze(df, config)

        # Save to database
        analysis = AnalysisResult(
            session_id=session_id,
            analysis_type='pareto',
            config=config.to_dict(),
            result=result.to_dict(),
            execution_time_ms=result.metadata['execution_time_ms']
        )
        db.session.add(analysis)
        db.session.commit()

        return {'status': 'success', 'analysis_id': analysis.id}

    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

# Task 5.2.4: Create API endpoint for async analysis
@app.route('/api/v2/analysis/pareto/async', methods=['POST'])
@jwt_required()
def async_pareto():
    """Submit Pareto analysis task to background queue"""
    data = request.json
    task = async_pareto_analysis.delay(data['session_id'], data['config'])
    return jsonify({
        'status': 'processing',
        'task_id': task.id,
        'poll_url': f'/api/v2/tasks/{task.id}'
    }), 202

# Task 5.2.5: Create task status polling endpoint
@app.route('/api/v2/tasks/<task_id>', methods=['GET'])
@jwt_required()
def get_task_status(task_id):
    """Poll task status"""
    task = async_pareto_analysis.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {'state': task.state, 'status': 'Task is waiting to be executed'}
    elif task.state == 'SUCCESS':
        response = {'state': task.state, 'result': task.result}
    elif task.state == 'FAILURE':
        response = {'state': task.state, 'error': str(task.info)}
    else:
        response = {'state': task.state, 'status': str(task.info)}
    return jsonify(response)

# Task 5.2.6: Start Celery worker
# celery -A app_improved.celery worker --loglevel=info

# Task 5.2.7: Start Flower monitoring
# celery -A app_improved.celery flower --port=5555
```

**Testing Requirements**:
- Task submission test: Tasks queued successfully
- Task execution test: Workers process tasks correctly
- Retry test: Failed tasks retry with backoff
- Monitoring test: Flower dashboard accessible
- Load test: 100 concurrent tasks processed

**Dependencies**: US5.1 (Redis Infrastructure)

---

**US5.3 - Background Knowledge Base Updates** (Story Points: 5)
```
As a system
I want to automatically update knowledge base effectiveness scores
So that the system evolves based on usage patterns
```

**Acceptance Criteria**:
- ✅ Scheduled task runs daily to recalculate effectiveness scores
- ✅ Scores updated based on usage frequency and recency
- ✅ Low-scoring insights archived (score <0.3 for >30 days)
- ✅ New insights auto-generated from top Pareto analyses
- ✅ Task logs results for debugging

**Implementation Tasks**:
```python
# Task 5.3.1: Define scheduled task (Celery Beat)
from celery.schedules import crontab

celery.conf.beat_schedule = {
    'update-knowledge-scores-daily': {
        'task': 'app_improved.update_knowledge_scores',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
}

# Task 5.3.2: Implement score update logic
@celery.task
def update_knowledge_scores():
    """Recalculate effectiveness scores for all insights"""
    insights = KnowledgeBase.query.all()

    for insight in insights:
        # Decay score for unused insights
        days_since_use = (datetime.utcnow() - insight.last_used).days if insight.last_used else 999
        decay_factor = 0.95 ** (days_since_use / 7)  # 5% decay per week

        # Boost score for frequently used insights
        usage_boost = min(0.2, insight.usage_count / 100)  # Max 0.2 boost

        # Update score
        new_score = insight.effectiveness_score * decay_factor + usage_boost
        insight.effectiveness_score = max(0.0, min(1.0, new_score))  # Clamp to [0, 1]

        # Archive low-scoring old insights
        if insight.effectiveness_score < 0.3 and days_since_use > 30:
            insight.archived = True

    db.session.commit()
    return f"Updated {len(insights)} insights"

# Task 5.3.3: Implement auto-insight generation from analyses
@celery.task
def generate_insights_from_analyses():
    """Extract insights from recent Pareto analyses"""
    # Get analyses from last 7 days
    recent = AnalysisResult.query.filter(
        AnalysisResult.created_at >= datetime.utcnow() - timedelta(days=7)
    ).all()

    for analysis in recent:
        # Extract vital_few categories
        vital_few = analysis.result['vital_few']
        if len(vital_few) <= 3:  # Strong Pareto concentration
            insight_text = f"{', '.join(vital_few)} が全体の80%を占めています"
            add_insight(
                category='pareto_concentration',
                problem_type='vital_few_identified',
                insight_text=insight_text
            )

    return f"Generated insights from {len(recent)} analyses"

# Task 5.3.4: Start Celery Beat scheduler
# celery -A app_improved.celery beat --loglevel=info
```

**Testing Requirements**:
- Schedule test: Task runs at configured time
- Score update test: Effectiveness scores change correctly
- Archive test: Low-scoring insights archived
- Insight generation test: New insights created from analyses

**Dependencies**: US4.4 (Knowledge Base Foundation), US5.2 (Celery Setup)

---

#### Sprint 5 Deliverables

- ✅ Redis caching operational with >80% hit rate
- ✅ Celery task queue processing background analyses
- ✅ Knowledge base auto-updates running on schedule
- ✅ Flower monitoring dashboard accessible
- ✅ System handles 50+ concurrent users without degradation

#### Sprint 5 Definition of Done

- [ ] Redis and Celery stable under load (>99% uptime)
- [ ] Cache hit rate monitored and optimized
- [ ] Task queue processing <1s latency
- [ ] Background jobs logged and monitored
- [ ] Failover procedures tested (Redis/Celery restart)
- [ ] Performance improvement validated (>50% faster for repeated analyses)

---

### Sprint 6: Enhanced Authentication (Week 11-12)

**Sprint Goal**: Production-grade authentication with user management and audit logging

#### User Stories

**US6.1 - User Management Interface** (Story Points: 5)
```
As an administrator
I want to manage users (create, update, delete, reset passwords)
So that I can control system access
```

**Acceptance Criteria**:
- ✅ Admin dashboard for user management
- ✅ Create user endpoint with email validation
- ✅ Update user role endpoint (admin only)
- ✅ Reset password endpoint with email verification
- ✅ Delete user endpoint with cascading session cleanup
- ✅ List users with pagination and search

**Implementation Tasks** (Omitted for brevity - follow similar pattern to Sprint 3)

**Dependencies**: Sprint 3 US3.1-US3.2

---

**US6.2 - Audit Logging System** (Story Points: 3)
```
As a security officer
I want audit logs for all sensitive operations
So that I can track system access and changes
```

**Acceptance Criteria**:
- ✅ Audit log table created (user, action, timestamp, details)
- ✅ All authentication events logged (login, logout, failed attempts)
- ✅ All data modifications logged (upload, delete, update)
- ✅ Audit log query API for administrators
- ✅ Log retention policy enforced (90 days)

**Implementation Tasks** (Omitted for brevity)

**Dependencies**: Sprint 4 US4.2 (Database Schema)

---

**US6.3 - Session Management** (Story Points: 3)
```
As a user
I want to manage my active sessions
So that I can log out from all devices
```

**Acceptance Criteria**:
- ✅ Active session list endpoint
- ✅ Logout from specific session
- ✅ Logout from all sessions (invalidate all tokens)
- ✅ Session timeout after 24 hours of inactivity
- ✅ Session extended on user activity

**Implementation Tasks** (Omitted for brevity)

**Dependencies**: Sprint 3 US3.1, Sprint 5 US5.1 (Redis for session storage)

---

#### Sprint 6 Deliverables

- ✅ Complete user management system
- ✅ Comprehensive audit logging
- ✅ Session management with timeout
- ✅ **PRODUCTION v2.0 READY** (with persistence and auth)

---

## Phase 3: Intelligence (Weeks 13-18)

**Goal**: Integrate AI agents for QC Story methodology with intelligent insights and optimization

### Sprint 7: AI Agent 1 - 現状把握 (Week 13-14)

**Sprint Goal**: Implement Current State Analysis with AutoGluon feature importance

#### User Stories

**US7.1 - AutoGluon Integration** (Story Points: 8)

(Details omitted for brevity - follows spec Section 8.1.2)

---

### Sprint 8: AI Agent 2 - 原因特定 (Week 15-16)

**Sprint Goal**: Implement Root Cause Analysis with causal inference

#### User Stories

**US8.1 - Fishbone Diagram Generation** (Story Points: 5)
**US8.2 - Logistic Regression Analysis** (Story Points: 8)
**US8.3 - Causal Inference** (Story Points: 8)

(Details omitted for brevity)

---

### Sprint 9: AI Agent 3 - 効果予測・最適化 (Week 17-18)

**Sprint Goal**: Implement Effect Prediction and Optimization with PyMC and Gurobi

#### User Stories

**US9.1 - PyMC MCMC Analysis** (Story Points: 8)
**US9.2 - Gurobi Optimization** (Story Points: 8)
**US9.3 - ROI Analysis** (Story Points: 5)

(Details omitted for brevity)

---

## Cross-Cutting Concerns

### Testing Strategy

**Test Pyramid**:
- **Unit Tests** (70%): All business logic, data processing, utilities
- **Integration Tests** (20%): API endpoints, database operations, external services
- **E2E Tests** (10%): Complete user workflows

**Test Coverage Targets**:
- Phase 1: >70%
- Phase 2: >80%
- Phase 3: >85%

**Test Automation**:
```bash
# Run all tests
pytest tests/ --cov=app_improved --cov-report=html

# Run specific test suite
pytest tests/test_pareto_system.py -v

# Run integration tests only
pytest tests/integration/ -m integration

# Run with coverage threshold enforcement
pytest --cov=app_improved --cov-fail-under=80
```

---

### DevOps & Deployment

**CI/CD Pipeline**:

1. **Commit Stage** (Triggered on every commit):
   - Linting (flake8, mypy)
   - Unit tests
   - Security scan (Bandit)

2. **Build Stage** (Triggered on PR to main):
   - Integration tests
   - Build Docker image
   - Push to staging registry

3. **Deploy Stage** (Triggered on merge to main):
   - Deploy to staging
   - Smoke tests
   - Manual approval
   - Blue-green deployment to production

**Production Deployment Checklist**:

- [ ] Database migrations tested and documented
- [ ] Backup/rollback procedures validated
- [ ] Health check endpoints responding
- [ ] Monitoring alerts configured
- [ ] Rate limiting tested under load
- [ ] Security scan passed (no critical vulnerabilities)
- [ ] Load testing completed (target: 50 concurrent users, <3s response)
- [ ] Documentation updated
- [ ] Incident response runbook reviewed
- [ ] Stakeholder sign-off obtained

---

### Monitoring & Observability

**Application Metrics**:
- Request rate, error rate, duration (RED metrics)
- Cache hit rate (Redis)
- Task queue length (Celery)
- Database connection pool utilization

**Infrastructure Metrics**:
- CPU, memory, disk usage
- Network I/O
- PostgreSQL query performance (slow query log)
- Redis memory usage

**Alerting Rules**:
- Error rate >5% for 5 minutes → Page on-call engineer
- Response time >5s for 10 minutes → Warning
- Memory usage >90% → Critical alert
- Database connections >90% of pool → Warning
- Celery queue depth >100 tasks → Warning

**Logging**:
```python
import logging
import structlog

# Structured logging for production
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()

# Usage
logger.info("pareto_analysis_completed",
            session_id=session_id,
            categories=len(result.categories),
            execution_time_ms=result.metadata['execution_time_ms'])
```

---

## Risk Management

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Single-file architecture becomes unmaintainable** | High | High | Aggressive use of nested classes, comprehensive inline documentation |
| **psutil unavailable on production** | Medium | Medium | Graceful degradation to static limits, include in requirements.txt |
| **OpenAI API rate limits** | Medium | High | Implement caching, rate limiting, fallback to template-based explanations |
| **Database migration data loss** | Low | Critical | Comprehensive testing, dual-write strategy, automated backups |
| **Celery task queue overflow** | Medium | Medium | Task TTL, queue depth monitoring, worker auto-scaling |

### Schedule Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Sprint 1-2 delays block Phase 1** | Medium | High | Critical path protection, daily standups, early escalation |
| **AutoGluon integration complexity** | High | Medium | Spike in Sprint 6 to validate approach, fallback to simpler ML |
| **PyMC/Gurobi licensing issues** | Low | High | Early procurement, open-source fallback (PuLP) |
| **Team availability issues** | Medium | Medium | Cross-training, documentation, pair programming |

---

## Success Criteria Summary

### Phase 1 Success Criteria (Production v1.0)
- ✅ All backend API endpoints implemented and tested
- ✅ Frontend fully integrated with working visualizations
- ✅ JWT authentication protecting all sensitive endpoints
- ✅ Security audit passed (no critical/high vulnerabilities)
- ✅ Load testing: 10 concurrent users, <5s response time
- ✅ Test coverage >70%
- ✅ Zero critical bugs in production

### Phase 2 Success Criteria (Production v2.0)
- ✅ PostgreSQL operational with all data persisted
- ✅ Redis caching >80% hit rate
- ✅ Celery processing background tasks successfully
- ✅ User management and audit logging functional
- ✅ Load testing: 50 concurrent users, <3s response time
- ✅ Test coverage >80%
- ✅ 99.5% uptime over 30 days

### Phase 3 Success Criteria (Production v3.0)
- ✅ All 3 AI agents (現状把握, 原因特定, 効果予測) operational
- ✅ Knowledge base self-evolving with >100 insights
- ✅ AI insights accuracy >80% (validated against historical data)
- ✅ User satisfaction score >90%
- ✅ Test coverage >85%
- ✅ 99.9% uptime over 30 days

---

## Appendices

### Appendix A: Technology Stack Summary

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Backend** | Python | 3.11 | Core runtime |
| | Flask | 2.3 | Web framework |
| | SQLAlchemy | 2.0 | ORM |
| | Celery | 5.3 | Task queue |
| | Redis | 6.2 | Caching & broker |
| | PostgreSQL | 14 | Database |
| **Frontend** | React | 18 | UI framework |
| | TypeScript | 5.0 | Type safety |
| | Plotly.js | 2.x | Visualization |
| | Ant Design | 5.x | Component library |
| | React Query | 4.x | Data fetching |
| **AI/ML** | AutoGluon | 0.8 | AutoML |
| | LangChain | 0.0.200 | LLM integration |
| | PyMC | 5.x | MCMC |
| | Gurobi | 10.x | Optimization |
| **DevOps** | Docker | 24.x | Containerization |
| | Nginx | 1.24 | Reverse proxy |
| | Gunicorn | 21.x | WSGI server |

### Appendix B: Sprint Velocity Assumptions

**Story Point Estimation**:
- 1 point = 1-2 hours of development
- 3 points = 4-6 hours (half day)
- 5 points = 1-2 days
- 8 points = 3-5 days
- 13 points = 1 week (split into smaller stories)

**Team Capacity** (per 2-week sprint):
- Backend Developer: 30-40 points
- Frontend Developer: 30-40 points
- DevOps Engineer: 20-30 points (shared responsibility)
- QA Engineer: 20-30 points (testing all sprints)

**Total Sprint Capacity**: 100-140 points across team

### Appendix C: Definition of Ready (DoR)

Before a user story enters a sprint:
- [ ] Acceptance criteria clearly defined
- [ ] Dependencies identified and resolved
- [ ] Design mockups available (if UI work)
- [ ] API contract agreed upon (if backend work)
- [ ] Test scenarios documented
- [ ] Story points estimated by team
- [ ] No blockers or external dependencies

### Appendix D: Rollback Procedures

**Database Rollback**:
```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Restore from backup
pg_restore -d qstorm_db backup_20250115.sql
```

**Application Rollback (Blue-Green)**:
```bash
# Switch traffic back to blue (previous version)
# Update load balancer configuration
# Verify health checks pass on blue environment
# Monitor error rates for 10 minutes
# If stable, decommission green environment
```

**Cache Invalidation**:
```bash
# Clear all Redis cache after rollback
redis-cli FLUSHDB
```

### Appendix E: LangChain統合ガイド

このAppendixは、Q-Storm PlatformにLangChain + OpenAI APIを統合するための環境セットアップ、トラブルシューティング、コスト管理ガイドです。

#### E.1 環境セットアップ

**Step 1: OpenAI APIキーの取得**

1. OpenAI Platform (https://platform.openai.com/) にアクセス
2. アカウント作成またはログイン
3. "API keys" セクションから新しいAPIキーを生成
4. 生成されたキー（`sk-proj-...`形式）を安全に保存

**Step 2: 依存ライブラリのインストール**

```bash
# LangChain + OpenAI dependencies
pip install langchain==0.1.0 openai==1.12.0

# 互換性確認
python3 -c "import langchain; import openai; print('✅ Dependencies installed')"
```

**Step 3: 環境変数の設定**

**Linux/Mac**:
```bash
# ~/.bashrc または ~/.zshrc に追加
export OPENAI_API_KEY='sk-proj-xxxxxxxxxxxxxxxxxxxx'

# 即座に反映
source ~/.bashrc  # または source ~/.zshrc

# 確認
echo $OPENAI_API_KEY | head -c 10  # 最初の10文字のみ表示
```

**Windows (PowerShell)**:
```powershell
# 現在のセッションのみ
$env:OPENAI_API_KEY = "sk-proj-xxxxxxxxxxxxxxxxxxxx"

# 永続的に設定
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'sk-proj-xxxxxxxxxxxxxxxxxxxx', 'User')

# 確認
$env:OPENAI_API_KEY.Substring(0, 10)
```

**Docker環境**:
```bash
# .env ファイル作成（.gitignoreに追加必須）
echo "OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxx" > .env

# Docker Compose
version: '3.8'
services:
  app:
    env_file:
      - .env
    # または
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

**Step 4: 動作確認スクリプト**

```python
#!/usr/bin/env python3
# test_langchain_setup.py

import os
import sys
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

def test_langchain_setup():
    """LangChainセットアップ確認"""

    # Step 1: API Key確認
    print("🔍 Step 1: OpenAI API Key確認...")
    api_key = os.environ.get('OPENAI_API_KEY', '')

    if not api_key:
        print("❌ OPENAI_API_KEY が設定されていません")
        print("   設定方法: export OPENAI_API_KEY='sk-proj-...'")
        return False

    if not api_key.startswith('sk-'):
        print("❌ OPENAI_API_KEY の形式が不正です")
        print(f"   現在の値: {api_key[:10]}... (sk-で始まる必要があります)")
        return False

    print(f"✅ API Key検出: {api_key[:7]}***{api_key[-4:]}")

    # Step 2: LangChain初期化
    print("\n🔍 Step 2: LangChain ChatOpenAI初期化...")
    try:
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            openai_api_key=api_key,
            request_timeout=30
        )
        print("✅ ChatOpenAI初期化成功")
    except Exception as e:
        print(f"❌ LangChain初期化失敗: {e}")
        return False

    # Step 3: API呼び出しテスト
    print("\n🔍 Step 3: OpenAI API呼び出しテスト...")
    try:
        response = llm([HumanMessage(content="こんにちは。簡潔に挨拶を返してください。")])
        print("✅ LangChain API呼び出し成功")
        print(f"   応答: {response.content}")
        return True
    except Exception as e:
        print(f"❌ LangChain API呼び出し失敗: {e}")
        if "authentication" in str(e).lower():
            print("   → APIキーが無効です。OpenAI Platformで確認してください")
        elif "quota" in str(e).lower():
            print("   → API利用制限に達しています。課金設定を確認してください")
        elif "timeout" in str(e).lower():
            print("   → タイムアウトしました。ネットワーク接続を確認してください")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Q-Storm Platform - LangChain統合セットアップ確認")
    print("=" * 60)

    success = test_langchain_setup()

    print("\n" + "=" * 60)
    if success:
        print("✅ セットアップ完了: LangChain統合が正常に動作しています")
        print("   次のステップ: python3 app_improved.py でアプリケーションを起動")
        sys.exit(0)
    else:
        print("❌ セットアップ失敗: 上記のエラーを解決してください")
        print("   ヘルプ: Appendix E トラブルシューティングセクションを参照")
        sys.exit(1)
```

**実行**:
```bash
python3 test_langchain_setup.py
```

#### E.2 トラブルシューティング

**問題1: `OPENAI_API_KEY が設定されていません`**

**原因**: 環境変数が正しく設定されていない、またはシェルセッションで読み込まれていない

**解決策**:
```bash
# 環境変数を確認
env | grep OPENAI_API_KEY

# 設定されていない場合
export OPENAI_API_KEY='sk-proj-...'

# 永続化（~/.bashrcに追加）
echo "export OPENAI_API_KEY='sk-proj-...'" >> ~/.bashrc
source ~/.bashrc
```

---

**問題2: `AuthenticationError: Incorrect API key provided`**

**原因**: APIキーが無効、期限切れ、または誤って入力されている

**解決策**:
1. OpenAI Platform (https://platform.openai.com/api-keys) でAPIキーを確認
2. 新しいAPIキーを生成して再設定
3. キーに余分なスペースや改行が含まれていないか確認

```bash
# キーの前後の空白を削除
export OPENAI_API_KEY=$(echo $OPENAI_API_KEY | xargs)

# 再テスト
python3 test_langchain_setup.py
```

---

**問題3: `RateLimitError: You exceeded your current quota`**

**原因**: OpenAI APIの無料枠を使い果たした、または課金設定がされていない

**解決策**:
1. OpenAI Platform > Billing > Usage でAPI使用量を確認
2. 課金方法を追加: OpenAI Platform > Billing > Payment methods
3. 使用制限を設定: OpenAI Platform > Billing > Limits

**一時的回避策（テンプレートフォールバック使用）**:
```python
# app_improved.py では自動的にテンプレートにフォールバックします
# LangChain未設定時は定型文を生成（警告付き）
```

---

**問題4: `Timeout error: Request timed out`**

**原因**: ネットワーク接続が遅い、またはOpenAI APIサーバーの応答が遅延

**解決策**:
```python
# タイムアウト時間を延長
llm = ChatOpenAI(
    model_name="gpt-3.5-turbo",
    temperature=0.7,
    openai_api_key=api_key,
    request_timeout=60  # 30秒 → 60秒に延長
)
```

---

**問題5: `ModuleNotFoundError: No module named 'langchain'`**

**原因**: LangChainがインストールされていない、または仮想環境が異なる

**解決策**:
```bash
# 現在のPython環境を確認
which python3
python3 --version

# LangChainを再インストール
pip install --upgrade langchain==0.1.0 openai==1.12.0

# インストール確認
python3 -c "import langchain; print(langchain.__version__)"
```

---

**問題6: `JSONDecodeError: Expecting value`**

**原因**: OpenAI APIからの応答が期待されるJSON形式ではない（稀なケース）

**解決策**:
```python
# リトライロジックで対応（app_improved.pyに実装済み）
# 最大3回リトライ → 失敗時はテンプレートフォールバック
```

#### E.3 コスト管理ガイド

**GPT-3.5-turbo 料金（2025年1月時点）**:
- Input: $0.0005 / 1K tokens (約¥0.075 / 1K tokens, 1ドル=150円換算)
- Output: $0.0015 / 1K tokens (約¥0.225 / 1K tokens)

**Q-Storm Platform 使用パターンごとの推定コスト**:

| シナリオ | Input Tokens | Output Tokens | API Call単価 | 月間100回実行時コスト |
|----------|--------------|---------------|-------------|---------------------|
| **EDA洞察生成** (標準データセット) | ~2,500 | ~800 | $0.0025 | $0.25 (約¥38) |
| **パレート解説生成** | ~1,500 | ~600 | $0.0018 | $0.18 (約¥27) |
| **大規模データセット EDA** | ~4,000 | ~1,200 | $0.0038 | $0.38 (約¥57) |

**推定月間コスト**:
- **軽量使用** (週10回EDA実行): 約¥152 (~$1.00)
- **標準使用** (日1回EDA実行): 約¥1,140 (~$7.60)
- **ヘビー使用** (日5回EDA実行): 約¥5,700 (~$38.00)

**コスト削減戦略**:

1. **LRUキャッシュ活用** (app_improved.pyに実装済み):
   - 同一データ・同一パラメータのリクエストはキャッシュから返却
   - TTL: 1時間、最大100エントリ
   - **期待削減効果**: 30-50%

2. **テンプレートフォールバック**:
   - 開発環境やデモ環境では`OPENAI_API_KEY`を設定せずテンプレートのみ使用
   - **削減効果**: 100% (API呼び出しゼロ)

3. **使用制限設定**:
   ```bash
   # OpenAI Platform > Billing > Limits で月間上限を設定
   # 例: 月$10上限 → 約400回のEDA実行が可能
   ```

4. **プロンプト最適化**:
   - 不要な変数を削除してInput Token数を削減
   - 出力形式を簡潔に（`max_tokens`パラメータで制御）

#### E.4 本番環境デプロイメント

**Step 1: APIキーの安全な管理**

```bash
# ❌ 悪い例: APIキーをコードに埋め込み
api_key = "sk-proj-xxxxxxxxxxxxxxxxxxxx"  # NEVER DO THIS

# ✅ 良い例: 環境変数から取得
api_key = os.environ.get('OPENAI_API_KEY', '')
```

**Step 2: .gitignore設定**

```.gitignore
# API Keys and secrets
.env
.env.local
.env.production

# Credentials
credentials.json
openai_key.txt
```

**Step 3: CI/CDパイプライン設定**

```yaml
# .github/workflows/deploy.yml (GitHub Actions example)

name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Verify LangChain setup
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python3 test_langchain_setup.py

      - name: Deploy to server
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          # デプロイスクリプト実行
          ./deploy.sh
```

**Step 4: モニタリング**

```python
# app_improved.py にLangChain使用統計ロギングを追加

import logging

langchain_usage_logger = logging.getLogger('langchain_usage')
langchain_usage_logger.setLevel(logging.INFO)

handler = logging.FileHandler('logs/langchain_usage.log')
handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
langchain_usage_logger.addHandler(handler)

# LangChain API呼び出し時にログ記録
def log_langchain_usage(prompt_tokens, completion_tokens, cache_hit=False):
    langchain_usage_logger.info(
        f"API_Call | Prompt: {prompt_tokens} tokens | "
        f"Completion: {completion_tokens} tokens | "
        f"Cache: {'HIT' if cache_hit else 'MISS'} | "
        f"Estimated_Cost: ${(prompt_tokens * 0.0005 + completion_tokens * 0.0015) / 1000:.4f}"
    )
```

**定期レビュー**:
```bash
# 月間使用統計の確認
cat logs/langchain_usage.log | grep "API_Call" | wc -l  # API呼び出し回数
grep "Estimated_Cost" logs/langchain_usage.log | awk '{sum+=$NF} END {print "Total: $"sum}'  # 総コスト
```

#### E.5 チェックリスト

**開発環境セットアップ**:
- [ ] OpenAI APIキー取得完了
- [ ] 環境変数 `OPENAI_API_KEY` 設定完了
- [ ] `pip install langchain openai` 完了
- [ ] `test_langchain_setup.py` 実行成功
- [ ] app_improved.py 起動時にLangChain初期化ログ確認

**本番環境デプロイメント前**:
- [ ] APIキーが `.gitignore` に追加されている
- [ ] 環境変数がCI/CD Secretsに設定されている
- [ ] 使用制限（月間上限）が設定されている
- [ ] モニタリング・ロギングが有効化されている
- [ ] フォールバック機構の動作確認完了

**トラブルシューティング参照済み**:
- [ ] Appendix E.2 のよくある問題を確認済み
- [ ] コスト管理ガイド（E.3）を理解済み
- [ ] 本番環境デプロイメント手順（E.4）を確認済み

### Appendix F: Renderデプロイメントガイド

このAppendixは、Q-Storm PlatformをRender (https://render.com) にデプロイするための完全ガイドです。Renderは、Herokuの代替として人気のPaaSプラットフォームで、無料プランからスタートでき、自動スケーリング、PostgreSQL統合、GitHub連携が標準装備されています。

#### F.1 Render設定

**プロジェクト構成要件**:
```
Q-Storm-Project3/
├── app_improved.py          # メインアプリケーション
├── requirements.txt         # Python依存関係
├── render.yaml              # Render設定ファイル（Infrastructure as Code）
├── .gitignore               # Git除外設定
├── README.md
├── uploads/                 # セッションデータ（.gitignore追加）
└── outputs/                 # 生成レポート（.gitignore追加）
```

**render.yaml サンプル設定**:

```yaml
# render.yaml - Render Infrastructure as Code
# このファイルをリポジトリルートに配置

services:
  # Web Service - Flask Application
  - type: web
    name: qstorm-platform
    env: python
    region: singapore  # または oregon (地理的に近いリージョンを選択)
    plan: starter      # 無料: free, 有料: starter ($7/month), standard ($25/month)
    branch: main       # デプロイ対象ブランチ
    buildCommand: pip install -r requirements.txt
    startCommand: python3 app_improved.py

    # 環境変数（Render Dashboard で実際の値を設定）
    envVars:
      - key: OPENAI_API_KEY
        sync: false  # Dashboard経由で手動設定（Secretとして扱う）

      - key: PORT
        value: 5003

      - key: FLASK_ENV
        value: production

      - key: DATABASE_URL
        fromDatabase:
          name: qstorm-db
          property: connectionString

      - key: MAX_FILE_SIZE_MB
        value: 200

      - key: SESSION_SECRET_KEY
        generateValue: true  # Renderが自動生成

      - key: PYTHONUNBUFFERED
        value: 1  # ログ即時出力

    # ヘルスチェック
    healthCheckPath: /api/v2/health

    # 自動デプロイ
    autoDeploy: true

    # ディスク（永続化が必要な場合）
    # Note: 無料プランではディスク永続化不可
    # disk:
    #   name: qstorm-data
    #   mountPath: /opt/render/project/src/uploads
    #   sizeGB: 1

  # Background Worker (オプション - Celeryタスク用)
  # - type: worker
  #   name: qstorm-worker
  #   env: python
  #   branch: main
  #   buildCommand: pip install -r requirements.txt
  #   startCommand: celery -A app_improved.celery worker --loglevel=info

# Database - PostgreSQL
databases:
  - name: qstorm-db
    databaseName: qstorm_production
    user: qstorm_user
    plan: starter  # 無料: free (90日後削除), 有料: starter ($7/month)
    region: singapore
    ipAllowList: []  # 空 = すべてのIPから接続可能（Web Serviceのみアクセス）

# Redis (オプション - キャッシング用)
# - type: redis
#   name: qstorm-redis
#   plan: starter
#   region: singapore
#   maxmemoryPolicy: allkeys-lru
#   ipAllowList: []
```

**requirements.txt 更新**:

```txt
# requirements.txt - Render用に最適化

# Core Framework
Flask==3.0.0
flask-cors==4.0.0
Werkzeug==3.0.1

# Data Processing
pandas==2.1.4
numpy==1.26.2
openpyxl==3.1.2

# Analysis & Visualization
scipy==1.11.4
matplotlib==3.8.2
sweetviz==2.3.1

# NLP/LLM
langchain==0.1.0
openai==1.12.0

# System Monitoring
psutil==5.9.6

# Production Server
gunicorn==21.2.0      # 本番用WSGIサーバー（Renderで推奨）

# Database (Phase 2以降で有効化)
# psycopg2-binary==2.9.9  # PostgreSQL adapter
# SQLAlchemy==2.0.23      # ORM

# Caching (Phase 2以降で有効化)
# redis==5.0.1
# celery==5.3.4

# Environment Management
python-dotenv==1.0.0
```

**ビルドコマンド詳細**:

```bash
# Renderが実行するビルドプロセス

# Step 1: Python環境セットアップ（自動）
# Python 3.11が自動インストールされる

# Step 2: 依存関係インストール
pip install -r requirements.txt

# Step 3: 静的ファイル収集（必要に応じて）
# mkdir -p outputs uploads

# Step 4: データベースマイグレーション（Phase 2以降）
# python3 manage.py db upgrade
```

**スタートコマンド詳細**:

```bash
# Option 1: 開発サーバー（小規模・テスト用）
python3 app_improved.py

# Option 2: Gunicorn（本番推奨 - 4ワーカー）
gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 app_improved:app

# Option 3: Gunicorn with 非同期ワーカー（高負荷対応）
gunicorn --bind 0.0.0.0:$PORT --workers 4 --worker-class gevent --timeout 120 app_improved:app
```

**推奨スタートコマンド** (render.yamlに記載):
```yaml
startCommand: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app_improved:app
```

**環境変数リスト（完全版）**:

| 環境変数名 | 必須 | デフォルト値 | 説明 | Render設定方法 |
|-----------|------|-------------|------|---------------|
| `OPENAI_API_KEY` | ❌ (Phase 1で推奨) | なし | OpenAI API認証キー | Dashboard > Environment > Add Secret |
| `PORT` | ✅ | 5003 | アプリケーションポート | 自動設定（Renderが注入） |
| `FLASK_ENV` | ✅ | production | Flask環境モード | `production` 固定 |
| `DATABASE_URL` | ❌ (Phase 2で必須) | なし | PostgreSQL接続URL | 自動設定（DB連携時） |
| `SESSION_SECRET_KEY` | ✅ | ランダム生成 | Flask session暗号化キー | Generate Value有効化 |
| `MAX_FILE_SIZE_MB` | ❌ | 200 | 最大アップロードファイルサイズ | 200-500 |
| `PYTHONUNBUFFERED` | ✅ | 1 | ログバッファリング無効化 | `1` 固定 |
| `REDIS_URL` | ❌ (Phase 2) | なし | Redisキャッシュ接続URL | 自動設定（Redis連携時） |

#### F.2 GitHub連携

**リポジトリ構成要件**:

```
GitHub Repository: Q-Storm-Platform
├── main branch          # 本番環境（Render自動デプロイ）
├── develop branch       # 開発環境（ステージング）
└── feature/* branches   # 機能開発ブランチ
```

**推奨ブランチ戦略**:

```
main (protected)
  ↑ Pull Request + Review Required
develop
  ↑ Pull Request
feature/eda-langchain-integration
feature/frontend-dashboard
hotfix/critical-bug-fix
```

**GitHub連携手順**:

**Step 1: Renderアカウント作成とGitHub接続**

```bash
# 1. Render (https://render.com) でアカウント作成
# 2. "Connect GitHub" をクリック
# 3. リポジトリアクセス権限を承認
# 4. "Q-Storm-Platform" リポジトリを選択
```

**Step 2: 自動デプロイメント設定**

Render Dashboard:
```
1. New > Web Service
2. Connect Repository: Q-Storm-Platform
3. Branch: main (本番) または develop (ステージング)
4. Build Command: pip install -r requirements.txt
5. Start Command: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app_improved:app
6. Auto-Deploy: Yes (mainブランチへのpush/mergeで自動デプロイ)
```

**Step 3: プルリクエストプレビュー（オプション - 有料プラン）**

```yaml
# render.yaml に追加

services:
  - type: web
    name: qstorm-platform
    # ... (既存設定)

    # Pull Request Previews (Standardプラン以上)
    previewsEnabled: true
    previewsExpireAfterDays: 7
```

これにより、PRごとに一時的なプレビュー環境が自動生成されます。

**Step 4: .gitignore 設定**

```gitignore
# .gitignore - Renderデプロイ用

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Flask
instance/
.webassets-cache

# Data & Uploads (Renderでは永続化されない)
uploads/*
!uploads/.gitkeep
outputs/*
!outputs/.gitkeep

# Logs
*.log
logs/

# Environment Variables
.env
.env.local
.env.production

# API Keys & Secrets
credentials.json
openai_key.txt

# OS Files
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp

# Test Coverage
htmlcov/
.coverage
.pytest_cache/

# Database
*.db
*.sqlite3

# Backups
*.backup
IMPLEMENTATION_WORKFLOW.md.backup
```

**Step 5: GitHub Actions CI/CD（オプション）**

```yaml
# .github/workflows/render-deploy.yml

name: Deploy to Render

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run tests
        run: |
          python3 -m pytest test_pareto_system.py -v

      - name: Verify LangChain setup (mock)
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python3 test_langchain_setup.py || echo "LangChain test skipped (no API key)"

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to Render
        run: |
          echo "Render auto-deploys on git push to main"
          echo "No manual deployment needed"
```

#### F.3 データベース設定

**PostgreSQL接続設定（Phase 2以降）**:

**Step 1: Render PostgreSQL作成**

```bash
# Render Dashboard
1. New > PostgreSQL
2. Name: qstorm-db
3. Database: qstorm_production
4. User: qstorm_user (自動生成)
5. Plan: Starter ($7/month) または Free (90日制限)
6. Region: Singapore (Web Serviceと同じリージョン推奨)
```

**Step 2: 接続URL取得**

Renderが自動生成する環境変数:
```bash
DATABASE_URL=postgresql://qstorm_user:password@dpg-xxxxx.singapore-postgres.render.com/qstorm_production

# 内部接続URL（より高速 - 同リージョン内通信）
DATABASE_URL_INTERNAL=postgresql://qstorm_user:password@dpg-xxxxx/qstorm_production
```

**Step 3: app_improved.py でのDB接続**

```python
# app_improved.py - PostgreSQL統合（Phase 2）

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 環境変数からDB URL取得（Renderが自動注入）
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Renderの内部URL優先（高速化）
    DATABASE_URL_INTERNAL = os.environ.get('DATABASE_URL_INTERNAL', DATABASE_URL)

    # SQLAlchemy engine作成
    engine = create_engine(
        DATABASE_URL_INTERNAL,
        pool_size=5,              # 接続プールサイズ
        max_overflow=10,          # 最大追加接続数
        pool_pre_ping=True,       # 接続有効性チェック
        pool_recycle=3600,        # 1時間で接続リサイクル
        echo=False                # SQLログ無効化（本番環境）
    )

    Session = sessionmaker(bind=engine)
    logger.info(f'PostgreSQL接続成功: {DATABASE_URL_INTERNAL.split("@")[1]}')
else:
    logger.warning('DATABASE_URL未設定 - ファイルベースストレージを使用')
    engine = None
```

**マイグレーション戦略**:

**Option 1: Alembic（推奨 - Phase 2）**

```bash
# Alembicセットアップ
pip install alembic

# 初期化
alembic init migrations

# マイグレーションファイル作成
alembic revision --autogenerate -m "Initial schema"

# 本番適用（Renderビルドコマンドに追加）
alembic upgrade head
```

**render.yaml にマイグレーション追加**:
```yaml
services:
  - type: web
    name: qstorm-platform
    buildCommand: |
      pip install -r requirements.txt
      alembic upgrade head  # マイグレーション自動実行
    startCommand: gunicorn --bind 0.0.0.0:$PORT --workers 2 app_improved:app
```

**Option 2: 手動SQL実行（Phase 1 - シンプル）**

```sql
-- Render Dashboard > Database > Query で実行

CREATE TABLE IF NOT EXISTS analysis_sessions (
    session_id VARCHAR(50) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    store VARCHAR(20),
    file_name VARCHAR(255),
    row_count INTEGER,
    column_count INTEGER
);

CREATE INDEX idx_sessions_created ON analysis_sessions(created_at);
```

**データベースバックアップ**:

```bash
# Render Dashboard > Database > Backups
# 自動バックアップ: 毎日（Starterプラン以上）
# 手動バックアップ: "Create Backup" ボタン

# ローカルへのエクスポート
pg_dump $DATABASE_URL > qstorm_backup_$(date +%Y%m%d).sql

# リストア
psql $DATABASE_URL < qstorm_backup_20250120.sql
```

#### F.4 環境変数管理

**Render Dashboardでの環境変数設定手順**:

**Step 1: Web Service > Environment タブ**

```
1. Environment Variables セクション
2. "Add Environment Variable" クリック
3. Key/Value入力
4. Secret (機密情報) の場合は "Secret" にチェック
```

**Step 2: 必須環境変数の設定**

**OpenAI APIキー（LangChain統合用）**:
```
Key: OPENAI_API_KEY
Value: sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
Type: Secret ✅
```

**データベースURL（Phase 2 - 自動設定）**:
```
Key: DATABASE_URL
Value: (Render PostgreSQL連携時に自動設定)
Type: Secret ✅
```

**Flaskセッションシークレット**:
```
Key: SESSION_SECRET_KEY
Value: (Generate Valueで自動生成)
Type: Secret ✅
```

**その他の推奨設定**:
```
Key: MAX_FILE_SIZE_MB
Value: 200
Type: Plain

Key: FLASK_ENV
Value: production
Type: Plain

Key: PYTHONUNBUFFERED
Value: 1
Type: Plain

Key: LOG_LEVEL
Value: INFO
Type: Plain
```

**環境変数の検証スクリプト**:

```python
# verify_env.py - デプロイ前の環境変数チェック

import os
import sys

def verify_environment():
    """必須環境変数の存在確認"""

    required_vars = {
        'PORT': 'アプリケーションポート',
        'FLASK_ENV': 'Flask環境モード',
        'SESSION_SECRET_KEY': 'セッション暗号化キー',
    }

    recommended_vars = {
        'OPENAI_API_KEY': 'LangChain統合（Phase 1推奨）',
        'DATABASE_URL': 'PostgreSQL接続（Phase 2必須）',
    }

    missing_required = []
    missing_recommended = []

    print("=" * 60)
    print("環境変数検証")
    print("=" * 60)

    # 必須変数チェック
    for var, desc in required_vars.items():
        if os.environ.get(var):
            print(f"✅ {var}: {desc}")
        else:
            print(f"❌ {var}: {desc} - 未設定")
            missing_required.append(var)

    # 推奨変数チェック
    for var, desc in recommended_vars.items():
        if os.environ.get(var):
            print(f"✅ {var}: {desc}")
        else:
            print(f"⚠️  {var}: {desc} - 未設定（推奨）")
            missing_recommended.append(var)

    print("=" * 60)

    if missing_required:
        print(f"❌ エラー: 必須環境変数が未設定です: {', '.join(missing_required)}")
        sys.exit(1)

    if missing_recommended:
        print(f"⚠️  警告: 推奨環境変数が未設定です: {', '.join(missing_recommended)}")
        print("   一部機能が制限される可能性があります")

    print("✅ 環境変数検証完了")
    return True

if __name__ == '__main__':
    verify_environment()
```

**ビルドプロセスに統合**:
```yaml
# render.yaml
services:
  - type: web
    buildCommand: |
      pip install -r requirements.txt
      python3 verify_env.py
```

#### F.5 モニタリングとログ

**Renderログ確認方法**:

**リアルタイムログ表示**:
```bash
# Render Dashboard > Logs タブ
# または CLI経由（render-cliインストール後）

render logs -s qstorm-platform --tail 100
```

**ログフィルタリング**:
```
# Dashboard > Logs > Search
# 検索例:
ERROR                    # エラーのみ表示
LangChain               # LangChain関連ログ
API呼び出し             # 日本語ログ検索
status=500              # HTTPステータスコード
```

**ログの永続化（推奨）**:

```python
# app_improved.py - ログ設定強化

import logging
from logging.handlers import RotatingFileHandler
import os

# ログディレクトリ作成
os.makedirs('logs', exist_ok=True)

# ロガー設定
logger = logging.getLogger('qstorm')
logger.setLevel(logging.INFO)

# コンソール出力（Renderログ）
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(console_formatter)

# ファイル出力（ローテーション: 10MB x 5ファイル）
file_handler = RotatingFileHandler(
    'logs/qstorm.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(console_formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

# 使用例
logger.info('Application started')
logger.error('Database connection failed', exc_info=True)
```

**構造化ログ（JSON形式）**:

```python
import json
import logging

class JSONFormatter(logging.Formatter):
    """JSON形式のログフォーマッター"""

    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)

# ハンドラーに適用
json_handler = logging.StreamHandler()
json_handler.setFormatter(JSONFormatter())
logger.addHandler(json_handler)
```

**アラート設定（Render Notifications）**:

**Step 1: Render Dashboard > Service > Notifications**

```
1. "Add Notification" クリック
2. Notification Type: Email, Slack, Webhook
3. Events:
   - Deploy Started
   - Deploy Succeeded
   - Deploy Failed
   - Service Suspended (無料プラン)
   - High Memory Usage (80%以上)
   - Health Check Failed
```

**Step 2: Slack Webhook統合例**

```python
# app_improved.py - Slackアラート送信

import requests

SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')

def send_slack_alert(message, level='warning'):
    """Slackにアラート送信"""
    if not SLACK_WEBHOOK_URL:
        return

    colors = {
        'info': '#36a64f',
        'warning': '#ff9900',
        'error': '#ff0000'
    }

    payload = {
        'attachments': [{
            'color': colors.get(level, '#808080'),
            'title': f'Q-Storm Platform Alert ({level.upper()})',
            'text': message,
            'footer': 'Render Deployment',
            'ts': int(time.time())
        }]
    }

    try:
        requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        logger.error(f'Slack通知失敗: {e}')

# 使用例
send_slack_alert('Memory usage exceeded 80%', level='warning')
send_slack_alert('LangChain API quota exceeded', level='error')
```

**ヘルスチェックエンドポイント強化**:

```python
@app.route('/api/v2/health', methods=['GET'])
def health_check():
    """Render用ヘルスチェック（拡張版）"""

    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '3.0.0',
        'checks': {}
    }

    # 1. メモリチェック
    try:
        import psutil
        memory = psutil.virtual_memory()
        health_status['checks']['memory'] = {
            'status': 'ok' if memory.percent < 85 else 'warning',
            'usage_percent': memory.percent,
            'available_gb': round(memory.available / (1024**3), 2)
        }
    except Exception as e:
        health_status['checks']['memory'] = {'status': 'error', 'message': str(e)}

    # 2. データベース接続チェック（Phase 2）
    if DATABASE_URL:
        try:
            engine.execute('SELECT 1')
            health_status['checks']['database'] = {'status': 'ok'}
        except Exception as e:
            health_status['checks']['database'] = {'status': 'error', 'message': str(e)}
            health_status['status'] = 'degraded'

    # 3. LangChain APIチェック
    api_key = os.environ.get('OPENAI_API_KEY', '')
    health_status['checks']['langchain'] = {
        'status': 'ok' if api_key else 'disabled',
        'api_key_configured': bool(api_key)
    }

    # 4. ファイルシステムチェック
    try:
        disk_usage = psutil.disk_usage('/')
        health_status['checks']['disk'] = {
            'status': 'ok' if disk_usage.percent < 90 else 'warning',
            'usage_percent': disk_usage.percent
        }
    except Exception as e:
        health_status['checks']['disk'] = {'status': 'error', 'message': str(e)}

    # 総合ステータス判定
    check_statuses = [check.get('status') for check in health_status['checks'].values()]
    if 'error' in check_statuses:
        health_status['status'] = 'unhealthy'
        status_code = 503
    elif 'warning' in check_statuses:
        health_status['status'] = 'degraded'
        status_code = 200
    else:
        health_status['status'] = 'healthy'
        status_code = 200

    return jsonify(health_status), status_code
```

**パフォーマンスモニタリング**:

```python
# app_improved.py - リクエストメトリクス

from functools import wraps
import time

request_metrics = {
    'total_requests': 0,
    'total_duration': 0,
    'endpoint_stats': {}
}

def track_performance(f):
    """エンドポイントパフォーマンストラッキング"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()

        try:
            response = f(*args, **kwargs)
            return response
        finally:
            duration = time.time() - start_time
            endpoint = request.endpoint or 'unknown'

            # メトリクス更新
            request_metrics['total_requests'] += 1
            request_metrics['total_duration'] += duration

            if endpoint not in request_metrics['endpoint_stats']:
                request_metrics['endpoint_stats'][endpoint] = {
                    'count': 0,
                    'total_duration': 0,
                    'avg_duration': 0
                }

            stats = request_metrics['endpoint_stats'][endpoint]
            stats['count'] += 1
            stats['total_duration'] += duration
            stats['avg_duration'] = stats['total_duration'] / stats['count']

            # 遅いリクエストをログ記録（3秒以上）
            if duration > 3:
                logger.warning(f'Slow request: {endpoint} took {duration:.2f}s')

    return decorated_function

# 全エンドポイントに適用
@app.route('/api/v1/analysis/eda/execute', methods=['POST'])
@track_performance
def execute_eda_analysis():
    # ... (既存実装)
    pass

# メトリクスエンドポイント
@app.route('/api/v2/metrics', methods=['GET'])
def get_metrics():
    """パフォーマンスメトリクス取得"""
    return jsonify({
        'total_requests': request_metrics['total_requests'],
        'average_duration': request_metrics['total_duration'] / max(request_metrics['total_requests'], 1),
        'endpoints': request_metrics['endpoint_stats']
    })
```

#### F.6 デプロイメントチェックリスト

**デプロイ前の準備**:

- [ ] GitHubリポジトリ作成・push完了
- [ ] `render.yaml` 配置完了
- [ ] `requirements.txt` 更新（gunicorn追加）
- [ ] `.gitignore` 設定（uploads/, outputs/, .env除外）
- [ ] 環境変数リスト作成（OPENAI_API_KEY等）
- [ ] ヘルスチェックエンドポイント実装（`/api/v2/health`）

**Render初期設定**:

- [ ] Renderアカウント作成
- [ ] GitHub連携完了
- [ ] Web Service作成（リポジトリ選択）
- [ ] ビルド・スタートコマンド設定
- [ ] 環境変数設定（最低限: `OPENAI_API_KEY`, `SESSION_SECRET_KEY`）
- [ ] Auto-Deploy有効化（mainブランチ）

**デプロイ後の確認**:

- [ ] ビルドログ確認（エラーなし）
- [ ] デプロイ成功確認（緑のチェックマーク）
- [ ] ヘルスチェックURL確認（`https://qstorm-platform.onrender.com/api/v2/health`）
- [ ] アップロード機能テスト（サンプルExcelファイル）
- [ ] EDA実行テスト（Sweetvizレポート生成確認）
- [ ] LangChain統合テスト（日本語洞察生成確認 or テンプレートフォールバック）
- [ ] ログ確認（エラー・警告なし）

**Phase 2以降の追加設定**:

- [ ] PostgreSQLデータベース作成
- [ ] `DATABASE_URL` 環境変数設定（自動）
- [ ] データベースマイグレーション実行（Alembic）
- [ ] Redis作成（キャッシング用 - オプション）
- [ ] Celery Workerデプロイ（バックグラウンドタスク - オプション）

**継続的モニタリング**:

- [ ] Render Notifications設定（Email/Slack）
- [ ] ログ定期確認（週1回）
- [ ] パフォーマンスメトリクス確認（`/api/v2/metrics`）
- [ ] データベースバックアップ確認（Phase 2 - 毎日自動）
- [ ] コスト確認（Render Billing Dashboard）

---

**トラブルシューティング FAQ**:

**Q1: "Application failed to respond" エラー**

A: ヘルスチェックエンドポイントが正しく応答していない可能性があります。
```bash
# ログ確認
render logs -s qstorm-platform --tail 100

# ヘルスチェックパス確認（render.yaml）
healthCheckPath: /api/v2/health

# app_improved.py で該当エンドポイント実装確認
```

**Q2: ビルドが失敗する**

A: `requirements.txt` の依存関係エラーの可能性があります。
```bash
# ローカルで再現テスト
python3 -m venv test_env
source test_env/bin/activate
pip install -r requirements.txt

# エラーが出た場合、該当パッケージのバージョンを調整
```

**Q3: 環境変数が読み込まれない**

A: Render Dashboardで環境変数を設定後、再デプロイが必要です。
```bash
# Render Dashboard > Manual Deploy > "Deploy latest commit" クリック
```

**Q4: ファイルアップロードが失敗する（413 Payload Too Large）**

A: Renderの制限、またはアプリケーションの`MAX_FILE_SIZE_MB`設定を確認してください。
```python
# app_improved.py
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_FILE_SIZE_MB', 200)) * 1024 * 1024
```

## Appendix G: Phase 1 Security Implementation Guide

### G.1 Input Validation Scope
- API request parameter validation
- File upload size and type restrictions
- SQL injection prevention (prepared statements)
- XSS prevention in error messages

### G.2 Security Checklist for Phase 1
- [ ] Environment variable validation
- [ ] Error message sanitization
- [ ] File path traversal prevention
- [ ] Request rate limiting (basic)

### G.3 Phase 2 Security Features (Deferred)
- User authentication (JWT/OAuth)
- Role-based access control
- API key management
- Audit logging

## Appendix H: Sample Data Standardization Guide

### H.1 Repository Data Structure
```
Q-Storm-Project3/
├── data/
│   ├── sample/
│   │   └── fixed_extended_store_data_2024-FIX_kaizen_monthlyvol3.xlsx
│   └── README.md
```

### H.2 Data Access Configuration
```python
# config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
SAMPLE_DATA_DIR = BASE_DIR / 'data' / 'sample'
SAMPLE_DATA_FILE = 'fixed_extended_store_data_2024-FIX_kaizen_monthlyvol3.xlsx'
```

### H.3 Setup Instructions
1. Clone repository
2. Place sample data in `data/sample/` directory
3. Verify data file exists: `python verify_data_prerequisites.py`

## Appendix I: Phase 2 Preparation Roadmap

### I.1 Infrastructure PoC Timeline
- Week 1-2: PostgreSQL setup and migration strategy
- Week 3-4: Redis caching implementation
- Week 5-6: Celery async task queue

### I.2 Parallel Tasks During Phase 1
- [ ] PostgreSQL schema design
- [ ] Redis cache strategy document
- [ ] Celery task definitions
- [ ] Docker Compose configuration for Phase 2

### I.3 Phase 2 PoC Environment
```yaml
# docker-compose.yml (draft)
version: '3.8'
services:
  postgres:
    image: postgres:15
  redis:
    image: redis:7
  celery:
    build: .
    command: celery -A app worker
```

---

**END OF IMPLEMENTATION WORKFLOW**

Document Version: 1.0
Generated: 2025-10-18
Review Cycle: After each sprint retrospective
Next Review: End of Sprint 3 (Week 6)
