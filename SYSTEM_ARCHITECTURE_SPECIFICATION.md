# Q-Storm Platform - System Architecture Specification v3.0

**Document Version**: 3.0
**Date**: 2025-10-18
**Status**: Production-Ready Architecture
**Classification**: Technical Design Specification

---

## Executive Summary

### Platform Overview

Q-Storm Platform is a comprehensive AI-powered QC Story analysis system that integrates statistical analysis, machine learning, and natural language processing to support data-driven problem-solving following the QC Story methodology. The system provides both web-based and CLI interfaces for retail store data analysis with specialization in Pareto analysis, time series analysis, and causal inference.

### Key Architectural Drivers

1. **QC Story Methodology Alignment**: System architecture directly maps to 6-step QC Story process
2. **Single-File Architecture**: Monolithic deployment for simplified management and reduced complexity
3. **Progressive Enhancement**: Two parallel implementations (app.py and app_improved.py) supporting different feature sets
4. **Japanese Language Support**: Native Japanese text processing with natural language explanations
5. **Dynamic Resource Management**: Memory-aware upload limits and processing optimization

### System Capabilities

| Category | Capabilities |
|----------|-------------|
| **Data Processing** | Excel/CSV upload (200-500MB), 41-column schema support, NaN/Infinity handling |
| **Analysis Types** | Pareto, Histogram, Scatter, Time Series, Probability Distribution (6 types) |
| **Machine Learning** | AutoGluon integration, Random Forest, Logistic Regression, Propensity Score Matching |
| **Visualization** | Plotly-based interactive charts, Japanese text rendering, PNG export |
| **AI Integration** | LangChain-based natural language explanations, LLM-powered insights |
| **Deployment** | Flask web server, CLI mode, RESTful API (v1 + v2) |

---

## 1. System Architecture Overview

### 1.1 Architecture Style

**Monolithic Single-File Architecture** with modular class organization

**Rationale**:
- Simplified deployment and distribution (single Python file)
- Reduced dependency management complexity
- Easier version control and rollback
- Suitable for mid-scale data analysis workloads (not enterprise distributed systems)

### 1.2 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Q-Storm Platform                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐           ┌──────────────────┐             │
│  │   Client Layer  │           │  External APIs    │             │
│  │                 │           │                   │             │
│  │ - Web Browser   │◄─────────►│ - OpenAI GPT     │             │
│  │ - CLI Terminal  │   HTTP    │ - LangChain      │             │
│  │ - HTTP Client   │           │ - AutoGluon      │             │
│  └────────────────┘           └──────────────────┘             │
│         │                              │                         │
│         │ CORS-enabled                 │ API Calls               │
│         ▼                              ▼                         │
│  ┌──────────────────────────────────────────────────────┐       │
│  │           Flask Application Server                    │       │
│  │           (app.py / app_improved.py)                  │       │
│  │                                                        │       │
│  │  ┌──────────────────────────────────────────────┐    │       │
│  │  │         API Layer (REST)                      │    │       │
│  │  │  - /api/v1/* (backward compatible)            │    │       │
│  │  │  - /api/v2/* (advanced features)              │    │       │
│  │  │  - CORS middleware                            │    │       │
│  │  └──────────────────────────────────────────────┘    │       │
│  │                       │                                │       │
│  │  ┌──────────────────────────────────────────────┐    │       │
│  │  │       Business Logic Layer                    │    │       │
│  │  │                                               │    │       │
│  │  │  ┌─────────────────────────────────────┐     │    │       │
│  │  │  │   ParetoAnalysisEngine              │     │    │       │
│  │  │  │   - Core Pareto calculation         │     │    │       │
│  │  │  │   - ABC analysis                    │     │    │       │
│  │  │  │   - Statistical tests               │     │    │       │
│  │  │  │   - Outlier detection               │     │    │       │
│  │  │  │   - Result caching (LRU)            │     │    │       │
│  │  │  └─────────────────────────────────────┘     │    │       │
│  │  │                                               │    │       │
│  │  │  ┌─────────────────────────────────────┐     │    │       │
│  │  │  │   ProbabilityDistributionAnalyzer   │     │    │       │
│  │  │  │   - 6 distribution types            │     │    │       │
│  │  │  │   - KS test goodness-of-fit         │     │    │       │
│  │  │  │   - AIC/BIC model selection         │     │    │       │
│  │  │  └─────────────────────────────────────┘     │    │       │
│  │  │                                               │    │       │
│  │  │  ┌─────────────────────────────────────┐     │    │       │
│  │  │  │   NaturalLanguageExplainer          │     │    │       │
│  │  │  │   - LangChain integration           │     │    │       │
│  │  │  │   - Japanese text generation        │     │    │       │
│  │  │  │   - Context-aware insights          │     │    │       │
│  │  │  └─────────────────────────────────────┘     │    │       │
│  │  │                                               │    │       │
│  │  │  ┌─────────────────────────────────────┐     │    │       │
│  │  │  │   EnhancedDataFilter                │     │    │       │
│  │  │  │   - Shop/date filtering             │     │    │       │
│  │  │  │   - Outlier removal (IQR/Z-score)   │     │    │       │
│  │  │  │   - Column validation               │     │    │       │
│  │  │  └─────────────────────────────────────┘     │    │       │
│  │  └──────────────────────────────────────────────┘    │       │
│  │                       │                                │       │
│  │  ┌──────────────────────────────────────────────┐    │       │
│  │  │       Data Access Layer                       │    │       │
│  │  │                                               │    │       │
│  │  │  - Session-based file storage                 │    │       │
│  │  │  - DataFrame memory caching                   │    │       │
│  │  │  - JSON-safe serialization                    │    │       │
│  │  │  - NaN/Infinity handling                      │    │       │
│  │  └──────────────────────────────────────────────┘    │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │           Persistent Storage                          │       │
│  │                                                        │       │
│  │  - uploads/ (session-based file storage)              │       │
│  │  - outputs/ (generated visualizations)                │       │
│  │  - analysis_outputs/ (analysis results)               │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Legend:
  ◄────► Bidirectional communication
  ─────► Unidirectional flow
  ┌────┐ Component boundary
```

### 1.3 Technology Stack

#### Core Technologies

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Runtime** | Python | 3.8-3.11 | Core platform runtime |
| **Web Framework** | Flask | 2.x | HTTP server and routing |
| **CORS** | Flask-CORS | 4.x | Cross-origin resource sharing |
| **Data Processing** | pandas | 1.x | DataFrame operations |
| **Numerical Computing** | NumPy | 1.x | Array operations and math |
| **Statistics** | SciPy | 1.x | Statistical tests and distributions |
| **Visualization** | Matplotlib | 3.x | Chart generation |
| **File Handling** | Werkzeug | 2.x | Secure file uploads |
| **Machine Learning** | AutoGluon | 0.x (optional) | Automated ML |
| **EDA Tools** | Sweetviz | 2.x | Automated EDA report generation |
| | pandas-profiling | 3.x | Comprehensive data profiling (optional) |
| **NLP/LLM** | LangChain | 0.1.x | Natural language explanation generation |
| | OpenAI API | gpt-3.5-turbo | LLM backend for Japanese insights |
| **Memory Monitoring** | psutil | 5.x (optional) | Dynamic resource management |

#### Frontend Technologies

| Technology | Purpose |
|-----------|---------|
| **HTML5** | UI structure |
| **CSS3** | Styling with Meiryo font for Japanese |
| **JavaScript** | Client-side interactivity |
| **Plotly.js** | Interactive data visualization |

---

## 2. Component Architecture

### 2.1 Component Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      Flask Application                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   Configuration Layer                       │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │                                                             │  │
│  │  Security Constants:                                        │  │
│  │  - MAX_FILE_SIZE (dynamic: 200-500MB)                      │  │
│  │  - MAX_CONTENT_LENGTH (dynamic: 500MB-1GB)                 │  │
│  │  - ALLOWED_EXTENSIONS = {xlsx, xls, csv}                   │  │
│  │                                                             │  │
│  │  Analysis Constants:                                        │  │
│  │  - MIN_DATA_POINTS = 10                                    │  │
│  │  - MAX_CATEGORIES = 30                                     │  │
│  │  - PARETO_THRESHOLD_DEFAULT = 80.0                         │  │
│  │  - ABC_THRESHOLDS = {A: 70, B: 90, C: 100}                │  │
│  │                                                             │  │
│  │  Cache Configuration:                                       │  │
│  │  - DEFAULT_CACHE_SIZE = 128                                │  │
│  │  - LRU cache for analysis results                          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   Data Models (Enums + Dataclasses)        │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │                                                             │  │
│  │  class AnalysisLevel(Enum):                                │  │
│  │    BASIC, STANDARD, ADVANCED, EXPERT                       │  │
│  │                                                             │  │
│  │  class ExplanationStyle(Enum):                             │  │
│  │    TECHNICAL, BUSINESS, BEGINNER, EXECUTIVE                │  │
│  │                                                             │  │
│  │  @dataclass ParetoConfig:                                  │  │
│  │    - pareto_threshold: float                               │  │
│  │    - outlier_detection: bool                               │  │
│  │    - abc_analysis: bool                                    │  │
│  │    - statistical_tests: bool                               │  │
│  │    - generate_insights: bool                               │  │
│  │                                                             │  │
│  │  @dataclass ParetoResult:                                  │  │
│  │    - categories, values, percentages                       │  │
│  │    - cumulative_percentages, vital_few, trivial_many       │  │
│  │    - statistics, abc_analysis, outliers                    │  │
│  │    - insights, recommendations, visualizations             │  │
│  │    - probability_distribution                              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   Security Layer                            │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │                                                             │  │
│  │  sanitize_input(text: str) -> str                          │  │
│  │    - HTML escape                                           │  │
│  │    - SQL injection prevention                              │  │
│  │    - Max length enforcement (1000 chars)                   │  │
│  │                                                             │  │
│  │  allowed_file(filename: str) -> bool                       │  │
│  │    - Extension validation                                  │  │
│  │                                                             │  │
│  │  validate_dataframe_columns(df, required_cols) -> Tuple    │  │
│  │    - Column existence check                                │  │
│  │                                                             │  │
│  │  get_dynamic_upload_limits() -> Tuple[int, int]            │  │
│  │    - psutil-based memory monitoring                        │  │
│  │    - Dynamic limit calculation (33% of available memory)   │  │
│  │    - Memory pressure detection (>80% usage)                │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Analysis Engines (Core Business Logic)        │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │                                                             │  │
│  │  class ParetoAnalysisEngine:                               │  │
│  │    - analyze(df, config) -> ParetoResult                   │  │
│  │    - _calculate_pareto_data()                              │  │
│  │    - _perform_abc_analysis()                               │  │
│  │    - _detect_outliers()                                    │  │
│  │    - _calculate_statistics()                               │  │
│  │    - _generate_insights()                                  │  │
│  │    - _create_visualizations()                              │  │
│  │    - Result caching with @lru_cache                        │  │
│  │                                                             │  │
│  │  class ProbabilityDistributionAnalyzer:                    │  │
│  │    - analyze(data, dist_type) -> Dict                      │  │
│  │    - Supported distributions:                              │  │
│  │      * Exponential                                         │  │
│  │      * Gamma                                               │  │
│  │      * Lognormal                                           │  │
│  │      * Normal                                              │  │
│  │      * Weibull                                             │  │
│  │      * Beta                                                │  │
│  │    - KS test for goodness-of-fit                           │  │
│  │    - AIC/BIC for model selection                           │  │
│  │    - Auto-selection of best-fit distribution               │  │
│  │                                                             │  │
│  │  class NaturalLanguageExplainer:                           │  │
│  │    - explain(result, style) -> str                         │  │
│  │    - LangChain integration                                 │  │
│  │    - Japanese text generation                              │  │
│  │    - Context-aware insights                                │  │
│  │    - Multi-style support (technical/business/executive)    │  │
│  │                                                             │  │
│  │  class EnhancedDataFilter:                                 │  │
│  │    - filter(df, criteria) -> pd.DataFrame                  │  │
│  │    - Shop filtering                                        │  │
│  │    - Date range filtering                                  │  │
│  │    - Column-based filtering                                │  │
│  │    - Outlier removal (IQR method, Z-score)                 │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   Data Processing Utilities                │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │                                                             │  │
│  │  safe_json_value(value) -> Any                             │  │
│  │    - Converts NaN/Inf to None                              │  │
│  │                                                             │  │
│  │  clean_dataframe_for_json(df) -> pd.DataFrame              │  │
│  │    - Replaces NaN/Inf with JSON-safe values                │  │
│  │                                                             │  │
│  │  safe_to_dict(df) -> dict                                  │  │
│  │    - DataFrame to dict with NaN handling                   │  │
│  │                                                             │  │
│  │  generate_session_id() -> str                              │  │
│  │    - Timestamp-based session ID generation                 │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   API Endpoints (Routes)                   │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │                                                             │  │
│  │  /api/v1/upload                  POST  - File upload       │  │
│  │  /api/v1/analysis/pareto         POST  - Pareto analysis   │  │
│  │  /api/v1/sessions/<id>           GET   - Session data      │  │
│  │                                                             │  │
│  │  /api/v2/analysis/pareto/advanced POST - Advanced Pareto   │  │
│  │  /api/v2/analysis/probability    POST  - Distribution      │  │
│  │  /api/v2/health                  GET   - Health check      │  │
│  │  /api/v2/export/<session_id>     GET   - Export results    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow Architecture

#### 2.2.1 Upload and Analysis Flow

```
┌─────────────┐
│   Client    │
│ (Browser)   │
└──────┬──────┘
       │
       │ 1. POST /api/v1/upload
       │    Content-Type: multipart/form-data
       │    File: store_data.xlsx
       │
       ▼
┌──────────────────────────────────────────┐
│  Flask Application                        │
│                                           │
│  ┌────────────────────────────────────┐  │
│  │  Security Layer                    │  │
│  │  - Validate file extension         │  │
│  │  - Check file size vs MAX_FILE_SIZE│  │
│  │  - Secure filename generation      │  │
│  └────────────────────────────────────┘  │
│              │                            │
│              │ 2. File validated          │
│              ▼                            │
│  ┌────────────────────────────────────┐  │
│  │  Session Manager                   │  │
│  │  - Generate session_id             │  │
│  │  - Create uploads/<session_id>/    │  │
│  │  - Save file to disk               │  │
│  └────────────────────────────────────┘  │
│              │                            │
│              │ 3. File saved              │
│              ▼                            │
│  ┌────────────────────────────────────┐  │
│  │  Data Loader                       │  │
│  │  - Read Excel/CSV via pandas       │  │
│  │  - Validate 41-column schema       │  │
│  │  - Clean NaN/Infinity values       │  │
│  └────────────────────────────────────┘  │
│              │                            │
│              │ 4. DataFrame ready         │
│              ▼                            │
│  ┌────────────────────────────────────┐  │
│  │  EnhancedDataFilter                │  │
│  │  - Apply shop filter (if specified)│  │
│  │  - Apply date range filter         │  │
│  │  - Remove outliers (if enabled)    │  │
│  └────────────────────────────────────┘  │
│              │                            │
│              │ 5. Filtered DataFrame      │
│              ▼                            │
│  ┌────────────────────────────────────┐  │
│  │  ParetoAnalysisEngine              │  │
│  │  - Calculate Pareto data           │  │
│  │  - Perform ABC analysis            │  │
│  │  - Detect outliers                 │  │
│  │  - Generate insights               │  │
│  │  - Create visualizations           │  │
│  │  - Cache results (LRU)             │  │
│  └────────────────────────────────────┘  │
│              │                            │
│              │ 6. ParetoResult object     │
│              ▼                            │
│  ┌────────────────────────────────────┐  │
│  │  NaturalLanguageExplainer          │  │
│  │  (if advanced analysis)            │  │
│  │  - Generate Japanese explanation   │  │
│  │  - Create actionable insights      │  │
│  └────────────────────────────────────┘  │
│              │                            │
│              │ 7. JSON serialization      │
│              ▼                            │
│  ┌────────────────────────────────────┐  │
│  │  Response Builder                  │  │
│  │  - Convert to JSON-safe format     │  │
│  │  - Include visualizations (base64) │  │
│  │  - Add metadata                    │  │
│  └────────────────────────────────────┘  │
│              │                            │
└──────────────┼────────────────────────────┘
               │
               │ 8. HTTP 200 OK
               │    Content-Type: application/json
               ▼
         ┌─────────────┐
         │   Client    │
         │ (Browser)   │
         └─────────────┘
```

#### 2.2.2 Probability Distribution Analysis Flow

```
Client Request:
POST /api/v2/analysis/probability
{
  "session_id": "20250118_143052",
  "target_column": "Total_Sales",
  "distribution_type": "auto"  // or specific: exponential, gamma, etc.
}

         │
         ▼
┌────────────────────────────────┐
│  Load session DataFrame         │
│  - Retrieve from uploads/       │
│  - Validate target_column       │
└────────────────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  ProbabilityDistributionAnalyzer│
│  - Extract column data          │
│  - Remove NaN/Inf               │
│  - Normalize if needed          │
└────────────────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  If distribution_type == "auto"│
│  - Fit all 6 distributions      │
│  - Calculate AIC/BIC for each   │
│  - Select best-fit distribution │
│  Else:                          │
│  - Fit specified distribution   │
└────────────────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  Statistical Testing            │
│  - Perform KS test              │
│  - Calculate p-value            │
│  - Generate Q-Q plot            │
└────────────────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  Result Compilation             │
│  {                              │
│    "distribution": "gamma",     │
│    "parameters": {...},         │
│    "ks_statistic": 0.032,       │
│    "p_value": 0.421,            │
│    "aic": 1234.5,               │
│    "bic": 1240.2,               │
│    "visualization": "base64..." │
│  }                              │
└────────────────────────────────┘
         │
         ▼
     Response to Client
```

---

## 3. Data Architecture

### 3.1 Data Schema

#### 3.1.1 Store Data Schema (41 Columns)

**File Format**: Excel (.xlsx, .xls) or CSV
**Date Range**: 2019/4/30 to 2024/12/31
**Stores**: 恵比寿 (Ebisu), 横浜元町 (Yokohama Motomachi)

| Category | Column Name (English) | Column Name (Japanese) | Data Type | Description |
|----------|----------------------|----------------------|-----------|-------------|
| **Store** | shop | 店舗名 | string | Store name |
| | shop_code | 店舗コード | string | Store code |
| **Date** | Date | 営業日付 | datetime | Business date (YYYY/MM/DD) |
| **Financial** | Total_Sales | 店舗別売上高 | float | Total store sales |
| | gross_profit | 売上総利益 | float | Gross profit |
| | discount | 値引・割引 | float | Discounts (monthly) |
| | purchasing | 仕入高 | float | Purchasing cost |
| | rent | 家賃 | float | Rent |
| | personnel_expenses | 人件費 | float | Personnel expenses |
| | depreciation | 減価償却費 | float | Depreciation |
| | sales_promotion | 販売促進費 | float | Sales promotion expenses |
| | head_office_expenses | 本部費用配賦 | float | Head office allocation |
| | operating_cost | 営業経費 | float | Operating expenses |
| | Operating_profit | 営業利益 | float | Operating profit |
| **Product Sales** | Mens_JACKETS&OUTER2 | メンズ ジャケット・アウター 売上高 | float | Men's jackets & outerwear sales |
| | Mens_KNIT | メンズ ニット 売上高 | float | Men's knitwear sales |
| | Mens_PANTS | メンズ パンツ 売上高 | float | Men's pants sales |
| | WOMEN'S_JACKETS2 | レディース ジャケット 売上高 | float | Women's jacket sales |
| | WOMEN'S_TOPS | レディース トップス 売上高 | float | Women's tops sales |
| | WOMEN'S_ONEPIECE | レディース ワンピース 売上高 | float | Women's one-piece sales |
| | WOMEN'S_bottoms | レディース ボトムス 売上高 | float | Women's bottoms sales |
| | WOMEN'S_SCARF & STOLES | レディース スカーフ・ストール 売上高 | float | Women's scarves & stoles sales |
| **Inventory** | Inventory | 在庫金額 | float | Inventory amount |
| | Months_of_inventory | 在庫月数 | float | Months of inventory |
| **Metrics** | BEP | 損益分岐点 | float | Break-even point |
| | Average_Temperature | 平均気温 | float | Average temperature (°C) |
| | Number_of_guests | 来客数 | integer | Number of customers |
| | Price_per_customer | 客単価 | float | Average price per customer |
| **Sales Mix %** | Mens_JACKETS&OUTER2R | メンズ ジャケット・アウター 売上構成比 | float | Men's jackets mix % |
| | Mens_KNITR | メンズ ニット 売上構成比 | float | Men's knitwear mix % |
| | Mens_PANTSR | メンズ パンツ 売上構成比 | float | Men's pants mix % |
| | WOMEN'S_JACKETSR | レディース ジャケット 売上構成比 | float | Women's jackets mix % |
| | WOMEN'S_TOPSR | レディース トップス 売上構成比 | float | Women's tops mix % |
| | WOMEN'S_ONEPIECER | レディース ワンピース 売上構成比 | float | Women's one-piece mix % |
| | WOMEN'S_bottomsR | レディース ボトムス 売上構成比 | float | Women's bottoms mix % |
| | WOMEN'S_SCARF & STOLESR | レディース スカーフ・ストール 売上構成比 | float | Women's scarves mix % |
| **Evaluation** | judge | 判定 | string | Evaluation/judgment |

#### 3.1.2 Session Storage Schema

```
uploads/
└── <session_id>/                # Format: YYYYMMDD_HHMMSS
    ├── original_file.xlsx       # Uploaded file
    └── metadata.json            # Session metadata
        {
          "session_id": "20250118_143052",
          "filename": "store_data.xlsx",
          "upload_time": "2025-01-18T14:30:52Z",
          "file_size": 1234567,
          "rows": 1000,
          "columns": 41,
          "stores": ["恵比寿", "横浜元町"],
          "date_range": {
            "start": "2019-04-30",
            "end": "2024-12-31"
          }
        }
```

#### 3.1.3 Analysis Result Schema

**ParetoResult Dataclass Structure**:

```python
{
  "categories": ["商品A", "商品B", "商品C"],  # Sorted by value descending
  "values": [1000000, 500000, 200000],      # Absolute values
  "percentages": [58.8, 29.4, 11.8],        # Individual percentages
  "cumulative_percentages": [58.8, 88.2, 100.0],  # Cumulative %
  "cumulative_values": [1000000, 1500000, 1700000],

  "vital_few": ["商品A", "商品B"],          # Items contributing to 80%
  "trivial_many": ["商品C"],                 # Remaining items

  "pareto_point": {
    "index": 1,                              # Index where 80% is reached
    "category": "商品B",
    "cumulative_percentage": 88.2,
    "exact_80_value": 1360000                # Interpolated value at 80%
  },

  "statistics": {
    "total": 1700000,
    "mean": 566666.67,
    "median": 500000,
    "std_dev": 412310.56,
    "coefficient_of_variation": 0.73,
    "gini_coefficient": 0.35,                # Inequality measure
    "concentration_ratio": 0.882             # Top 2 items concentration
  },

  "abc_analysis": {
    "A": {
      "categories": ["商品A"],
      "percentage": 70.0,
      "threshold": 70
    },
    "B": {
      "categories": ["商品B"],
      "percentage": 20.0,
      "threshold": 90
    },
    "C": {
      "categories": ["商品C"],
      "percentage": 10.0,
      "threshold": 100
    }
  },

  "outliers": {
    "method": "IQR",                         # IQR or Z-score
    "detected": ["商品D"],
    "threshold_upper": 2000000,
    "threshold_lower": 0
  },

  "metrics": {
    "pareto_efficiency": 0.95,               # How well it fits 80/20
    "diversity_index": 0.65,                 # Category diversity
    "concentration_index": 0.82              # Market concentration
  },

  "insights": [
    "上位2カテゴリで全体の88%を占めています",
    "商品Aが圧倒的なシェアを持っています（59%）",
    "商品C以降のロングテール商品は改善余地があります"
  ],

  "recommendations": [
    {
      "category": "vital_few",
      "action": "focus",
      "description": "上位2商品に経営資源を集中投下してください",
      "priority": "high"
    },
    {
      "category": "trivial_many",
      "action": "optimize",
      "description": "低貢献商品の在庫削減を検討してください",
      "priority": "medium"
    }
  ],

  "visualizations": {
    "pareto_chart": "data:image/png;base64,iVBORw0KG...",  # Base64 PNG
    "abc_pie_chart": "data:image/png;base64,iVBORw0KG...",
    "trend_chart": "data:image/png;base64,iVBORw0KG..."
  },

  "metadata": {
    "analysis_level": "ADVANCED",
    "analysis_timestamp": "2025-01-18T14:35:22Z",
    "execution_time_ms": 234,
    "config": {
      "pareto_threshold": 80.0,
      "outlier_detection": true,
      "abc_analysis": true
    }
  },

  "probability_distribution": {
    "best_fit": "gamma",
    "parameters": {"shape": 2.5, "scale": 400000},
    "ks_statistic": 0.032,
    "p_value": 0.421,
    "aic": 1234.5,
    "bic": 1240.2
  }
}
```

### 3.2 Data Processing Pipeline

#### 3.2.1 NaN and Infinity Handling

**Critical Safety Functions**:

```python
def safe_json_value(value):
    """Convert NaN/Inf to JSON-safe values"""
    if pd.isna(value):
        return None
    if np.isinf(value):
        return None
    if isinstance(value, (np.integer, np.floating)):
        return float(value)
    return value

def clean_dataframe_for_json(df):
    """Replace NaN/Inf with JSON-safe values"""
    df = df.copy()
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.fillna(value=None)  # Replace NaN with None
    return df

def safe_to_dict(df):
    """DataFrame to dict with NaN handling"""
    df_clean = clean_dataframe_for_json(df)
    return df_clean.to_dict(orient='records')
```

**Processing Order**:

1. **File Upload Validation**
   - Extension check (xlsx, xls, csv)
   - Size check (dynamic limit based on available memory)
   - Security check (filename sanitization)

2. **Data Loading**
   - Read Excel/CSV via pandas
   - Automatic type inference
   - UTF-8 encoding for Japanese text

3. **Data Cleaning**
   - Replace NaN/Inf with None
   - Type conversion for numeric columns
   - Date parsing for Date column

4. **Filter Application**
   - Shop filtering (if specified)
   - Date range filtering
   - Column selection

5. **Analysis Execution**
   - Pareto calculation
   - Statistical tests
   - Distribution fitting

6. **Result Serialization**
   - JSON-safe conversion
   - Base64 encoding for images
   - Metadata addition

#### 3.2.2 Caching Strategy

**LRU Cache for Analysis Results**:

```python
from functools import lru_cache

class CachedAnalysisEngine:
    @lru_cache(maxsize=128)
    def analyze_cached(self, data_hash, config_hash):
        """Cache analysis results based on data and config hash"""
        return self.analyze(data, config)

    def get_data_hash(self, df):
        """Generate MD5 hash of DataFrame for cache key"""
        return hashlib.md5(
            pd.util.hash_pandas_object(df).values
        ).hexdigest()
```

**Cache Invalidation**:
- Session-based (cleared on new file upload)
- LRU eviction (oldest unused results removed when cache full)
- Manual cache clearing via `/api/v2/cache/clear` endpoint

---

## 4. API Architecture

### 4.1 API Versioning Strategy

**Version 1 (v1)**: Backward-compatible legacy API
**Version 2 (v2)**: Advanced features with enhanced security

### 4.2 API Endpoint Specifications

#### 4.2.1 File Upload (v1)

**Endpoint**: `POST /api/v1/upload`

**Request**:
```http
POST /api/v1/upload HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="file"; filename="store_data.xlsx"
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

<binary data>
------WebKitFormBoundary7MA4YWxkTrZu0gW--
```

**Response**:
```json
{
  "status": "success",
  "session_id": "20250118_143052",
  "filename": "store_data.xlsx",
  "rows": 1000,
  "columns": 41,
  "stores": ["恵比寿", "横浜元町"],
  "date_range": {
    "start": "2019-04-30",
    "end": "2024-12-31"
  },
  "available_columns": [
    "shop", "Date", "Total_Sales", "Operating_profit", ...
  ]
}
```

**Error Response**:
```json
{
  "status": "error",
  "message": "ファイルサイズが制限を超えています",
  "code": "FILE_TOO_LARGE",
  "max_size_mb": 200
}
```

#### 4.2.2 Pareto Analysis (v1)

**Endpoint**: `POST /api/v1/analysis/pareto`

**Request**:
```json
{
  "session_id": "20250118_143052",
  "category_column": "Mens_JACKETS&OUTER2",
  "value_column": "Total_Sales",
  "store": "恵比寿",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

**Response**: See section 3.1.3 for complete ParetoResult schema

#### 4.2.3 Advanced Pareto Analysis (v2)

**Endpoint**: `POST /api/v2/analysis/pareto/advanced`

**Request**:
```json
{
  "session_id": "20250118_143052",
  "category_column": "商品名",
  "value_column": "Total_Sales",
  "analysis_level": "ADVANCED",
  "filters": {
    "shop": "恵比寿",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "remove_outliers": true,
    "outlier_method": "IQR"
  },
  "config": {
    "pareto_threshold": 80.0,
    "abc_analysis": true,
    "statistical_tests": true,
    "generate_insights": true,
    "explanation_style": "BUSINESS"
  }
}
```

**Response**: Enhanced ParetoResult with natural language explanations

#### 4.2.4 Probability Distribution Analysis (v2)

**Endpoint**: `POST /api/v2/analysis/probability`

**Request**:
```json
{
  "session_id": "20250118_143052",
  "target_column": "Total_Sales",
  "distribution_type": "auto",  // or: exponential, gamma, lognormal, normal, weibull, beta
  "filters": {
    "shop": "恵比寿",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "distribution": "gamma",
  "parameters": {
    "shape": 2.5,
    "scale": 400000,
    "location": 0
  },
  "goodness_of_fit": {
    "ks_statistic": 0.032,
    "p_value": 0.421,
    "interpretation": "良好なフィット（p > 0.05）"
  },
  "model_selection": {
    "aic": 1234.5,
    "bic": 1240.2,
    "best_distribution": "gamma",
    "alternatives": [
      {"distribution": "lognormal", "aic": 1245.3, "bic": 1251.1},
      {"distribution": "weibull", "aic": 1256.7, "bic": 1262.4}
    ]
  },
  "visualizations": {
    "pdf_plot": "data:image/png;base64,...",
    "cdf_plot": "data:image/png;base64,...",
    "qq_plot": "data:image/png;base64,..."
  },
  "insights": [
    "データはガンマ分布によく適合しています",
    "右側に長い尾があり、まれに高い売上が発生します",
    "平均売上は約1,000,000円、最頻値は約800,000円です"
  ]
}
```

#### 4.2.5 Health Check (v2)

**Endpoint**: `GET /api/v2/health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-18T14:35:22Z",
  "version": "3.0.0",
  "system": {
    "memory": {
      "total_gb": 16.0,
      "available_gb": 8.5,
      "used_gb": 7.5,
      "percent": 46.9
    },
    "upload_limits": {
      "max_file_size_mb": 200,
      "max_content_length_mb": 500,
      "dynamic_adjustment": true
    },
    "cache": {
      "size": 12,
      "max_size": 128,
      "hit_rate": 0.75
    }
  },
  "features": {
    "pareto_analysis": true,
    "probability_distribution": true,
    "natural_language_explanation": true,
    "psutil_available": true,
    "autogluon_available": false
  }
}
```

#### 4.2.6 Analysis Mode Selection (v1)

**Endpoint**: `POST /api/v1/analysis/mode`

**Purpose**: ユーザーが分析モード（自動EDAまたはマニュアル分析）を選択し、セッション構成を保存します。

**Request**:
```json
{
  "session_id": "20250118_143052",
  "mode": "auto_eda",
  "target_column": "Total_Sales",
  "options": {
    "include_correlations": true,
    "include_outliers": true,
    "max_categories": 30
  }
}
```

**Request Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | アップロード時に取得したセッションID |
| `mode` | string | Yes | 分析モード: `"auto_eda"` または `"manual"` |
| `target_column` | string | No | EDAターゲットカラム（auto_edaモード時） |
| `options` | object | No | 分析オプション設定 |

**Response (Success)**:
```json
{
  "status": "success",
  "session_id": "20250118_143052",
  "mode": "auto_eda",
  "config_saved": true,
  "config_path": "/uploads/20250118_143052/analysis_config.json",
  "next_step": {
    "endpoint": "/api/v1/analysis/eda/execute",
    "method": "POST",
    "description": "EDA分析を実行してください"
  }
}
```

**Response (Error - Invalid Mode)**:
```json
{
  "status": "error",
  "code": "INVALID_MODE",
  "message": "無効な分析モードです。'auto_eda' または 'manual' を指定してください",
  "allowed_values": ["auto_eda", "manual"]
}
```

**Saved Configuration Format** (`analysis_config.json`):
```json
{
  "mode": "auto_eda",
  "target_column": "Total_Sales",
  "timestamp": "2025-01-18T14:35:22Z",
  "options": {
    "include_correlations": true,
    "include_outliers": true,
    "max_categories": 30
  }
}
```

#### 4.2.7 EDA Execution (v1)

**Endpoint**: `POST /api/v1/analysis/eda/execute`

**Purpose**: Sweetvizによる自動EDAレポート生成とLangChainによる日本語洞察生成を実行します。

**Request**:
```json
{
  "session_id": "20250118_143052",
  "target_column": "Total_Sales",
  "filters": {
    "shop": "恵比寿",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "remove_outliers": false
  }
}
```

**Request Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | セッションID |
| `target_column` | string | No | Sweetviz分析のターゲットカラム |
| `filters` | object | No | データフィルタリング条件 |
| `filters.shop` | string | No | 店舗フィルタ（例: "恵比寿"） |
| `filters.start_date` | string | No | 開始日（YYYY-MM-DD） |
| `filters.end_date` | string | No | 終了日（YYYY-MM-DD） |
| `filters.remove_outliers` | boolean | No | 外れ値除去フラグ（デフォルト: false） |

**Response (Success with LangChain)**:
```json
{
  "status": "success",
  "session_id": "20250118_143052",
  "report_path": "/outputs/20250118_143052/eda_report.html",
  "insights": {
    "source": "langchain",
    "model": "gpt-3.5-turbo",
    "content": "### 📊 主要な発見\n\n1. **売上トレンド**: 2024年第3四半期に20%の売上増加が観測されました...\n2. **相関分析**: Total_SalesとOperating_profitの間に強い正の相関（r=0.89）が確認されました...\n\n### 💡 ビジネス上の示唆\n\n- 夏季キャンペーンの効果が顕著に現れています\n- 粗利率の改善余地があります（現在平均35%）\n\n### ⚠️ 注意すべき点\n\n- 12月の在庫回転率が低下傾向にあります",
    "warning": null
  },
  "key_findings": [
    {
      "type": "dataset_size",
      "message": "総レコード数: 1,000件、カラム数: 41個"
    },
    {
      "type": "high_correlation",
      "severity": "info",
      "message": "3組の高相関ペアが検出されました",
      "details": [
        "Total_Sales ↔ Operating_profit: 0.892",
        "Inventory ↔ purchasing: 0.756"
      ]
    }
  ],
  "stats_summary": {
    "Total_Sales": {
      "mean": 125340.5,
      "std": 45230.2,
      "min": 45000.0,
      "max": 350000.0,
      "median": 115000.0,
      "q25": 95000.0,
      "q75": 145000.0,
      "missing": 0
    }
  },
  "execution_time": 18.45
}
```

**Response (Success with Template Fallback)**:
```json
{
  "status": "success",
  "session_id": "20250118_143052",
  "report_path": "/outputs/20250118_143052/eda_report.html",
  "insights": {
    "source": "template",
    "model": null,
    "content": "### 📊 主要な発見\n\n1. **データセット規模**: 総レコード数 1,000件、分析期間 2024-01-01 〜 2024-12-31...",
    "warning": "LangChain未設定のため、定型文を生成しました。OPENAI_API_KEYを設定すると、より詳細な洞察が得られます。"
  },
  "key_findings": [...],
  "stats_summary": {...},
  "execution_time": 15.32
}
```

**Response (Error - Session Not Found)**:
```json
{
  "status": "error",
  "error_type": "SessionNotFound",
  "message": "セッション 20250118_143052 にデータファイルが見つかりません",
  "suggestion": "先にデータをアップロードしてください（POST /api/v1/upload）",
  "timestamp": "2025-01-18T14:35:12+09:00"
}
```

**Response (Error - Sweetviz Failed)**:
```json
{
  "status": "error",
  "error_type": "SweetvizError",
  "message": "Sweetviz分析中にエラーが発生しました",
  "details": "DataFrame must have at least 10 rows",
  "execution_time": 2.15
}
```

**Processing Notes**:
- **実行時間**: 通常10-30秒（データサイズに依存）
- **LangChain統合**: `OPENAI_API_KEY`環境変数が設定されている場合のみ有効
- **フォールバック**: LangChain APIエラー時は自動的にテンプレートベースの洞察を生成
- **HTMLレポート**: Sweetvizレポートは `/outputs/<session_id>/eda_report.html` に保存
- **キャッシング**: 同一データ・同一パラメータの場合、LangChain応答をキャッシュから取得（TTL: 1時間）

**使用例（curl)**:
```bash
curl -X POST http://localhost:5003/api/v1/analysis/eda/execute \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "20250118_143052",
    "target_column": "Total_Sales",
    "filters": {
      "shop": "恵比寿",
      "start_date": "2024-01-01",
      "end_date": "2024-12-31"
    }
  }'
```

### 4.3 Error Handling

**Standard Error Response Format**:

```json
{
  "status": "error",
  "code": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "field": "category_column",
    "reason": "Column not found in DataFrame"
  },
  "timestamp": "2025-01-18T14:35:22Z",
  "request_id": "uuid-here"
}
```

**Error Codes**:

| Code | HTTP Status | Description |
|------|------------|-------------|
| `FILE_TOO_LARGE` | 413 | File exceeds upload limit |
| `INVALID_FILE_TYPE` | 400 | File extension not allowed |
| `INVALID_SESSION` | 404 | Session ID not found |
| `MISSING_COLUMN` | 400 | Required column missing in data |
| `INSUFFICIENT_DATA` | 400 | Less than MIN_DATA_POINTS rows |
| `ANALYSIS_FAILED` | 500 | Internal analysis error |
| `MEMORY_LIMIT` | 507 | Insufficient memory for operation |

---

## 5. Security Architecture

### 5.1 Security Layers

#### 5.1.1 Input Validation

**File Upload Security**:
- Extension whitelist: `{xlsx, xls, csv}`
- Dynamic file size limits based on available memory
- Secure filename generation via `werkzeug.secure_filename()`
- MIME type validation (optional, not currently implemented)

**Parameter Sanitization**:
```python
def sanitize_input(text: str) -> str:
    """XSS and SQL injection prevention"""
    if not text:
        return ""
    # HTML escape
    text = html.escape(text)
    # Remove SQL injection patterns
    text = re.sub(r'[;\'"\\]', '', text)
    # Max length enforcement
    return text[:1000]
```

#### 5.1.2 CORS Configuration

```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:5000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

#### 5.1.3 Session Security

- **Session ID Format**: `YYYYMMDD_HHMMSS` (timestamp-based)
- **Session Storage**: Isolated directories per session
- **Session Expiration**: Manual cleanup required (no automatic expiration)
- **No Authentication**: Currently app_noauth.py bypasses authentication

### 5.2 Data Protection

**Personal Data Handling**:
- Store names are not considered PII
- Financial data is processed in-memory only
- No persistent database (session-based file storage)

**Encryption**:
- No encryption at rest (local file system)
- HTTPS recommended for production deployment

---

## 6. Performance Architecture

### 6.1 Memory Management

#### 6.1.1 Dynamic Upload Limits

```python
def get_dynamic_upload_limits():
    """Calculate upload limits based on available memory"""
    if psutil:
        available_memory = psutil.virtual_memory().available
        memory_usage_percent = psutil.virtual_memory().percent

        # Use 33% of available memory for file uploads (max 500MB)
        dynamic_file_size = min(500 * 1024 * 1024, available_memory // 3)

        # If memory usage > 80%, reduce limits aggressively
        if memory_usage_percent > 80:
            dynamic_file_size = min(100 * 1024 * 1024, available_memory // 5)

        # Minimum 50MB guarantee
        dynamic_file_size = max(50 * 1024 * 1024, dynamic_file_size)

        return dynamic_file_size, dynamic_file_size * 2.5
    else:
        # Fallback to static limits
        return 200 * 1024 * 1024, 500 * 1024 * 1024
```

#### 6.1.2 DataFrame Memory Optimization

**Techniques**:
- Lazy loading: Load only required columns
- Data type optimization: Use appropriate dtypes (int32 vs int64)
- Chunk processing for large files (future enhancement)

### 6.2 Caching Strategy

**LRU Cache**:
- Analysis results cached with `@lru_cache(maxsize=128)`
- Cache key: MD5 hash of (DataFrame + config)
- Automatic eviction of least recently used results

**Session-Based Caching**:
- Uploaded files stored in `uploads/<session_id>/`
- Analysis results stored in memory during session
- No persistent cache across server restarts

### 6.3 Performance Benchmarks

| Operation | Data Size | Expected Performance |
|-----------|-----------|---------------------|
| File Upload (Excel) | 50MB | < 5 seconds |
| Pareto Analysis (BASIC) | 1,000 rows | < 1 second |
| Pareto Analysis (ADVANCED) | 10,000 rows | < 5 seconds |
| Probability Distribution | 10,000 rows | < 3 seconds |
| Natural Language Explanation | 1 result | < 2 seconds (LLM-dependent) |

---

## 7. Deployment Architecture

### 7.1 Development Environment

**Local Development**:
```bash
# Install dependencies
pip install flask flask-cors pandas numpy scipy matplotlib werkzeug psutil

# Run development server
python3 app_improved.py --port 5003

# Or use environment variable
PORT=5001 python3 app_improved.py
```

**Environment Variables**:
```bash
PORT=5003                  # Server port (default: 5003)
MAX_FILE_SIZE_MB=200       # Override file size limit
FLASK_ENV=development      # Enable debug mode
OPENAI_API_KEY=sk-...      # For LangChain integration
```

### 7.2 Production Deployment

**Production Server Recommendations**:

1. **WSGI Server**: Use Gunicorn or uWSGI (not Flask dev server)
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5003 app_improved:app
   ```

2. **Reverse Proxy**: Use Nginx for SSL termination and load balancing
   ```nginx
   server {
       listen 80;
       server_name qstorm.example.com;

       location / {
           proxy_pass http://127.0.0.1:5003;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       # File upload size limit
       client_max_body_size 500M;
   }
   ```

3. **Process Manager**: Use systemd or supervisord for process monitoring
   ```ini
   [program:qstorm]
   command=/usr/bin/gunicorn -w 4 app_improved:app
   directory=/opt/qstorm
   user=qstorm
   autostart=true
   autorestart=true
   ```

4. **Resource Limits**:
   - Minimum RAM: 16GB
   - Recommended RAM: 32GB
   - CPU: 8 cores recommended for concurrent users

### 7.3 Scaling Considerations

**Current Limitations**:
- Single-process architecture (no horizontal scaling)
- Session-based file storage (not suitable for distributed deployment)
- In-memory caching (not shared across processes)

**Future Scaling Options**:
- **Redis**: For shared session storage and distributed caching
- **Celery**: For background analysis tasks
- **PostgreSQL**: For persistent analysis history
- **S3**: For uploaded file storage

---

## 8. EDA（探索的データ分析）アーキテクチャ

### 8.1 EDA機能概要

Q-Storm Platformは、データ分析の初期段階において、ユーザーが以下の2つのモードから選択できる柔軟な分析アプローチを提供します：

1. **自動EDAモード**: Sweetviz/Pandas Profilingによる包括的な自動分析
2. **マニュアル分析モード**: パレート図、時系列、ヒストグラムなど個別分析手法の選択実行

この二層構造により、初心者ユーザーは自動EDAでデータの全体像を把握し、経験豊富なアナリストは目的に応じた詳細分析を実行できます。

### 8.2 EDAモード選択アーキテクチャ

#### 8.2.1 システム構成図

```
┌─────────────────────────────────────────────────────────────────┐
│                     EDA Mode Selection Layer                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────┐           ┌─────────────────────┐    │
│  │  Auto EDA Mode      │           │  Manual Mode        │    │
│  │                     │           │                     │    │
│  │  ┌───────────────┐  │           │  ┌───────────────┐  │    │
│  │  │   Sweetviz    │  │           │  │ Pareto Chart  │  │    │
│  │  │   Analysis    │  │           │  │   Analysis    │  │    │
│  │  └───────────────┘  │           │  └───────────────┘  │    │
│  │                     │           │                     │    │
│  │  ┌───────────────┐  │           │  ┌───────────────┐  │    │
│  │  │   Pandas      │  │           │  │  Time Series  │  │    │
│  │  │   Profiling   │  │           │  │   Analysis    │  │    │
│  │  └───────────────┘  │           │  └───────────────┘  │    │
│  │                     │           │                     │    │
│  │  ┌───────────────┐  │           │  ┌───────────────┐  │    │
│  │  │   Custom EDA  │  │           │  │  Histogram    │  │    │
│  │  │   Engine      │  │           │  │   Analysis    │  │    │
│  │  └───────────────┘  │           │  └───────────────┘  │    │
│  └─────────────────────┘           └─────────────────────┘    │
│              │                                  │               │
│              └──────────────┬───────────────────┘               │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         LangChain Natural Language Explainer            │   │
│  │                                                          │   │
│  │  - EDA結果の日本語解説生成                                  │   │
│  │  - ビジネス洞察の自動抽出                                    │   │
│  │  - 改善アクションの提案                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Analysis Results Storage                    │   │
│  │                                                          │   │
│  │  - analysis_config.json (モード設定)                        │   │
│  │  - eda_report_*.html (EDAレポート)                          │   │
│  │  - insights_*.json (洞察データ)                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3 LangChain統合アーキテクチャ

#### 8.3.1 LangChain統合の必要性

Q-Storm Platformにおいて、LangChainは**単なるオプション機能ではなく、システムの中核的価値を提供する必須コンポーネント**です。その理由は以下の通りです：

1. **専門用語の翻訳**: 統計用語（相関係数、標準偏差、p値など）をビジネス用語に変換
2. **文脈理解**: 店舗データ、商品カテゴリー、季節性などのドメイン知識を考慮した解説
3. **アクション指向**: 分析結果から具体的な改善策を自動生成
4. **多様なスタイル**: 技術者向け、経営者向け、初心者向けなど対象者に応じた解説

#### 8.3.2 LangChain統合コンポーネント図

```
┌─────────────────────────────────────────────────────────────┐
│                   EDA実行エンドポイント                      │
│              POST /api/v1/analysis/eda/execute              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │  EDAAAnalysisEngine    │
         │  - execute_eda()       │
         └────────┬───────────────┘
                  │
      ┌───────────┴──────────────┐
      │                          │
      ▼                          ▼
┌─────────────────┐    ┌──────────────────────────┐
│ SweetvizExecutor│    │ LangChainInsightGenerator│
│ - generate()    │    │ - generate_insights()    │
└────────┬────────┘    └────────┬─────────────────┘
         │                      │
         │                      ▼
         │            ┌──────────────────────┐
         │            │ PromptTemplateManager│
         │            │ - EDA_INSIGHTS       │
         │            │ - PARETO_EXPLAIN     │
         │            └─────────┬────────────┘
         │                      │
         │                      ▼
         │            ┌──────────────────────┐
         │            │   ChatOpenAI(GPT3.5) │
         │            │   - invoke()         │
         │            └──────────┬───────────┘
         │                       │
         │                       ▼ (API Error?)
         │            ┌──────────────────────┐
         │            │  TemplateFallback    │
         │            │  - template_insights()│
         │            └──────────────────────┘
         │                      │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   統合レスポンス     │
         │ - report_path        │
         │ - insights (日本語)  │
         │ - key_findings       │
         └──────────────────────┘
```

**コンポーネント役割**:
- **SweetvizExecutor**: Sweetvizライブラリによる自動EDAレポート生成
- **LangChainInsightGenerator**: GPTモデルを使用した日本語ビジネス洞察生成
- **PromptTemplateManager**: プロンプトテンプレートの管理と変数注入
- **TemplateFallback**: APIエラー時の定型文生成フォールバック機構

#### 8.3.3 プロンプトテンプレート設計

**EDA洞察生成テンプレート（eda_insights_template）:**

```python
EDA_INSIGHTS_TEMPLATE = """
あなたは経験豊富なデータアナリストです。以下の店舗データの探索的データ分析（EDA）結果に基づいて、
ビジネス上の重要な洞察を日本語で3〜5個抽出してください。

## データセット情報
- **総レコード数**: {num_records}
- **分析期間**: {date_range}
- **店舗**: {shop_name}
- **対象カラム**: {target_columns}

## 統計サマリー
{stats_summary}

## 高相関ペア（相関係数 > 0.7）
{high_correlations}

## 外れ値の検出
{outlier_info}

## 出力形式
以下の形式で出力してください：

### 📊 主要な発見
1. [発見1の詳細]
2. [発見2の詳細]
3. [発見3の詳細]

### 💡 ビジネス上の示唆
- [示唆1]
- [示唆2]

### ⚠️ 注意すべき点
- [注意点1]
- [注意点2]

各洞察は具体的な数値を含め、ビジネス担当者が理解しやすい言葉で記述してください。
"""

PARETO_EXPLANATION_TEMPLATE = """
あなたはQCストーリー手法に精通したビジネスアナリストです。以下のパレート分析結果を、
改善活動の担当者向けに日本語で解説してください。

## パレート分析結果
- **分析対象**: {category_column}
- **集計指標**: {value_column}
- **総アイテム数**: {total_items}
- **総売上**: {total_value:,.0f}円

## 上位20%の重要アイテム
{top_items}

## 累積寄与率
- **上位3アイテム**: {top3_contribution:.1f}%
- **上位5アイテム**: {top5_contribution:.1f}%
- **上位10アイテム**: {top10_contribution:.1f}%

## 80/20ルールの検証
{pareto_rule_check}

## 出力形式
以下の形式で、改善活動の担当者が次のアクションを起こしやすいように解説してください：

### 🎯 重点管理すべきアイテム
[上位アイテムの特徴と重要性]

### 📈 改善の優先順位
1. [最優先アイテムと理由]
2. [次点アイテムと理由]

### 🔍 深掘り分析の提案
[さらに調査すべき観点や仮説]

### ✅ 次のステップ
[具体的なアクション案]

QCストーリーの「現状把握」フェーズとして、数値の羅列ではなく、
改善活動につながるストーリーを語るように記述してください。
"""
```

**プロンプト変数の動的注入**:

```python
class PromptTemplateManager:
    """プロンプトテンプレート管理クラス"""

    def __init__(self):
        self.eda_template = EDA_INSIGHTS_TEMPLATE
        self.pareto_template = PARETO_EXPLANATION_TEMPLATE

    def build_eda_prompt(self, df: pd.DataFrame, stats_summary: dict) -> str:
        """EDA洞察生成プロンプトの構築"""
        return self.eda_template.format(
            num_records=len(df),
            date_range=f"{df['Date'].min()} 〜 {df['Date'].max()}",
            shop_name=df['shop'].iloc[0] if 'shop' in df.columns else "全店舗",
            target_columns=", ".join(df.select_dtypes(include=[np.number]).columns.tolist()),
            stats_summary=self._format_stats(stats_summary),
            high_correlations=self._format_correlations(df),
            outlier_info=self._format_outliers(df)
        )

    def build_pareto_prompt(self, pareto_result: dict) -> str:
        """パレート解説生成プロンプトの構築"""
        top_items_df = pareto_result['data'].head(10)
        top_items_str = top_items_df.to_string(index=False)

        return self.pareto_template.format(
            category_column=pareto_result['category_column'],
            value_column=pareto_result['value_column'],
            total_items=len(pareto_result['data']),
            total_value=pareto_result['data'][pareto_result['value_column']].sum(),
            top_items=top_items_str,
            top3_contribution=pareto_result['data'].head(3)['cumulative_percentage'].iloc[-1],
            top5_contribution=pareto_result['data'].head(5)['cumulative_percentage'].iloc[-1],
            top10_contribution=pareto_result['data'].head(10)['cumulative_percentage'].iloc[-1],
            pareto_rule_check=self._check_pareto_rule(pareto_result['data'])
        )

    def _format_stats(self, stats: dict) -> str:
        """統計サマリーのフォーマット"""
        lines = []
        for col, stat in stats.items():
            lines.append(f"- **{col}**: 平均={stat['mean']:.2f}, 標準偏差={stat['std']:.2f}, "
                        f"最小={stat['min']:.2f}, 最大={stat['max']:.2f}")
        return "\n".join(lines)

    def _format_correlations(self, df: pd.DataFrame, threshold: float = 0.7) -> str:
        """高相関ペアの抽出とフォーマット"""
        corr_matrix = df.select_dtypes(include=[np.number]).corr()
        high_corrs = []

        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > threshold:
                    col1 = corr_matrix.columns[i]
                    col2 = corr_matrix.columns[j]
                    high_corrs.append(f"- **{col1}** ↔ **{col2}**: {corr_value:.3f}")

        return "\n".join(high_corrs) if high_corrs else "- 高相関ペアは検出されませんでした"

    def _format_outliers(self, df: pd.DataFrame) -> str:
        """外れ値情報のフォーマット（IQR法）"""
        outlier_counts = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)]
            if len(outliers) > 0:
                outlier_counts[col] = len(outliers)

        if outlier_counts:
            lines = [f"- **{col}**: {count}件の外れ値" for col, count in outlier_counts.items()]
            return "\n".join(lines)
        else:
            return "- 外れ値は検出されませんでした"

    def _check_pareto_rule(self, df: pd.DataFrame) -> str:
        """80/20ルールの検証"""
        top20_index = max(1, int(len(df) * 0.2))
        top20_contribution = df.iloc[top20_index-1]['cumulative_percentage']

        if top20_contribution >= 80:
            return f"✅ **80/20ルール適用可能**: 上位20%のアイテムが{top20_contribution:.1f}%を占めています"
        else:
            return f"⚠️ **80/20ルールから逸脱**: 上位20%のアイテムの寄与率は{top20_contribution:.1f}%です"
```

#### 8.3.4 Fallback機構（テンプレートベース）

LangChain APIが利用できない場合（APIキー未設定、レート制限、ネットワークエラー等）のための**グレースフルデグラデーション**を実装します。

**フォールバック判定フロー**:

```
┌─────────────────────────┐
│ generate_insights()呼出 │
└────────┬────────────────┘
         │
         ▼
   ┌─────────────┐
   │ API Key確認 │
   └────┬────────┘
        │
   ┌────┴─────┐
   │ あり なし │
   ▼          ▼
┌────────┐ ┌──────────────┐
│LangChain│ │Template生成  │
│API呼出 │ │(Fallback)    │
└───┬────┘ └──────┬───────┘
    │             │
    ▼ (Exception) │
┌────────────┐    │
│Retry (3回) │    │
└───┬────────┘    │
    │ (失敗)      │
    └─────────────┤
                  ▼
         ┌────────────────┐
         │ Template返却   │
         │ + Warning通知  │
         └────────────────┘
```

**実装例**:

```python
class LangChainInsightGenerator:
    """LangChain統合による洞察生成クラス"""

    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY', '')
        self.llm = None
        self.template_manager = PromptTemplateManager()
        self.max_retries = 3
        self.cache = {}  # シンプルなLRUキャッシュ (max 100 entries)

        if self.api_key and self.api_key.startswith('sk-'):
            try:
                from langchain.chat_models import ChatOpenAI
                self.llm = ChatOpenAI(
                    model_name="gpt-3.5-turbo",
                    temperature=0.7,
                    openai_api_key=self.api_key,
                    request_timeout=30
                )
            except Exception as e:
                logger.warning(f"LangChain初期化失敗: {e}")
                self.llm = None

    def generate_eda_insights(self, df: pd.DataFrame, stats_summary: dict) -> dict:
        """EDA洞察生成（フォールバック対応）"""
        prompt = self.template_manager.build_eda_prompt(df, stats_summary)
        cache_key = hashlib.md5(prompt.encode()).hexdigest()

        # キャッシュチェック
        if cache_key in self.cache:
            logger.info("EDA洞察をキャッシュから取得")
            return self.cache[cache_key]

        # LangChain利用可能チェック
        if self.llm is None:
            logger.warning("LangChain未設定 → テンプレート生成にフォールバック")
            result = self._generate_template_insights(df, stats_summary, analysis_type='eda')
            result['warning'] = 'LangChain未設定のため、定型文を生成しました。OPENAI_API_KEYを設定すると、より詳細な洞察が得られます。'
            return result

        # LangChain API呼び出し（リトライあり）
        for attempt in range(self.max_retries):
            try:
                from langchain.schema import HumanMessage
                response = self.llm([HumanMessage(content=prompt)])

                result = {
                    'insights': response.content,
                    'source': 'langchain',
                    'model': 'gpt-3.5-turbo',
                    'warning': None
                }

                # キャッシュに保存
                if len(self.cache) >= 100:
                    self.cache.pop(next(iter(self.cache)))  # 最古のエントリ削除
                self.cache[cache_key] = result

                return result

            except Exception as e:
                logger.error(f"LangChain API呼び出し失敗 (試行{attempt+1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    # 最終試行失敗 → フォールバック
                    logger.warning("LangChain API失敗 → テンプレート生成にフォールバック")
                    result = self._generate_template_insights(df, stats_summary, analysis_type='eda')
                    result['warning'] = f'LangChain API呼び出しに失敗しました（{str(e)[:100]}）。定型文を生成しました。'
                    return result
                time.sleep(2 ** attempt)  # Exponential backoff

    def _generate_template_insights(self, df: pd.DataFrame, stats_summary: dict,
                                    analysis_type: str = 'eda') -> dict:
        """テンプレートベースの洞察生成（フォールバック）"""
        if analysis_type == 'eda':
            insights = f"""
### 📊 主要な発見

1. **データセット規模**: 総レコード数 {len(df):,}件、分析期間 {df['Date'].min()} 〜 {df['Date'].max()}
2. **数値カラム**: {len(df.select_dtypes(include=[np.number]).columns)}個の数値カラムを検出
3. **欠損値**: {df.isnull().sum().sum()}個の欠損値が存在します

### 💡 ビジネス上の示唆

- 詳細な分析のためには、LangChain統合（OPENAI_API_KEY設定）を推奨します
- Sweetviz HTMLレポートで個別カラムの詳細分布を確認できます

### ⚠️ 注意すべき点

- この解説は定型文です。より詳細な洞察には、OpenAI APIキーの設定が必要です
"""
        else:  # pareto
            top_item = df.iloc[0]
            insights = f"""
### 🎯 重点管理すべきアイテム

上位1位の「{top_item[df.columns[0]]}」が全体の{top_item['percentage']:.1f}%を占めています。

### 📈 改善の優先順位

1. 上位3アイテムで累積{df.head(3)['cumulative_percentage'].iloc[-1]:.1f}%
2. 上位5アイテムで累積{df.head(5)['cumulative_percentage'].iloc[-1]:.1f}%

### 🔍 深掘り分析の提案

- LangChain統合により、より詳細な改善提案が可能です

### ✅ 次のステップ

1. OPENAI_API_KEYを設定して、詳細な洞察を取得
2. 上位アイテムの時系列トレンド分析
"""

        return {
            'insights': insights,
            'source': 'template',
            'model': None,
            'warning': None  # 外部で設定される
        }
```

### 8.4 EDA実行フロー

#### 8.4.1 Sweetviz分析実行

**実行フロー**:

```
┌──────────────────────┐
│ POST /api/v1/analysis│
│    /eda/execute      │
└─────────┬────────────┘
          │
          ▼
┌─────────────────────────┐
│ 1. セッションデータ取得 │
│    uploads/<sid>/data.csv│
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ 2. Sweetviz実行         │
│    sv.analyze(df)       │
│    ※処理時間: 10-30秒  │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ 3. HTML保存             │
│    outputs/<sid>/eda.html│
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ 4. 統計サマリー抽出     │
│    - describe()         │
│    - corr() > 0.7       │
│    - outlier detection  │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ 5. LangChain洞察生成    │
│    (or Template)        │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ 6. JSONレスポンス返却   │
│    - report_path        │
│    - insights           │
│    - key_findings       │
└─────────────────────────┘
```

**実装例**:

```python
class EDAAnalysisEngine:
    """EDA分析エンジン（Sweetviz + LangChain統合）"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.upload_dir = os.path.join('uploads', session_id)
        self.output_dir = os.path.join('outputs', session_id)
        self.langchain_generator = LangChainInsightGenerator()

        os.makedirs(self.output_dir, exist_ok=True)

    def execute_eda(self, df: pd.DataFrame, target_column: str = None) -> dict:
        """
        EDA分析の実行

        Args:
            df: 分析対象データフレーム
            target_column: ターゲットカラム（オプション）

        Returns:
            分析結果辞書 {report_path, insights, key_findings, execution_time}
        """
        start_time = time.time()

        try:
            # 1. Sweetviz レポート生成
            logger.info(f"Sweetviz分析開始 (session: {self.session_id})")

            if target_column and target_column in df.columns:
                report = sv.analyze(df, target_feat=target_column)
            else:
                report = sv.analyze(df)

            report_path = os.path.join(self.output_dir, 'eda_report.html')
            report.show_html(filepath=report_path, open_browser=False)

            logger.info(f"Sweetvizレポート生成完了: {report_path}")

            # 2. 統計サマリー抽出
            stats_summary = self._extract_statistics(df)

            # 3. LangChain による洞察生成
            insights_result = self.langchain_generator.generate_eda_insights(df, stats_summary)

            # 4. 主要発見事項の抽出
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
            logger.error(f"EDA分析エラー: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'execution_time': round(time.time() - start_time, 2)
            }

    def _extract_statistics(self, df: pd.DataFrame) -> dict:
        """統計サマリーの抽出"""
        stats = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns

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

    def _extract_key_findings(self, df: pd.DataFrame, stats_summary: dict) -> list:
        """主要発見事項の抽出"""
        findings = []

        # データセット規模
        findings.append({
            'type': 'dataset_size',
            'message': f'総レコード数: {len(df):,}件、カラム数: {len(df.columns)}個'
        })

        # 欠損値チェック
        total_missing = df.isnull().sum().sum()
        if total_missing > 0:
            findings.append({
                'type': 'missing_values',
                'severity': 'warning',
                'message': f'欠損値が{total_missing:,}個検出されました'
            })

        # 高相関ペア
        corr_matrix = df.select_dtypes(include=[np.number]).corr()
        high_corrs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                if abs(corr_matrix.iloc[i, j]) > 0.7:
                    high_corrs.append((
                        corr_matrix.columns[i],
                        corr_matrix.columns[j],
                        corr_matrix.iloc[i, j]
                    ))

        if high_corrs:
            findings.append({
                'type': 'high_correlation',
                'severity': 'info',
                'message': f'{len(high_corrs)}組の高相関ペアが検出されました',
                'details': [f'{c1} ↔ {c2}: {v:.3f}' for c1, c2, v in high_corrs[:3]]
            })

        return findings
```

#### 8.4.2 エラーハンドリング

**エラー分類と対応**:

| エラー種類 | 原因 | 対応 | HTTPステータス |
|-----------|------|------|---------------|
| **SessionNotFound** | 無効なsession_id | エラーメッセージ返却 | 404 |
| **DataFileNotFound** | データ未アップロード | アップロード促進 | 400 |
| **SweetvizError** | Sweetviz実行失敗 | ログ記録、統計サマリーのみ返却 | 500 |
| **LangChainAPIError** | OpenAI API呼出失敗 | テンプレートフォールバック + 警告 | 200 (partial) |
| **InsufficientData** | レコード数 < 10 | エラーメッセージ | 400 |
| **MemoryError** | データサイズ過大 | チャンク処理提案 | 413 |

**エラーレスポンス例**:

```json
{
  "status": "error",
  "error_type": "DataFileNotFound",
  "message": "セッション 20240920_143052 にデータファイルが見つかりません",
  "suggestion": "先にデータをアップロードしてください（POST /api/v1/upload）",
  "timestamp": "2024-09-20T14:35:12+09:00"
}
```

### 8.5 セキュリティ考慮事項

#### 8.5.1 OpenAI APIキー管理

**保護レベル**: 🔴 **CRITICAL**

- **環境変数による管理**: `OPENAI_API_KEY` は環境変数でのみ設定、ハードコード禁止
- **ログ出力の除外**: APIキーをログに出力しない（マスキング処理）
- **クライアント送信禁止**: APIキーをJSONレスポンスに含めない
- **Git除外**: `.env` ファイルを `.gitignore` に追加

**実装例**:

```python
import os
import re

def validate_openai_api_key() -> tuple[bool, str]:
    """OpenAI APIキーの検証"""
    api_key = os.environ.get('OPENAI_API_KEY', '')

    if not api_key:
        return False, 'OPENAI_API_KEY環境変数が設定されていません'

    if not api_key.startswith('sk-'):
        return False, 'APIキーの形式が不正です（sk-で始まる必要があります）'

    if len(api_key) < 20:
        return False, 'APIキーが短すぎます'

    # ログにはマスキングして記録
    masked_key = api_key[:7] + '*' * (len(api_key) - 11) + api_key[-4:]
    logger.info(f'OpenAI APIキー検証成功: {masked_key}')

    return True, 'OK'

# アプリケーション起動時にチェック
is_valid, message = validate_openai_api_key()
if not is_valid:
    logger.warning(f'LangChain機能が無効化されます: {message}')
```

#### 8.5.2 プロンプトインジェクション対策

**脅威**: ユーザー入力データにプロンプト操作命令が含まれる可能性

**対策**:

1. **入力サニタイゼーション**: ユーザー入力から制御文字を除去
2. **テンプレート分離**: システムプロンプトとユーザーデータを明確に分離
3. **出力バリデーション**: LLM応答が期待形式に準拠しているか検証

```python
def sanitize_for_llm(text: str) -> str:
    """LLM入力用のサニタイゼーション"""
    # 制御文字の除去
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

    # プロンプト操作を試みるパターンの無害化
    dangerous_patterns = [
        r'ignore (previous|above) (instructions|prompts?)',
        r'system:\s*you are',
        r'<\|im_start\|>',
        r'<\|im_end\|>'
    ]

    for pattern in dangerous_patterns:
        text = re.sub(pattern, '[REMOVED]', text, flags=re.IGNORECASE)

    return text[:5000]  # 最大5000文字に制限
```

### 8.6 パフォーマンス最適化

#### 8.6.1 Sweetviz処理の非同期化

**課題**: Sweetviz分析は10-30秒かかり、同期処理ではタイムアウトリスク

**解決策**: バックグラウンドタスク実行 + ポーリング

```python
from flask import Flask
from threading import Thread
import uuid

app = Flask(__name__)

# タスク状態管理（本番環境ではRedis等を推奨）
task_status = {}

def run_eda_async(task_id: str, session_id: str, df: pd.DataFrame):
    """EDA分析をバックグラウンド実行"""
    try:
        task_status[task_id] = {'status': 'running', 'progress': 0}

        engine = EDAAnalysisEngine(session_id)
        result = engine.execute_eda(df)

        task_status[task_id] = {
            'status': 'completed',
            'result': result,
            'progress': 100
        }
    except Exception as e:
        task_status[task_id] = {
            'status': 'failed',
            'error': str(e),
            'progress': 0
        }

@app.route('/api/v1/analysis/eda/execute', methods=['POST'])
def execute_eda_async():
    """EDA実行（非同期）"""
    data = request.get_json()
    session_id = data['session_id']

    # データフレーム取得
    df = load_session_data(session_id)

    # タスクIDを生成してバックグラウンド実行
    task_id = str(uuid.uuid4())
    thread = Thread(target=run_eda_async, args=(task_id, session_id, df))
    thread.start()

    return jsonify({
        'task_id': task_id,
        'status': 'running',
        'poll_url': f'/api/v1/analysis/eda/status/{task_id}'
    })

@app.route('/api/v1/analysis/eda/status/<task_id>', methods=['GET'])
def get_eda_status(task_id: str):
    """EDA実行状態の取得"""
    if task_id not in task_status:
        return jsonify({'error': 'Task not found'}), 404

    return jsonify(task_status[task_id])
```

#### 8.6.2 LangChainレスポンスキャッシュ

**目的**: 同一データへの繰り返しリクエストでAPI呼出を削減

**実装**: LRUキャッシュ（最大100エントリ、TTL 1時間）

```python
from functools import lru_cache
import hashlib
import time

class CachedLangChainGenerator:
    """キャッシュ付きLangChain洞察生成"""

    def __init__(self):
        self.cache = {}  # {hash: (result, timestamp)}
        self.max_cache_size = 100
        self.cache_ttl = 3600  # 1時間

    def generate_with_cache(self, prompt: str) -> dict:
        """キャッシュ付き生成"""
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        current_time = time.time()

        # キャッシュヒット確認
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if current_time - timestamp < self.cache_ttl:
                logger.info(f'キャッシュヒット: {cache_key[:8]}')
                result['cache_hit'] = True
                return result

        # キャッシュミス → LangChain呼出
        result = self.llm_call(prompt)
        result['cache_hit'] = False

        # キャッシュに保存
        if len(self.cache) >= self.max_cache_size:
            # 最古エントリを削除
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]

        self.cache[cache_key] = (result, current_time)
        return result
```

### 8.7 テスト戦略

#### 8.7.1 単体テスト

**対象クラス**: `PromptTemplateManager`, `LangChainInsightGenerator`, `EDAAnalysisEngine`

```python
import unittest
from unittest.mock import Mock, patch
import pandas as pd

class TestPromptTemplateManager(unittest.TestCase):
    """プロンプトテンプレート管理のテスト"""

    def setUp(self):
        self.manager = PromptTemplateManager()
        self.sample_df = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=100),
            'shop': ['恵比寿'] * 100,
            'Total_Sales': np.random.randint(10000, 50000, 100),
            'gross_profit': np.random.randint(3000, 15000, 100)
        })

    def test_build_eda_prompt_structure(self):
        """EDAプロンプト構築の構造テスト"""
        stats = self.manager._extract_statistics(self.sample_df)
        prompt = self.manager.build_eda_prompt(self.sample_df, stats)

        # 必須キーワードの存在確認
        self.assertIn('データセット情報', prompt)
        self.assertIn('統計サマリー', prompt)
        self.assertIn('高相関ペア', prompt)
        self.assertIn('📊 主要な発見', prompt)

    def test_format_correlations(self):
        """相関係数フォーマットのテスト"""
        # 強い相関を持つデータ作成
        df = pd.DataFrame({
            'A': range(100),
            'B': [x * 2 for x in range(100)],  # A と完全相関
            'C': np.random.rand(100)
        })

        result = self.manager._format_correlations(df, threshold=0.7)
        self.assertIn('A', result)
        self.assertIn('B', result)

class TestLangChainInsightGenerator(unittest.TestCase):
    """LangChain洞察生成のテスト"""

    @patch('langchain.chat_models.ChatOpenAI')
    def test_fallback_when_no_api_key(self, mock_llm):
        """APIキー未設定時のフォールバック動作テスト"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}, clear=True):
            generator = LangChainInsightGenerator()
            df = pd.DataFrame({'A': range(10)})
            stats = {}

            result = generator.generate_eda_insights(df, stats)

            self.assertEqual(result['source'], 'template')
            self.assertIn('warning', result)
            self.assertIn('OPENAI_API_KEY', result['warning'])

    @patch('langchain.chat_models.ChatOpenAI')
    def test_retry_on_api_error(self, mock_llm):
        """API呼出失敗時のリトライテスト"""
        mock_instance = Mock()
        mock_instance.side_effect = [
            Exception('Timeout'),  # 1回目失敗
            Exception('Rate limit'),  # 2回目失敗
            Mock(content='成功応答')  # 3回目成功
        ]
        mock_llm.return_value = mock_instance

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'}):
            generator = LangChainInsightGenerator()
            # テスト実装（リトライロジック検証）
```

#### 8.7.2 統合テスト

**シナリオ**: エンドツーエンドのEDA実行フロー

```python
class TestEDAIntegration(unittest.TestCase):
    """EDA統合テスト"""

    def test_full_eda_workflow(self):
        """完全なEDAワークフロー"""
        # 1. テストデータ作成
        df = create_test_store_data(rows=500)
        session_id = 'test_session_001'

        # 2. EDAエンジン初期化
        engine = EDAAnalysisEngine(session_id)

        # 3. EDA実行
        result = engine.execute_eda(df, target_column='Total_Sales')

        # 4. 結果検証
        self.assertEqual(result['status'], 'success')
        self.assertIn('report_path', result)
        self.assertIn('insights', result)
        self.assertIn('key_findings', result)
        self.assertTrue(os.path.exists(result['report_path']))

    def test_eda_with_langchain_mock(self):
        """LangChainモック使用時のテスト"""
        with patch('langchain.chat_models.ChatOpenAI') as mock_llm:
            mock_llm.return_value.invoke.return_value = Mock(
                content='### 📊 主要な発見\n1. テスト洞察'
            )

            # テスト実行
            df = create_test_store_data(rows=100)
            engine = EDAAnalysisEngine('test_session_002')
            result = engine.execute_eda(df)

            self.assertEqual(result['insights_source'], 'langchain')
            self.assertIn('テスト洞察', result['insights'])
```

---

## 9. Integration Architecture

### 9.1 AI/ML Integrations

#### 9.1.1 LangChain Integration

**Purpose**: Natural language explanations in Japanese

**Configuration**:
```python
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

llm = ChatOpenAI(
    model_name="gpt-3.5-turbo",
    temperature=0.7,
    openai_api_key=os.environ.get("OPENAI_API_KEY")
)

template = """
以下のパレート分析結果を日本語で解説してください。

分析結果:
{analysis_result}

解説の出力は以下の構造に従ってください:
### 主要な発見
### 推奨アクション
### 注意点
"""
```

**Usage**:
```python
class NaturalLanguageExplainer:
    def explain(self, result: ParetoResult, style: ExplanationStyle) -> str:
        prompt = self._build_prompt(result, style)
        response = llm(prompt)
        return response.content
```

#### 9.1.2 AutoGluon Integration

**Purpose**: Automated machine learning for feature importance

**Configuration**:
```python
from autogluon.tabular import TabularPredictor

predictor = TabularPredictor(
    label='Operating_profit',
    eval_metric='r2',
    verbosity=0
)
predictor.fit(
    train_data=df_train,
    time_limit=300,  # 5 minutes
    presets='best_quality'
)
```

**Feature Importance Analysis**:
```python
def analyze_feature_importance(df: pd.DataFrame, target: str) -> Dict:
    """Use AutoGluon to identify important features"""
    predictor = TabularPredictor(label=target)
    predictor.fit(df)

    importance = predictor.feature_importance(df)
    return {
        'features': importance.index.tolist(),
        'importance': importance.values.tolist(),
        'model': predictor.get_model_best()
    }
```

### 9.2 Frontend Integration

**HTML Template Embedding**:
- Flask serves static HTML files
- Plotly.js for interactive visualizations
- Japanese font support via CSS

**Example Frontend Code**:
```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>Q-Storm Platform</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: 'Meiryo', sans-serif; }
    </style>
</head>
<body>
    <div id="pareto-chart"></div>
    <script>
        fetch('/api/v1/analysis/pareto', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                category_column: 'Mens_JACKETS&OUTER2',
                value_column: 'Total_Sales'
            })
        })
        .then(res => res.json())
        .then(data => {
            const trace = {
                x: data.categories,
                y: data.values,
                type: 'bar'
            };
            Plotly.newPlot('pareto-chart', [trace]);
        });
    </script>
</body>
</html>
```

---

## 10. Quality Architecture

### 10.1 Testing Strategy

#### 10.1.1 Unit Tests

**Test Files**:
- `test_pareto_system.py`: Core Pareto functionality
- `test_nan_fix.py`: NaN/Infinity handling
- `test_timeseries_fix.py`: Time series analysis
- `test_distribution.py`: Probability distribution analysis

**Example Test**:
```python
def test_pareto_analysis():
    """Test basic Pareto analysis"""
    df = create_test_dataframe()
    engine = ParetoAnalysisEngine()
    config = ParetoConfig(pareto_threshold=80.0)

    result = engine.analyze(df, config)

    assert len(result.categories) > 0
    assert sum(result.percentages) == 100.0
    assert len(result.vital_few) >= 1
```

#### 9.1.2 Integration Tests

**Test Scenarios**:
- File upload → Analysis → Export
- Multi-session isolation
- Error handling for invalid data
- Memory limit testing

#### 9.1.3 Performance Tests

**Load Testing**:
```bash
# Simulate 10 concurrent users
ab -n 100 -c 10 -p upload_payload.txt -T multipart/form-data \
   http://localhost:5003/api/v1/upload
```

### 10.2 Code Quality

**Code Style**:
- PEP 8 compliance
- Type hints for public functions
- Docstrings for all classes and public methods

**Linting**:
```bash
# Install tools
pip install flake8 mypy black

# Run linting
flake8 app_improved.py --max-line-length=100
mypy app_improved.py
black app_improved.py --check
```

### 10.3 Monitoring and Logging

**Logging Configuration**:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('qstorm.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

**Monitoring Endpoints**:
- `/api/v2/health`: System health and memory status
- `/api/v2/metrics`: Performance metrics (future enhancement)

---

## 11. Constraints and Limitations

### 11.1 Architectural Constraints

| Constraint | Impact | Mitigation |
|-----------|--------|------------|
| **Single-File Architecture** | Cannot scale horizontally | Use process managers for vertical scaling |
| **Session-Based Storage** | Not suitable for distributed deployment | Migrate to Redis/S3 for cloud deployment |
| **In-Memory Caching** | Cache lost on restart | Implement persistent cache with Redis |
| **No Authentication** | Security risk in production | Re-enable authentication in app.py (not app_noauth.py) |
| **Synchronous Processing** | Blocking for long analyses | Add Celery for background tasks |

### 11.2 Data Constraints

| Limit | Value | Rationale |
|-------|-------|-----------|
| **Max File Size** | 200-500MB (dynamic) | Memory availability |
| **Min Data Points** | 10 rows | Statistical significance |
| **Max Categories** | 30 | Visualization clarity |
| **Date Range** | 2019/4/30 - 2024/12/31 | Dataset specification |
| **Supported Stores** | 2 (恵比寿, 横浜元町) | Dataset specification |

### 11.3 Performance Constraints

**Expected Performance Degradation**:
- **>100MB files**: Upload time >10 seconds
- **>50,000 rows**: Analysis time >30 seconds
- **Concurrent users >5**: Response time degradation without horizontal scaling

---

## 12. Future Architecture Enhancements

### 12.1 Short-Term Enhancements (3-6 months)

1. **Persistent Database**
   - PostgreSQL for analysis history
   - SQLite knowledge base for QC Story insights

2. **Background Task Processing**
   - Celery for long-running analyses
   - Redis for task queue

3. **Enhanced Caching**
   - Redis for distributed caching
   - Cache warming strategies

4. **Authentication & Authorization**
   - JWT-based authentication
   - Role-based access control (RBAC)

### 12.2 Medium-Term Enhancements (6-12 months)

1. **Microservices Architecture**
   - Separate services for:
     - File upload & storage
     - Analysis engine
     - Visualization generation
     - Natural language processing

2. **Real-Time Analysis**
   - WebSocket for progress updates
   - Streaming analysis results

3. **AI Agent Integration**
   - Agent 1: 現状把握 (Current State Analysis)
   - Agent 2: 原因特定 (Root Cause Identification)
   - Agent 3: 効果予測・最適化 (Effect Prediction & Optimization)

4. **Advanced Analytics**
   - Causal inference with PyMC
   - Propensity score matching
   - Time series forecasting

### 12.3 Long-Term Vision (12+ months)

1. **Self-Evolving Knowledge System**
   - Analysis results → Knowledge base
   - Effectiveness score auto-update
   - Personalized improvement suggestions

2. **Multi-Tenant SaaS Architecture**
   - Tenant isolation
   - Usage-based pricing
   - Scalable infrastructure (Kubernetes)

3. **Enterprise Features**
   - LDAP/SAML integration
   - Audit logging
   - Data retention policies
   - Compliance (GDPR, ISO 27001)

---

## 13. Migration and Upgrade Paths

### 13.1 Version Migration

**From app.py (v2.0) to app_improved.py (v3.0)**:

| Feature | app.py | app_improved.py | Migration Notes |
|---------|--------|-----------------|-----------------|
| Upload Limits | Static (200MB) | Dynamic (200-500MB) | No code changes required |
| Security | Basic | Enhanced (XSS, input sanitization) | Test input validation |
| Probability Distribution | Not available | 6 distributions | New API endpoint |
| Caching | None | LRU cache | Performance improvement |
| Memory Management | Manual | Dynamic (psutil) | Install psutil |

**Migration Steps**:
1. Install psutil: `pip install psutil`
2. Update environment variables if needed
3. Test with small dataset first
4. Validate API compatibility (v1 endpoints unchanged)
5. Deploy app_improved.py to production

### 13.2 Data Migration

**Session Data Compatibility**:
- Both versions use same session ID format
- Uploaded files compatible between versions
- No database migration required (file-based storage)

---

## 14. Appendices

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| **QC Story** | Quality Control Story - 6-step problem-solving methodology |
| **Pareto Analysis** | 80/20 rule analysis identifying vital few vs trivial many |
| **ABC Analysis** | Categorization into A (70%), B (20%), C (10%) groups |
| **Vital Few** | Categories contributing to 80% of total value |
| **Trivial Many** | Categories contributing to remaining 20% of value |
| **Session ID** | Timestamp-based identifier for user sessions (YYYYMMDD_HHMMSS) |
| **NaN** | Not a Number - pandas representation of missing values |
| **LRU Cache** | Least Recently Used cache eviction policy |

### Appendix B: Reference Implementations

**Key Files**:
- `app.py`: Production stable version (v2.0)
- `app_improved.py`: Enhanced version (v3.0)
- `CLAUDE.md`: Development guidelines
- `Q-Storm Platform.md`: Requirements specification
- `test_pareto_system.py`: Comprehensive test suite

### Appendix C: External Dependencies

**Python Packages**:
```txt
flask==2.3.0
flask-cors==4.0.0
pandas==2.0.0
numpy==1.24.0
scipy==1.10.0
matplotlib==3.7.0
werkzeug==2.3.0
psutil==5.9.0  # Optional but recommended
langchain==0.0.200  # Optional for NLP
autogluon==0.8.0  # Optional for AutoML
```

### Appendix D: Contact and Support

**Project Owner**: Q-Storm Development Team
**Documentation Version**: 3.0
**Last Updated**: 2025-10-18
**Review Cycle**: Quarterly

## 15. Phase Transition Strategy

### 15.1 Phase 1 → Phase 2 Migration Path
- Database migration from file-based to PostgreSQL
- Session storage migration to Redis
- Async task queue implementation with Celery

### 15.2 Backward Compatibility
- Phase 1 API endpoints remain stable
- Data format compatibility maintained
- Gradual feature rollout

### 15.3 Rollback Plan
- Phase 1 environment preserved as fallback
- Database migration reversal procedures
- Performance regression testing

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-06 | Initial Team | Initial architecture documentation |
| 2.0 | 2024-09-20 | Claude Code | Enhanced with app_improved.py features |
| 3.0 | 2025-10-18 | Claude Code | Complete architecture specification with detailed diagrams |

---

**END OF DOCUMENT**
