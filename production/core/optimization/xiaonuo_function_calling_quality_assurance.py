#!/usr/bin/env python3
from __future__ import annotations
"""
小诺·双鱼公主Function Calling质量保障系统
Xiaonuo·Pisces Princess Function Calling Quality Assurance System

全方位的质量保障机制,确保工具调用的可靠性、性能和安全性

作者: 小诺·双鱼公主
创建时间: 2025-12-18
版本: v1.0.0 "质量守护"
"""

import asyncio
import json
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any

from core.logging_config import setup_logging

if TYPE_CHECKING:
    from collections.abc import Callable

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class ValidationLevel(Enum):
    """验证级别"""

    BASIC = "basic"  # 基础验证
    STANDARD = "standard"  # 标准验证
    COMPREHENSIVE = "comprehensive"  # 全面验证
    STRICT = "strict"  # 严格验证


class QualityLevel(Enum):
    """质量等级"""

    EXCELLENT = "excellent"  # 优秀 (95-100)
    GOOD = "good"  # 良好 (85-94)
    ACCEPTABLE = "acceptable"  # 可接受 (70-84)
    POOR = "poor"  # 较差 (50-69)
    UNACCEPTABLE = "unacceptable"  # 不可接受 (<50)


class RiskLevel(Enum):
    """风险等级"""

    LOW = "low"  # 低风险
    MEDIUM = "medium"  # 中等风险
    HIGH = "high"  # 高风险
    CRITICAL = "critical"  # 严重风险


@dataclass
class ValidationRule:
    """验证规则"""

    name: str
    description: str
    level: ValidationLevel
    validator: Callable
    is_required: bool = True
    error_message: str = ""


@dataclass
class QualityMetric:
    """质量指标"""

    name: str
    value: float
    unit: str
    threshold_min: float | None = None
    threshold_max: float | None = None
    quality_level: QualityLevel = QualityLevel.ACCEPTABLE


@dataclass
class RiskAssessment:
    """风险评估"""

    risk_level: RiskLevel
    risk_score: float
    identified_risks: list[str]
    mitigation_strategies: list[str]
    confidence: float


@dataclass
class QualityReport:
    """质量报告"""

    call_id: str
    tool_name: str
    timestamp: datetime
    validation_level: ValidationLevel
    validation_results: dict[str, bool]
    quality_metrics: list[QualityMetric]
    overall_quality_score: float
    overall_quality_level: QualityLevel
    risk_assessment: RiskAssessment
    recommendations: list[str]
    execution_time: float = 0.0


class XiaonuoFunctionCallingQualityAssurance:
    """小诺Function Calling质量保障系统"""

    def __init__(self):
        self.name = "小诺·双鱼公主Function Calling质量保障系统"
        self.version = "v1.0.0"

        # 验证规则注册表
        self.validation_rules: dict[str, ValidationRule] = {}

        # 质量历史
        self.quality_history: list[QualityReport] = []

        # 基准指标
        self.quality_benchmarks: dict[str, dict[str, float]] = {
            "response_time": {"excellent": 1.0, "good": 2.0, "acceptable": 5.0},
            "success_rate": {"excellent": 0.95, "good": 0.85, "acceptable": 0.70},
            "error_rate": {"excellent": 0.01, "good": 0.05, "acceptable": 0.10},
            "resource_usage": {"excellent": 0.5, "good": 0.7, "acceptable": 0.9},
        }

        # 安全配置
        self.security_config = {
            "max_parameter_size": 1024 * 1024,  # 1MB
            "allowed_domains": [],  # 允许的外部域名
            "blocked_patterns": [r"rm\s+-rf", r"sudo\s+", r"eval\s*\(", r"exec\s*\("],
            "timeout_limits": {"default": 30.0, "critical": 10.0, "long_running": 300.0},
        }

        # 初始化验证规则
        self._init_validation_rules()

        logger.info(f"🛡️ {self.name} v{self.version} 初始化完成")

    def _init_validation_rules(self) -> Any:
        """初始化验证规则"""
        # 参数验证规则
        self.register_validation_rule(
            ValidationRule(
                name="parameter_structure",
                description="验证参数结构完整性",
                level=ValidationLevel.BASIC,
                validator=self._validate_parameter_structure,
            )
        )

        self.register_validation_rule(
            ValidationRule(
                name="parameter_types",
                description="验证参数类型正确性",
                level=ValidationLevel.STANDARD,
                validator=self._validate_parameter_types,
            )
        )

        self.register_validation_rule(
            ValidationRule(
                name="parameter_values",
                description="验证参数值有效性",
                level=ValidationLevel.STANDARD,
                validator=self._validate_parameter_values,
            )
        )

        self.register_validation_rule(
            ValidationRule(
                name="security_check",
                description="安全性检查",
                level=ValidationLevel.COMPREHENSIVE,
                validator=self._validate_security,
                is_required=True,
            )
        )

        self.register_validation_rule(
            ValidationRule(
                name="resource_limits",
                description="资源使用限制检查",
                level=ValidationLevel.STANDARD,
                validator=self._validate_resource_limits,
            )
        )

        self.register_validation_rule(
            ValidationRule(
                name="dependency_check",
                description="依赖关系检查",
                level=ValidationLevel.COMPREHENSIVE,
                validator=self._validate_dependencies,
            )
        )

        logger.info(f"✅ 已注册 {len(self.validation_rules)} 个验证规则")

    def register_validation_rule(self, rule: ValidationRule) -> Any:
        """注册验证规则"""
        self.validation_rules[rule.name] = rule

    async def validate_function_call(
        self,
        tool_name: str,
        function: Callable,
        parameters: dict[str, Any],        validation_level: ValidationLevel = ValidationLevel.STANDARD,
        context: dict[str, Any] | None = None,
    ) -> QualityReport:
        """
        验证函数调用质量

        Args:
            tool_name: 工具名称
            function: 函数对象
            parameters: 参数字典
            validation_level: 验证级别
            context: 执行上下文

        Returns:
            质量报告
        """
        start_time = time.time()
        call_id = str(uuid.uuid4())

        try:
            logger.info(f"🔍 开始质量验证: {tool_name}")

            # 1. 执行验证规则
            validation_results = {}
            applicable_rules = [
                rule
                for rule in self.validation_rules.values()
                if self._is_rule_applicable(rule, validation_level)
            ]

            for rule in applicable_rules:
                try:
                    result = await self._execute_validation_rule(
                        rule, tool_name, function, parameters, context
                    )
                    validation_results[rule.name] = result
                except Exception as e:
                    logger.warning(f"⚠️ 验证规则 {rule.name} 执行失败: {e}")
                    if rule.is_required:
                        validation_results[rule.name] = False
                    else:
                        validation_results[rule.name] = True

            # 2. 计算质量指标
            quality_metrics = await self._calculate_quality_metrics(
                tool_name, function, parameters, validation_results
            )

            # 3. 风险评估
            risk_assessment = await self._assess_risks(
                tool_name, parameters, validation_results, context
            )

            # 4. 生成建议
            recommendations = await self._generate_recommendations(
                validation_results, quality_metrics, risk_assessment
            )

            # 5. 计算总体质量分数
            overall_score = self._calculate_overall_quality_score(
                validation_results, quality_metrics
            )
            overall_level = self._determine_quality_level(overall_score)

            execution_time = time.time() - start_time

            # 6. 创建质量报告
            report = QualityReport(
                call_id=call_id,
                tool_name=tool_name,
                timestamp=datetime.now(),
                validation_level=validation_level,
                validation_results=validation_results,
                quality_metrics=quality_metrics,
                overall_quality_score=overall_score,
                overall_quality_level=overall_level,
                risk_assessment=risk_assessment,
                recommendations=recommendations,
                execution_time=execution_time,
            )

            # 7. 保存报告
            self.quality_history.append(report)

            logger.info(
                f"✅ 质量验证完成: {tool_name}, 质量等级: {overall_level.value} ({overall_score:.2f})"
            )

            return report

        except Exception as e:
            logger.error(f"❌ 质量验证失败: {e}")
            return QualityReport(
                call_id=call_id,
                tool_name=tool_name,
                timestamp=datetime.now(),
                validation_level=validation_level,
                validation_results={"error": False},
                quality_metrics=[],
                overall_quality_score=0.0,
                overall_quality_level=QualityLevel.UNACCEPTABLE,
                risk_assessment=RiskAssessment(
                    risk_level=RiskLevel.CRITICAL,
                    risk_score=1.0,
                    identified_risks=[f"验证系统错误: {e!s}"],
                    mitigation_strategies=["检查质量保障系统配置"],
                    confidence=1.0,
                ),
                recommendations=["修复质量保障系统"],
                execution_time=time.time() - start_time,
            )

    def _is_rule_applicable(self, rule: ValidationRule, validation_level: ValidationLevel) -> bool:
        """检查规则是否适用"""
        level_priority = {
            ValidationLevel.BASIC: 1,
            ValidationLevel.STANDARD: 2,
            ValidationLevel.COMPREHENSIVE: 3,
            ValidationLevel.STRICT: 4,
        }

        return level_priority[rule.level] <= level_priority[validation_level]

    async def _execute_validation_rule(
        self,
        rule: ValidationRule,
        tool_name: str,
        function: Callable,
        parameters: dict[str, Any],        context: dict[str, Any] | None = None,
    ) -> bool:
        """执行验证规则"""
        try:
            if asyncio.iscoroutinefunction(rule.validator):
                return await rule.validator(tool_name, function, parameters, context)
            else:
                return rule.validator(tool_name, function, parameters, context)
        except Exception as e:
            logger.error(f"❌ 验证规则 {rule.name} 执行异常: {e}")
            return not rule.is_required

    # 验证规则实现
    def _validate_parameter_structure(
        self,
        tool_name: str,
        function: Callable,
        parameters: dict[str, Any],        context: dict[str, Any] | None = None,
    ) -> bool:
        """验证参数结构"""
        if not isinstance(parameters, dict):
            return False

        # 检查函数签名
        try:
            import inspect

            sig = inspect.signature(function)
            required_params = [
                name
                for name, param in sig.parameters.items()
                if param.default == inspect.Parameter.empty and param.kind != param.VAR_KEYWORD
            ]

            # 检查必需参数是否存在
            for param in required_params:
                if param not in parameters:
                    logger.warning(f"⚠️ 缺少必需参数: {param}")
                    return False

            return True

        except Exception as e:
            logger.warning(f"⚠️ 参数结构验证失败: {e}")
            return True  # 如果无法检查,默认通过

    def _validate_parameter_types(
        self,
        tool_name: str,
        function: Callable,
        parameters: dict[str, Any],        context: dict[str, Any] | None = None,
    ) -> bool:
        """验证参数类型"""
        try:
            import inspect

            sig = inspect.signature(function)

            for param_name, param_value in parameters.items():
                if param_name in sig.parameters:
                    param_info = sig.parameters[param_name]
                    expected_type = param_info.annotation

                    # 如果有类型注解,检查类型匹配
                    if expected_type != inspect.Parameter.empty:
                        try:
                            if not isinstance(param_value, expected_type):
                                # 尝试类型转换
                                converted_value = expected_type(param_value)
                                parameters[param_name] = converted_value
                        except (ValueError, TypeError):
                            logger.warning(
                                f"⚠️ 参数类型不匹配: {param_name} 期望 {expected_type}, 实际 {type(param_value)}"
                            )
                            return False

            return True

        except Exception as e:
            logger.warning(f"⚠️ 参数类型验证失败: {e}")
            return True

    def _validate_parameter_values(
        self,
        tool_name: str,
        function: Callable,
        parameters: dict[str, Any],        context: dict[str, Any] | None = None,
    ) -> bool:
        """验证参数值"""
        # 检查空值
        for key, value in parameters.items():
            if value is None:
                logger.warning(f"⚠️ 参数值为空: {key}")

        # 检查字符串长度
        for key, value in parameters.items():
            if isinstance(value, str) and len(value) > 10000:  # 10KB限制
                logger.warning(f"⚠️ 参数值过长: {key} ({len(value)} 字符)")
                return False

        # 检查数值范围
        for key, value in parameters.items():
            if isinstance(value, (int, float)):
                if value < -1e9 or value > 1e9:  # 数值范围检查
                    logger.warning(f"⚠️ 参数值超出范围: {key} = {value}")

        return True

    def _validate_security(
        self,
        tool_name: str,
        function: Callable,
        parameters: dict[str, Any],        context: dict[str, Any] | None = None,
    ) -> bool:
        """安全性验证"""
        # 检查危险模式
        import re

        for pattern in self.security_config["blocked_patterns"]:
            for value in parameters.values():
                if isinstance(value, str) and re.search(pattern, value, re.IGNORECASE):
                    logger.error(f"❌ 检测到危险模式: {pattern}")
                    return False

        # 检查参数大小
        for key, value in parameters.items():
            if isinstance(value, str):
                if len(value.encode("utf-8")) > self.security_config["max_parameter_size"]:
                    logger.error(f"❌ 参数过大: {key}")
                    return False

        # 检查外部URL(如果有)
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                if self.security_config["allowed_domains"]:
                    domain = value.split("/")[2]
                    if domain not in self.security_config["allowed_domains"]:
                        logger.warning(f"⚠️ 不允许的域名: {domain}")

        return True

    def _validate_resource_limits(
        self,
        tool_name: str,
        function: Callable,
        parameters: dict[str, Any],        context: dict[str, Any] | None = None,
    ) -> bool:
        """验证资源限制"""
        # 检查递归深度(如果有)
        recursion_depth = context.get("recursion_depth", 0) if context else 0
        if recursion_depth > 10:
            logger.error(f"❌ 递归深度过大: {recursion_depth}")
            return False

        # 检查并发限制
        concurrent_calls = context.get("concurrent_calls", 0) if context else 0
        if concurrent_calls > 50:
            logger.warning(f"⚠️ 并发调用过多: {concurrent_calls}")

        return True

    def _validate_dependencies(
        self,
        tool_name: str,
        function: Callable,
        parameters: dict[str, Any],        context: dict[str, Any] | None = None,
    ) -> bool:
        """验证依赖关系"""
        try:
            # 检查函数所需的模块是否可用
            import inspect

            source = inspect.getsource(function)

            # 简化的依赖检查
            required_modules = []
            for line in source.split("\n"):
                if line.strip().startswith("import "):
                    module_name = line.strip().replace("import ", "").split(" as ")[0]
                    required_modules.append(module_name)
                elif line.strip().startswith("from "):
                    module_name = line.strip().split(" ")[1]
                    required_modules.append(module_name)

            # 检查模块是否可导入
            for module in required_modules:
                try:
                    __import__(module)
                except ImportError as e:
                    logger.warning(f"⚠️ 依赖模块不可用: {module} - {e}")
                    return False

            return True

        except Exception as e:
            logger.warning(f"⚠️ 依赖检查失败: {e}")
            return True

    async def _calculate_quality_metrics(
        self,
        tool_name: str,
        function: Callable,
        parameters: dict[str, Any],        validation_results: dict[str, bool],
    ) -> list[QualityMetric]:
        """计算质量指标"""
        metrics = []

        # 验证通过率
        passed_validations = sum(validation_results.values())
        total_validations = len(validation_results)
        validation_pass_rate = passed_validations / max(total_validations, 1)

        metrics.append(
            QualityMetric(
                name="validation_pass_rate",
                value=validation_pass_rate,
                unit="ratio",
                threshold_min=0.8,
            )
        )

        # 参数复杂度
        param_complexity = len(str(parameters)) / 1000  # KB为单位
        metrics.append(
            QualityMetric(
                name="parameter_complexity", value=param_complexity, unit="KB", threshold_max=10.0
            )
        )

        # 函数复杂度(简化)
        try:
            import inspect

            source_lines = len(inspect.getsource(function).split("\n"))
            metrics.append(
                QualityMetric(
                    name="function_complexity", value=source_lines, unit="lines", threshold_max=500
                )
            )
        except Exception as e:
            logger.warning(f"操作失败: {e}")

        # 安全评分
        security_score = 1.0 if validation_results.get("security_check", True) else 0.0
        metrics.append(
            QualityMetric(
                name="security_score", value=security_score, unit="ratio", threshold_min=0.9
            )
        )

        # 计算每个指标的质量等级
        for metric in metrics:
            metric.quality_level = self._determine_metric_quality_level(metric)

        return metrics

    async def _assess_risks(
        self,
        tool_name: str,
        parameters: dict[str, Any],        validation_results: dict[str, bool],
        context: dict[str, Any] | None = None,
    ) -> RiskAssessment:
        """风险评估"""
        risks = []
        mitigation_strategies = []
        risk_score = 0.0

        # 安全风险
        if not validation_results.get("security_check", True):
            risks.append("安全检查失败")
            mitigation_strategies.append("检查参数安全性")
            risk_score += 0.4

        # 参数风险
        param_risks = self._assess_parameter_risks(parameters)
        risks.extend(param_risks["risks"])
        mitigation_strategies.extend(param_risks["mitigations"])
        risk_score += param_risks["score"]

        # 上下文风险
        if context:
            context_risks = self._assess_context_risks(context)
            risks.extend(context_risks["risks"])
            mitigation_strategies.extend(context_risks["mitigations"])
            risk_score += context_risks["score"]

        # 确定风险等级
        if risk_score >= 0.8:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 0.3:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        return RiskAssessment(
            risk_level=risk_level,
            risk_score=min(risk_score, 1.0),
            identified_risks=risks,
            mitigation_strategies=mitigation_strategies,
            confidence=0.8,
        )

    def _assess_parameter_risks(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """评估参数风险"""
        risks = []
        mitigations = []
        score = 0.0

        for key, value in parameters.items():
            # 大参数风险
            if isinstance(value, str) and len(value) > 5000:
                risks.append(f"参数 {key} 过大")
                mitigations.append(f"限制参数 {key} 的大小")
                score += 0.1

            # URL风险
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                risks.append(f"参数 {key} 包含外部URL")
                mitigations.append(f"验证URL安全性: {value}")
                score += 0.15

            # 特殊字符风险
            if isinstance(value, str) and any(char in value for char in ["<", ">", "&", "|", ";"]):
                risks.append(f"参数 {key} 包含特殊字符")
                mitigations.append(f"清理特殊字符: {value}")
                score += 0.1

        return {"risks": risks, "mitigations": mitigations, "score": score}

    def _assess_context_risks(self, context: dict[str, Any]) -> dict[str, Any]:
        """评估上下文风险"""
        risks = []
        mitigations = []
        score = 0.0

        # 并发风险
        concurrent = context.get("concurrent_calls", 0)
        if concurrent > 20:
            risks.append(f"高并发调用: {concurrent}")
            mitigations.append("限制并发数量")
            score += 0.2

        # 递归风险
        depth = context.get("recursion_depth", 0)
        if depth > 5:
            risks.append(f"递归深度过大: {depth}")
            mitigations.append("限制递归深度")
            score += 0.15

        # 超时风险
        timeout = context.get("timeout", 30)
        if timeout > 300:
            risks.append(f"超时时间过长: {timeout}s")
            mitigations.append("设置合理的超时时间")
            score += 0.1

        return {"risks": risks, "mitigations": mitigations, "score": score}

    async def _generate_recommendations(
        self,
        validation_results: dict[str, bool],
        quality_metrics: list[QualityMetric],
        risk_assessment: RiskAssessment,
    ) -> list[str]:
        """生成改进建议"""
        recommendations = []

        # 基于验证结果的建议
        failed_validations = [name for name, passed in validation_results.items() if not passed]
        if failed_validations:
            recommendations.append(f"修复失败的验证规则: {', '.join(failed_validations)}")

        # 基于质量指标的建议
        poor_metrics = [
            m
            for m in quality_metrics
            if m.quality_level in [QualityLevel.POOR, QualityLevel.UNACCEPTABLE]
        ]
        for metric in poor_metrics:
            if metric.name == "validation_pass_rate":
                recommendations.append("提高参数验证通过率")
            elif metric.name == "parameter_complexity":
                recommendations.append("简化参数结构")
            elif metric.name == "function_complexity":
                recommendations.append("重构函数以降低复杂度")
            elif metric.name == "security_score":
                recommendations.append("加强安全性检查")

        # 基于风险评估的建议
        if risk_assessment.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.extend(risk_assessment.mitigation_strategies)

        # 如果没有严重问题,给出积极建议
        if not recommendations:
            recommendations.append("质量检查通过,继续保持")

        return recommendations

    def _calculate_overall_quality_score(
        self, validation_results: dict[str, bool], quality_metrics: list[QualityMetric]
    ) -> float:
        """计算总体质量分数"""
        # 验证结果权重 60%
        validation_score = 0.0
        if validation_results:
            passed = sum(validation_results.values())
            total = len(validation_results)
            validation_score = passed / total

        # 质量指标权重 40%
        metric_score = 0.0
        if quality_metrics:
            scores = []
            for metric in quality_metrics:
                if metric.name == "validation_pass_rate" or metric.name == "security_score":
                    scores.append(metric.value)
                elif metric.name == "parameter_complexity":
                    # 复杂度越低越好
                    normalized = max(0, 1 - metric.value / 10.0)
                    scores.append(normalized)
                elif metric.name == "function_complexity":
                    # 复杂度越低越好
                    normalized = max(0, 1 - metric.value / 500.0)
                    scores.append(normalized)

            if scores:
                metric_score = sum(scores) / len(scores)

        # 加权平均
        overall_score = validation_score * 0.6 + metric_score * 0.4
        return min(overall_score, 1.0)

    def _determine_quality_level(self, score: float) -> QualityLevel:
        """确定质量等级"""
        if score >= 0.95:
            return QualityLevel.EXCELLENT
        elif score >= 0.85:
            return QualityLevel.GOOD
        elif score >= 0.70:
            return QualityLevel.ACCEPTABLE
        elif score >= 0.50:
            return QualityLevel.POOR
        else:
            return QualityLevel.UNACCEPTABLE

    def _determine_metric_quality_level(self, metric: QualityMetric) -> QualityLevel:
        """确定指标质量等级"""
        score = metric.value

        if metric.name == "validation_pass_rate" or metric.name == "security_score":
            # 越高越好的指标
            if score >= 0.95:
                return QualityLevel.EXCELLENT
            elif score >= 0.85:
                return QualityLevel.GOOD
            elif score >= 0.70:
                return QualityLevel.ACCEPTABLE
            elif score >= 0.50:
                return QualityLevel.POOR
            else:
                return QualityLevel.UNACCEPTABLE

        elif metric.name in ["parameter_complexity", "function_complexity"]:
            # 越低越好的指标(需要归一化)
            if metric.threshold_max:
                normalized = 1 - (score / metric.threshold_max)
                return self._determine_quality_level(normalized)

        return QualityLevel.ACCEPTABLE

    def get_quality_summary(self, days: int = 7) -> dict[str, Any]:
        """获取质量摘要"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_reports = [r for r in self.quality_history if r.timestamp >= cutoff_date]

        if not recent_reports:
            return {"message": "暂无质量历史数据"}

        # 统计分析
        total_calls = len(recent_reports)
        quality_distribution = {level.value: 0 for level in QualityLevel}
        risk_distribution = {level.value: 0 for level in RiskLevel}

        total_score = 0.0
        validation_failures = defaultdict(int)

        for report in recent_reports:
            quality_distribution[report.overall_quality_level.value] += 1
            risk_distribution[report.risk_assessment.risk_level.value] += 1
            total_score += report.overall_quality_score

            # 统计验证失败
            for rule_name, passed in report.validation_results.items():
                if not passed:
                    validation_failures[rule_name] += 1

        # 计算平均值
        avg_quality_score = total_score / total_calls

        # 常见问题
        common_issues = sorted(validation_failures.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "period_days": days,
            "total_calls": total_calls,
            "average_quality_score": avg_quality_score,
            "quality_distribution": quality_distribution,
            "risk_distribution": risk_distribution,
            "common_validation_failures": common_issues,
            "generated_at": datetime.now().isoformat(),
        }

    def export_quality_data(self, format: str = "json") -> str:
        """导出质量数据"""
        data = {
            "system_info": {
                "name": self.name,
                "version": self.version,
                "export_timestamp": datetime.now().isoformat(),
            },
            "validation_rules": {
                name: {
                    "description": rule.description,
                    "level": rule.level.value,
                    "is_required": rule.is_required,
                }
                for name, rule in self.validation_rules.items()
            },
            "quality_benchmarks": self.quality_benchmarks,
            "quality_history": [
                {
                    "call_id": report.call_id,
                    "tool_name": report.tool_name,
                    "timestamp": report.timestamp.isoformat(),
                    "quality_score": report.overall_quality_score,
                    "quality_level": report.overall_quality_level.value,
                    "risk_level": report.risk_assessment.risk_level.value,
                    "validation_results": report.validation_results,
                }
                for report in self.quality_history
            ],
        }

        if format.lower() == "json":
            return json.dumps(data, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的导出格式: {format}")


# 全局实例
xiaonuo_quality_assurance = XiaonuoFunctionCallingQualityAssurance()


# 便捷函数
async def validate_call(
    tool_name: str,
    function: Callable,
    parameters: dict[str, Any],    level: ValidationLevel = ValidationLevel.STANDARD,
) -> QualityReport:
    """便捷的验证函数"""
    return await xiaonuo_quality_assurance.validate_function_call(
        tool_name, function, parameters, level
    )
