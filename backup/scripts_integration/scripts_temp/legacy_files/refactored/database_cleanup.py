#!/usr/bin/env python3
"""
重构后的数据库清理脚本
使用新的基础设施库
"""

import sys
import os
import logging

# 添加核心库路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.database import db_manager
from utils.progress_tracker import ProgressTracker
from utils.logger import ScriptLogger


class DatabaseCleanup:
    """数据库清理服务"""

    def __init__(self):
        self.logger = ScriptLogger("DatabaseCleanup")
        self.db = db_manager

    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志"""
        self.logger.info(f"开始清理超过{days}天的日志记录")

        # 查询需要删除的记录
        query = """
            SELECT COUNT(*) as count
            FROM system_logs
            WHERE created_at < NOW() - INTERVAL '%s days'
        """ % days

        result = self.db.execute_query(query)
        if result:
            count = result[0]['count']
            self.logger.info(f"找到 {count} 条旧日志记录")

            if count > 0:
                tracker = ProgressTracker(count, "日志清理")

                # 分批删除
                batch_size = 1000
                deleted = 0

                while deleted < count:
                    batch_delete = min(batch_size, count - deleted)

                    query = """
                        DELETE FROM system_logs
                        WHERE id IN (
                            SELECT id FROM system_logs
                            WHERE created_at < NOW() - INTERVAL '%s days'
                            LIMIT %s
                        )
                    """ % (days, batch_delete)

                    rows_deleted = self.db.execute_update(query)
                    deleted += rows_deleted
                    tracker.update(batch_delete)

                tracker.complete()

    def cleanup_temp_tables(self):
        """清理临时表"""
        temp_tables = [
            'temp_imports',
            'temp_processing',
            'temp_cache'
        ]

        tracker = ProgressTracker(len(temp_tables), "临时表清理")

        for table in temp_tables:
            # 检查表是否存在
            if self._table_exists(table):
                self.logger.info(f"清理临时表: {table}")

                # 删除表数据
                self.db.execute_update(f"DELETE FROM {table}")

                # 重置序列（如果有）
                self.db.execute_update(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1")

                tracker.update(1, f"已清理 {table}")
            else:
                self.logger.info(f"临时表 {table} 不存在，跳过")

        tracker.complete()

    def _table_exists(self, table: str) -> bool:
        """检查表是否存在"""
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = %s
            )
        """
        result = self.db.execute_query(query, (table,))
        return result[0]['exists'] if result else False

    def vacuum_database(self):
        """数据库真空清理"""
        self.logger.info("开始数据库真空清理...")

        # 获取所有表名
        query = """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename NOT LIKE 'pg_%'
        """

        tables = self.db.execute_query(query)
        if tables:
            tracker = ProgressTracker(len(tables), "VACUUM")

            for table_info in tables:
                table = table_info['tablename']
                try:
                    self.db.execute_query(f"VACUUM ANALYZE {table}")
                    tracker.update(1, f"VACUUM {table}")
                except Exception as e:
                    self.logger.error(f"VACUUM {table} 失败: {e}")

            tracker.complete()

    def update_statistics(self):
        """更新统计信息"""
        self.logger.info("更新统计信息...")

        tables = ['users', 'patents', 'logs', 'system_logs']
        tracker = ProgressTracker(len(tables), "统计更新")

        for table in tables:
            if self._table_exists(table):
                try:
                    self.db.execute_query(f"ANALYZE {table}")
                    tracker.update(1, f"ANALYZE {table}")
                except Exception as e:
                    self.logger.error(f"ANALYZE {table} 失败: {e}")

        tracker.complete()

    def run_cleanup(self):
        """执行完整清理流程"""
        try:
            self.logger.info("开始数据库清理流程")

            # 1. 清理旧日志
            self.cleanup_old_logs(30)

            # 2. 清理临时表
            self.cleanup_temp_tables()

            # 3. 更新统计信息
            self.update_statistics()

            # 4. VACUUM清理（可选，在低峰期执行）
            if input("是否执行VACUUM清理？这可能需要较长时间 (y/n): ").lower() == 'y':
                self.vacuum_database()

            self.logger.info("✅ 数据库清理完成")

        except Exception as e:
            self.logger.error(f"数据库清理失败: {e}")
            raise


def main():
    """主函数"""
    cleanup = DatabaseCleanup()
    cleanup.run_cleanup()


if __name__ == "__main__":
    main()