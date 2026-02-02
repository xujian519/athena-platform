#!/usr/bin/env python3
"""
从本地JSON文件导入无效决定数据
Import Invalidation Decisions from Local JSON Files

作者: Athena平台团队
版本: v2.0.0
日期: 2026-01-27
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InvalidationDecisionImporter:
    """无效决定数据导入器"""

    def __init__(
        self,
        data_dir: str = "/Users/xujian/语料/专利-json/专利复审无效-json",
        host: str = "localhost",
        port: int = 5432,
        database: str = "patent_rules",
        user: str = "xujian"
    ):
        """初始化导入器"""
        self.data_dir = Path(data_dir)
        self.conn = psycopg2.connect(host=host, port=port, database=database, user=user)
        self.conn.autocommit = False
        logger.info(f"✅ 连接到PostgreSQL: {database}")
        logger.info(f"📁 数据目录: {data_dir}")

    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()

    def create_tables_if_not_exists(self):
        """创建必要的表"""
        logger.info("🔨 检查并创建表结构...")

        with self.conn.cursor() as cursor:
            # 创建新的增强表（与现有表不同）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invalidation_decisions_import (
                    decision_id VARCHAR(200) PRIMARY KEY,
                    patent_number VARCHAR(100),
                    invention_name TEXT,
                    patent_type VARCHAR(50),
                    patent_owner TEXT,
                    decision_conclusion VARCHAR(50),
                    decision_date DATE,
                    decision_content TEXT,
                    source_file TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)

            logger.info("✅ 表结构已就绪")
            self.conn.commit()

    def import_from_json_files(self, limit: int = None):
        """从JSON文件导入数据"""
        logger.info("📂 从JSON文件导入数据...")

        # 查找所有JSON文件
        json_files = list(self.data_dir.glob("*.json"))
        total_files = len(json_files)

        if limit:
            json_files = json_files[:limit]

        logger.info(f"📊 找到 {len(json_files):,} 个文件 (总共: {total_files:,})")

        imported_count = 0
        skipped_count = 0
        error_count = 0

        with self.conn.cursor() as cursor:
            batch_size = 100
            batch = []

            for i, json_file in enumerate(json_files):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # 提取关键字段
                    decision_id = data.get("document_id") or json_file.stem
                    patent_data = data.get("patent", {})
                    metadata = data.get("metadata", {})
                    content = data.get("content", {})

                    # 处理日期字段（空字符串转为None）
                    decision_date = metadata.get("decision_date", "")
                    if not decision_date or decision_date.strip() == "":
                        decision_date = None

                    # 插入主表
                    cursor.execute("""
                        INSERT INTO invalidation_decisions_import (
                            decision_id, patent_number, invention_name,
                            patent_type, patent_owner, decision_conclusion,
                            decision_date, decision_content, source_file
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (decision_id) DO UPDATE SET
                            updated_at = NOW()
                    """, (
                        decision_id,
                        patent_data.get("patent_number", ""),
                        patent_data.get("invention_name", ""),
                        patent_data.get("patent_type", ""),
                        patent_data.get("owner", ""),
                        metadata.get("decision_conclusion", ""),
                        decision_date,
                        content.get("full_text", "") or content.get("decision_text", "") or str(content)[:10000],
                        str(json_file.name)
                    ))

                    imported_count += 1

                    if imported_count % batch_size == 0:
                        self.conn.commit()
                        logger.info(f"  已导入: {imported_count}/{len(json_files)}")

                except json.JSONDecodeError as e:
                    skipped_count += 1
                    if skipped_count <= 5:
                        logger.warning(f"  ⚠️ 跳过 {json_file.name}: JSON解析错误")
                except Exception as e:
                    error_count += 1
                    if error_count <= 5:
                        logger.warning(f"  ⚠️ 错误 {json_file.name}: {e}")

            # 最后提交
            self.conn.commit()

        logger.info(f"✅ 导入完成:")
        logger.info(f"  • 成功: {imported_count:,}")
        logger.info(f"  • 跳过: {skipped_count:,}")
        logger.info(f"  • 错误: {error_count:,}")

        return imported_count

    def verify_import(self):
        """验证导入结果"""
        logger.info("🔍 验证导入结果...")

        with self.conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM invalidation_decisions_import")
            count = cursor.fetchone()[0]
            logger.info(f"📊 总记录数: {count:,}")

            # 按决定结果统计
            cursor.execute("""
                SELECT decision_conclusion, COUNT(*) as count
                FROM invalidation_decisions_import
                GROUP BY decision_conclusion
                ORDER BY count DESC
            """)
            logger.info("\n📊 按决定结果统计:")
            for record in cursor:
                conclusion = record[0] or "未知"
                count = record[1]
                logger.info(f"  • {conclusion}: {count:,}")

            # 按专利类型统计
            cursor.execute("""
                SELECT patent_type, COUNT(*) as count
                FROM invalidation_decisions_import
                GROUP BY patent_type
                ORDER BY count DESC
            """)
            logger.info("\n📊 按专利类型统计:")
            for record in cursor:
                patent_type = record[0] or "未知"
                count = record[1]
                logger.info(f"  • {patent_type}: {count:,}")

    def run(self, limit: int = None):
        """执行导入"""
        logger.info("🚀 开始无效决定数据导入...")
        start_time = datetime.now()

        try:
            # 1. 创建表
            self.create_tables_if_not_exists()

            # 2. 从文件导入
            count = self.import_from_json_files(limit)

            # 3. 验证
            self.verify_import()

            elapsed = (datetime.now() - start_time).total_seconds()

            logger.info(f"""
╔═══════════════════════════════════════════════════════════╗
║           ✅ 无效决定数据导入完成！                         ║
╠═══════════════════════════════════════════════════════════╣
║  导入记录数: {count:>20,} 条                              ║
║  耗时: {elapsed:>26.2f} 秒                               ║
╚═══════════════════════════════════════════════════════════╝
            """)

        except Exception as e:
            logger.error(f"❌ 导入失败: {e}")
            self.conn.rollback()
            raise


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="导入无效决定数据")
    parser.add_argument("--limit", type=int, help="限制导入文件数量（测试用）")
    args = parser.parse_args()

    importer = InvalidationDecisionImporter()

    try:
        importer.run(limit=args.limit)
        return 0
    except Exception as e:
        logger.error(f"❌ 执行失败: {e}")
        return 1
    finally:
        importer.close()


if __name__ == "__main__":
    sys.exit(main())
