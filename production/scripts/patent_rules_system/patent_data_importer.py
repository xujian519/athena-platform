#!/usr/bin/env python3
"""
专利规则高质量数据导入器
从移动硬盘备份数据导入专利法规，构建最高质量向量库和知识图谱

作者: Athena平台团队
创建时间: 2025-12-20
版本: v3.0.0 - 顶级质量版本
"""

from __future__ import annotations
import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / "patent_rules_system"))

from dynamic_prompt_generator import DynamicPromptGenerator
from patent_entity_extractor_pro import PatentEntityExtractorPro
from patent_rules_builder_enhanced import PatentRulesBuilderEnhanced
from qdrant_vector_store_simple import QdrantVectorStoreSimple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ImportMetrics:
    """导入指标"""
    total_documents: int = 0
    processed_documents: int = 0
    total_chunks: int = 0
    successful_embeddings: int = 0
    failed_embeddings: int = 0
    duplicate_chunks: int = 0
    total_entities: int = 0
    total_relations: int = 0
    processing_time: float = 0.0
    quality_score: float = 0.0

class PatentDataImporter:
    """专利数据高质量导入器"""

    def __init__(self):
        self.vector_store = QdrantVectorStoreSimple()
        self.entity_extractor = PatentEntityExtractorPro()
        self.prompt_generator = DynamicPromptGenerator()
        self.document_processor = PatentRulesBuilderEnhanced()
        self.metrics = ImportMetrics()

        # 质量阈值
        self.min_chunk_length = 50
        self.max_chunk_length = 2000
        self.min_entity_confidence = 0.7
        self.duplicate_threshold = 0.95

        # 数据源路径
        self.patent_docs_path = Path("/Volumes/AthenaData/语料/专利/专利法律法规")
        self.backup_data_path = Path("/Volumes/AthenaData/backup_legal_data/backup_20251220_215415")

    async def initialize_import_environment(self):
        """初始化导入环境"""
        logger.info("="*80)
        logger.info("🚀 初始化专利规则高质量导入环境")
        logger.info("="*80)

        # 检查NLP服务
        logger.info("📡 检查本地NLP服务状态...")
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8001/health", timeout=5) as response:
                    if response.status == 200:
                        health = await response.json()
                        logger.info(f"✅ NLP服务正常: {health}")
                    else:
                        logger.error("❌ NLP服务异常")
                        return False
        except Exception as e:
            logger.error(f"❌ 无法连接NLP服务: {str(e)}")
            logger.info("💡 请确保本地NLP服务在端口8001运行")
            return False

        # 初始化向量库
        logger.info("🗄️ 初始化向量数据库...")
        try:
            collection_info = await self.vector_store.get_collection_stats()
            logger.info(f"✅ 向量库已就绪: {collection_info}")
        except Exception as e:
            logger.error(f"❌ 向量库初始化失败: {str(e)}")
            return False

        # 检查数据源
        logger.info("📁 检查数据源...")
        if not self.patent_docs_path.exists():
            logger.error(f"❌ 专利文档路径不存在: {self.patent_docs_path}")
            return False

        doc_files = list(self.patent_docs_path.glob("*"))
        logger.info(f"✅ 发现 {len(doc_files)} 个专利文档文件")

        # 检查备份数据
        if self.backup_data_path.exists():
            logger.info("💾 发现备份数据，准备合并导入")
        else:
            logger.info("📝 未发现备份数据，将全新构建")

        logger.info("✅ 导入环境初始化完成")
        return True

    def _calculate_content_hash(self, content: str) -> str:
        """计算内容哈希用于去重"""
        return short_hash(content.encode('utf-8'))

    async def _check_duplicate_content(self, content: str) -> bool:
        """检查是否重复内容"""
        content_hash = self._calculate_content_hash(content)

        # 简化的重复检查，实际应该查询向量库
        # 这里先实现基础版本
        return False

    async def _process_document_with_quality(self, file_path: Path) -> list[dict[str, Any]]:
        """高质量处理单个文档"""
        logger.info(f"📖 处理文档: {file_path.name}")

        try:
            # 处理文档
            # PatentRulesBuilderEnhanced期望的参数格式是Dict[str, Any]
            doc_info = {
                'path': file_path,
                'name': file_path.name,
                'type': file_path.suffix,
                'format': file_path.suffix,  # 添加format字段
                'size': file_path.stat().st_size,  # 添加size字段
                'file_type': file_path.suffix,
                'file_name': file_path.name
            }

            vector_docs = await self.document_processor.process_document(doc_info)
            if not vector_docs:
                logger.warning(f"⚠️ 文档处理失败，跳过: {file_path.name}")
                return []

            # 提取文本片段
            chunks = [doc.content for doc in vector_docs]

            quality_chunks = []
            for i, chunk in enumerate(chunks):
                # 质量检查
                if len(chunk) < self.min_chunk_length:
                    continue
                if len(chunk) > self.max_chunk_length:
                    # 继续分割大块
                    sub_chunks = await self.document_processor._split_large_chunk(chunk)
                    chunks.extend(sub_chunks)
                    continue

                # 检查重复
                if await self._check_duplicate_content(chunk):
                    self.metrics.duplicate_chunks += 1
                    continue

                # 从原始VectorDocument获取元数据
                original_metadata = vector_docs[i].metadata if i < len(vector_docs) else {}

                # 生成增强元数据
                chunk_metadata = {
                    **original_metadata,
                    'source_file': str(file_path),
                    'file_name': file_path.name,
                    'file_type': file_path.suffix,
                    'chunk_index': i,
                    'chunk_length': len(chunk),
                    'created_at': datetime.now().isoformat(),
                    'quality_score': min(1.0, len(chunk) / 500),  # 基于长度的质量分数
                    'document_type': self._classify_document_type(file_path.name),
                    'processing_version': 'v3.0.0'
                }

                quality_chunks.append({
                    'content': chunk,
                    'metadata': chunk_metadata
                })

            logger.info(f"✅ 文档处理完成: {len(quality_chunks)} 个高质量片段")
            return quality_chunks

        except Exception as e:
            logger.error(f"❌ 文档处理失败 {file_path.name}: {str(e)}")
            return []

    def _classify_document_type(self, filename: str) -> str:
        """分类文档类型"""
        filename_lower = filename.lower()

        if '专利法' in filename_lower:
            return 'PATENT_LAW'
        elif '实施细则' in filename_lower:
            return 'IMPLEMENTATION_RULES'
        elif '审查指南' in filename_lower:
            return 'EXAMINATION_GUIDE'
        elif '最高人民法院' in filename_lower:
            return 'SUPREME_PEOPLE_COURT'
        elif '条例' in filename_lower:
            return 'REGULATION'
        elif '解释' in filename_lower:
            return 'JUDICIAL_INTERPRETATION'
        else:
            return 'OTHER_LEGAL_DOCUMENT'

    async def _generate_embeddings_with_quality(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """高质量生成嵌入向量"""
        logger.info(f"🧠 开始生成 {len(chunks)} 个片段的1024维嵌入向量...")

        successful_chunks = []

        # 使用本地NLP服务
        import aiohttp

        batch_size = 5  # 降低批次大小以确保质量
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]

            try:
                async with aiohttp.ClientSession() as session:
                    # 准备请求
                    texts = [chunk['content'] for chunk in batch]

                    # 调用本地NLP服务
                    async with session.post(
                        "http://localhost:8001/embed",
                        json={"texts": texts, "model": "legal_bert"},
                        timeout=30
                    ) as response:

                        if response.status == 200:
                            result = await response.json()

                            if result.get('success') and 'embeddings' in result:
                                embeddings = result['embeddings']

                                # 验证维度
                                if len(embeddings[0]) != 1024:
                                    logger.error(f"❌ 嵌入维度错误: 期望1024, 实际{len(embeddings[0])}")
                                    continue

                                # 合并数据和嵌入
                                for chunk, embedding in zip(batch, embeddings, strict=False):
                                    chunk_with_embedding = chunk.copy()
                                    chunk_with_embedding['embedding'] = embedding
                                    successful_chunks.append(chunk_with_embedding)

                                    self.metrics.successful_embeddings += 1

                                logger.info(f"✅ 批次 {i//batch_size + 1} 处理成功")
                            else:
                                logger.error(f"❌ 嵌入生成失败: {result.get('error', '未知错误')}")
                                self.metrics.failed_embeddings += len(batch)
                        else:
                            logger.error(f"❌ NLP服务错误: HTTP {response.status}")
                            self.metrics.failed_embeddings += len(batch)

                # 短暂延迟避免过载
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"❌ 批次处理失败: {str(e)}")
                self.metrics.failed_embeddings += len(batch)

        logger.info(f"🎯 嵌入生成完成: {len(successful_chunks)} 成功, {self.metrics.failed_embeddings} 失败")
        return successful_chunks

    async def _extract_entities_and_relations(self, chunks: list[dict[str, Any]]) -> tuple[list[dict], list[dict]]:
        """提取实体和关系"""
        logger.info("🕸️ 开始提取实体和关系...")

        all_entities = []
        all_relations = []

        for i, chunk in enumerate(chunks):
            if i % 10 == 0:
                logger.info(f"  处理进度: {i+1}/{len(chunks)}")

            content = chunk['content']
            metadata = chunk['metadata']

            # 提取实体
            entities = self.entity_extractor.extract_patent_entities(content, metadata.get('source_file', ''))

            # 过滤低质量实体
            quality_entities = [
                entity for entity in entities
                if entity.get('confidence', 0) >= self.min_entity_confidence
            ]

            # 增强实体信息
            for entity in quality_entities:
                entity.update({
                    'source_chunk': metadata.get('chunk_index'),
                    'source_file': metadata.get('file_name'),
                    'document_type': metadata.get('document_type'),
                    'created_at': datetime.now().isoformat()
                })

            # 提取关系
            relations = self.entity_extractor.extract_relations(content, quality_entities, metadata.get('source_file', ''))

            all_entities.extend(quality_entities)
            all_relations.extend(relations)

        # 去重实体
        unique_entities = self._deduplicate_entities(all_entities)
        unique_relations = self._deduplicate_relations(all_relations)

        logger.info(f"✅ 实体关系提取完成: {len(unique_entities)} 实体, {len(unique_relations)} 关系")
        return unique_entities, unique_relations

    def _deduplicate_entities(self, entities: list[dict]) -> list[dict]:
        """去重实体"""
        seen = set()
        unique_entities = []

        for entity in entities:
            key = (entity['text'], entity['type'])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)

        return unique_entities

    def _deduplicate_relations(self, relations: list[dict]) -> list[dict]:
        """去重关系"""
        seen = set()
        unique_relations = []

        for relation in relations:
            key = (relation['subject'], relation['relation'], relation['object'])
            if key not in seen:
                seen.add(key)
                unique_relations.append(relation)

        return unique_relations

    async def import_patent_documents(self):
        """导入专利文档"""
        logger.info("="*80)
        logger.info("📚 开始导入专利文档")
        logger.info("="*80)

        start_time = datetime.now()

        # 获取所有文档文件
        doc_files = []
        for ext in ['*.md', '*.docx', '*.pdf', '*.txt']:
            doc_files.extend(self.patent_docs_path.glob(ext))

        self.metrics.total_documents = len(doc_files)
        logger.info(f"📄 发现 {len(doc_files)} 个文档文件")

        # 处理所有文档
        all_chunks = []
        for file_path in doc_files:
            self.metrics.processed_documents += 1

            chunks = await self._process_document_with_quality(file_path)
            all_chunks.extend(chunks)

            logger.info(f"📊 当前进度: {self.metrics.processed_documents}/{self.metrics.total_documents}")

        self.metrics.total_chunks = len(all_chunks)
        logger.info(f"📝 总共生成 {len(all_chunks)} 个高质量片段")

        # 生成嵌入向量
        chunks_with_embeddings = await self._generate_embeddings_with_quality(all_chunks)

        # 导入向量库
        logger.info("🗄️ 导入向量数据库...")
        for i, chunk in enumerate(chunks_with_embeddings):
            try:
                await self.vector_store.store_document(
                    content=chunk['content'],
                    doc_type=chunk['metadata']['document_type'],
                    metadata=chunk['metadata'],
                    embedding=chunk['embedding']
                )

                if (i + 1) % 10 == 0:
                    logger.info(f"  向量导入进度: {i+1}/{len(chunks_with_embeddings)}")

            except Exception as e:
                logger.error(f"❌ 向量存储失败: {str(e)}")

        # 提取实体和关系
        entities, relations = await self._extract_entities_and_relations(chunks_with_embeddings)

        self.metrics.total_entities = len(entities)
        self.metrics.total_relations = len(relations)

        # 保存知识图谱
        await self._save_knowledge_graph(entities, relations)

        # 计算处理时间
        end_time = datetime.now()
        self.metrics.processing_time = (end_time - start_time).total_seconds()

        # 计算质量分数
        self.metrics.quality_score = self._calculate_quality_score()

        logger.info("✅ 专利文档导入完成")

    async def _save_knowledge_graph(self, entities: list[dict], relations: list[dict]):
        """保存知识图谱数据"""
        logger.info("💾 保存知识图谱数据...")

        kg_path = Path("/Users/xujian/Athena工作平台/production/data/patent_rules/knowledge_graph")
        kg_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 按类型分组实体
        entities_by_type = {}
        for entity in entities:
            entity_type = entity['type']
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)

        # 保存实体
        for entity_type, type_entities in entities_by_type.items():
            entity_file = kg_path / f"entities_{entity_type}_{timestamp}.json"
            with open(entity_file, 'w', encoding='utf-8') as f:
                json.dump(type_entities, f, ensure_ascii=False, indent=2)

        # 按类型分组关系
        relations_by_type = {}
        for relation in relations:
            relation_type = relation['relation']
            if relation_type not in relations_by_type:
                relations_by_type[relation_type] = []
            relations_by_type[relation_type].append(relation)

        # 保存关系
        for relation_type, type_relations in relations_by_type.items():
            relation_file = kg_path / f"relations_{relation_type}_{timestamp}.json"
            with open(relation_file, 'w', encoding='utf-8') as f:
                json.dump(type_relations, f, ensure_ascii=False, indent=2)

        # 保存统计信息
        stats = {
            'timestamp': timestamp,
            'source': 'patent_documents_import',
            'entities': {k: len(v) for k, v in entities_by_type.items()},
            'relations': {k: len(v) for k, v in relations_by_type.items()},
            'total_entities': len(entities),
            'total_relations': len(relations),
            'quality_metrics': {
                'min_entity_confidence': self.min_entity_confidence,
                'duplicate_threshold': self.duplicate_threshold,
                'processing_version': 'v3.0.0'
            }
        }

        stats_file = kg_path / f"import_stats_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 知识图谱已保存到: {kg_path}")

    def _calculate_quality_score(self) -> float:
        """计算质量分数"""
        if self.metrics.total_chunks == 0:
            return 0.0

        success_rate = self.metrics.successful_embeddings / self.metrics.total_chunks
        entity_rate = min(1.0, self.metrics.total_entities / self.metrics.total_chunks)
        duplicate_penalty = min(0.1, self.metrics.duplicate_chunks / self.metrics.total_chunks)

        quality_score = (success_rate * 0.5 + entity_rate * 0.4 - duplicate_penalty) * 100
        return max(0.0, min(100.0, quality_score))

    def generate_import_report(self) -> Any:
        """生成导入报告"""
        logger.info("="*80)
        logger.info("📊 专利规则导入报告")
        logger.info("="*80)

        logger.info("📄 文档处理:")
        logger.info(f"  - 总文档数: {self.metrics.total_documents}")
        logger.info(f"  - 处理成功: {self.metrics.processed_documents}")
        logger.info(f"  - 成功率: {self.metrics.processed_documents/self.metrics.total_documents*100:.1f}%")

        logger.info("📝 内容分块:")
        logger.info(f"  - 总片段数: {self.metrics.total_chunks}")
        logger.info(f"  - 成功嵌入: {self.metrics.successful_embeddings}")
        logger.info(f"  - 失败嵌入: {self.metrics.failed_embeddings}")
        logger.info(f"  - 重复片段: {self.metrics.duplicate_chunks}")
        logger.info(f"  - 嵌入成功率: {self.metrics.successful_embeddings/self.metrics.total_chunks*100:.1f}%" if self.metrics.total_chunks > 0 else "  - 嵌入成功率: N/A")

        logger.info("🕸️ 知识图谱:")
        logger.info(f"  - 实体总数: {self.metrics.total_entities}")
        logger.info(f"  - 关系总数: {self.metrics.total_relations}")

        logger.info("⏱️ 性能指标:")
        logger.info(f"  - 总处理时间: {self.metrics.processing_time:.1f}秒")
        logger.info(f"  - 平均每文档: {self.metrics.processing_time/max(1, self.metrics.processed_documents):.1f}秒")
        logger.info(f"  - 处理速度: {self.metrics.total_chunks/max(1, self.metrics.processing_time):.1f} 片段/秒")

        logger.info(f"🎯 质量评分: {self.metrics.quality_score:.1f}/100")

        # 保存报告
        report = {
            'import_time': datetime.now().isoformat(),
            'metrics': self.metrics.__dict__,
            'quality_settings': {
                'min_chunk_length': self.min_chunk_length,
                'max_chunk_length': self.max_chunk_length,
                'min_entity_confidence': self.min_entity_confidence,
                'duplicate_threshold': self.duplicate_threshold
            },
            'data_sources': {
                'patent_documents': str(self.patent_docs_path),
                'backup_data': str(self.backup_data_path) if self.backup_data_path.exists() else None
            },
            'version': 'v3.0.0'
        }

        report_path = Path(f"/Users/xujian/Athena工作平台/production/data/patent_rules/import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"📋 详细报告已保存: {report_path}")

    async def run_import(self):
        """运行完整导入流程"""
        logger.info("🚀 启动专利规则高质量导入系统 v3.0.0")

        # 初始化环境
        if not await self.initialize_import_environment():
            logger.error("❌ 环境初始化失败，导入终止")
            return False

        # 执行导入
        try:
            await self.import_patent_documents()

            # 生成报告
            self.generate_import_report()

            logger.info("="*80)
            logger.info("🎉 专利规则导入完成！系统已准备投入使用")
            logger.info("="*80)

            return True

        except Exception as e:
            logger.error(f"❌ 导入过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """主函数"""
    importer = PatentDataImporter()
    success = await importer.run_import()

    if success:
        logger.info("✅ 导入成功完成")
    else:
        logger.error("❌ 导入失败")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
