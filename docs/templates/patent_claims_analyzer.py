#!/usr/bin/env python3
"""
专利权利要求书分析器
专门用于权利要求的技术特征提取、实体识别和关系分析
支持无效宣告、专利侵权诉讼等法律场景
"""

import json
import logging
import re
import uuid
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)

class PatentClaimsAnalyzer:
    """专利权利要求书分析器"""

    def __init__(self, template_file: str = 'enhanced_patent_claims_analysis_template.json'):
        """
        初始化分析器

        Args:
            template_file: 分析模板文件路径
        """
        with open(template_file, encoding='utf-8') as f:
            self.template = json.load(f)

        # 实体识别模式
        self.entity_patterns = {
            '部件': [
                r"([^，。；:]+?)本体",
                r"([^，。；:]+?)部件",
                r"([^，。；:]+?)组件",
                r"([^，。；:]+?)装置",
                r"([^，。；:]+?)器",
                r"([^，。；:]+?)机构",
                r"([^，。；:]+?]元件"
            ],
            '位置': [
                r"([^，。；:]+?)区域",
                r"([^，。；:]+?]位置",
                r"([^，。；:]+?]部位",
                r"([^，。；:]+?]端部"
            ],
            '材料': [
                r"([^，。；:]+?]板",
                r"([^，。；:]+?]层",
                r"([^，。；:]+?]膜",
                r"([^，。；:]+?]材料"
            ]
        }

        # 关系识别模式
        self.relationship_patterns = {
            '包含关系': [r"([^，。；:]+?)包括([^，。；:]+?)', r'([^，。；:]+?]设置有([^，。；:]+?)"],
            '连接关系': [r"([^，。；:]+?)连接([^，。；:]+?)', r'([^，。；:]+?]固定([^，。；:]+?)"],
            '位置关系': [r"([^，。；:]+?)位于([^，。；:]+?)', r'([^，。；:]+?]设置于([^，。；:]+?)"],
            '接触关系': [r"([^，。；:]+?)接触([^，。；:]+?)', r'([^，。；:]+?]与([^，。；:]+?)接触"]
        }

    def analyze_claim(self, claim_text: str, claim_number: int = 1) -> dict[str, Any]:
        """
        分析单个权利要求

        Args:
            claim_text: 权利要求文本
            claim_number: 权利要求编号

        Returns:
            分析结果字典
        """
        result = {
            'claim_basic_info': self._analyze_basic_info(claim_text, claim_number),
            'technical_feature_extraction': self._extract_technical_features(claim_text),
            'entity_extraction': {},  # 将在特征提取后填充
            'entity_relationship_analysis': {},  # 将在实体提取后填充
            'claim_structure_analysis': self._analyze_claim_structure(claim_text),
            'legal_protection_scope': self._analyze_protection_scope(claim_text)
        }

        # 提取实体和关系
        features = result['technical_feature_extraction']['features']
        entities = self._extract_entities(features)
        result['entity_extraction']['entities'] = entities

        relationships = self._analyze_relationships(features, entities)
        result['entity_relationship_analysis']['relationships'] = relationships

        # 构建关系网络
        result['entity_relationship_analysis']['relationship_network'] = \
            self._build_relationship_network(entities, relationships)

        return result

    def _analyze_basic_info(self, claim_text: str, claim_number: int) -> dict[str, Any]:
        """分析权利要求基本信息"""
        # 统计标点符号
        punctuation_count = {
            'commas': claim_text.count('，'),
            'periods': claim_text.count('。'),
            'colons': claim_text.count('：'),
            'semicolons': claim_text.count('；')
        }

        total_count = sum(punctuation_count.values())

        # 清理文本（去除冗余空格和换行）
        cleaned_text = re.sub(r'\s+', '', claim_text)

        # 判断权利要求类型
        claim_type = 'independent' if claim_number == 1 or '根据权利要求' not in claim_text else 'dependent'

        return {
            'claim_number': claim_number,
            'claim_type': claim_type,
            'original_text': claim_text,
            'cleaned_text': cleaned_text,
            'punctuation_analysis': {
                'total_count': total_count,
                'breakdown': punctuation_count
            }
        }

    def _extract_technical_features(self, claim_text: str) -> dict[str, Any]:
        """基于标点符号提取技术特征"""
        features = []

        # 定义分割优先级和规则
        splitting_rules = [
            ('。', 'period'),      # 句号分割完整技术方案
            ('，', 'comma'),       # 逗号分割技术特征
            ('：', 'colon'),       # 冒号分割特征引导
            ('；', 'semicolon')    # 分号分割并列特征
        ]

        # 先去除数字编号前缀（如"1、"）
        text = re.sub(r'^\d+、', '', claim_text)

        sequence_number = 1

        for punct, _punct_type in splitting_rules:
            if punct in text:
                parts = text.split(punct)
                for _i, part in enumerate(parts):
                    if part.strip():
                        # 保存特征
                        feature = {
                            'feature_id': f"feature_{uuid.uuid4().hex[:8]}",
                            'sequence_number': sequence_number,
                            'feature_text': part.strip(),
                            'splitting_punctuation': punct,
                            'feature_category': self._classify_feature(part.strip()),
                            'feature_nature': self._determine_feature_nature(part.strip()),
                            'feature_level': self._assess_feature_level(part.strip())
                        }
                        features.append(feature)
                        sequence_number += 1
                break  # 只使用第一个分割点

        # 如果没有找到标点符号，整个文本作为一个特征
        if not features:
            feature = {
                'feature_id': f"feature_{uuid.uuid4().hex[:8]}",
                'sequence_number': 1,
                'feature_text': text.strip(),
                'splitting_punctuation': 'none',
                'feature_category': self._classify_feature(text.strip()),
                'feature_nature': self._determine_feature_nature(text.strip()),
                'feature_level': self._assess_feature_level(text.strip())
            }
            features.append(feature)

        # 统计特征信息
        stats = self._calculate_feature_statistics(features)

        return {
            'extraction_method': {
                'basis': '标点符号分割',
                'splitting_rules': [
                    '按逗号(，)分割技术特征',
                    '按句号(。)分割完整技术方案',
                    '按冒号(：)分割特征引导词后内容',
                    '按分号(；)分割并列技术特征'
                ]
            },
            'features': features,
            'feature_statistics': stats
        }

    def _classify_feature(self, feature_text: str) -> str:
        """分类技术特征"""
        if '包括' in feature_text or '设置有' in feature_text or '安装有' in feature_text:
            return '结构特征'
        elif '能够' in feature_text or '用于' in feature_text or '实现' in feature_text:
            return '功能特征'
        elif '通过' in feature_text or '采用' in feature_text or '步骤' in feature_text:
            return '方法特征'
        elif re.search(r'\d+\s*[mmcmkg℃℉%]', feature_text):
            return '参数特征'
        elif '位于' in feature_text or '位置' in feature_text:
            return '位置特征'
        elif '连接' in feature_text or '固定' in feature_text or '配合' in feature_text:
            return '连接特征'
        else:
            return '结构特征'  # 默认

    def _determine_feature_nature(self, feature_text: str) -> str:
        """确定技术特征性质"""
        if '其特征' in feature_text or '还包括' in feature_text:
            return '附加技术特征'
        elif '包括' in feature_text and '本体' in feature_text:
            return '必要技术特征'
        else:
            return '可选技术特征'

    def _assess_feature_level(self, feature_text: str) -> str:
        """评估技术特征重要性级别"""
        # 基于关键词判断重要性
        high_importance_keywords = ['核心', '关键', '主要', '基本']
        medium_importance_keywords = ['重要', '显著', '特殊']

        for keyword in high_importance_keywords:
            if keyword in feature_text:
                return '核心特征'

        for keyword in medium_importance_keywords:
            if keyword in feature_text:
                return '重要特征'

        return '一般特征'

    def _calculate_feature_statistics(self, features: list[dict]) -> dict[str, int]:
        """计算技术特征统计信息"""
        stats = {
            'total_features': len(features),
            'essential_features': 0,
            'structural_features': 0,
            'functional_features': 0
        }

        for feature in features:
            if feature['feature_nature'] == '必要技术特征':
                stats['essential_features'] += 1
            if feature['feature_category'] == '结构特征':
                stats['structural_features'] += 1
            if feature['feature_category'] == '功能特征':
                stats['functional_features'] += 1

        return stats

    def _extract_entities(self, features: list[dict]) -> list[dict]:
        """从技术特征中提取实体"""
        entities = {}
        entity_id_counter = 1

        for feature in features:
            feature_text = feature['feature_text']

            # 提取附图标记
            reference_match = re.search(r'（(\d+)）', feature_text)
            reference_number = reference_match.group(1) if reference_match else None

            # 根据模式提取实体
            for entity_type, patterns in self.entity_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, feature_text)
                    for match in matches:
                        entity_name = match.strip()
                        if entity_name and len(entity_name) > 1:  # 过滤过短的匹配
                            entity_id = f"entity_{entity_id_counter}"

                            # 提取实体属性
                            attributes = self._extract_entity_attributes(feature_text, entity_name)

                            if entity_id not in entities:
                                entities[entity_id] = {
                                    'entity_id': entity_id,
                                    'entity_name': entity_name,
                                    'entity_type': entity_type,
                                    'reference_number': reference_number,
                                    'feature_ids': [feature['feature_id']],
                                    'entity_attributes': attributes,
                                    'synonyms': []
                                }
                            else:
                                entities[entity_id]['feature_ids'].append(feature['feature_id'])

                            entity_id_counter += 1

        return list(entities.values())

    def _extract_entity_attributes(self, text: str, entity_name: str) -> dict[str, str]:
        """提取实体属性"""
        attributes = {}

        # 提取尺寸信息
        size_pattern = f"{entity_name}[^，。；:]*?(\\d+\\s*[mmcmµm])"
        size_match = re.search(size_pattern, text)
        if size_match:
            attributes['size'] = size_match.group(1)

        # 提取形状信息
        shape_keywords = ['圆形', '方形', '矩形', '球形', '柱形', '锥形']
        for shape in shape_keywords:
            if shape in text:
                attributes['shape'] = shape
                break

        # 提取材料信息
        material_keywords = ['铜', '铝', '钢', '铁', '塑料', '橡胶', '陶瓷']
        for material in material_keywords:
            if material in text:
                attributes['material'] = material
                break

        return attributes

    def _analyze_relationships(self, features: list[dict], entities: list[dict]) -> list[dict]:
        """分析实体间关系"""
        relationships = []
        relationship_id_counter = 1

        # 创建实体名称到ID的映射
        entity_name_to_id = {entity['entity_name']: entity['entity_id'] for entity in entities}

        for feature in features:
            feature_text = feature['feature_text']

            # 根据关系模式识别关系
            for relationship_type, patterns in self.relationship_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, feature_text)
                    for match in matches:
                        if len(match) >= 2:
                            subject_name = match[0].strip()
                            object_name = match[1].strip()

                            # 查找对应的实体ID
                            subject_id = entity_name_to_id.get(subject_name)
                            object_id = entity_name_to_id.get(object_name)

                            if subject_id and object_id and subject_id != object_id:
                                relationship = {
                                    'relationship_id': f"rel_{relationship_id_counter}",
                                    'subject_entity': subject_id,
                                    'object_entity': object_id,
                                    'relationship_type': relationship_type,
                                    'relationship_description': feature_text,
                                    'relationship_strength': self._assess_relationship_strength(feature_text),
                                    'source_feature_ids': [feature['feature_id']]
                                }
                                relationships.append(relationship)
                                relationship_id_counter += 1

        return relationships

    def _assess_relationship_strength(self, text: str) -> str:
        """评估关系强度"""
        strong_keywords = ['固定连接', '牢固固定', '紧密配合']
        weak_keywords = ['可拆卸', '活动连接', '松配合']

        for keyword in strong_keywords:
            if keyword in text:
                return '强关系'

        for keyword in weak_keywords:
            if keyword in text:
                return '弱关系'

        return '可选关系'

    def _build_relationship_network(self, entities: list[dict], relationships: list[dict]) -> dict[str, Any]:
        """构建关系网络"""
        # 构建节点
        nodes = []
        for entity in entities:
            nodes.append({
                'id': entity['entity_id'],
                'name': entity['entity_name'],
                'type': entity['entity_type'],
                'attributes': entity['entity_attributes']
            })

        # 构建边
        edges = []
        for rel in relationships:
            edges.append({
                'source': rel['subject_entity'],
                'target': rel['object_entity'],
                'type': rel['relationship_type'],
                'strength': rel['relationship_strength']
            })

        # 计算中心性指标（简化版）
        centrality_analysis = self._calculate_centrality(nodes, edges)

        return {
            'nodes': nodes,
            'edges': edges,
            'centrality_analysis': centrality_analysis
        }

    def _calculate_centrality(self, nodes: list[dict], edges: list[dict]) -> dict[str, Any]:
        """计算网络中心性指标（简化实现）"""
        # 计算度中心性
        degree_count = defaultdict(int)
        for edge in edges:
            degree_count[edge['source']] += 1
            degree_count[edge['target']] += 1

        max_degree = max(degree_count.values()) if degree_count else 1

        degree_centrality = {}
        for node in nodes:
            node_id = node['id']
            degree_centrality[node_id] = degree_count.get(node_id, 0) / max_degree

        return {
            'degree_centrality': degree_centrality,
            'betweenness_centrality': {},  # 简化实现暂不计算
            'closeness_centrality': {}    # 简化实现暂不计算
        }

    def _analyze_claim_structure(self, claim_text: str) -> dict[str, Any]:
        """分析权利要求结构"""
        # 分割前序部分和特征部分
        characterizing_phrases = ['其特征是', '其特征在于', '还包括', '其中', '进一步']

        preamble_text = claim_text
        characterizing_text = ''
        transition_phrase = ''

        for phrase in characterizing_phrases:
            if phrase in claim_text:
                parts = claim_text.split(phrase, 1)
                preamble_text = parts[0].strip()
                characterizing_text = phrase + parts[1].strip()
                transition_phrase = phrase
                break

        # 分析依赖关系
        dependency_analysis = {
            'applicable': '根据权利要求' in claim_text,
            'referenced_claims': [],
            'reference_type': '单引',
            'additional_limitations': []
        }

        if dependency_analysis['applicable']:
            # 提取引用的权利要求
            ref_pattern = r"根据权利要求(\d+)"
            refs = re.findall(ref_pattern, claim_text)
            dependency_analysis['referenced_claims'] = [int(ref) for ref in refs]

            if len(refs) > 1:
                dependency_analysis['reference_type'] = '多引'

        return {
            'preamble_analysis': {
                'text': preamble_text,
                'features': [],  # 可以进一步分析
                'shared_features': [],  # 可以进一步分析
                'theme_name': self._extract_theme_name(preamble_text)
            },
            'characterizing_analysis': {
                'text': characterizing_text,
                'transition_phrases': [transition_phrase] if transition_phrase else [],
                'distinguishing_features': [],  # 可以进一步分析
                'innovative_aspects': []  # 可以进一步分析
            },
            'dependency_analysis': dependency_analysis
        }

    def _extract_theme_name(self, text: str) -> str:
        """提取技术方案主题名称"""
        # 通常在前面的"一种/一种..."表述中
        theme_pattern = r"一种([^，。；:]+?)(?:，|$|。)"
        match = re.search(theme_pattern, text)
        return match.group(1).strip() if match else ''

    def _analyze_protection_scope(self, claim_text: str) -> dict[str, Any]:
        """分析法律保护范围"""
        # 这里是简化分析，实际应用中需要更复杂的NLP技术
        scope_analysis = {
            'scope_definition': {
                'breadth': '中',  # 简化判断
                'core_technical_features': [],
                'boundary_features': []
            },
            'equivalents_analysis': {
                'potential_equivalents': [],
                'essential_features': [],
                'replaceable_features': []
            },
            'vulnerability_points': {
                'weak_features': [],
                'ambiguous_descriptions': [],
                'prior_art_risks': []
            }
        }

        # 简单的脆弱性分析
        if '约' in claim_text or '左右' in claim_text:
            scope_analysis['vulnerability_points']['ambiguous_descriptions'].append('包含约数表述')

        if re.search(r'\d+\s*-\s*\d+', claim_text):
            scope_analysis['vulnerability_points']['ambiguous_descriptions'].append('包含数值范围')

        return scope_analysis

    def compare_claims(self, target_claim: dict, reference_claims: list[dict]) -> dict[str, Any]:
        """
        对比分析多个权利要求

        Args:
            target_claim: 目标权利要求分析结果
            reference_claims: 对比权利要求分析结果列表

        Returns:
            对比分析结果
        """
        comparison_result = {
            'comparison_setup': {
                'target_claim': {
                    'features': target_claim.get('technical_feature_extraction', {}).get('features', [])
                }
            },
            'feature_comparison': {
                'common_features': [],
                'different_features': {
                    'target_only': [],
                    'reference_only': []
                },
                'equivalent_features': []
            },
            'infringement_analysis': {},
            'comparison_metrics': {}
        }

        # 这里实现简化的特征对比逻辑
        # 实际应用中需要更复杂的相似度计算算法

        return comparison_result

# 使用示例
if __name__ == '__main__':
    # 创建分析器
    analyzer = PatentClaimsAnalyzer()

    # 示例权利要求
    sample_claim = '1、一种铜铝复合阳极母线，包括母线本体（1），其特征在于：所述母线本体（1）与导杆（6）的接触区域设置有凹槽（2），所述凹槽（2）内固定设置有接触铜板（4），所述接触铜板（4）与母线本体（1）表面平齐，所述接触铜板（4）宽度方向大于导杆（6）宽度。'

    # 分析权利要求
    result = analyzer.analyze_claim(sample_claim, claim_number=1)

    # 打印分析结果
    logger.info('=== 权利要求分析结果 ===')
    logger.info(f"标点符号总数: {result['claim_basic_info']['punctuation_analysis']['total_count']}")
    logger.info(f"技术特征数量: {result['technical_feature_extraction']['feature_statistics']['total_features']}")
    logger.info(f"实体数量: {len(result['entity_extraction']['entities'])}")
    logger.info(f"关系数量: {len(result['entity_relationship_analysis']['relationships'])}")

    logger.info("\n=== 技术特征 ===")
    for feature in result['technical_feature_extraction']['features']:
        logger.info(f"{feature['sequence_number']}. [{feature['splitting_punctuation']}] {feature['feature_text']}")

    logger.info("\n=== 实体 ===")
    for entity in result['entity_extraction']['entities']:
        logger.info(f"- {entity['entity_name']} ({entity['entity_type']}) [{entity.get('reference_number', 'N/A')}]")

    logger.info("\n=== 实体关系 ===")
    for rel in result['entity_relationship_analysis']['relationships']:
        subject = next((e['entity_name'] for e in result['entity_extraction']['entities']
                       if e['entity_id'] == rel['subject_entity']), '')
        object_entity = next((e['entity_name'] for e in result['entity_extraction']['entities']
                            if e['entity_id'] == rel['object_entity']), '')
        logger.info(f"- {subject} --[{rel['relationship_type']}]--> {object_entity}")

    # 保存完整结果到JSON文件
    with open('claim_analysis_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info("\n分析结果已保存到 claim_analysis_result.json")
