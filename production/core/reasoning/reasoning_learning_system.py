#!/usr/bin/env python3
"""
推理历史分析和增量学习系统
Reasoning History Analysis and Incremental Learning System

作者: Athena AI团队
版本: v1.0.0
创建时间: 2026-01-26

功能:
1. 记录和分析推理历史
2. 从历史数据中学习优化策略
3. 自动调整路由权重
4. 个性化推理偏好
5. 预测性引擎选择
"""

from __future__ import annotations
import asyncio
import hashlib
import json
import logging
import statistics
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """反馈类型"""

    POSITIVE = "positive"  # 正面反馈
    NEGATIVE = "negative"  # 负面反馈
    NEUTRAL = "neutral"  # 中性反馈


class MetricType(Enum):
    """指标类型"""

    RESPONSE_TIME = "response_time"
    ACCURACY = "accuracy"
    CONFIDENCE = "confidence"
    USER_SATISFACTION = "user_satisfaction"
    CACHE_HIT_RATE = "cache_hit_rate"


@dataclass
class ReasoningRecord:
    """推理记录"""

    record_id: str
    timestamp: datetime
    task_description: str
    task_type: str
    engine_name: str
    reasoning_mode: str | None = None

    # 输入信息
    input_data: dict[str, Any] = field(default_factory=dict)

    # 输出结果
    result: dict[str, Any] = field(default_factory=dict)
    conclusion: str = ""
    confidence: float = 0.0

    # 性能指标
    execution_time: float = 0.0
    from_cache: bool = False
    success: bool = True
    error_message: str | None = None

    # 用户反馈
    user_feedback: FeedbackType | None = None
    feedback_score: float | None = None  # 0-10
    feedback_comment: str | None = None

    # 上下文信息
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        if self.user_feedback:
            data["user_feedback"] = self.user_feedback.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReasoningRecord":
        """从字典创建"""
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if isinstance(data.get("user_feedback"), str):
            data["user_feedback"] = FeedbackType(data["user_feedback"])
        return cls(**data)

    def compute_hash(self) -> str:
        """计算任务哈希（用于识别相似任务）"""
        content = f"{self.task_type}:{self.task_description}"
        return hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()[:16]


@dataclass
class EnginePerformanceStats:
    """引擎性能统计"""

    engine_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_execution_time: float = 0.0

    # 性能指标
    avg_response_time: float = 0.0
    p50_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0

    # 质量指标
    avg_confidence: float = 0.0
    avg_user_satisfaction: float = 0.0

    # 缓存指标
    cache_hits: int = 0
    cache_misses: int = 0

    # 时间窗口
    response_times: list[float] = field(default_factory=list)
    recent_scores: list[float] = field(default_factory=list)

    def update(self, record: ReasoningRecord) -> None:
        """更新统计信息"""
        self.total_requests += 1

        if record.success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        self.total_execution_time += record.execution_time
        self.response_times.append(record.execution_time)

        # 只保留最近100次记录
        if len(self.response_times) > 100:
            self.response_times = self.response_times[-100:]

        # 更新响应时间统计
        if self.response_times:
            sorted_times = sorted(self.response_times)
            self.p50_response_time = sorted_times[len(sorted_times) // 2]
            self.p95_response_time = sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 1 else sorted_times[0]
            self.p99_response_time = sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 1 else sorted_times[0]
            self.avg_response_time = statistics.mean(self.response_times)

        # 更新置信度
        if record.confidence > 0:
            self.recent_scores.append(record.confidence)
            if len(self.recent_scores) > 100:
                self.recent_scores = self.recent_scores[-100:]
            self.avg_confidence = statistics.mean(self.recent_scores)

        # 更新用户满意度
        if record.feedback_score is not None:
            # 这里简化处理，实际应该单独跟踪
            self.avg_user_satisfaction = record.feedback_score

        # 更新缓存统计
        if record.from_cache:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def get_score(self, metric_weights: dict[str, float | None] | None = None) -> float:
        """计算综合评分"""
        weights = metric_weights or {
            "speed": 0.3,
            "reliability": 0.3,
            "quality": 0.2,
            "satisfaction": 0.2,
        }

        # 归一化指标
        speed_score = max(0, 1 - min(self.avg_response_time / 5.0, 1.0))  # 5秒为基准
        reliability_score = self.successful_requests / max(self.total_requests, 1)
        quality_score = self.avg_confidence
        satisfaction_score = self.avg_user_satisfaction / 10.0 if self.avg_user_satisfaction > 0 else 0.5

        total_score = (
            speed_score * weights["speed"]
            + reliability_score * weights["reliability"]
            + quality_score * weights["quality"]
            + satisfaction_score * weights["satisfaction"]
        )

        return total_score


@dataclass
class RoutingRule:
    """路由规则"""

    task_type: str
    engine_preferences: dict[str, float]  # engine_name -> weight
    confidence_threshold: float = 0.7
    bypass_super_reasoning: bool = False

    # 规则统计
    usage_count: int = 0
    success_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

    def update_weights(
        self, performance_data: dict[str, EnginePerformanceStats]
    ) -> None:
        """根据性能数据更新权重"""
        total_score = 0.0

        # 计算每个引擎的得分
        engine_scores = {}
        for engine_name, weight in self.engine_preferences.items():
            if engine_name in performance_data:
                stats = performance_data[engine_name]
                score = stats.get_score()
                engine_scores[engine_name] = score * weight
                total_score += engine_scores[engine_name]

        # 归一化权重
        if total_score > 0:
            for engine_name in self.engine_preferences:
                if engine_name in engine_scores:
                    self.engine_preferences[engine_name] = engine_scores[engine_name] / total_score

        self.last_updated = datetime.now()


class ReasoningHistoryAnalyzer:
    """推理历史分析器"""

    def __init__(
        self,
        storage_path: str | None = None,
        max_history_size: int = 10000,
        analysis_window: int = 7,  # 天
    ):
        self.storage_path = Path(storage_path or "data/reasoning_history")
        self.max_history_size = max_history_size
        self.analysis_window = analysis_window

        # 历史记录
        self.records: deque[ReasoningRecord] = deque(maxlen=max_history_size)

        # 引擎性能统计
        self.engine_stats: dict[str, EnginePerformanceStats] = defaultdict(
            lambda: EnginePerformanceStats(engine_name="")
        )

        # 路由规则
        self.routing_rules: dict[str, RoutingRule] = {}

        # 任务模式
        self.task_patterns: dict[str, list[str]] = defaultdict(list)

        # 加载历史数据
        self._load_history()

        logger.info("📊 推理历史分析器初始化完成")

    def _load_history(self) -> None:
        """加载历史数据"""
        try:
            # 创建存储目录
            self.storage_path.mkdir(parents=True, exist_ok=True)

            # 加载记录
            records_file = self.storage_path / "reasoning_records.jsonl"
            if records_file.exists():
                with open(records_file, encoding="utf-8") as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            record = ReasoningRecord.from_dict(data)
                            self.records.append(record)
                            self._update_stats(record)
                        except Exception as e:
                            logger.warning(f"加载记录失败: {e}")

            # 加载路由规则
            rules_file = self.storage_path / "routing_rules.json"
            if rules_file.exists():
                with open(rules_file, encoding="utf-8") as f:
                    try:
                        rules_data = json.load(f)
                        for task_type, rule_data in rules_data.items():
                            rule = RoutingRule(
                                task_type=task_type,
                                engine_preferences=rule_data["engine_preferences"],
                                confidence_threshold=rule_data.get("confidence_threshold", 0.7),
                                bypass_super_reasoning=rule_data.get("bypass_super_reasoning", False),
                            )
                            self.routing_rules[task_type] = rule
                    except Exception as e:
                        logger.warning(f"加载路由规则失败: {e}")

            logger.info(f"📂 已加载 {len(self.records)} 条历史记录")

        except Exception as e:
            logger.error(f"加载历史数据失败: {e}")

    def _update_stats(self, record: ReasoningRecord) -> None:
        """更新统计信息"""
        # 更新引擎统计
        if record.engine_name not in self.engine_stats:
            self.engine_stats[record.engine_name] = EnginePerformanceStats(
                engine_name=record.engine_name
            )
        self.engine_stats[record.engine_name].update(record)

        # 更新任务模式
        task_hash = record.compute_hash()
        self.task_patterns[task_hash].append(record.engine_name)

    def record_reasoning(self, record: ReasoningRecord) -> None:
        """记录推理过程"""
        # 添加到内存
        self.records.append(record)

        # 更新统计
        self._update_stats(record)

        # 持久化
        self._persist_record(record)

    def _persist_record(self, record: ReasoningRecord) -> None:
        """持久化记录"""
        try:
            records_file = self.storage_path / "reasoning_records.jsonl"
            with open(records_file, "a", encoding="utf-8") as f:
                json.dump(record.to_dict(), f, ensure_ascii=False)
                f.write("\n")
        except Exception as e:
            logger.error(f"持久化记录失败: {e}")

    def get_engine_performance(
        self, engine_name: str
    ) -> EnginePerformanceStats | None:
        """获取引擎性能统计"""
        return self.engine_stats.get(engine_name)

    def get_task_type_performance(self, task_type: str) -> dict[str, float]:
        """获取任务类型的引擎性能"""
        # 筛选相关记录
        relevant_records = [
            r for r in self.records if r.task_type == task_type and r.success
        ]

        if not relevant_records:
            return {}

        # 按引擎分组统计
        engine_performance: dict[str, list[float]] = defaultdict(list)
        for record in relevant_records:
            # 综合评分：响应时间(40%) + 置信度(30%) + 用户满意度(30%)
            time_score = max(0, 1 - record.execution_time / 5.0)
            confidence_score = record.confidence
            satisfaction_score = record.feedback_score / 10.0 if record.feedback_score else 0.5

            total_score = (
                time_score * 0.4
                + confidence_score * 0.3
                + satisfaction_score * 0.3
            )

            engine_performance[record.engine_name].append(total_score)

        # 计算平均得分
        return {
            engine: statistics.mean(scores)
            for engine, scores in engine_performance.items()
            if scores
        }

    def analyze_trends(self, days: int = 7) -> dict[str, Any]:
        """分析趋势"""
        cutoff_time = datetime.now() - timedelta(days=days)
        recent_records = [
            r for r in self.records if r.timestamp >= cutoff_time
        ]

        if not recent_records:
            return {"error": "没有足够的近期数据"}

        # 按天统计
        daily_stats: dict[str, dict] = defaultdict(lambda: {
            "total": 0,
            "successful": 0,
            "avg_time": 0.0,
            "avg_confidence": 0.0,
        })

        for record in recent_records:
            day_key = record.timestamp.strftime("%Y-%m-%d")
            daily_stats[day_key]["total"] += 1
            if record.success:
                daily_stats[day_key]["successful"] += 1
            daily_stats[day_key]["avg_time"] += record.execution_time
            daily_stats[day_key]["avg_confidence"] += record.confidence

        # 计算平均值
        for day_stats in daily_stats.values():
            if day_stats["total"] > 0:
                day_stats["avg_time"] /= day_stats["total"]
                day_stats["avg_confidence"] /= day_stats["total"]
                day_stats["success_rate"] = day_stats["successful"] / day_stats["total"]

        return {
            "period": f"最近{days}天",
            "total_requests": len(recent_records),
            "daily_stats": dict(sorted(daily_stats.items())),
        }

    def recommend_engine(
        self,
        task_type: str,
        task_description: str,
        n_recommendations: int = 3,
    ) -> list[dict[str, Any]]:
        """推荐引擎"""
        recommendations = []

        # 获取任务类型性能
        task_performance = self.get_task_type_performance(task_type)

        # 获取全局性能
        global_performance = {
            engine: stats.get_score()
            for engine, stats in self.engine_stats.items()
        }

        # 组合推荐
        engine_scores: dict[str, float] = defaultdict(float)

        # 任务类型性能权重70%
        for engine, score in task_performance.items():
            engine_scores[engine] += score * 0.7

        # 全局性能权重30%
        for engine, score in global_performance.items():
            engine_scores[engine] += score * 0.3

        # 排序
        sorted_engines = sorted(
            engine_scores.items(), key=lambda x: x[1], reverse=True
        )

        # 生成推荐
        for engine_name, score in sorted_engines[:n_recommendations]:
            stats = self.engine_stats.get(engine_name)
            recommendations.append({
                "engine_name": engine_name,
                "score": score,
                "avg_response_time": stats.avg_response_time if stats else 0,
                "success_rate": (
                    stats.successful_requests / max(stats.total_requests, 1)
                    if stats else 0
                ),
                "avg_confidence": stats.avg_confidence if stats else 0,
            })

        return recommendations


class IncrementalLearningSystem:
    """增量学习系统"""

    def __init__(
        self,
        analyzer: ReasoningHistoryAnalyzer | None = None,
        learning_interval: int = 3600,  # 秒
    ):
        self.analyzer = analyzer or ReasoningHistoryAnalyzer()
        self.learning_interval = learning_interval

        # 学习任务
        self._learning_task: asyncio.Task | None = None

        # 路由权重优化器
        self.routing_optimizer = RoutingOptimizer(self.analyzer)

        # 个性化偏好
        self.user_preferences: dict[str, dict] = {}

        logger.info("🧠 增量学习系统初始化完成")

    async def start_learning(self) -> None:
        """启动学习循环"""
        if self._learning_task is None or self._learning_task.done():
            self._learning_task = asyncio.create_task(self._learning_loop())
            logger.info("🚀 增量学习已启动")

    async def stop_learning(self) -> None:
        """停止学习"""
        if self._learning_task and not self._learning_task.done():
            self._learning_task.cancel()
            logger.info("⏹️ 增量学习已停止")

    async def _learning_loop(self) -> None:
        """学习循环"""
        while True:
            try:
                await asyncio.sleep(self.learning_interval)
                await self._learn()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"学习循环异常: {e}")

    async def _learn(self) -> None:
        """执行学习"""
        logger.info("📚 开始学习优化...")

        # 1. 优化路由权重
        await self.routing_optimizer.optimize()

        # 2. 分析趋势
        trends = self.analyzer.analyze_trends()
        logger.info(f"📈 趋势分析: {trends.get('total_requests', 0)} 个请求")

        # 3. 更新个性化偏好
        self._update_user_preferences()

        logger.info("✅ 学习优化完成")

    def _update_user_preferences(self) -> None:
        """更新用户偏好"""
        # 分析用户反馈模式
        positive_records = [
            r for r in self.analyzer.records
            if r.user_feedback == FeedbackType.POSITIVE
        ]

        if not positive_records:
            return

        # 按任务类型统计
        task_engines: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for record in positive_records:
            task_engines[record.task_type][record.engine_name] += 1

        # 更新偏好
        self.user_preferences = {
            task_type: {
                engine: count / max(sum(engines.values()), 1)
                for engine, count in engines.items()
            }
            for task_type, engines in task_engines.items()
        }

    def get_personalized_recommendation(
        self, task_type: str
    ) -> dict[str, float | None]:
        """获取个性化推荐"""
        return self.user_preferences.get(task_type)

    async def learn_from_feedback(
        self, record: ReasoningRecord, feedback: FeedbackType
    ) -> None:
        """从反馈中学习"""
        record.user_feedback = feedback

        # 更新记录
        self.analyzer.record_reasoning(record)

        # 立即触发学习
        if feedback == FeedbackType.NEGATIVE:
            # 负面反馈立即优化
            await self.routing_optimizer.optimize_task_type(record.task_type)


class RoutingOptimizer:
    """路由优化器"""

    def __init__(self, analyzer: ReasoningHistoryAnalyzer):
        self.analyzer = analyzer

    async def optimize(self) -> None:
        """优化所有路由规则"""
        for task_type in self.analyzer.routing_rules:
            await self.optimize_task_type(task_type)

    async def optimize_task_type(self, task_type: str) -> None:
        """优化特定任务类型的路由"""
        rule = self.analyzer.routing_rules.get(task_type)
        if not rule:
            return

        # 获取性能数据
        performance_data = self.analyzer.engine_stats

        # 更新权重
        rule.update_weights(performance_data)

        # 更新统计
        relevant_records = [
            r for r in self.analyzer.records
            if r.task_type == task_type
        ]
        rule.usage_count = len(relevant_records)

        if relevant_records:
            rule.success_rate = (
                sum(1 for r in relevant_records if r.success)
                / len(relevant_records)
            )

        logger.info(f"优化路由规则: {task_type}")


# 全局单例
_analyzer_instance: ReasoningHistoryAnalyzer | None = None
_learning_system_instance: IncrementalLearningSystem | None = None


def get_history_analyzer() -> ReasoningHistoryAnalyzer:
    """获取历史分析器实例"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = ReasoningHistoryAnalyzer()
    return _analyzer_instance


def get_learning_system() -> IncrementalLearningSystem:
    """获取学习系统实例"""
    global _learning_system_instance
    if _learning_system_instance is None:
        _learning_system_instance = IncrementalLearningSystem(
            analyzer=get_history_analyzer()
        )
    return _learning_system_instance


# 便捷函数
def record_reasoning(
    task_description: str,
    task_type: str,
    engine_name: str,
    result: dict[str, Any],    execution_time: float,
    confidence: float = 0.0,
    success: bool = True,
    from_cache: bool = False,
) -> ReasoningRecord:
    """记录推理过程（便捷函数）"""
    analyzer = get_history_analyzer()

    record = ReasoningRecord(
        record_id=f"{datetime.now().timestamp()}",
        timestamp=datetime.now(),
        task_description=task_description,
        task_type=task_type,
        engine_name=engine_name,
        result=result,
        conclusion=result.get("result", ""),
        confidence=confidence,
        execution_time=execution_time,
        from_cache=from_cache,
        success=success,
    )

    analyzer.record_reasoning(record)
    return record


# 测试代码
if __name__ == "__main__":
    async def test_learning_system():
        """测试学习系统"""
        print("=" * 80)
        print("🧪 测试推理历史分析和增量学习系统")
        print("=" * 80)

        # 创建系统
        learning_system = get_learning_system()
        await learning_system.start_learning()

        # 模拟推理记录
        import random

        engines = ["athena_super", "semantic_v4", "dual_system"]
        task_types = ["patent_search", "office_action_response", "general_reasoning"]

        print("\n📝 模拟推理记录...")
        for i in range(20):
            engine = random.choice(engines)
            task_type = random.choice(task_types)

            record = ReasoningRecord(
                record_id=f"test_{i}",
                timestamp=datetime.now(),
                task_description=f"测试任务 {i}",
                task_type=task_type,
                engine_name=engine,
                conclusion=f"测试结论 {i}",
                confidence=random.uniform(0.6, 0.95),
                execution_time=random.uniform(0.5, 3.0),
                success=random.random() > 0.1,
                feedback_score=random.uniform(5.0, 10.0) if random.random() > 0.5 else None,
            )

            learning_system.analyzer.record_reasoning(record)

        # 获取引擎性能
        print("\n📊 引擎性能:")
        for engine_name in engines:
            stats = learning_system.analyzer.get_engine_performance(engine_name)
            if stats:
                print(f"\n{engine_name}:")
                print(f"  总请求: {stats.total_requests}")
                print(f"  平均响应时间: {stats.avg_response_time:.3f}s")
                print(f"  成功率: {stats.successful_requests / max(stats.total_requests, 1):.1%}")
                print(f"  综合评分: {stats.get_score():.3f}")

        # 获取推荐
        print("\n💡 引擎推荐:")
        recommendations = learning_system.analyzer.recommend_engine(
            task_type="patent_search",
            task_description="专利检索测试"
        )

        for rec in recommendations:
            print(f"  {rec['engine_name']}: 评分 {rec['score']:.3f}, "
                  f"响应时间 {rec['avg_response_time']:.3f}s, "
                  f"成功率 {rec['success_rate']:.1%}")

        # 等待学习
        await asyncio.sleep(2)

        await learning_system.stop_learning()

    asyncio.run(test_learning_system())
