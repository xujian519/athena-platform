#!/usr/bin/env python3
from __future__ import annotations
"""
上下文冲突检测器 - 第二阶段
Context Conflict Detector - Phase 2

核心功能:
1. 上下文一致性检测
2. 参数冲突识别
3. 意图冲突分析
4. 冲突解决建议

作者: 小诺·双鱼公主
版本: v1.0.0 "冲突检测"
创建: 2026-01-12
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """冲突类型"""

    PARAMETER_VALUE = "parameter_value"  # 参数值冲突
    PARAMETER_TYPE = "parameter_type"  # 参数类型冲突
    INTENT_INCONSISTENCY = "intent_inconsistency"  # 意图不一致
    CONTEXT_INCOHERENCE = "context_incoherence"  # 上下文不连贯
    TEMPORAL_INCONSISTENCY = "temporal_inconsistency"  # 时序不一致
    LOGICAL_CONTRADICTION = "logical_contradiction"  # 逻辑矛盾


class ConflictSeverity(Enum):
    """冲突严重程度"""

    CRITICAL = "critical"  # 严重冲突,必须解决
    HIGH = "high"  # 高危冲突,强烈建议解决
    MEDIUM = "medium"  # 中等冲突,建议解决
    LOW = "low"  # 轻微冲突,可选解决


@dataclass
class Conflict:
    """冲突"""

    conflict_id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    description: str

    # 冲突涉及的信息
    involved_elements: list[str]  # 涉及的元素(参数、意图等)
    conflicting_values: dict[str, Any]
    # 检测信息
    detected_at: datetime = field(default_factory=datetime.now)
    detection_method: str = ""

    # 解决信息
    resolution_suggestions: list[str] = field(default_factory=list)
    auto_resolvable: bool = False
    resolution: Optional[str] = None


@dataclass
class ContextState:
    """上下文状态"""

    session_id: str
    user_id: str

    # 当前意图
    current_intent: Optional[str] = None
    intent_history: list[str] = field(default_factory=list)

    # 参数状态
    parameters: dict[str, Any] = field(default_factory=dict)
    parameter_history: list[dict[str, Any]] = field(default_factory=list)

    # 对话历史
    conversation_history: list[dict[str, Any]] = field(default_factory=list)

    # 时间戳
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ConflictDetectionResult:
    """冲突检测结果"""

    has_conflicts: bool
    conflicts: list[Conflict]
    context_state: ContextState
    detection_summary: dict[str, int]  # 各类型冲突数量
    resolution_priority: list[str]  # 解决优先级


class ContextConflictDetector:
    """上下文冲突检测器"""

    def __init__(self):
        self.name = "上下文冲突检测器 v1.0"
        self.version = "1.0.0"

        # 冲突历史
        self.conflict_history: list[Conflict] = []

        # 冲突模式库
        self.conflict_patterns = self._init_conflict_patterns()

        # 解决策略库
        self.resolution_strategies = self._init_resolution_strategies()

        # 统计信息
        self.stats = {
            "total_detections": 0,
            "conflicts_found": 0,
            "conflicts_resolved": 0,
            "auto_resolved": 0,
            "conflict_types": defaultdict(int),
        }

        logger.info(f"🔍 {self.name} 初始化完成")

    def _init_conflict_patterns(self) -> dict[ConflictType, list[dict]]:
        """初始化冲突模式库"""
        return {
            ConflictType.PARAMETER_VALUE: [
                {
                    "pattern": "duplicate_parameter",
                    "description": "参数重复定义但值不同",
                    "check_fn": self._check_duplicate_parameters,
                },
                {
                    "pattern": "value_range_conflict",
                    "description": "参数值超出有效范围",
                    "check_fn": self._check_value_ranges,
                },
            ],
            ConflictType.PARAMETER_TYPE: [
                {
                    "pattern": "type_mismatch",
                    "description": "参数类型不匹配",
                    "check_fn": self._check_parameter_types,
                }
            ],
            ConflictType.INTENT_INCONSISTENCY: [
                {
                    "pattern": "intent_switch",
                    "description": "意图频繁切换",
                    "check_fn": self._check_intent_stability,
                },
                {
                    "pattern": "intent_parameter_mismatch",
                    "description": "意图与参数不匹配",
                    "check_fn": self._check_intent_parameter_match,
                },
            ],
            ConflictType.CONTEXT_INCOHERENCE: [
                {
                    "pattern": "topic_drift",
                    "description": "话题偏离",
                    "check_fn": self._check_topic_coherence,
                }
            ],
            ConflictType.TEMPORAL_INCONSISTENCY: [
                {
                    "pattern": "temporal_violation",
                    "description": "时序违反",
                    "check_fn": self._check_temporal_consistency,
                }
            ],
            ConflictType.LOGICAL_CONTRADICTION: [
                {
                    "pattern": "logical_contradiction",
                    "description": "逻辑矛盾",
                    "check_fn": self._check_logical_contradictions,
                }
            ],
        }

    def _init_resolution_strategies(self) -> dict[ConflictType, list[str]]:
        """初始化解决策略库"""
        return {
            ConflictType.PARAMETER_VALUE: [
                "使用最新的参数值",
                "合并参数值(取并集)",
                "根据优先级选择",
                "询问用户确认",
            ],
            ConflictType.PARAMETER_TYPE: [
                "尝试类型转换",
                "使用默认值",
                "提示用户重新输入",
                "跳过该参数",
            ],
            ConflictType.INTENT_INCONSISTENCY: [
                "使用当前意图",
                "基于上下文推断",
                "询问用户确认",
                "重置对话状态",
            ],
            ConflictType.CONTEXT_INCOHERENCE: ["总结前文", "重新聚焦主题", "引导用户回到主题"],
            ConflictType.TEMPORAL_INCONSISTENCY: ["按时间排序", "标记时序异常", "使用最新状态"],
            ConflictType.LOGICAL_CONTRADICTION: ["标记矛盾点", "请求澄清", "基于置信度选择"],
        }

    def detect_conflicts(
        self, context_state: ContextState, new_input: Optional[dict[str, Any]] = None
    ) -> ConflictDetectionResult:
        """
        检测上下文冲突

        Args:
            context_state: 当前上下文状态
            new_input: 新输入(可选)

        Returns:
            ConflictDetectionResult: 检测结果
        """
        self.stats["total_detections"] += 1

        # 如果有新输入,更新上下文
        if new_input:
            context_state = self._update_context(context_state, new_input)

        conflicts = []

        # 1. 检测参数值冲突
        param_value_conflicts = self._detect_parameter_value_conflicts(context_state)
        conflicts.extend(param_value_conflicts)

        # 2. 检测参数类型冲突
        param_type_conflicts = self._detect_parameter_type_conflicts(context_state)
        conflicts.extend(param_type_conflicts)

        # 3. 检测意图不一致
        intent_conflicts = self._detect_intent_conflicts(context_state)
        conflicts.extend(intent_conflicts)

        # 4. 检测上下文不连贯
        context_conflicts = self._detect_context_incoherence(context_state)
        conflicts.extend(context_conflicts)

        # 5. 检测时序不一致
        temporal_conflicts = self._detect_temporal_conflicts(context_state)
        conflicts.extend(temporal_conflicts)

        # 6. 检测逻辑矛盾
        logical_conflicts = self._detect_logical_contradictions(context_state)
        conflicts.extend(logical_conflicts)

        # 7. 更新统计
        self._update_stats(conflicts)

        # 8. 记录冲突
        self.conflict_history.extend(conflicts)

        # 9. 生成检测摘要
        detection_summary = self._generate_detection_summary(conflicts)

        # 10. 确定解决优先级
        resolution_priority = self._determine_resolution_priority(conflicts)

        return ConflictDetectionResult(
            has_conflicts=len(conflicts) > 0,
            conflicts=conflicts,
            context_state=context_state,
            detection_summary=detection_summary,
            resolution_priority=resolution_priority,
        )

    def _update_context(
        self, context_state: ContextState, new_input: dict[str, Any]
    ) -> ContextState:
        """更新上下文状态"""
        # 更新意图
        if "intent" in new_input:
            context_state.current_intent = new_input["intent"]
            context_state.intent_history.append(new_input["intent"])

        # 更新参数
        if "parameters" in new_input:
            context_state.parameters.update(new_input["parameters"])
            context_state.parameter_history.append(new_input["parameters"].copy())

        # 更新对话历史
        context_state.conversation_history.append(
            {"timestamp": datetime.now().isoformat(), "input": new_input}
        )

        context_state.last_updated = datetime.now()

        return context_state

    def _detect_parameter_value_conflicts(self, context: ContextState) -> list[Conflict]:
        """检测参数值冲突"""
        conflicts = []

        for pattern_info in self.conflict_patterns[ConflictType.PARAMETER_VALUE]:
            try:
                pattern_conflicts = pattern_info["check_fn"](context)
                conflicts.extend(pattern_conflicts)
            except Exception as e:
                logger.error(f"❌ 检测参数值冲突失败: {e}")

        return conflicts

    def _detect_parameter_type_conflicts(self, context: ContextState) -> list[Conflict]:
        """检测参数类型冲突"""
        conflicts = []

        for pattern_info in self.conflict_patterns[ConflictType.PARAMETER_TYPE]:
            try:
                pattern_conflicts = pattern_info["check_fn"](context)
                conflicts.extend(pattern_conflicts)
            except Exception as e:
                logger.error(f"❌ 检测参数类型冲突失败: {e}")

        return conflicts

    def _detect_intent_conflicts(self, context: ContextState) -> list[Conflict]:
        """检测意图冲突"""
        conflicts = []

        for pattern_info in self.conflict_patterns[ConflictType.INTENT_INCONSISTENCY]:
            try:
                pattern_conflicts = pattern_info["check_fn"](context)
                conflicts.extend(pattern_conflicts)
            except Exception as e:
                logger.error(f"❌ 检测意图冲突失败: {e}")

        return conflicts

    def _detect_context_incoherence(self, context: ContextState) -> list[Conflict]:
        """检测上下文不连贯"""
        conflicts = []

        for pattern_info in self.conflict_patterns[ConflictType.CONTEXT_INCOHERENCE]:
            try:
                pattern_conflicts = pattern_info["check_fn"](context)
                conflicts.extend(pattern_conflicts)
            except Exception as e:
                logger.error(f"❌ 检测上下文不连贯失败: {e}")

        return conflicts

    def _detect_temporal_conflicts(self, context: ContextState) -> list[Conflict]:
        """检测时序冲突"""
        conflicts = []

        for pattern_info in self.conflict_patterns[ConflictType.TEMPORAL_INCONSISTENCY]:
            try:
                pattern_conflicts = pattern_info["check_fn"](context)
                conflicts.extend(pattern_conflicts)
            except Exception as e:
                logger.error(f"❌ 检测时序冲突失败: {e}")

        return conflicts

    def _detect_logical_contradictions(self, context: ContextState) -> list[Conflict]:
        """检测逻辑矛盾"""
        conflicts = []

        for pattern_info in self.conflict_patterns[ConflictType.LOGICAL_CONTRADICTION]:
            try:
                pattern_conflicts = pattern_info["check_fn"](context)
                conflicts.extend(pattern_conflicts)
            except Exception as e:
                logger.error(f"❌ 检测逻辑矛盾失败: {e}")

        return conflicts

    # ========== 具体检测方法 ==========

    def _check_duplicate_parameters(self, context: ContextState) -> list[Conflict]:
        """检查重复参数"""
        conflicts = []

        # 检查参数历史中是否有重复但值不同的情况
        param_history = context.parameter_history
        if len(param_history) < 2:
            return conflicts

        # 跟踪参数值变化
        param_values = {}
        for i, params in enumerate(param_history):
            for param_name, param_value in params.items():
                if param_name in param_values:
                    if param_values[param_name] != param_value:
                        conflicts.append(
                            Conflict(
                                conflict_id=f"dup_param_{param_name}_{i}",
                                conflict_type=ConflictType.PARAMETER_VALUE,
                                severity=ConflictSeverity.MEDIUM,
                                description=f"参数'{param_name}'的值发生变化: {param_values[param_name]} → {param_value}",
                                involved_elements=[param_name],
                                conflicting_values={
                                    "old_value": param_values[param_name],
                                    "new_value": param_value,
                                },
                                detection_method="duplicate_parameter_check",
                                resolution_suggestions=[
                                    "使用最新值",
                                    "根据上下文选择",
                                    "询问用户确认",
                                ],
                            )
                        )
                param_values[param_name] = param_value

        return conflicts

    def _check_value_ranges(self, context: ContextState) -> list[Conflict]:
        """检查值范围"""
        conflicts = []

        # 定义参数有效范围
        value_ranges = {
            "confidence": (0.0, 1.0),
            "threshold": (0.0, 1.0),
            "temperature": (0.0, 2.0),
            "max_tokens": (1, 4096),
        }

        for param_name, (min_val, max_val) in value_ranges.items():
            if param_name in context.parameters:
                value = context.parameters[param_name]

                try:
                    numeric_value = float(value)
                    if numeric_value < min_val or numeric_value > max_val:
                        conflicts.append(
                            Conflict(
                                conflict_id=f"range_{param_name}",
                                conflict_type=ConflictType.PARAMETER_VALUE,
                                severity=ConflictSeverity.HIGH,
                                description=f"参数'{param_name}'的值{numeric_value}超出范围[{min_val}, {max_val}]",
                                involved_elements=[param_name],
                                conflicting_values={
                                    "value": numeric_value,
                                    "range": (min_val, max_val),
                                },
                                detection_method="value_range_check",
                                auto_resolvable=True,
                                resolution_suggestions=[
                                    "将值裁剪到有效范围",
                                    "使用默认值",
                                    "提示用户重新输入",
                                ],
                            )
                        )
                except (ValueError, TypeError):
                    pass

        return conflicts

    def _check_parameter_types(self, context: ContextState) -> list[Conflict]:
        """检查参数类型"""
        conflicts = []

        # 定义参数期望类型
        expected_types = {
            "patent_number": str,
            "confidence": (int, float),
            "max_results": int,
            "aspects": list,
        }

        for param_name, expected_type in expected_types.items():
            if param_name in context.parameters:
                value = context.parameters[param_name]

                if not isinstance(value, expected_type):
                    conflicts.append(
                        Conflict(
                            conflict_id=f"type_{param_name}",
                            conflict_type=ConflictType.PARAMETER_TYPE,
                            severity=ConflictSeverity.MEDIUM,
                            description=f"参数'{param_name}'的类型不匹配,期望{expected_type},实际{type(value)}",
                            involved_elements=[param_name],
                            conflicting_values={
                                "expected": str(expected_type),
                                "actual": str(type(value)),
                            },
                            detection_method="type_check",
                            resolution_suggestions=[
                                "尝试类型转换",
                                "使用默认值",
                                "提示用户重新输入",
                            ],
                        )
                    )

        return conflicts

    def _check_intent_stability(self, context: ContextState) -> list[Conflict]:
        """检查意图稳定性"""
        conflicts = []

        intent_history = context.intent_history
        if len(intent_history) < 3:
            return conflicts

        # 检查最近3次意图是否频繁变化
        recent_intents = intent_history[-3:]
        unique_intents = set(recent_intents)

        if len(unique_intents) == len(recent_intents):
            # 每次意图都不同,可能存在不稳定
            conflicts.append(
                Conflict(
                    conflict_id="intent_instability",
                    conflict_type=ConflictType.INTENT_INCONSISTENCY,
                    severity=ConflictSeverity.LOW,
                    description=f"意图频繁切换: {recent_intents}",
                    involved_elements=["intent"],
                    conflicting_values={"intent_history": recent_intents},
                    detection_method="intent_stability_check",
                    resolution_suggestions=["使用当前意图", "基于上下文推断", "询问用户确认"],
                )
            )

        return conflicts

    def _check_intent_parameter_match(self, context: ContextState) -> list[Conflict]:
        """检查意图参数匹配"""
        conflicts = []

        if not context.current_intent or not context.parameters:
            return conflicts

        # 定义意图必需参数
        intent_required_params = {
            "patent_analysis": ["patent_number"],
            "coding": ["requirements"],
            "data_analysis": ["data"],
        }

        required_params = intent_required_params.get(context.current_intent, [])
        missing_params = [p for p in required_params if p not in context.parameters]

        if missing_params:
            conflicts.append(
                Conflict(
                    conflict_id=f"intent_param_mismatch_{context.current_intent}",
                    conflict_type=ConflictType.INTENT_INCONSISTENCY,
                    severity=ConflictSeverity.HIGH,
                    description=f"意图'{context.current_intent}'缺少必需参数: {missing_params}",
                    involved_elements=["intent", *missing_params],
                    conflicting_values={
                        "intent": context.current_intent,
                        "required_params": required_params,
                        "provided_params": list(context.parameters.keys()),
                    },
                    detection_method="intent_parameter_match_check",
                    resolution_suggestions=["从上下文推断参数值", "使用默认值", "询问用户提供参数"],
                )
            )

        return conflicts

    def _check_topic_coherence(self, context: ContextState) -> list[Conflict]:
        """检查主题连贯性"""
        conflicts = []

        # 简化实现: 检查意图变化幅度
        if len(context.intent_history) < 2:
            return conflicts

        # 定义相关意图组
        intent_groups = {
            "patent": ["patent_analysis", "patent_search", "patent_drafting"],
            "coding": ["coding", "debug", "code_review"],
            "chat": ["daily_chat", "greeting", "casual_conversation"],
        }

        # 检查是否在不同组之间频繁切换
        recent_intents = context.intent_history[-5:]
        switches = 0

        for i in range(len(recent_intents) - 1):
            current_group = self._get_intent_group(recent_intents[i], intent_groups)
            next_group = self._get_intent_group(recent_intents[i + 1], intent_groups)

            if current_group and next_group and current_group != next_group:
                switches += 1

        if switches >= 3:
            conflicts.append(
                Conflict(
                    conflict_id="topic_drift",
                    conflict_type=ConflictType.CONTEXT_INCOHERENCE,
                    severity=ConflictSeverity.MEDIUM,
                    description=f"检测到话题偏离,最近{switches}次跨主题切换",
                    involved_elements=["context"],
                    conflicting_values={"switches": switches, "intents": recent_intents},
                    detection_method="topic_coherence_check",
                    resolution_suggestions=["总结前文", "引导用户回到主题", "重新开始新主题"],
                )
            )

        return conflicts

    def _get_intent_group(self, intent: str, groups: dict[str, list[str]]) -> Optional[str]:
        """获取意图所属组"""
        for group_name, intents in groups.items():
            if intent in intents:
                return group_name
        return None

    def _check_temporal_consistency(self, context: ContextState) -> list[Conflict]:
        """检查时序一致性"""
        conflicts = []

        # 检查对话历史的时间顺序
        timestamps = [
            datetime.fromisoformat(turn["timestamp"])
            for turn in context.conversation_history
            if "timestamp" in turn
        ]

        for i in range(1, len(timestamps)):
            if timestamps[i] < timestamps[i - 1]:
                conflicts.append(
                    Conflict(
                        conflict_id=f"temporal_violation_{i}",
                        conflict_type=ConflictType.TEMPORAL_INCONSISTENCY,
                        severity=ConflictSeverity.LOW,
                        description=f"时序异常: 第{i}轮对话早于第{i-1}轮",
                        involved_elements=[f"turn_{i}", f"turn_{i-1}"],
                        conflicting_values={
                            "turn_i": timestamps[i].isoformat(),
                            "turn_i_minus_1": timestamps[i - 1].isoformat(),
                        },
                        detection_method="temporal_consistency_check",
                        auto_resolvable=True,
                        resolution_suggestions=["按时间排序", "使用最新状态", "忽略异常记录"],
                    )
                )

        return conflicts

    def _check_logical_contradictions(self, context: ContextState) -> list[Conflict]:
        """检查逻辑矛盾"""
        conflicts = []

        # 检查参数之间的逻辑关系
        # 示例: max_results <= 0 是矛盾的
        if "max_results" in context.parameters:
            max_results = context.parameters["max_results"]
            try:
                if int(max_results) <= 0:
                    conflicts.append(
                        Conflict(
                            conflict_id="logical_contradiction_max_results",
                            conflict_type=ConflictType.LOGICAL_CONTRADICTION,
                            severity=ConflictSeverity.HIGH,
                            description=f"逻辑矛盾: max_results={max_results}应该大于0",
                            involved_elements=["max_results"],
                            conflicting_values={"max_results": max_results},
                            detection_method="logical_contradiction_check",
                            auto_resolvable=True,
                            resolution_suggestions=[
                                "使用默认值(例如10)",
                                "设置为1",
                                "提示用户重新输入",
                            ],
                        )
                    )
            except (ValueError, TypeError):
                pass

        # 检查confidence和threshold的关系
        if "confidence" in context.parameters and "threshold" in context.parameters:
            confidence = context.parameters.get("confidence", 0.5)
            threshold = context.parameters.get("threshold", 0.5)

            try:
                if float(confidence) < float(threshold):
                    conflicts.append(
                        Conflict(
                            conflict_id="logical_contradiction_confidence",
                            conflict_type=ConflictType.LOGICAL_CONTRADICTION,
                            severity=ConflictSeverity.MEDIUM,
                            description=f"逻辑矛盾: confidence({confidence}) < threshold({threshold})",
                            involved_elements=["confidence", "threshold"],
                            conflicting_values={"confidence": confidence, "threshold": threshold},
                            detection_method="logical_contradiction_check",
                            resolution_suggestions=[
                                "提高confidence",
                                "降低threshold",
                                "询问用户确认",
                            ],
                        )
                    )
            except (ValueError, TypeError):
                pass

        return conflicts

    def _update_stats(self, conflicts: list[Conflict]) -> Any:
        """更新统计"""
        self.stats["conflicts_found"] += len(conflicts)

        for conflict in conflicts:
            self.stats["conflict_types"][conflict.conflict_type.value] += 1

    def _generate_detection_summary(self, conflicts: list[Conflict]) -> dict[str, int]:
        """生成检测摘要"""
        summary = defaultdict(int)
        for conflict in conflicts:
            summary[conflict.conflict_type.value] += 1
        return dict(summary)

    def _determine_resolution_priority(self, conflicts: list[Conflict]) -> list[str]:
        """确定解决优先级"""
        # 按严重程度排序
        severity_order = {
            ConflictSeverity.CRITICAL: 0,
            ConflictSeverity.HIGH: 1,
            ConflictSeverity.MEDIUM: 2,
            ConflictSeverity.LOW: 3,
        }

        sorted_conflicts = sorted(conflicts, key=lambda c: severity_order.get(c.severity, 4))

        return [c.conflict_id for c in sorted_conflicts]

    def resolve_conflict(self, conflict: Conflict, resolution_method: str) -> bool:
        """
        解决冲突

        Args:
            conflict: 冲突对象
            resolution_method: 解决方法

        Returns:
            bool: 是否成功解决
        """
        try:
            # 根据冲突类型和解决方法执行解决逻辑
            if resolution_method == "auto":
                if conflict.auto_resolvable:
                    conflict.resolution = "自动解决"
                    self.stats["auto_resolved"] += 1
                    return True
                else:
                    return False

            # 其他解决方法...
            conflict.resolution = f"使用方法: {resolution_method}"
            self.stats["conflicts_resolved"] += 1
            return True

        except Exception as e:
            logger.error(f"❌ 解决冲突失败: {e}")
            return False

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "conflict_history_size": len(self.conflict_history),
            "pattern_count": sum(len(patterns) for patterns in self.conflict_patterns.values()),
        }


# 全局实例
_detector_instance: ContextConflictDetector | None = None


def get_context_conflict_detector() -> ContextConflictDetector:
    """获取上下文冲突检测器单例"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = ContextConflictDetector()
    return _detector_instance
