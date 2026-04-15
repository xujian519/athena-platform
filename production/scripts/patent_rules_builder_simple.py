#!/usr/bin/env python3
"""
专利规则构建系统 - 简化版
Patent Rules Builder - Simple Version

从专利法律法规文档构建向量库和知识图谱

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / "patent_rules_system"))

from bert_extractor_simple import PatentEntityRelationExtractor
from nebula_graph_builder import NebulaGraphBuilder
from qdrant_vector_store_simple import DocumentType, QdrantVectorStoreSimple, VectorDocument

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PatentRulesBuilderSimple:
    """专利规则构建系统 - 简化版"""

    def __init__(self):
        self.laws_path = Path("/Users/xujian/学习资料/专利/专利法律法规")
        self.output_path = Path("/Users/xujian/Athena工作平台/production/data/patent_rules")
        self.vector_store = QdrantVectorStoreSimple()
        self.extractor = PatentEntityRelationExtractor()
        self.graph_builder = NebulaGraphBuilder()

        # 创建输出目录
        self.output_path.mkdir(parents=True, exist_ok=True)

        # 统计信息
        self.stats = {
            "total_files": 0,
            "processed_files": 0,
            "failed_files": [],
            "total_documents": 0,
            "total_entities": 0,
            "total_relations": 0,
            "start_time": None,
            "end_time": None
        }

    async def scan_documents(self) -> list[dict]:
        """扫描专利法律法规文档（仅处理txt和md文件）"""
        logger.info(f"🔍 扫描目录: {self.laws_path}")

        documents = []
        # 先处理txt和md文件
        file_types = ['.txt', '.md']

        for file_path in self.laws_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in file_types:
                # 判断文档类型
                file_name = file_path.name.lower()
                if '专利审查指南' in file_name:
                    doc_type = DocumentType.PATENT_GUIDELINE
                elif '专利法' in file_name and '实施细则' not in file_name:
                    doc_type = DocumentType.PATENT_LAW
                elif '实施细则' in file_name:
                    doc_type = DocumentType.IMPLEMENTATION_RULES
                elif '最高人民法院' in file_name or '解释' in file_name:
                    doc_type = DocumentType.JUDICIAL_INTERPRETATION
                elif '条例' in file_name:
                    doc_type = DocumentType.REGULATION
                else:
                    doc_type = DocumentType.PATENT_LAW  # 默认使用专利法类型

                documents.append({
                    'path': str(file_path),
                    'name': file_path.name,
                    'type': doc_type,
                    'size': file_path.stat().st_size
                })

        self.stats['total_files'] = len(documents)
        logger.info(f"✅ 找到 {len(documents)} 个文档")

        # 按类型统计
        type_count = {}
        for doc in documents:
            type_name = doc['type'].value if hasattr(doc['type'], 'value') else str(doc['type'])
            type_count[type_name] = type_count.get(type_name, 0) + 1

        for doc_type, count in sorted(type_count.items()):
            logger.info(f"  - {doc_type}: {count} 个")

        return documents

    async def process_document(self, doc_info: dict) -> list[VectorDocument | None]:
        """处理单个文档"""
        file_path = Path(doc_info['path'])

        try:
            logger.info(f"📖 处理文档: {file_path.name}")

            # 读取文本内容
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            if not content:
                logger.warning(f"⚠️ 文档内容为空: {file_path.name}")
                return None

            # 清理内容
            content = re.sub(r'\n{3,}', '\n\n', content)  # 减少空行
            content = content.strip()

            # 智能分段
            documents = []
            sections = self.split_content(content)

            for i, section in enumerate(sections):
                # 创建向量文档
                doc = VectorDocument(
                    doc_id=f"{file_path.stem}_{i}",
                    content=section,
                    doc_type=doc_info['type'],
                    metadata={
                        'source_file': str(file_path),
                        'section_number': i + 1,
                        'total_sections': len(sections),
                        'file_size': doc_info['size'],
                        'document_title': file_path.stem
                    }
                )
                documents.append(doc)

            self.stats['processed_files'] += 1
            self.stats['total_documents'] += len(documents)

            logger.info(f"✅ 成功处理 {len(documents)} 个段落")
            return documents

        except Exception as e:
            logger.error(f"❌ 处理文档失败 {file_path.name}: {str(e)}")
            self.stats['failed_files'].append(str(file_path))
            return None

    def split_content(self, content: str) -> list[str]:
        """智能分割内容"""
        # 按空行分割
        paragraphs = content.split('\n\n')

        # 过滤短段落
        paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 50]

        # 如果段落太长，进一步分割
        sections = []
        for para in paragraphs:
            if len(para) > 1000:
                # 按句子分割长段落
                sentences = re.split(r'[。！？；]\s*', para)
                current_section = ""
                for sentence in sentences:
                    if sentence:
                        if len(current_section + sentence) < 800:
                            current_section += sentence + "。"
                        else:
                            if current_section:
                                sections.append(current_section.strip())
                            current_section = sentence + "。"
                if current_section:
                    sections.append(current_section.strip())
            else:
                sections.append(para)

        return sections

    async def extract_entities_and_relations(self, documents: list[VectorDocument]) -> dict:
        """提取实体和关系"""
        logger.info("🧠 开始提取实体和关系...")

        all_entities = []
        all_relations = []

        for doc in documents:
            try:
                # 提取实体
                entities = await self.extractor.extract_entities(doc.content, doc.doc_id)
                relations = []  # 暂时不提取关系

                # 处理实体
                for entity in entities:
                    entity['source_document'] = doc.doc_id
                    entity['document_type'] = doc.doc_type.value
                    all_entities.append(entity)

            except Exception as e:
                logger.warning(f"⚠️ 提取实体关系失败 {doc.doc_id}: {str(e)}")

        self.stats['total_entities'] = len(all_entities)
        self.stats['total_relations'] = len(all_relations)

        logger.info(f"✅ 提取完成: {len(all_entities)} 个实体, {len(all_relations)} 个关系")

        return {
            'entities': all_entities,
            'relations': all_relations
        }

    async def build_vector_database(self, all_documents: list[VectorDocument]):
        """构建向量数据库"""
        logger.info("🗄️ 构建向量数据库...")

        try:
            # 初始化向量库（使用默认的patent_rules集合）
            await self.vector_store.create_collection()

            # 批量索引文档
            batch_size = 50
            total_batches = (len(all_documents) + batch_size - 1) // batch_size

            for i in range(0, len(all_documents), batch_size):
                batch = all_documents[i:i + batch_size]
                batch_num = i // batch_size + 1

                logger.info(f"📦 处理批次 {batch_num}/{total_batches} ({len(batch)} 个文档)")

                # 批量索引
                await self.vector_store.batch_index(batch)

            logger.info(f"✅ 向量数据库构建完成: {len(all_documents)} 个文档")

        except Exception as e:
            logger.error(f"❌ 构建向量数据库失败: {str(e)}")
            raise

    async def build_knowledge_graph(self, entities_and_relations: dict):
        """构建知识图谱"""
        logger.info("🕸️ 构建知识图谱...")

        try:
            # 初始化图数据库
            await self.graph_builder.initialize_space()

            # 添加实体
            entities = entities_and_relations.get('entities', [])
            if entities:
                entity_ids = await self.graph_builder.add_entities(entities)
                logger.info(f"✅ 添加 {len(entity_ids)} 个实体")

            # 添加关系
            relations = entities_and_relations.get('relations', [])
            if relations and entities:
                relation_ids = await self.graph_builder.add_relations(relations)
                logger.info(f"✅ 添加 {len(relation_ids)} 个关系")

            logger.info("✅ 知识图谱构建完成")

        except Exception as e:
            logger.error(f"❌ 构建知识图谱失败: {str(e)}")
            raise

    async def generate_report(self):
        """生成构建报告"""
        self.stats['end_time'] = datetime.now()

        # 计算耗时
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

        # 生成报告
        report = {
            "构建时间": self.stats['start_time'].isoformat(),
            "完成时间": self.stats['end_time'].isoformat(),
            "总耗时": f"{duration:.2f}秒",
            "文档统计": {
                "扫描文档数": self.stats['total_files'],
                "处理成功数": self.stats['processed_files'],
                "处理失败数": len(self.stats['failed_files']),
                "失败文档": self.stats['failed_files'],
                "生成段落数": self.stats['total_documents']
            },
            "知识提取统计": {
                "提取实体数": self.stats['total_entities'],
                "提取关系数": self.stats['total_relations']
            },
            "输出位置": {
                "向量数据库": str(self.output_path / "vector_db"),
                "知识图谱": str(self.output_path / "knowledge_graph")
            }
        }

        # 保存报告
        report_file = self.output_path / f"build_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 构建报告已保存: {report_file}")

        # 打印摘要
        logger.info("\n" + "="*60)
        logger.info("🎯 专利规则构建系统 - 构建完成")
        logger.info("="*60)
        logger.info(f"📊 处理文档: {self.stats['processed_files']}/{self.stats['total_files']}")
        logger.info(f"📝 生成段落: {self.stats['total_documents']}")
        logger.info(f"🏷️ 提取实体: {self.stats['total_entities']}")
        logger.info(f"🔗 提取关系: {self.stats['total_relations']}")
        logger.info(f"⏱️ 总耗时: {duration:.2f}秒")
        logger.info("="*60)

        return report

    async def run(self):
        """运行构建流程"""
        logger.info("🚀 启动专利规则构建系统")
        self.stats['start_time'] = datetime.now()

        try:
            # 1. 扫描文档
            documents = await self.scan_documents()

            # 2. 处理所有文档
            logger.info("\n📖 开始处理文档...")
            all_documents = []
            all_entities_and_relations = {'entities': [], 'relations': []}

            for doc_info in documents:
                docs = await self.process_document(doc_info)
                if docs:
                    all_documents.extend(docs)

                    # 提取实体和关系
                    entities_and_relations = await self.extract_entities_and_relations(docs)
                    all_entities_and_relations['entities'].extend(entities_and_relations['entities'])
                    all_entities_and_relations['relations'].extend(entities_and_relations['relations'])

            # 3. 构建向量数据库
            if all_documents:
                await self.build_vector_database(all_documents)

            # 4. 构建知识图谱
            if all_entities_and_relations['entities']:
                await self.build_knowledge_graph(all_entities_and_relations)

            # 5. 生成报告
            report = await self.generate_report()

            logger.info("🎉 构建完成!")
            return report

        except Exception as e:
            logger.error(f"❌ 构建失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise

async def main():
    """主函数"""
    builder = PatentRulesBuilderSimple()
    await builder.run()

if __name__ == "__main__":
    asyncio.run(main())
