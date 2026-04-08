"""
数据库管理模块
"""
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from config import DB_PATH, DEFAULT_CATEGORIES


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_database()

    def _get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)

    def _init_database(self):
        """初始化数据库表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 创建 snippets 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS snippets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    code TEXT NOT NULL,
                    language TEXT DEFAULT 'text',
                    tags TEXT DEFAULT '',
                    category TEXT DEFAULT '默认',
                    usage_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建 categories 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    name TEXT PRIMARY KEY,
                    description TEXT DEFAULT ''
                )
            """)

            # 初始化默认分类
            for name, desc in DEFAULT_CATEGORIES:
                cursor.execute(
                    "INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)",
                    (name, desc)
                )

            conn.commit()

    def execute_query(self, query: str, params: tuple = ()) -> List[tuple]:
        """执行查询并返回结果"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """执行更新，返回影响行数或插入ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """批量执行"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount