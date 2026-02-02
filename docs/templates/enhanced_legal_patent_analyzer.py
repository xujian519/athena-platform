#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版法律专利分析器
专门支持实体关系提取和法律场景分析
包括无效宣告、侵权诉讼、新创性评估、FTO分析
"""

import json
import logging
import re
import uuid
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class RelationshipType(Enum):
    """关系类型枚举"""
    STRUCTURAL = '结构关系'
    FUNCTIONAL = '功能关系'
    SPATIAL = '空间关系'
    MATERIAL = '材料关系'
    CONNECTION = '连接关系'
    POSITION = '位置关系'
    CONTAINMENT = '包含关系'
    ATTACHMENT = '附着关系'
    CONTACT = '接触关系'
    DIMENSIONAL = '尺寸关系'
    ORIENTATION = '方向关系'
    MOVEMENT = '运动关系'

class LegalScenario(Enum):
    """法律场景枚举"""
    INVALIDITY = '无效宣告'
    INFRINGEMENT = '侵权诉讼'
    NOVELTY = '新颖性评估'
    CREATIVITY = '创造性评估'
    FTO = '技术自由实施'
    LICENSING = '许可谈判'
    DUE_DILIGENCE = '技术尽职调查'

@dataclass
class Entity:
    """实体数据类"""
    id: str
    name: str
    type: str
    reference_number: str | None = None
    attributes: Dict[str, Any] = None
    synonyms: Optional[List[str] = None
    source_features: Optional[List[str] = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}
        if self.synonyms is None:
            self.synonyms = []
        if self.source_features is None:
            self.source_features = []

@dataclass
class Relationship:
    """关系数据类"""
    id: str
    subject: str
    object: str
    type: RelationshipType
    description: str
    confidence: float = 1.0
    strength: str = 'medium'
    source_features: Optional[List[str] = None
    legal_implications: Dict[str, Any] = None

    def __post_init__(self):
        if self.source_features is None:
            self.source_features = []
        if self.legal_implications is None:
            self.legal_implications = {}

class EnhancedLegalPatentAnalyzer:
    """增强版法律专利分析器"""

    def __init__(self):
        """初始化分析器"""
        # 实体识别模式库
        self.entity_patterns = {
            '部件': [
                r"([^，。；:]+?)本体",
                r"([^，。；:]+?]部件",
                r"([^，。；:]+?]组件",
                r"([^，。；:]+?]装置",
                r"([^，。；:]+?]器",
                r"([^，。；:]+?]机构",
                r"([^，。；:]+?]元件",
                r"([^，。；:]+?]单元",
                r"([^，。；:]+?]模块"
            ],
            '材料': [
                r"([^，。；:]+?]板",
                r"([^，。；:]+?]层",
                r"([^，。；:]+?]膜",
                r"([^，。；:]+?]材料",
                r"([^，。；:]+?]涂层",
                r"([^，。；:]+?]合金",
                r"([^，。；:]+?]塑料",
                r"([^，。；:]+?]橡胶",
                r"([^，。；:]+?]陶瓷"
            ],
            '位置': [
                r"([^，。；:]+?]区域",
                r"([^，。；:]+?]位置",
                r"([^，。；:]+?]部位",
                r"([^，。；:]+?]端部",
                r"([^，。；:]+?]侧部",
                r"([^，。；:]+?]中部",
                r"([^，。；:]+?]顶部",
                r"([^，。；:]+?]底部",
                r"([^，。；:]+?]表面"
            ],
            '结构': [
                r"([^，。；:]+?]槽",
                r"([^，。；:]+?]孔",
                r"([^，。；:]+?]口",
                r"([^，。；:]+?]腔",
                r"([^，。；:]+?]槽",
                r"([^，。；:]+?]凸起",
                r"([^，。；:]+?]凹陷",
                r"([^，。；:]+?]缝隙",
                r"([^，。；:]+?]间隙"
            ]
        }

        # 关系识别模式库
        self.relationship_patterns = {
            RelationshipType.STRUCTURAL: [
                r"([^，。；:]+?)由([^，。；:]+?]构成",
                r"([^，。；:]+?]包括([^，。；:]+?)",
                r"([^，。；:]+?]包含([^，。；:]+?)",
                r"([^，。；:]+?]具有([^，。；:]+?)"
            ],
            RelationshipType.CONNECTION: [
                r"([^，。；:]+?)连接([^，。；:]+?)",
                r"([^，。；:]+?]固定([^，。；:]+?)",
                r"([^，。；:]+?]安装([^，。；:]+?)",
                r"([^，。；:]+?]装配([^，。；:]+?)"
            ],
            RelationshipType.CONTACT: [
                r"([^，。；:]+?)接触([^，。；:]+?)",
                r"([^，。；:]+?]与([^，。；:]+?)接触",
                r"([^，。；:]+?]贴合([^，。；:]+?)",
                r"([^，。；:]+?]紧贴([^，。；:]+?)"
            ],
            RelationshipType.SPATIAL: [
                r"([^，。；:]+?]位于([^，。；:]+?)",
                r"([^，。；:]+?]设置于([^，。；:]+?)",
                r"([^，。；:]+?]布置在([^，。；:]+?)",
                r"([^，。；:]+?]形成于([^，。；:]+?)"
            ],
            RelationshipType.DIMENSIONAL: [
                r"([^，。；:]+?)(大于|小于|等于|宽于|窄于|高于|低于)([^，。；:]+?)",
                r"([^，。；:]+?]宽度(.+)([^，。；:]+?]宽度",
                r"([^，。；:]+?]长度(.+)([^，。；:]+?]长度",
                r"([^，。；:]+?]厚度(.+)([^，。；:]+?]厚度"
            ],
            RelationshipType.MATERIAL: [
                r"([^，。；:]+?]由([^，。；:]+?]制成",
                r"([^，。；:]+?]采用([^，。；:]+?]材料",
                r"([^，。；:]+?]材质为([^，。；:]+?)",
                r"([^，。；:]+?]为([^，。；:]+?]材质"
            ]
        }

        # 法律场景特定分析器
        self.legal_analyzers = {
            LegalScenario.INVALIDITY: self._analyze_for_invalidity,
            LegalScenario.INFRINGEMENT: self._analyze_for_infringement,
            LegalScenario.Novelty: self._analyze_for_novelty,
            LegalScenario.CREATIVITY: self._analyze_for_creativity,
            LegalScenario.FTO: self._analyze_for_fto
        }

    def extract_entities_and_relationships(self, claim_text: str, claim_number: int = 1) -> Dict[str, Any]:
        """
        提取实体和关系的核心方法

        Args:
            claim_text: 权利要求文本
            claim_number: 权利要求编号

        Returns:
            包含实体和关系的分析结果
        """
        # 第一步：提取技术特征
        features = self._extract_technical_features(claim_text)

        # 第二步：从特征中识别实体
        entities = self._extract_entities_from_features(features)

        # 第三步：分析实体间关系
        relationships = self._analyze_relationships_from_features(features, entities)

        # 第四步：构建关系网络
        relationship_network = self._build_relationship_network(entities, relationships)

        # 第五步：法律场景分析
        legal_analysis = self._perform_legal_scenarios_analysis(entities, relationships)

        return {
            'claim_info': {
                'claim_number': claim_number,
                'claim_text': claim_text
            },
            'features': features,
            'entities': [self._entity_to_dict(e) for e in entities],
            'relationships': [self._relationship_to_dict(r) for r in relationships],
            'relationship_network': relationship_network,
            'legal_analysis': legal_analysis,
            'extraction_statistics': self._calculate_statistics(entities, relationships)
        }

    def _extract_technical_features(self, claim_text: str) -> List[Dict[str, Any]]:
        """提取技术特征"""
        # 去除权利要求编号
        clean_text = re.sub(r"^\d+[、.]\s*', '", claim_text)

        # 按标点符号分割
        features = []
        segments = self._split_by_punctuation(clean_text)

        for i, segment in enumerate(segments):
            if segment.strip():
                feature = {
                    'id': f"F_{i+1}_{uuid.uuid4().hex[:6]}",
                    'sequence': i + 1,
                    'text': segment.strip(),
                    'punctuation': self._identify_punctuation(segment, segments, i),
                    'category': self._categorize_feature(segment.strip()),
                    'importance': self._assess_importance(segment.strip(), i, segments)
                }
                features.append(feature)

        return features

    def _split_by_punctuation(self, text: str) -> List[str]:
        """按标点符号分割文本"""
        splitters = ['。', '，', '：', '；']
        segments = [text]

        for splitter in splitters:
            new_segments = []
            for segment in segments:
                if splitter in segment:
                    parts = segment.split(splitter)
                    for i, part in enumerate(parts):
                        if part.strip():
                            new_segments.append(part.strip() + (splitter if i < len(parts) - 1 else ''))
                else:
                    new_segments.append(segment)
            segments = new_segments
            if len(segments) > 1:
                break

        return segments

    def _identify_punctuation(self, segment: str, all_segments: List[str], index: int) -> str:
        """识别分割标点"""
        if segment.endswith(('。', '，', '：', '；')):
            return segment[-1]
        elif index < len(all_segments) - 1:
            next_segment = all_segments[index + 1]
            if next_segment.startswith(('。', '，', '：', '；')):
                return next_segment[0]
        return 'none'

    def _categorize_feature(self, feature_text: str) -> str:
        """特征分类"""
        categories = {
            '结构特征': ['包括', '设置有', '安装', '固定', '连接'],
            '功能特征': ['能够', '用于', '实现', '具有', '可'],
            '位置特征': ['位于', '设置于', '位置', '区域', '部位'],
            '参数特征': ['mm', 'cm', '℃', '°C', 'mm²', '比例'],
            '材料特征': ['铜', '铝', '钢', '铁', '塑料', '橡胶', '陶瓷'],
            '方法特征': ['步骤', '方法', '工艺', '过程', '操作']
        }

        for category, keywords in categories.items():
            if any(keyword in feature_text for keyword in keywords):
                return category
        return '其他特征'

    def _assess_importance(self, feature_text: str, index: int, segments: List[str]) -> str:
        """评估特征重要性"""
        if index == 0:
            return '核心特征'
        if '其特征' in feature_text or '还包括' in feature_text:
            return '重要特征'
        if re.search(r"（\d+）", feature_text):
            return '重要特征'
        return '一般特征'

    def _extract_entities_from_features(self, features: List[Dict[str, Any]]) -> List[Entity]:
        """从特征中提取实体"""
        entities = []
        entity_map = {}  # 名称到实体的映射
        entity_counter = 1

        for feature in features:
            feature_text = feature['text']

            # 提取附图标记
            ref_match = re.search(r"（(\d+)）", feature_text)
            ref_number = ref_match.group(1) if ref_match else None

            # 识别实体
            for entity_type, patterns in self.entity_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, feature_text)
                    for match in matches:
                        entity_name = match.strip()
                        if len(entity_name) > 1:
                            if entity_name not in entity_map:
                                entity_id = f"E_{entity_counter:03d}"

                                # 提取实体属性
                                attributes = self._extract_entity_attributes(feature_text, entity_name)

                                entity = Entity(
                                    id=entity_id,
                                    name=entity_name,
                                    type=entity_type,
                                    reference_number=ref_number,
                                    attributes=attributes,
                                    source_features=[feature['id']]
                                )

                                entities.append(entity)
                                entity_map[entity_name] = entity
                                entity_counter += 1
                            else:
                                # 更新现有实体
                                entity = entity_map[entity_name]
                                entity.source_features.append(feature['id'])
                                if ref_number and not entity.reference_number:
                                    entity.reference_number = ref_number

        return entities

    def _extract_entity_attributes(self, text: str, entity_name: str) -> Dict[str, str]:
        """提取实体属性"""
        attributes = {}

        # 尺寸属性
        size_patterns = [
            f"{entity_name}[^，。；:]*?(\\d+\\s*[mmcmµm])",
            f"{entity_name}[^，。；:]*?(\\d+\\.\\d+\\s*[mmcmµm])"
        ]
        for pattern in size_patterns:
            match = re.search(pattern, text)
            if match:
                attributes['size'] = match.group(1)
                break

        # 形状属性
        shapes = ['圆形', '方形', '矩形', '球形', '柱形', '锥形', '环形']
        for shape in shapes:
            if shape in text:
                attributes['shape'] = shape
                break

        # 材料属性
        materials = ['铜', '铝', '钢', '铁', '塑料', '橡胶', '陶瓷', '不锈钢']
        for material in materials:
            if material in text:
                attributes['material'] = material
                break

        return attributes

    def _analyze_relationships_from_features(self, features: List[Dict[str, Any]], entities: List[Entity]) -> List[Relationship]:
        """分析实体间关系"""
        relationships = []
        entity_name_to_id = {e.name: e.id for e in entities}
        relationship_counter = 1

        for feature in features:
            feature_text = feature['text']

            for rel_type, patterns in self.relationship_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, feature_text)
                    for match in matches:
                        if len(match) >= 2:
                            subject_name = match[0].strip()
                            object_name = match[1].strip()

                            subject_id = entity_name_to_id.get(subject_name)
                            object_id = entity_name_to_id.get(object_name)

                            if subject_id and object_id and subject_id != object_id:
                                # 评估关系强度
                                strength = self._assess_relationship_strength(feature_text, rel_type)

                                # 生成法律含义
                                legal_implications = self._generate_legal_implications(rel_type, feature_text)

                                relationship = Relationship(
                                    id=f"R_{relationship_counter:03d}",
                                    subject=subject_id,
                                    object=object_id,
                                    type=rel_type,
                                    description=feature_text,
                                    confidence=1.0 if subject_id and object_id else 0.7,
                                    strength=strength,
                                    source_features=[feature['id']],
                                    legal_implications=legal_implications
                                )

                                relationships.append(relationship)
                                relationship_counter += 1

        return relationships

    def _assess_relationship_strength(self, text: str, rel_type: RelationshipType) -> str:
        """评估关系强度"""
        strong_indicators = ['固定', '牢固', '紧密', '完全']
        weak_indicators = ['可', '活动', '松', '临时']

        for indicator in strong_indicators:
            if indicator in text:
                return '强关系'

        for indicator in weak_indicators:
            if indicator in text:
                return '弱关系'

        return '中等关系'

    def _generate_legal_implications(self, rel_type: RelationshipType, text: str) -> Dict[str, Any]:
        """生成关系的法律含义"""
        implications = {
            'essential_for_patentability': False,
            'affects_infringement_analysis': False,
            'influences_claim_scope': False,
            'relevant_for_equivalence': False
        }

        # 根据关系类型设定法律含义
        if rel_type == RelationshipType.STRUCTURAL:
            implications.update({
                'essential_for_patentability': True,
                'influences_claim_scope': True,
                'notes': '结构关系是专利保护的核心要素'
            })
        elif rel_type == RelationshipType.CONNECTION:
            implications.update({
                'affects_infringement_analysis': True,
                'relevant_for_equivalence': True,
                'notes': '连接关系影响侵权判断和等同认定'
            })
        elif rel_type == RelationshipType.DIMENSIONAL:
            implications.update({
                'affects_infringement_analysis': True,
                'relevant_for_equivalence': False,
                'notes': '尺寸关系通常是精确技术特征，不适用等同原则'
            })
        elif rel_type == RelationshipType.CONTACT:
            implications.update({
                'essential_for_patentability': True,
                'affects_infringement_analysis': True,
                'notes': '接触关系直接影响技术方案实现'
            })

        return implications

    def _build_relationship_network(self, entities: List[Entity], relationships: List[Relationship]) -> Dict[str, Any]:
        """构建关系网络"""
        nodes = []
        edges = []

        # 构建节点
        for entity in entities:
            node = {
                'id': entity.id,
                'name': entity.name,
                'type': entity.type,
                'reference_number': entity.reference_number,
                'attributes': entity.attributes,
                'importance': len(entity.source_features)
            }
            nodes.append(node)

        # 构建边
        for rel in relationships:
            edge = {
                'id': rel.id,
                'source': rel.subject,
                'target': rel.object,
                'type': rel.type.value,
                'strength': rel.strength,
                'confidence': rel.confidence,
                'legal_implications': rel.legal_implications
            }
            edges.append(edge)

        # 计算网络指标
        centrality = self._calculate_network_centrality(nodes, edges)

        return {
            'nodes': nodes,
            'edges': edges,
            'metrics': {
                'node_count': len(nodes),
                'edge_count': len(edges),
                'network_density': len(edges) / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0,
                'centrality': centrality
            }
        }

    def _calculate_network_centrality(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, Any]:
        """计算网络中心性"""
        degree_count = defaultdict(int)

        for edge in edges:
            degree_count[edge['source']] += 1
            degree_count[edge['target']] += 1

        max_degree = max(degree_count.values()) if degree_count else 1

        degree_centrality = {}
        for node in nodes:
            node_id = node['id']
            degree_centrality[node_id] = degree_count.get(node_id, 0) / max_degree

        # 识别关键节点（中心性最高的几个）
        sorted_nodes = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)
        key_nodes = sorted_nodes[:min(3, len(sorted_nodes))]

        return {
            'degree_centrality': degree_centrality,
            'key_nodes': [{'id': nid, 'centrality': score} for nid, score in key_nodes]
        }

    def _perform_legal_scenarios_analysis(self, entities: List[Entity], relationships: List[Relationship]) -> Dict[str, Any]:
        """执行法律场景分析"""
        analysis_results = {}

        for scenario in LegalScenario:
            if scenario in self.legal_analyzers:
                analysis_results[scenario.value] = self.legal_analyzers[scenario](entities, relationships)

        return analysis_results

    def _analyze_for_invalidity(self, entities: List[Entity], relationships: List[Relationship]) -> Dict[str, Any]:
        """无效宣告场景分析"""
        # 识别核心要素
        core_entities = [e for e in entities if len(e.source_features) > 1]
        essential_relationships = [r for r in relationships if r.legal_implications.get('essential_for_patentability', False)]

        # 识别可能的无效点
        potential_invalidity_points = []
        for entity in core_entities:
            if entity.type == '部件' and not entity.reference_number:
                potential_invalidity_points.append({
                    'type': '模糊的技术特征',
                    'entity': entity.name,
                    'reason': '核心部件缺乏附图标记，可能存在保护范围不明确'
                })

        return {
            'core_entities_count': len(core_entities),
            'essential_relationships_count': len(essential_relationships),
            'potential_invalidity_points': potential_invalidity_points,
            'invalidity_defense_strategies': [
                '强调技术方案的创新性',
                '提供详细的技术实施例',
                '论证技术特征的必要性'
            ]
        }

    def _analyze_for_infringement(self, entities: List[Entity], relationships: List[Relationship]) -> Dict[str, Any]:
        """侵权诉讼场景分析"""
        # 识别侵权关键要素
        infringement_key_elements = []
        for rel in relationships:
            if rel.legal_implications.get('affects_infringement_analysis', False):
                infringement_key_elements.append({
                    'relationship': f"{rel.type.value}: {rel.description}",
                    'strength': rel.strength,
                    'relevant_for_equivalence': rel.legal_implications.get('relevant_for_equivalence', False)
                })

        # 分析保护范围
        protection_scope = {
            'clearly_defined_entities': len([e for e in entities if e.reference_number]),
            'ambiguous_entities': len([e for e in entities if not e.reference_number]),
            'strong_relationships': len([r for r in relationships if r.strength == '强关系'])
        }

        return {
            'infringement_key_elements': infringement_key_elements,
            'protection_scope_analysis': protection_scope,
            'infringement_detection_focus': [
                '检查被诉产品是否包含所有核心实体',
                '分析实体间关系是否相同或等同',
                '评估尺寸参数是否在保护范围内'
            ],
            'defense_strategies': [
                '主张现有技术抗辩',
                '论证技术特征不同',
                '适用禁止反悔原则'
            ]
        }

    def _analyze_for_novelty(self, entities: List[Entity], relationships: List[Relationship]) -> Dict[str, Any]:
        """新颖性分析场景"""
        # 识别独特技术特征
        unique_combinations = []
        for rel in relationships:
            if rel.confidence > 0.8:
                unique_combinations.append({
                    'combination': f"{rel.type.value}",
                    'description': rel.description,
                    'confidence': rel.confidence
                })

        return {
            'novelty_key_points': unique_combinations,
            'prior_art_search_focus': [
                '相同实体组合的技术方案',
                '相似的结构关系',
                '等同的功能实现'
            ],
            'novelty_assertion_points': [
                '独特的实体组合',
                '创新的结构关系',
                '特定的参数配置'
            ]
        }

    def _analyze_for_creativity(self, entities: List[Entity], relationships: List[Relationship]) -> Dict[str, Any]:
        """创造性分析场景"""
        # 识别突出的实质性特点
        substantive_features = []
        for rel in relationships:
            if rel.type == RelationshipType.STRUCTURAL and rel.strength == '强关系':
                substantive_features.append(rel.description)

        # 分析技术进步
        technical_advancement = {
            'solves_technical_problem': len(substantive_features) > 0,
            'provides_beneficial_effects': len([r for r in relationships if r.type == RelationshipType.FUNCTIONAL]),
            'unexpected_results': '需要结合说明书评估'
        }

        return {
            'substantive_features': substantive_features,
            'technical_advancement': technical_advancement,
            'creativity_arguments': [
                '非显而易见的结构组合',
                '产生预料不到的技术效果',
                '解决了长期存在的技术难题'
            ]
        }

    def _analyze_for_fto(self, entities: List[Entity], relationships: List[Relationship]) -> Dict[str, Any]:
        """FTO分析场景"""
        # 识别高风险要素
        high_risk_entities = [e for e in entities if e.type in ['部件', '结构']]
        critical_relationships = [r for r in relationships if r.confidence > 0.9]

        return {
            'high_risk_elements': [
                {
                    'entity': e.name,
                    'type': e.type,
                    'risk_level': 'high' if e.reference_number else 'medium'
                } for e in high_risk_entities
            ],
            'critical_relationships': [
                {
                    'description': r.description,
                    'confidence': r.confidence
                } for r in critical_relationships
            ],
            'design_around_opportunities': [
                '修改非核心实体',
                '调整实体间关系',
                '使用替代材料或结构'
            ],
            'risk_mitigation_strategies': [
                '进行详细的权利要求对比',
                '考虑规避设计',
                '评估许可可能性'
            ]
        }

    def _entity_to_dict(self, entity: Entity) -> Dict[str, Any]:
        """实体转字典"""
        return {
            'id': entity.id,
            'name': entity.name,
            'type': entity.type,
            'reference_number': entity.reference_number,
            'attributes': entity.attributes,
            'synonyms': entity.synonyms,
            'source_features': entity.source_features
        }

    def _relationship_to_dict(self, relationship: Relationship) -> Dict[str, Any]:
        """关系转字典"""
        return {
            'id': relationship.id,
            'subject': relationship.subject,
            'object': relationship.object,
            'type': relationship.type.value,
            'description': relationship.description,
            'confidence': relationship.confidence,
            'strength': relationship.strength,
            'source_features': relationship.source_features,
            'legal_implications': relationship.legal_implications
        }

    def _calculate_statistics(self, entities: List[Entity], relationships: List[Relationship]) -> Dict[str, Any]:
        """计算统计信息"""
        entity_type_counts = defaultdict(int)
        for entity in entities:
            entity_type_counts[entity.type] += 1

        relationship_type_counts = defaultdict(int)
        for rel in relationships:
            relationship_type_counts[rel.type.value] += 1

        return {
            'total_entities': len(entities),
            'total_relationships': len(relationships),
            'entity_type_distribution': dict(entity_type_counts),
            'relationship_type_distribution': dict(relationship_type_counts),
            'entities_with_references': len([e for e in entities if e.reference_number]),
            'strong_relationships': len([r for r in relationships if r.strength == '强关系'])
        }

# 使用示例
if __name__ == '__main__':
    # 创建增强版分析器
    analyzer = EnhancedLegalPatentAnalyzer()

    # 示例权利要求
    claim_text = '1、一种铜铝复合阳极母线，包括母线本体（1），其特征在于：所述母线本体（1）与导杆（6）的接触区域设置有凹槽（2），所述凹槽（2）内固定设置有接触铜板（4），所述接触铜板（4）与母线本体（1）表面平齐，所述接触铜板（4）宽度方向大于导杆（6）宽度。'

    # 执行分析
    result = analyzer.extract_entities_and_relationships(claim_text, claim_number=1)

    # 保存结果
    with open('enhanced_legal_analysis_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 打印关键信息
    logger.info("\n=== 增强版法律分析结果 ===")
    logger.info(f"提取的实体数: {len(result['entities'])}")
    logger.info(f"识别的关系数: {len(result['relationships'])}")
    logger.info("\n=== 实体列表 ===")
    for entity in result['entities']:
        logger.info(f"- {entity['name']} ({entity['type']}) [附图标记: {entity.get('reference_number', 'N/A')}]")

    logger.info("\n=== 关系列表 ===")
    for rel in result['relationships']:
        logger.info(f"- {rel['type']}: {rel['description']} [强度: {rel['strength']}]")

    logger.info("\n=== 法律场景分析 ===")
    for scenario, analysis in result['legal_analysis'].items():
        logger.info(f"\n{scenario}:")
        if isinstance(analysis, dict):
            for key, value in analysis.items():
                if isinstance(value, list) and value:
                    logger.info(f"  {key}: {len(value)} 项")
                elif not isinstance(value, list):
                    logger.info(f"  {key}: {value}")

    logger.info("\n分析结果已保存到 enhanced_legal_analysis_result.json")