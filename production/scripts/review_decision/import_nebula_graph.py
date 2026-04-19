#!/usr/bin/env python3
"""
直接使用Python客户端导入NebulaGraph
避免console解析问题

作者: 小诺·双鱼公主
创建时间: 2025-12-26
"""

from __future__ import annotations
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from nebula3.Config import Config

# NebulaGraph Python客户端
from nebula3.gclient.net import ConnectionPool

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/import_nebula_graph_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class NebulaGraphImporter:
    """NebulaGraph导入器"""

    def __init__(self):
        self.space_name = "patent_rules"
        self.connection_pool = None
        self.session = None

    def connect(self) -> Any:
        """连接到NebulaGraph"""
        logger.info("🔗 连接到NebulaGraph...")

        config = Config()
        config.max_connection_pool_size = 10

        # 连接配置
        hosts = [("127.0.0.1", 9669)]
        self.connection_pool = ConnectionPool()
        self.connection_pool.init(hosts, config)

        # 获取session
        self.session = self.connection_pool.get_session('root', 'nebula')
        logger.info("✅ NebulaGraph连接成功")

    def create_schema(self) -> Any:
        """创建TAG和EDGE类型"""
        logger.info("📝 创建Schema...")

        # 使用空间
        result = self.session.execute(f'USE {self.space_name};')
        logger.info(f"使用空间: {self.space_name}")

        # 创建TAG
        statements = [
            # 创建决策块TAG
            "CREATE TAG IF NOT EXISTS decision_block(doc_id string, decision_date string, block_type string, char_count int);",
            # 创建法律引用TAG
            "CREATE TAG IF NOT EXISTS legal_reference(law_name string, reference_count int);",
            # 创建边类型
            "CREATE EDGE IF NOT EXISTS cites(law_name string, reference_type string, weight int);",
            "CREATE EDGE IF NOT EXISTS decides(case_id string, decision_date string);",
            "CREATE EDGE IF NOT EXISTS refers_to(evidence_id string, reference_type string);",
            "CREATE EDGE IF NOT EXISTS precedes(decision_number string, similarity float);"
        ]

        for stmt in statements:
            result = self.session.execute(stmt)
            if not result.is_succeeded():
                logger.warning(f"警告: {result.error_msg()}")
            else:
                logger.info("✅ 执行成功")

    def import_decision_blocks(self, chunks) -> None:
        """导入决策块节点"""
        logger.info("=" * 60)
        logger.info("📦 开始导入决策块节点")
        logger.info("=" * 60)

        # 使用nGQL批量插入
        # 格式: INSERT VERTEX decision_block(prop1, prop2): "vid1", "vid2"
        batch_size = 100
        imported = 0

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            vertex_values = []

            for chunk in batch:
                chunk_id = chunk['chunk_id']
                doc_id = chunk.get('doc_id', '').replace('"', '\\"').replace("'", "\\'")
                decision_date = chunk.get('decision_date', '')
                block_type = chunk.get('block_type', '')
                char_count = chunk.get('char_count', 0)

                # 构建属性字符串
                props = f'"{doc_id}", "{decision_date}", "{block_type}", {char_count}'
                vertex_values.append(f'{props}: "{chunk_id}"')

            # 构建批量插入语句
            if vertex_values:
                stmt = f'INSERT VERTEX decision_block({", ".join(["doc_id", "decision_date", "block_type", "char_count"])}) ' + \
                       ', '.join([f'"{vid}"' for vid in [c['chunk_id'] for c in batch]]) + ' ' + \
                       'VALUES ' + ', '.join(vertex_values) + ';'

                result = self.session.execute(stmt)
                if result.is_succeeded():
                    imported += len(batch)
                    if imported % 10000 == 0:
                        logger.info(f"  已导入 {imported}/{len(chunks)}")
                else:
                    logger.error(f"  批次 {i//batch_size} 失败: {result.error_msg()}")

        logger.info(f"✅ 决策块节点导入完成: {imported} 个")

    def import_legal_references(self, chunks) -> None:
        """导入法律引用节点"""
        logger.info("=" * 60)
        logger.info("📚 开始导入法律引用节点")
        logger.info("=" * 60)

        from collections import defaultdict
        law_ref_counts = defaultdict(int)

        for chunk in chunks:
            for law_ref in chunk.get('law_references', []):
                law_ref_counts[law_ref] += 1

        logger.info(f"  发现 {len(law_ref_counts)} 个唯一法律引用")

        # 批量插入
        batch_size = 50
        imported = 0

        law_items = list(law_ref_counts.items())
        for i in range(0, len(law_items), batch_size):
            batch = law_items[i:i+batch_size]

            for law_name, count in batch:
                law_id = f"law_{abs(hash(law_name)) % 1000000}"
                law_name_escaped = law_name.replace('"', '\\"').replace("'", "\\'")
                stmt = f'INSERT VERTEX legal_reference(\'{law_name_escaped}\', {count}): "{law_id}";'

                result = self.session.execute(stmt)
                if result.is_succeeded():
                    imported += 1
                else:
                    logger.error(f"  导入法律 {law_name[:30]}... 失败: {result.error_msg()}")

        logger.info(f"✅ 法律引用节点导入完成: {imported} 个")
        return law_ref_counts

    def import_cites_edges(self, chunks, law_ref_counts) -> None:
        """导入cites边关系"""
        logger.info("=" * 60)
        logger.info("🔗 开始导入cites边关系")
        logger.info("=" * 60)

        imported = 0
        batch_size = 100

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]

            for chunk in batch:
                chunk_id = chunk['chunk_id']
                law_refs = chunk.get('law_references', [])

                for law_ref in law_refs:
                    law_id = f"law_{abs(hash(law_ref)) % 1000000}"
                    law_ref_escaped = law_ref.replace('"', '\\"').replace("'", "\\'")

                    stmt = f'INSERT EDGE cites(\'{law_ref_escaped}\', "statute", 1): "{chunk_id}" -> "{law_id}";'
                    result = self.session.execute(stmt)

                    if result.is_succeeded():
                        imported += 1
                    else:
                        logger.error(f"  导入边失败: {result.error_msg()}")

            if (i + batch_size) % 10000 == 0:
                logger.info(f"  已处理 {i + batch_size}/{len(chunks)}")

        logger.info(f"✅ cites边导入完成: {imported} 条")

    def run_import(self) -> Any:
        """运行导入流程"""
        logger.info("=" * 60)
        logger.info("🚀 启动NebulaGraph导入器")
        logger.info("=" * 60)

        try:
            # 连接
            self.connect()

            # 创建Schema
            self.create_schema()

            # 加载数据（从Qdrant导出的JSON）
            logger.info("📦 加载数据...")
            data_file = Path("/Users/xujian/Athena工作平台/production/data/patent_decisions/knowledge_graph/nebula_decisions_full_20251226_005737.ngql")
            # 这里直接从Qdrant获取数据会更简单，但为了复用已有的逻辑，我们直接读取chunks

            # 简化：直接从Qdrant获取
            logger.info("📦 从Qdrant获取数据...")
            from qdrant_client import QdrantClient

            qdrant_client = QdrantClient(url="http://localhost:6333")

            all_points = []
            offset = None
            batch_size = 100

            while True:
                results = qdrant_client.scroll(
                    collection_name="patent_decisions",
                    limit=batch_size,
                    offset=offset,
                    with_payload=["chunk_id", "doc_id", "block_type", "decision_date", "char_count", "law_references"]
                )

                points = results[0]
                all_points.extend(points)

                logger.info(f"  已获取 {len(points)} 条，累计 {len(all_points)} 条")

                offset = results[1]
                if offset is None or len(points) == 0:
                    break

            # 转换为chunk格式
            chunks = []
            for point in all_points:
                payload = point.payload if hasattr(point, 'payload') else {}
                chunks.append({
                    'chunk_id': payload.get('chunk_id', ''),
                    'doc_id': payload.get('doc_id', ''),
                    'block_type': payload.get('block_type', ''),
                    'decision_date': payload.get('decision_date', ''),
                    'char_count': payload.get('char_count', 0),
                    'law_references': payload.get('law_references', [])
                })

            logger.info(f"✅ 总共获取 {len(chunks)} 个数据块")

            # 导入决策块
            self.import_decision_blocks(chunks)

            # 导入法律引用
            law_ref_counts = self.import_legal_references(chunks)

            # 导入边关系
            self.import_cites_edges(chunks, law_ref_counts)

            logger.info("=" * 60)
            logger.info("🎉 导入完成！")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ 导入失败: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # 清理
            if self.session:
                self.session.release()
            if self.connection_pool:
                self.connection_pool.close()


def main() -> None:
    """主函数"""
    importer = NebulaGraphImporter()
    importer.run_import()


if __name__ == "__main__":
    main()
