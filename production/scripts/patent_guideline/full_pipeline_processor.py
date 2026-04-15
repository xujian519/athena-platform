#!/usr/bin/env python3
"""
专利审查指南全量处理管道
为396个小节生成BGE向量、提取实体关系、构建知识图谱

作者: Athena平台团队
创建时间: 2025-12-23
"""

from __future__ import annotations
import asyncio
import json
import logging
import sys
import time
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
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/full_pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class GuidelineFullPipeline:
    """专利审查指南全量处理管道"""

    def __init__(self):
        self.base_dir = Path("/Users/xujian/Athena工作平台")
        self.data_dir = self.base_dir / "production/data/patent_rules/legal_documents"
        self.output_dir = self.base_dir / "production/data/patent_rules"

        # BGE服务
        self.bge_service = None

        logger.info("全量处理管道初始化完成")

    async def initialize_bge_service(self):
        """初始化BGE服务"""
        logger.info("=" * 60)
        logger.info("🚀 初始化BGE嵌入服务")
        logger.info("=" * 60)

        try:
            from core.nlp.bge_embedding_service import BGEEmbeddingService

            model_path = self.base_dir / "models/converted/bge-large-zh-v1.5"
            if not model_path.exists():
                model_path = self.base_dir / "models/bge-large-zh-v1.5"

            config = {
                "model_path": str(model_path),
                "device": "cpu",
                "batch_size": 32,
                "max_length": 512,
                "normalize_embeddings": True,
                "cache_enabled": True,
                "preload": True
            }

            self.bge_service = BGEEmbeddingService(config)
            await self.bge_service.initialize()

            # 健康检查
            health = await self.bge_service.health_check()
            logger.info(f"✅ BGE服务状态: {health['status']}, 维度: {health['dimension']}")

            return True

        except Exception as e:
            logger.error(f"❌ BGE服务初始化失败: {e}")
            return False

    async def generate_vectors_for_subsections(self, chunks_data: list[dict[str, Any]]) -> dict[str, Any]:
        """为小节生成BGE向量"""
        logger.info("=" * 60)
        logger.info(f"📊 为 {len(chunks_data)} 个小节生成BGE向量")
        logger.info("=" * 60)

        start_time = time.time()
        results = []

        # 准备文本
        texts = [chunk['text'] for chunk in chunks_data]
        chunk_ids = [chunk['chunk_id'] for chunk in chunks_data]

        batch_size = 32
        total_batches = (len(texts) + batch_size - 1) // batch_size

        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(texts))

            batch_texts = texts[start_idx:end_idx]
            batch_ids = chunk_ids[start_idx:end_idx]

            try:
                # 编码
                result = await self.bge_service.encode(batch_texts, task_type="patent_guideline")

                # 处理结果
                for _i, (chunk_id, embedding) in enumerate(zip(batch_ids, result.embeddings, strict=False)):
                    results.append({
                        'chunk_id': chunk_id,
                        'embedding': embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding),
                        'dimension': len(embedding) if isinstance(embedding, list) else 1024
                    })

                # 进度
                progress = (batch_idx + 1) / total_batches * 100
                logger.info(f"✅ 批次 {batch_idx + 1}/{total_batches} ({progress:.1f}%)")

            except Exception as e:
                logger.error(f"❌ 批次 {batch_idx} 失败: {e}")

        elapsed_time = time.time() - start_time
        throughput = len(chunks_data) / elapsed_time if elapsed_time > 0 else 0

        logger.info("=" * 60)
        logger.info("📊 BGE向量生成完成")
        logger.info(f"   总数: {len(results)}")
        logger.info(f"   耗时: {elapsed_time:.2f}秒")
        logger.info(f"   速度: {throughput:.2f} 节/秒")
        logger.info("=" * 60)

        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / "vectors" / f"guideline_bge_vectors_{timestamp}.json"

        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_chunks': len(chunks_data),
                'vectors_generated': len(results),
                'elapsed_time': elapsed_time,
                'throughput': throughput,
                'vectors': results
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 向量已保存: {output_file}")

        return {
            'vectors_generated': len(results),
            'elapsed_time': elapsed_time,
            'throughput': throughput,
            'output_file': str(output_file)
        }

    def extract_entities_from_subsections(self, chunks_data: list[dict[str, Any]]) -> dict[str, Any]:
        """从小节中提取实体"""
        logger.info("=" * 60)
        logger.info(f"🔍 从 {len(chunks_data)} 个小节提取实体")
        logger.info("=" * 60)

        start_time = time.time()
        all_entities = []

        # 简化的实体提取规则
        entity_patterns = {
            '法律条款': [
                r'专利法第[一二三四五六七八九十百千万零\d]+条',
                r'实施细则第[一二三四五六七八九十百千万零\d]+条',
                r'审查指南第[一二三四五六七八九十百千万零\d]+条'
            ],
            '专利类型': [
                r'发明专利[申请]?',
                r'实用新型专利[申请]?',
                r'外观设计专利[申请]?'
            ],
            '审查概念': [
                r'新颖性',
                r'创造性',
                r'实用性',
                r'现有技术',
                r'优先权',
                r'抵触申请'
            ],
            '程序术语': [
                r'初步审查',
                r'实质审查',
                r'复审',
                r'无效宣告',
                r'补正'
            ]
        }

        import re

        for i, chunk in enumerate(chunks_data):
            text = chunk['text']
            chunk_id = chunk['chunk_id']

            entities = {
                'chunk_id': chunk_id,
                'entities': {}
            }

            for entity_type, patterns in entity_patterns.items():
                matches = []
                for pattern in patterns:
                    found = re.findall(pattern, text)
                    matches.extend(found)

                if matches:
                    entities['entities'][entity_type] = list(set(matches))

            if entities['entities']:
                all_entities.append(entities)

            if (i + 1) % 50 == 0:
                logger.info(f"✅ 进度: {i + 1}/{len(chunks_data)}")

        elapsed_time = time.time() - start_time

        logger.info("=" * 60)
        logger.info("🔍 实体提取完成")
        logger.info(f"   有实体的块: {len(all_entities)}")
        logger.info(f"   耗时: {elapsed_time:.2f}秒")
        logger.info("=" * 60)

        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / "knowledge_graph" / f"guideline_entities_{timestamp}.json"

        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'extracted_at': datetime.now().isoformat(),
                'total_chunks': len(chunks_data),
                'chunks_with_entities': len(all_entities),
                'elapsed_time': elapsed_time,
                'entities': all_entities
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 实体已保存: {output_file}")

        return {
            'entities_extracted': len(all_entities),
            'elapsed_time': elapsed_time,
            'output_file': str(output_file)
        }

    def build_knowledge_graph_structure(self, chunks_data: list[dict[str, Any]]) -> dict[str, Any]:
        """构建知识图谱结构"""
        logger.info("=" * 60)
        logger.info(f"🌐 为 {len(chunks_data)} 个小节构建知识图谱")
        logger.info("=" * 60)

        start_time = time.time()

        # 构建节点和边
        nodes = []
        edges = []

        # 部分节点
        parts = set()
        chapters = set()
        sections = set()

        for chunk in chunks_data:
            metadata = chunk.get('metadata', {})

            if metadata.get('part'):
                parts.add(metadata['part'])
            if metadata.get('chapter'):
                chapters.add(metadata['chapter'])
            if metadata.get('section'):
                sections.add(metadata['section'])

        # 创建节点
        for part in parts:
            nodes.append({
                'node_id': f"part_{hash(part)}",
                'node_type': 'Part',
                'name': part
            })

        for chapter in chapters:
            nodes.append({
                'node_id': f"chapter_{hash(chapter)}",
                'node_type': 'Chapter',
                'name': chapter
            })

        for section in sections:
            nodes.append({
                'node_id': f"section_{hash(section)}",
                'node_type': 'Section',
                'name': section
            })

        # 创建小节节点
        for chunk in chunks_data:
            metadata = chunk.get('metadata', {})
            nodes.append({
                'node_id': chunk['chunk_id'],
                'node_type': 'Subsection',
                'name': metadata.get('title', ''),
                'full_path': metadata.get('full_path', ''),
                'word_count': metadata.get('word_count', 0)
            })

        elapsed_time = time.time() - start_time

        logger.info("=" * 60)
        logger.info("🌐 知识图谱构建完成")
        logger.info(f"   节点数: {len(nodes)}")
        logger.info(f"   耗时: {elapsed_time:.2f}秒")
        logger.info("=" * 60)

        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / "knowledge_graph" / f"guideline_kg_structure_{timestamp}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'created_at': datetime.now().isoformat(),
                'total_nodes': len(nodes),
                'node_types': {
                    'Part': len(parts),
                    'Chapter': len(chapters),
                    'Section': len(sections),
                    'Subsection': len(chunks_data)
                },
                'nodes': nodes,
                'edges': edges
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 知识图谱已保存: {output_file}")

        return {
            'total_nodes': len(nodes),
            'elapsed_time': elapsed_time,
            'output_file': str(output_file)
        }

    async def run_full_pipeline(self):
        """运行全量处理管道"""
        logger.info("=" * 60)
        logger.info("🚀 启动专利审查指南全量处理管道")
        logger.info("=" * 60)

        results = {}
        start_time = time.time()

        try:
            # 1. 初始化BGE服务
            if not await self.initialize_bge_service():
                logger.error("BGE服务初始化失败，终止处理")
                return {'error': 'BGE服务初始化失败'}

            # 2. 加载小节数据
            vector_input_file = self.data_dir / "guideline_vectors_input_20251223_003233.json"

            if not vector_input_file.exists():
                logger.error(f"找不到小节数据文件: {vector_input_file}")
                return {'error': '小节数据文件不存在'}

            with open(vector_input_file, encoding='utf-8') as f:
                data = json.load(f)

            chunks_data = data.get('chunks', [])
            logger.info(f"📦 加载了 {len(chunks_data)} 个小节")

            # 3. 生成BGE向量
            vector_results = await self.generate_vectors_for_subsections(chunks_data)
            results['vectors'] = vector_results

            # 4. 提取实体
            entity_results = self.extract_entities_from_subsections(chunks_data)
            results['entities'] = entity_results

            # 5. 构建知识图谱
            kg_results = self.build_knowledge_graph_structure(chunks_data)
            results['knowledge_graph'] = kg_results

            total_time = time.time() - start_time

            # 6. 生成最终报告
            report = {
                'completed_at': datetime.now().isoformat(),
                'total_time': total_time,
                'pipeline_results': results,
                'summary': {
                    'total_subsections': len(chunks_data),
                    'vectors_generated': results['vectors']['vectors_generated'],
                    'entities_extracted': results['entities']['entities_extracted'],
                    'kg_nodes_created': results['knowledge_graph']['total_nodes']
                }
            }

            # 保存报告
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.output_dir / f"full_pipeline_report_{timestamp}.json"

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            logger.info("=" * 60)
            logger.info("🎉 全量处理完成！")
            logger.info(f"📊 总耗时: {total_time:.2f}秒")
            logger.info(f"📄 报告: {report_file}")
            logger.info("=" * 60)

            return report

        except Exception as e:
            logger.error(f"❌ 管道执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}


async def main():
    """主函数"""
    pipeline = GuidelineFullPipeline()
    await pipeline.run_full_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
