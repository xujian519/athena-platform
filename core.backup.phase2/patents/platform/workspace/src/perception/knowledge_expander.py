#!/usr/bin/env python3
"""
知识库扩展器
Knowledge Base Expander

扩展专利知识库，增加技术标准、案例和行业知识
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import requests

logger = logging.getLogger(__name__)

class KnowledgeType(Enum):
    """知识类型"""
    PATENT_STANDARD = 'patent_standard'      # 专利标准
    TECHNICAL_SPEC = 'technical_spec'       # 技术规范
    INDUSTRY_CASE = 'industry_case'         # 行业案例
    LEGAL_PRECEDENT = 'legal_precedent'     # 法律判例
    TECH_GLOSSARY = 'tech_glossary'         # 技术术语
    COMPANY_INFO = 'company_info'           # 企业信息
    INVENTOR_PROFILE = 'inventor_profile'   # 发明人档案
    EXPERTISE_AREA = 'expertise_area'       # 专业领域

class DataSource(Enum):
    """数据来源"""
    CNIPA = 'cnipa'                         # 国家知识产权局
    WIPO = 'wipo'                           # 世界知识产权组织
    USPTO = 'uspto'                         # 美国专利商标局
    TECH_STANDARDS = 'tech_standards'       # 技术标准组织
    INDUSTRY_REPORTS = 'industry_reports'   # 行业报告
    ACADEMIC_PAPERS = 'academic_papers'     # 学术论文
    CUSTOM_INPUT = 'custom_input'           # 自定义输入

@dataclass
class KnowledgeEntity:
    """知识实体"""
    entity_id: str
    title: str
    content: str
    knowledge_type: KnowledgeType
    source: DataSource
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    related_entities: List[str] = field(default_factory=list)

@dataclass
class KnowledgeRelation:
    """知识关系"""
    relation_id: str
    source_entity: str
    target_entity: str
    relation_type: str
    strength: float = 1.0
    description: str = ''
    evidence: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

class TechnicalStandardsLoader:
    """技术标准加载器"""

    def __init__(self):
        self.standards_db = {}
        self.loaders = {
            DataSource.TECH_STANDARDS: self._load_tech_standards,
            DataSource.CUSTOM_INPUT: self._load_custom_standards
        }

    async def load_standards(self, source: DataSource) -> List[KnowledgeEntity]:
        """加载技术标准"""
        loader = self.loaders.get(source, self._load_default)
        return await loader()

    async def _load_tech_standards(self) -> List[KnowledgeEntity]:
        """加载技术标准数据"""
        standards = []

        # 示例：GB标准
        gb_standards = [
            {
                'code': 'GB/T 150.1-2011',
                'title': '压力容器 第1部分：通用要求',
                'category': '压力容器',
                'content': '规定了压力容器的设计、制造、检验和验收要求'
            },
            {
                'code': 'GB/T 151-2014',
                'title': '热交换器',
                'category': '换热设备',
                'content': '规定了管壳式热交换器的设计、制造、检验要求'
            },
            {
                'code': 'GB/T 20801-2006',
                'title': '压力管道规范 工业管道',
                'category': '压力管道',
                'content': '规定了工业压力管道的设计、制造、安装、检验要求'
            }
        ]

        for std in gb_standards:
            entity = KnowledgeEntity(
                entity_id=f"standard_{std['code']}",
                title=std['title'],
                content=std['content'],
                knowledge_type=KnowledgeType.PATENT_STANDARD,
                source=DataSource.TECH_STANDARDS,
                tags=[std['category'], '国家标准', '技术规范'],
                metadata={
                    'code': std['code'],
                    'category': std['category'],
                    'type': 'GB标准'
                }
            )
            standards.append(entity)

        logger.info(f"✅ 加载技术标准: {len(standards)} 个")
        return standards

    async def _load_custom_standards(self) -> List[KnowledgeEntity]:
        """加载自定义标准"""
        standards = []

        # 从文件加载
        custom_standards_file = Path('data/custom_standards.json')
        if custom_standards_file.exists():
            try:
                with open(custom_standards_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for item in data:
                    entity = KnowledgeEntity(
                        entity_id=item.get('id', f"custom_{hashlib.md5(item['title'].encode('utf-8'), usedforsecurity=False).hexdigest()}"),
                        title=item['title'],
                        content=item['content'],
                        knowledge_type=KnowledgeType.TECHNICAL_SPEC,
                        source=DataSource.CUSTOM_INPUT,
                        tags=item.get('tags', []),
                        metadata=item.get('metadata', {})
                    )
                    standards.append(entity)

                logger.info(f"✅ 加载自定义标准: {len(standards)} 个")

            except Exception as e:
                logger.error(f"❌ 加载自定义标准失败: {str(e)}")

        return standards

    async def _load_default(self) -> List[KnowledgeEntity]:
        """默认加载"""
        return []

class IndustryCasesLoader:
    """行业案例加载器"""

    def __init__(self):
        self.case_db = {}

    async def load_industry_cases(self) -> List[KnowledgeEntity]:
        """加载行业案例"""
        cases = []

        # 典型专利案例
        patent_cases = [
            {
                'title': '高通诉苹果专利侵权案',
                'summary': '涉及移动通信标准必要专利（SEP）的许可费率争议',
                'keywords': ['标准必要专利', '许可费率', 'FRAND原则', '移动通信'],
                'outcome': '法院裁定按FRAND原则确定许可费率'
            },
            {
                'title': '华为诉三星专利侵权案',
                'summary': '涉及4G通信专利的跨境侵权诉讼',
                'keywords': ['4G专利', '跨境诉讼', '专利池', '交叉许可'],
                'outcome': '达成和解协议'
            },
            {
                'title': '宁德时代专利保护案例',
                'summary': '动力电池技术专利布局与保护策略',
                'keywords': ['动力电池', '专利布局', '技术壁垒', '知识产权保护'],
                'outcome': '成功建立技术壁垒'
            }
        ]

        for case in patent_cases:
            entity = KnowledgeEntity(
                entity_id=f"case_{hashlib.md5(case['title'].encode('utf-8'), usedforsecurity=False).hexdigest()[:16]}",
                title=case['title'],
                content=case['summary'],
                knowledge_type=KnowledgeType.INDUSTRY_CASE,
                source=DataSource.INDUSTRY_REPORTS,
                tags=case['keywords'],
                metadata={
                    'outcome': case['outcome'],
                    'case_type': '专利诉讼',
                    'importance': 'high'
                }
            )
            cases.append(entity)

        logger.info(f"✅ 加载行业案例: {len(cases)} 个")
        return cases

class KnowledgeExpander:
    """知识库扩展器"""

    def __init__(self):
        self.knowledge_base = {}
        self.relations = []
        self.entity_index = {}  # 实体索引
        self.tag_index = {}     # 标签索引
        self.lock = threading.RLock()

        # 初始化加载器
        self.standards_loader = TechnicalStandardsLoader()
        self.cases_loader = IndustryCasesLoader()

        # 统计信息
        self.stats = {
            'total_entities': 0,
            'total_relations': 0,
            'knowledge_types': {},
            'data_sources': {}
        }

        logger.info('🚀 知识库扩展器初始化完成')

    async def expand_knowledge_base(self, sources: Optional[List[DataSource] = None) -> bool:
        """扩展知识库"""
        sources = sources or [
            DataSource.TECH_STANDARDS,
            DataSource.INDUSTRY_REPORTS,
            DataSource.CUSTOM_INPUT
        ]

        try:
            logger.info('📚 开始扩展知识库...')

            all_entities = []

            # 加载技术标准
            if DataSource.TECH_STANDARDS in sources:
                standards = await self.standards_loader.load_standards(DataSource.TECH_STANDARDS)
                all_entities.extend(standards)

            # 加载行业案例
            if DataSource.INDUSTRY_REPORTS in sources:
                cases = await self.cases_loader.load_industry_cases()
                all_entities.extend(cases)

            # 加载自定义输入
            if DataSource.CUSTOM_INPUT in sources:
                customs = await self.standards_loader.load_standards(DataSource.CUSTOM_INPUT)
                all_entities.extend(customs)

            # 扩展技术术语
            tech_terms = await self._expand_technical_terms()
            all_entities.extend(tech_terms)

            # 添加到知识库
            for entity in all_entities:
                self._add_entity(entity)

            # 构建关系
            await self._build_relations()

            # 更新统计
            self._update_statistics()

            logger.info(f"✅ 知识库扩展完成: {len(all_entities)} 个实体")
            return True

        except Exception as e:
            logger.error(f"❌ 知识库扩展失败: {str(e)}")
            return False

    async def _expand_technical_terms(self) -> List[KnowledgeEntity]:
        """扩展技术术语"""
        terms = []

        # 常见技术术语
        tech_terms = [
            {
                'term': '精馏塔',
                'definition': '用于分离液体混合物的化工设备',
                'category': '化工设备',
                'related_concepts': ['传质', '分离', '提纯']
            },
            {
                'term': '反应器',
                'definition': '进行化学反应的设备或系统',
                'category': '反应设备',
                'related_concepts': ['化学反应', '催化剂', '转化率']
            },
            {
                'term': '换热器',
                'definition': '实现热量传递的设备',
                'category': '换热设备',
                'related_concepts': ['传热', '热交换', '节能']
            },
            {
                'term': '压缩机',
                'definition': '提高气体压力的机械设备',
                'category': '流体机械',
                'related_concepts': ['气体压缩', '压力提升', '能量转换']
            }
        ]

        for term_info in tech_terms:
            entity = KnowledgeEntity(
                entity_id=f"term_{term_info['term']}",
                title=term_info['term'],
                content=f"{term_info['definition']}。相关概念：{', '.join(term_info['related_concepts'])}",
                knowledge_type=KnowledgeType.TECH_GLOSSARY,
                source=DataSource.CUSTOM_INPUT,
                tags=[term_info['category'], '技术术语'] + term_info['related_concepts'],
                metadata={
                    'category': term_info['category'],
                    'definition': term_info['definition'],
                    'related_concepts': term_info['related_concepts']
                }
            )
            terms.append(entity)

        logger.info(f"✅ 扩展技术术语: {len(terms)} 个")
        return terms

    def _add_entity(self, entity: KnowledgeEntity):
        """添加知识实体"""
        with self.lock:
            self.knowledge_base[entity.entity_id] = entity

            # 更新索引
            self.entity_index[entity.title] = entity.entity_id
            for tag in entity.tags:
                if tag not in self.tag_index:
                    self.tag_index[tag] = []
                self.tag_index[tag].append(entity.entity_id)

    async def _build_relations(self):
        """构建知识关系"""
        relations = []

        for entity_id, entity in self.knowledge_base.items():
            # 基于标签构建关系
            for tag in entity.tags:
                related_entities = self.tag_index.get(tag, [])
                for related_id in related_entities:
                    if related_id != entity_id:
                        # 检查是否已存在关系
                        existing = any(
                            (r.source_entity == entity_id and r.target_entity == related_id) or
                            (r.source_entity == related_id and r.target_entity == entity_id)
                            for r in relations
                        )
                        if not existing:
                            relation = KnowledgeRelation(
                                relation_id=f"rel_{entity_id}_{related_id}_{tag}",
                                source_entity=entity_id,
                                target_entity=related_id,
                                relation_type='related_by_tag',
                                strength=0.8,
                                description=f"通过标签 '{tag}' 关联",
                                evidence=[f"共同标签: {tag}"]
                            )
                            relations.append(relation)

            # 基于内容相似性构建关系
            for other_id, other_entity in self.knowledge_base.items():
                if other_id != entity_id:
                    similarity = await self._calculate_content_similarity(
                        entity.content, other_entity.content
                    )
                    if similarity > 0.6:  # 相似度阈值
                        relation = KnowledgeRelation(
                            relation_id=f"sim_{entity_id}_{other_id}",
                            source_entity=entity_id,
                            target_entity=other_id,
                            relation_type='content_similarity',
                            strength=similarity,
                            description=f"内容相似度: {similarity:.2f}",
                            evidence=[f"相似度计算: {similarity:.2f}"]
                        )
                        relations.append(relation)

        self.relations = relations
        logger.info(f"✅ 构建知识关系: {len(relations)} 个")

    async def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """计算内容相似度"""
        try:
            # 简单的Jaccard相似度
            words1 = set(re.findall(r'\w+', content1))
            words2 = set(re.findall(r'\w+', content2))

            intersection = words1.intersection(words2)
            union = words1.union(words2)

            if len(union) == 0:
                return 0.0

            return len(intersection) / len(union)

        except Exception as e:
            logger.error(f"❌ 相似度计算失败: {str(e)}")
            return 0.0

    def _update_statistics(self):
        """更新统计信息"""
        self.stats['total_entities'] = len(self.knowledge_base)
        self.stats['total_relations'] = len(self.relations)

        # 按知识类型统计
        self.stats['knowledge_types'] = {}
        for entity in self.knowledge_base.values():
            ktype = entity.knowledge_type.value
            self.stats['knowledge_types'][ktype] = self.stats['knowledge_types'].get(ktype, 0) + 1

        # 按数据源统计
        self.stats['data_sources'] = {}
        for entity in self.knowledge_base.values():
            source = entity.source.value
            self.stats['data_sources'][source] = self.stats['data_sources'].get(source, 0) + 1

    def search_knowledge(self, query: str, limit: int = 10) -> List[KnowledgeEntity]:
        """搜索知识"""
        results = []

        query_lower = query.lower()
        query_terms = query_lower.split()

        for entity in self.knowledge_base.values():
            score = 0.0

            # 标题匹配
            if query_lower in entity.title.lower():
                score += 2.0

            # 内容匹配
            content_lower = entity.content.lower()
            for term in query_terms:
                if term in content_lower:
                    score += 1.0

            # 标签匹配
            for tag in entity.tags:
                if query_lower in tag.lower():
                    score += 1.5

            if score > 0:
                # 添加到结果
                results.append((entity, score))

        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)

        # 返回前N个
        return [entity for entity, _ in results[:limit]]

    def get_related_entities(self, entity_id: str, max_depth: int = 2) -> List[KnowledgeEntity]:
        """获取相关实体"""
        related = set()
        visited = set()
        queue = [(entity_id, 0)]

        while queue and len(related) < 20:  # 限制数量
            current_id, depth = queue.pop(0)

            if current_id in visited or depth > max_depth:
                continue

            visited.add(current_id)

            # 查找直接关系
            for relation in self.relations:
                if relation.source_entity == current_id:
                    if relation.target_entity not in visited:
                        related.add(relation.target_entity)
                        if depth < max_depth:
                            queue.append((relation.target_entity, depth + 1))
                elif relation.target_entity == current_id:
                    if relation.source_entity not in visited:
                        related.add(relation.source_entity)
                        if depth < max_depth:
                            queue.append((relation.source_entity, depth + 1))

        # 转换为实体对象
        return [
            self.knowledge_base[eid]
            for eid in related
            if eid in self.knowledge_base
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            'tag_distribution': {
                tag: len(entities)
                for tag, entities in self.tag_index.items()
            }
        }

    def export_knowledge_base(self, output_path: str):
        """导出知识库"""
        try:
            export_data = {
                'entities': [
                    {
                        'entity_id': entity.entity_id,
                        'title': entity.title,
                        'content': entity.content,
                        'knowledge_type': entity.knowledge_type.value,
                        'source': entity.source.value,
                        'tags': entity.tags,
                        'metadata': entity.metadata,
                        'confidence': entity.confidence,
                        'created_at': entity.created_at.isoformat(),
                        'updated_at': entity.updated_at.isoformat(),
                        'version': entity.version,
                        'related_entities': entity.related_entities
                    }
                    for entity in self.knowledge_base.values()
                ],
                'relations': [
                    {
                        'relation_id': relation.relation_id,
                        'source_entity': relation.source_entity,
                        'target_entity': relation.target_entity,
                        'relation_type': relation.relation_type,
                        'strength': relation.strength,
                        'description': relation.description,
                        'evidence': relation.evidence,
                        'created_at': relation.created_at.isoformat()
                    }
                    for relation in self.relations
                ],
                'statistics': self.stats
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 知识库已导出到: {output_path}")

        except Exception as e:
            logger.error(f"❌ 知识库导出失败: {str(e)}")

# 全局扩展器实例
knowledge_expander = KnowledgeExpander()

# 测试代码
if __name__ == '__main__':
    import asyncio

    async def test_knowledge_expander():
        """测试知识库扩展器"""
        logger.info('📚 测试知识库扩展器...')

        # 扩展知识库
        success = await knowledge_expander.expand_knowledge_base()
        logger.info(f"  知识库扩展: {'成功' if success else '失败'}")

        # 获取统计信息
        stats = knowledge_expander.get_statistics()
        logger.info(f"  实体总数: {stats['total_entities']}")
        logger.info(f"  关系总数: {stats['total_relations']}")
        logger.info(f"  知识类型: {list(stats['knowledge_types'].keys())}")

        # 搜索测试
        results = knowledge_expander.search_knowledge('精馏')
        logger.info(f"  搜索结果: {len(results)} 个")

        # 获取相关实体
        if results:
            related = knowledge_expander.get_related_entities(results[0].entity_id)
            logger.info(f"  相关实体: {len(related)} 个")

        # 导出知识库
        knowledge_expander.export_knowledge_base(
            'patent-platform/workspace/data/expanded_knowledge_base.json'
        )

        return True

    # 运行测试
    result = asyncio.run(test_knowledge_expander())
    logger.info(f"\n🎯 知识库扩展器测试: {'成功' if result else '失败'}")