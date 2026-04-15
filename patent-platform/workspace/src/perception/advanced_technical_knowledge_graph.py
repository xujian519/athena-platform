#!/usr/bin/env python3
"""
高级技术知识图谱系统
Advanced Technical Knowledge Graph System

集成CNIPA IPC定义、OwnThink知识图谱和向量库的完整技术知识图谱
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

import hashlib
import json
import logging
import pickle
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TechEntity:
    """技术实体"""
    entity_id: str
    name: str
    alias: list[str] = field(default_factory=list)
    category: str = 'general'  # 术语类别
    domain: str = 'unknown'  # 技术领域
    ipc_codes: list[str] = field(default_factory=list)  # 相关IPC分类
    definition: str | None = None
    description: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    relationships: dict[str, list[str]] = field(default_factory=dict)
    embedding: np.ndarray | None = None
    confidence: float = 1.0
    source: str = 'unknown'  # 数据来源
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class TechRelation:
    """技术关系"""
    relation_id: str
    subject: str  # 主语实体ID
    predicate: str  # 谓语/关系类型
    object: str  # 宾语实体ID
    confidence: float = 1.0
    evidence: list[str] = field(default_factory=list)
    source: str = 'unknown'
    created_at: datetime = field(default_factory=datetime.now)

class AdvancedTechnicalKnowledgeGraph:
    """高级技术知识图谱"""

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or '/Users/xujian/Athena工作平台/patent-platform/workspace/data/technical_kg'
        self.entities: dict[str, TechEntity] = {}
        self.relations: dict[str, TechRelation] = {}
        self.indices: dict[str, set[str]] = {
            'name': set(),
            'alias': set(),
            'domain': set(),
            'ipc': set(),
            'category': set()
        }
        self.embedding_index: Any | None = None
        self.is_loaded = False

    def load_knowledge_base(self):
        """加载知识库"""
        logger.info('🚀 加载技术知识图谱...')

        # 1. 加载CNIPA IPC中文定义
        self._load_cnipa_ipc_definitions()

        # 2. 加载现有技术词典
        self._load_existing_dictionary()

        # 3. 构建索引
        self._build_indices()

        # 4. 加载向量索引（如果存在）
        self._load_embedding_index()

        self.is_loaded = True
        logger.info(f"✅ 知识图谱加载完成，共{len(self.entities)}个实体，{len(self.relations)}个关系")

    def _load_cnipa_ipc_definitions(self):
        """加载CNIPA IPC中文定义"""
        try:
            with open('/Users/xujian/Athena工作平台/patent-platform/workspace/data/cnipa_ipc_chinese_definitions.json', encoding='utf-8') as f:
                ipc_data = json.load(f)

            # 处理每个部
            sections = ipc_data.get('ipc_definitions', {})
            for section_code, section_data in sections.items():
                section_name = section_data.get('section_name', '')

                # 创建部级别实体
                section_entity = TechEntity(
                    entity_id=f"CNIPA_SECTION_{section_code}",
                    name=section_name,
                    category='section',
                    domain=self._map_ipc_to_domain(section_code),
                    ipc_codes=[section_code],
                    definition=section_data.get('section_description', ''),
                    source='CNIPA',
                    attributes={'level': 'section', 'code': section_code}
                )
                self.add_entity(section_entity)

                # 处理类级别
                classes = section_data.get('classes', {})
                for class_code, class_data in classes.items():
                    class_name = class_data.get('class_name', '')
                    description = class_data.get('description', '')
                    key_terms = class_data.get('key_terms', [])
                    related_tech = class_data.get('related_technologies', [])
                    examples = class_data.get('examples', [])

                    # 创建类级别实体
                    class_entity = TechEntity(
                        entity_id=f"CNIPA_CLASS_{class_code}",
                        name=class_name,
                        alias=key_terms,
                        category='class',
                        domain=self._map_ipc_to_domain(class_code),
                        ipc_codes=[class_code],
                        definition=description,
                        description=f"{description} 相关技术：{', '.join(related_tech)}",
                        source='CNIPA',
                        attributes={
                            'level': 'class',
                            'code': class_code,
                            'related_technologies': related_tech,
                            'examples': examples
                        }
                    )
                    self.add_entity(class_entity)

                    # 创建技术术语实体
                    for term in key_terms:
                        if len(term) > 1:  # 过滤过短的术语
                            term_entity = TechEntity(
                                entity_id=f"CNIPA_TERM_{self._generate_id(term)}",
                                name=term,
                                category='technical_term',
                                domain=self._map_ipc_to_domain(class_code),
                                ipc_codes=[class_code],
                                source='CNIPA',
                                attributes={
                                    'ipc_class': class_code,
                                    'importance': 'high'
                                }
                            )
                            self.add_entity(term_entity)

                    # 创建示例实体
                    for example in examples:
                        example_entity = TechEntity(
                            entity_id=f"CNIPA_EXAMPLE_{self._generate_id(example)}",
                            name=example,
                            category='example',
                            domain=self._map_ipc_to_domain(class_code),
                            ipc_codes=[class_code],
                            source='CNIPA',
                            attributes={
                                'ipc_class': class_code,
                                'type': 'patent_example'
                            }
                        )
                        self.add_entity(example_entity)

                    # 添加关系
                    self.add_relation(TechRelation(
                        relation_id=f"CNIPA_REL_{section_code}_{class_code}",
                        subject=f"CNIPA_SECTION_{section_code}",
                        predicate='contains',
                        object=f"CNIPA_CLASS_{class_code}",
                        source='CNIPA'
                    ))

            logger.info('✅ CNIPA IPC定义加载完成')

        except Exception as e:
            logger.error(f"❌ 加载CNIPA IPC定义失败: {e}")

    def _load_existing_dictionary(self):
        """加载现有技术词典"""
        try:
            from comprehensive_technical_dictionary import get_dictionary_manager
            dict_manager = get_dictionary_manager()

            # 转换词典中的术语
            for term_text, term_info in dict_manager.terms.items():
                entity = TechEntity(
                    entity_id=f"DICT_TERM_{self._generate_id(term_text)}",
                    name=term_text,
                    alias=term_info.synonyms,
                    category=term_info.category,
                    domain=term_info.domain,
                    definition=term_info.definition,
                    source='technical_dictionary',
                    attributes={
                        'importance': term_info.importance,
                        'features': term_info.features,
                        'frequency': term_info.frequency
                    }
                )
                self.add_entity(entity)

            logger.info('✅ 现有技术词典加载完成')

        except Exception as e:
            logger.warning(f"⚠️ 加载现有技术词典失败: {e}")

    def _build_indices(self):
        """构建索引"""
        self.indices = {
            'name': set(),
            'alias': set(),
            'domain': set(),
            'ipc': set(),
            'category': set()
        }

        for entity in self.entities.values():
            self.indices['name'].add(entity.name.lower())
            for alias in entity.alias:
                self.indices['alias'].add(alias.lower())
            self.indices['domain'].add(entity.domain)
            for ipc in entity.ipc_codes:
                self.indices['ipc'].add(ipc)
            self.indices['category'].add(entity.category)

    def _load_embedding_index(self):
        """加载向量索引"""
        try:
            embedding_file = Path(self.storage_path) / 'entity_embeddings.pkl'
            if embedding_file.exists():
                with open(embedding_file, 'rb') as f:
                    self.embedding_index = pickle.load(f)
                logger.info('✅ 向量索引加载完成')
        except Exception as e:
            logger.warning(f"⚠️ 向量索引加载失败: {e}")
            self.embedding_index = None

    def _map_ipc_to_domain(self, ipc_code: str) -> str:
        """映射IPC代码到技术领域"""
        # 基于IPC代码映射到领域
        if ipc_code.startswith('A'):
            if '61' in ipc_code:
                return 'medical'
            return 'human_necessities'
        elif ipc_code.startswith('B'):
            if '23' in ipc_code or '25' in ipc_code:
                return 'mechanical'
            elif '60' in ipc_code:
                return 'automotive'
            return 'operations_transport'
        elif ipc_code.startswith('C'):
            return 'chemical'
        elif ipc_code.startswith('G'):
            if '06F' in ipc_code or '06N' in ipc_code:
                return 'software'
            elif '01' in ipc_code:
                return 'measurement'
            return 'physics'
        elif ipc_code.startswith('H'):
            if '04' in ipc_code:
                return 'communication'
            return 'electronic'
        elif ipc_code.startswith('F'):
            return 'mechanical_engineering'
        elif ipc_code.startswith('E'):
            return 'civil_engineering'
        else:
            return 'unknown'

    def _generate_id(self, text: str) -> str:
        """生成ID"""
        return hashlib.md5(text.encode('utf-8'), usedforsecurity=False).hexdigest()[:16]

    def add_entity(self, entity: TechEntity):
        """添加实体"""
        self.entities[entity.entity_id] = entity
        entity.last_updated = datetime.now()

    def add_relation(self, relation: TechRelation):
        """添加关系"""
        self.relations[relation.relation_id] = relation

    def search_entities(self, query: str, limit: int = 10) -> list[tuple[TechEntity, float]]:
        """搜索实体"""
        query_lower = query.lower()
        results = []

        for entity in self.entities.values():
            score = 0.0

            # 名称匹配
            if query_lower in entity.name.lower():
                score += 1.0

            # 别名匹配
            for alias in entity.alias:
                if query_lower in alias.lower():
                    score += 0.8

            # 描述匹配
            if entity.description and query_lower in entity.description.lower():
                score += 0.5

            # 定义匹配
            if entity.definition and query_lower in entity.definition.lower():
                score += 0.6

            if score > 0:
                results.append((entity, score))

        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def get_entities_by_domain(self, domain: str) -> list[TechEntity]:
        """根据领域获取实体"""
        return [entity for entity in self.entities.values() if entity.domain == domain]

    def get_entities_by_ipc(self, ipc_code: str) -> list[TechEntity]:
        """根据IPC分类获取实体"""
        return [entity for entity in self.entities.values() if ipc_code in entity.ipc_codes]

    def find_related_entities(self, entity_id: str, relation_type: str = None, limit: int = 10) -> list[TechEntity]:
        """查找相关实体"""
        related = []

        for relation in self.relations.values():
            if relation.subject == entity_id:
                if relation_type is None or relation.predicate == relation_type:
                    if relation.object in self.entities:
                        related.append(self.entities[relation.object])
            elif relation.object == entity_id:
                if relation_type is None or relation.predicate == relation_type:
                    if relation.subject in self.entities:
                        related.append(self.entities[relation.subject])

        return related[:limit] if limit > 0 else related

    def get_technology_trends(self, domain: str = None) -> dict[str, list[str]]:
        """获取技术趋势"""
        trends = {
            'emerging_technologies': [],
            'hot_domains': [],
            'cross_domain_innovations': []
        }

        # 分析新兴技术
        for entity in self.entities.values():
            if entity.category == 'technical_term':
                if '智能' in entity.name or 'AI' in entity.name or '人工智能' in entity.name:
                    trends['emerging_technologies'].append(entity.name)

        # 统计热门领域
        domain_counts = {}
        for entity in self.entities.values():
            domain_counts[entity.domain] = domain_counts.get(entity.domain, 0) + 1

        sorted_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)
        trends['hot_domains'] = [domain for domain, count in sorted_domains[:5] if domain != 'unknown']

        # 跨领域创新
        for entity in self.entities.values():
            if len(entity.ipc_codes) > 1:
                # 涉及多个IPC分类，可能是跨领域创新
                trends['cross_domain_innovations'].append({
                    'entity': entity.name,
                    'domains': entity.ipc_codes
                })

        return trends

    def generate_patent_keywords(self, patent_text: str, top_k: int = 20) -> list[tuple[str, float]]:
        """为专利生成关键词"""
        keywords = []

        # 分词
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', patent_text)
        word_freq = {}
        for word in words:
            if len(word) > 1:
                word_freq[word] = word_freq.get(word, 0) + 1

        # 匹配技术术语
        for word, freq in word_freq.items():
            matches = self.search_entities(word, limit=1)
            if matches:
                entity, score = matches[0]
                # 计算权重
                weight = score * freq * (1.2 if entity.category == 'technical_term' else 1.0)
                keywords.append((entity.name, weight))

        # 排序并返回
        keywords.sort(key=lambda x: x[1], reverse=True)
        return keywords[:top_k]

    def build_embeddings(self, model=None):
        """构建实体嵌入向量"""
        logger.info('🔄 构建实体嵌入向量...')

        if model is None:
            # 使用默认的嵌入模型
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

        # 编码所有实体名称和描述
        entity_texts = []
        entity_ids = []

        for entity_id, entity in self.entities.items():
            text = entity.name
            if entity.description:
                text += ' ' + entity.description
            if entity.definition:
                text += ' ' + entity.definition

            entity_texts.append(text)
            entity_ids.append(entity_id)

        # 生成嵌入
        embeddings = model.encode(entity_texts, show_progress_bar=True)

        # 存储嵌入
        for entity_id, embedding in zip(entity_ids, embeddings, strict=False):
            self.entities[entity_id].embedding = embedding

        # 保存到文件
        embedding_file = Path(self.storage_path)
        embedding_file.mkdir(parents=True, exist_ok=True)
        with open(embedding_file / 'entity_embeddings.pkl', 'wb') as f:
            pickle.dump(embeddings, f)

        self.embedding_index = embeddings
        logger.info('✅ 实体嵌入向量构建完成')

    def semantic_search(self, query: str, top_k: int = 10, model=None) -> list[tuple[TechEntity, float]]:
        """语义搜索"""
        if self.embedding_index is None:
            logger.warning('⚠️ 向量索引未构建，使用关键词搜索')
            return self.search_entities(query, top_k)

        # 编码查询
        if model is None:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

        query_embedding = model.encode([query])[0]

        # 计算相似度
        similarities = []
        entity_ids = list(self.entities.keys())

        for i, embedding in enumerate(self.embedding_index):
            # 计算余弦相似度
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            similarities.append((entity_ids[i], similarity))

        # 排序并返回
        similarities.sort(key=lambda x: x[1], reverse=True)

        results = []
        for entity_id, similarity in similarities[:top_k]:
            if entity_id in self.entities:
                results.append((self.entities[entity_id], similarity))

        return results

    def export_knowledge_graph(self, format: str = 'json') -> str:
        """导出知识图谱"""
        export_data = {
            'metadata': {
                'total_entities': len(self.entities),
                'total_relations': len(self.relations),
                'export_time': datetime.now().isoformat(),
                'format': format
            },
            'entities': [],
            'relations': []
        }

        # 导出实体
        for entity in self.entities.values():
            entity_data = {
                'entity_id': entity.entity_id,
                'name': entity.name,
                'alias': entity.alias,
                'category': entity.category,
                'domain': entity.domain,
                'ipc_codes': entity.ipc_codes,
                'definition': entity.definition,
                'description': entity.description,
                'attributes': entity.attributes,
                'confidence': entity.confidence,
                'source': entity.source
            }
            export_data['entities'].append(entity_data)

        # 导出关系
        for relation in self.relations.values():
            relation_data = {
                'relation_id': relation.relation_id,
                'subject': relation.subject,
                'predicate': relation.predicate,
                'object': relation.object,
                'confidence': relation.confidence,
                'evidence': relation.evidence,
                'source': relation.source
            }
            export_data['relations'].append(relation_data)

        # 保存文件
        export_path = Path(self.storage_path)
        export_path.mkdir(parents=True, exist_ok=True)

        filename = f"technical_kg_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
        filepath = export_path / filename

        if format == 'json':
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 知识图谱已导出到: {filepath}")
        return str(filepath)

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        stats = {
            'total_entities': len(self.entities),
            'total_relations': len(self.relations),
            'category_distribution': {},
            'domain_distribution': {},
            'source_distribution': {},
            'ipc_coverage': set()
        }

        for entity in self.entities.values():
            # 类别分布
            stats['category_distribution'][entity.category] = \
                stats['category_distribution'].get(entity.category, 0) + 1

            # 领域分布
            stats['domain_distribution'][entity.domain] = \
                stats['domain_distribution'].get(entity.domain, 0) + 1

            # 来源分布
            stats['source_distribution'][entity.source] = \
                stats['source_distribution'].get(entity.source, 0) + 1

            # IPC覆盖
            for ipc in entity.ipc_codes:
                stats['ipc_coverage'].add(ipc)

        stats['ipc_coverage'] = list(stats['ipc_coverage'])
        stats['ipc_coverage_count'] = len(stats['ipc_coverage'])

        return stats

# 全局实例
_knowledge_graph = None

def get_knowledge_graph() -> AdvancedTechnicalKnowledgeGraph:
    """获取全局知识图谱实例"""
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = AdvancedTechnicalKnowledgeGraph()
        _knowledge_graph.load_knowledge_base()
    return _knowledge_graph

# 演示函数
def test_advanced_knowledge_graph():
    """测试高级技术知识图谱"""
    logger.info('🧪 测试高级技术知识图谱')
    logger.info(str('=' * 80))

    # 初始化知识图谱
    kg = get_knowledge_graph()

    # 显示统计信息
    stats = kg.get_statistics()
    logger.info("\n📊 知识图谱统计:")
    logger.info(f"实体总数: {stats['total_entities']}")
    logger.info(f"关系总数: {stats['total_relations']}")
    logger.info(f"类别分布: {dict(list(stats['category_distribution'].items())[:5])}")
    logger.info(f"领域分布: {dict(list(stats['domain_distribution'].items())[:5])}")
    logger.info(f"IPC覆盖数: {stats['ipc_coverage_count']}")

    # 搜索测试
    logger.info("\n🔍 搜索测试:")
    search_queries = ['深度学习', '医疗诊断', '通信', '控制系统']
    for query in search_queries:
        results = kg.search_entities(query, limit=3)
        logger.info(f"\n查询: {query}")
        for entity, score in results:
            logger.info(f"  • {entity.name} (分数: {score:.2f}, 领域: {entity.domain})")

    # 生成专利关键词
    test_patent = '一种基于深度学习的医疗图像诊断系统，包括神经网络模块和图像处理单元'
    logger.info("\n📝 专利关键词生成测试:")
    logger.info(f"专利文本: {test_patent}")
    keywords = kg.generate_patent_keywords(test_patent, top_k=10)
    logger.info("提取的关键词:")
    for keyword, weight in keywords[:5]:
        logger.info(f"  • {keyword} (权重: {weight:.2f})")

    # 技术趋势
    logger.info("\n📈 技术趋势:")
    trends = kg.get_technology_trends()
    logger.info(f"热门领域: {trends['hot_domains'][:3]}")

if __name__ == '__main__':
    test_advanced_knowledge_graph()
