#!/usr/bin/env python3

"""
小诺意图识别模块
Xiaonuo Intent Analyzer

功能:
1. 深度理解用户真实意图
2. 提取关键实体信息
3. 识别任务类型和优先级
4. 构建完整意图对象

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import logging
import re
from datetime import datetime
from typing import Any

from .xiaonuo_planner_engine import Intent, IntentType

logger = logging.getLogger(__name__)


# ========== 意图模式配置 ==========


class IntentPattern:
    """意图识别模式"""

    # 查询类模式
    QUERY_PATTERNS = [
        r"查询|检索|搜索|找|查看|显示|列出|什么|如何|怎么",
        r"query|search|find|show|list|what|how|get",
    ]

    # 任务执行类模式
    TASK_PATTERNS = [
        r"执行|运行|启动|创建|生成|构建|部署|处理|完成",
        r"execute|run|start|create|generate|build|deploy|process",
    ]

    # 分析类模式
    ANALYSIS_PATTERNS = [
        r"分析|诊断|评估|检查|测试|验证|比较|统计",
        r"analyze|diagnose|evaluate|check|test|verify|compare",
    ]

    # 优化类模式
    OPTIMIZATION_PATTERNS = [
        r"优化|改进|提升|加速|精简|重构|调优",
        r"optimize|improve|enhance|accelerate|refactor|tune",
    ]

    # 协调类模式
    COORDINATION_PATTERNS = [
        r"协调|调度|安排|组织|分配|管理|计划",
        r"coordinate|schedule|arrange|organize|assign|manage",
    ]

    # 聊天类模式
    CHAT_PATTERNS = [
        r"你好|嗨|在吗|谢谢|辛苦|累|开心|不开心|聊聊天",
        r"hello|hi|thanks|tired|happy|sad|chat",
        r"❤️|💖|💕|🌸|✨|🎉",
    ]


# ========== 实体提取器 ==========


class EntityExtractor:
    """实体提取器"""

    # 智能体实体
    AGENT_ENTITIES = {
        "小娜": ["xiaona", "小娜", "天秤", "法律", "专利"],
        "小诺": ["xiaonuo", "小诺", "双鱼", "调度", "协调"],
        "小宸": ["xiaochen", "小宸", "运营", "内容"],
    }

    # 服务实体
    SERVICE_ENTITIES = {
        "专利检索": ["patent", "专利", "检索"],
        "数据分析": ["analysis", "分析", "数据"],
        "系统优化": ["optimize", "优化", "系统"],
        "IP管理": ["ip", "知识产权", "管理"],
    }

    # 时间实体
    TIME_PATTERNS = {
        "urgent": r"紧急|马上|立即|尽快|urgent|asap|immediately",
        "today": r"今天|today",
        "tomorrow": r"明天|tomorrow",
    }

    @classmethod
    def extract_entities(cls, text: str) -> dict[str, Any]:
        """提取实体"""
        entities = {
            "agents": [],
            "services": [],
            "time_constraints": [],
            "keywords": [],
        }

        text_lower = text.lower()

        # 提取智能体
        for agent_name, patterns in cls.AGENT_ENTITIES.items():
            if any(pattern in text_lower for pattern in patterns):
                entities["agents"].append(agent_name)

        # 提取服务
        for service_name, patterns in cls.SERVICE_ENTITIES.items():
            if any(pattern in text_lower for pattern in patterns):
                entities["services"].append(service_name)

        # 提取时间约束
        for time_type, pattern in cls.TIME_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                entities["time_constraints"].append(time_type)

        # 提取关键词
        # 中文分词简化版：按空格和标点分割
        words = re.split(r'[，。、！？\s,\.!?]+', text)
        entities["keywords"]] = [w for w in words if len(w) >= 2]

        return entities


# ========== 意图识别器 ==========


class IntentAnalyzer:
    """
    意图识别器

    核心功能:
    1. 意图类型识别
    2. 实体信息提取
    3. 置信度评估
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.pattern_config = IntentPattern()
        self.entity_extractor = EntityExtractor()

        # 意图识别历史（用于学习优化）
        self.recognition_history: list[dict[str, Any] = []

    async def analyze(
        self,
        user_input: str,
        context: dict[str, Any]]
    ) -> Intent:
        """
        分析用户意图

        Args:
            user_input: 用户输入
            context: 上下文信息

        Returns:
            Intent: 意图对象
        """
        self.logger.info(f"🔍 分析用户意图: {user_input[:50]}...")

        # 1. 识别意图类型
        intent_type = self._recognize_intent_type(user_input)

        # 2. 提取主要目标
        primary_goal = self._extract_primary_goal(user_input, intent_type)

        # 3. 提取子目标
        sub_goals = self._extract_sub_goals(user_input, intent_type)

        # 4. 提取实体
        entities = self.entity_extractor.extract_entities(user_input)

        # 5. 计算置信度
        confidence = self._calculate_confidence(user_input, intent_type, entities)

        # 6. 构建意图对象
        intent = Intent(
            intent_type=intent_type,
            primary_goal=primary_goal,
            sub_goals=sub_goals,
            entities=entities,
            confidence=confidence,
            context={
                **context,
                "original_input": user_input,
                "analyzed_at": datetime.now().isoformat(),
            }
        )

        # 7. 记录历史
        self.recognition_history.append({
            "input": user_input,
            "intent": intent,
            "timestamp": datetime.now(),
        })

        self.logger.info(f"   ✅ 意图识别完成: {intent_type.value} (置信度: {confidence:.2f})")
        return intent

    def _recognize_intent_type(self, text: str) -> IntentType:
        """识别意图类型"""
        text_lower = text.lower()

        # 按优先级检查各种模式
        # 聊天类优先级最高（情感交流）
        if self._match_patterns(text_lower, IntentPattern.CHAT_PATTERNS):
            return IntentType.CHAT

        # 查询类
        if self._match_patterns(text_lower, IntentPattern.QUERY_PATTERNS):
            return IntentType.QUERY

        # 任务执行类
        if self._match_patterns(text_lower, IntentPattern.TASK_PATTERNS):
            return IntentType.TASK

        # 分析类
        if self._match_patterns(text_lower, IntentPattern.ANALYSIS_PATTERNS):
            return IntentType.ANALYSIS

        # 优化类
        if self._match_patterns(text_lower, IntentPattern.OPTIMIZATION_PATTERNS):
            return IntentType.OPTIMIZATION

        # 协调类
        if self._match_patterns(text_lower, IntentPattern.COORDINATION_PATTERNS):
            return IntentType.COORDINATION

        # 默认未知
        return IntentType.UNKNOWN

    def _match_patterns(self, text: str, patterns: list[str]) -> bool:
        """匹配模式"""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _extract_primary_goal(self, text: str, intent_type: IntentType) -> str:
        """提取主要目标"""
        # 简化实现：返回输入的核心内容
        # 实际应该使用NLP技术提取主谓宾

        # 去除常见的修饰词
        text = re.sub(r"^(请|帮我|帮忙|麻烦|能否|可以|能不能)", "", text)
        text = re.sub(r"(吗|呢|吧|呀)$", "", text)

        # 提取核心句子（去除标点）
        core = re.sub(r'[，。、！？\s,\.!?]+', " ", text).strip()

        return core if core else "未指定目标"

    def _extract_sub_goals(self, text: str, intent_type: IntentType) -> list[str]:
        """提取子目标"""
        sub_goals = []

        # 根据意图类型生成子目标
        if intent_type == IntentType.QUERY:
            if "专利" in text or "patent" in text.lower():
                sub_goals = ["确定检索范围", "执行数据库查询", "整理结果"]
            else:
                sub_goals = ["理解查询需求", "检索相关信息", "返回结果"]

        elif intent_type == IntentType.TASK:
            sub_goals = ["分析任务需求", "准备执行环境", "执行任务", "验证结果"]

        elif intent_type == IntentType.ANALYSIS:
            sub_goals = ["收集数据", "执行分析", "生成报告"]

        elif intent_type == IntentType.OPTIMIZATION:
            sub_goals = ["诊断现状", "识别瓶颈", "设计方案", "实施优化"]

        elif intent_type == IntentType.COORDINATION:
            sub_goals = ["识别参与方", "分配任务", "监控执行", "整合结果"]

        return sub_goals

    def _calculate_confidence(
        self,
        text: str,
        intent_type: IntentType,
        entities: dict[str, Any]]
    ) -> float:
        """计算置信度"""
        confidence = 0.5  # 基础置信度

        # 意图类型明确性加分
        if intent_type != IntentType.UNKNOWN:
            confidence += 0.2

        # 实体存在加分
        if entities["agents"]:
            confidence += 0.1
        if entities["services"]:
            confidence += 0.1
        if entities["time_constraints"]:
            confidence += 0.05

        # 输入长度合理性
        if 5 <= len(text) <= 100:
            confidence += 0.05
        elif len(text) > 100:
            confidence -= 0.1  # 太长可能不清晰

        return min(1.0, confidence)

    def get_recognition_stats(self) -> dict[str, Any]:
        """获取识别统计信息"""
        if not self.recognition_history:
            return {"total_recognitions": 0}

        intent_distribution = {}
        confidence_sum = 0

        for record in self.recognition_history:
            intent_type = record["intent"].intent_type.value
            intent_distribution[intent_type] = intent_distribution.get(intent_type, 0) + 1
            confidence_sum += record["intent"].confidence

        return {
            "total_recognitions": len(self.recognition_history),
            "intent_distribution": intent_distribution,
            "average_confidence": confidence_sum / len(self.recognition_history),
        }

