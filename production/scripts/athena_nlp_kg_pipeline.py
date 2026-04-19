#!/usr/bin/env python3
"""
Athena专利法律知识图谱完整构建管道
集成BGE向量生成、NLP实体关系提取、NebulaGraph知识图谱构建

作者: Athena平台团队
创建时间: 2025-12-23
"""

from __future__ import annotations
import asyncio
import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/nlp_kg_pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class AthenaNLPKnowledgeGraphPipeline:
    """Athena NLP知识图谱构建管道"""

    def __init__(self):
        self.bge_service = None
        self.entity_extractor = None
        self.relation_extractor = None
        self.nebula_client = None

        # 配置路径
        self.base_dir = Path("/Users/xujian/Athena工作平台")
        self.data_dir = self.base_dir / "production/data/patent_rules"
        self.legal_docs_dir = self.data_dir / "legal_documents"
        self.vectors_dir = self.data_dir / "vectors"
        self.kg_dir = self.data_dir / "knowledge_graph"

        # 确保目录存在
        for dir_path in [self.data_dir, self.legal_docs_dir, self.vectors_dir, self.kg_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        logger.info("🏗️ Athena NLP知识图谱管道初始化完成")

    async def initialize(self):
        """初始化所有组件"""
        logger.info("=" * 60)
        logger.info("🚀 初始化管道组件")
        logger.info("=" * 60)

        try:
            # 1. 初始化BGE嵌入服务
            logger.info("📦 初始化BGE嵌入服务...")
            from core.nlp.bge_embedding_service import BGEEmbeddingService

            model_path = self.base_dir / "models/converted/bge-large-zh-v1.5"
            if not model_path.exists():
                model_path = self.base_dir / "models/bge-large-zh-v1.5"

            bge_config = {
                "model_path": str(model_path),
                "device": "cpu",
                "batch_size": 32,
                "max_length": 512,
                "normalize_embeddings": True,
                "cache_enabled": True,
                "preload": True
            }

            self.bge_service = BGEEmbeddingService(bge_config)
            await self.bge_service.initialize()

            # 测试BGE服务
            health = await self.bge_service.health_check()
            logger.info(f"✅ BGE服务状态: {health['status']}, 向量维度: {health['dimension']}")

            # 2. 初始化实体提取器
            logger.info("🔍 初始化实体提取器...")
            from patent_legal_kg.core.nlp.entity_extractor import PatentLegalEntityExtractor

            extractor_config = {
                'quality_thresholds': {
                    'min_entity_confidence': 0.7,
                    'min_relation_confidence': 0.6
                },
                'nlp_models': {
                    'bert_model': 'ckiplab/bert-base-chinese-ner'
                }
            }

            self.entity_extractor = PatentLegalEntityExtractor(extractor_config)
            logger.info("✅ 实体提取器初始化完成")

            # 3. 初始化关系提取器
            logger.info("🔗 初始化关系提取器...")
            from patent_legal_kg.core.nlp.relation_extractor import PatentLegalRelationExtractor

            self.relation_extractor = PatentLegalRelationExtractor(extractor_config)
            logger.info("✅ 关系提取器初始化完成")

            # 4. 初始化NebulaGraph连接（延迟，在需要时）
            logger.info("🌐 NebulaGraph连接将在需要时初始化")

            logger.info("=" * 60)
            logger.info("✅ 所有组件初始化完成")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            traceback.print_exc()
            raise

    async def generate_bge_vectors(self, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        """为文本块生成BGE向量"""
        logger.info("=" * 60)
        logger.info(f"📊 开始生成BGE向量，共 {len(chunks)} 个文本块")
        logger.info("=" * 60)

        start_time = time.time()
        vectors_generated = 0
        failed_count = 0
        results = []

        batch_size = 32
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            texts = [chunk.get('text', '') for chunk in batch]

            try:
                # 批量编码
                result = await self.bge_service.encode(texts, task_type="patent_legal")

                # 处理结果
                for _j, (chunk, embedding) in enumerate(zip(batch, result.embeddings, strict=False)):
                    results.append({
                        'chunk_id': chunk.get('chunk_id'),
                        'text': chunk.get('text', '')[:100],  # 保存前100字符用于调试
                        'embedding_dim': len(embedding) if isinstance(embedding, list) else 1024,
                        'embedding_preview': list(embedding[:5]) if isinstance(embedding, list) else [],
                        'metadata': chunk.get('metadata', {})
                    })
                    vectors_generated += 1

                # 进度报告
                progress = (i + len(batch)) / len(chunks) * 100
                logger.info(f"✅ 进度: {i + len(batch)}/{len(chunks)} ({progress:.1f}%)")

            except Exception as e:
                logger.error(f"❌ 批次 {i//batch_size} 处理失败: {e}")
                failed_count += len(batch)

        elapsed_time = time.time() - start_time
        throughput = vectors_generated / elapsed_time if elapsed_time > 0 else 0

        logger.info("=" * 60)
        logger.info("📊 BGE向量生成完成")
        logger.info(f"   成功: {vectors_generated}")
        logger.info(f"   失败: {failed_count}")
        logger.info(f"   耗时: {elapsed_time:.2f}秒")
        logger.info(f"   速度: {throughput:.2f} 文本/秒")
        logger.info("=" * 60)

        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.vectors_dir / f"bge_vectors_{timestamp}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_chunks': len(chunks),
                'vectors_generated': vectors_generated,
                'failed_count': failed_count,
                'elapsed_time': elapsed_time,
                'throughput': throughput,
                'reports/reports/results': results[:100]  # 只保存前100个用于调试
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 向量结果已保存: {output_file}")

        return {
            'vectors_generated': vectors_generated,
            'failed_count': failed_count,
            'elapsed_time': elapsed_time,
            'throughput': throughput,
            'output_file': str(output_file)
        }

    async def extract_entities_and_relations(self, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        """提取实体和关系"""
        logger.info("=" * 60)
        logger.info(f"🔍 开始提取实体和关系，共 {len(chunks)} 个文本块")
        logger.info("=" * 60)

        start_time = time.time()
        all_entities = []
        all_relations = []

        for i, chunk in enumerate(chunks):
            text = chunk.get('text', '')
            if not text:
                continue

            try:
                # 提取实体
                entities = await self.entity_extractor.extract_entities(text)
                for entity in entities:
                    entity['chunk_id'] = chunk.get('chunk_id')
                    entity['source_text'] = text[:100]
                all_entities.extend(entities)

                # 提取关系
                relations = await self.relation_extractor.extract_relations(text, entities)
                for relation in relations:
                    relation['chunk_id'] = chunk.get('chunk_id')
                all_relations.extend(relations)

                # 进度报告
                if (i + 1) % 100 == 0:
                    logger.info(f"✅ 进度: {i+1}/{len(chunks)}, 实体: {len(all_entities)}, 关系: {len(all_relations)}")

            except Exception as e:
                logger.error(f"❌ 处理块 {chunk.get('chunk_id')} 失败: {e}")

        elapsed_time = time.time() - start_time

        logger.info("=" * 60)
        logger.info("🔍 实体和关系提取完成")
        logger.info(f"   实体数: {len(all_entities)}")
        logger.info(f"   关系数: {len(all_relations)}")
        logger.info(f"   耗时: {elapsed_time:.2f}秒")
        logger.info("=" * 60)

        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        entities_file = self.kg_dir / f"entities_{timestamp}.json"
        with open(entities_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_entities': len(all_entities),
                'entities': all_entities[:1000]  # 保存前1000个用于调试
            }, f, ensure_ascii=False, indent=2)

        relations_file = self.kg_dir / f"relations_{timestamp}.json"
        with open(relations_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_relations': len(all_relations),
                'relations': all_relations[:1000]  # 保存前1000个用于调试
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 实体已保存: {entities_file}")
        logger.info(f"📄 关系已保存: {relations_file}")

        return {
            'entities_count': len(all_entities),
            'relations_count': len(all_relations),
            'elapsed_time': elapsed_time,
            'entities_file': str(entities_file),
            'relations_file': str(relations_file)
        }

    async def build_knowledge_graph(self, entities: list[dict], relations: list[dict]) -> dict[str, Any]:
        """构建NebulaGraph知识图谱"""
        logger.info("=" * 60)
        logger.info("🌐 开始构建NebulaGraph知识图谱")
        logger.info("=" * 60)

        try:
            from config.nebula_graph_config import NebulaGraphConfig
            from nebula3.gclient.net import ConnectionPool

            # 获取配置
            config = NebulaGraphConfig.get_production_config()

            # 创建连接池
            connection_pool = ConnectionPool()
            await connection_pool.init(
                hosts=config.hosts,
                port=config.port,
                user_name=config.username,
                password=config.password,
                space_name=config.space_name
            )

            logger.info(f"✅ 连接到NebulaGraph: {config.space_name}")

            # 执行建图操作
            session = connection_pool.get_session()

            try:
                # 创建空间（如果不存在）
                create_space_result = session.execute(
                    f"CREATE SPACE IF NOT EXISTS {config.space_name} "
                    f"(partition_num={config.partition_num}, replica_factor={config.replica_factor}, "
                    f"vid_type=FIXED_STRING(32));"
                )
                logger.info(f"✅ 创建空间: {create_space_result}")

                # 使用空间
                time.sleep(2)  # 等待空间创建完成
                use_space_result = session.execute(f"USE {config.space_name};")
                logger.info(f"✅ 使用空间: {use_space_result}")

                # 创建标签（简化版）
                tags = ["Document", "Entity", "Concept", "Rule", "Article"]
                for tag in tags:
                    try:
                        session.execute(f"CREATE TAG IF NOT EXISTS {tag}(name string, content string);")
                        logger.info(f"✅ 创建标签: {tag}")
                    except Exception as e:
                        logger.warning(f"⚠️ 创建标签 {tag} 失败: {e}")

                # 创建边类型
                edges =["RELATES_TO", "REFERENCES", "DEFINES", "CONTAINS"]
                for edge in edges:
                    try:
                        session.execute(f"CREATE EDGE IF NOT EXISTS {edge}(weight double);")
                        logger.info(f"✅ 创建边: {edge}")
                    except Exception as e:
                        logger.warning(f"⚠️ 创建边 {edge} 失败: {e}")

                # 插入实体和关系（示例）
                inserted_entities = 0
                inserted_relations = 0

                # 这里简化处理，实际应该批量插入
                for i, entity in enumerate(entities[:100]):  # 只处理前100个作为示例
                    try:
                        entity_id = f"entity_{i}"
                        insert_result = session.execute(
                            f'INSERT VERTEX Entity("{entity_id}", "{entity.get("text", "")[:50]}", '
                            f'"{entity.get("text", "")[:100]}");'
                        )
                        inserted_entities += 1
                    except Exception as e:
                        logger.debug(f"插入实体失败: {e}")

                logger.info(f"📊 插入实体: {inserted_entities}")
                logger.info(f"📊 插入关系: {inserted_relations}")

            finally:
                session.release()

            logger.info("=" * 60)
            logger.info("✅ NebulaGraph知识图谱构建完成")
            logger.info("=" * 60)

            return {
                'success': True,
                'inserted_entities': inserted_entities,
                'inserted_relations': inserted_relations
            }

        except Exception as e:
            logger.error(f"❌ NebulaGraph构建失败: {e}")
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

    async def process_review_documents(self, review_dir: str, max_files: int = 100) -> dict[str, Any]:
        """处理复审决定文档"""
        logger.info("=" * 60)
        logger.info("📂 开始处理复审决定文档")
        logger.info(f"   目录: {review_dir}")
        logger.info(f"   最大文件数: {max_files}")
        logger.info("=" * 60)

        import glob

        # 查找所有txt文件
        pattern = os.path.join(review_dir, "**/*.txt")
        txt_files = glob.glob(pattern, recursive=True)

        total_files = len(txt_files)
        files_to_process = min(total_files, max_files)

        logger.info(f"📊 找到 {total_files} 个文件，将处理 {files_to_process} 个")

        processed_files = 0
        failed_files = 0
        chunks_created = 0

        for i, file_path in enumerate(txt_files[:max_files]):
            try:
                # 读取文件
                with open(file_path, encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # 简单分块（每段一个块）
                paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                chunks_created += len(paragraphs)

                processed_files += 1

                if (i + 1) % 10 == 0:
                    logger.info(f"✅ 进度: {i+1}/{files_to_process}")

            except Exception as e:
                logger.error(f"❌ 处理文件 {file_path} 失败: {e}")
                failed_files += 1

        logger.info("=" * 60)
        logger.info("📂 复审决定文档处理完成")
        logger.info(f"   处理文件: {processed_files}")
        logger.info(f"   失败文件: {failed_files}")
        logger.info(f"   生成块: {chunks_created}")
        logger.info("=" * 60)

        return {
            'total_files': total_files,
            'processed_files': processed_files,
            'failed_files': failed_files,
            'chunks_created': chunks_created
        }

    async def run_full_pipeline(self) -> dict[str, Any]:
        """运行完整管道"""
        logger.info("=" * 60)
        logger.info("🚀 启动Athena NLP知识图谱完整管道")
        logger.info("=" * 60)

        results = {}
        start_time = time.time()

        try:
            # 步骤1: 初始化
            await self.initialize()

            # 步骤2: 准备测试数据（如果没有真实数据）
            # 创建5,034个测试文本块
            logger.info("📝 准备测试文本块数据...")
            chunks = self._generate_test_chunks(5034)

            # 步骤3: 生成BGE向量
            vector_results = await self.generate_bge_vectors(chunks)
            results['vectors'] = vector_results

            # 步骤4: 提取实体和关系
            er_results = await self.extract_entities_and_relations(chunks[:100])  # 先处理100个测试
            results['entities_relations'] = er_results

            # 步骤5: 构建知识图谱（可选）
            # kg_results = await self.build_knowledge_graph([], [])
            # results['knowledge_graph'] = kg_results

            # 步骤6: 处理复审决定文档（可选）
            # review_dir = "/Users/xujian/Athena工作平台/_BACKUP_TO_EXTERNAL_DRIVE/logs_and_temp/external_storage/语料/专利/专利复审决定原文"
            # if os.path.exists(review_dir):
            #     review_results = await self.process_review_documents(review_dir, max_files=100)
            #     results['review_documents'] = review_results

            total_time = time.time() - start_time

            logger.info("=" * 60)
            logger.info("🎉 管道执行完成")
            logger.info(f"   总耗时: {total_time:.2f}秒")
            logger.info("=" * 60)

            # 保存最终报告
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.data_dir / f"pipeline_report_{timestamp}.json"

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'completed_at': datetime.now().isoformat(),
                    'total_time': total_time,
                    'reports/reports/results': results
                }, f, ensure_ascii=False, indent=2)

            logger.info(f"📄 最终报告已保存: {report_file}")

            return results

        except Exception as e:
            logger.error(f"❌ 管道执行失败: {e}")
            traceback.print_exc()
            raise

    def _generate_test_chunks(self, count: int) -> list[dict[str, Any]]:
        """生成测试文本块"""
        chunks = []
        sample_texts = [
            "专利法规定授予专利权的发明和实用新型，应当具备新颖性、创造性和实用性。",
            "新颖性是指该发明或者实用新型不属于现有技术。",
            "创造性是指与现有技术相比，该发明有突出的实质性特点和显著的进步。",
            "实用性是指该发明或者实用新型能够制造或者使用，并且能够产生积极效果。",
            "专利审查指南对专利申请的审查标准进行了详细规定。",
            "发明创造的新颖性、创造性和实用性是授予专利权的关键条件。",
            "专利权人享有实施其专利技术的独占权。",
            "专利权的保护范围以权利要求的内容为准。",
            "专利侵权行为包括制造、使用、许诺销售、销售、进口其专利产品。",
            "专利权的期限为发明专利二十年，实用新型专利十年，外观设计专利十五年。"
        ]

        for i in range(count):
            chunk = {
                'chunk_id': f"chunk_{i:06d}",
                'text': sample_texts[i % len(sample_texts)],
                'metadata': {
                    'index': i,
                    'source': 'test_data'
                }
            }
            chunks.append(chunk)

        logger.info(f"📝 生成了 {len(chunks)} 个测试文本块")
        return chunks


async def main():
    """主函数"""
    pipeline = AthenaNLPKnowledgeGraphPipeline()
    await pipeline.run_full_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
