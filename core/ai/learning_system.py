"""
AI学习系统
实现AI角色的持续学习和能力提升
"""
import numpy as np

import asyncio
import hashlib
import logging
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class LearningType(Enum):
    """学习类型"""

    SUPERVISED = "supervised"  # 监督学习
    REINFORCEMENT = "reinforcement"  # 强化学习
    UNSUPERVISED = "unsupervised"  # 无监督学习
    FEW_SHOT = "few_shot"  # 少样本学习
    CONTINUAL = "continual"  # 持续学习


class FeedbackType(Enum):
    """反馈类型"""

    POSITIVE = "positive"  # 正反馈
    NEGATIVE = "negative"  # 负反馈
    CORRECTION = "correction"  # 纠正
    SUGGESTION = "suggestion"  # 建议
    RATING = "rating"  # 评分


@dataclass
class LearningExperience:
    """学习经验"""

    id: str
    ai_role_id: str
    task_type: str
    input_data: dict[str, Any]
    output_data: dict[str, Any]
    feedback: dict[str, Any] | None = None
    feedback_type: FeedbackType | None = None
    feedback_score: float | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillProgress:
    """技能进度"""

    skill_name: str
    current_level: float = 0.0
    target_level: float = 1.0
    progress_rate: float = 0.0
    experiences_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    improvement_trend: list[float] = field(default_factory=list)
    mastery_threshold: float = 0.8


@dataclass
class LearningConfig:
    """学习配置"""

    learning_rate: float = 0.01
    decay_rate: float = 0.95
    experience_window: int = 1000  # 保留最近的经验数量
    feedback_weight: float = 0.7  # 反馈权重
    self_learning_weight: float = 0.3  # 自我学习权重
    min_confidence: float = 0.6  # 最小置信度
    update_frequency: int = 100  # 每100次经验更新一次
    skill_decay_factor: float = 0.99  # 技能衰减因子


class PerformanceTracker:
    """性能跟踪器"""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics: dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.timestamps: deque = deque(maxlen=window_size)

    def record_metric(
        self, metric_name: str, value: float, timestamp: datetime | None = None
    ) -> Any:
        """记录性能指标"""
        self.metrics[metric_name].append(value)
        self.timestamps.append(timestamp or datetime.now())

    def get_metric_stats(self, metric_name: str) -> dict[str, float]:
        """获取指标统计"""
        if metric_name not in self.metrics or len(self.metrics[metric_name]) == 0:
            return {}

        values = list(self.metrics[metric_name])
        return {
            "mean": np.mean(values),
            "std": np.std(values),
            "min": np.min(values),
            "max": np.max(values),
            "latest": values[-1],
            "trend": self._calculate_trend(values),
        }

    def _calculate_trend(self, values: list[float]) -> float:
        """计算趋势(简单线性回归斜率)"""
        if len(values) < 2:
            return 0.0

        x = np.arange(len(values))
        y = np.array(values)
        slope = np.polyfit(x, y, 1)[0]
        return slope

    def get_improvement_rate(self, metric_name: str, periods: int = 10) -> float:
        """计算改进率"""
        if metric_name not in self.metrics or len(self.metrics[metric_name]) < periods * 2:
            return 0.0

        values = list(self.metrics[metric_name])
        recent_avg = np.mean(values[-periods:])
        previous_avg = np.mean(values[-periods * 2 : -periods])

        if previous_avg == 0:
            return 0.0

        return (recent_avg - previous_avg) / previous_avg


class FeedbackAnalyzer:
    """反馈分析器"""

    def __init__(self):
        self.feedback_patterns: dict[str, dict] = {}
        self.correlation_cache: dict[str, float] = {}

    def analyze_feedback(self, experiences: list[LearningExperience]) -> dict[str, Any]:
        """分析反馈"""
        if not experiences:
            return {}

        # 按任务类型分组
        task_groups = defaultdict(list)
        for exp in experiences:
            if exp.feedback:
                task_groups[exp.task_type].append(exp)

        analysis = {
            "overall_score": self._calculate_overall_score(experiences),
            "task_performance": {},
            "feedback_patterns": self._identify_patterns(experiences),
            "improvement_areas": self._identify_improvement_areas(experiences),
        }

        # 分析各任务类型性能
        for task_type, task_exps in task_groups.items():
            analysis["task_performance"][task_type] = {
                "avg_score": np.mean([exp.feedback_score or 0 for exp in task_exps]),
                "feedback_count": len(task_exps),
                "success_rate": len(
                    [e for e in task_exps if e.feedback_score and e.feedback_score > 0.7]
                )
                / len(task_exps),
            }

        return analysis

    def _calculate_overall_score(self, experiences: list[LearningExperience]) -> float:
        """计算总体分数"""
        scores = [exp.feedback_score for exp in experiences if exp.feedback_score is not None]
        return np.mean(scores) if scores else 0.0

    def _identify_patterns(self, experiences: list[LearningExperience]) -> dict[str, Any]:
        """识别反馈模式"""
        patterns = {"common_errors": [], "strength_areas": [], "feedback_correlations": {}}

        # 分析常见错误
        error_exps = [exp for exp in experiences if exp.feedback_type == FeedbackType.NEGATIVE]
        error_tasks = [exp.task_type for exp in error_exps]
        if error_tasks:
            from collections import Counter

            task_counts = Counter(error_tasks)
            patterns["common_errors"] = task_counts.most_common(5)

        # 分析优势领域
        success_exps = [
            exp for exp in experiences if exp.feedback_score and exp.feedback_score > 0.8
        ]
        success_tasks = [exp.task_type for exp in success_exps]
        if success_tasks:
            from collections import Counter

            task_counts = Counter(success_tasks)
            patterns["strength_areas"] = task_counts.most_common(5)

        return patterns

    def _identify_improvement_areas(self, experiences: list[LearningExperience]) -> list[str]:
        """识别需要改进的领域"""
        # 计算每个任务类型的平均分数
        task_scores = defaultdict(list)
        for exp in experiences:
            if exp.feedback_score is not None:
                task_scores[exp.task_type].append(exp.feedback_score)

        # 找出分数最低的任务类型
        avg_scores = {task: np.mean(scores) for task, scores in task_scores.items()}
        sorted_tasks = sorted(avg_scores.items(), key=lambda x: x[1])

        # 返回需要改进的前3个领域
        return [task for task, score in sorted_tasks[:3]]


class AdaptiveLearning:
    """自适应学习系统"""

    def __init__(self, config: LearningConfig | None = None):
        self.config = config or LearningConfig()
        self.experiences: dict[str, list[LearningExperience]] = defaultdict(list)
        self.skill_progress: dict[str, dict[str, SkillProgress]] = defaultdict(dict)
        self.performance_tracker: dict[str, PerformanceTracker] = defaultdict(PerformanceTracker)
        self.feedback_analyzer = FeedbackAnalyzer()
        self.learning_models: dict[str, Any] = {}
        self.update_queue: asyncio.Queue = asyncio.Queue()

    async def add_experience(self, experience: LearningExperience) -> str:
        """添加学习经验"""
        # 生成经验ID
        if not experience.id:
            experience.id = hashlib.md5(
                f"{experience.ai_role_id}_{experience.task_type}_{time.time()}".encode()
            ).hexdigest()

        # 添加到经验池
        self.experiences[experience.ai_role_id].append(experience)

        # 限制经验数量
        if len(self.experiences[experience.ai_role_id]) > self.config.experience_window:
            self.experiences[experience.ai_role_id].pop(0)

        # 记录性能指标
        if experience.feedback_score is not None:
            tracker = self.performance_tracker[experience.ai_role_id]
            tracker.record_metric("task_performance", experience.feedback_score)
            tracker.record_metric(f"{experience.task_type}_performance", experience.feedback_score)

        # 加入更新队列
        await self.update_queue.put(experience)

        logger.info(f"添加学习经验: {experience.id} for {experience.ai_role_id}")
        return experience.id

    async def process_learning_queue(self):
        """处理学习队列"""
        batch_size = self.config.update_frequency
        batch = []

        while True:
            try:
                # 收集批次
                try:
                    experience = await asyncio.wait_for(self.update_queue.get(), timeout=1.0)
                    batch.append(experience)
                except asyncio.TimeoutError:
                    batch = []

                # 处理批次
                if len(batch) >= batch_size:
                    await self._update_learning_models(batch)
                    batch = []

                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"处理学习队列错误: {e}")
                await asyncio.sleep(1)

    async def _update_learning_models(self, experiences: list[LearningExperience]):
        """更新学习模型"""
        # 按AI角色分组
        role_groups = defaultdict(list)
        for exp in experiences:
            role_groups[exp.ai_role_id].append(exp)

        # 更新每个角色的学习模型
        for role_id, role_exps in role_groups.items():
            await self._update_role_model(role_id, role_exps)

    async def _update_role_model(self, role_id: str, experiences: list[LearningExperience]):
        """更新角色模型"""
        # 更新技能进度
        await self._update_skill_progress(role_id, experiences)

        # 分析反馈
        analysis = self.feedback_analyzer.analyze_feedback(self.experiences[role_id])

        # 调整学习参数
        await self._adjust_learning_parameters(role_id, analysis)

        # 更新知识库
        await self._update_knowledge_base(role_id, experiences)

    async def _update_skill_progress(self, role_id: str, experiences: list[LearningExperience]):
        """更新技能进度"""
        if role_id not in self.skill_progress:
            self.skill_progress[role_id] = {}

        # 从经验中提取技能
        for exp in experiences:
            if exp.feedback_score is not None:
                # 任务类型作为技能
                skill_name = exp.task_type

                if skill_name not in self.skill_progress[role_id]:
                    self.skill_progress[role_id][skill_name] = SkillProgress(skill_name=skill_name)

                skill = self.skill_progress[role_id][skill_name]
                skill.experiences_count += 1

                # 更新技能等级(使用指数移动平均)
                alpha = self.config.learning_rate
                new_level = alpha * exp.feedback_score + (1 - alpha) * skill.current_level
                skill.current_level = new_level
                skill.last_updated = datetime.now()

                # 记录改进趋势
                skill.improvement_trend.append(new_level)
                if len(skill.improvement_trend) > 100:
                    skill.improvement_trend.pop(0)

                # 计算进度率
                skill.progress_rate = new_level / skill.target_level

    async def _adjust_learning_parameters(self, role_id: str, analysis: dict[str, Any]):
        """调整学习参数"""
        # 根据性能分析调整参数
        overall_score = analysis.get("overall_score", 0)

        if overall_score < 0.5:
            # 性能差,增加学习率
            self.config.learning_rate = min(0.1, self.config.learning_rate * 1.1)
        elif overall_score > 0.8:
            # 性能好,降低学习率
            self.config.learning_rate = max(0.001, self.config.learning_rate * 0.95)

    async def _update_knowledge_base(self, role_id: str, experiences: list[LearningExperience]):
        """更新知识库"""
        # 提取成功的经验模式
        successful_exps = [
            exp for exp in experiences if exp.feedback_score and exp.feedback_score > 0.7
        ]

        # 这里可以实现具体的知识更新逻辑
        # 例如:提取成功模式、更新规则库等
        logger.info(f"更新 {role_id} 的知识库,{len(successful_exps)} 个成功经验")

    def get_skill_assessment(self, role_id: str) -> dict[str, Any]:
        """获取技能评估"""
        if role_id not in self.skill_progress:
            return {}

        skills = self.skill_progress[role_id]
        assessment = {
            "total_skills": len(skills),
            "mastered_skills": [],
            "developing_skills": [],
            "novice_skills": [],
            "overall_proficiency": 0.0,
        }

        total_proficiency = 0

        for skill_name, skill in skills.items():
            proficiency = skill.current_level

            if proficiency >= skill.mastery_threshold:
                assessment["mastered_skills"].append(
                    {
                        "name": skill_name,
                        "level": proficiency,
                        "experiences": skill.experiences_count,
                    }
                )
            elif proficiency >= 0.5:
                assessment["developing_skills"].append(
                    {
                        "name": skill_name,
                        "level": proficiency,
                        "experiences": skill.experiences_count,
                    }
                )
            else:
                assessment["novice_skills"].append(
                    {
                        "name": skill_name,
                        "level": proficiency,
                        "experiences": skill.experiences_count,
                    }
                )

            total_proficiency += proficiency

        if len(skills) > 0:
            assessment["overall_proficiency"] = total_proficiency / len(skills)

        return assessment

    def get_learning_recommendations(self, role_id: str) -> list[dict[str, Any]]:
        """获取学习建议"""
        if role_id not in self.skill_progress:
            return []

        skills = self.skill_progress[role_id]
        recommendations = []

        # 识别需要改进的技能
        for skill_name, skill in skills.items():
            if skill.current_level < skill.mastery_threshold:
                # 计算改进潜力
                recent_trend = (
                    np.mean(skill.improvement_trend[-10:]) if skill.improvement_trend else 0
                )

                recommendations.append(
                    {
                        "skill": skill_name,
                        "current_level": skill.current_level,
                        "target_level": skill.target_level,
                        "improvement_potential": recent_trend,
                        "recommended_actions": self._generate_action_recommendations(
                            skill_name, skill
                        ),
                        "priority": "high" if skill.current_level < 0.3 else "medium",
                    }
                )

        # 按优先级排序
        recommendations.sort(key=lambda x: (x["priority"] == "high", -x["improvement_potential"]))

        return recommendations[:5]  # 返回前5个建议

    def _generate_action_recommendations(self, skill_name: str, skill: SkillProgress) -> list[str]:
        """生成行动建议"""
        actions = []

        if skill.current_level < 0.3:
            actions.append("需要加强基础训练")
            actions.append("寻求专家指导")
        elif skill.current_level < 0.6:
            actions.append("增加练习频率")
            actions.append("分析成功案例")
        else:
            actions.append("挑战更高难度任务")
            actions.append("分享经验帮助他人")

        return actions

    def get_performance_trends(self, role_id: str, days: int = 30) -> dict[str, Any]:
        """获取性能趋势"""
        if role_id not in self.performance_tracker:
            return {}

        tracker = self.performance_tracker[role_id]
        trends = {}

        # 计算各指标的趋势
        for metric_name in tracker.metrics:
            stats = tracker.get_metric_stats(metric_name)
            improvement_rate = tracker.get_improvement_rate(metric_name)

            trends[metric_name] = {
                "current_level": stats.get("latest", 0),
                "average": stats.get("mean", 0),
                "trend": stats.get("trend", 0),
                "improvement_rate": improvement_rate,
                "volatility": stats.get("std", 0),
            }

        return trends

    async def export_learning_data(self, role_id: str) -> dict[str, Any]:
        """导出学习数据"""
        return {
            "role_id": role_id,
            "experiences": [asdict(exp) for exp in self.experiences.get(role_id, [])],
            "skill_progress": {
                skill: asdict(progress)
                for skill, progress in self.skill_progress.get(role_id, {}).items()
            },
            "performance_stats": {
                metric: tracker.get_metric_stats(metric)
                for metric, tracker in self.performance_tracker[role_id].metrics.items()
            },
            "export_timestamp": datetime.now().isoformat(),
        }

    async def import_learning_data(self, data: dict[str, Any]):
        """导入学习数据"""
        role_id = data["role_id"]

        # 导入经验
        for exp_data in data.get("experiences", []):
            experience = LearningExperience(**exp_data)
            self.experiences[role_id].append(experience)

        # 导入技能进度
        for skill_name, progress_data in data.get("skill_progress", {}).items():
            self.skill_progress[role_id][skill_name] = SkillProgress(**progress_data)

        logger.info(f"导入学习数据完成: {role_id}")


# 全局学习系统实例
learning_system = AdaptiveLearning()


# 启动学习处理任务
async def start_learning_system():
    """启动学习系统"""
    logger.info("启动自适应学习系统")
    asyncio.create_task(learning_system.process_learning_queue())


# 便捷函数
async def record_ai_experience(
    ai_role_id: str,
    task_type: str,
    input_data: dict[str, Any],    output_data: dict[str, Any],    feedback: dict[str, Any] | None = None,
    feedback_type: FeedbackType | None = None,
    feedback_score: float | None = None,
) -> str:
    """记录AI经验"""
    experience = LearningExperience(
        id="",  # 将自动生成
        ai_role_id=ai_role_id,
        task_type=task_type,
        input_data=input_data,
        output_data=output_data,
        feedback=feedback,
        feedback_type=feedback_type,
        feedback_score=feedback_score,
    )
    return await learning_system.add_experience(experience)
