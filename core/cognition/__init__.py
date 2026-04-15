#!/usr/bin/env python3
from __future__ import annotations
"""
认知与决策层模块
Cognition & Decision Module

作者: Athena AI系统
创建时间: 2025-12-04
版本: 3.0.0
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class CognitiveEngine:
    """认知引擎 - 集成Ollama NLP能力"""

    def __init__(self, agent_id: str, config: dict | None = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.initialized = False
        self.nlp_service = None

    async def initialize(self):
        """初始化认知引擎"""
        logger.info(f"🧠 启动认知引擎: {self.agent_id}")

        try:
            # 尝试使用新的NLP适配器
            from .nlp_adapter import NLPAdapter

            self.nlp_service = NLPAdapter(self.config.get("nlp", {}))
            await self.nlp_service.initialize()
            logger.info(f"✅ NLP适配器集成完成: {self.agent_id}")

        except Exception:
            try:
                from .ollama_integration import get_ollama_nlp_instance

                self.nlp_service = await get_ollama_nlp_instance(self.config.get("nlp", {}))
                logger.info(f"✅ Ollama NLP服务集成完成: {self.agent_id}")
            except Exception as e2:
                logger.warning(f"⚠️ 所有NLP服务初始化失败,使用基础认知功能: {e2}")
                self.nlp_service = None

        self.initialized = True

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        """处理认知输入"""
        if not self.initialized:
            raise RuntimeError("认知引擎未初始化")

        try:
            # 如果有NLP服务,使用增强处理
            if self.nlp_service:
                return await self._enhanced_processing(data)
            else:
                return await self._basic_processing(data)

        except Exception:
            return await self._basic_processing(data)

    async def _enhanced_processing(self, data) -> dict[str, Any]:
        """使用NLP服务的增强处理"""
        # 处理PerceptionResult对象
        if hasattr(data, "input"):
            input_text = str(data.input)
        elif hasattr(data, "get"):
            input_text = str(data.get("input", data))
        else:
            input_text = str(data)

        # 获取处理类型
        if hasattr(data, "type"):
            processing_type = data.type
        elif hasattr(data, "get"):
            processing_type = data.get("type", "general")
        else:
            processing_type = "general"

        if processing_type == "patent_analysis":
            # 专利分析
            result = await self.nlp_service.analyze_patent(input_text)
            return {
                "cognition": "enhanced_patent_analysis",
                "agent_id": self.agent_id,
                "nlp_result": result,
                "processing_type": "patent",
            }

        elif processing_type == "technical_reasoning":
            # 技术推理
            context = getattr(data, "context", "") if hasattr(data, "context") else ""
            result = await self.nlp_service.technical_reasoning(input_text, context)
            return {
                "cognition": "enhanced_technical_reasoning",
                "agent_id": self.agent_id,
                "nlp_result": result,
                "processing_type": "technical",
            }

        elif processing_type == "emotional_analysis":
            # 情感分析(优先使用专门方法)
            result = await self.analyze_emotion(input_text)
            return {
                "cognition": "enhanced_emotional_analysis",
                "agent_id": self.agent_id,
                "nlp_result": result,
                "processing_type": "emotional",
            }

        elif processing_type == "creative_writing":
            # 创意写作
            style = data.get("style", "story")
            result = await self.nlp_service.creative_writing(input_text, style)
            return {
                "cognition": "enhanced_creative_writing",
                "agent_id": self.agent_id,
                "nlp_result": result,
                "processing_type": "creative",
            }

        else:
            # 通用对话处理
            context = data.get("context", {})
            result = await self.nlp_service.conversation_response(input_text, context)
            return {
                "cognition": "enhanced_conversation",
                "agent_id": self.agent_id,
                "nlp_result": result,
                "processing_type": "conversation",
            }

    async def _basic_processing(self, data) -> dict[str, Any]:
        """基础认知处理(降级方案)"""
        # 处理PerceptionResult对象
        if hasattr(data, "input"):
            input_text = str(data.input)
        elif hasattr(data, "get"):
            input_text = str(data.get("input", data))
        else:
            input_text = str(data)

        # 获取处理类型
        if hasattr(data, "type"):
            processing_type = data.type
        elif hasattr(data, "get"):
            processing_type = data.get("type", "general")
        else:
            processing_type = "general"

        return {
            "cognition": "basic_processing",
            "agent_id": self.agent_id,
            "input_summary": input_text[:100] + "..." if len(input_text) > 100 else input_text,
            "processing_type": processing_type,
            "confidence": 0.8,
            "timestamp": datetime.now().isoformat(),
        }

    async def analyze_emotion(self, data: Any) -> dict[str, Any]:
        """情感分析"""
        if not self.initialized:
            raise RuntimeError("认知引擎未初始化")

        input_text = str(data)

        try:
            # 如果有NLP服务,使用增强情感分析
            if self.nlp_service:
                result = await self.nlp_service.emotional_analysis(input_text)
                return {
                    "analysis_type": "enhanced_emotional",
                    "input_text": input_text[:50] + "..." if len(input_text) > 50 else input_text,
                    "result": result,
                    "agent_id": self.agent_id,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                # 基础情感分析
                return await self._basic_emotion_analysis(input_text)

        except Exception:
            return await self._basic_emotion_analysis(input_text)

    async def _basic_emotion_analysis(self, input_text: str) -> dict[str, Any]:
        """基础情感分析"""
        # 简单的关键词检测
        positive_keywords = ["开心", "高兴", "快乐", "棒", "好", "爱", "谢谢"]
        negative_keywords = ["难过", "伤心", "生气", "愤怒", "不好", "累", "烦", "失望"]

        positive_count = sum(1 for word in positive_keywords if word in input_text)
        negative_count = sum(1 for word in negative_keywords if word in input_text)

        if positive_count > negative_count:
            emotion = "positive"
            intensity = min(0.8, 0.5 + positive_count * 0.1)
        elif negative_count > positive_count:
            emotion = "negative"
            intensity = min(0.8, 0.5 + negative_count * 0.1)
        else:
            emotion = "neutral"
            intensity = 0.5

        return {
            "analysis_type": "basic_emotional",
            "input_text": input_text[:50] + "..." if len(input_text) > 50 else input_text,
            "result": {
                "primary_emotion": emotion,
                "emotion_intensity": intensity,
                "emotional_complexity": "simple",
                "detection_method": "keyword_based",
            },
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
        }

    async def patent_analysis(self, patent_text: str) -> dict[str, Any]:
        """专利分析 - 新增方法"""
        if not self.initialized:
            raise RuntimeError("认知引擎未初始化")

        data = {"input": patent_text, "type": "patent_analysis"}
        return await self.process(data)

    async def technical_reasoning(self, problem: str, context: str = "") -> dict[str, Any]:
        """技术推理 - 新增方法"""
        if not self.initialized:
            raise RuntimeError("认知引擎未初始化")

        data = {"input": problem, "context": context, "type": "technical_reasoning"}
        return await self.process(data)

    async def creative_response(self, prompt: str, style: str = "story") -> dict[str, Any]:
        """创意响应生成 - 新增方法"""
        if not self.initialized:
            raise RuntimeError("认知引擎未初始化")

        data = {"input": prompt, "style": style, "type": "creative_writing"}
        return await self.process(data)

    async def conversation_processing(
        self, message: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """对话处理 - 新增方法"""
        if not self.initialized:
            raise RuntimeError("认知引擎未初始化")

        data = {"input": message, "context": context or {}, "type": "conversation"}
        return await self.process(data)

    async def reason(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """推理方法 - 用于测试"""
        if not self.initialized:
            raise RuntimeError("认知引擎未初始化")

        # 从输入数据中提取查询
        query = input_data.get("query", "")

        # 处理查询
        result = await self.process({"input": query, "type": "technical_reasoning"})

        return {
            "status": "success",
            "reasoning_result": result,
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
        }

    def register_callback(self, event_type: str, callback) -> None:
        """注册回调函数"""
        if not hasattr(self, "_callbacks"):
            self._callbacks = {}
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)

    async def shutdown(self):
        """关闭认知引擎"""
        logger.info(f"🔄 关闭认知引擎: {self.agent_id}")
        self.initialized = False

    @classmethod
    async def initialize_global(cls):
        """初始化全局实例"""
        if not hasattr(cls, "global_instance"):
            cls.global_instance = cls("global", {})
            await cls.global_instance.initialize()
        return cls.global_instance

    @classmethod
    async def shutdown_global(cls):
        """关闭全局实例"""
        if hasattr(cls, "global_instance") and cls.global_instance:
            await cls.global_instance.shutdown()
            del cls.global_instance


# 导入智能体设计模式组件
try:

    # 导入增强认知系统(保持向后兼容)
    from .athena_cognition_enhanced import (
        AthenaCognitionEnhanced,
        CognitionConfig,
        CognitionMode,
    )
    from .xiaonuo_cognition_enhanced import (
        XiaonuoCognitionConfig,
        XiaonuoCognitionEnhanced,
        XiaonuoCognitionMode,
    )
    from .xiaonuo_super_reasoning import (
        XiaonuoReasoningConfig,
        XiaonuoSuperReasoningEngine,
        XiaonuoThinkingMode,
    )

    __all__ = [
        # 智能体设计模式组件
        "AgenticTaskPlanner",
        "AthenaCognitionEnhanced",
        "AthenaSuperReasoningEngine",
        "ChainExecution",
        "ChainStep",
        "CognitionConfig",
        "CognitionMode",
        # 原有认知系统组件
        "CognitiveEngine",
        "ExecutionPlan",
        "PromptChainProcessor",
        "ReasoningConfig",
        "ReasoningMode",
        "TaskStep",
        "XiaonuoCognitionConfig",
        "XiaonuoCognitionEnhanced",
        "XiaonuoCognitionMode",
        "XiaonuoReasoningConfig",
        "XiaonuoSuperReasoningEngine",
        "XiaonuoThinkingMode",
    ]

    # Minitap式进度追踪 - Phase 1新增
    try:
        from .plan_executor import (
            ExecutionResult,
            PlanExecutor,
            StepResult,
            StepStatus,
            TaskStatus,
            create_executor,
        )
        __all__.extend([
            "PlanExecutor",
            "StepStatus",
            "TaskStatus",
            "StepResult",
            "ExecutionResult",
            "create_executor",
        ])
    except ImportError:
        logger.warning("⚠️ PlanExecutor 模块未加载")

except ImportError:
    # 导入原有组件作为后备
    from .athena_cognition_enhanced import (
        AthenaCognitionEnhanced,
        CognitionConfig,
        CognitionMode,
    )
    from .xiaonuo_cognition_enhanced import (
        XiaonuoCognitionConfig,
        XiaonuoCognitionEnhanced,
        XiaonuoCognitionMode,
    )
    from .xiaonuo_super_reasoning import (
        XiaonuoReasoningConfig,
        XiaonuoSuperReasoningEngine,
        XiaonuoThinkingMode,
    )

    __all__ = [
        "AthenaCognitionEnhanced",
        "AthenaSuperReasoningEngine",
        "CognitionConfig",
        "CognitionMode",
        "CognitiveEngine",
        "ReasoningConfig",
        "ReasoningMode",
        "XiaonuoCognitionConfig",
        "XiaonuoCognitionEnhanced",
        "XiaonuoCognitionMode",
        "XiaonuoReasoningConfig",
        "XiaonuoSuperReasoningEngine",
        "XiaonuoThinkingMode",
    ]
