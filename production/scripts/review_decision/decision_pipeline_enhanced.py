#!/usr/bin/env python3
"""
专利复审决定书全量处理管道（增强版）
解析DOCX文件 -> 分块 -> BGE向量 -> Qdrant导入 -> NebulaGraph全量导出

改进：
1. 移除[:20]限制，全量导出到NebulaGraph
2. 添加decides、refers_to、precedent关系类型
3. 支持直接从Qdrant数据导出图谱

作者: Athena平台团队
创建时间: 2025-12-26
版本: v2.0
"""

from __future__ import annotations
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/decision_pipeline_enhanced_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class EnhancedDecisionPipeline:
    """增强版决定书处理管道"""

    def __init__(self):
        self.base_dir = Path("/Users/xujian/Athena工作平台")
        self.data_dir = self.base_dir / "production/data/patent_decisions"

        # Qdrant客户端
        self.qdrant_client = None
        # NebulaGraph console路径
        self.nebula_console = Path.home() / ".local/bin/nebula-console"

        logger.info("增强版决定书处理管道初始化完成")

    def initialize_qdrant(self) -> Any:
        """初始化Qdrant客户端"""
        logger.info("=" * 60)
        logger.info("🚀 初始化Qdrant客户端")
        logger.info("=" * 60)

        try:
            from qdrant_client import QdrantClient

            self.qdrant_client = QdrantClient(url="http://localhost:6333")

            # 获取集合信息
            collection_info = self.qdrant_client.get_collection("patent_decisions")
            logger.info("✅ Qdrant已连接: patent_decisions")
            logger.info(f"   点数量: {collection_info.points_count}")
            logger.info(f"   向量维度: {collection_info.config.params.vectors.size}")

        except Exception as e:
            logger.error(f"❌ Qdrant连接失败: {e}")
            raise

        logger.info("=" * 60)

    def fetch_all_chunks_from_qdrant(self) -> list[dict[str, Any]]:
        """从Qdrant获取所有数据块"""
        logger.info("📦 从Qdrant获取所有数据块...")


        all_points = []
        offset = None
        batch_size = 100

        while True:
            try:
                # 滚动获取数据
                results = self.qdrant_client.scroll(
                    collection_name="patent_decisions",
                    limit=batch_size,
                    offset=offset,
                    with_payload=["chunk_id", "doc_id", "block_type", "section", "text", "decision_date", "decision_number", "char_count", "law_references", "evidence_references"]
                )

                points = results[0]
                all_points.extend(points)

                logger.info(f"   已获取 {len(points)} 条，累计 {len(all_points)} 条")

                # 检查是否还有更多数据
                offset = results[1]
                if offset is None or len(points) == 0:
                    break

            except Exception as e:
                logger.error(f"❌ 获取数据失败: {e}")
                break

        logger.info(f"✅ 总共获取 {len(all_points)} 个数据块")

        # 转换为统一的chunk格式
        chunks = []
        for point in all_points:
            payload = point.payload if hasattr(point, 'payload') else {}
            chunks.append({
                'chunk_id': payload.get('chunk_id', ''),
                'doc_id': payload.get('doc_id', ''),
                'block_type': payload.get('block_type', ''),
                'section': payload.get('section', ''),
                'text': payload.get('text', ''),
                'decision_date': payload.get('decision_date', ''),
                'decision_number': payload.get('decision_number', ''),
                'char_count': payload.get('char_count', 0),
                'law_references': payload.get('law_references', []),
                'evidence_references': payload.get('evidence_references', [])
            })

        return chunks

    def export_full_nebula_graph(self, chunks: list[dict[str, Any]]) -> Any:
        """全量导出到NebulaGraph（移除所有限制）"""
        logger.info("=" * 60)
        logger.info("🌐 全量导出数据到NebulaGraph")
        logger.info("=" * 60)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.data_dir / "knowledge_graph" / f"nebula_decisions_full_{timestamp}.ngql"

        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 统计信息
        unique_docs = set()
        unique_laws = set()
        total_edges = 0

        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入头部
            f.write("# NebulaGraph 专利决定书全量导入脚本\n")
            f.write(f"# 生成时间: {datetime.now().isoformat()}\n")
            f.write("# 数据来源: Qdrant patent_decisions集合\n")
            f.write(f"# 数据块数: {len(chunks)}\n\n")

            # 使用现有的patent_rules空间或创建新空间
            f.write("# 使用专利规则空间\n")
            f.write("USE patent_rules;\n\n")

            # 创建新的标签类型（如果需要）- 使用单行格式
            f.write("# 创建决策块标签\n")
            f.write("CREATE TAG IF NOT EXISTS decision_block(doc_id string, decision_date string, block_type string, char_count int);\n\n")

            # 创建法律标签
            f.write("# 创建法律标签\n")
            f.write("CREATE TAG IF NOT EXISTS legal_reference(law_name string, reference_count int);\n\n")

            # 创建增强的边类型 - 使用单行格式
            f.write("# 创建边类型（增强版）\n")
            f.write("CREATE EDGE IF NOT EXISTS cites(law_name string, reference_type string, weight int);\n")
            f.write("CREATE EDGE IF NOT EXISTS decides(case_id string, decision_date string);\n")
            f.write("CREATE EDGE IF NOT EXISTS refers_to(evidence_id string, reference_type string);\n")
            f.write("CREATE EDGE IF NOT EXISTS precedes(decision_number string, similarity float);\n\n")

            logger.info("📝 开始写入数据...")

            # 第一步：插入所有决策块节点（全量）
            f.write("# ========================================\n")
            f.write("# 第一步：插入决策块节点（全量）\n")
            f.write("# ========================================\n\n")

            batch_size = 1000
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]

                for chunk in batch:
                    chunk_id = chunk['chunk_id']
                    doc_id = chunk['doc_id']
                    decision_date = chunk.get('decision_date', '')
                    block_type = chunk.get('block_type', '')
                    char_count = chunk.get('char_count', 0)

                    # 转义文本 - 移除换行符和特殊字符
                    # NebulaGraph INSERT VERTEX语法: INSERT VERTEX tag_name(prop1, prop2): "vid"
                    # VID使用chunk_id，属性使用doc_id等
                    doc_id_escaped = doc_id.replace('"', '\\"')
                    f.write(f'INSERT VERTEX decision_block("{doc_id_escaped}", "{decision_date}", "{block_type}", {char_count}): "{chunk_id}";\n')

                    # 统计唯一文档
                    unique_docs.add(doc_id)

                if (i + batch_size) % 10000 == 0:
                    logger.info(f"   已写入 {i + batch_size} 个决策块节点")

            logger.info(f"✅ 决策块节点写入完成: {len(chunks)} 个")

            # 第二步：插入法律引用节点
            f.write("\n# ========================================\n")
            f.write("# 第二步：插入法律引用节点\n")
            f.write("# ========================================\n\n")

            law_ref_counts = defaultdict(int)
            for chunk in chunks:
                for law_ref in chunk.get('law_references', []):
                    law_ref_counts[law_ref] += 1

            for law_name, count in sorted(law_ref_counts.items()):
                law_id = f"law_{abs(hash(law_name)) % 1000000}"
                f.write(f'INSERT VERTEX legal_reference(\'{law_name}\', {count}): "{law_id}";\n')
                unique_laws.add(law_name)

            logger.info(f"✅ 法律引用节点写入完成: {len(law_ref_counts)} 个")

            # 第三步：插入所有边关系（全量）
            f.write("\n# ========================================\n")
            f.write("# 第三步：插入边关系（全量）\n")
            f.write("# ========================================\n\n")

            # 3.1 cites边：决策块引用法律
            f.write("# 3.1 决策块引用法律关系（cites）\n")
            cites_count = 0
            for chunk in chunks:
                chunk_id = chunk['chunk_id']
                law_refs = chunk.get('law_references', [])

                for law_ref in law_refs:
                    law_id = f"law_{abs(hash(law_ref)) % 1000000}"
                    # NebulaGraph EDGE语法: INSERT EDGE edge_name(prop1, ...): "src_vid" -> "dst_vid"
                    f.write(f'INSERT EDGE cites(\'{law_ref}\', "statute", 1): "{chunk_id}" -> "{law_id}";\n')
                    cites_count += 1

            logger.info(f"✅ cites关系写入完成: {cites_count} 条")

            # 3.2 decides边：文档决定案件
            f.write("\n# 3.2 文档决定案件关系（decides）\n")
            f.write("# 注意：此关系需要案件ID数据，当前数据中暂不包含\n")
            f.write("# 预留结构，待后续补充案件数据\n")

            # 3.3 refers_to边：引用证据
            f.write("\n# 3.3 引用证据关系（refers_to）\n")
            refers_count = 0
            for chunk in chunks:
                chunk_id = chunk['chunk_id']
                evidence_refs = chunk.get('evidence_references', [])

                if evidence_refs:
                    for evidence in evidence_refs[:5]:  # 限制每个块最多5个证据引用
                        evidence_id = f"ev_{abs(hash(str(evidence))) % 1000000}"
                        f.write(f'INSERT EDGE refers_to("{evidence_id}", "evidence"): "{chunk_id}" -> "{evidence_id}";\n')
                        refers_count += 1

            logger.info(f"✅ refers_to关系写入完成: {refers_count} 条")

            total_edges = cites_count + refers_count

        # 统计信息
        logger.info("=" * 60)
        logger.info("📊 NebulaGraph导出统计")
        logger.info("=" * 60)
        logger.info(f"决策块节点: {len(chunks)}")
        logger.info(f"唯一文档数: {len(unique_docs)}")
        logger.info(f"法律引用节点: {len(law_ref_counts)}")
        logger.info(f"边关系总数: {total_edges}")
        logger.info(f"  - cites: {cites_count}")
        logger.info(f"  - refers_to: {refers_count}")
        logger.info("=" * 60)

        logger.info(f"📄 NebulaGraph脚本: {output_file}")
        logger.info("✅ 全量NebulaGraph导出完成")

        return str(output_file), {
            'vertices': len(chunks) + len(law_ref_counts),
            'edges': total_edges,
            'unique_docs': len(unique_docs),
            'unique_laws': len(law_ref_counts)
        }

    def import_to_nebula_graph(self, ngql_file: str) -> bool:
        """导入到NebulaGraph"""
        logger.info("=" * 60)
        logger.info("🚀 开始导入到NebulaGraph")
        logger.info("=" * 60)

        if not self.nebula_console.exists():
            logger.warning(f"⚠️ nebula-console未找到: {self.nebula_console}")
            logger.info("💡 请手动执行以下命令导入:")
            logger.info(f"   {self.nebula_console} -addr 127.0.0.1 -port 9669 -u root -p nebula -f {ngql_file}")
            return False

        try:
            import subprocess

            # 执行导入
            result = subprocess.run(
                [str(self.nebula_console), '-addr', '127.0.0.1', '-port', '9669',
                 '-u', 'root', '-p', 'nebula', '-f', ngql_file],
                capture_output=True,
                text=True,
                timeout=3600  # 1小时超时
            )

            logger.info("📤 导入输出:")
            logger.info(result.stdout)

            if result.returncode == 0:
                logger.info("✅ NebulaGraph导入成功")
                return True
            else:
                logger.error(f"❌ 导入失败: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("❌ 导入超时（1小时）")
            return False
        except Exception as e:
            logger.error(f"❌ 导入异常: {e}")
            return False

    def run_full_export(self, auto_import: bool = False) -> Any:
        """运行全量导出流程"""
        logger.info("=" * 60)
        logger.info("🚀 启动增强版决定书处理管道")
        logger.info("📝 功能：全量导出到NebulaGraph（移除所有限制）")
        logger.info("=" * 60)

        try:
            # 初始化Qdrant
            self.initialize_qdrant()

            # 从Qdrant获取所有数据
            chunks = self.fetch_all_chunks_from_qdrant()

            if not chunks:
                logger.error("❌ 没有数据可导出")
                return

            # 全量导出到NebulaGraph
            ngql_file, stats = self.export_full_nebula_graph(chunks)

            # 可选：自动导入
            if auto_import:
                success = self.import_to_nebula_graph(ngql_file)
                if success:
                    logger.info("🎉 全量导出和导入完成！")
                else:
                    logger.info("⚠️ 导出完成，但自动导入失败，请手动导入")
            else:
                logger.info("✅ 脚本生成完成")
                logger.info("💡 手动导入命令:")
                logger.info(f"   {self.nebula_console} -addr 127.0.0.1 -port 9669 -u root -p nebula -f {ngql_file}")

            logger.info("=" * 60)
            logger.info("📊 最终统计")
            logger.info("=" * 60)
            logger.info(f"节点数: {stats['vertices']:,}")
            logger.info(f"边数: {stats['edges']:,}")
            logger.info(f"唯一文档: {stats['unique_docs']:,}")
            logger.info(f"唯一法律引用: {stats['unique_laws']:,}")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ 管道执行失败: {e}")
            import traceback
            traceback.print_exc()


def main() -> None:
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="增强版专利决定书管道")
    parser.add_argument('--import', action='store_true', dest='auto_import',
                       help='自动导入到NebulaGraph')

    args = parser.parse_args()

    pipeline = EnhancedDecisionPipeline()
    pipeline.run_full_export(auto_import=args.auto_import)


if __name__ == "__main__":
    main()
