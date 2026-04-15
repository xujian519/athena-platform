#!/usr/bin/env python3
"""
增强专利特征提取器
Enhanced Patent Feature Extractor

集成BERT模型提升语义理解能力
结合规则和深度学习进行专利特征提取

作者: Athena (小娜)
创建时间: 2025-12-05
版本: 2.0.0
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np

# AI模型集成
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoModel, AutoTokenizer

# 本地导入 - 暂时注释掉不存在的模块
# sys.path.append(str(Path(__file__).parent.parent.parent))
# from core.cognition.ollama_integration import OllamaNLPIntegration
# from core.memory.vector_memory import VectorMemory

# 简化的模拟类
class OllamaNLPIntegration:
    """模拟的Ollama NLP集成"""
    def __init__(self, name):
        self.name = name

    async def initialize(self):
        pass

    async def generate_response(self, prompt):
        # 简单的响应模拟
        if '技术性' in prompt or 'technical' in prompt.lower():
            return 'technical'
        elif '功能性' in prompt or 'functional' in prompt.lower():
            return 'functional'
        elif '结构性' in prompt or 'structural' in prompt.lower():
            return 'structural'
        elif '性能性' in prompt or 'performance' in prompt.lower():
            return 'performance'
        elif '法律性' in prompt or 'legal' in prompt.lower():
            return 'legal'
        else:
            return 'technical'

class VectorMemory:
    """模拟的向量记忆系统"""
    def __init__(self, agent_id, vector_dim):
        self.agent_id = agent_id
        self.vector_dim = vector_dim

    async def initialize(self):
        pass

    async def store_memory(self, content, embedding, metadata):
        pass

logger = logging.getLogger(__name__)

class FeatureCategory(Enum):
    """特征类别枚举"""
    STRUCTURAL = 'structural'      # 结构特征
    FUNCTIONAL = 'functional'      # 功能特征
    PERFORMANCE = 'performance'    # 性能特征
    SEMANTIC = 'semantic'          # 语义特征
    LEGAL = 'legal'                # 法律特征
    TECHNICAL = 'technical'        # 技术特征

@dataclass
class EnhancedFeature:
    """增强特征类"""
    feature_id: str
    category: FeatureCategory
    text: str
    confidence: float
    weight: float
    semantic_embedding: np.ndarray | None = None
    relations: list[dict[str, Any]] = None
    context: dict[str, Any] = None
    extraction_method: str = 'hybrid'

class BERTEnhancedExtractor:
    """BERT增强特征提取器"""

    def __init__(self):
        self.model_name = 'bert-base-chinese'
        self.sentence_model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'

        # 初始化模型
        self.tokenizer = None
        self.bert_model = None
        self.sentence_model = None
        self.ollama_integration = None

        # 特征提取规则
        self.feature_patterns = self._load_feature_patterns()

        # 缓存系统
        self.feature_cache = {}
        self.vector_memory = None

        self._initialized = False

    async def initialize(self):
        """初始化模型"""
        if self._initialized:
            return

        try:
            logger.info('🤖 初始化BERT增强特征提取器...')

            # 初始化BERT模型
            logger.info('📥 加载BERT模型...')
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.bert_model = AutoModel.from_pretrained(self.model_name)

            # 初始化句向量模型
            logger.info('📥 加载句子向量模型...')
            self.sentence_model = SentenceTransformer(self.sentence_model_name)

            # 初始化Ollama集成
            logger.info('🔗 初始化Ollama集成...')
            self.ollama_integration = OllamaNLPIntegration('bert_enhanced_extractor')
            await self.ollama_integration.initialize()

            # 初始化向量记忆
            logger.info('🧠 初始化向量记忆系统...')
            self.vector_memory = VectorMemory(
                agent_id='enhanced_patent_extractor',
                vector_dim=768
            )
            await self.vector_memory.initialize()

            self._initialized = True
            logger.info('✅ BERT增强特征提取器初始化完成')

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            raise

    def _load_feature_patterns(self) -> dict[FeatureCategory, list[dict]]:
        """加载特征提取规则"""
        return {
            FeatureCategory.STRUCTURAL: [
                {
                    'pattern': r"包括|包含|具有|设有|配置有",
                    'keywords': ['包括', '包含', '具有', '设有', '配置有'],
                    'weight': 0.8
                },
                {
                    'pattern': r"由.*组成|由.*构成",
                    'keywords': ['由...组成', '由...构成'],
                    'weight': 0.9
                }
            ],
            FeatureCategory.FUNCTIONAL: [
                {
                    'pattern': r"用于|实现|能够|可以|适用于",
                    'keywords': ['用于', '实现', '能够', '可以', '适用于'],
                    'weight': 0.85
                },
                {
                    'pattern': r"通过.*方式|采用.*方法",
                    'keywords': ['通过', '采用', '方式', '方法'],
                    'weight': 0.8
                }
            ],
            FeatureCategory.PERFORMANCE: [
                {
                    'pattern': r"提高|改善|增强|优化|减少",
                    'keywords': ['提高', '改善', '增强', '优化', '减少'],
                    'weight': 0.9
                },
                {
                    'pattern': r"精度|效率|速度|性能|稳定性",
                    'keywords': ['精度', '效率', '速度', '性能', '稳定性'],
                    'weight': 0.85
                }
            ],
            FeatureCategory.LEGAL: [
                {
                    'pattern': r"专利|发明|创造|新颖性|创造性",
                    'keywords': ['专利', '发明', '创造', '新颖性', '创造性'],
                    'weight': 0.9
                },
                {
                    'pattern': r"现有技术|对比文件|公知常识",
                    'keywords': ['现有技术', '对比文件', '公知常识'],
                    'weight': 0.85
                }
            ],
            FeatureCategory.TECHNICAL: [
                {
                    'pattern': r"算法|系统|设备|装置|模块",
                    'keywords': ['算法', '系统', '设备', '装置', '模块'],
                    'weight': 0.8
                },
                {
                    'pattern': r"数据|信号|处理|分析|计算",
                    'keywords': ['数据', '信号', '处理', '分析', '计算'],
                    'weight': 0.85
                }
            ]
        }

    async def extract_features(self, text: str, patent_context: dict | None = None) -> list[EnhancedFeature]:
        """提取增强特征"""
        if not self._initialized:
            await self.initialize()

        logger.info(f"🔍 开始提取专利特征，文本长度: {len(text)}")

        # 检查缓存
        cache_key = hash(text)
        if cache_key in self.feature_cache:
            logger.info('💾 从缓存获取特征')
            return self.feature_cache[cache_key]

        features = []

        # 1. 基于规则的特征提取
        rule_features = await self._extract_rule_based_features(text)
        features.extend(rule_features)

        # 2. 基于BERT的语义特征提取
        semantic_features = await self._extract_semantic_features(text)
        features.extend(semantic_features)

        # 3. 基于句子向量的特征提取
        vector_features = await self._extract_vector_features(text)
        features.extend(vector_features)

        # 4. 特征关系挖掘
        await self._mine_feature_relations(features)

        # 5. 特征权重优化
        features = await self._optimize_feature_weights(features, patent_context)

        # 缓存结果
        self.feature_cache[cache_key] = features

        logger.info(f"✅ 特征提取完成，共提取 {len(features)} 个特征")
        return features

    async def _extract_rule_based_features(self, text: str) -> list[EnhancedFeature]:
        """基于规则的特征提取"""
        features = []
        sentences = self._split_into_sentences(text)

        for i, sentence in enumerate(sentences):
            for category, patterns in self.feature_patterns.items():
                for pattern_info in patterns:
                    matches = re.findall(pattern_info['pattern'], sentence)
                    for match in matches:
                        feature = EnhancedFeature(
                            feature_id=f"rule_{category.value}_{i}_{len(features)}",
                            category=category,
                            text=match.strip(),
                            confidence=0.8,
                            weight=pattern_info['weight'],
                            extraction_method='rule_based',
                            context={'sentence_index': i, 'full_sentence': sentence}
                        )
                        features.append(feature)

        return features

    async def _extract_semantic_features(self, text: str) -> list[EnhancedFeature]:
        """基于BERT的语义特征提取"""
        features = []

        try:
            # 分句处理
            sentences = self._split_into_sentences(text)

            for i, sentence in enumerate(sentences):
                if len(sentence.strip()) < 5:  # 跳过太短的句子
                    continue

                # BERT编码
                inputs = self.tokenizer(
                    sentence,
                    return_tensors='pt',
                    max_length=512,
                    truncation=True,
                    padding=True
                )

                with torch.no_grad():
                    outputs = self.bert_model(**inputs)

                    # 获取[CLS]向量作为句子表示
                    sentence_embedding = outputs.last_hidden_state[:, 0, :].numpy()

                # 语义特征分类
                semantic_category = await self._classify_semantic_feature(sentence)

                feature = EnhancedFeature(
                    feature_id=f"semantic_{semantic_category}_{i}",
                    category=FeatureCategory.SEMANTIC,
                    text=sentence.strip(),
                    confidence=0.9,
                    weight=0.85,
                    semantic_embedding=sentence_embedding.flatten(),
                    extraction_method='bert_semantic',
                    context={'sentence_index': i, 'semantic_category': semantic_category}
                )
                features.append(feature)

        except Exception as e:
            logger.error(f"❌ BERT语义特征提取失败: {e}")

        return features

    async def _extract_vector_features(self, text: str) -> list[EnhancedFeature]:
        """基于句子向量的特征提取"""
        features = []

        try:
            # 使用句子向量模型
            sentences = self._split_into_sentences(text)

            # 批量编码句子
            sentence_embeddings = self.sentence_model.encode(
                sentences,
                batch_size=16,
                show_progress_bar=False
            )

            for i, (sentence, embedding) in enumerate(zip(sentences, sentence_embeddings, strict=False)):
                if len(sentence.strip()) < 5:
                    continue

                # 基于向量相似度进行特征分类
                feature_category = await self._classify_vector_feature(embedding)

                feature = EnhancedFeature(
                    feature_id=f"vector_{feature_category}_{i}",
                    category=feature_category,
                    text=sentence.strip(),
                    confidence=0.85,
                    weight=0.8,
                    semantic_embedding=embedding,
                    extraction_method='sentence_transformer',
                    context={'sentence_index': i, 'embedding_norm': np.linalg.norm(embedding)}
                )
                features.append(feature)

                # 存储到向量记忆
                if self.vector_memory:
                    await self.vector_memory.store_memory(
                        content=sentence,
                        embedding=embedding,
                        metadata={
                            'feature_id': feature.feature_id,
                            'category': feature_category.value,
                            'extraction_method': 'sentence_transformer'
                        }
                    )

        except Exception as e:
            logger.error(f"❌ 向量特征提取失败: {e}")

        return features

    async def _classify_semantic_feature(self, sentence: str) -> str:
        """使用Ollama分类语义特征"""
        try:
            prompt = f"""
请分析以下专利文本的语义特征类别，从以下选项中选择最合适的：
- technical: 技术性描述
- functional: 功能性描述
- structural: 结构性描述
- performance: 性能性描述
- legal: 法律性描述

文本：{sentence}

请只返回类别名称，不要解释。
"""

            response = await self.ollama_integration.generate_response(prompt)
            return response.strip().lower()

        except Exception as e:
            logger.warning(f"⚠️ 语义分类失败，使用默认值: {e}")
            return 'technical'

    async def _classify_vector_feature(self, embedding: np.ndarray) -> FeatureCategory:
        """基于向量分类特征类别"""
        # 简单的基于向量特征的分类
        norm = np.linalg.norm(embedding)

        # 这里可以实现更复杂的分类逻辑
        # 比如使用预训练的分类器或聚类
        if norm > 0.8:
            return FeatureCategory.TECHNICAL
        elif norm > 0.6:
            return FeatureCategory.FUNCTIONAL
        else:
            return FeatureCategory.STRUCTURAL

    async def _mine_feature_relations(self, features: list[EnhancedFeature]):
        """挖掘特征关系"""
        try:
            for i, feature1 in enumerate(features):
                relations = []

                for j, feature2 in enumerate(features):
                    if i != j:
                        # 计算语义相似度
                        similarity = self._calculate_semantic_similarity(feature1, feature2)

                        if similarity > 0.7:  # 相似度阈值
                            relations.append({
                                'feature_id': feature2.feature_id,
                                'similarity': similarity,
                                'relation_type': 'semantic_similarity'
                            })

                feature1.relations = relations

        except Exception as e:
            logger.warning(f"⚠️ 特征关系挖掘失败: {e}")

    def _calculate_semantic_similarity(self, feature1: EnhancedFeature, feature2: EnhancedFeature) -> float:
        """计算语义相似度"""
        if feature1.semantic_embedding is None or feature2.semantic_embedding is None:
            return 0.0

        # 使用余弦相似度
        vec1 = feature1.semantic_embedding
        vec2 = feature2.semantic_embedding

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    async def _optimize_feature_weights(self, features: list[EnhancedFeature], context: dict | None = None):
        """优化特征权重"""
        try:
            # 基于上下文调整权重
            if context:
                patent_type = context.get('patent_type', 'unknown')
                context.get('technical_domain', 'unknown')

                for feature in features:
                    # 根据专利类型调整权重
                    if patent_type == 'invention' and feature.category == FeatureCategory.LEGAL:
                        feature.weight *= 1.2
                    elif patent_type == 'utility_model' and feature.category == FeatureCategory.TECHNICAL:
                        feature.weight *= 1.1

            # 标准化权重
            total_weight = sum(f.weight for f in features)
            if total_weight > 0:
                for feature in features:
                    feature.weight = feature.weight / total_weight

        except Exception as e:
            logger.warning(f"⚠️ 特征权重优化失败: {e}")

        return features

    def _split_into_sentences(self, text: str) -> list[str]:
        """分割文本为句子"""
        # 简单的句子分割，可以改进为更复杂的分割算法
        sentences = re.split(r'[。！？；;]', text)
        return [s.strip() for s in sentences if s.strip()]

    async def analyze_feature_importance(self, features: list[EnhancedFeature]) -> dict[str, Any]:
        """分析特征重要性"""
        analysis = {
            'total_features': len(features),
            'category_distribution': {},
            'average_confidence': 0.0,
            'high_confidence_features': 0,
            'feature_relations': 0,
            'recommendations': []
        }

        # 统计类别分布
        for feature in features:
            category = feature.category.value
            if category not in analysis['category_distribution']:
                analysis['category_distribution'][category] = 0
            analysis['category_distribution'][category] += 1

        # 计算平均置信度
        if features:
            analysis['average_confidence'] = sum(f.confidence for f in features) / len(features)
            analysis['high_confidence_features'] = sum(1 for f in features if f.confidence > 0.8)

        # 统计关系数量
        analysis['feature_relations'] = sum(len(f.relations or []) for f in features)

        # 生成建议
        if analysis['average_confidence'] < 0.7:
            analysis['recommendations'].append('建议增加更多训练数据以提升特征识别置信度')

        if analysis['high_confidence_features'] < len(features) * 0.5:
            analysis['recommendations'].append('考虑优化特征提取规则以提高准确性')

        return analysis

class PatentCognitiveProcessor:
    """专利认知处理器"""

    def __init__(self):
        self.feature_extractor = BERTEnhancedExtractor()
        self._initialized = False

    async def initialize(self):
        """初始化处理器"""
        if not self._initialized:
            await self.feature_extractor.initialize()
            self._initialized = True
            logger.info('✅ 专利认知处理器初始化完成')

    async def process_patent_text(self, text: str, patent_info: dict | None = None) -> dict[str, Any]:
        """处理专利文本"""
        if not self._initialized:
            await self.initialize()

        logger.info(f"🧠 开始处理专利文本，长度: {len(text)}")

        # 提取特征
        features = await self.feature_extractor.extract_features(text, patent_info)

        # 分析特征
        feature_analysis = await self.feature_extractor.analyze_feature_importance(features)

        # 生成认知理解
        cognitive_understanding = await self._generate_cognitive_understanding(features, patent_info)

        result = {
            'features': [
                {
                    'feature_id': f.feature_id,
                    'category': f.category.value,
                    'text': f.text,
                    'confidence': f.confidence,
                    'weight': f.weight,
                    'extraction_method': f.extraction_method,
                    'relations': f.relations or []
                }
                for f in features
            ],
            'analysis': feature_analysis,
            'cognitive_understanding': cognitive_understanding,
            'processing_metadata': {
                'text_length': len(text),
                'feature_count': len(features),
                'processing_time': None,  # 可以添加时间戳
                'model_info': {
                    'bert_model': self.feature_extractor.model_name,
                    'sentence_model': self.feature_extractor.sentence_model_name
                }
            }
        }

        logger.info('✅ 专利认知处理完成')
        return result

    async def _generate_cognitive_understanding(self, features: list[EnhancedFeature], patent_info: dict | None = None) -> dict[str, Any]:
        """生成认知理解"""
        understanding = {
            'patent_summary': '',
            'key_technical_points': [],
            'functional_aspects': [],
            'performance_indicators': [],
            'legal_considerations': [],
            'innovation_level': 'medium',
            'complexity_score': 0.5
        }

        try:
            # 按类别组织特征
            features_by_category = {}
            for feature in features:
                category = feature.category
                if category not in features_by_category:
                    features_by_category[category] = []
                features_by_category[category].append(feature)

            # 提取关键信息
            if FeatureCategory.TECHNICAL in features_by_category:
                technical_features = features_by_category[FeatureCategory.TECHNICAL]
                understanding['key_technical_points'] = [
                    f.text for f in technical_features if f.confidence > 0.7
                ][:5]  # 取前5个高置信度特征

            if FeatureCategory.FUNCTIONAL in features_by_category:
                functional_features = features_by_category[FeatureCategory.FUNCTIONAL]
                understanding['functional_aspects'] = [
                    f.text for f in functional_features if f.confidence > 0.7
                ][:5]

            if FeatureCategory.PERFORMANCE in features_by_category:
                performance_features = features_by_category[FeatureCategory.PERFORMANCE]
                understanding['performance_indicators'] = [
                    f.text for f in performance_features if f.confidence > 0.7
                ][:5]

            if FeatureCategory.LEGAL in features_by_category:
                legal_features = features_by_category[FeatureCategory.LEGAL]
                understanding['legal_considerations'] = [
                    f.text for f in legal_features if f.confidence > 0.7
                ][:5]

            # 计算创新水平
            innovation_score = self._calculate_innovation_score(features)
            if innovation_score > 0.8:
                understanding['innovation_level'] = 'high'
            elif innovation_score < 0.4:
                understanding['innovation_level'] = 'low'

            # 计算复杂度分数
            understanding['complexity_score'] = self._calculate_complexity_score(features)

        except Exception as e:
            logger.warning(f"⚠️ 认知理解生成失败: {e}")

        return understanding

    def _calculate_innovation_score(self, features: list[EnhancedFeature]) -> float:
        """计算创新水平分数"""
        score = 0.0
        total_weight = 0.0

        innovation_keywords = ['新颖', '创新', '独特', '首创', '突破', '改进']

        for feature in features:
            feature_score = 0.0
            for keyword in innovation_keywords:
                if keyword in feature.text:
                    feature_score += 0.2
            feature_score = min(feature_score, 1.0)  # 限制最大值为1

            score += feature_score * feature.weight
            total_weight += feature.weight

        return score / total_weight if total_weight > 0 else 0.0

    def _calculate_complexity_score(self, features: list[EnhancedFeature]) -> float:
        """计算复杂度分数"""
        if not features:
            return 0.0

        # 基于特征数量、关系数量和置信度的复杂度计算
        feature_count = len(features)
        relation_count = sum(len(f.relations or []) for f in features)
        avg_confidence = sum(f.confidence for f in features) / len(features)

        # 归一化复杂度分数
        complexity = (feature_count * 0.3 + relation_count * 0.3 + avg_confidence * 0.4) / 10.0
        return min(complexity, 1.0)

async def main():
    """测试函数"""
    processor = PatentCognitiveProcessor()
    await processor.initialize()

    # 测试文本
    test_text = """
    本发明涉及一种智能专利分析系统，包括：图像采集模块，用于采集多模态医疗图像数据，
    预处理模块，采用自适应算法进行图像标准化和增强，特征提取模块，使用改进的残差网络和注意力机制提取关键特征，
    分类模块，基于深度学习算法实现高精度疾病分类，优化模块，通过强化学习动态调整模型参数，
    能够实现高精度疾病分类，显著提高医疗诊断的准确性和效率。
    """

    result = await processor.process_patent_text(test_text)

    logger.info('🧠 专利认知处理结果:')
    logger.info(f"特征数量: {result['analysis']['total_features']}")
    logger.info(f"类别分布: {result['analysis']['category_distribution']}")
    logger.info(f"平均置信度: {result['analysis']['average_confidence']:.2f}")
    logger.info(f"高置信度特征: {result['analysis']['high_confidence_features']}")
    logger.info("\n认知理解:")
    understanding = result['cognitive_understanding']
    logger.info(f"创新水平: {understanding['innovation_level']}")
    logger.info(f"复杂度分数: {understanding['complexity_score']:.2f}")
    logger.info(f"技术要点: {len(understanding['key_technical_points'])} 个")
    logger.info(f"功能方面: {len(understanding['functional_aspects'])} 个")

if __name__ == '__main__':
    asyncio.run(main())
