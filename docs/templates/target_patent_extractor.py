#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目标专利技术特征提取器
专门用于目标专利的权利要求书技术特征提取
作为后续技术比对、新颖性分析、创造性分析的基础步骤
"""

import json
import logging
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class TargetPatentExtractor:
    """目标专利技术特征提取器"""

    def __init__(self):
        """初始化提取器"""
        self.extraction_stats = {
            'total_claims_processed': 0,
            'total_features_extracted': 0,
            'total_entities_identified': 0,
            'total_relationships_found': 0
        }

    def extract_target_patent(self, patent_info: Dict[str, Any], claims_text: str) -> Dict[str, Any]:
        """
        提取目标专利的技术特征

        Args:
            patent_info: 专利基本信息
            claims_text: 权利要求书文本

        Returns:
            标准化的目标专利提取结果
        """
        # 初始化结果结构
        result = {
            'extraction_metadata': {
                'extraction_date': datetime.now().isoformat(),
                'extractor_version': '1.0',
                'workflow_step': 'target_patent_feature_extraction'
            },
            'patent_identification': self._format_patent_info(patent_info),
            'claims_overview': self._analyze_claims_overview(claims_text),
            'feature_extraction_details': {},
            'extracted_technical_features': {},
            'entity_analysis': {},
            'downstream_analysis_ready': {}
        }

        # 提取权利要求
        claims = self._parse_claims(claims_text)
        result['claims_overview']['parsed_claims'] = claims

        # 逐个分析权利要求
        all_features = []
        all_entities = []
        all_relationships = []

        for claim in claims:
            if claim['type'] == 'independent':
                # 重点分析独立权利要求
                analysis = self._analyze_single_claim(claim)
                all_features.extend(analysis['features'])
                all_entities.extend(analysis['entities'])
                all_relationships.extend(analysis['relationships'])

        # 去重实体
        all_entities = self._deduplicate_entities(all_entities)

        # 构建最终结果
        result['feature_extraction_details'] = self._build_extraction_details(all_features)
        result['extracted_technical_features'] = self._build_features_structure(all_features)
        result['entity_analysis'] = self._build_entity_structure(all_entities, all_relationships)

        # 更新统计信息
        self.extraction_stats['total_claims_processed'] = len(claims)
        self.extraction_stats['total_features_extracted'] = len(all_features)
        self.extraction_stats['total_entities_identified'] = len(all_entities)
        self.extraction_stats['total_relationships_found'] = len(all_relationships)

        # 判断下游分析准备情况
        result['downstream_analysis_ready'] = self._assess_downstream_readiness(result)

        # 质量检查
        result['quality_assessment'] = self._perform_quality_assessment(result)

        return result

    def _format_patent_info(self, patent_info: Dict[str, Any]) -> Dict[str, Any]:
        """格式化专利信息"""
        return {
            'patent_number': patent_info.get('patent_number', ''),
            'application_number': patent_info.get('application_number', ''),
            'title': patent_info.get('title', ''),
            'application_date': patent_info.get('application_date', ''),
            'publication_date': patent_info.get('publication_date', ''),
            'applicant': patent_info.get('applicant', ''),
            'inventor': patent_info.get('inventor', ''),
            'ipc_classification': patent_info.get('ipc', [])
        }

    def _analyze_claims_overview(self, claims_text: str) -> Dict[str, Any]:
        """分析权利要求概况"""
        # 统计标点符号
        punctuation_stats = {
            'commas': claims_text.count('，'),
            'periods': claims_text.count('。'),
            'colons': claims_text.count('：'),
            'semicolons': claims_text.count('；')
        }
        punctuation_stats['total'] = sum(punctuation_stats.values())

        # 识别权利要求编号
        claim_numbers = re.findall(r"(\d+)[、.]", claims_text)

        return {
            'total_claims_count': len(claim_numbers),
            'independent_claims_count': self._count_independent_claims(claims_text),
            'dependent_claims_count': self._count_dependent_claims(claims_text),
            'main_claim_number': '1',  # 通常第一个是主权利要求
            'punctuation_analysis': punctuation_stats,
            'claim_numbers': [int(num) for num in claim_numbers]
        }

    def _parse_claims(self, claims_text: str) -> List[Dict[str, Any]]:
        """解析权利要求"""
        claims = []

        # 按权利要求编号分割
        claim_pattern = r"(\d+)[、.]\s*([\s\S]*?)(?=\d+[、.]|$)"
        matches = re.findall(claim_pattern, claims_text)

        for claim_num, claim_text in matches:
            claim = {
                'number': int(claim_num),
                'text': claim_text.strip(),
                'type': 'dependent' if '根据权利要求' in claim_text else 'independent',
                'raw_text': claim_text.strip()
            }
            claims.append(claim)

        return claims

    def _count_independent_claims(self, claims_text: str) -> int:
        """统计独立权利要求数量"""
        claims = self._parse_claims(claims_text)
        return sum(1 for claim in claims if claim['type'] == 'independent')

    def _count_dependent_claims(self, claims_text: str) -> int:
        """统计从属权利要求数量"""
        claims = self._parse_claims(claims_text)
        return sum(1 for claim in claims if claim['type'] == 'dependent')

    def _analyze_single_claim(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """分析单个权利要求"""
        analysis = {
            'claim_number': claim['number'],
            'features': [],
            'entities': [],
            'relationships': []
        }

        # 提取技术特征
        features = self._extract_features_by_punctuation(claim['text'])
        analysis['features'] = features

        # 提取实体
        entities = self._extract_entities_from_features(features)
        analysis['entities'] = entities

        # 提取关系
        relationships = self._extract_relationships_from_features(features, entities)
        analysis['relationships'] = relationships

        return analysis

    def _extract_features_by_punctuation(self, claim_text: str) -> List[Dict[str, Any]]:
        """基于标点符号提取技术特征"""
        features = []

        # 去除权利要求编号
        clean_text = re.sub(r"^\d+[、.]\s*', '", claim_text)

        # 按标点符号分割
        segments = self._split_by_punctuation(clean_text)

        for i, segment in enumerate(segments):
            if segment.strip():
                feature = {
                    'feature_id': f"F_{claim['number']}_{i+1}_{uuid.uuid4().hex[:6]}",
                    'sequence_number': i + 1,
                    'feature_text': segment.strip(),
                    'splitting_punctuation': self._get_splitting_punctuation(segment, segments, i),
                    'feature_category': self._categorize_feature(segment.strip()),
                    'feature_importance': self._assess_feature_importance(segment.strip(), i, segments),
                    'claim_number': claim['number']
                }
                features.append(feature)

        return features

    def _split_by_punctuation(self, text: str) -> List[str]:
        """按标点符号分割文本"""
        # 定义分割优先级
        splitters = ['。', '，', '：', '；']

        segments = [text]
        for splitter in splitters:
            new_segments = []
            for segment in segments:
                if splitter in segment:
                    parts = segment.split(splitter)
                    for i, part in enumerate(parts):
                        if part.strip():
                            new_segments.append(part.strip() + splitter if i < len(parts) - 1 else part.strip())
                else:
                    new_segments.append(segment)
            segments = new_segments
            if len(segments) > 1:
                break  # 只使用第一个分割点

        return segments

    def _get_splitting_punctuation(self, segment: str, all_segments: List[str], index: int) -> str:
        """获取分割标点符号"""
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
            '功能特征': ['能够', '用于', '实现', '具有'],
            '位置特征': ['位于', '设置于', '位置', '区域'],
            '参数特征': ['mm', 'cm', '℃', 'mm²'],
            '材料特征': ['铜', '铝', '钢', '塑料', '橡胶'],
            '方法特征': ['步骤', '方法', '工艺', '过程']
        }

        for category, keywords in categories.items():
            if any(keyword in feature_text for keyword in keywords):
                return category

        return '其他特征'

    def _assess_feature_importance(self, feature_text: str, index: int, total_features: List[str]) -> str:
        """评估特征重要性"""
        # 前序特征通常更重要
        if index == 0:
            return '核心特征'

        # 包含"其特征"的特征很重要
        if '其特征' in feature_text:
            return '重要特征'

        # 包含附图标记的特征可能更重要
        if re.search(r"（\d+）", feature_text):
            return '重要特征'

        # 其他为一般特征
        return '一般特征'

    def _extract_entities_from_features(self, features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从特征中提取实体"""
        entities = []

        # 实体识别模式
        entity_patterns = {
            '部件': [
                r"([^，。；:]+?)本体",
                r"([^，。；:]+?]部件",
                r"([^，。；:]+?]组件",
                r"([^，。；:]+?]装置",
                r"([^，。；:]+?]器",
                r"([^，。；:]+?]机构"
            ],
            '材料': [
                r"([^，。；:]+?]板",
                r"([^，。；:]+?]层",
                r"([^，。；:]+?]膜",
                r"([^，。；:]+?]材料"
            ],
            '位置': [
                r"([^，。；:]+?]区域",
                r"([^，。；:]+?]位置",
                r"([^，。；:]+?]部位",
                r"([^，。；:]+?]端部"
            ],
            '结构': [
                r"([^，。；:]+?]槽",
                r"([^，。；:]+?]孔",
                r"([^，。；:]+?]口",
                r"([^，。；:]+?]腔"
            ]
        }

        entity_counter = 1
        entity_map = {}  # 用于去重

        for feature in features:
            feature_text = feature['feature_text']

            # 提取附图标记
            ref_number = None
            ref_match = re.search(r"（(\d+)）", feature_text)
            if ref_match:
                ref_number = ref_match.group(1)

            # 识别实体
            for entity_type, patterns in entity_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, feature_text)
                    for match in matches:
                        entity_name = match.strip()
                        if len(entity_name) > 1:  # 过滤过短的匹配
                            if entity_name not in entity_map:
                                entity_id = f"E_{entity_counter:03d}"
                                entity_map[entity_name] = entity_id

                                entity = {
                                    'entity_id': entity_id,
                                    'entity_name': entity_name,
                                    'entity_type': entity_type,
                                    'reference_number': ref_number,
                                    'source_features': [feature['feature_id']],
                                    'first_appearance_claim': feature['claim_number']
                                }
                                entities.append(entity)
                                entity_counter += 1
                            else:
                                # 更新现有实体的信息
                                entity_id = entity_map[entity_name]
                                for entity in entities:
                                    if entity['entity_id'] == entity_id:
                                        entity['source_features'].append(feature['feature_id'])
                                        if ref_number and not entity.get('reference_number'):
                                            entity['reference_number'] = ref_number
                                        break

        return entities

    def _extract_relationships_from_features(self, features: List[Dict[str, Any]], entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从特征中提取关系"""
        relationships = []

        # 创建实体名称到ID的映射
        entity_name_to_id = {entity['entity_name']: entity['entity_id'] for entity in entities}

        # 关系识别模式
        relationship_patterns = {
            '包含关系': [
                r"([^，。；:]+?)包括([^，。；:]+?)",
                r"([^，。；:]+?]设置有([^，。；:]+?)"
            ],
            '连接关系': [
                r"([^，。；:]+?)连接([^，。；:]+?)",
                r"([^，。；:]+?]固定([^，。；:]+?)"
            ],
            '位置关系': [
                r"([^，。；:]+?]位于([^，。；:]+?)",
                r"([^，。；:]+?]设置于([^，。；:]+?)"
            ],
            '接触关系': [
                r"([^，。；:]+?)接触([^，。；:]+?)",
                r"([^，。；:]+?]与([^，。；:]+?)接触"
            ],
            '尺寸关系': [
                r"([^，。；:]+?)(大于|小于|等于)([^，。；:]+?)",
                r"([^，。；:]+?]宽度(.+)导杆(.+?)宽度"
            ],
            '平齐关系': [
                r"([^，。；:]+?)与([^，。；:]+?)平齐"
            ]
        }

        relationship_counter = 1

        for feature in features:
            feature_text = feature['feature_text']

            for rel_type, patterns in relationship_patterns.items():
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
                                    'relationship_id': f"R_{relationship_counter:03d}",
                                    'subject_entity': subject_id,
                                    'object_entity': object_id,
                                    'relationship_type': rel_type,
                                    'relationship_description': feature_text,
                                    'source_feature': feature['feature_id'],
                                    'confidence': 'high' if subject_id and object_id else 'medium'
                                }
                                relationships.append(relationship)
                                relationship_counter += 1

        return relationships

    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去除重复实体"""
        seen = set()
        unique_entities = []

        for entity in entities:
            entity_key = (entity['entity_name'], entity['entity_type'])
            if entity_key not in seen:
                seen.add(entity_key)
                unique_entities.append(entity)

        return unique_entities

    def _build_extraction_details(self, features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建提取详情"""
        total_features = len(features)
        category_stats = {}

        for feature in features:
            category = feature['feature_category']
            category_stats[category] = category_stats.get(category, 0) + 1

        return {
            'extraction_method': '基于标点符号分割',
            'punctuation_analysis': {
                'total_punctuation_points': sum(f['feature_text'].count(p)
                                             for f in features
                                             for p in ['，', '。', '：', '；']),
                'splitting_distribution': {
                    p: sum(1 for f in features if f['splitting_punctuation'] == p)
                    for p in ['，', '。', '：', '；', 'none']
                }
            },
            'total_features_extracted': total_features,
            'feature_categorization': category_stats,
            'extraction_timestamp': datetime.now().isoformat()
        }

    def _build_features_structure(self, features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建特征结构"""
        return {
            'features_list': features,
            'feature_statistics': {
                'essential_features_count': sum(1 for f in features if f['feature_importance'] == '核心特征'),
                'important_features_count': sum(1 for f in features if f['feature_importance'] == '重要特征'),
                'structural_features_count': sum(1 for f in features if f['feature_category'] == '结构特征'),
                'functional_features_count': sum(1 for f in features if f['feature_category'] == '功能特征')
            }
        }

    def _build_entity_structure(self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建实体结构"""
        return {
            'identified_entities': entities,
            'entity_relationships': relationships,
            'entity_statistics': {
                'total_entities': len(entities),
                'entity_type_distribution': {
                    entity_type: sum(1 for e in entities if e['entity_type'] == entity_type)
                    for entity_type in set(e['entity_type'] for e in entities)
                }
            }
        }

    def _assess_downstream_readiness(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """评估下游分析准备情况"""
        # 检查必要的提取结果
        has_features = result.get('extracted_technical_features', {}).get('features_list')
        has_entities = result.get('entity_analysis', {}).get('identified_entities')

        ready_for_novelty = bool(has_features and len(has_features) > 0)
        ready_for_creativity = bool(has_features and len(has_features) > 0)
        ready_for_infringement = bool(has_features and has_entities)
        ready_for_fto = bool(has_features and has_entities)

        return {
            'ready_for_novelty_analysis': ready_for_novelty,
            'ready_for_creativity_analysis': ready_for_creativity,
            'ready_for_infringement_analysis': ready_for_infringement,
            'ready_for_fto_analysis': ready_for_fto,
            'overall_readiness': 'complete' if all([ready_for_novelty, ready_for_creativity, ready_for_infringement, ready_for_fto]) else 'partial'
        }

    def _perform_quality_assessment(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """执行质量评估"""
        features = result.get('extracted_technical_features', {}).get('features_list', [])
        entities = result.get('entity_analysis', {}).get('identified_entities', [])

        # 计算质量指标
        feature_completeness = len(features) > 0
        entity_recognition_quality = len(entities) > 0
        reference_number_preservation = sum(1 for e in entities if e.get('reference_number')) > 0

        overall_quality_score = 0
        if feature_completeness:
            overall_quality_score += 40
        if entity_recognition_quality:
            overall_quality_score += 30
        if reference_number_preservation:
            overall_quality_score += 30

        return {
            'feature_completeness': '通过' if feature_completeness else '未通过',
            'entity_recognition_quality': '通过' if entity_recognition_quality else '未通过',
            'reference_number_preservation': '通过' if reference_number_preservation else '未通过',
            'overall_quality_score': overall_quality_score,
            'quality_grade': '优秀' if overall_quality_score >= 90 else '良好' if overall_quality_score >= 70 else '需改进'
        }

    def save_extraction_result(self, result: Dict[str, Any], output_path: str) -> None:
        """保存提取结果"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"目标专利提取结果已保存到: {output_path}")

# 使用示例
if __name__ == '__main__':
    # 创建提取器
    extractor = TargetPatentExtractor()

    # 示例专利信息
    patent_info = {
        'patent_number': 'CN109876543A',
        'application_number': 'CN201810000001.0',
        'title': '一种铜铝复合阳极母线',
        'application_date': '2018-01-01',
        'publication_date': '2019-05-01',
        'applicant': '某某科技有限公司',
        'inventor': '张某'
    }

    # 示例权利要求书
    claims_text = """
    1、一种铜铝复合阳极母线，包括母线本体（1），其特征在于：所述母线本体（1）与导杆（6）的接触区域设置有凹槽（2），所述凹槽（2）内固定设置有接触铜板（4），所述接触铜板（4）与母线本体（1）表面平齐，所述接触铜板（4）宽度方向大于导杆（6）宽度。

    2、根据权利要求1所述的铜铝复合阳极母线，其特征在于：所述凹槽（2）的深度为5-10mm。
    """

    # 执行提取
    result = extractor.extract_target_patent(patent_info, claims_text)

    # 保存结果
    extractor.save_extraction_result(result, 'output/target_patent_extraction_result.json')

    # 打印关键信息
    logger.info("\n=== 目标专利提取结果摘要 ===")
    logger.info(f"专利号: {result['patent_identification']['patent_number']}")
    logger.info(f"权利要求数: {result['claims_overview']['total_claims_count']}")
    logger.info(f"提取的特征数: {result['feature_extraction_details']['total_features_extracted']}")
    logger.info(f"识别的实体数: {result['entity_analysis']['entity_statistics']['total_entities']}")
    logger.info(f"质量评估: {result['quality_assessment']['quality_grade']}")
    logger.info(f"下游分析准备状态: {result['downstream_analysis_ready']['overall_readiness']}")