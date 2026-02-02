#!/usr/bin/env python3
"""
在线学习系统 - 第二阶段
Online Learning System - Phase 2

核心功能:
1. 用户反馈收集
2. 模型增量更新
3. 学习调度策略
4. A/B测试框架

作者: 小诺·双鱼公主
版本: v1.0.0 "在线学习"
创建: 2026-01-12
"""

import logging
import queue
import random
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# 导入配置常量
try:
    from .learning_config import BatchConfig
except ImportError:
    from core.learning.learning_config import BatchConfig

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """反馈类型"""

    THUMBS_UP = "thumbs_up"  # 点赞
    THUMBS_DOWN = "thumbs_down"  # 点踩
    RATING = "rating"  # 评分(1-5)
    CORRECTION = "correction"  # 纠正
    SUGGESTION = "suggestion"  # 建议


@dataclass
class UserFeedback:
    """用户反馈"""

    feedback_id: str
    user_id: str
    session_id: str
    feedback_type: FeedbackType
    feedback_data: Any

    # 关联的任务信息
    task_type: str  # 任务类型(如: routing, extraction)
    task_input: dict[str, Any]  # 任务输入
    task_output: dict[str, Any]  # 任务输出
    model_used: str  # 使用的模型/策略

    # 反馈详情
    rating: int | None = None  # 1-5评分
    correction: str | None = None  # 纠正内容
    suggestions: list[str] = field(default_factory=list)

    # 元数据
    timestamp: datetime = field(default_factory=datetime.now)
    processed: bool = False
    processed_at: datetime | None = None


@dataclass
class LearningUpdate:
    """学习更新"""

    update_id: str
    model_id: str
    update_type: str  # incremental, full, adaptive
    old_performance: float
    new_performance: float
    update_size: int  # 更新的样本数
    update_time: datetime = field(default_factory=datetime.now)


@dataclass
class ABTestVariant:
    """A/B测试变体"""

    variant_id: str
    name: str
    model_id: str
    config: dict[str, Any]
    traffic_ratio: float  # 流量比例(0-1)

    # 统计
    total_requests: int = 0
    successful_requests: int = 0
    avg_reward: float = 0.0
    user_satisfaction: float = 0.0


class OnlineLearningSystem:
    """在线学习系统"""

    def __init__(self):
        self.name = "在线学习系统 v1.0"
        self.version = "1.0.0"

        # 反馈队列
        self.feedback_queue: queue.Queue = queue.Queue(maxsize=10000)

        # 反馈存储(线程安全)
        self.feedback_storage: list[UserFeedback] = []
        self._storage_lock = threading.Lock()

        # 学习历史(线程安全)
        self.learning_history: list[LearningUpdate] = []
        self._history_lock = threading.Lock()

        # A/B测试管理(线程安全)
        self.ab_tests: dict[str, list[ABTestVariant]] = {}
        self._ab_test_lock = threading.Lock()

        # 模型性能追踪(线程安全)
        self.model_performance: dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._performance_lock = threading.Lock()

        # 统计信息(线程安全)
        self.stats = {
            "total_feedback": 0,
            "processed_feedback": 0,
            "learning_updates": 0,
            "active_ab_tests": 0,
            "feedback_rate": 0.0,
        }
        self._stats_lock = threading.Lock()

        # 后台线程
        self._learning_thread: threading.Thread | None = None
        self._running = False

        # 关闭事件(用于优雅关闭)
        self._shutdown_event = threading.Event()

        logger.info(f"🎓 {self.name} 初始化完成(带线程安全保护)")

    def start(self) -> None:
        """启动在线学习系统"""
        if self._running:
            logger.warning("在线学习系统已在运行")
            return

        self._running = True
        self._learning_thread = threading.Thread(target=self._learning_loop, daemon=True)
        self._learning_thread.start()

        logger.info("🚀 在线学习系统已启动")

    def stop(self) -> None:
        """停止在线学习系统"""
        self._running = False
        if self._learning_thread:
            self._learning_thread.join(timeout=5.0)

        logger.info("🛑 在线学习系统已停止")

    def _learning_loop(self) -> Any:
        """学习循环(后台线程)"""
        logger.info("🔄 学习循环已启动")

        while self._running and not self._shutdown_event.is_set():
            try:
                # 从队列获取反馈
                try:
                    feedback = self.feedback_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                # 处理反馈
                self._process_feedback_async(feedback)

                # 定期批量更新模型(使用配置常量)- 线程安全读取
                with self._stats_lock:
                    processed_count = self.stats["processed_feedback"]

                if processed_count % BatchConfig.MODEL_UPDATE_BATCH_SIZE == 0:
                    self._batch_model_update()

            except Exception as e:
                logger.error(f"❌ 学习循环错误: {e}", exc_info=True)

        logger.info("🔄 学习循环已停止")

    async def collect_feedback(
        self,
        user_id: str,
        session_id: str,
        feedback_type: FeedbackType,
        task_info: dict[str, Any],        feedback_data: Any,
    ) -> str:
        """
        收集用户反馈

        Args:
            user_id: 用户ID
            session_id: 会话ID
            feedback_type: 反馈类型
            task_info: 任务信息
            feedback_data: 反馈数据

        Returns:
            str: 反馈ID
        """
        feedback_id = f"feedback_{int(time.time() * 1000)}"

        feedback = UserFeedback(
            feedback_id=feedback_id,
            user_id=user_id,
            session_id=session_id,
            feedback_type=feedback_type,
            feedback_data=feedback_data,
            task_type=task_info.get("task_type", "unknown"),
            task_input=task_info.get("input", {}),
            task_output=task_info.get("output", {}),
            model_used=task_info.get("model", "default"),
            rating=(
                feedback_data.get("rating") if isinstance(feedback_data, dict) else feedback_data
            ),
            correction=feedback_data.get("correction") if isinstance(feedback_data, dict) else None,
            suggestions=(
                feedback_data.get("suggestions", []) if isinstance(feedback_data, dict) else []
            ),
        )

        # 添加到队列
        try:
            self.feedback_queue.put(feedback, timeout=1.0)
            # 线程安全地更新统计
            with self._stats_lock:
                self.stats["total_feedback"] += 1

            logger.info(f"📝 反馈已收集: {feedback_id}")
            return feedback_id

        except queue.Full:
            logger.error("❌ 反馈队列已满")
            raise

    def _process_feedback_async(self, feedback: UserFeedback) -> Any:
        """异步处理反馈"""
        try:
            # 1. 根据任务类型处理
            if feedback.task_type == "routing":
                self._process_routing_feedback(feedback)
            elif feedback.task_type == "extraction":
                self._process_extraction_feedback(feedback)
            elif feedback.task_type == "classification":
                self._process_classification_feedback(feedback)
            else:
                logger.warning(f"⚠️ 未知任务类型: {feedback.task_type}")

            # 2. 更新模型性能追踪(线程安全)
            self._update_model_performance(feedback)

            # 3. 标记为已处理(线程安全)
            feedback.processed = True
            feedback.processed_at = datetime.now()
            with self._storage_lock:
                self.feedback_storage.append(feedback)

            # 线程安全地更新统计
            with self._stats_lock:
                self.stats["processed_feedback"] += 1

        except Exception as e:
            logger.error(f"❌ 反馈处理失败: {e}", exc_info=True)

    def _process_routing_feedback(self, feedback: UserFeedback) -> Any:
        """处理路由反馈"""
        model = feedback.model_used
        rating = feedback.rating

        if rating is None:
            return

        # 记录性能(线程安全)
        performance = rating / 5.0  # 归一化到0-1
        with self._performance_lock:
            self.model_performance[model].append(
                {"performance": performance, "timestamp": datetime.now().isoformat()}
            )

        logger.debug(f"📊 路由模型 {model} 性能更新: {performance:.2f}")

    def _process_extraction_feedback(self, feedback: UserFeedback) -> Any:
        """处理参数提取反馈"""
        # 简化实现: 记录反馈
        logger.debug(f"📊 参数提取反馈: {feedback.feedback_id}")

    def _process_classification_feedback(self, feedback: UserFeedback) -> Any:
        """处理分类反馈"""
        # 简化实现: 记录反馈
        logger.debug(f"📊 分类反馈: {feedback.feedback_id}")

    def _update_model_performance(self, feedback: UserFeedback) -> Any:
        """更新模型性能(线程安全)"""
        # 根据反馈更新性能指标
        if feedback.rating:
            feedback.rating / 5.0
            model = feedback.model_used

            # 更新最近性能(线程安全)
            with self._performance_lock:
                recent_perf = self.model_performance[model]
                if len(recent_perf) > 0:
                    avg_perf = sum(p["performance"] for p in recent_perf) / len(recent_perf)
                    self.model_performance[model].append(
                        {
                            "performance": avg_perf,
                            "timestamp": datetime.now().isoformat(),
                            "type": "average",
                        }
                    )

    def _batch_model_update(self) -> Any:
        """批量更新模型(线程安全)"""
        logger.info("🔄 执行批量模型更新...")

        # 遍历所有模型(线程安全地读取)
        with self._performance_lock:
            model_items = list(self.model_performance.items())

        for model_id, perf_history in model_items:
            if len(perf_history) < 10:
                continue  # 样本不足,跳过

            # 计算平均性能
            recent_perf = list(perf_history)[-10:]
            avg_performance = sum(p["performance"] for p in recent_perf) / len(recent_perf)

            # 检查是否需要更新
            old_performance = recent_perf[0]["performance"]
            if avg_performance > old_performance * 1.05:  # 性能提升5%以上
                self._trigger_model_update(model_id, old_performance, avg_performance)

    def _trigger_model_update(self, model_id: str, old_performance: float, new_performance: float):
        """触发模型更新(线程安全)"""
        update_id = f"update_{int(time.time() * 1000)}"

        update = LearningUpdate(
            update_id=update_id,
            model_id=model_id,
            update_type="incremental",
            old_performance=old_performance,
            new_performance=new_performance,
            update_size=10,  # 最近10个样本
        )

        # 线程安全地更新学习历史
        with self._history_lock:
            self.learning_history.append(update)

        # 线程安全地更新统计
        with self._stats_lock:
            self.stats["learning_updates"] += 1

        logger.info(f"📈 模型 {model_id} 更新: {old_performance:.3f} → {new_performance:.3f}")

    def create_ab_test(self, test_name: str, variants: list[dict[str, Any]]) -> str:
        """
        创建A/B测试

        Args:
            test_name: 测试名称
            variants: 变体列表 [{"name": "A", "model_id": "model_a", "traffic": 0.5}, ...]

        Returns:
            str: 测试ID
        """
        test_id = f"ab_test_{test_name}_{int(time.time())}"

        # 创建变体
        ab_variants = []
        total_traffic = sum(v.get("traffic", 0.5) for v in variants)

        for i, var in enumerate(variants):
            traffic_ratio = var.get("traffic", 0.5) / total_traffic
            ab_variants.append(
                ABTestVariant(
                    variant_id=f"{test_id}_variant_{i}",
                    name=var["name"],
                    model_id=var["model_id"],
                    config=var.get("config", {}),
                    traffic_ratio=traffic_ratio,
                )
            )

        self.ab_tests[test_id] = ab_variants
        # 线程安全地更新统计
        with self._stats_lock:
            self.stats["active_ab_tests"] = len(self.ab_tests)

        logger.info(f"🧪 A/B测试已创建: {test_id}, {len(variants)}个变体")
        return test_id

    def get_ab_variant(self, test_id: str) -> ABTestVariant | None:
        """获取A/B测试的变体(线程安全)"""
        with self._ab_test_lock:
            if test_id not in self.ab_tests:
                return None

            variants = self.ab_tests[test_id]

        # 基于流量比例随机选择
        rand = random.random()
        cumulative = 0.0

        for variant in variants:
            cumulative += variant.traffic_ratio
            if rand <= cumulative:
                variant.total_requests += 1
                return variant

        return variants[-1]  # 返回最后一个作为兜底

    def record_ab_result(self, test_id: str, variant_id: str, success: bool, reward: float):
        """记录A/B测试结果(线程安全)"""
        with self._ab_test_lock:
            if test_id not in self.ab_tests:
                logger.warning(f"⚠️ 未知测试ID: {test_id}")
                return

            variant = next((v for v in self.ab_tests[test_id] if v.variant_id == variant_id), None)

            if variant:
                variant.total_requests += 1
                if success:
                    variant.successful_requests += 1

                # 更新平均奖励
                n = variant.total_requests
                old_avg = variant.avg_reward
                variant.avg_reward = (old_avg * (n - 1) + reward) / n

    def analyze_ab_test(self, test_id: str) -> dict[str, Any]:
        """分析A/B测试结果(线程安全)"""
        with self._ab_test_lock:
            if test_id not in self.ab_tests:
                return {"error": "未知测试ID"}

            variants = self.ab_tests[test_id]

        results = []
        for variant in variants:
            if variant.total_requests == 0:
                continue

            success_rate = variant.successful_requests / variant.total_requests

            results.append(
                {
                    "variant": variant.name,
                    "model_id": variant.model_id,
                    "total_requests": variant.total_requests,
                    "success_rate": success_rate,
                    "avg_reward": variant.avg_reward,
                }
            )

        # 找出最佳变体
        if results:
            best = max(results, key=lambda r: r["success_rate"])
            return {
                "test_id": test_id,
                "results": results,
                "best_variant": best["variant"],
                "best_success_rate": best["success_rate"],
            }

        return {"error": "没有足够的数据"}

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息(线程安全)"""
        # 线程安全地读取所有数据
        with self._stats_lock:
            stats_copy = self.stats.copy()
            total_feedback = stats_copy["total_feedback"]
            processed_feedback = stats_copy["processed_feedback"]

        with self._storage_lock:
            storage_size = len(self.feedback_storage)

        with self._performance_lock:
            models_count = len(self.model_performance)

        with self._ab_test_lock:
            ab_tests_count = len(self.ab_tests)

        # 计算反馈率
        feedback_rate = 0.0
        if total_feedback > 0:
            feedback_rate = processed_feedback / total_feedback

        return {
            **stats_copy,
            "feedback_rate": feedback_rate,
            "queue_size": self.feedback_queue.qsize(),
            "storage_size": storage_size,
            "models_tracked": models_count,
            "ab_tests_active": ab_tests_count,
        }

    def get_model_performance(self, model_id: str, window: int = 10) -> dict[str, float]:
        """获取模型性能(线程安全)"""
        with self._performance_lock:
            if model_id not in self.model_performance:
                return {}

            perf_history = list(self.model_performance[model_id])
            recent = perf_history[-window:]

        if not recent:
            return {}

        performances = [p["performance"] for p in recent if "performance" in p]

        return {
            "avg_performance": sum(performances) / len(performances),
            "min_performance": min(performances),
            "max_performance": max(performances),
            "sample_count": len(performances),
        }


# 全局实例
_learning_system_instance: OnlineLearningSystem | None = None


def get_online_learning_system() -> OnlineLearningSystem:
    """获取在线学习系统单例"""
    global _learning_system_instance
    if _learning_system_instance is None:
        _learning_system_instance = OnlineLearningSystem()
    return _learning_system_instance
