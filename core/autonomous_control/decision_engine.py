from __future__ import annotations
"""
Athena自主决策引擎
基于论文中的LLM Agent方法论实现智能决策
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class DecisionType(Enum):
    """决策类型"""

    PLATFORM_CONTROL = "platform_control"  # 平台控制决策
    SERVICE_MANAGEMENT = "service_management"  # 服务管理决策
    TASK_PLANNING = "task_planning"  # 任务规划决策
    ERROR_RECOVERY = "error_recovery"  # 错误恢复决策
    OPTIMIZATION = "optimization"  # 性能优化决策
    SECURITY = "security"  # 安全决策


class Priority(Enum):
    """优先级"""

    CRITICAL = 5  # 关键决策,立即执行
    HIGH = 4  # 高优先级
    MEDIUM = 3  # 中等优先级
    LOW = 2  # 低优先级
    INFO = 1  # 信息性决策


@dataclass
class DecisionContext:
    """决策上下文"""

    platform_status: dict[str, Any] = field(default_factory=dict)
    system_metrics: dict[str, float] = field(default_factory=dict)
    user_intent: str = ""
    history: list[dict[str, Any]] = field(default_factory=list)
    current_time: datetime = field(default_factory=datetime.now)
    agent_emotions: dict[str, float] = field(default_factory=dict)


@dataclass
class DecisionOption:
    """决策选项"""

    action: str
    description: str
    confidence: float
    priority: Priority
    estimated_time: float
    resource_cost: float
    risk_level: float
    expected_outcome: dict[str, Any]
class DecisionEngine:
    """Athena自主决策引擎"""

    def __init__(self):
        self.decision_history = []
        self.action_patterns = self._load_action_patterns()
        self.optimization_goals = self._load_optimization_goals()
        self.learning_rate = 0.1

    def _load_action_patterns(self) -> dict[str, list[dict[str, Any]]]:
        """加载行动模式(基于论文中的最佳实践)"""
        return {
            "service_failure": [
                {
                    "pattern": "restart_service",
                    "weight": 0.8,
                    "conditions": ["status_error", "not_critical"],
                    "actions": ["stop_service", "wait_2s", "start_service"],
                },
                {
                    "pattern": "scale_resources",
                    "weight": 0.6,
                    "conditions": ["high_load", "available_resources"],
                    "actions": ["scale_up", "monitor", "adjust_limits"],
                },
                {
                    "pattern": "graceful_degradation",
                    "weight": 0.7,
                    "conditions": ["system_overload", "maintain_core"],
                    "actions": ["stop_nonessential", "reduce_load", "notify_users"],
                },
            ],
            "performance_optimization": [
                {
                    "pattern": "cache_optimization",
                    "weight": 0.75,
                    "conditions": ["low_cache_hit", "available_memory"],
                    "actions": ["increase_cache", "optimize_strategy", "monitor_hit_rate"],
                },
                {
                    "pattern": "load_balancing",
                    "weight": 0.8,
                    "conditions": ["uneven_load", "multiple_instances"],
                    "actions": ["redistribute", "add_instances", "update_routes"],
                },
            ],
            "security_threat": [
                {
                    "pattern": "isolate_threat",
                    "weight": 0.95,
                    "conditions": ["suspicious_activity", "potential_breach"],
                    "actions": ["isolate_service", "audit_logs", "notify_admin"],
                },
                {
                    "pattern": "enhance_security",
                    "weight": 0.85,
                    "conditions": ["vulnerability_detected", "security_patch"],
                    "actions": ["apply_patch", "update_config", "scan_again"],
                },
            ],
        }

    def _load_optimization_goals(self) -> dict[str, dict[str, float]]:
        """加载优化目标"""
        return {
            "performance": {"response_time": 0.4, "throughput": 0.3, "resource_efficiency": 0.3},
            "reliability": {"uptime": 0.5, "error_rate": 0.3, "recovery_time": 0.2},
            "security": {
                "threat_detection": 0.4,
                "vulnerability_patch": 0.3,
                "access_control": 0.3,
            },
            "cost_efficiency": {
                "resource_usage": 0.4,
                "operational_cost": 0.3,
                "energy_efficiency": 0.3,
            },
        }

    async def make_decision(
        self,
        context: DecisionContext,
        decision_type: DecisionType,
        options: Optional[list[str]] = None,
    ) -> tuple[DecisionOption, float]:
        """
        基于上下文和类型进行决策
        返回:(最佳决策选项, 置信度)
        """
        try:
            # 1. 分析当前情况
            situation_analysis = await self._analyze_situation(context)

            # 2. 生成决策选项
            decision_options = await self._generate_options(
                context, decision_type, situation_analysis, options
            )

            # 3. 评估选项
            evaluated_options = await self._evaluate_options(
                decision_options, context, situation_analysis
            )

            # 4. 选择最佳选项
            best_option = await self._select_best_option(evaluated_options)

            # 5. 计算决策置信度
            confidence = await self._calculate_confidence(best_option, context)

            # 6. 记录决策
            self._record_decision(best_option, context, confidence)

            return best_option, confidence

        except Exception as e:
            logger.error(f"决策制定失败: {e}")
            # 返回默认安全决策
            fallback_option = DecisionOption(
                action="maintain_status",
                description="维持当前状态,等待人工干预",
                confidence=0.5,
                priority=Priority.MEDIUM,
                estimated_time=0,
                resource_cost=0,
                risk_level=0.1,
                expected_outcome={"status": "unchanged"},
            )
            return fallback_option, 0.5

    async def _analyze_situation(self, context: DecisionContext) -> dict[str, Any]:
        """分析当前情况"""
        analysis = {
            "platform_health": "unknown",
            "critical_issues": [],
            "opportunities": [],
            "risks": [],
            "resource_state": "unknown",
        }

        try:
            # 分析平台健康状态
            platform_status = context.platform_status
            if isinstance(platform_status, dict):
                error_count = platform_status.get("service_status_counts", {}).get("error", 0)
                total_services = platform_status.get("total_services", 0)

                if error_count == 0:
                    analysis["platform_health"] = "healthy"
                elif error_count < total_services * 0.2:
                    analysis["platform_health"] = "degraded"
                else:
                    analysis["platform_health"] = "critical"

                # 识别关键问题
                for service_name, service_info in platform_status.get("services", {}).items():
                    if service_info.get("status") == "error":
                        analysis["critical_issues"].append(f"{service_name}服务异常")
                    if service_info.get("cpu_usage", 0) > 80:
                        analysis["critical_issues"].append(f"{service_name}CPU使用率过高")
                    if service_info.get("memory_usage", 0) > 85:
                        analysis["critical_issues"].append(f"{service_name}内存使用率过高")

            # 分析系统指标
            if context.system_metrics:
                if context.system_metrics.get("cpu_percent", 0) > 90:
                    analysis["critical_issues"].append("系统CPU负载过高")
                if context.system_metrics.get("memory_percent", 0) > 90:
                    analysis["critical_issues"].append("系统内存不足")
                if context.system_metrics.get("disk_usage", 0) > 85:
                    analysis["risks"].append("磁盘空间不足")

            # 识别优化机会
            if analysis["platform_health"] == "healthy":
                analysis["opportunities"].append("系统运行良好,可以进行性能优化")
                if context.system_metrics.get("memory_percent", 0) < 50:
                    analysis["opportunities"].append("内存资源充足,可以增加缓存")

        except Exception as e:
            logger.warning(f"情况分析失败: {e}")

        return analysis

    async def _generate_options(
        self,
        context: DecisionContext,
        decision_type: DecisionType,
        situation_analysis: dict[str, Any],        suggested_options: Optional[list[str]] = None,
    ) -> list[DecisionOption]:
        """生成决策选项"""
        options = []

        try:
            # 基于决策类型生成选项
            if decision_type == DecisionType.PLATFORM_CONTROL:
                options.extend(await self._generate_platform_control_options(situation_analysis))

            elif decision_type == DecisionType.SERVICE_MANAGEMENT:
                options.extend(await self._generate_service_management_options(situation_analysis))

            elif decision_type == DecisionType.ERROR_RECOVERY:
                options.extend(await self._generate_error_recovery_options(situation_analysis))

            elif decision_type == DecisionType.OPTIMIZATION:
                options.extend(await self._generate_optimization_options(situation_analysis))

            # 添加用户建议的选项
            if suggested_options:
                for opt in suggested_options:
                    options.append(
                        DecisionOption(
                            action=opt,
                            description=f"用户建议: {opt}",
                            confidence=0.7,
                            priority=Priority.MEDIUM,
                            estimated_time=5.0,
                            resource_cost=1.0,
                            risk_level=0.3,
                            expected_outcome={"user_satisfaction": "high"},
                        )
                    )

        except Exception as e:
            logger.warning(f"生成决策选项失败: {e}")

        return options

    async def _generate_platform_control_options(
        self, situation_analysis: dict[str, Any]
    ) -> list[DecisionOption]:
        """生成平台控制选项"""
        options = []

        # 基于情况生成控制选项
        if situation_analysis.get("platform_health") == "critical":
            options.append(
                DecisionOption(
                    action="emergency_restart",
                    description="紧急重启平台",
                    confidence=0.8,
                    priority=Priority.CRITICAL,
                    estimated_time=30.0,
                    resource_cost=10.0,
                    risk_level=0.6,
                    expected_outcome={"platform_recovery": True},
                )
            )
            options.append(
                DecisionOption(
                    action="selective_restart",
                    description="选择性重启关键服务",
                    confidence=0.7,
                    priority=Priority.HIGH,
                    estimated_time=15.0,
                    resource_cost=5.0,
                    risk_level=0.4,
                    expected_outcome={"partial_recovery": True},
                )
            )

        elif situation_analysis.get("platform_health") == "degraded":
            options.append(
                DecisionOption(
                    action="restart_failed_services",
                    description="重启失败的服务",
                    confidence=0.9,
                    priority=Priority.HIGH,
                    estimated_time=10.0,
                    resource_cost=3.0,
                    risk_level=0.2,
                    expected_outcome={"service_recovery": True},
                )
            )

        return options

    async def _generate_service_management_options(
        self, situation_analysis: dict[str, Any]
    ) -> list[DecisionOption]:
        """生成服务管理选项"""
        options = []

        # 基于关键问题生成选项
        for issue in situation_analysis.get("critical_issues", []):
            if "CPU使用率过高" in issue:
                options.append(
                    DecisionOption(
                        action="scale_up_service",
                        description="扩容高负载服务",
                        confidence=0.8,
                        priority=Priority.HIGH,
                        estimated_time=5.0,
                        resource_cost=3.0,
                        risk_level=0.2,
                        expected_outcome={"load_reduction": True},
                    )
                )

            elif "内存使用率过高" in issue:
                options.append(
                    DecisionOption(
                        action="optimize_memory",
                        description="优化服务内存使用",
                        confidence=0.7,
                        priority=Priority.MEDIUM,
                        estimated_time=10.0,
                        resource_cost=2.0,
                        risk_level=0.3,
                        expected_outcome={"memory_optimization": True},
                    )
                )

            elif "服务异常" in issue:
                options.append(
                    DecisionOption(
                        action="restart_service",
                        description="重启异常服务",
                        confidence=0.9,
                        priority=Priority.HIGH,
                        estimated_time=5.0,
                        resource_cost=1.0,
                        risk_level=0.2,
                        expected_outcome={"service_recovery": True},
                    )
                )

        return options

    async def _generate_error_recovery_options(
        self, situation_analysis: dict[str, Any]
    ) -> list[DecisionOption]:
        """生成错误恢复选项"""
        options = []

        options.append(
            DecisionOption(
                action="diagnose_root_cause",
                description="诊断根本原因",
                confidence=0.8,
                priority=Priority.HIGH,
                estimated_time=15.0,
                resource_cost=2.0,
                risk_level=0.1,
                expected_outcome={"root_cause_identified": True},
            )
        )

        options.append(
            DecisionOption(
                action="apply_fix",
                description="应用修复方案",
                confidence=0.7,
                priority=Priority.MEDIUM,
                estimated_time=10.0,
                resource_cost=3.0,
                risk_level=0.3,
                expected_outcome={"issue_resolved": True},
            )
        )

        return options

    async def _generate_optimization_options(
        self, situation_analysis: dict[str, Any]
    ) -> list[DecisionOption]:
        """生成优化选项"""
        options = []

        for opportunity in situation_analysis.get("opportunities", []):
            if "性能优化" in opportunity:
                options.append(
                    DecisionOption(
                        action="tune_performance",
                        description="性能调优",
                        confidence=0.75,
                        priority=Priority.MEDIUM,
                        estimated_time=20.0,
                        resource_cost=2.0,
                        risk_level=0.2,
                        expected_outcome={"performance_improvement": 0.2},
                    )
                )

            if "缓存" in opportunity:
                options.append(
                    DecisionOption(
                        action="optimize_cache",
                        description="优化缓存策略",
                        confidence=0.8,
                        priority=Priority.MEDIUM,
                        estimated_time=10.0,
                        resource_cost=1.0,
                        risk_level=0.1,
                        expected_outcome={"cache_hit_rate_improvement": 0.15},
                    )
                )

        return options

    async def _evaluate_options(
        self,
        options: list[DecisionOption],
        context: DecisionContext,
        situation_analysis: dict[str, Any],    ) -> list[DecisionOption]:
        """评估决策选项"""
        evaluated_options = []

        for option in options:
            try:
                # 计算综合得分
                score = await self._calculate_option_score(option, context, situation_analysis)

                # 更新选项的置信度
                option.confidence = min(option.confidence * score, 1.0)
                evaluated_options.append(option)

            except Exception as e:
                logger.warning(f"评估选项 {option.action} 失败: {e}")
                option.confidence *= 0.5  # 降低置信度
                evaluated_options.append(option)

        return evaluated_options

    async def _calculate_option_score(
        self, option: DecisionOption, context: DecisionContext, situation_analysis: dict[str, Any]
    ) -> float:
        """计算选项得分"""
        try:
            score = 0.0

            # 优先级权重
            priority_weight = option.priority.value / 5.0
            score += priority_weight * 0.3

            # 风险评估
            risk_penalty = option.risk_level * 0.2
            score -= risk_penalty

            # 成本效益
            if option.resource_cost > 0:
                cost_efficiency = min(1.0 / option.resource_cost, 1.0)
                score += cost_efficiency * 0.2

            # 历史成功率
            historical_success = await self._get_historical_success_rate(option.action)
            score += historical_success * 0.3

            # 上下文适配度
            context_fit = await self._calculate_context_fit(option, context, situation_analysis)
            score += context_fit * 0.2

            return max(0.0, min(1.0, score))

        except Exception as e:
            logger.warning(f"计算选项得分失败: {e}")
            return 0.5

    async def _get_historical_success_rate(self, action: str) -> float:
        """获取历史成功率"""
        try:
            similar_decisions = [
                d
                for d in self.decision_history
                if d.get("action") == action and d.get("success", False)
            ]

            if not similar_decisions:
                return 0.7  # 默认成功率

            success_count = len([d for d in similar_decisions if d.get("success")])
            return success_count / len(similar_decisions)

        except Exception:
            return 0.7

    async def _calculate_context_fit(
        self, option: DecisionOption, context: DecisionContext, situation_analysis: dict[str, Any]
    ) -> float:
        """计算上下文适配度"""
        try:
            fit_score = 0.0

            # 情感适配度
            if context.agent_emotions:
                emotion_factor = 0.0
                for emotion, value in context.agent_emotions.items():
                    if (emotion == "confidence" and value > 0.7) or (emotion == "responsibility" and value > 0.8):
                        emotion_factor += 0.3

                fit_score += min(emotion_factor, 0.4)

            # 情况适配度
            if situation_analysis.get("platform_health") == "critical":
                if option.priority in [Priority.CRITICAL, Priority.HIGH]:
                    fit_score += 0.4
                elif option.priority in [Priority.LOW, Priority.INFO]:
                    fit_score -= 0.3

            # 用户意图适配度
            if context.user_intent and any(
                keyword in option.description.lower() for keyword in ["紧急", "关键", "重要"]
            ):
                fit_score += 0.2

            return max(0.0, min(1.0, fit_score))

        except Exception:
            return 0.5

    async def _select_best_option(self, evaluated_options: list[DecisionOption]) -> DecisionOption:
        """选择最佳选项"""
        if not evaluated_options:
            # 返回默认选项
            return DecisionOption(
                action="no_action",
                description="无操作",
                confidence=0.1,
                priority=Priority.LOW,
                estimated_time=0,
                resource_cost=0,
                risk_level=0,
                expected_outcome={},
            )

        # 按优先级和置信度排序
        sorted_options = sorted(
            evaluated_options, key=lambda x: (x.priority.value, x.confidence), reverse=True
        )

        return sorted_options[0]

    async def _calculate_confidence(
        self, option: DecisionOption, context: DecisionContext
    ) -> float:
        """计算决策置信度"""
        try:
            base_confidence = option.confidence

            # 基于上下文调整置信度
            context_boost = 0.0

            # 平台状态影响
            platform_status = context.platform_status
            if isinstance(platform_status, dict):
                if platform_status.get("platform_status") == "healthy":
                    context_boost += 0.1
                elif platform_status.get("platform_status") == "critical":
                    context_boost -= 0.1

            # 情感状态影响
            if context.agent_emotions.get("confidence", 0) > 0.8:
                context_boost += 0.1
            elif context.agent_emotions.get("uncertainty", 0) > 0.7:
                context_boost -= 0.1

            # 历史成功经验
            historical_boost = await self._get_historical_success_rate(option.action) - 0.7
            context_boost += historical_boost

            return max(0.0, min(1.0, base_confidence + context_boost))

        except Exception:
            return option.confidence

    def _record_decision(
        self, option: DecisionOption, context: DecisionContext, confidence: float
    ) -> Any:
        """记录决策"""
        try:
            decision_record = {
                "timestamp": datetime.now().isoformat(),
                "action": option.action,
                "description": option.description,
                "confidence": confidence,
                "priority": option.priority.name,
                "context": {
                    "platform_health": context.platform_status.get("platform_status", "unknown"),
                    "critical_issues": len(
                        context.platform_status.get("service_status_counts", {}).get("error", 0)
                    ),
                    "user_intent": context.user_intent,
                },
                "expected_outcome": option.expected_outcome,
                "success": None,  # 将在执行后更新
            }

            self.decision_history.append(decision_record)

            # 保持历史记录在合理范围内
            if len(self.decision_history) > 1000:
                self.decision_history = self.decision_history[-500:]

        except Exception as e:
            logger.warning(f"记录决策失败: {e}")

    def update_decision_success(
        self, action: str, success: bool, actual_outcome: Optional[dict[str, Any]] = None
    ) -> None:
        """更新决策成功状态"""
        try:
            for record in reversed(self.decision_history):
                if record["action"] == action and record["success"] is None:
                    record["success"] = success
                    if actual_outcome:
                        record["actual_outcome"] = actual_outcome
                    break

        except Exception as e:
            logger.warning(f"更新决策成功状态失败: {e}")

    def get_decision_stats(self) -> dict[str, Any]:
        """获取决策统计信息"""
        try:
            if not self.decision_history:
                return {"total_decisions": 0}

            total_decisions = len(self.decision_history)
            successful_decisions = len([d for d in self.decision_history if d.get("success")])
            success_rate = successful_decisions / total_decisions if total_decisions > 0 else 0

            # 按决策类型统计
            decision_types = {}
            for record in self.decision_history:
                action = record.get("action", "unknown")
                decision_types[action] = decision_types.get(action, 0) + 1

            # 平均置信度
            avg_confidence = (
                sum(d.get("confidence", 0) for d in self.decision_history) / total_decisions
            )

            return {
                "total_decisions": total_decisions,
                "successful_decisions": successful_decisions,
                "success_rate": round(success_rate, 3),
                "average_confidence": round(avg_confidence, 3),
                "decision_types": decision_types,
                "last_decision_time": (
                    self.decision_history[-1]["timestamp"] if self.decision_history else None
                ),
            }

        except Exception as e:
            logger.error(f"获取决策统计失败: {e}")
            return {"error": str(e)}


# 全局决策引擎实例
decision_engine = DecisionEngine()
