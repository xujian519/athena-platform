#!/usr/bin/env python3
"""
评估与反思引擎
Evaluation and Reflection Engine

智能评估与自我反思系统

作者: 小娜·天秤女神
创建时间: 2024年12月15日
"""

import asyncio
import json
import logging
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class EvaluationType(Enum):
    """评估类型"""
    PERFORMANCE = "performance"
    QUALITY = "quality"
    EFFICIENCY = "efficiency"
    SATISFACTION = "satisfaction"
    LEARNING = "learning"

class ReflectionType(Enum):
    """反思类型"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    INCIDENT = "incident"
    STRATEGIC = "strategic"

@dataclass
class EvaluationMetric:
    """评估指标"""
    name: str
    value: float
    unit: str
    benchmark: float
    trend: str  # improving, stable, declining
    last_updated: datetime

@dataclass
class Reflection:
    """反思记录"""
    reflection_id: str
    type: ReflectionType
    topic: str
    insights: list[str]
    action_items: list[str]
    impact_assessment: str
    confidence: float
    created_at: datetime
    status: str = "pending"

class EvaluationReflectionEngine:
    """评估与反思引擎"""

    def __init__(self):
        """初始化引擎"""
        self.name = "小娜评估反思引擎"
        self.version = "v2.0"

        # 存储路径
        self.data_dir = Path("/Users/xujian/Athena工作平台/data/evaluation_reflection")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 数据文件
        self.metrics_file = self.data_dir / "metrics.json"
        self.reflections_file = self.data_dir / "reflections.json"
        self.reports_file = self.data_dir / "reports"
        self.reports_file.mkdir(exist_ok=True)

        # 评估指标
        self.metrics = {
            "performance": {
                "response_time": 0,
                "accuracy": 0,
                "success_rate": 0,
                "throughput": 0
            },
            "quality": {
                "completeness": 0,
                "relevance": 0,
                "clarity": 0,
                "professionalism": 0
            },
            "efficiency": {
                "resource_usage": 0,
                "automation_rate": 0,
                "error_rate": 0,
                "escalation_rate": 0
            },
            "satisfaction": {
                "user_satisfaction": 0,
                "nps_score": 0,
                "retention_rate": 0,
                "feedback_quality": 0
            },
            "learning": {
                "knowledge_growth": 0,
                "skill_improvement": 0,
                "adaptation_speed": 0,
                "innovation_rate": 0
            }
        }

        # 历史数据
        self.metrics_history = defaultdict(lambda: deque(maxlen=100))
        self.reflections = []

        # 基准值
        self.benchmarks = {
            "performance": {
                "response_time": 5.0,  # 秒
                "accuracy": 0.9,
                "success_rate": 0.85,
                "throughput": 10  # 任务/小时
            },
            "quality": {
                "completeness": 0.9,
                "relevance": 0.85,
                "clarity": 0.9,
                "professionalism": 0.95
            },
            "efficiency": {
                "resource_usage": 0.7,
                "automation_rate": 0.8,
                "error_rate": 0.05,
                "escalation_rate": 0.1
            },
            "satisfaction": {
                "user_satisfaction": 0.85,
                "nps_score": 50,
                "retention_rate": 0.8,
                "feedback_quality": 0.8
            },
            "learning": {
                "knowledge_growth": 0.1,  # 月增长率
                "skill_improvement": 0.05,
                "adaptation_speed": 3.0,  # 天
                "innovation_rate": 0.1
            }
        }

        # 反思配置
        self.reflection_schedule = {
            ReflectionType.DAILY: {"interval": 1, "enabled": True},
            ReflectionType.WEEKLY: {"interval": 7, "enabled": True},
            ReflectionType.MONTHLY: {"interval": 30, "enabled": True},
            ReflectionType.INCIDENT: {"interval": 0, "enabled": True},
            ReflectionType.STRATEGIC: {"interval": 90, "enabled": True}
        }

        self.initialized = False

    async def initialize(self):
        """初始化引擎"""
        try:
            # 加载历史数据
            await self._load_historical_data()

            # 启动定期评估任务
            asyncio.create_task(self._periodic_evaluation())

            # 启动定期反思任务
            asyncio.create_task(self._periodic_reflection())

            self.initialized = True
            logger.info("✅ 评估反思引擎初始化完成")

        except Exception as e:
            logger.error(f"❌ 评估反思引擎初始化失败: {str(e)}")
            self.initialized = True  # 使用默认配置

    async def evaluate_performance(self, evaluation_type: EvaluationType,
                                  data: dict[str, Any]) -> dict[str, Any]:
        """
        评估性能

        Args:
            evaluation_type: 评估类型
            data: 评估数据
            {
                "task_id": "TASK_001",
                "start_time": "2024-01-01T10:00:00",
                "end_time": "2024-01-01T10:05:00",
                "result": "success|failure|partial",
                "quality_score": 0.9,
                "user_feedback": {...}
            }

        Returns:
            评估结果
        """
        try:
            # 计算指标
            metrics = await self._calculate_metrics(evaluation_type, data)

            # 分析趋势
            trends = await self._analyze_trends(evaluation_type, metrics)

            # 生成洞察
            insights = await self._generate_insights(evaluation_type, metrics, trends)

            # 更新指标历史
            await self._update_metrics_history(evaluation_type, metrics)

            # 检查是否需要触发反思
            await self._check_reflection_triggers(evaluation_type, metrics, trends)

            # 保存评估结果
            evaluation_result = {
                "evaluation_id": f"EVAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "type": evaluation_type.value,
                "metrics": metrics,
                "trends": trends,
                "insights": insights,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }

            await self._save_evaluation_result(evaluation_result)

            return evaluation_result

        except Exception as e:
            logger.error(f"❌ 性能评估失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def reflect(self, reflection_type: ReflectionType,
                      context: dict[str, Any] = None) -> dict[str, Any]:
        """
        执行反思

        Args:
            reflection_type: 反思类型
            context: 反思上下文（可选）

        Returns:
            反思结果
        """
        try:
            # 收集反思数据
            reflection_data = await self._collect_reflection_data(reflection_type, context)

            # 执行深度分析
            analysis = await self._deep_analysis(reflection_data)

            # 生成洞察
            insights = await self._generate_reflection_insights(analysis)

            # 制定行动计划
            action_items = await self._create_action_items(insights)

            # 评估影响
            impact = await self._assess_impact(insights, action_items)

            # 创建反思记录
            reflection = Reflection(
                reflection_id=f"REF_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                type=reflection_type,
                topic=await self._determine_reflection_topic(reflection_type, reflection_data),
                insights=insights,
                action_items=action_items,
                impact_assessment=impact,
                confidence=await self._calculate_reflection_confidence(insights),
                created_at=datetime.now()
            )

            # 保存反思
            self.reflections.append(reflection)
            await self._save_reflections()

            # 执行行动计划（如果需要）
            if reflection_type in [ReflectionType.INCIDENT, ReflectionType.STRATEGIC]:
                await self._execute_action_items(action_items)

            logger.info(f"✅ 反思完成: {reflection.reflection_id}")

            return {
                "success": True,
                "reflection": asdict(reflection),
                "analysis": analysis
            }

        except Exception as e:
            logger.error(f"❌ 反思失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_evaluation_report(self, report_type: str = "comprehensive",
                                   time_range: int = 30) -> dict[str, Any]:
        """
        获取评估报告

        Args:
            report_type: 报告类型
                - "comprehensive": 综合报告
                - "performance": 性能报告
                - "quality": 质量报告
                - "trend": 趋势报告
            time_range: 时间范围（天）

        Returns:
            评估报告
        """
        try:
            # 收集数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=time_range)

            # 生成报告
            if report_type == "comprehensive":
                report = await self._generate_comprehensive_report(start_date, end_date)
            elif report_type == "performance":
                report = await self._generate_performance_report(start_date, end_date)
            elif report_type == "quality":
                report = await self._generate_quality_report(start_date, end_date)
            elif report_type == "trend":
                report = await self._generate_trend_report(start_date, end_date)
            else:
                raise ValueError(f"不支持的报告类型: {report_type}")

            # 保存报告
            report_file = self.reports_file / f"{report_type}_{datetime.now().strftime('%Y%m%d')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)

            return report

        except Exception as e:
            logger.error(f"❌ 生成评估报告失败: {str(e)}")
            return {
                "error": str(e),
                "report": None
            }

    async def _calculate_metrics(self, evaluation_type: EvaluationType,
                                data: dict[str, Any]) -> dict[str, float]:
        """计算指标"""
        metrics = {}

        if evaluation_type == EvaluationType.PERFORMANCE:
            # 响应时间
            start_time = datetime.fromisoformat(data.get("start_time", datetime.now().isoformat()))
            end_time = datetime.fromisoformat(data.get("end_time", datetime.now().isoformat()))
            response_time = (end_time - start_time).total_seconds()
            metrics["response_time"] = response_time

            # 成功率
            metrics["success_rate"] = 1.0 if data.get("result") == "success" else 0.0

            # 准确性
            metrics["accuracy"] = data.get("quality_score", 0.5)

            # 吞吐量
            metrics["throughput"] = 1.0 / max(response_time, 0.1)  # 简化计算

        elif evaluation_type == EvaluationType.QUALITY:
            # 完整性
            metrics["completeness"] = data.get("completeness_score", 0.5)

            # 相关性
            metrics["relevance"] = data.get("relevance_score", 0.5)

            # 清晰度
            metrics["clarity"] = data.get("clarity_score", 0.5)

            # 专业性
            metrics["professionalism"] = data.get("professionalism_score", 0.5)

        elif evaluation_type == EvaluationType.SATISFACTION:
            feedback = data.get("user_feedback", {})
            metrics["user_satisfaction"] = feedback.get("satisfaction_score", 0.5)
            metrics["nps_score"] = feedback.get("nps", 50)
            metrics["retention_rate"] = feedback.get("retention", 0.5)

        return metrics

    async def _analyze_trends(self, evaluation_type: EvaluationType,
                            metrics: dict[str, float]) -> dict[str, str]:
        """分析趋势"""
        trends = {}
        category = evaluation_type.value

        for metric_name, current_value in metrics.items():
            # 获取历史值
            history = self.metrics_history.get(f"{category}_{metric_name}", deque(maxlen=100))
            if len(history) > 0:
                # 计算趋势
                recent_values = list(history)[-5:]  # 最近5个值
                avg_recent = sum(recent_values) / len(recent_values)

                if current_value > avg_recent * 1.1:
                    trend = "improving"
                elif current_value < avg_recent * 0.9:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"

            trends[metric_name] = trend

        return trends

    async def _generate_insights(self, evaluation_type: EvaluationType,
                                metrics: dict[str, float],
                                trends: dict[str, str]) -> list[str]:
        """生成洞察"""
        insights = []
        category = evaluation_type.value
        benchmarks = self.benchmarks.get(category, {})

        for metric_name, value in metrics.items():
            benchmark = benchmarks.get(metric_name, 0)
            trend = trends.get(metric_name, "stable")

            # 与基准比较
            if value < benchmark * 0.8:
                insights.append(f"{metric_name} 低于基准值 {benchmark:.2f}，需要改进")
            elif value > benchmark * 1.2:
                insights.append(f"{metric_name} 表现优秀，超出基准值 {benchmark:.2f}")

            # 趋势分析
            if trend == "declining":
                insights.append(f"{metric_name} 呈下降趋势，需要关注")
            elif trend == "improving":
                insights.append(f"{metric_name} 持续改善，继续保持")

        return insights

    async def _update_metrics_history(self, evaluation_type: EvaluationType,
                                    metrics: dict[str, float]):
        """更新指标历史"""
        category = evaluation_type.value
        timestamp = datetime.now()

        for metric_name, value in metrics.items():
            key = f"{category}_{metric_name}"
            self.metrics_history[key].append({
                "value": value,
                "timestamp": timestamp
            })

    async def _check_reflection_triggers(self, evaluation_type: EvaluationType,
                                       metrics: dict[str, float],
                                       trends: dict[str, str]):
        """检查反思触发条件"""
        # 如果有关键指标下降，触发事件反思
        for metric_name, trend in trends.items():
            if trend == "declining":
                asyncio.create_task(
                    self.reflect(ReflectionType.INCIDENT, {
                        "trigger_metric": metric_name,
                        "evaluation_type": evaluation_type.value,
                        "metrics": metrics
                    })
                )
                break

    async def _collect_reflection_data(self, reflection_type: ReflectionType,
                                     context: dict[str, Any] = None) -> dict[str, Any]:
        """收集反思数据"""
        data = {
            "type": reflection_type.value,
            "timestamp": datetime.now().isoformat(),
            "metrics": dict(self.metrics),
            "reflections": [asdict(r) for r in self.reflections[-10:]]  # 最近10条反思
        }

        if context:
            data.update(context)

        return data

    async def _deep_analysis(self, data: dict[str, Any]) -> dict[str, Any]:
        """深度分析"""
        analysis = {
            "patterns": await self._identify_patterns(data),
            "correlations": await self._find_correlations(data),
            "anomalies": await self._detect_anomalies(data),
            "opportunities": await self._identify_opportunities(data),
            "risks": await self._assess_risks(data)
        }
        return analysis

    async def _identify_patterns(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """识别模式"""
        patterns = []
        # 简化实现，返回空列表
        return patterns

    async def _find_correlations(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """发现关联"""
        correlations = []
        # 简化实现，返回空列表
        return correlations

    async def _detect_anomalies(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """检测异常"""
        anomalies = []
        # 简化实现，返回空列表
        return anomalies

    async def _identify_opportunities(self, data: dict[str, Any]) -> list[str]:
        """识别机会"""
        opportunities = []

        # 基于指标识别改进机会
        for category, metrics in self.metrics.items():
            for metric, value in metrics.items():
                benchmark = self.benchmarks.get(category, {}).get(metric, 0)
                if value < benchmark:
                    opportunities.append(f"改进 {category}.{metric}")

        return opportunities

    async def _assess_risks(self, data: dict[str, Any]) -> list[str]:
        """评估风险"""
        risks = []

        # 检查关键风险指标
        if self.metrics["performance"]["success_rate"] < 0.7:
            risks.append("成功率过低，可能影响用户信任")

        if self.metrics["satisfaction"]["user_satisfaction"] < 0.6:
            risks.append("用户满意度低，存在流失风险")

        return risks

    async def _generate_reflection_insights(self, analysis: dict[str, Any]) -> list[str]:
        """生成反思洞察"""
        insights = []

        # 基于模式生成洞察
        patterns = analysis.get("patterns", [])
        if patterns:
            insights.append("识别到重复模式，值得深入研究")

        # 基于机会生成洞察
        opportunities = analysis.get("opportunities", [])
        if opportunities:
            insights.append(f"发现 {len(opportunities)} 个改进机会")

        # 基于风险生成洞察
        risks = analysis.get("risks", [])
        if risks:
            insights.append(f"识别到 {len(risks)} 个潜在风险")

        return insights

    async def _create_action_items(self, insights: list[str]) -> list[dict[str, Any]]:
        """创建行动项"""
        action_items = []

        for insight in insights:
            if "改进机会" in insight:
                action_items.append({
                    "action": "优化相关流程",
                    "priority": "medium",
                    "owner": "system",
                    "deadline": (datetime.now() + timedelta(days=7)).isoformat()
                })
            elif "风险" in insight:
                action_items.append({
                    "action": "制定风险缓解计划",
                    "priority": "high",
                    "owner": "system",
                    "deadline": (datetime.now() + timedelta(days=3)).isoformat()
                })

        return action_items

    async def _assess_impact(self, insights: list[str],
                           action_items: list[dict[str, Any]]) -> str:
        """评估影响"""
        high_priority_count = sum(1 for item in action_items if item.get("priority") == "high")

        if high_priority_count > 3:
            return "重大影响，需要立即行动"
        elif high_priority_count > 0:
            return "中等影响，需要计划性处理"
        else:
            return "轻微影响，可持续改进"

    async def _calculate_reflection_confidence(self, insights: list[str]) -> float:
        """计算反思置信度"""
        # 基于洞察数量和质量计算置信度
        if not insights:
            return 0.5

        # 简化实现
        return min(0.95, 0.6 + len(insights) * 0.1)

    async def _determine_reflection_topic(self, reflection_type: ReflectionType,
                                        data: dict[str, Any]) -> str:
        """确定反思主题"""
        if reflection_type == ReflectionType.DAILY:
            return "日常运营反思"
        elif reflection_type == ReflectionType.WEEKLY:
            return "周度绩效反思"
        elif reflection_type == ReflectionType.MONTHLY:
            return "月度发展反思"
        elif reflection_type == ReflectionType.INCIDENT:
            return "事件响应反思"
        else:
            return "战略规划反思"

    async def _execute_action_items(self, action_items: list[dict[str, Any]]):
        """执行行动项"""
        for item in action_items:
            # 这里应该实际执行行动
            logger.info(f"执行行动项: {item['action']}")

    async def _generate_comprehensive_report(self, start_date: datetime,
                                           end_date: datetime) -> dict[str, Any]:
        """生成综合报告"""
        report = {
            "report_type": "comprehensive",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": await self._generate_summary(),
            "performance": await self._generate_performance_section(),
            "quality": await self._generate_quality_section(),
            "trends": await self._generate_trends_section(),
            "recommendations": await self._generate_recommendations()
        }
        return report

    async def _generate_summary(self) -> dict[str, Any]:
        """生成摘要"""
        return {
            "overall_health": "good",  # good/fair/poor
            "key_achievements": ["服务质量提升", "响应时间改善"],
            "main_challenges": ["知识覆盖面需扩大", "某些场景准确性待提高"],
            "next_focus": ["优化推理算法", "扩大案例库"]
        }

    async def _generate_performance_section(self) -> dict[str, Any]:
        """生成性能部分"""
        return {
            "metrics": self.metrics["performance"],
            "benchmarks": self.benchmarks["performance"],
            "trends": {
                "response_time": "improving",
                "accuracy": "stable",
                "success_rate": "improving"
            }
        }

    async def _generate_quality_section(self) -> dict[str, Any]:
        """生成质量部分"""
        return {
            "metrics": self.metrics["quality"],
            "benchmarks": self.benchmarks["quality"],
            "quality_distribution": {
                "excellent": 0.3,
                "good": 0.5,
                "fair": 0.15,
                "poor": 0.05
            }
        }

    async def _generate_trends_section(self) -> dict[str, Any]:
        """生成趋势部分"""
        return {
            "improving_metrics": ["success_rate", "user_satisfaction"],
            "stable_metrics": ["accuracy", "completeness"],
            "declining_metrics": [],
            "trend_analysis": "整体呈积极发展趋势"
        }

    async def _generate_recommendations(self) -> list[str]:
        """生成建议"""
        return [
            "继续优化响应速度，目标控制在3秒内",
            "加强专业知识库建设，提高准确性",
            "收集更多用户反馈，持续改进体验",
            "探索AI模型的更新升级方案"
        ]

    async def _load_historical_data(self):
        """加载历史数据"""
        try:
            # 加载指标历史
            if self.metrics_file.exists():
                with open(self.metrics_file, encoding='utf-8') as f:
                    data = json.load(f)
                    self.metrics = data.get("metrics", self.metrics)

                    # 加载历史记录
                    for key, values in data.get("history", {}).items():
                        for value in values:
                            self.metrics_history[key].append(value)

            # 加载反思记录
            if self.reflections_file.exists():
                with open(self.reflections_file, encoding='utf-8') as f:
                    reflections_data = json.load(f)
                    for ref_data in reflections_data:
                        reflection = Reflection(**ref_data)
                        self.reflections.append(reflection)

            logger.info("✅ 历史数据加载完成")

        except Exception as e:
            logger.warning(f"加载历史数据失败: {str(e)}")

    async def _save_evaluation_result(self, result: dict[str, Any]):
        """保存评估结果"""
        # 简化实现，可以保存到数据库或文件
        pass

    async def _save_reflections(self):
        """保存反思记录"""
        try:
            reflections_data = [asdict(ref) for ref in self.reflections]
            with open(self.reflections_file, 'w', encoding='utf-8') as f:
                json.dump(reflections_data, f, ensure_ascii=False, indent=2, default=str)

            # 保存指标和历史
            save_data = {
                "metrics": self.metrics,
                "history": {key: list(value) for key, value in self.metrics_history.items()},
                "last_updated": datetime.now().isoformat()
            }
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)

        except Exception as e:
            logger.error(f"保存反思记录失败: {str(e)}")

    async def _periodic_evaluation(self):
        """定期评估任务"""
        while True:
            try:
                # 每小时执行一次性能评估
                await asyncio.sleep(3600)

                # 模拟评估数据
                eval_data = {
                    "task_id": f"PERIODIC_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "start_time": (datetime.now() - timedelta(minutes=2)).isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "result": "success",
                    "quality_score": 0.85
                }

                await self.evaluate_performance(EvaluationType.PERFORMANCE, eval_data)

            except Exception as e:
                logger.error(f"定期评估失败: {str(e)}")

    async def _periodic_reflection(self):
        """定期反思任务"""
        while True:
            try:
                # 每天执行一次日常反思
                await asyncio.sleep(86400)  # 24小时
                await self.reflect(ReflectionType.DAILY)

            except Exception as e:
                logger.error(f"定期反思失败: {str(e)}")

    async def _generate_performance_report(self, start_date: datetime,
                                         end_date: datetime) -> dict[str, Any]:
        """生成性能报告"""
        # 返回性能相关的数据
        return {
            "report_type": "performance",
            "metrics": self.metrics["performance"],
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }

    async def _generate_quality_report(self, start_date: datetime,
                                     end_date: datetime) -> dict[str, Any]:
        """生成质量报告"""
        return {
            "report_type": "quality",
            "metrics": self.metrics["quality"],
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }

    async def _generate_trend_report(self, start_date: datetime,
                                   end_date: datetime) -> dict[str, Any]:
        """生成趋势报告"""
        trends = {}
        for category in self.metrics:
            trends[category] = {}
            for metric in self.metrics[category]:
                history_key = f"{category}_{metric}"
                if history_key in self.metrics_history:
                    values = list(self.metrics_history[history_key])
                    if len(values) > 1:
                        # 简单的趋势计算
                        if values[-1]["value"] > values[-2]["value"]:
                            trend = "up"
                        elif values[-1]["value"] < values[-2]["value"]:
                            trend = "down"
                        else:
                            trend = "stable"
                        trends[category][metric] = trend

        return {
            "report_type": "trend",
            "trends": trends,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }

# 使用示例
async def main():
    """测试评估反思引擎"""
    engine = EvaluationReflectionEngine()
    await engine.initialize()

    # 执行性能评估
    result = await engine.evaluate_performance(
        EvaluationType.PERFORMANCE,
        {
            "task_id": "TASK_001",
            "start_time": "2024-12-15T10:00:00",
            "end_time": "2024-12-15T10:03:00",
            "result": "success",
            "quality_score": 0.88
        }
    )
    print(f"评估结果: {result}")

    # 执行反思
    reflection = await engine.reflect(ReflectionType.DAILY)
    print(f"反思结果: {reflection}")

    # 获取综合报告
    await engine.get_evaluation_report("comprehensive", 7)
    print("综合报告已生成")

# 入口点: @async_main装饰器已添加到main函数
