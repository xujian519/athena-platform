#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模型向量融合器
Multi-Model Vectorizer

使用多个BERT模型进行向量化并融合结果
"""

import logging
import os
import pickle
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
from intelligent_model_selector import IntelligentModelSelector
from model_manager import ChineseBERTModelManager

# 配置日志
logger = logging.getLogger(__name__)

class MultiModelVectorizer:
    """多模型向量融合器"""

    def __init__(
        self,
        cache_dir: str = '/Users/xujian/Athena工作平台/patent_hybrid_retrieval/cache',
        max_cache_size: int = 10000
    ):
        """初始化多模型向量器

        Args:
            cache_dir: 缓存目录
            max_cache_size: 最大缓存条目数
        """
        self.model_manager = ChineseBERTModelManager()
        self.selector = IntelligentModelSelector()
        self.cache_dir = cache_dir
        self.max_cache_size = max_cache_size
        self.vector_cache = {}

        # 融合策略
        self.fusion_strategies = {
            'concatenation': self._concatenation_fusion,
            'weighted_average': self._weighted_average_fusion,
            'attention_fusion': self._attention_fusion,
            'adaptive_fusion': self._adaptive_fusion
        }

        # 性能统计
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'model_switches': defaultdict(int),
            'fusion_times': defaultdict(list),
            'last_updated': datetime.now()
        }

    def encode_with_multiple_models(
        self,
        texts: List[str],
        model_config: Optional[Dict[str, Any]] = None,
        fusion_strategy: str = 'weighted_average',
        return_individual: bool = False
    ) -> Dict[str, Any]:
        """使用多个模型编码文本

        Args:
            texts: 文本列表
            model_config: 模型配置
                {
                    'models': ['model1', 'model2', ...],  # 指定模型列表
                    'auto_select': True,  # 自动选择模型
                    'max_models': 3,  # 最大模型数
                    'weights': [0.5, 0.3, 0.2]  # 模型权重
                }
            fusion_strategy: 融合策略
            return_individual: 是否返回各模型的独立结果

        Returns:
            {
                'fused_vector': 融合后的向量,
                'individual_vectors': 各模型的独立向量（如果return_individual=True）,
                'model_info': 使用的模型信息,
                'fusion_info': 融合过程信息
            }
        """
        start_time = datetime.now()
        self.stats['total_requests'] += 1

        # 检查缓存
        cache_key = self._get_cache_key(texts, model_config, fusion_strategy)
        if cache_key in self.vector_cache:
            self.stats['cache_hits'] += 1
            cached_result = self.vector_cache[cache_key]
            cached_result['from_cache'] = True
            return cached_result

        # 确定使用的模型
        if not model_config:
            model_config = {
                'auto_select': True,
                'max_models': 3
            }

        model_names = model_config.get('models', [])
        if not model_names or model_config.get('auto_select', False):
            if texts:
                # 使用第一个查询文本进行模型选择
                model_names = [name for name, _, _ in self.selector.select_models_for_ensemble(texts[0], model_config.get('max_models', 3))]
            else:
                model_names = ['bge-base-zh-v1.5']

        # 限制模型数量
        max_models = model_config.get('max_models', len(model_names))
        model_names = model_names[:max_models]

        # 获取权重
        weights = model_config.get('weights', [1.0] * len(model_names))
        if len(weights) != len(model_names):
            weights = [1.0] * len(model_names)

        # 归一化权重
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]

        # 加载模型
        model_info = {}
        for model_name in model_names:
            if self.model_manager.load_model(model_name):
                model_info[model_name] = self.model_manager.get_model_info(model_name)
                self.stats['model_switches'][model_name] += 1
            else:
                logger.warning(f"模型 {model_name} 加载失败")

        # 多模型编码
        embeddings = {}
        dimensions = set()

        def encode_with_model(model_name):
            """单个模型编码"""
            if model_name not in model_info:
                return model_name, None

            try:
                vectors = self.model_manager.encode_texts(texts, model_name=model_name)
                return model_name, vectors
            except Exception as e:
                logger.error(f"模型 {model_name} 编码失败: {e}")
                return model_name, None

        # 并行编码
        with ThreadPoolExecutor(max_workers=min(4, len(model_names))) as executor:
            futures = {executor.submit(encode_with_model, name): name for name in model_names}

            for future in as_completed(futures):
                model_name, vectors = future.result()
                if vectors is not None:
                    embeddings[model_name] = vectors
                    dimensions.add(vectors.shape[1])

        # 检查是否有成功的编码
        if not embeddings:
            logger.error('没有模型成功编码')
            return {'error': 'no_successful_encodings'}

        # 融合向量
        fusion_start = datetime.now()
        fusion_func = self.fusion_strategies.get(fusion_strategy, self._weighted_average_fusion)

        try:
            fused_vector, fusion_info = fusion_func(embeddings, weights)
        except Exception as e:
            logger.error(f"向量融合失败: {e}")
            # 回退到简单平均
            fused_vector, fusion_info = self._simple_average_fusion(embeddings, weights)

        fusion_time = (datetime.now() - fusion_start).total_seconds()
        self.stats['fusion_times'][fusion_strategy].append(fusion_time)

        # 准备结果
        result = {
            'fused_vector': fused_vector,
            'model_info': model_info,
            'fusion_info': {
                'strategy': fusion_strategy,
                'models_used': list(embeddings.keys()),
                'weights': weights,
                'dimensions': list(dimensions),
                'fusion_time': fusion_time,
                'details': fusion_info
            },
            'from_cache': False
        }

        if return_individual:
            result['individual_vectors'] = embeddings

        # 缓存结果
        self._cache_result(cache_key, result)

        # 更新统计
        total_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"多模型编码完成: {len(texts)} 个文本, {len(embeddings)} 个模型, 耗时 {total_time:.3f}s")

        return result

    def _concatenation_fusion(
        self,
        embeddings: Dict[str, np.ndarray],
        weights: List[float]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """拼接融合策略"""
        vectors = list(embeddings.values())
        max_length = max(v.shape[1] for v in vectors)

        # 填充到相同维度
        padded_vectors = []
        for v in vectors:
            if v.shape[1] < max_length:
                padding = np.zeros((v.shape[0], max_length - v.shape[1]))
                v_padded = np.hstack([v, padding])
            else:
                v_padded = v
            padded_vectors.append(v_padded)

        # 拼接
        fused = np.hstack(padded_vectors)

        fusion_info = {
            'method': 'concatenation',
            'input_dimensions': [v.shape[1] for v in vectors],
            'output_dimension': fused.shape[1],
            'padding_used': any(v.shape[1] < max_length for v in vectors)
        }

        return fused, fusion_info

    def _weighted_average_fusion(
        self,
        embeddings: Dict[str, np.ndarray],
        weights: List[float]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """加权平均融合策略"""
        vectors = list(embeddings.values())
        weights_array = np.array(weights)

        # 检查维度一致性
        dimensions = [v.shape[1] for v in vectors]
        if len(set(dimensions)) > 1:
            logger.warning(f"模型输出维度不一致: {dimensions}，使用维度对齐")
            # 使用平均填充
            max_dim = max(dimensions)
            aligned_vectors = []
            for v in vectors:
                if v.shape[1] < max_dim:
                    padding = np.zeros((v.shape[0], max_dim - v.shape[1]))
                    v_aligned = np.hstack([v, padding])
                else:
                    v_aligned = v
                aligned_vectors.append(v_aligned)
            vectors = aligned_vectors

        # 加权平均
        fused = np.zeros_like(vectors[0])
        for i, (v, weight) in enumerate(zip(vectors, weights_array)):
            fused += weight * v

        fusion_info = {
            'method': 'weighted_average',
            'weights': weights,
            'input_dimensions': dimensions,
            'output_dimension': fused.shape[1]
        }

        return fused, fusion_info

    def _attention_fusion(
        self,
        embeddings: Dict[str, np.ndarray],
        weights: List[float]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """注意力融合策略（简化版）"""
        # 将weights作为注意力权重
        return self._weighted_average_fusion(embeddings, weights)

    def _adaptive_fusion(
        self,
        embeddings: Dict[str, np.ndarray],
        weights: List[float]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """自适应融合策略"""
        # 简化实现：根据模型性能调整权重
        performance_scores = self._get_model_performance(list(embeddings.keys()))
        adapted_weights = []

        for i, (model_name, original_weight) in enumerate(zip(embeddings.keys(), weights)):
            performance = performance_scores.get(model_name, 1.0)
            adapted_weight = original_weight * performance
            adapted_weights.append(adapted_weight)

        # 归一化
        total_weight = sum(adapted_weights)
        adapted_weights = [w / total_weight for w in adapted_weights]

        return self._weighted_average_fusion(embeddings, adapted_weights)

    def _simple_average_fusion(
        self,
        embeddings: Dict[str, np.ndarray],
        weights: List[float]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """简单平均融合（回退策略）"""
        vectors = list(embeddings.values())

        # 确保维度一致
        max_dim = max(v.shape[1] for v in vectors)
        aligned_vectors = []
        for v in vectors:
            if v.shape[1] < max_dim:
                padding = np.zeros((v.shape[0], max_dim - v.shape[1]))
                v_aligned = np.hstack([v, padding])
            else:
                v_aligned = v
            aligned_vectors.append(v_aligned)

        # 平均
        fused = np.mean(aligned_vectors, axis=0)

        fusion_info = {
            'method': 'simple_average',
            'input_dimensions': [v.shape[1] for v in vectors],
            'output_dimension': fused.shape[1]
        }

        return fused, fusion_info

    def _get_model_performance(self, model_names: List[str]) -> Dict[str, float]:
        """获取模型性能分数"""
        # 简化实现，实际应该基于历史性能数据
        performance_map = {
            'bge-large-zh-v1.5': 1.2,
            'chinese-legal-electra': 1.1,
            'bge-base-zh-v1.5': 0.9
        }

        return {
            name: performance_map.get(name, 1.0)
            for name in model_names
        }

    def encode_patents(
        self,
        patents: List[Dict[str, Any]],
        text_fields: List[str] = ['title', 'abstract'],
        model_config: Optional[Dict[str, Any]] = None,
        fusion_strategy: str = 'weighted_average'
    ) -> Dict[str, Any]:
        """编码专利数据

        Args:
            patents: 专利数据列表
            text_fields: 要编码的文本字段
            model_config: 模型配置
            fusion_strategy: 融合策略

        Returns:
            包含向量的专利数据
        """
        # 准备文本
        texts = []
        for patent in patents:
            text_parts = []
            for field in text_fields:
                value = patent.get(field, '')
                if value:
                    text_parts.append(f"{field}: {value}")
            texts.append(' | '.join(text_parts))

        # 编码
        result = self.encode_with_multiple_models(
            texts,
            model_config=model_config,
            fusion_strategy=fusion_strategy
        )

        # 将向量添加回专利数据
        if 'fused_vector' in result:
            fused_vectors = result['fused_vector']
            for i, patent in enumerate(patents):
                if i < len(fused_vectors):
                    patent['vector'] = fused_vectors[i].tolist()
                    patent['vector_dimension'] = fused_vectors.shape[1]

        # 添加融合信息
        patents_with_vectors = {
            'patents': patents,
            'encoding_info': result,
            'text_fields': text_fields
        }

        return patents_with_vectors

    def batch_encode(
        self,
        text_batches: List[List[str]],
        model_config: Optional[Dict[str, Any]] = None,
        fusion_strategy: str = 'weighted_average'
    ) -> List[Dict[str, Any]]:
        """批量编码

        Args:
            text_batches: 文本批次列表
            model_config: 模型配置
            fusion_strategy: 融合策略

        Returns:
            每个批次的编码结果
        """
        results = []

        for i, batch in enumerate(text_batches):
            logger.info(f"编码批次 {i+1}/{len(text_batches)}, 文本数: {len(batch)}")
            result = self.encode_with_multiple_models(
                batch,
                model_config=model_config,
                fusion_strategy=fusion_strategy
            )
            results.append(result)

        return results

    def _get_cache_key(self, texts: List[str], config: Dict, strategy: str) -> str:
        """生成缓存键"""
        import hashlib
        content = {
            'texts': texts[:5],  # 只用前5个文本生成key
            'config': config,
            'strategy': strategy
        }
        content_str = str(content)
        return hashlib.md5(content_str.encode('utf-8'), usedforsecurity=False).hexdigest()

    def _cache_result(self, key: str, result: Dict[str, Any]):
        """缓存结果"""
        # 如果缓存已满，清理旧缓存
        if len(self.vector_cache) >= self.max_cache_size:
            # 简单策略：删除最旧的缓存项
            oldest_key = next(iter(self.vector_cache))
            del self.vector_cache[oldest_key]

        self.vector_cache[key] = result

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            'cache_size': len(self.vector_cache),
            'max_cache_size': self.max_cache_size,
            'cache_hit_rate': self.stats['cache_hits'] / max(1, self.stats['total_requests'])
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        fusion_stats = {}
        for strategy, times in self.stats['fusion_times'].items():
            fusion_stats[strategy] = {
                'count': len(times),
                'avg_time': np.mean(times) if times else 0,
                'min_time': min(times) if times else 0,
                'max_time': max(times) if times else 0
            }

        return {
            'total_requests': self.stats['total_requests'],
            'cache_hits': self.stats['cache_hits'],
            'cache_hit_rate': self.stats['cache_hits'] / max(1, self.stats['total_requests']),
            'model_switches': dict(self.stats['model_switches']),
            'fusion_stats': fusion_stats,
            'last_updated': self.stats['last_updated']
        }

    def clear_cache(self):
        """清空缓存"""
        self.vector_cache.clear()
        logger.info('向量缓存已清空')

    def cleanup(self):
        """清理资源"""
        self.clear_cache()
        self.model_manager.cleanup()

# 测试函数
def test_multi_model_vectorizer():
    """测试多模型向量器"""
    logger.info("=== 测试多模型向量融合器 ===\n")

    vectorizer = MultiModelVectorizer()

    try:
        # 测试文本
        test_texts = [
            '本发明涉及一种新型电池管理系统',
            '根据专利法规定，发明应当具备新颖性',
            '人工智能技术在医疗诊断中的应用'
        ]

        logger.info('1. 自动选择模型融合...')
        result = vectorizer.encode_with_multiple_models(
            test_texts,
            model_config={
                'auto_select': True,
                'max_models': 3
            },
            fusion_strategy='weighted_average'
        )

        logger.info(f"   融合向量形状: {result['fused_vector'].shape}")
        logger.info(f"   使用的模型: {result['fusion_info']['models_used']}")
        logger.info(f"   融合时间: {result['fusion_info']['fusion_time']:.3f}s")

        logger.info("\n2. 指定模型融合...")
        result2 = vectorizer.encode_with_multiple_models(
            test_texts,
            model_config={
                'models': ['bge-base-zh-v1.5', 'patent-bert-base'],
                'weights': [0.6, 0.4]
            },
            fusion_strategy='concatenation',
            return_individual=True
        )

        logger.info(f"   融合向量形状: {result2['fused_vector'].shape}")
        logger.info(f"   独立向量数量: {len(result2['individual_vectors'])}")

        # 测试专利编码
        logger.info("\n3. 专利数据编码...")
        patents = [
            {
                'title': '电池管理系统',
                'abstract': '一种用于监测电池状态的管理系统',
                'patent_type': 'invention'
            },
            {
                'title': '医疗诊断设备',
                'abstract': '基于AI的医疗诊断装置和方法',
                'patent_type': 'utility'
            }
        ]

        patent_result = vectorizer.encode_patents(patents)
        logger.info(f"   编码专利数: {len(patent_result['patents'])}")
        for patent in patent_result['patents']:
            if 'vector' in patent:
                logger.info(f"   - {patent['title']}: 向量维度 {len(patent['vector'])}")

        # 性能统计
        logger.info("\n4. 性能统计:")
        stats = vectorizer.get_performance_stats()
        logger.info(f"   总请求数: {stats['total_requests']}")
        logger.info(f"   缓存命中率: {stats['cache_hit_rate']:.2%}")
        logger.info(f"   模型切换次数: {sum(stats['model_switches'].values())}")

    except Exception as e:
        logger.info(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        vectorizer.cleanup()

if __name__ == '__main__':
    test_multi_model_vectorizer()