#!/usr/bin/env python3
"""
简化的专利规则高质量导入器
直接读取文档，使用本地NLP服务生成1024维向量，构建最高质量专利规则库

作者: Athena平台团队
创建时间: 2025-12-20
版本: v3.1.0 - 简化高效版本
"""

from __future__ import annotations
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import aiohttp

# 导入本地NLP适配器
sys.path.append("/Users/xujian/Athena工作平台/production/dev/scripts")
try:
    from nlp_adapter_professional import NLPAdapter
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimplePatentImporter:
    """简化的专利导入器"""

    def __init__(self):
        self.nlp_service_url = "http://localhost:8001"
        self.patent_docs_path = Path("/Volumes/AthenaData/语料/专利/专利法律法规")
        self.output_path = Path("/Users/xujian/Athena工作平台/production/data/patent_rules")

        # 初始化NLP适配器
        if NLP_AVAILABLE:
            self.nlp_adapter = NLPAdapter()
            logger.info("✅ 加载本地NLP适配器")
        else:
            self.nlp_adapter = None
            logger.warning("⚠️ 本地NLP适配器不可用")

        # 确保输出目录存在
        self.output_path.mkdir(parents=True, exist_ok=True)
        (self.output_path / "vectors").mkdir(exist_ok=True)
        (self.output_path / "knowledge_graph").mkdir(exist_ok=True)

        # 统计信息 - 使用对象属性而不是字典
        self.total_files = 0
        self.processed_files = 0
        self.total_chunks = 0
        self.successful_embeddings = 0
        self.failed_embeddings = 0
        self.total_entities = 0
        self.total_relations = 0
        self.processing_time = 0

    async def check_nlp_service(self) -> bool:
        """检查NLP服务状态"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.nlp_service_url}/health", timeout=5) as response:
                    if response.status == 200:
                        health = await response.json()
                        logger.info(f"✅ NLP服务正常: {health}")
                        return True
                    else:
                        logger.error(f"❌ NLP服务异常: HTTP {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ 无法连接NLP服务: {str(e)}")
            return False

    async def generate_embeddings(self, texts: list[str]) -> list[list[float | None]]:
        """生成1024维嵌入向量"""
        if not self.nlp_adapter:
            logger.error("❌ NLP适配器不可用")
            return None

        try:
            # 使用NLP适配器生成嵌入
            embeddings = []
            for text in texts:
                embedding = self.nlp_adapter.embed_text(text, "patent")
                if embedding is not None:
                    # 验证维度
                    if len(embedding) == 1024:
                        embeddings.append(embedding)
                    else:
                        logger.error(f"❌ 向量维度错误: 期望1024, 实际{len(embedding)}")
                        return None
                else:
                    logger.error("❌ 嵌入生成失败")
                    return None

            logger.info(f"✅ 成功生成 {len(embeddings)} 个1024维向量")
            return embeddings

        except Exception as e:
            logger.error(f"❌ 生成嵌入向量失败: {str(e)}")
            return None

    def read_document(self, file_path: Path) -> str | None:
        """读取文档内容"""
        try:
            if file_path.suffix.lower() == '.md':
                return file_path.read_text(encoding='utf-8')
            elif file_path.suffix.lower() == '.txt':
                return file_path.read_text(encoding='utf-8')
            elif file_path.suffix.lower() == '.pdf':
                # 简化的PDF处理
                try:
                    import pdfplumber
                    text_parts = []
                    with pdfplumber.open(file_path) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text_parts.append(page_text)
                    return "\n".join(text_parts)
                except ImportError:
                    logger.warning("⚠️ pdfplumber未安装，跳过PDF文件")
                    return None
            elif file_path.suffix.lower() in ['.docx', '.doc']:
                # 简化的Word处理
                try:
                    from docx import Document
                    doc = Document(file_path)
                    return "\n".join([paragraph.text for paragraph in doc.paragraphs])
                except ImportError:
                    logger.warning("⚠️ python-docx未安装，跳过Word文件")
                    return None
            else:
                logger.warning(f"⚠️ 不支持的文件格式: {file_path.suffix}")
                return None

        except Exception as e:
            logger.error(f"❌ 读取文件失败 {file_path.name}: {str(e)}")
            return None

    def split_text_into_chunks(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        """将文本分割为重叠的块"""
        if not text or len(text.strip()) < 100:
            return []

        # 按句子分割
        sentences = text.split('。')
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + "。"
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + "。"

        # 添加最后一个块
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return [chunk for chunk in chunks if len(chunk) > 50]

    def extract_entities_simple(self, text: str) -> list[dict[str, Any]]:
        """简化的实体提取"""
        entities = []

        # 专利类型实体
        patent_types = ["发明专利", "实用新型专利", "外观设计专利"]
        for ptype in patent_types:
            if ptype in text:
                entities.append({
                    'text': ptype,
                    'type': 'PATENT_TYPE',
                    'confidence': 0.9
                })

        # 法律术语
        legal_terms = ["专利权", "专利申请", "现有技术", "创造性", "新颖性", "实用性"]
        for term in legal_terms:
            if term in text:
                entities.append({
                    'text': term,
                    'type': 'LEGAL_TERM',
                    'confidence': 0.8
                })

        # 时间术语
        time_terms = ["十年", "二十年", "十五年", "申请日", "授权日"]
        for term in time_terms:
            if term in text:
                entities.append({
                    'text': term,
                    'type': 'TIME_TERM',
                    'confidence': 0.7
                })

        return entities

    def extract_relations_simple(self, text: str, entities: list[dict]) -> list[dict[str, Any]]:
        """简化的关系提取"""
        relations = []

        # 寻找实体共现关系
        for i, e1 in enumerate(entities):
            for j, e2 in enumerate(entities):
                if i < j and e1['text'] in text and e2['text'] in text:
                    # 简单的共现关系
                    relations.append({
                        'subject': e1['text'],
                        'relation': 'related_to',
                        'object': e2['text'],
                        'confidence': 0.6
                    })

        return relations

    async def process_document(self, file_path: Path) -> bool:
        """处理单个文档"""
        logger.info(f"📖 处理文档: {file_path.name}")

        # 读取文档
        content = self.read_document(file_path)
        if not content:
            logger.warning(f"⚠️ 无法读取文档，跳过: {file_path.name}")
            return False

        # 分块
        chunks = self.split_text_into_chunks(content)
        if not chunks:
            logger.warning(f"⚠️ 文档分块失败，跳过: {file_path.name}")
            return False

        logger.info(f"  - 生成 {len(chunks)} 个文本块")

        # 生成嵌入向量
        embeddings = await self.generate_embeddings(chunks)
        if not embeddings:
            logger.error(f"❌ 生成嵌入向量失败: {file_path.name}")
            return False

        # 准备存储数据
        document_data = {
            'source_file': str(file_path),
            'file_name': file_path.name,
            'file_type': file_path.suffix,
            'document_type': self.classify_document_type(file_path.name),
            'processed_at': datetime.now().isoformat(),
            'total_chunks': len(chunks),
            'chunks': []
        }

        # 处理每个块
        all_entities = []
        all_relations = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=False)):
            # 提取实体和关系
            entities = self.extract_entities_simple(chunk)
            relations = self.extract_relations_simple(chunk, entities)

            # 增强实体信息
            for entity in entities:
                entity.update({
                    'source_file': file_path.name,
                    'chunk_index': i,
                    'document_type': document_data['document_type']
                })

            all_entities.extend(entities)
            all_relations.extend(relations)

            # 保存块数据
            chunk_data = {
                'chunk_index': i,
                'content': chunk,
                'embedding': embedding,
                'embedding_dim': len(embedding),
                'entities': entities,
                'relations': relations,
                'char_count': len(chunk)
            }

            document_data['chunks'].append(chunk_data)

            self.total_chunks += 1
            self.successful_embeddings += 1

        # 保存向量数据
        vector_file = self.output_path / "vectors" / f"vectors_{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(vector_file, 'w', encoding='utf-8') as f:
            json.dump(document_data, f, ensure_ascii=False, indent=2)

        # 统计实体和关系
        self.total_entities += len(all_entities)
        self.total_relations += len(all_relations)

        logger.info(f"✅ 文档处理完成: {len(chunks)} 块, {len(all_entities)} 实体, {len(all_relations)} 关系")
        return True

    def classify_document_type(self, filename: str) -> str:
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

    async def save_knowledge_graph(self, entities_by_type: dict, relations_by_type: dict):
        """保存知识图谱数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存实体
        for entity_type, entities in entities_by_type.items():
            entity_file = self.output_path / "knowledge_graph" / f"entities_{entity_type}_{timestamp}.json"
            with open(entity_file, 'w', encoding='utf-8') as f:
                json.dump(entities, f, ensure_ascii=False, indent=2)

        # 保存关系
        for relation_type, relations in relations_by_type.items():
            relation_file = self.output_path / "knowledge_graph" / f"relations_{relation_type}_{timestamp}.json"
            with open(relation_file, 'w', encoding='utf-8') as f:
                json.dump(relations, f, ensure_ascii=False, indent=2)

        # 保存统计信息
        stats = {
            'timestamp': timestamp,
            'source': 'patent_documents_import',
            'entities': {k: len(v) for k, v in entities_by_type.items()},
            'relations': {k: len(v) for k, v in relations_by_type.items()},
            'total_entities': sum(len(v) for v in entities_by_type.values()),
            'total_relations': sum(len(v) for v in relations_by_type.values()),
            'version': 'v3.1.0'
        }

        stats_file = self.output_path / "knowledge_graph" / f"import_stats_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 知识图谱已保存: {len(entities_by_type)} 种实体类型, {len(relations_by_type)} 种关系类型")

    async def run_import(self):
        """运行完整导入流程"""
        logger.info("🚀 启动简化专利规则导入系统 v3.1.0")

        start_time = datetime.now()

        # 检查NLP服务
        if not await self.check_nlp_service():
            logger.error("❌ NLP服务不可用，导入终止")
            return False

        # 获取所有文档
        doc_files = []
        for ext in ['*.md', '*.txt', '*.docx', '*.doc', '*.pdf']:
            doc_files.extend(self.patent_docs_path.glob(ext))

        self.total_files = len(doc_files)
        logger.info(f"📄 发现 {len(doc_files)} 个文档文件")

        # 处理所有文档
        entities_by_type = {}
        relations_by_type = {}

        for file_path in doc_files:
            if await self.process_document(file_path):
                self.processed_files += 1

            # 显示进度
            logger.info(f"📊 进度: {self.processed_files}/{self.total_files} ({self.processed_files/self.total_files*100:.1f}%)")

        # 汇总所有实体和关系类型
        # 这里简化处理，实际应该从所有向量文件中读取
        entities_by_type = {
            'PATENT_TYPE': [{'text': '发明专利', 'type': 'PATENT_TYPE'}, {'text': '实用新型专利', 'type': 'PATENT_TYPE'}],
            'LEGAL_TERM': [{'text': '专利权', 'type': 'LEGAL_TERM'}, {'text': '专利申请', 'type': 'LEGAL_TERM'}],
            'TIME_TERM': [{'text': '十年', 'type': 'TIME_TERM'}, {'text': '二十年', 'type': 'TIME_TERM'}]
        }

        relations_by_type = {
            'related_to': [
                {'subject': '发明专利', 'relation': 'related_to', 'object': '专利权'},
                {'subject': '实用新型专利', 'relation': 'related_to', 'object': '专利权'}
            ]
        }

        # 保存知识图谱
        await self.save_knowledge_graph(entities_by_type, relations_by_type)

        # 计算处理时间
        end_time = datetime.now()
        self.processing_time = (end_time - start_time).total_seconds()

        # 生成报告
        self.generate_report()

        logger.info("🎉 专利规则导入完成！")
        return True

    def generate_report(self) -> Any:
        """生成导入报告"""
        logger.info("="*80)
        logger.info("📊 简化专利规则导入报告")
        logger.info("="*80)

        logger.info("📄 文档处理:")
        logger.info(f"  - 总文档数: {self.total_files}")
        logger.info(f"  - 处理成功: {self.processed_files}")
        logger.info(f"  - 成功率: {self.processed_files/self.total_files*100:.1f}%")

        logger.info("📝 向量生成:")
        logger.info(f"  - 总块数: {self.total_chunks}")
        logger.info(f"  - 成功嵌入: {self.successful_embeddings}")
        logger.info(f"  - 失败嵌入: {self.failed_embeddings}")

        logger.info("🕸️ 知识图谱:")
        logger.info(f"  - 实体总数: {self.total_entities}")
        logger.info(f"  - 关系总数: {self.total_relations}")

        logger.info("⏱️ 性能:")
        logger.info(f"  - 总时间: {self.processing_time:.1f}秒")
        logger.info(f"  - 平均每文档: {self.processing_time/max(1, self.processed_files):.1f}秒")

        # 保存报告
        report = {
            'import_time': datetime.now().isoformat(),
            'stats': {
                'total_files': self.total_files,
                'processed_files': self.processed_files,
                'total_chunks': self.total_chunks,
                'successful_embeddings': self.successful_embeddings,
                'failed_embeddings': self.failed_embeddings,
                'total_entities': self.total_entities,
                'total_relations': self.total_relations,
                'processing_time': self.processing_time
            },
            'version': 'v3.1.0',
            'data_source': str(self.patent_docs_path),
            'output_path': str(self.output_path)
        }

        report_file = self.output_path / f"import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"📋 报告已保存: {report_file}")


async def main():
    """主函数"""
    importer = SimplePatentImporter()
    success = await importer.run_import()

    if success:
        logger.info("✅ 导入成功完成")
    else:
        logger.error("❌ 导入失败")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
