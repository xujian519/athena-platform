#!/usr/bin/env python3
"""
语义融合引擎 - 多模态深度语义理解
Semantic Fusion Engine - Deep Multi-Modal Semantic Understanding

基于设计文档要求的跨模态注意力机制和语义融合实现
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

# Numpy兼容性导入
import asyncio
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np

from config.numpy_compatibility import sum, zeros

# AI和向量处理导入
try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)

class SemanticRelationType(Enum):
    """语义关系类型"""
    EQUIVALENCE = 'equivalence'       # 等价关系
    EXPLANATION = 'explanation'       # 解释关系
    REFERENCE = 'reference'           # 引用关系
    COMPOSITION = 'composition'       # 组成关系
    SPATIAL = 'spatial'              # 空间关系
    TEMPORAL = 'temporal'            # 时间关系
    CAUSAL = 'causal'               # 因果关系

class AttentionType(Enum):
    """注意力类型"""
    CROSS_MODAL = 'cross_modal'      # 跨模态注意力
    SELF_ATTENTION = 'self_attention'  # 自注意力
    HIERARCHICAL = 'hierarchical'    # 层次注意力

@dataclass
class SemanticVector:
    """语义向量"""
    vector_id: str
    content: str
    embedding: list[float]
    modality: str
    attention_weights: dict[str, float]
    semantic_tags: list[str]
    confidence: float

@dataclass
class SemanticRelation:
    """语义关系"""
    relation_id: str
    source_vector: str
    target_vector: str
    relation_type: SemanticRelationType
    strength: float              # 关系强度
    evidence: list[str]          # 证据
    confidence: float

@dataclass
class FusionResult:
    """融合结果"""
    fusion_id: str
    unified_representation: list[float]
    contributing_modalities: list[str]
    attention_map: dict[str, dict[str, float]]
    semantic_relations: list[SemanticRelation]
    consistency_score: float

class SemanticEmbeddingEngine:
    """语义嵌入引擎"""

    def __init__(self):
        self.word_embeddings = {}
        self.domain_embeddings = {}
        self.cross_modal_mappings = {}

        # 初始化领域特定词汇
        self._initialize_domain_vocabulary()

    def _initialize_domain_vocabulary(self):
        """初始化领域词汇表"""
        # 专利法律术语
        self.patent_legal_terms = {
            '权利要求': {'category': 'legal', 'importance': 1.0, 'synonyms': ['claim', '专利权要求']},
            '现有技术': {'category': 'legal', 'importance': 0.9, 'synonyms': ['prior art', '背景技术']},
            '新颖性': {'category': 'legal', 'importance': 0.9, 'synonyms': ['novelty', '新创性']},
            '创造性': {'category': 'legal', 'importance': 0.9, 'synonyms': ['inventive step', '非显而易见性']},
            '说明书': {'category': 'legal', 'importance': 0.8, 'synonyms': ['specification', '描述']},
            '附图': {'category': 'legal', 'importance': 0.8, 'synonyms': ['drawing', '图纸', '图示']},
            '实施例': {'category': 'legal', 'importance': 0.7, 'synonyms': ['embodiment', '具体实施方式']},
            '技术领域': {'category': 'technical', 'importance': 0.8, 'synonyms': ['technical field', '技术方案']},
        }

        # 技术术语
        self.technical_terms = {
            '传感器': {'category': 'component', 'importance': 0.8, 'synonyms': ['sensor', '检测器']},
            '微处理器': {'category': 'component', 'importance': 0.9, 'synonyms': ['microprocessor', 'CPU', '处理器']},
            '控制器': {'category': 'component', 'importance': 0.8, 'synonyms': ['controller', '控制单元']},
            '连接': {'category': 'relation', 'importance': 0.6, 'synonyms': ['connect', '耦合', '连接到']},
            '设置': {'category': 'relation', 'importance': 0.6, 'synonyms': ['setup', '配置', '设有']},
        }

    async def encode_text(self, text: str, modality: str = 'text') -> SemanticVector:
        """编码文本为语义向量"""
        # 简化的嵌入实现 (实际应使用BERT等预训练模型)
        words = re.findall(r'[\w\u4e00-\u9fff]+', text.lower())

        # 计算简单的词向量 (基于词频和TF-IDF)
        embedding = zeros(100)  # 100维向量

        for word in words:
            if word in self.patent_legal_terms:
                idx = hash(word) % 100
                embedding[idx] += self.patent_legal_terms[word]['importance']
            elif word in self.technical_terms:
                idx = hash(word) % 100
                embedding[idx] += self.technical_terms[word]['importance']
            else:
                idx = hash(word) % 100
                embedding[idx] += 0.1

        # 归一化
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        # 生成语义标签
        semantic_tags = self._generate_semantic_tags(text)

        return SemanticVector(
            vector_id=f"text_{hash(text, dtype=np.float64)}",
            content=text,
            embedding=embedding.tolist(),
            modality=modality,
            attention_weights={},
            semantic_tags=semantic_tags,
            confidence=0.8
        )

    def _generate_semantic_tags(self, text: str) -> list[str]:
        """生成语义标签"""
        tags = []

        # 检测法律相关标签
        if any(term in text for term in self.patent_legal_terms):
            tags.append('legal_content')

        # 检测技术相关标签
        if any(term in text for term in self.technical_terms):
            tags.append('technical_content')

        # 检测数值和参数
        if re.search(r'\d+', text):
            tags.append('numeric_content')

        # 检测引用
        if re.search(r'图\s*\d+|权利要求\s*\d+', text):
            tags.append('reference_content')

        return tags

class CrossModalAttentionMechanism:
    """跨模态注意力机制"""

    def __init__(self):
        self.attention_weights = {}
        self.alignment_threshold = 0.5

    async def compute_cross_attention(self,
                                    source_vectors: list[SemanticVector],
                                    target_vectors: list[SemanticVector]) -> dict[str, dict[str, float]]:
        """计算跨模态注意力权重"""
        attention_map = {}

        if not SKLEARN_AVAILABLE:
            # 简化的注意力计算
            return self._compute_simple_attention(source_vectors, target_vectors)

        # 使用余弦相似度计算注意力
        for source_vec in source_vectors:
            attention_map[source_vec.vector_id] = {}
            source_embedding = np.array(source_vec.embedding).reshape(1, -1)

            for target_vec in target_vectors:
                target_embedding = np.array(target_vec.embedding).reshape(1, -1)

                # 计算余弦相似度
                similarity = cosine_similarity(source_embedding, target_embedding)[0][0]

                # 应用注意力阈值
                if similarity > self.alignment_threshold:
                    attention_map[source_vec.vector_id][target_vec.vector_id] = similarity

        return attention_map

    def _compute_simple_attention(self,
                                source_vectors: list[SemanticVector],
                                target_vectors: list[SemanticVector]) -> dict[str, dict[str, float]]:
        """简化的注意力计算"""
        attention_map = {}

        for source_vec in source_vectors:
            attention_map[source_vec.vector_id] = {}

            for target_vec in target_vectors:
                # 基于语义标签和内容相似度的简化计算
                similarity = self._calculate_content_similarity(source_vec.content, target_vec.content)
                tag_similarity = self._calculate_tag_similarity(source_vec.semantic_tags, target_vec.semantic_tags)

                combined_similarity = 0.7 * similarity + 0.3 * tag_similarity

                if combined_similarity > self.alignment_threshold:
                    attention_map[source_vec.vector_id][target_vec.vector_id] = combined_similarity

        return attention_map

    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """计算内容相似度"""
        # 简单的词汇重叠计算
        words1 = set(re.findall(r'[\w\u4e00-\u9fff]+', content1.lower()))
        words2 = set(re.findall(r'[\w\u4e00-\u9fff]+', content2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def _calculate_tag_similarity(self, tags1: list[str], tags2: list[str]) -> float:
        """计算标签相似度"""
        if not tags1 or not tags2:
            return 0.0

        intersection = set(tags1).intersection(set(tags2))
        union = set(tags1).union(set(tags2))

        return len(intersection) / len(union)

class SemanticRelationExtractor:
    """语义关系提取器"""

    def __init__(self):
        self.relation_patterns = {
            SemanticRelationType.REFERENCE: [
                r'根据权利要求(\d+)',
                r'如图(\d+)所示',
                r'参照图(\d+)',
                r'参见附图(\d+)'
            ],
            SemanticRelationType.COMPOSITION: [
                r'([^，。；；]+)包括([^，。；；]+)',
                r'([^，。；；]+)由([^，。；；]+)组成',
                r'([^，。；；]+)包含([^，。；；]+)'
            ],
            SemanticRelationType.SPATIAL: [
                r'([^，。；；]+)位于([^，。；；]+)',
                r'([^，。；；]+)连接到([^，。；；]+)',
                r'([^，。；；]+)设置在([^，。；；]+)'
            ],
            SemanticRelationType.EQUIVALENCE: [
                r'([^，。；；]+)即([^，。；；]+)',
                r'([^，。；；]+)也就是([^，。；；]+)'
            ]
        }

    async def extract_relations(self, vectors: list[SemanticVector]) -> list[SemanticRelation]:
        """提取语义关系"""
        relations = []

        # 基于模式匹配的关系提取
        pattern_relations = self._extract_pattern_relations(vectors)
        relations.extend(pattern_relations)

        # 基于语义相似性的关系提取
        semantic_relations = self._extract_semantic_relations(vectors)
        relations.extend(semantic_relations)

        # 去重和排序
        relations = self._deduplicate_relations(relations)
        relations.sort(key=lambda x: x.strength, reverse=True)

        return relations

    def _extract_pattern_relations(self, vectors: list[SemanticVector]) -> list[SemanticRelation]:
        """基于模式匹配提取关系"""
        relations = []

        for vector in vectors:
            content = vector.content

            for relation_type, patterns in self.relation_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, content)

                    for match in matches:
                        if isinstance(match, tuple):
                            source_entity, target_entity = match
                        else:
                            target_entity = ''

                        relation = SemanticRelation(
                            relation_id=f"{relation_type.value}_{hash(content)}",
                            source_vector=vector.vector_id,
                            target_vector=f"entity_{hash(target_entity)}",
                            relation_type=relation_type,
                            strength=0.8,
                            evidence=[content],
                            confidence=0.7
                        )
                        relations.append(relation)

        return relations

    def _extract_semantic_relations(self, vectors: list[SemanticVector]) -> list[SemanticRelation]:
        """基于语义相似性提取关系"""
        relations = []

        for i, vec1 in enumerate(vectors):
            for j, vec2 in enumerate(vectors):
                if i >= j:  # 避免重复
                    continue

                # 计算语义相似性
                similarity = self._calculate_semantic_similarity(vec1, vec2)

                if similarity > 0.7:
                    relation = SemanticRelation(
                        relation_id=f"semantic_{i}_{j}",
                        source_vector=vec1.vector_id,
                        target_vector=vec2.vector_id,
                        relation_type=SemanticRelationType.EQUIVALENCE,
                        strength=similarity,
                        evidence=[vec1.content, vec2.content],
                        confidence=similarity
                    )
                    relations.append(relation)

        return relations

    def _calculate_semantic_similarity(self, vec1: SemanticVector, vec2: SemanticVector) -> float:
        """计算语义相似性"""
        # 标签相似性
        tags1 = set(vec1.semantic_tags)
        tags2 = set(vec2.semantic_tags)

        if not tags1 and not tags2:
            tag_sim = 0.0
        else:
            tag_intersection = len(tags1.intersection(tags2))
            tag_union = max(len(tags1), len(tags2))
            tag_sim = tag_intersection / tag_union if tag_union > 0 else 0.0

        # 内容相似性
        words1 = set(re.findall(r'[\w\u4e00-\u9fff]+', vec1.content.lower()))
        words2 = set(re.findall(r'[\w\u4e00-\u9fff]+', vec2.content.lower()))

        if words1 and words2:
            content_sim = len(words1.intersection(words2)) / len(words1.union(words2))
        else:
            content_sim = 0.0

        # 综合相似性
        return 0.6 * content_sim + 0.4 * tag_sim

    def _deduplicate_relations(self, relations: list[SemanticRelation]) -> list[SemanticRelation]:
        """去重关系"""
        seen = set()
        deduplicated = []

        for relation in relations:
            key = (relation.source_vector, relation.target_vector, relation.relation_type)
            if key not in seen:
                seen.add(key)
                deduplicated.append(relation)

        return deduplicated

class SemanticFusionEngine:
    """语义融合引擎 - 核心类"""

    def __init__(self):
        self.embedding_engine = SemanticEmbeddingEngine()
        self.attention_mechanism = CrossModalAttentionMechanism()
        self.relation_extractor = SemanticRelationExtractor()
        self.fusion_history = []

        logger.info('🧠 语义融合引擎初始化完成')

    async def fuse_modalities(self,
                             modalities: dict[str, list[dict[str, Any]]]) -> FusionResult:
        """融合多模态语义"""
        logger.info(f"🔄 开始语义融合，模态数量: {len(modalities)}")

        try:
            # 1. 为每个模态生成语义向量
            semantic_vectors = await self._generate_semantic_vectors(modalities)

            # 2. 计算跨模态注意力
            attention_map = await self._compute_attention_maps(semantic_vectors)

            # 3. 提取语义关系
            semantic_relations = await self.relation_extractor.extract_relations(semantic_vectors)

            # 4. 执行语义融合
            unified_representation = await self._perform_fusion(semantic_vectors, attention_map)

            # 5. 计算一致性分数
            consistency_score = self._calculate_consistency(semantic_vectors, attention_map, semantic_relations)

            # 创建融合结果
            fusion_result = FusionResult(
                fusion_id=f"fusion_{len(self.fusion_history)}",
                unified_representation=unified_representation.tolist(),
                contributing_modalities=list(modalities.keys()),
                attention_map=attention_map,
                semantic_relations=semantic_relations,
                consistency_score=consistency_score
            )

            self.fusion_history.append(fusion_result)
            logger.info(f"✅ 语义融合完成，一致性分数: {consistency_score:.3f}")

            return fusion_result

        except Exception as e:
            logger.error(f"❌ 语义融合失败: {str(e)}")
            raise

    async def _generate_semantic_vectors(self, modalities: dict[str, list[dict[str, Any]]]) -> list[SemanticVector]:
        """生成语义向量"""
        vectors = []

        for modality_type, modality_list in modalities.items():
            for modality in modality_list:
                if modality_type == 'text':
                    vector = await self.embedding_engine.encode_text(
                        modality.get('content', ''), modality_type
                    )
                    vectors.append(vector)

                elif modality_type == 'image':
                    # 处理图像模态
                    ocr_text = modality.get('ocr_text', '')
                    if ocr_text:
                        vector = await self.embedding_engine.encode_text(ocr_text, modality_type)
                        vectors.append(vector)

                elif modality_type == 'table':
                    # 处理表格模态
                    table_content = modality.get('content', '')
                    if isinstance(table_content, dict):
                        # 转换表格为文本
                        text_content = self._convert_table_to_text(table_content)
                        vector = await self.embedding_engine.encode_text(text_content, modality_type)
                        vectors.append(vector)

        return vectors

    def _convert_table_to_text(self, table_content: dict[str, Any]) -> str:
        """将表格内容转换为文本"""
        text_parts = []

        if 'headers' in table_content:
            text_parts.append('表头: ' + ' | '.join(table_content['headers']))

        if 'rows' in table_content:
            for i, row in enumerate(table_content['rows']):
                row_text = f"第{i+1}行: ' + ' | ".join(str(cell) for cell in row)
                text_parts.append(row_text)

        if 'title' in table_content:
            text_parts.insert(0, f"表格标题: {table_content['title']}")

        return "\n".join(text_parts)

    async def _compute_attention_maps(self, vectors: list[SemanticVector]) -> dict[str, dict[str, float]]:
        """计算注意力图谱"""
        attention_map = {}

        # 按模态分组向量
        modality_groups = {}
        for vector in vectors:
            if vector.modality not in modality_groups:
                modality_groups[vector.modality] = []
            modality_groups[vector.modality].append(vector)

        # 计算跨模态注意力
        modality_types = list(modality_groups.keys())
        for i, mod1 in enumerate(modality_types):
            for j, mod2 in enumerate(modality_types):
                if i <= j:  # 包含自注意力
                    cross_attention = await self.attention_mechanism.compute_cross_attention(
                        modality_groups[mod1], modality_groups[mod2]
                    )

                    # 合并到总的注意力图谱
                    for source_id, targets in cross_attention.items():
                        if source_id not in attention_map:
                            attention_map[source_id] = {}
                        attention_map[source_id].update(targets)

        return attention_map

    async def _perform_fusion(self,
                             vectors: list[SemanticVector],
                             attention_map: dict[str, dict[str, float]]) -> np.ndarray:
        """执行语义融合"""
        if not vectors:
            return zeros(100)

        # 计算加权平均
        total_weight = 0
        weighted_sum = np.zeros(100)

        for vector in vectors:
            # 计算每个向量的权重
            weight = vector.confidence

            # 考虑注意力权重
            if vector.vector_id in attention_map:
                attention_weight = np.mean(list(attention_map[vector.vector_id].values()))
                weight *= (1 + attention_weight)

            weighted_sum += weight * np.array(vector.embedding)
            total_weight += weight

        if total_weight > 0:
            return weighted_sum / total_weight
        else:
            return np.mean([np.array(v.embedding, dtype=np.float64) for v in vectors], axis=0)

    def _calculate_consistency(self,
                              vectors: list[SemanticVector],
                              attention_map: dict[str, dict[str, float]],
                              relations: list[SemanticRelation]) -> float:
        """计算一致性分数"""
        consistency_factors = []

        # 1. 注意力一致性
        if attention_map:
            attention_values = []
            for source_targets in attention_map.values():
                attention_values.extend(source_targets.values())

            if attention_values:
                attention_consistency = np.mean(attention_values)
                consistency_factors.append(attention_consistency)

        # 2. 关系强度一致性
        if relations:
            relation_strengths = [r.strength for r in relations]
            relation_consistency = np.mean(relation_strengths)
            consistency_factors.append(relation_consistency)

        # 3. 置信度一致性
        if vectors:
            confidences = [v.confidence for v in vectors]
            confidence_consistency = np.mean(confidences)
            consistency_factors.append(confidence_consistency)

        # 综合一致性分数
        if consistency_factors:
            return np.mean(consistency_factors)
        else:
            return 0.0

    def get_fusion_statistics(self) -> dict[str, Any]:
        """获取融合统计信息"""
        if not self.fusion_history:
            return {'total_fusions': 0}

        return {
            'total_fusions': len(self.fusion_history),
            'average_consistency': np.mean([f.consistency_score for f in self.fusion_history]),
            'modalities_processed': set(),
            'relations_extracted': sum([len(f.semantic_relations) for f in self.fusion_history])
        }

# 测试代码
if __name__ == '__main__':
    async def test_semantic_fusion():
        """测试语义融合引擎"""
        engine = SemanticFusionEngine()

        # 模拟多模态数据
        modalities = {
            'text': [
                {'content': '本实用新型涉及一种甲醇精馏装置，包括精馏塔和冷凝器。'},
                {'content': '权利要求1所述的装置，其特征在于所述冷凝器与精馏塔顶部连接。'}
            ],
            'image': [
                {
                    'ocr_text': '图1：甲醇精馏装置结构示意图',
                    'content': '图示显示精馏塔1，冷凝器2，连接管道3'
                }
            ],
            'table': [
                {
                    'title': '技术参数表',
                    'headers': ['参数', '数值', '单位'],
                    'rows': [
                        ['精馏温度', '65', '°C'],
                        ['处理能力', '100', 'kg/h']
                    ]
                }
            ]
        }

        logger.info('🧠 测试语义融合引擎...')

        result = await engine.fuse_modalities(modalities)

        logger.info("✅ 融合完成:")
        logger.info(f"  融合ID: {result.fusion_id}")
        logger.info(f"  参与模态: {', '.join(result.contributing_modalities)}")
        logger.info(f"  语义关系: {len(result.semantic_relations)}个")
        logger.info(f"  一致性分数: {result.consistency_score:.3f}")

        # 显示注意力图谱
        logger.info("\n🔗 注意力图谱:")
        for source, targets in list(result.attention_map.items())[:3]:  # 显示前3个
            logger.info(f"  {source}: {len(targets)}个连接")

        # 显示语义关系
        logger.info("\n📋 语义关系:")
        for relation in result.semantic_relations[:3]:  # 显示前3个
            logger.info(f"  {relation.relation_type.value}: {relation.strength:.3f}")

        # 获取统计信息
        stats = engine.get_fusion_statistics()
        logger.info(f"\n📊 融合统计: {stats}")

    # 运行测试
    asyncio.run(test_semantic_fusion())
