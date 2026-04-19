#!/usr/bin/env python3
"""
专利审查指南原始数据导入脚本
Original Patent Guidelines Data Import Script

功能：导入原始JSON数据到PostgreSQL + pgvector（跳过已存在的数据）

作者: Athena平台团队
创建时间: 2026-01-21
"""

from __future__ import annotations
import hashlib
import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import execute_values

# 配置日志
log_dir = Path("/Users/xujian/Athena工作平台/logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(log_dir / f'original_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class OriginalDataImporter:
    """原始数据导入器"""

    def __init__(self):
        self.base_dir = Path("/Users/xujian/语料/专利-json/guideline")
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
            "skipped_files": 0,
            "failed_files": 0,
            "total_chunks": 0,
            "imported_chunks": 0,
            "skipped_chunks": 0,
            "start_time": None,
            "end_time": None
        }

        logger.info("=" * 80)
        logger.info("🚀 原始专利数据导入器")
        logger.info("=" * 80)

    def connect_db(self) -> Any:
        """连接数据库"""
        try:
            self.pg_conn = psycopg2.connect(**self.pg_config)
            self.pg_conn.autocommit = False
            logger.info("✅ 数据库连接成功")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise

    def generate_chunk_id(self, section_id: str, chunk_type: str, index: int) -> str:
        """生成唯一的chunk_id"""
        content = f"{section_id}_{chunk_type}_{index}"
        return hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()[:16]

    def import_file(self, json_path: Path) -> bool:
        """导入单个原始JSON文件"""
        try:
            with open(json_path, encoding='utf-8') as f:
                data = json.load(f)

            cursor = self.pg_conn.cursor()

            section_id = data.get("section_id", "")
            hierarchy = data.get("hierarchy", {})
            content = data.get("content", {})
            entities = data.get("entities", [])
            embedding_chunks = data.get("embedding_chunks", [])

            file_name = json_path.name
            level = hierarchy.get("level", "unknown")
            title = content.get("title", "")
            raw_text = content.get("raw_text", "")
            enhanced_text = content.get("enhanced_text", "")

            # 构建chunk数据
            chunks_to_import = []
            skipped_count = 0

            # 为每个embedding chunk创建记录
            for idx, emb_chunk in enumerate(embedding_chunks):
                chunk_type = emb_chunk.get("type", "unknown")
                embedding = emb_chunk.get("embedding", [])

                # 生成chunk_id
                chunk_id = self.generate_chunk_id(section_id, chunk_type, idx)

                # 检查是否已存在
                cursor.execute(
                    "SELECT chunk_id FROM guideline_chunks WHERE chunk_id = %s",
                    (chunk_id,)
                )
                if cursor.fetchone():
                    skipped_count += 1
                    continue

                # 根据type选择文本内容
                if chunk_type == "title":
                    text = title
                elif chunk_type == "content":
                    text = raw_text or enhanced_text
                else:
                    text = raw_text or title

                # 限制文本长度
                text = text[:5000] if text else ""

                # 构建向量字符串
                embedding_str = None
                if embedding and isinstance(embedding, list):
                    embedding_str = f"[{','.join(map(str, embedding))}]"

                chunks_to_import.append((
                    chunk_id,
                    section_id,
                    file_name,
                    level,
                    title[:500] if title else None,
                    text,
                    embedding_str,
                    json.dumps(entities, ensure_ascii=False),
                    None,  # deepseek_summary (原始数据没有)
                    [],   # deepseek_key_concepts
                    None, # deepseek_practical_guidance
                    [],   # deepseek_related_rules
                    [],   # deepseek_risk_points
                    None, # deepseek_thinking_process
                    json.dumps({"source": "original", "chunk_type": chunk_type}, ensure_ascii=False)
                ))

            # 批量插入
            if chunks_to_import:
                execute_values(
                    cursor,
                    """
                    INSERT INTO guideline_chunks (
                        chunk_id, document_id, file_name, level, title, content, bge_m3_embedding,
                        bert_ner_entities, deepseek_summary, deepseek_key_concepts,
                        deepseek_practical_guidance, deepseek_related_rules,
                        deepseek_risk_points, deepseek_thinking_process, metadata
                    ) VALUES %s
                    """,
                    chunks_to_import
                )
                self.pg_conn.commit()
                self.stats["imported_chunks"] += len(chunks_to_import)

            self.stats["total_chunks"] += len(embedding_chunks)
            self.stats["skipped_chunks"] += skipped_count

            if chunks_to_import:
                self.stats["processed_files"] += 1
            else:
                self.stats["skipped_files"] += 1

            cursor.close()
            return True

        except Exception as e:
            logger.error(f"❌ 导入失败 {json_path.name}: {e}")
            self.pg_conn.rollback()
            self.stats["failed_files"] += 1
            return False

    def run(self) -> None:
        """运行导入流程"""
        self.stats["start_time"] = datetime.now()

        logger.info("=" * 80)
        logger.info("🚀 开始导入原始数据")
        logger.info("=" * 80)

        # 连接数据库
        self.connect_db()

        # 检查现有数据
        cursor = self.pg_conn.cursor()
        cursor.execute("SELECT COUNT(*), COUNT(DISTINCT document_id) FROM guideline_chunks")
        total_count, doc_count = cursor.fetchone()
        logger.info(f"📊 现有数据: {total_count} 条记录, {doc_count} 个文档")
        cursor.close()

        # 扫描原始JSON文件
        json_files = list(self.base_dir.glob("*.json"))
        self.stats["total_files"] = len(json_files)

        logger.info(f"📁 发现 {len(json_files)} 个原始JSON文件")

        # 批量处理文件
        batch_size = 50
        for i in range(0, len(json_files), batch_size):
            batch = json_files[i:i + batch_size]
            logger.info(f"📦 处理批次 {i // batch_size + 1}/{(len(json_files) + batch_size - 1) // batch_size}")

            for json_path in batch:
                self.import_file(json_path)

            # 显示进度
            progress = (i + len(batch)) / len(json_files) * 100
            logger.info("  批次完成")
            logger.info(f"📊 总进度: {min(progress, 100):.1f}%")
            logger.info(f"  新增记录: {self.stats['imported_chunks']}")
            logger.info(f"  跳过记录: {self.stats['skipped_chunks']}")

        # 最终统计
        cursor = self.pg_conn.cursor()
        cursor.execute("SELECT COUNT(*), COUNT(DISTINCT document_id) FROM guideline_chunks")
        final_total, final_docs = cursor.fetchone()
        cursor.close()

        logger.info("")
        logger.info("=" * 80)
        logger.info("📊 最终数据库状态")
        logger.info(f"  总记录数: {final_total}")
        logger.info(f"  总文档数: {final_docs}")
        logger.info("=" * 80)

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
        logger.info(f"  处理文件: {self.stats['processed_files']} (新增)")
        logger.info(f"  跳过文件: {self.stats['skipped_files']} (已存在)")
        logger.info(f"  失败文件: {self.stats['failed_files']}")
        logger.info(f"  总chunk数: {self.stats['total_chunks']}")
        logger.info(f"  新增chunk: {self.stats['imported_chunks']}")
        logger.info(f"  跳过chunk: {self.stats['skipped_chunks']} (已存在)")
        logger.info(f"  处理时间: {duration:.2f}秒 ({duration/60:.1f}分钟)")
        logger.info(f"  平均速度: {self.stats['total_chunks'] / duration if duration > 0 else 0:.2f} chunk/秒")
        logger.info("=" * 80)

        # 保存统计
        stats_file = log_dir / f"original_import_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
    importer = OriginalDataImporter()

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
