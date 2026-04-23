#!/usr/bin/env python3
"""
中文BERT模型管理器
Chinese BERT Model Manager

管理和切换多个中文BERT embedding模型
"""

# Numpy兼容性导入
import logging
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any

import numpy as np
import torch
from FlagEmbedding import FlagReranker
from sentence_transformers import SentenceTransformer

from config.numpy_compatibility import array

# 添加项目路径以导入本地模型配置
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.models.local_model_config import model_config

# 配置日志
logger = logging.getLogger(__name__)

class ChineseBERTModelManager:
    """中文BERT模型管理器"""

    def __init__(self, model_cache_dir='/Users/xujian/Athena工作平台/models'):
        """初始化模型管理器

        Args:
            model_cache_dir: 模型缓存目录
        """
        # 设置离线模式
        model_config.setup_offline_mode()

        self.model_cache_dir = model_cache_dir
        self.models = {}
        self.rerankers = {}
        self.model_configs = self._load_model_configs()
        self.device = 'cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'
        self.current_model = None
        self.current_reranker = None
        self.lock = threading.Lock()

        # 预加载性能指标
        self.performance_metrics = {}

    def _load_model_configs(self) -> dict[str, dict[str, Any]]:
        """加载模型配置"""
        return {
            # 通用中文模型
            'bge-large-zh-v1.5': {
                'path': '/Users/xujian/Athena工作平台/models/bge-large-zh-v1.5',
                'type': 'embedding',
                'dimension': 1024,
                'description': '通用中文大模型，适合大多数场景',
                'specialties': ['通用', '长文本', '语义理解'],
                'speed': 'medium',
                'accuracy': 'high'
            },
            'bge-base-zh-v1.5': {
                'path': '/Users/xujian/Athena工作平台/models/bge-base-zh-v1.5/snapshots/f03589ceff5aac7111bd60cfc7d497ca17ecac65',
                'type': 'embedding',
                'dimension': 768,
                'description': '通用中文基础模型，平衡速度和质量',
                'specialties': ['通用', '快速检索', '中等长度文本'],
                'speed': 'fast',
                'accuracy': 'medium'
            },

            # 法律专业模型
            'chinese-legal-electra': {
                'path': '/Users/xujian/Athena工作平台/models/chinese_legal_electra',
                'type': 'embedding',
                'dimension': 768,
                'description': '中文法律文本专用模型',
                'specialties': ['法律文书', '合同分析', '条款匹配'],
                'speed': 'medium',
                'accuracy': 'high'
            }
        }

    def load_model(self, model_name: str, force_reload: bool = False) -> bool:
        """加载指定模型

        Args:
            model_name: 模型名称
            force_reload: 是否强制重新加载

        Returns:
            是否加载成功
        """
        if model_name not in self.model_configs:
            logger.error(f"未知模型: {model_name}")
            return False

        if model_name in self.models and not force_reload:
            logger.info(f"模型 {model_name} 已加载")
            return True

        with self.lock:
            try:
                config = self.model_configs[model_name]
                model_path = config['path']

                logger.info(f"加载模型: {model_name} from {model_path}")

                if not os.path.exists(model_path):
                    logger.warning(f"本地模型不存在: {model_path}")
                    # 尝试使用HuggingFace模型ID
                    model_path = model_name.split('/')[-1]

                # 加载模型，使用本地路径
                model = SentenceTransformer(
                    model_config.get_sentence_transformer_model(model_name),
                    cache_folder=self.model_cache_dir,
                    device=self.device
                )

                # 测试模型
                test_texts = ['这是一个测试文本']
                embeddings = model.encode(test_texts, normalize_embeddings=True)

                if embeddings is not None and len(embeddings) > 0:
                    self.models[model_name] = {
                        'model': model,
                        'config': config,
                        'loaded_at': datetime.now(),
                        'dimension': embeddings.shape[1]
                    }

                    self.current_model = model_name
                    logger.info(f"✅ 模型 {model_name} 加载成功，维度: {embeddings.shape[1]}")
                    return True
                else:
                    logger.error(f"模型 {model_name} 加载失败：无法生成embedding")
                    return False

            except Exception as e:
                logger.error(f"加载模型 {model_name} 失败: {e}")
                return False

    def load_reranker(self, model_name: str = 'bge-reranker-large') -> bool:
        """加载重排序模型

        Args:
            model_name: 重排序模型名称

        Returns:
            是否加载成功
        """
        try:
            # BGE重排序模型
            model_path = f'/Users/xujian/Athena工作平台/models/{model_name}'

            if not os.path.exists(model_path):
                logger.info(f"本地重排序模型不存在，使用在线模型: {model_name}")
                model_path = model_name

            reranker = FlagReranker(
                model_path,
                cache_dir=self.model_cache_dir,
                use_fp16=True
            )

            self.rerankers[model_name] = {
                'reranker': reranker,
                'loaded_at': datetime.now()
            }
            self.current_reranker = model_name

            logger.info(f"✅ 重排序模型 {model_name} 加载成功")
            return True

        except Exception as e:
            logger.error(f"加载重排序模型失败: {e}")
            return False

    def switch_model(self, model_name: str) -> bool:
        """切换当前使用的模型

        Args:
            model_name: 目标模型名称

        Returns:
            是否切换成功
        """
        if model_name == self.current_model:
            logger.info(f"当前已是模型 {model_name}")
            return True

        if self.load_model(model_name):
            self.current_model = model_name
            logger.info(f"✅ 已切换到模型: {model_name}")
            return True
        else:
            logger.error(f"切换模型失败: {model_name}")
            return False

    def encode_texts(
        self,
        texts: list[str],
        model_name: Optional[str] = None,
        batch_size: int = 32,
        normalize: bool = True
    ) -> np.ndarray:
        """编码文本

        Args:
            texts: 文本列表
            model_name: 使用的模型名，None表示使用当前模型
            batch_size: 批处理大小
            normalize: 是否归一化

        Returns:
            文本向量
        """
        if not texts:
            return array([])

        # 确定使用的模型
        model_name = model_name or self.current_model
        if not model_name:
            logger.error('没有可用的模型')
            return array([])

        if model_name not in self.models:
            if not self.load_model(model_name):
                return array([])

        model = self.models[model_name]['model']

        # 记录性能
        start_time = datetime.now()

        try:
            # 分批编码
            embeddings = model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=normalize,
                show_progress_bar=False,
                convert_to_numpy=True
            )

            # 记录性能指标
            duration = (datetime.now() - start_time).total_seconds()
            self._record_performance(model_name, len(texts), duration)

            return embeddings

        except Exception as e:
            logger.error(f"文本编码失败: {e}")
            return array([])

    def rerank_results(
        self,
        query: str,
        passages: list[str],
        top_k: Optional[int] = None
    ) -> list[tuple[int, float]]:
        """重排序结果

        Args:
            query: 查询文本
            passages: 候选文本列表
            top_k: 返回前k个结果

        Returns:
            (索引, 分数) 列表
        """
        if not self.current_reranker:
            logger.warning('没有加载重排序模型，返回原始顺序')
            return [(i, 1.0) for i in range(len(passages))]

        reranker = self.rerankers[self.current_reranker]['reranker']

        try:
            # 准备输入
            pairs = [(query, passage) for passage in passages]

            # 计算分数
            scores = reranker.compute_score(pairs)

            # 组合结果
            results = [(i, float(score)) for i, score in enumerate(scores)]

            # 排序并返回top_k
            results.sort(key=lambda x: x[1], reverse=True)

            if top_k:
                results = results[:top_k]

            return results

        except Exception as e:
            logger.error(f"重排序失败: {e}")
            return [(i, 1.0) for i in range(len(passages))]

    def get_model_info(self, model_name: Optional[str] = None) -> Optional[dict[str, Any]]:
        """获取模型信息

        Args:
            model_name: 模型名称，None表示当前模型

        Returns:
            模型信息字典
        """
        model_name = model_name or self.current_model

        if not model_name:
            return None

        if model_name in self.models:
            model_data = self.models[model_name]
            return {
                'name': model_name,
                'config': model_data['config'],
                'loaded_at': model_data['loaded_at'],
                'dimension': model_data['dimension'],
                'is_current': model_name == self.current_model
            }

        return None

    def list_available_models(self) -> list[dict[str, Any]]:
        """列出所有可用模型"""
        models = []

        for name, config in self.model_configs.items():
            model_info = {
                'name': name,
                'config': config,
                'is_loaded': name in self.models,
                'is_current': name == self.current_model
            }
            models.append(model_info)

        return models

    def recommend_model(self, text_type: str, speed_preference: str = 'medium') -> Optional[str]:
        """根据文本类型和速度偏好推荐模型

        Args:
            text_type: 文本类型 ('patent', 'legal', 'general', 'short')
            speed_preference: 速度偏好 ('fast', 'medium', 'slow')

        Returns:
            推荐的模型名称
        """
        # 模型推荐映射
        recommendations = {
            ('patent', 'fast'): 'patent-bert-base',
            ('patent', 'medium'): 'bge-base-zh-v1.5',
            ('patent', 'slow'): 'bge-large-zh-v1.5',

            ('legal', 'fast'): 'patent-bert-base',
            ('legal', 'medium'): 'text2vec-large-chinese',
            ('legal', 'slow'): 'bge-large-zh-v1.5',

            ('general', 'fast'): 'paraphrase-multilingual-MiniLM-L12-v2',
            ('general', 'medium'): 'bge-base-zh-v1.5',
            ('general', 'slow'): 'bge-large-zh-v1.5',

            ('short', 'fast'): 'paraphrase-multilingual-MiniLM-L12-v2',
            ('short', 'medium'): 'bge-base-zh-v1.5',
            ('short', 'slow'): 'bge-large-zh-v1.5'
        }

        key = (text_type, speed_preference)
        return recommendations.get(key, 'bge-base-zh-v1.5')

    def batch_encode_with_models(
        self,
        texts: list[str],
        model_names: list[str],
        weights: list[float] | None = None
    ) -> dict[str, np.ndarray]:
        """使用多个模型批量编码

        Args:
            texts: 文本列表
            model_names: 模型名称列表
            weights: 各模型权重

        Returns:
            模型名称到向量的映射
        """
        if not weights:
            weights = [1.0] * len(model_names)
        elif len(weights) != len(model_names):
            weights = [1.0] * len(model_names)

        results = {}

        def encode_with_model(model_name, weight):
            if self.load_model(model_name):
                embeddings = self.encode_texts(texts, model_name=model_name)
                if weight != 1.0:
                    embeddings = embeddings * weight
                results[model_name] = embeddings

        # 并行执行
        with ThreadPoolExecutor(max_workers=min(4, len(model_names))) as executor:
            futures = []
            for model_name, weight in zip(model_names, weights, strict=False):
                future = executor.submit(encode_with_model, model_name, weight)
                futures.append(future)

            # 等待所有任务完成
            for future in futures:
                future.result()

        return results

    def _record_performance(self, model_name: str, text_count: int, duration: float):
        """记录性能指标"""
        if model_name not in self.performance_metrics:
            self.performance_metrics[model_name] = {
                'total_requests': 0,
                'total_texts': 0,
                'total_time': 0,
                'avg_texts_per_second': 0,
                'last_updated': datetime.now()
            }

        metrics = self.performance_metrics[model_name]
        metrics['total_requests'] += 1
        metrics['total_texts'] += text_count
        metrics['total_time'] += duration

        if metrics['total_time'] > 0:
            metrics['avg_texts_per_second'] = metrics['total_texts'] / metrics['total_time']

        metrics['last_updated'] = datetime.now()

    def get_performance_metrics(self) -> dict[str, dict[str, Any]]:
        """获取性能指标"""
        return self.performance_metrics

    def cleanup(self):
        """清理资源"""
        with self.lock:
            for model_name in list(self.models.keys()):
                del self.models[model_name]

            for reranker_name in list(self.rerankers.keys()):
                del self.rerankers[reranker_name]

            self.models.clear()
            self.rerankers.clear()
            self.current_model = None
            self.current_reranker = None

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

# 测试函数
def test_model_manager():
    """测试模型管理器"""
    logger.info("=== 测试中文BERT模型管理器 ===\n")

    manager = ChineseBERTModelManager()

    try:
        # 列出可用模型
        logger.info('1. 可用模型列表:')
        models = manager.list_available_models()
        for model in models:
            status = '✅' if model['is_loaded'] else '⭕'
            current = ' (当前)' if model['is_current'] else ''
            logger.info(f"   {status} {model['name']}{current}")
            logger.info(f"      描述: {model['config']['description']}")
            logger.info(f"      特长: {', '.join(model['config']['specialties'])}")

        # 加载默认模型
        logger.info("\n2. 加载默认模型...")
        if manager.load_model('bge-base-zh-v1.5'):
            logger.info('✅ 模型加载成功')

        # 测试编码
        test_texts = [
            '本发明涉及一种新型电池管理系统',
            '专利申请需要满足新颖性和创造性要求',
            '人工智能在医疗诊断中的应用'
        ]

        logger.info("\n3. 测试文本编码...")
        embeddings = manager.encode_texts(test_texts, batch_size=2)
        logger.info(f"   编码成功: {embeddings.shape}")

        # 测试模型推荐
        logger.info("\n4. 测试模型推荐...")
        recommendations = [
            manager.recommend_model('patent', 'fast'),
            manager.recommend_model('legal', 'high'),
            manager.recommend_model('general', 'slow')
        ]
        logger.info(f"   专利文档(快速): {recommendations[0]}")
        logger.info(f"   法律文档(高质量): {recommendations[1]}")
        logger.info(f"   通用文档(慢速): {recommendations[2]}")

        # 性能指标
        logger.info("\n5. 性能指标:")
        metrics = manager.get_performance_metrics()
        for model_name, metric in metrics.items():
            logger.info(f"   {model_name}:")
            logger.info(f"     请求数: {metric['total_requests']}")
            logger.info(f"     文本数: {metric['total_texts']}")
            logger.info(f"     平均速度: {metric['avg_texts_per_second']:.1f} texts/s")

    except Exception as e:
        logger.info(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        manager.cleanup()

if __name__ == '__main__':
    test_model_manager()
