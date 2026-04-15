#!/usr/bin/env python3
"""
专利审查指南增强数据PostgreSQL导入脚本
Enhanced Patent Guidelines PostgreSQL Import Script

功能：导入增强JSON数据到PostgreSQL + pgvector

作者: Athena平台团队
创建时间: 2026-01-21
版本: 4.0 (支持三模型增强数据)
"""

from __future__ import annotations
import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import execute_values

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(log_dir / f'pgvector_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class PGVectorImporter:
    """PostgreSQL + pgvector导入器"""

    def __init__(self):
        self.base_dir = Path("/Users/xujian/语料/专利-json-enhanced-v4/guideline")
        self.pg_config = {
            "host": "localhost",
            "port": 5432,
            "database": "patent_guidelines",
            "user": "xujian",
            "password": ""
        }
        self.pg_conn = None

        self.stats = {
            "total_files": 0,
            "processed_files": 0,
            "failed_files": 0,
            "total_chunks": 0,
            "postgresql_imported": 0,
            "start_time": None,
            "end_time": None
        }

        logger.info("=" * 80)
        logger.info("🚀 PostgreSQL + pgvector导入器")
        logger.info("=" * 80)

    def initialize_postgresql(self) -> Any:
        """初始化PostgreSQL并创建表"""
        logger.info("📊 初始化PostgreSQL数据库")

        try:
            # 首先连接到postgres数据库创建目标数据库
            conn_postgres = psycopg2.connect(
                host=self.pg_config["host"],
                port=self.pg_config["port"],
                database="postgres",
                user=self.pg_config["user"],
                password=self.pg_config["password"]
            )
            conn_postgres.autocommit = True
            cursor_postgres = conn_postgres.cursor()

            # 创建数据库（如果不存在）
            cursor_postgres.execute("SELECT 1 FROM pg_database WHERE datname='patent_guidelines'")
            if not cursor_postgres.fetchone():
                cursor_postgres.execute("CREATE DATABASE patent_guidelines")
                logger.info("✅ 创建数据库: patent_guidelines")

            cursor_postgres.close()
            conn_postgres.close()

            # 连接到目标数据库
            self.pg_conn = psycopg2.connect(**self.pg_config)
            self.pg_conn.autocommit = False
            cursor = self.pg_conn.cursor()

            # 启用pgvector扩展
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                logger.info("✅ pgvector扩展已启用")
            except Exception as e:
                logger.warning(f"⚠️ pgvector扩展警告: {e}")

            # 创建表结构
            tables_sql = [
                # 主文档表
                """
                DROP TABLE IF EXISTS guideline_chunks CASCADE;
                CREATE TABLE guideline_chunks (
                    id SERIAL PRIMARY KEY,
                    chunk_id VARCHAR(100) UNIQUE NOT NULL,
                    document_id VARCHAR(100),
                    file_name VARCHAR(255),
                    level VARCHAR(50),
                    title TEXT,
                    content TEXT,
                    bge_m3_embedding vector(1024),
                    bert_ner_entities JSONB,
                    deepseek_summary TEXT,
                    deepseek_key_concepts TEXT[],
                    deepseek_practical_guidance TEXT,
                    deepseek_related_rules TEXT[],
                    deepseek_risk_points TEXT[],
                    deepseek_thinking_process TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                """,

                # 创建索引
                "CREATE INDEX IF NOT EXISTS idx_chunks_document ON guideline_chunks(document_id);",
                "CREATE INDEX IF NOT EXISTS idx_chunks_level ON guideline_chunks(level);",
                "CREATE INDEX IF NOT EXISTS idx_chunks_file ON guideline_chunks(file_name);",
            ]

            for sql in tables_sql:
                cursor.execute(sql)

            self.pg_conn.commit()
            cursor.close()

            logger.info("✅ PostgreSQL表结构创建完成")

        except Exception as e:
            logger.error(f"❌ PostgreSQL初始化失败: {e}")
            logger.error(traceback.format_exc())
            raise

    def import_file(self, json_path: Path) -> bool:
        """导入单个增强JSON文件"""
        try:
            with open(json_path, encoding='utf-8') as f:
                enhanced_data = json.load(f)

            cursor = self.pg_conn.cursor()

            # 提取基础信息
            original_data = enhanced_data.get("original_data", {})
            hierarchy_info = enhanced_data.get("hierarchy_info", {})
            enhanced_chunks = enhanced_data.get("enhanced_chunks", [])

            document_id = original_data.get("section_id", "unknown")
            file_name = hierarchy_info.get("file_name", json_path.name)

            # 批量插入内容块
            chunk_values = []

            for chunk in enhanced_chunks:
                chunk_id = chunk.get("chunk_id", "")
                bge_embedding = chunk.get("bge_m3_embedding", {})
                bert_entities = chunk.get("bert_ner_entities", [])
                deepseek_enhancement = chunk.get("qwen_enhancement", {}).get("enhanced_content", {})

                # 构建向量字符串
                embedding_str = None
                if bge_embedding.get("embedding"):
                    embedding_str = f"[{','.join(map(str, bge_embedding['embedding']))}]"

                chunk_values.append((
                    chunk_id,
                    document_id,
                    file_name,
                    chunk.get("level", 0),
                    chunk.get("title", "")[:500],
                    chunk.get("content", "")[:5000],
                    embedding_str,
                    json.dumps(bert_entities, ensure_ascii=False),
                    deepseek_enhancement.get("summary", "")[:1000],
                    deepseek_enhancement.get("key_concepts", []),
                    deepseek_enhancement.get("practical_guidance", "")[:2000],
                    deepseek_enhancement.get("related_rules", []),
                    deepseek_enhancement.get("risk_points", []),
                    deepseek_enhancement.get("thinking_process", "")[:2000],
                    json.dumps(chunk.get("metadata", {}), ensure_ascii=False)
                ))

            # 批量插入
            if chunk_values:
                execute_values(
                    cursor,
                    """
                    INSERT INTO guideline_chunks (
                        chunk_id, document_id, file_name, level, title, content, bge_m3_embedding,
                        bert_ner_entities, deepseek_summary, deepseek_key_concepts,
                        deepseek_practical_guidance, deepseek_related_rules,
                        deepseek_risk_points, deepseek_thinking_process, metadata
                    ) VALUES %s
                    ON CONFLICT (chunk_id) DO UPDATE SET
                        bge_m3_embedding = EXCLUDED.bge_m3_embedding,
                        bert_ner_entities = EXCLUDED.bert_ner_entities,
                        deepseek_summary = EXCLUDED.deepseek_summary,
                        deepseek_key_concepts = EXCLUDED.deepseek_key_concepts,
                        deepseek_practical_guidance = EXCLUDED.deepseek_practical_guidance,
                        deepseek_related_rules = EXCLUDED.deepseek_related_rules,
                        deepseek_risk_points = EXCLUDED.deepseek_risk_points,
                        deepseek_thinking_process = EXCLUDED.deepseek_thinking_process,
                        metadata = EXCLUDED.metadata
                    """,
                    chunk_values
                )
                self.pg_conn.commit()
                self.stats["postgresql_imported"] += len(chunk_values)
                self.stats["total_chunks"] += len(chunk_values)

            cursor.close()
            return True

        except Exception as e:
            logger.error(f"❌ 导入失败 {json_path.name}: {e}")
            self.pg_conn.rollback()
            return False

    def run(self) -> None:
        """运行导入流程"""
        self.stats["start_time"] = datetime.now()

        logger.info("=" * 80)
        logger.info("🚀 开始导入流程")
        logger.info("=" * 80)

        # 初始化PostgreSQL
        self.initialize_postgresql()

        # 扫描增强JSON文件
        json_files = list(self.base_dir.glob("*.json"))
        self.stats["total_files"] = len(json_files)

        logger.info(f"📁 发现 {len(json_files)} 个增强JSON文件")

        # 批量处理文件
        batch_size = 50
        for i in range(0, len(json_files), batch_size):
            batch = json_files[i:i + batch_size]
            logger.info(f"📦 处理批次 {i // batch_size + 1}/{(len(json_files) + batch_size - 1) // batch_size}")

            batch_success = 0
            for json_path in batch:
                if self.import_file(json_path):
                    batch_success += 1
                    self.stats["processed_files"] += 1
                else:
                    self.stats["failed_files"] += 1

            # 显示进度
            progress = (i + len(batch)) / len(json_files) * 100
            logger.info(f"  批次完成: {batch_success}/{len(batch)} 成功")
            logger.info(f"📊 总进度: {min(progress, 100):.1f}% ({self.stats['processed_files']}/{len(json_files)})")
            logger.info(f"  已导入内容块: {self.stats['postgresql_imported']}")

        self.stats["end_time"] = datetime.now()
        self.print_statistics()

    def print_statistics(self) -> Any:
        """打印统计信息"""
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        logger.info("")
        logger.info("=" * 80)
        logger.info("🎉 导入完成！")
        logger.info("=" * 80)
        logger.info("📊 统计信息:")
        logger.info(f"  总文件数: {self.stats['total_files']}")
        logger.info(f"  成功处理: {self.stats['processed_files']}")
        logger.info(f"  失败文件: {self.stats['failed_files']}")
        logger.info(f"  总内容块: {self.stats['total_chunks']}")
        logger.info(f"  PostgreSQL导入: {self.stats['postgresql_imported']}")
        logger.info(f"  处理时间: {duration:.2f}秒 ({duration/60:.1f}分钟)")
        logger.info(f"  平均速度: {self.stats['total_chunks'] / duration if duration > 0 else 0:.2f} 块/秒")
        logger.info("=" * 80)

        # 保存统计
        stats_file = log_dir / f"import_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump({
                **self.stats,
                "start_time": self.stats["start_time"].isoformat(),
                "end_time": self.stats["end_time"].isoformat()
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"📄 统计已保存: {stats_file}")

    def close(self) -> Any:
        """关闭连接"""
        if self.pg_conn:
            self.pg_conn.close()


def main() -> None:
    """主函数"""
    importer = PGVectorImporter()

    try:
        importer.run()
    except KeyboardInterrupt:
        logger.info("⚠️ 用户中断")
    except Exception as e:
        logger.error(f"❌ 导入失败: {e}")
        logger.error(traceback.format_exc())
    finally:
        importer.close()


if __name__ == "__main__":
    main()
