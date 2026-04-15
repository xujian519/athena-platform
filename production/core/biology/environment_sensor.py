#!/usr/bin/env python3
"""
环境感知系统
Environment Perception System

基于生物学中"环境选择压力"的思想:
- 生命需要感知环境变化以适应演化
- 用户需求 = AI系统的环境压力
- 从被动响应到主动预判

作者: 小诺·双鱼公主
创建时间: 2025-12-24
版本: v0.1.2 "晨星初现"
"""

from __future__ import annotations
import json
import logging
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class PressureType(Enum):
    """压力类型"""

    USER_REQUEST = "user_request"  # 用户请求
    USER_FEEDBACK = "user_feedback"  # 用户反馈
    PERFORMANCE_ISSUE = "performance_issue"  # 性能问题
    ERROR_OCCURRED = "error_occurred"  # 错误发生
    NOVELTY_DETECTED = "novelty_detected"  # 新奇性检测


class UrgencyLevel(Enum):
    """紧急程度"""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class EnvironmentalPressure:
    """环境压力"""

    pressure_id: str
    pressure_type: PressureType
    urgency: UrgencyLevel
    description: str
    source: str  # 压力来源(如"用户输入")
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved: bool = False


@dataclass
class AdaptationAction:
    """适应性行动"""

    action_id: str
    pressure_id: str
    description: str
    action_type: str
    confidence: float = 0.5
    executed: bool = False
    result: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class EnvironmentSensor:
    """
    环境感知系统

    核心功能:
    1. 感知环境压力(用户需求、系统状态)
    2. 评估压力紧急程度
    3. 触发适应性行动
    4. 预测未来压力
    """

    def __init__(self, history_window: int = 100):
        """
        初始化环境感知系统

        Args:
            history_window: 历史记录窗口大小
        """
        self.name = "环境感知系统"
        self.version = "v0.1.2"

        # 压力历史
        self.pressure_history: deque = deque(maxlen=history_window)

        # 适应行动历史
        self.adaptation_history: deque = deque(maxlen=history_window)

        # 当前活跃压力
        self.active_pressures: dict[str, EnvironmentalPressure] = {}

        # 压力模式(用于预测)
        self.pressure_patterns: dict[str, list[EnvironmentalPressure]] = defaultdict(list)

        # 预测模型(简化实现)
        self.prediction_rules = self._init_prediction_rules()

        logger.info(f"🌍 {self.name} ({self.version}) 初始化完成")

    def _init_prediction_rules(self) -> dict[str, Any]:
        """初始化预测规则"""
        return {
            "time_based": {
                "morning_rush": {  # 早高峰
                    "hour_range": (8, 10),
                    "likely_pressure": "性能压力",
                    "suggested_action": "预热系统",
                },
                "evening_rush": {  # 晚高峰
                    "hour_range": (18, 21),
                    "likely_pressure": "用户请求增多",
                    "suggested_action": "增加资源",
                },
            },
            "frequency_based": {
                "threshold": 3,  # 连续3次类似压力
                "action": "优化该功能的调用路径",
            },
            "pattern_based": {"novelty_detection": True, "anomaly_detection": True},
        }

    def detect_pressure(
        self,
        pressure_type: PressureType,
        description: str,
        urgency: UrgencyLevel = UrgencyLevel.MEDIUM,
        source: str = "system",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        检测环境压力

        Args:
            pressure_type: 压力类型
            description: 描述
            urgency: 紧急程度
            source: 来源
            metadata: 元数据

        Returns:
            压力ID
        """
        pressure_id = f"pressure_{datetime.now().timestamp()}"

        pressure = EnvironmentalPressure(
            pressure_id=pressure_id,
            pressure_type=pressure_type,
            urgency=urgency,
            description=description,
            source=source,
            metadata=metadata or {},
        )

        # 添加到历史
        self.pressure_history.append(pressure)

        # 如果未解决,添加到活跃压力
        if not pressure.resolved:
            self.active_pressures[pressure_id] = pressure

        # 记录模式
        self.pressure_patterns[pressure_type.value].append(pressure)

        logger.info(f"🌍 检测到压力: {pressure_type.value} - {description}")

        return pressure_id

    def resolve_pressure(self, pressure_id: str) -> None:
        """
        解决压力

        Args:
            pressure_id: 压力ID
        """
        if pressure_id in self.active_pressures:
            self.active_pressures[pressure_id].resolved = True
            del self.active_pressures[pressure_id]
            logger.info(f"🌍 压力已解决: {pressure_id}")

    def evaluate_urgency(
        self, pressure_type: PressureType, context: dict[str, Any] | None = None
    ) -> UrgencyLevel:
        """
        评估压力紧急程度

        Args:
            pressure_type: 压力类型
            context: 上下文

        Returns:
            紧急程度
        """
        context = context or {}

        # 基于类型的基础紧急度
        base_urgency = {
            PressureType.ERROR_OCCURRED: UrgencyLevel.URGENT,
            PressureType.PERFORMANCE_ISSUE: UrgencyLevel.HIGH,
            PressureType.USER_REQUEST: UrgencyLevel.MEDIUM,
            PressureType.USER_FEEDBACK: UrgencyLevel.MEDIUM,
            PressureType.NOVELTY_DETECTED: UrgencyLevel.LOW,
        }

        urgency = base_urgency.get(pressure_type, UrgencyLevel.MEDIUM)

        # 根据上下文调整
        if context.get("user_satisfaction") == "low":
            urgency = UrgencyLevel(min(4, urgency.value + 1))

        if context.get("response_time", 0) > 5:  # 5秒以上
            urgency = UrgencyLevel(min(4, urgency.value + 1))

        if context.get("error_count", 0) > 3:
            urgency = UrgencyLevel.URGENT

        return urgency

    def trigger_adaptation(self, pressure: EnvironmentalPressure) -> AdaptationAction:
        """
        触发适应性行动

        Args:
            pressure: 环境压力

        Returns:
            适应性行动
        """
        action_id = f"action_{datetime.now().timestamp()}"

        # 根据压力类型决定行动
        action_type, description, confidence = self._decide_adaptation(pressure)

        action = AdaptationAction(
            action_id=action_id,
            pressure_id=pressure.pressure_id,
            description=description,
            action_type=action_type,
            confidence=confidence,
        )

        self.adaptation_history.append(action)

        logger.info(f"🌍 适应性行动: {description}")

        return action

    def _decide_adaptation(self, pressure: EnvironmentalPressure) -> tuple[str, str, float]:
        """
        决定适应性行动

        Args:
            pressure: 环境压力

        Returns:
            (行动类型, 描述, 置信度)
        """
        # 根据压力类型决定行动
        if pressure.pressure_type == PressureType.USER_REQUEST:
            return ("optimize_response", f"优化对用户请求'{pressure.description}'的响应", 0.8)

        elif pressure.pressure_type == PressureType.PERFORMANCE_ISSUE:
            return ("performance_optimization", f"优化性能问题: {pressure.description}", 0.9)

        elif pressure.pressure_type == PressureType.ERROR_OCCURRED:
            return ("error_handling", f"处理错误: {pressure.description}", 0.95)

        elif pressure.pressure_type == PressureType.USER_FEEDBACK:
            satisfaction = pressure.metadata.get("satisfaction", "neutral")
            if satisfaction == "low":
                return ("system_improvement", "根据用户反馈改进系统", 0.7)
            else:
                return ("maintain_status", "维持当前状态", 0.5)

        elif pressure.pressure_type == PressureType.NOVELTY_DETECTED:
            return ("learn_pattern", f"学习新模式: {pressure.description}", 0.6)

        else:
            return ("general_adaptation", "一般性适应", 0.5)

    def predict_pressure(self) -> list[dict[str, Any]]:
        """
        预测未来压力

        Returns:
            预测的压力列表
        """
        predictions = []

        # 基于时间的预测
        current_hour = datetime.now().hour

        for rule_name, rule in self.prediction_rules["time_based"].items():
            hour_range = rule["hour_range"]
            if hour_range[0] <= current_hour <= hour_range[1]:
                predictions.append(
                    {
                        "type": "time_based",
                        "rule": rule_name,
                        "likely_pressure": rule["likely_pressure"],
                        "suggested_action": rule["suggested_action"],
                        "confidence": 0.7,
                    }
                )

        # 基于频率的预测
        for pressure_type, pressures in self.pressure_patterns.items():
            if len(pressures) >= self.prediction_rules["frequency_based"]["threshold"]:
                recent = pressures[-3:]  # 最近3次
                # 检查是否连续发生
                timestamps = [datetime.fromisoformat(p.timestamp) for p in recent]
                # 如果在短时间内连续发生
                if len(timestamps) >= 2:
                    time_diff = (timestamps[-1] - timestamps[0]).total_seconds()
                    if time_diff < 3600:  # 1小时内
                        predictions.append(
                            {
                                "type": "frequency_based",
                                "pressure_type": pressure_type,
                                "pattern": "repeated_pressure",
                                "suggested_action": "优化该功能",
                                "confidence": 0.8,
                            }
                        )

        return predictions

    def get_environment_status(self) -> dict[str, Any]:
        """获取环境状态"""
        # 统计压力类型
        pressure_types = Counter(p.pressure_type.value for p in self.pressure_history)

        # 统计紧急程度
        urgency_levels = Counter(p.urgency.value for p in self.active_pressures.values())

        # 适应行动统计
        action_types = Counter(a.action_type for a in self.adaptation_history)

        return {
            "active_pressures": len(self.active_pressures),
            "total_pressures_detected": len(self.pressure_history),
            "pressure_type_distribution": dict(pressure_types),
            "active_urgency_distribution": dict(urgency_levels),
            "total_adaptations": len(self.adaptation_history),
            "adaptation_type_distribution": dict(action_types),
            "predictions": self.predict_pressure(),
        }


# 全局单例
_environment_sensor_instance = None


def get_environment_sensor() -> EnvironmentSensor:
    """获取环境感知系统单例"""
    global _environment_sensor_instance
    if _environment_sensor_instance is None:
        _environment_sensor_instance = EnvironmentSensor()
    return _environment_sensor_instance


# 测试代码
async def main():
    """测试环境感知系统"""

    print("\n" + "=" * 60)
    print("🌍 环境感知系统测试")
    print("=" * 60 + "\n")

    sensor = get_environment_sensor()

    # 测试1:检测压力
    print("📝 测试1: 检测环境压力")
    sensor.detect_pressure(
        pressure_type=PressureType.USER_REQUEST,
        description="用户请求专利分析",
        urgency=UrgencyLevel.MEDIUM,
        source="用户输入",
    )

    sensor.detect_pressure(
        pressure_type=PressureType.PERFORMANCE_ISSUE,
        description="响应时间过长",
        urgency=UrgencyLevel.HIGH,
        source="系统监控",
    )

    print("✅ 压力检测完成\n")

    # 测试2:触发适应
    print("📝 测试2: 触发适应性行动")
    for pressure in sensor.active_pressures.values():
        action = sensor.trigger_adaptation(pressure)
        print(f"行动: {action.description}")
    print()

    # 测试3:预测压力
    print("📝 测试3: 预测未来压力")
    predictions = sensor.predict_pressure()
    print(f"预测数量: {len(predictions)}")
    for pred in predictions:
        print(f"• {pred}")
    print()

    # 测试4:环境状态
    print("📝 测试4: 环境状态")
    status = sensor.get_environment_status()
    print(json.dumps(status, ensure_ascii=False, indent=2))

    print("\n✅ 测试完成!")


# 入口点: @async_main装饰器已添加到main函数
