#!/usr/bin/env python3
"""
SQLite到PostgreSQL数据迁移脚本
Data Migration Script: SQLite to PostgreSQL

将记忆系统数据从SQLite迁移到PostgreSQL
"""

from __future__ import annotations
import logging
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg2
from dotenv import load_dotenv

# 设置路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
env_file = project_root / "production" / "config" / ".env.memory"
if env_file.exists():
    load_dotenv(env_file)

# 配置日志
log_dir = project_root / "production" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "migration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# 数据库配置
SQLITE_DB_PATH = project_root / "data" / "memory" / "long_term_memory.db"

POSTGRES_CONFIG = {
    'host': os.getenv('MEMORY_DB_HOST', 'localhost'),
    'port': int(os.getenv('MEMORY_DB_PORT', '5432')),
    'database': os.getenv('MEMORY_DB_NAME', 'memory_module'),
    'user': os.getenv('MEMORY_DB_USER', 'xujian'),
    'password': os.getenv('MEMORY_DB_PASSWORD', '')
}


class DataMigration:
    """数据迁移类"""

    def __init__(self):
        self.sqlite_conn = None
        self.postgres_conn = None
        self.migration_stats = {
            'memories_migrated': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }

    def connect_sqlite(self) -> bool:
        """连接SQLite数据库"""
        try:
            if not SQLITE_DB_PATH.exists():
                logger.error(f"SQLite数据库不存在: {SQLITE_DB_PATH}")
                return False

            self.sqlite_conn = sqlite3.connect(str(SQLITE_DB_PATH))
            self.sqlite_conn.row_factory = sqlite3.Row
            logger.info(f"✅ 已连接SQLite数据库: {SQLITE_DB_PATH}")
            return True
        except Exception as e:
            logger.error(f"❌ 连接SQLite失败: {e}")
            return False

    def connect_postgres(self) -> bool:
        """连接PostgreSQL数据库"""
        try:
            self.postgres_conn = psycopg2.connect(
                host=POSTGRES_CONFIG['host'],
                port=POSTGRES_CONFIG['port'],
                database=POSTGRES_CONFIG['database'],
                user=POSTGRES_CONFIG['user'],
                password=POSTGRES_CONFIG['password']
            )
            logger.info(f"✅ 已连接PostgreSQL数据库: {POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}")
            return True
        except Exception as e:
            logger.error(f"❌ 连接PostgreSQL失败: {e}")
            return False

    def create_postgres_tables(self) -> bool:
        """创建PostgreSQL表结构"""
        try:
            with self.postgres_conn.cursor() as cursor:
                # 创建记忆表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS memories (
                        id SERIAL PRIMARY KEY,
                        memory_id VARCHAR(255) UNIQUE NOT NULL,
                        agent_id VARCHAR(255) NOT NULL,
                        content TEXT NOT NULL,
                        memory_type VARCHAR(100) NOT NULL,
                        importance FLOAT DEFAULT 0.5,
                        emotional_weight FLOAT DEFAULT 0.0,
                        family_related BOOLEAN DEFAULT FALSE,
                        work_related BOOLEAN DEFAULT TRUE,
                        tags JSONB,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        access_count INTEGER DEFAULT 0
                    );
                """)

                # 创建索引
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_memories_agent_id
                    ON memories(agent_id);
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_memories_type
                    ON memories(memory_type);
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_memories_importance
                    ON memories(importance DESC);
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_memories_created
                    ON memories(created_at DESC);
                """)

                self.postgres_conn.commit()
                logger.info("✅ PostgreSQL表结构创建完成")
                return True

        except Exception as e:
            logger.error(f"❌ 创建PostgreSQL表失败: {e}")
            self.postgres_conn.rollback()
            return False

    def get_sqlite_data(self) -> list[dict[str, Any]]:
        """从SQLite获取数据"""
        try:
            with self.sqlite_conn.cursor() as cursor:
                cursor.execute("SELECT * FROM long_term_memories")
                rows = cursor.fetchall()
                data = [dict(row) for row in rows]
                logger.info(f"📊 从SQLite读取 {len(data)} 条记录")
                return data
        except Exception as e:
            logger.error(f"❌ 读取SQLite数据失败: {e}")
            return []

    def migrate_data(self, data: list[dict[str, Any]]) -> int:
        """迁移数据到PostgreSQL"""
        migrated_count = 0

        try:
            with self.postgres_conn.cursor() as cursor:
                for record in data:
                    try:
                        # 转换数据格式
                        insert_query = """
                            INSERT INTO memories (
                                memory_id, agent_id, content, memory_type,
                                importance, emotional_weight, family_related,
                                work_related, tags, metadata, created_at
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                            ON CONFLICT (memory_id) DO NOTHING
                        """

                        cursor.execute(insert_query, (
                            record.get('memory_id'),
                            record.get('agent_id'),
                            record.get('content'),
                            record.get('memory_type'),
                            record.get('importance', 0.5),
                            record.get('emotional_weight', 0.0),
                            record.get('family_related', False),
                            record.get('work_related', True),
                            record.get('tags', '[]'),
                            record.get('metadata', '{}'),
                            record.get('created_at', datetime.now())
                        ))

                        migrated_count += 1

                        # 每100条提交一次
                        if migrated_count % 100 == 0:
                            self.postgres_conn.commit()
                            logger.info(f"   已迁移 {migrated_count} 条记录")

                    except Exception as e:
                        logger.warning(f"⚠️  跳过记录 {record.get('memory_id')}: {e}")
                        self.migration_stats['errors'] += 1
                        continue

                # 最终提交
                self.postgres_conn.commit()

        except Exception as e:
            logger.error(f"❌ 迁移数据失败: {e}")
            self.postgres_conn.rollback()

        return migrated_count

    def verify_migration(self) -> bool:
        """验证迁移结果"""
        try:
            with self.postgres_conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM memories")
                postgres_count = cursor.fetchone()[0]

            with self.sqlite_conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM long_term_memories")
                sqlite_count = cursor.fetchone()[0]

            logger.info("📊 迁移验证:")
            logger.info(f"   SQLite记录数: {sqlite_count}")
            logger.info(f"   PostgreSQL记录数: {postgres_count}")

            if postgres_count >= sqlite_count:
                logger.info("✅ 数据迁移验证通过")
                return True
            else:
                logger.warning(f"⚠️  数据不完整: PostgreSQL比SQLite少{sqlite_count - postgres_count}条")
                return False

        except Exception as e:
            logger.error(f"❌ 验证失败: {e}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
            logger.info("✅ SQLite连接已关闭")

        if self.postgres_conn:
            self.postgres_conn.close()
            logger.info("✅ PostgreSQL连接已关闭")

    def run(self) -> bool:
        """执行完整迁移流程"""
        self.migration_stats['start_time'] = datetime.now()

        logger.info("=" * 60)
        logger.info("🔄 开始SQLite到PostgreSQL数据迁移")
        logger.info("=" * 60)

        # 连接数据库
        if not self.connect_sqlite():
            return False

        if not self.connect_postgres():
            return False

        # 创建表结构
        if not self.create_postgres_tables():
            return False

        # 获取数据
        data = self.get_sqlite_data()
        if not data:
            logger.warning("⚠️  没有数据需要迁移")
            return True

        # 迁移数据
        logger.info("📦 开始迁移数据...")
        migrated = self.migrate_data(data)
        self.migration_stats['memories_migrated'] = migrated

        # 验证结果
        if not self.verify_migration():
            logger.warning("⚠️  迁移验证未完全通过，请检查数据")

        # 关闭连接
        self.close()

        self.migration_stats['end_time'] = datetime.now()

        # 输出统计
        duration = (self.migration_stats['end_time'] - self.migration_stats['start_time']).total_seconds()
        logger.info("=" * 60)
        logger.info("📊 迁移统计:")
        logger.info(f"   迁移记录数: {migrated}")
        logger.info(f"   错误数量: {self.migration_stats['errors']}")
        logger.info(f"   耗时: {duration:.2f}秒")
        logger.info("=" * 60)

        return True


def main():
    """主函数"""

    # 检查SQLite数据库
    if not SQLITE_DB_PATH.exists():
        logger.error(f"❌ SQLite数据库文件不存在: {SQLITE_DB_PATH}")
        logger.info("💡 如果没有SQLite数据，可以忽略此迁移")
        return

    # 执行迁移
    migration = DataMigration()
    success = migration.run()

    if success:
        logger.info("✅ 数据迁移完成")
        sys.exit(0)
    else:
        logger.error("❌ 数据迁移失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
