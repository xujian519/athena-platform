"""
迁移学习框架
支持跨任务、跨域的知识迁移和快速适应
"""
import numpy as np

import logging
import pickle
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# 深度学习框架
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:

    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

# 机器学习工具
try:

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class TransferStrategy(Enum):
    """迁移策略"""

    FINE_TUNING = "fine_tuning"  # 微调
    FEATURE_EXTRACTION = "feature_extraction"  # 特征提取
    DOMAIN_ADAPTATION = "domain_adaptation"  # 域适应
    MULTI_TASK = "multi_task"  # 多任务学习
    PROGRESSIVE = "progressive"  # 渐进式迁移
    ADVERSARIAL = "adversarial"  # 对抗迁移


class SimilarityMetric(Enum):
    """相似度度量"""

    EUCLIDEAN = "euclidean"  # 欧氏距离
    COSINE = "cosine"  # 余弦相似度
    PEARSON = "pearson"  # 皮尔逊相关
    KL_DIVERGENCE = "kl_divergence"  # KL散度
    STRUCTURAL = "structural"  # 结构相似度


@dataclass
class SourceTask:
    """源任务"""

    task_id: str
    task_name: str
    domain: str
    task_type: str
    model_data: bytes
    performance_metrics: dict[str, float]
    feature_space: str
    data_statistics: dict[str, Any]
    created_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TransferMapping:
    """迁移映射"""

    mapping_id: str
    source_task_id: str
    target_task_id: str
    similarity_score: float
    transfer_strategy: TransferStrategy
    layer_mappings: dict[str, str]
    adaptation_steps: list[str]
    expected_performance_gain: float
    confidence: float
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TransferResult:
    """迁移结果"""

    transfer_id: str
    source_task_id: str
    target_task_id: str
    strategy: TransferStrategy
    performance_before: float
    performance_after: float
    transfer_time: float
    success: bool
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class TransferLearningFramework:
    """迁移学习框架"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {
            "similarity_threshold": 0.3,
            "max_source_tasks": 100,
            "transfer_strategies": [
                TransferStrategy.FINE_TUNING,
                TransferStrategy.FEATURE_EXTRACTION,
            ],
            "fine_tuning_lr": 0.001,
            "adaptation_epochs": 50,
            "early_stopping_patience": 10,
            "enable_domain_adaptation": True,
            "enable_multi_task": True,
            "cache_mappings": True,
            "auto_select_strategy": True,
        }

        # 源任务库
        self.source_tasks = {}
        self.task_embeddings = {}

        # 迁移映射缓存
        self.transfer_mappings = defaultdict(dict)
        self.mapping_cache = {}

        # 迁移历史
        self.transfer_history = deque(maxlen=1000)
        self.successful_transfers = defaultdict(list)

        # 相似度计算器
        self.similarity_calculator = SimilarityCalculator()

        # 域适配器
        if self.config["enable_domain_adaptation"]:
            self.domain_adapter = DomainAdapter(self.config)

        # 多任务学习器
        if self.config["enable_multi_task"]:
            self.multi_task_learner = MultiTaskLearner(self.config)

        # 性能追踪
        self.performance_tracker = defaultdict(list)

    async def register_source_task(
        self,
        task_id: str,
        task_name: str,
        domain: str,
        task_type: str,
        model: Any,
        performance_metrics: dict[str, float],
        feature_space: str = "unknown",
        data_statistics: dict[str, Any] | None = None,
    ) -> bool:
        """注册源任务"""
        try:
            # 序列化模型
            model_data = pickle.dumps(model)

            # 创建源任务
            source_task = SourceTask(
                task_id=task_id,
                task_name=task_name,
                domain=domain,
                task_type=task_type,
                model_data=model_data,
                performance_metrics=performance_metrics,
                feature_space=feature_space,
                data_statistics=data_statistics or {},
                created_at=datetime.now(),
            )

            # 保存源任务
            self.source_tasks[task_id] = source_task

            # 计算任务嵌入
            embedding = await self._compute_task_embedding(source_task)
            self.task_embeddings[task_id] = embedding

            # 更新相似度矩阵
            await self._update_similarity_matrix()

            logger.info(f"注册源任务: {task_id}")
            return True

        except Exception as e:
            logger.error(f"注册源任务失败: {e}")
            return False

    async def _compute_task_embedding(self, task: SourceTask) -> np.ndarray:
        """计算任务嵌入"""
        # 结合多种特征计算嵌入
        features = []

        # 1. 任务类型编码
        type_encoding = self._encode_task_type(task.task_type)
        features.extend(type_encoding)

        # 2. 域编码
        domain_encoding = self._encode_domain(task.domain)
        features.extend(domain_encoding)

        # 3. 性能指标
        perf_features = [
            task.performance_metrics.get("accuracy", 0),
            task.performance_metrics.get("f1_score", 0),
            task.performance_metrics.get("precision", 0),
            task.performance_metrics.get("recall", 0),
        ]
        features.extend(perf_features)

        # 4. 数据统计特征
        if task.data_statistics:
            data_features = [
                task.data_statistics.get("num_samples", 0) / 10000,  # 归一化
                task.data_statistics.get("num_features", 0) / 1000,
                task.data_statistics.get("class_balance", 0.5),
            ]
            features.extend(data_features)

        # 5. 特征空间编码
        space_encoding = self._encode_feature_space(task.feature_space)
        features.extend(space_encoding)

        # 转换为numpy数组
        embedding = np.array(features, dtype=np.float32)

        # 归一化
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)

        return embedding

    def _encode_task_type(self, task_type: str) -> list[float]:
        """编码任务类型"""
        task_types = ["classification", "regression", "clustering", "generation", "detection"]
        encoding = [0.0] * len(task_types)
        if task_type in task_types:
            encoding[task_types.index(task_type)] = 1.0
        return encoding

    def _encode_domain(self, domain: str) -> list[float]:
        """编码域"""
        domains = ["nlp", "cv", "audio", "tabular", "time_series", "graph"]
        encoding = [0.0] * len(domains)
        if domain in domains:
            encoding[domains.index(domain)] = 1.0
        return encoding

    def _encode_feature_space(self, feature_space: str) -> list[float]:
        """编码特征空间"""
        spaces = ["image", "text", "audio", "numeric", "categorical", "mixed"]
        encoding = [0.0] * len(spaces)
        if feature_space in spaces:
            encoding[spaces.index(feature_space)] = 1.0
        return encoding

    async def _update_similarity_matrix(self):
        """更新相似度矩阵"""
        task_ids = list(self.task_embeddings.keys())

        for i, task_id1 in enumerate(task_ids):
            for task_id2 in task_ids[i + 1 :]:
                embedding1 = self.task_embeddings[task_id1]
                embedding2 = self.task_embeddings[task_id2]

                # 计算多种相似度
                similarities = {}
                for metric in SimilarityMetric:
                    sim = await self.similarity_calculator.compute_similarity(
                        embedding1, embedding2, metric
                    )
                    similarities[metric.value] = sim

                # 综合相似度
                overall_sim = np.mean(list(similarities.values()))

                # 缓存相似度
                if self.config["cache_mappings"]:
                    self.mapping_cache[f"{task_id1}_{task_id2}"] = {
                        "similarities": similarities,
                        "overall": overall_sim,
                    }
                    self.mapping_cache[f"{task_id2}_{task_id1}"] = {
                        "similarities": similarities,
                        "overall": overall_sim,
                    }

    async def find_similar_tasks(
        self,
        target_task_id: str,
        target_description: dict[str, Any] | None = None,
        top_k: int = 5,
    ) -> list[tuple[str, float]]:
        """查找相似任务"""
        if target_task_id in self.task_embeddings:
            target_embedding = self.task_embeddings[target_task_id]
        elif target_description:
            # 从描述生成嵌入
            target_embedding = await self._generate_embedding_from_description(target_description)
        else:
            logger.error("需要提供目标任务ID或描述")
            return []

        similarities = []
        for task_id, embedding in self.task_embeddings.items():
            if task_id != target_task_id:
                sim = await self.similarity_calculator.compute_similarity(
                    target_embedding, embedding, SimilarityMetric.COSINE
                )
                similarities.append((task_id, sim))

        # 排序并返回top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    async def _generate_embedding_from_description(self, description: dict[str, Any]) -> np.ndarray:
        """从描述生成嵌入"""
        # 基于描述创建虚拟源任务
        virtual_task = SourceTask(
            task_id="virtual",
            task_name="",
            domain=description.get("domain", "unknown"),
            task_type=description.get("task_type", "unknown"),
            model_data=b"",
            performance_metrics=description.get("performance_metrics", {}),
            feature_space=description.get("feature_space", "unknown"),
            data_statistics=description.get("data_statistics", {}),
            created_at=datetime.now(),
        )

        return await self._compute_task_embedding(virtual_task)

    async def transfer_knowledge(
        self,
        source_task_id: str,
        target_task_id: str,
        target_model: Any,
        target_data: Any | None = None,
        strategy: TransferStrategy | None = None,
    ) -> TransferResult:
        """迁移知识"""
        transfer_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # 检查源任务是否存在
            if source_task_id not in self.source_tasks:
                raise ValueError(f"源任务不存在: {source_task_id}")

            source_task = self.source_tasks[source_task_id]

            # 评估目标模型当前性能
            performance_before = await self._evaluate_model(target_model, target_data)

            # 选择迁移策略
            if strategy is None and self.config["auto_select_strategy"]:
                strategy = await self._select_best_strategy(source_task, target_model)

            # 执行迁移
            if strategy == TransferStrategy.FINE_TUNING:
                transferred_model = await self._fine_tuning_transfer(
                    source_task, target_model, target_data
                )
            elif strategy == TransferStrategy.FEATURE_EXTRACTION:
                transferred_model = await self._feature_extraction_transfer(
                    source_task, target_model
                )
            elif strategy == TransferStrategy.DOMAIN_ADAPTATION:
                transferred_model = await self._domain_adaptation_transfer(
                    source_task, target_model, target_data
                )
            elif strategy == TransferStrategy.MULTI_TASK:
                transferred_model = await self._multi_task_transfer(
                    source_task, target_model, target_data
                )
            else:
                raise ValueError(f"不支持的迁移策略: {strategy}")

            # 评估迁移后性能
            performance_after = await self._evaluate_model(transferred_model, target_data)

            # 计算迁移时间
            transfer_time = time.time() - start_time

            # 创建迁移结果
            result = TransferResult(
                transfer_id=transfer_id,
                source_task_id=source_task_id,
                target_task_id=target_task_id,
                strategy=strategy,
                performance_before=performance_before,
                performance_after=performance_after,
                transfer_time=transfer_time,
                success=True,
            )

            # 记录迁移历史
            self.transfer_history.append(result)

            # 更新成功迁移记录
            if performance_after > performance_before:
                self.successful_transfers[source_task_id].append(
                    {
                        "target_task_id": target_task_id,
                        "improvement": performance_after - performance_before,
                        "timestamp": datetime.now(),
                    }
                )

            # 更新性能追踪
            self.performance_tracker[target_task_id].append(performance_after)

            logger.info(
                f"知识迁移成功: {source_task_id} -> {target_task_id}, "
                f"性能提升: {performance_after - performance_before:.4f}"
            )

            return result

        except Exception as e:
            logger.error(f"知识迁移失败: {e}")
            transfer_time = time.time() - start_time

            return TransferResult(
                transfer_id=transfer_id,
                source_task_id=source_task_id,
                target_task_id=target_task_id,
                strategy=strategy or TransferStrategy.FINE_TUNING,
                performance_before=0.0,
                performance_after=0.0,
                transfer_time=transfer_time,
                success=False,
                error_message=str(e),
            )

    async def _select_best_strategy(
        self, source_task: SourceTask, target_model: Any
    ) -> TransferStrategy:
        """选择最佳迁移策略"""
        # 基于任务相似度和模型类型选择策略
        strategies = self.config["transfer_strategies"]

        # 如果模型是神经网络,优先微调
        if isinstance(target_model, dict) and target_model.get("type") == "neural_network":
            if TransferStrategy.FINE_TUNING in strategies:
                return TransferStrategy.FINE_TUNING
            elif TransferStrategy.FEATURE_EXTRACTION in strategies:
                return TransferStrategy.FEATURE_EXTRACTION

        # 如果域相似,使用域适应
        # (简化实现)
        return strategies[0]

    async def _fine_tuning_transfer(
        self, source_task: SourceTask, target_model: Any, target_data: Any | None = None
    ) -> Any:
        """微调迁移"""
        try:
            # 加载源模型
            source_model = pickle.loads(source_task.model_data)

            if (
                isinstance(source_model, dict)
                and source_model.get("type") == "neural_network"
                and isinstance(target_model, dict)
                and target_model.get("type") == "neural_network"
                and TORCH_AVAILABLE
            ):

                # 获取模型
                source_nn = source_model["model"]
                target_nn = target_model["model"]

                # 初始化目标模型的部分权重
                await self._initialize_target_from_source(source_nn, target_nn)

                # 创建优化器
                if TORCH_AVAILABLE:
                    import torch.optim as torch_optim  # type: ignore

                    optimizer = torch_optim.Adam(
                        target_nn.parameters(), lr=self.config["fine_tuning_lr"]
                    )
                else:
                    # 无优化器可用,跳过微调
                    logger.warning("PyTorch不可用,跳过微调")
                    return target_model

                # 微调训练
                if target_data:
                    await self._fine_tune_training(target_nn, optimizer, target_data)

                target_model["model"] = target_nn
                return target_model

            else:
                # 非神经网络模型的迁移
                return await self._transfer_sklearn_model(source_task, target_model)

        except Exception as e:
            logger.error(f"微调迁移失败: {e}")
            raise

    async def _initialize_target_from_source(
        self, source_model: nn.Module, target_model: nn.Module
    ):
        """从源模型初始化目标模型"""
        # 匹配并迁移层
        source_dict = source_model.state_dict()
        target_dict = target_model.state_dict()

        # 找到匹配的层
        for target_name, target_param in target_dict.items():
            # 尝试找到最相似的源层
            best_match = None
            best_similarity = 0.0

            for source_name, source_param in source_dict.items():
                if target_param.shape == source_param.shape:
                    # 简单的名称相似度
                    name_similarity = self._calculate_name_similarity(target_name, source_name)
                    if name_similarity > best_similarity:
                        best_similarity = name_similarity
                        best_match = source_name

            if best_match and best_similarity > 0.5:
                target_dict[target_name] = source_dict[best_match]

        target_model.load_state_dict(target_dict)

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """计算层名相似度"""
        # 简单的字符串相似度
        name1_parts = set(name1.split("."))
        name2_parts = set(name2.split("."))
        intersection = len(name1_parts.intersection(name2_parts))
        union = len(name1_parts.union(name2_parts))
        return intersection / union if union > 0 else 0.0

    async def _fine_tune_training(self, model: nn.Module, optimizer: optim.Optimizer, data: Any):
        """微调训练"""
        # 这里应该实现实际的训练循环
        # 简化实现
        epochs = min(self.config["adaptation_epochs"], 10)

        for _epoch in range(epochs):
            # 这里应该处理实际的数据
            # 简化实现,只做前向传播
            pass

    async def _transfer_sklearn_model(self, source_task: SourceTask, target_model: Any) -> Any:
        """迁移sklearn模型"""
        # 对于非神经网络模型,通常需要重新训练但使用相同的超参数
        source_model = pickle.loads(source_task.model_data)

        # 提取超参数
        if hasattr(source_model, "get_params"):
            params = source_model.get_params()
            target_model["model"].set_params(**params)

        return target_model

    async def _feature_extraction_transfer(self, source_task: SourceTask, target_model: Any) -> Any:
        """特征提取迁移"""
        # 使用源模型作为特征提取器
        source_model = pickle.loads(source_task.model_data)

        # 创建新的模型组合
        combined_model = {
            "type": "feature_extraction",
            "feature_extractor": source_model,
            "target_head": target_model,
        }

        return combined_model

    async def _domain_adaptation_transfer(
        self, source_task: SourceTask, target_model: Any, target_data: Any
    ) -> Any:
        """域适应迁移"""
        if self.domain_adapter:
            return await self.domain_adapter.adapt(source_task, target_model, target_data)
        else:
            # 回退到微调
            return await self._fine_tuning_transfer(source_task, target_model, target_data)

    async def _multi_task_transfer(
        self, source_task: SourceTask, target_model: Any, target_data: Any
    ) -> Any:
        """多任务迁移"""
        if self.multi_task_learner:
            return await self.multi_task_learner.add_task(source_task, target_model, target_data)
        else:
            # 回退到微调
            return await self._fine_tuning_transfer(source_task, target_model, target_data)

    async def _evaluate_model(self, model: Any, data: Any | None = None) -> float:
        """评估模型性能"""
        try:
            if isinstance(model, dict):
                model_type = model.get("type", "unknown")
                model_obj = model.get("model")

                if model_type == "neural_network" and TORCH_AVAILABLE and data:
                    # 评估神经网络
                    if model_obj is not None:
                        # 使用类型忽略处理Unknown类型的model_obj
                        return await self._evaluate_neural_network(model_obj, data)  # type: ignore
                elif SKLEARN_AVAILABLE and data:
                    # 评估sklearn模型
                    return await self._evaluate_sklearn_model(model_obj, data)

            # 默认返回0.5
            return 0.5

        except Exception as e:
            logger.error(f"模型评估失败: {e}")
            return 0.0

    async def _evaluate_neural_network(self, model: nn.Module, data: Any) -> float:
        """评估神经网络"""
        # 简化实现
        if not TORCH_AVAILABLE:
            return 0.5

        model.eval()
        with torch.no_grad():  # type: ignore
            # 这里应该实际计算准确率或其他指标
            return 0.75  # 模拟值

    async def _evaluate_sklearn_model(self, model: Any, data: Any) -> float:
        """评估sklearn模型"""
        # 简化实现
        return 0.75  # 模拟值

    async def batch_transfer(
        self,
        target_task_id: str,
        target_model: Any,
        target_data: Any | None = None,
        max_sources: int = 3,
    ) -> list[TransferResult]:
        """批量迁移"""
        # 查找最相似的源任务
        similar_tasks = await self.find_similar_tasks(target_task_id, top_k=max_sources)

        results = []
        for source_task_id, similarity in similar_tasks:
            # 只迁移相似度足够的任务
            if similarity > self.config["similarity_threshold"]:
                result = await self.transfer_knowledge(
                    source_task_id, target_task_id, target_model, target_data
                )
                results.append(result)

        return results

    def get_transfer_statistics(self) -> dict[str, Any]:
        """获取迁移统计信息"""
        total_transfers = len(self.transfer_history)
        successful_transfers = sum(1 for t in self.transfer_history if t.success)

        # 计算平均性能提升
        performance_gains = []
        for result in self.transfer_history:
            if result.success:
                gain = result.performance_after - result.performance_before
                performance_gains.append(gain)

        # 最成功的迁移
        best_transfers = sorted(
            [t for t in self.transfer_history if t.success],
            key=lambda x: x.performance_after - x.performance_before,
            reverse=True,
        )[:5]

        return {
            "total_transfers": total_transfers,
            "success_rate": successful_transfers / total_transfers if total_transfers > 0 else 0,
            "avg_performance_gain": np.mean(performance_gains) if performance_gains else 0,
            "source_tasks_count": len(self.source_tasks),
            "cached_mappings": len(self.mapping_cache),
            "best_transfers": [
                {
                    "source": t.source_task_id,
                    "target": t.target_task_id,
                    "gain": t.performance_after - t.performance_before,
                    "strategy": t.strategy.value,
                }
                for t in best_transfers
            ],
        }


class SimilarityCalculator:
    """相似度计算器"""

    async def compute_similarity(
        self, embedding1: np.ndarray, embedding2: np.ndarray, metric: SimilarityMetric
    ) -> float:
        """计算相似度"""
        if metric == SimilarityMetric.EUCLIDEAN:
            # 欧氏距离转相似度
            distance = np.linalg.norm(embedding1 - embedding2)
            return float(1.0 / (1.0 + distance))  # type: ignore

        elif metric == SimilarityMetric.COSINE:
            # 余弦相似度
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            return float(dot_product / (norm1 * norm2 + 1e-8))  # type: ignore

        elif metric == SimilarityMetric.PEARSON:
            # 皮尔逊相关系数
            correlation = np.corrcoef(embedding1, embedding2)[0, 1]
            return float(correlation if not np.isnan(correlation) else 0.0)  # type: ignore

        elif metric == SimilarityMetric.KL_DIVERGENCE:
            # KL散度(需要归一化为概率分布)
            p1 = embedding1 + 1e-8
            p1 = p1 / np.sum(p1)
            p2 = embedding2 + 1e-8
            p2 = p2 / np.sum(p2)
            kl_div = np.sum(p1 * np.log(p1 / p2))
            return 1.0 / (1.0 + kl_div)

        elif metric == SimilarityMetric.STRUCTURAL:
            # 结构相似度(基于特征的分布)
            return self._structural_similarity(embedding1, embedding2)

        else:
            return 0.0

    def _structural_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """计算结构相似度"""
        # 计算特征分布的相似度
        mean1, std1 = np.mean(embedding1), np.std(embedding1)
        mean2, std2 = np.mean(embedding2), np.std(embedding2)

        mean_sim = 1.0 / (1.0 + abs(mean1 - mean2))
        std_sim = 1.0 / (1.0 + abs(std1 - std2))

        return float((mean_sim + std_sim) / 2.0)  # type: ignore


class DomainAdapter:
    """域适配器"""

    def __init__(self, config: dict[str, Any]):
        self.config = config

    async def adapt(self, source_task: SourceTask, target_model: Any, target_data: Any) -> Any:
        """执行域适应"""
        # 实现域适应算法(如DANN、ADDA等)
        # 简化实现
        return target_model


class MultiTaskLearner:
    """多任务学习器"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.shared_layers = {}
        self.task_specific_layers = {}

    async def add_task(self, source_task: SourceTask, target_model: Any, target_data: Any) -> Any:
        """添加新任务到多任务学习"""
        # 实现多任务学习
        # 简化实现
        return target_model


# 创建全局迁移学习框架实例
transfer_learning_framework = TransferLearningFramework()


# 便捷函数
async def register_model_for_transfer(task_id: str, model: Any, performance: float) -> bool:
    """注册模型用于迁移"""
    performance_metrics = {"accuracy": performance}
    return await transfer_learning_framework.register_source_task(
        task_id, task_id, "unknown", "unknown", model, performance_metrics
    )


async def transfer_from_similar(task_id: str, model: Any, top_k: int = 3) -> list[TransferResult]:
    """从相似任务迁移"""
    return await transfer_learning_framework.batch_transfer(task_id, model, max_sources=top_k)


def get_transfer_stats() -> dict[str, Any]:
    """获取迁移统计"""
    return transfer_learning_framework.get_transfer_statistics()


# =============================================================================
# === 域适应类 ===
# =============================================================================

@dataclass
class DomainAdaptation:
    """域适应配置"""

    source_domain: str
    target_domain: str
    adaptation_method: str = "fine_tuning"  # fine_tuning, feature_alignment, adversarial
    adaptation_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 10

    def adapt_model(
        self,
        source_model: Any,
        target_data: Any,
    ) -> Any:
        """
        适应源模型到目标域

        Args:
            source_model: 源域模型
            target_data: 目标域数据

        Returns:
            适应后的模型
        """
        # 简化实现：返回源模型（实际中应该进行微调）
        return source_model


# 创建便捷函数
def create_domain_adaptation(
    source_domain: str,
    target_domain: str,
    adaptation_method: str = "fine_tuning",
) -> DomainAdaptation:
    """创建域适应配置"""
    return DomainAdaptation(
        source_domain=source_domain,
        target_domain=target_domain,
        adaptation_method=adaptation_method,
    )


__all__ = [
    "SourceTask",
    "TransferResult",
    "TransferStrategy",
    "TransferLearningFramework",
    "transfer_learning_framework",
    "DomainAdaptation",
    "create_domain_adaptation",
    "register_model_for_transfer",
    "transfer_from_similar",
    "get_transfer_stats",
]
