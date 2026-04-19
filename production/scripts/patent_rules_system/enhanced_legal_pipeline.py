#!/usr/bin/env python3
"""
专利法律法规NER增强处理管道
Enhanced Legal Pipeline with NER Integration

集成新的BERT NER系统，处理专利法律法规文档：
1. 使用增强NER提取实体
2. 构建向量库（去重）
3. 构建知识图谱（去重）
4. 生成处理报告

重要：使用本地Apple Silicon优化模型，禁止网络下载

作者: 小诺AI团队
创建时间: 2025-12-28
版本: v2.0.0
"""

from __future__ import annotations
import json
import logging
import os
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# ===== 强制使用本地模型，禁止网络下载 =====
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'  # 仅用于已有模型
os.environ['TRANSFORMERS_OFFLINE'] = '1'  # 强制离线模式
os.environ['HF_HUB_OFFLINE'] = '1'  # HuggingFace离线

# 本地模型路径
LOCAL_MODELS = {
    'ner': '/Users/xujian/.cache/huggingface/hub/models--uer--roberta-base-finetuned-cluener2020-chinese',
    'embedding': '/Users/xujian/Athena工作平台/models/converted/bge-large-zh-v1.5',
}

# 文档处理
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

import pdfplumber
from production.core.ner_production_service import extract_entities_from_text, get_ner_service

# Qdrant
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

# NLP和向量
from sentence_transformers import SentenceTransformer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class LegalChunk:
    """法律文本块"""
    id: str
    content: str
    doc_type: str  # law, rule, interpretation, guideline
    source_file: str
    chunk_type: str  # article, section, clause, content
    chapter: str = ""
    section: str = ""
    article_number: str = ""
    page_num: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    # NER提取的实体
    entities: list[dict[str, Any]] = field(default_factory=list)

    # 向量
    embedding: list[float] | None = None

    def to_hash(self) -> str:
        """生成内容哈希用于去重"""
        content_str = f"{self.content}|{self.chunk_type}|{self.article_number}"
        return short_hash(content_str.encode())


@dataclass
class LegalEntity:
    """法律实体"""
    id: str
    text: str
    entity_type: str
    source_chunk_id: str
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LegalRelation:
    """法律关系"""
    id: str
    source_entity: str
    target_entity: str
    relation_type: str
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)


class LegalDocumentProcessor:
    """法律文档处理器"""

    def __init__(self, source_dir: str):
        self.source_dir = Path(source_dir)

        # 支持的文件类型
        self.supported_extensions = ['.md', '.txt', '.docx', '.pdf', '.doc']

        # 法律文档类型识别
        self.doc_type_patterns = {
            'law': ['专利法'],
            'rule': ['实施细则', '条例', '办法'],
            'interpretation': ['解释', '规定'],
            'guideline': ['指南', '说明'],
        }

    def scan_documents(self) -> list[Path]:
        """扫描所有法律文档"""
        documents = []

        for ext in self.supported_extensions:
            for file_path in self.source_dir.rglob(f'*{ext}'):
                if not file_path.name.startswith('.'):
                    documents.append(file_path)

        logger.info(f"扫描到 {len(documents)} 个法律文档")
        return documents

    def detect_doc_type(self, file_path: Path) -> str:
        """检测文档类型"""
        filename = file_path.name.lower()

        for doc_type, patterns in self.doc_type_patterns.items():
            if any(p in filename for p in patterns):
                return doc_type

        return 'other'

    def read_document(self, file_path: Path) -> str:
        """读取文档内容"""
        suffix = file_path.suffix.lower()

        if suffix == '.pdf':
            return self._read_pdf(file_path)
        elif suffix == '.docx' and DOCX_AVAILABLE:
            return self._read_docx(file_path)
        elif suffix in ['.md', '.txt']:
            return self._read_text(file_path)
        else:
            logger.warning(f"不支持的文件类型: {suffix}")
            return ""

    def _read_pdf(self, file_path: Path) -> str:
        """读取PDF"""
        try:
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)

            return '\n'.join(text_parts)
        except Exception as e:
            logger.error(f"PDF读取失败 {file_path}: {e}")
            return ""

    def _read_docx(self, file_path: Path) -> str:
        """读取DOCX"""
        try:
            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return '\n'.join(paragraphs)
        except Exception as e:
            logger.error(f"DOCX读取失败 {file_path}: {e}")
            return ""

    def _read_text(self, file_path: Path) -> str:
        """读取文本文件"""
        try:
            with open(file_path, encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, encoding='gbk') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"文本读取失败 {file_path}: {e}")
                return ""

    def chunk_document(self, content: str, doc_type: str, source_file: Path) -> list[LegalChunk]:
        """将文档分块"""
        chunks = []

        # 按章节分块
        articles = self._split_by_articles(content)

        for i, (article_num, article_content) in enumerate(articles):
            if len(article_content.strip()) < 10:
                continue

            chunk = LegalChunk(
                id=f"{source_file.stem}_article_{i}",
                content=article_content.strip(),
                doc_type=doc_type,
                source_file=str(source_file),
                chunk_type="article",
                article_number=article_num,
            )

            chunks.append(chunk)

        logger.info(f"文档 {source_file.name} 分块为 {len(chunks)} 个文章")
        return chunks

    def _split_by_articles(self, content: str) -> list[tuple[str, str]]:
        """按条分块"""
        articles = []

        # 匹配模式: 第XX条、第XX款等
        patterns = [
            r'第([一二三四五六七八九十百千万\d]+)条[：:\s]*(.*?)(?=第[一二三四五六七八九十百千万\d]+条|$)',
            r'([一二三四五六七八九十百千万\d]+)[、.](.*?)(?=[一二三四五六七八九十百千万\d]+[、.]|$)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                for match in matches:
                    num = match[0]
                    text = match[1] if len(match) > 1 else ""
                    if text.strip():
                        articles.append((f"第{num}条", text.strip()))
                break

        # 如果没有匹配到，返回整个文档作为一个块
        if not articles and content.strip():
            articles.append(("全文", content.strip()))

        return articles


class EnhancedLegalNERExtractor:
    """增强NER实体提取器"""

    def __init__(self):
        # 获取NER服务
        self.ner_service = get_ner_service()
        self.extracted_entities = defaultdict(list)

    def extract_entities(self, chunk: LegalChunk) -> list[LegalEntity]:
        """从文本块提取实体"""
        try:
            # 使用增强NER服务
            result = extract_entities_from_text(chunk.content)

            entities = []
            for entity_data in result.get('entities', []):
                entity = LegalEntity(
                    id=f"{chunk.id}_entity_{len(entities)}",
                    text=entity_data['text'],
                    entity_type=entity_data['type'],
                    source_chunk_id=chunk.id,
                    confidence=entity_data.get('confidence', 0.9),
                    metadata={
                        'start': entity_data.get('start', 0),
                        'end': entity_data.get('end', 0),
                    }
                )
                entities.append(entity)

            # 更新chunk的实体
            chunk.entities = [asdict(e) for e in entities]

            # 统计
            for entity in entities:
                self.extracted_entities[entity.entity_type].append(entity)

            return entities

        except Exception as e:
            logger.error(f"实体提取失败: {e}")
            return []

    def get_entity_summary(self) -> dict[str, int]:
        """获取实体统计摘要"""
        return {k: len(v) for k, v in self.extracted_entities.items()}


class DeduplicationManager:
    """去重管理器"""

    def __init__(self):
        self.content_hashes: set[str] = set()
        self.entity_hashes: set[str] = set()
        self.duplicate_count = 0

    def is_duplicate_content(self, chunk: LegalChunk) -> bool:
        """检查内容是否重复"""
        content_hash = chunk.to_hash()

        if content_hash in self.content_hashes:
            self.duplicate_count += 1
            return True

        self.content_hashes.add(content_hash)
        return False

    def is_duplicate_entity(self, entity: LegalEntity) -> bool:
        """检查实体是否重复"""
        entity_hash = short_hash(
            f"{entity.text}_{entity.entity_type}".encode('utf-8')
        )

        if entity_hash in self.entity_hashes:
            return False  # 允许相同实体在不同上下文中出现

        self.entity_hashes.add(entity_hash)
        return False

    def get_stats(self) -> dict[str, int]:
        """获取去重统计"""
        return {
            'unique_contents': len(self.content_hashes),
            'unique_entities': len(self.entity_hashes),
            'duplicates_found': self.duplicate_count,
        }


class VectorStoreManager:
    """向量存储管理器"""

    def __init__(self, collection_name: str = "patent_legal_rules_enhanced"):
        self.collection_name = collection_name
        self.client = QdrantClient(host="localhost", port=6333)

        # 强制使用本地BGE模型
        model_path = LOCAL_MODELS['embedding']
        if Path(model_path).exists():
            logger.info(f"✅ 使用本地BGE模型: {model_path}")
            self.embedding_model = SentenceTransformer(
                model_path,
                trust_remote_code=False,  # 不信任远程代码
                local_files_only=True,    # 仅使用本地文件
            )
        else:
            raise RuntimeError(
                f"本地BGE模型不存在: {model_path}\n"
                f"请确保模型已下载到本地目录"
            )

        self.vector_dim = self.embedding_model.get_sentence_embedding_dimension()
        logger.info(f"向量维度: {self.vector_dim}")

        # 创建集合
        self._ensure_collection()

    def _ensure_collection(self) -> Any:
        """确保集合存在"""
        collections = [c.name for c in self.client.get_collections().collections]

        if self.collection_name not in collections:
            logger.info(f"创建集合: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_dim,
                    distance=Distance.COSINE,
                ),
            )
        else:
            logger.info(f"集合已存在: {self.collection_name}")

    def embed_chunks(self, chunks: list[LegalChunk]) -> list[LegalChunk]:
        """向量化文本块"""
        if not chunks:
            return []

        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_model.encode(
            texts,
            show_progress_bar=True,
            batch_size=32,
        )

        for chunk, embedding in zip(chunks, embeddings, strict=False):
            chunk.embedding = embedding.tolist()

        logger.info(f"向量化 {len(chunks)} 个文本块")
        return chunks

    def upsert_chunks(self, chunks: list[LegalChunk]) -> int:
        """批量插入向量"""
        if not chunks:
            return 0

        points = []
        for chunk in chunks:
            if chunk.embedding is None:
                continue

            point = PointStruct(
                id=hash(chunk.id) % (2**32),  # 转换为正整数
                vector=chunk.embedding,
                payload={
                    'content': chunk.content,
                    'doc_type': chunk.doc_type,
                    'source_file': chunk.source_file,
                    'chunk_type': chunk.chunk_type,
                    'article_number': chunk.article_number,
                    'chapter': chunk.chapter,
                    'section': chunk.section,
                    'entities': chunk.entities,
                    'entity_count': len(chunk.entities),
                }
            )
            points.append(point)

        # 批量插入
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        logger.info(f"插入 {len(points)} 个向量点")
        return len(points)

    def search_similar(self, query: str, limit: int = 5) -> list[dict]:
        """搜索相似内容"""
        query_vector = self.embedding_model.encode(query)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            limit=limit,
        )

        return [
            {
                'content': r.payload.get('content', ''),
                'score': r.score,
                'metadata': r.payload,
            }
            for r in results
        ]

    def get_collection_info(self) -> dict:
        """获取集合信息"""
        info = self.client.get_collection(self.collection_name)
        return {
            'name': self.collection_name,
            'points_count': info.points_count,
            'config': str(info.config),
        }


class KnowledgeGraphBuilder:
    """知识图谱构建器"""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.entities: dict[str, dict] = {}
        self.relations: dict[str, list[dict]] = defaultdict(list)

    def add_entity(self, entity: LegalEntity) -> None:
        """添加实体"""
        if entity.id not in self.entities:
            self.entities[entity.id] = {
                'id': entity.id,
                'text': entity.text,
                'type': entity.entity_type,
                'metadata': entity.metadata,
                'relations_count': 0,
            }

    def add_relation(self, relation: LegalRelation) -> None:
        """添加关系"""
        relation_key = f"{relation.source_entity}_{relation.relation_type}_{relation.target_entity}"
        self.relations[relation.relation_type].append({
            'id': relation.id,
            'source': relation.source_entity,
            'target': relation.target_entity,
            'confidence': relation.confidence,
            'metadata': relation.metadata,
        })

    def infer_relations(self, chunks: list[LegalChunk]) -> Any:
        """推断法律关系"""
        for i, chunk in enumerate(chunks):
            entities = chunk.entities

            # 同一文档内的实体关系
            for j, e1 in enumerate(entities):
                for k, e2 in enumerate(entities):
                    if j >= k:  # 避免重复
                        continue

                    # 推断关系类型
                    relation_type = self._infer_relation_type(e1, e2, chunk)

                    if relation_type:
                        relation = LegalRelation(
                            id=f"rel_{i}_{j}_{k}",
                            source_entity=e1.get('text', ''),
                            target_entity=e2.get('text', ''),
                            relation_type=relation_type,
                            confidence=0.8,
                        )
                        self.add_relation(relation)

    def _infer_relation_type(self, e1: dict, e2: dict, chunk: LegalChunk) -> str | None:
        """推断两个实体之间的关系"""
        type1 = e1.get('entity_type', '')
        type2 = e2.get('entity_type', '')

        # 定义关系映射
        relation_rules = {
            ('PATENT_NUM', 'APPLICANT'): 'applied_by',
            ('PATENT_NUM', 'INVENTOR'): 'invented_by',
            ('APPLICANT', 'INVENTOR'): 'employs',
            ('COMP', 'NAME'): 'employs',
            ('ORG', 'ADDR'): 'located_at',
            ('PATENT_NUM', 'IPC_CODE'): 'classified_as',
            ('TECH_TERM', 'PATENT_NUM'): 'relates_to',
        }

        # 双向检查
        key = (type1, type2)
        reverse_key = (type2, type1)

        if key in relation_rules:
            return relation_rules[key]
        elif reverse_key in relation_rules:
            return relation_rules[reverse_key]

        return None

    def save(self) -> Any:
        """保存知识图谱"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存实体
        entities_file = self.output_dir / f"entities_{timestamp}.json"
        with open(entities_file, 'w', encoding='utf-8') as f:
            json.dump(self.entities, f, ensure_ascii=False, indent=2)

        # 保存关系
        relations_file = self.output_dir / f"relations_{timestamp}.json"
        with open(relations_file, 'w', encoding='utf-8') as f:
            json.dump(dict(self.relations), f, ensure_ascii=False, indent=2)

        logger.info(f"知识图谱已保存: {len(self.entities)} 个实体, {sum(len(v) for v in self.relations.values())} 个关系")

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            'total_entities': len(self.entities),
            'total_relations': sum(len(v) for v in self.relations.values()),
            'relation_types': list(self.relations.keys()),
        }


class EnhancedLegalPipeline:
    """增强法律处理管道"""

    def __init__(self, source_dir: str, output_dir: str):
        self.source_dir = source_dir
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化组件
        self.doc_processor = LegalDocumentProcessor(source_dir)
        self.ner_extractor = EnhancedLegalNERExtractor()
        self.deduplicator = DeduplicationManager()
        self.vector_store = VectorStoreManager()
        self.kg_builder = KnowledgeGraphBuilder(str(self.output_dir / "knowledge_graph"))

        # 统计
        self.stats = {
            'start_time': datetime.now().isoformat(),
            'documents_processed': 0,
            'chunks_created': 0,
            'chunks_after_dedup': 0,
            'entities_extracted': 0,
            'vectors_stored': 0,
        }

    def run(self) -> None:
        """运行管道"""
        logger.info("=" * 60)
        logger.info("🚀 启动增强法律处理管道")
        logger.info("=" * 60)
        logger.info(f"源目录: {self.source_dir}")
        logger.info(f"输出目录: {self.output_dir}")

        # 1. 扫描文档
        logger.info("\n📂 扫描文档...")
        documents = self.doc_processor.scan_documents()
        self.stats['documents_processed'] = len(documents)

        # 2. 处理每个文档
        all_chunks = []
        all_entities = []

        for i, doc_path in enumerate(documents, 1):
            logger.info(f"\n📄 处理文档 {i}/{len(documents)}: {doc_path.name}")

            # 读取文档
            content = self.doc_processor.read_document(doc_path)
            if not content:
                logger.warning("文档内容为空，跳过")
                continue

            # 检测文档类型
            doc_type = self.doc_processor.detect_doc_type(doc_path)
            logger.info(f"文档类型: {doc_type}")

            # 分块
            chunks = self.doc_processor.chunk_document(content, doc_type, doc_path)
            self.stats['chunks_created'] += len(chunks)

            # NER实体提取
            for chunk in chunks:
                entities = self.ner_extractor.extract_entities(chunk)
                all_entities.extend(entities)

                # 去重检查
                if not self.deduplicator.is_duplicate_content(chunk):
                    all_chunks.append(chunk)

            self.stats['entities_extracted'] = len(all_entities)

        # 去重统计
        dedup_stats = self.deduplicator.get_stats()
        self.stats['chunks_after_dedup'] = dedup_stats['unique_contents']
        self.stats['duplicates_removed'] = dedup_stats['duplicates_found']

        logger.info("\n🔄 去重完成:")
        logger.info(f"  原始块数: {self.stats['chunks_created']}")
        logger.info(f"  去重后: {self.stats['chunks_after_dedup']}")
        logger.info(f"  移除重复: {self.stats['duplicates_removed']}")

        # 3. 向量化并存储
        logger.info(f"\n🔢 向量化 {len(all_chunks)} 个文本块...")
        chunks_with_embeddings = self.vector_store.embed_chunks(all_chunks)

        logger.info("\n💾 存储向量到Qdrant...")
        points_count = self.vector_store.upsert_chunks(chunks_with_embeddings)
        self.stats['vectors_stored'] = points_count

        # 4. 构建知识图谱
        logger.info("\n🕸️  构建知识图谱...")
        self.kg_builder.infer_relations(chunks_with_embeddings)

        # 添加实体到知识图谱
        for entity in all_entities:
            self.kg_builder.add_entity(entity)

        self.kg_builder.save()

        # 5. 生成报告
        self.stats['end_time'] = datetime.now().isoformat()
        self._generate_report()

        logger.info("\n" + "=" * 60)
        logger.info("✅ 管道处理完成！")
        logger.info("=" * 60)

    def _generate_report(self) -> Any:
        """生成处理报告"""
        report = {
            'pipeline': 'enhanced_legal_pipeline',
            'version': '2.0.0',
            'stats': self.stats,
            'deduplication': self.deduplicator.get_stats(),
            'entities': self.ner_extractor.get_entity_summary(),
            'vector_store': self.vector_store.get_collection_info(),
            'knowledge_graph': self.kg_builder.get_stats(),
        }

        # 保存JSON报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.output_dir / f"pipeline_report_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"📊 报告已保存: {report_file}")

        # 打印摘要
        logger.info("\n📋 处理摘要:")
        logger.info(f"  文档数: {self.stats['documents_processed']}")
        logger.info(f"  文本块数: {self.stats['chunks_after_dedup']}")
        logger.info(f"  实体数: {self.stats['entities_extracted']}")
        logger.info(f"  向量数: {self.stats['vectors_stored']}")


def main() -> None:
    """主函数"""
    # 配置
    source_dir = "/Volumes/AthenaData/语料/专利/专利法律法规"
    output_dir = "/Users/xujian/Athena工作平台/production/data/patent_rules_enhanced"

    # 创建并运行管道
    pipeline = EnhancedLegalPipeline(source_dir, output_dir)
    pipeline.run()


if __name__ == "__main__":
    main()
