"""Q-Storm Platform - SQLite Database Manager (Phase 2A)"""
import sqlite3
from datetime import datetime
import json
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict, Any, List


class DatabaseManager:
    """SQLiteベースのデータベース管理"""

    def __init__(self, db_path='data/qstorm.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def get_connection(self):
        """コンテキストマネージャーで安全な接続管理"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # 辞書形式でアクセス
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """データベース初期化"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # sessions テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    store TEXT,
                    user_id TEXT,
                    metadata TEXT
                )
            ''')

            # analysis_results テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    analysis_type TEXT NOT NULL,
                    store TEXT,
                    target_column TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    parameters TEXT,
                    results TEXT,
                    execution_time REAL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            ''')

            # インデックス作成
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_session_id 
                ON analysis_results(session_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analysis_type 
                ON analysis_results(analysis_type)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON analysis_results(created_at DESC)
            ''')

    def save_session(self, session_id: str, store: Optional[str] = None,
                    user_id: Optional[str] = None, metadata: Optional[Dict] = None) -> int:
        """セッション保存"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO sessions 
                (session_id, store, user_id, metadata, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (session_id, store, user_id, json.dumps(metadata or {})))
            return cursor.lastrowid

    def save_analysis_result(self, session_id: str, analysis_type: str,
                            store: Optional[str], target_column: Optional[str],
                            parameters: Dict, results: Dict,
                            execution_time: float) -> int:
        """分析結果保存"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO analysis_results 
                (session_id, analysis_type, store, target_column, 
                 parameters, results, execution_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, analysis_type, store, target_column,
                  json.dumps(parameters), json.dumps(results), execution_time))
            return cursor.lastrowid

    def get_analysis_results(self, session_id: Optional[str] = None,
                            analysis_type: Optional[str] = None,
                            store: Optional[str] = None,
                            limit: int = 100) -> List[Dict[str, Any]]:
        """分析結果取得"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = 'SELECT * FROM analysis_results WHERE 1=1'
            params = []

            if session_id:
                query += ' AND session_id = ?'
                params.append(session_id)
            if analysis_type:
                query += ' AND analysis_type = ?'
                params.append(analysis_type)
            if store:
                query += ' AND store = ?'
                params.append(store)

            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッションサマリー取得"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    s.*,
                    COUNT(ar.id) as analysis_count,
                    MAX(ar.created_at) as last_analysis
                FROM sessions s
                LEFT JOIN analysis_results ar ON s.session_id = ar.session_id
                WHERE s.session_id = ?
                GROUP BY s.session_id
            ''', (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
