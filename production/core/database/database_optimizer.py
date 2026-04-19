#!/usr/bin/env python3
"""
数据库优化器
Database Optimizer for Production

提供SQLite数据库的性能优化功能,包括索引创建、查询优化和数据清理。
"""

from __future__ import annotations
import logging
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """
    数据库优化器

    提供SQLite数据库的性能优化功能,包括:
    - 创建索引
    - 查询计划分析
    - 数据清理
    - 数据库碎片整理(VACUUM)
    - 统计信息更新(ANALYZE)
    """

    # 默认数据库路径(相对于项目根目录)
    DEFAULT_DB_PATH = "data/online_learning.db"

    # SQLite优化配置
    PRAGMA_SETTINGS = {
        "journal_mode": "WAL",  # Write-Ahead Logging模式
        "synchronous": "NORMAL",  # 同步模式
        "cache_size": -10000,  # 缓存大小(负值表示KB,-10000=10MB)
        "temp_store": "MEMORY",  # 临时表存储在内存中
        "mmap_size": 268435456,  # 内存映射大小(256MB)
    }

    def __init__(self, db_path: str | None = None):
        """
        初始化数据库优化器

        Args:
            db_path: 数据库文件路径。如果为None,使用以下顺序查找:
                     1. 环境变量 DB_PATH
                     2. 项目data目录下的默认路径
        """
        if db_path is None:
            # 优先使用环境变量
            db_path = os.getenv("DB_PATH")

            # 其次使用项目相对路径
            if db_path is None:
                # 获取项目根目录(假设当前文件在core/database/下)
                project_root = Path(__file__).parent.parent.parent
                db_path = str(project_root / self.DEFAULT_DB_PATH)

        self.db_path = db_path
        self.connection: sqlite3.Connection | None = None

        logger.info(f"数据库优化器初始化,数据库路径: {self.db_path}")

    def connect(self) -> bool:
        """
        连接数据库并应用优化设置

        Returns:
            bool: 连接是否成功
        """
        try:
            # 确保数据库目录存在
            db_file = Path(self.db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)

            self.connection = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)

            # 应用SQLite优化设置
            for pragma, value in self.PRAGMA_SETTINGS.items():
                self.connection.execute(f"PRAGMA {pragma}={value}")

            logger.info("✅ 数据库连接成功,优化设置已应用")
            return True

        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            return False

    def create_indexes(self) -> bool:
        """
        创建数据库索引以提升查询性能

        Returns:
            bool: 索引创建是否成功
        """
        if not self.connection:
            logger.error("数据库未连接")
            return False

        try:
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_conversations_intent ON conversations(predicted_intent)",
                "CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_feedback_request ON feedback(request_id)",
                "CREATE INDEX IF NOT EXISTS idx_model_versions_created ON model_versions(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_performance_metrics_intent ON performance_metrics(predicted_intent)",
            ]

            for index_sql in indexes:
                start_time = time.time()
                self.connection.execute(index_sql)
                # 提取索引名称
                index_name = index_sql.split()[5]
                elapsed = time.time() - start_time
                logger.info(f"🔑 索引创建: {index_name} ({elapsed:.3f}s)")

            self.connection.commit()
            logger.info("✅ 数据库索引创建完成")
            return True

        except Exception as e:
            logger.error(f"❌ 索引创建失败: {e}")
            return False

    def optimize_database(self) -> dict[str, Any]:
        """
        优化数据库

        包括:
        1. 分析查询计划
        2. 检查表统计信息
        3. 清理过期数据
        4. 数据库碎片整理(VACUUM)
        5. 更新统计信息(ANALYZE)

        Returns:
            dict: 优化结果报告
        """
        if not self.connection:
            return {"error": "数据库未连接"}

        optimization_results: dict[str, Any] = {}

        try:
            # 1. 分析查询计划
            start_time = time.time()
            cursor = self.connection.cursor()
            cursor.execute(
                "EXPLAIN QUERY PLAN SELECT * FROM conversations WHERE predicted_intent = ? LIMIT 10",
                ("PATENT_ANALYSIS",),
            )
            plan = cursor.fetchall()
            optimization_results["query_plan_analysis"] = {
                "execution_time": time.time() - start_time,
                "plan": [row[3] for row in plan[:3]],  # 提取查询计划详情
            }

            # 2. 检查表统计信息
            start_time = time.time()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            table_stats = {}
            for table_name in tables:
                if table_name not in ["sqlite_sequence"]:
                    try:
                        # 验证表名安全(只允许字母、数字和下划线)
                        import re

                        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
                            logger.warning(f"跳过非法表名: {table_name}")
                            continue

                        # SQLite中表名来自sqlite_master,已验证安全性
                        # 使用方括号进一步保护
                        cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
                        count = cursor.fetchone()[0]
                        table_stats[table_name] = count
                    except Exception:
                        pass  # 跳过无法查询的表

            optimization_results["table_statistics"] = table_stats

            # 3. 清理过期数据(30天前的性能指标)
            start_time = time.time()
            cursor.execute(
                "DELETE FROM performance_metrics WHERE timestamp < datetime('now', '-30 days')"
            )
            deleted_rows = cursor.rowcount

            if deleted_rows > 0:
                self.connection.commit()
                logger.info(f"🗑️ 清理过期性能数据: {deleted_rows} 行")

            optimization_results["cleanup"] = {
                "deleted_rows": deleted_rows,
                "execution_time": time.time() - start_time,
            }

            # 4. 数据库碎片整理
            start_time = time.time()
            cursor.execute("VACUUM")
            optimization_results["vacuum"] = {"execution_time": time.time() - start_time}

            # 5. 更新统计信息
            start_time = time.time()
            cursor.execute("ANALYZE")
            optimization_results["analyze"] = {"execution_time": time.time() - start_time}

            logger.info("✅ 数据库优化完成")

        except Exception as e:
            logger.error(f"❌ 数据库优化失败: {e}")
            optimization_results["error"] = str(e)

        return optimization_results

    def get_database_stats(self) -> dict[str, Any]:
        """
        获取数据库统计信息

        Returns:
            dict: 数据库统计信息
        """
        if not self.connection:
            return {"error": "数据库未连接"}

        try:
            cursor = self.connection.cursor()

            # 数据库文件大小
            db_file = Path(self.db_path)
            file_size = db_file.stat().st_size if db_file.exists() else 0

            # 页面统计
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]

            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]

            # 获取所有表的行数
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            table_row_counts = {}
            for table_name in tables:
                if table_name not in ["sqlite_sequence"]:
                    try:
                        # 验证表名安全(只允许字母、数字和下划线)
                        import re

                        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
                            logger.warning(f"跳过非法表名: {table_name}")
                            continue

                        # SQLite中表名来自sqlite_master,已验证安全性
                        # 使用方括号进一步保护
                        cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
                        table_row_counts[table_name] = cursor.fetchone()[0]
                    except Exception as e:
                        # 记录异常但不中断流程
                        logger.debug(f"[database_optimizer] Exception: {e}")

            stats = {
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / 1024 / 1024, 2),
                "page_count": page_count,
                "page_size": page_size,
                "total_size_pages": page_count * page_size,
                "table_row_counts": table_row_counts,
                "total_tables": len(tables),
                "journal_mode": self.PRAGMA_SETTINGS["journal_mode"],
            }

            return stats

        except Exception as e:
            return {"error": f"获取统计失败: {e}"}

    def close(self) -> Any:
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("🔒 数据库连接已关闭")


# 全局数据库优化器实例(延迟初始化)
_db_optimizer: DatabaseOptimizer | None = None


def get_database_optimizer(db_path: str | None = None) -> DatabaseOptimizer:
    """
    获取数据库优化器实例(单例模式)

    Args:
        db_path: 数据库路径(仅在首次调用时有效)

    Returns:
        DatabaseOptimizer: 数据库优化器实例
    """
    global _db_optimizer

    if _db_optimizer is None:
        _db_optimizer = DatabaseOptimizer(db_path)
        _db_optimizer.connect()

    return _db_optimizer
