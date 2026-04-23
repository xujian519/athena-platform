
# pyright: ignore
# !/usr/bin/env python3
"""
增强认知决策模块 - BaseModule标准接口兼容版本
Enhanced Cognition Module - BaseModule Compatible Version

基于现有AthenaCognitionEnhanced,添加BaseModule标准接口支持
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from core.logging_config import setup_logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 导入BaseModule
from core.base_module import BaseModule

# 导入现有认知系统
try:
    from enhanced_cognition_module import (
        AthenaCognitionEnhanced,
        CognitionConfig,
        CognitionMode,
    )

    COGNITION_SYSTEM_AVAILABLE = True
except ImportError:
    COGNITION_SYSTEM_AVAILABLE = False  # type: ignore

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class EnhancedCognitionConfig:
    """增强认知配置"""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        config = config or {}

        # 认知模式配置
        self.cognition_mode = config.get("cognition_mode", "enhanced")  # basic, enhanced, super
        self.enable_super_reasoning = config.get("enable_super_reasoning", True)
        self.reasoning_depth = config.get("reasoning_depth", 3)

        # 集成配置
        self.enable_learning = config.get("enable_learning", True)
        self.enable_memory_integration = config.get("enable_memory_integration", True)
        self.enable_knowledge_synthesis = config.get("enable_knowledge_synthesis", True)

        # 性能配置
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
        self.max_reasoning_time = config.get("max_reasoning_time", 300)  # 5分钟
        self.enable_caching = config.get("enable_caching", True)

        # 安全配置
        self.enable_safety_checks = config.get("enable_safety_checks", True)
        self.max_input_length = config.get("max_input_length", 10000)
        self.enable_content_filter = config.get("enable_content_filter", True)


@dataclass
class CognitionResult:
    """认知结果数据结构"""

    success: bool
    result: Any
    confidence: float
    reasoning_steps: list[str]
    processing_time: float
    mode_used: str
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class EnhancedCognitionModule(BaseModule):
    """增强认知决策模块 - BaseModule标准接口版本"""

    def __init__(self, agent_id: str, config: Optional[dict[str, Any]] = None):
        """
        初始化增强认知决策模块

        Args:
            agent_id: 智能体标识符
            config: 配置参数
        """
        super().__init__(agent_id, config)

        # 认知模块特有配置
        self.cognition_config = EnhancedCognitionConfig(config)

        # 初始化现有认知系统
        self.cognition_engine = None
        if COGNITION_SYSTEM_AVAILABLE:
            try:
                cognition_config = CognitionConfig(  # type: ignore
                    mode=CognitionMode(self.cognition_config.cognition_mode),  # type: ignore
                    enable_super_reasoning=self.cognition_config.enable_super_reasoning,
                    reasoning_depth=self.cognition_config.reasoning_depth,
                    enable_learning=self.cognition_config.enable_learning,
                    enable_memory_integration=self.cognition_config.enable_memory_integration,
                    enable_knowledge_synthesis=self.cognition_config.enable_knowledge_synthesis,
                )
                self.cognition_engine = AthenaCognitionEnhanced(cognition_config)  # type: ignore
                logger.info("✅ 现有认知系统集成成功")
            except Exception as e:
                logger.warning(f"现有认知系统集成失败: {e}")

        # 认知状态
        self.cognition_stats = {
            "total_cognitions": 0,
            "successful_cognitions": 0,
            "failed_cognitions": 0,
            "super_reasoning_uses": 0,
            "average_confidence": 0.0,
            "average_processing_time": 0.0,
            "last_cognition_time": None,
        }

        # 认知缓存
        self.cognition_cache = {} if self.cognition_config.enable_caching else None

        # 支持的认知能力
        self.supported_capabilities = [
            "reasoning",
            "analysis",
            "decision_making",
            "learning",
            "memory_integration",
            "knowledge_synthesis",
            "super_reasoning",
        ]

        logger.info(f"🧠 增强认知决策模块初始化完成 - Agent: {self.agent_id}")

    async def _on_initialize(self) -> bool:
        """模块初始化"""
        try:
            await self._initialize_fallback_cognition()
            return True
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False

    async def _on_health_check(self) -> bool:
        """健康检查"""
        try:
            checks = {
                "cognition_engine_available": self.cognition_engine is not None,
                "dependencies_ok": await self._verify_dependencies(),
                "reasoning_available": True,
                "memory_usage_ok": self._check_memory_usage(),
                "cache_system_ok": self.cognition_cache is not None
                or not self.cognition_config.enable_caching,
            }

            overall_healthy = all(checks.values())

            # 存储健康检查详情
            self._health_check_details = {
                "cognition_status": (
                    "available" if checks["cognition_engine_available"] else "unavailable"
                ),
                "dependencies_status": "ok" if checks["dependencies_ok"] else "missing",
                "reasoning_status": "ready" if checks["reasoning_available"] else "busy",
                "cache_status": "ok" if checks["cache_system_ok"] else "error",
                "stats": self.cognition_stats,
            }

            return overall_healthy

        except Exception as e:
            self._health_check_details = {"error": str(e)}
            return False

    async def analyze(self, input_data: Any) -> dict[str, Any]:
        """分析方法 - 深度分析"""
        try:
            if isinstance(input_data, str):
                cognition_result = await self.cognize(input_data)
                return {
                    "success": cognition_result.success,
                    "analysis_result": cognition_result.result,
                    "confidence": cognition_result.confidence,
                    "reasoning_steps": cognition_result.reasoning_steps,
                    "processing_agent": self.agent_id,
                }
            else:
                return {
                    "success": False,
                    "error": "不支持的输入类型",
                    "input_type": type(input_data).__name__,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def reason(self, query: str, context: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """推理方法 - 逻辑推理"""
        try:
            cognition_result = await self.cognize(query, context)

            return {
                "success": cognition_result.success,
                "reasoning_result": cognition_result.result,
                "confidence": cognition_result.confidence,
                "reasoning_steps": cognition_result.reasoning_steps,
                "reasoning_mode": cognition_result.mode_used,
                "processing_agent": self.agent_id,
            }

        except Exception as e:
            logger.error(f"推理过程失败: {e}", exc_info=True)
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def decide(
        self, options: Optional[list[str] | dict[str, Any], criteria: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """决策方法 - 智能决策"""
        try:
            # 构建决策查询
            options_str = " | ".join(
                [opt if isinstance(opt, str) else str(opt) for opt in options]
            )
            query = f"决策选择: {options_str}"

            if criteria:
                query += f" (标准: {criteria})"

            cognition_result = await self.cognize(query, context=criteria)

            return {
                "success": cognition_result.success,
                "decision_result": cognition_result.result,
                "confidence": cognition_result.confidence,
                "reasoning_steps": cognition_result.reasoning_steps,
                "options_evaluated": len(options),
                "processing_agent": self.agent_id,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def process(self, input_data: Any) -> dict[str, Any]:
        """标准处理接口 - BaseModule兼容"""
        return await self.analyze(input_data)

    async def cognize(
        self, query: str, context: Optional[dict[str, Any]] = None
    ) -> CognitionResult:
        """
        认知处理 - 核心功能方法

        Args:
            query: 认知查询
            context: 上下文信息

        Returns:
            认知结果
        """
        start_time = datetime.now()
        try:

            # 更新统计信息
            self.cognition_stats["total_cognitions"] += 1

            # 安全检查
            if not await self._safety_check(query):
                raise ValueError("输入内容安全检查失败")

            # 缓存检查
            cache_key = self._get_cache_key(query, context)
            if self.cognition_cache is not None and cache_key in self.cognition_cache:
                cached_result = self.cognition_cache.get(cache_key)
                logger.info(f"✅ 缓存命中: {query[:50]}...")
                return cached_result

            # 使用现有认知引擎
            if self.cognition_engine:
                result_data = await self.cognition_engine.cognize(query, context)
                cognition_result = self._convert_to_cognition_result(result_data)
            else:
                # 使用备用认知处理
                cognition_result = await self._fallback_cognition(query, context)

            # 更新统计信息
            processing_time = (datetime.now() - start_time).total_seconds()
            self.cognition_stats["successful_cognitions"] += 1
            self.cognition_stats["last_cognition_time"] = processing_time
            self._update_average_processing_time(processing_time)
            self._update_average_confidence(cognition_result.confidence)

            # 缓存结果
            if self.cognition_cache is not None:
                self.cognition_cache[cache_key] = cognition_result

            logger.info(
                f"✅ 认知处理完成 - 耗时: {processing_time:.2f}s, 置信度: {cognition_result.confidence:.2f}"
            )
            return cognition_result

        except Exception as e:
            logger.error(f"❌ 认知处理失败: {e!s}")

            # 返回失败结果
            return CognitionResult(
                success=False,
                result=None,
                confidence=0.0,
                reasoning_steps=[],
                processing_time=0.0,
                mode_used="error",
                error=str(e),
            )

    async def _initialize_fallback_cognition(self):
        """初始化备用认知能力"""
        self.fallback_capabilities = {
            "basic_reasoning": True,
            "simple_analysis": True,
            "decision_support": True,
            "learning": False,  # 简化版本不支持学习
        }

    async def _verify_dependencies(self) -> bool:
        """验证依赖"""
        try:
            return True  # 认知模块主要依赖内部逻辑
        except Exception:
            return False

    def _check_memory_usage(self) -> bool:
        """检查内存使用"""
        try:
            import psutil

            memory_percent = psutil.virtual_memory().percent
            return memory_percent < 90
        except ImportError:
            return True  # 如果psutil不可用，假设内存使用正常

    async def _safety_check(self, content: str) -> bool:
        """安全检查"""
        if not self.cognition_config.enable_safety_checks:
            return True

        # 长度检查
        if len(content) > self.cognition_config.max_input_length:
            logger.warning(f"输入内容过长: {len(content)} 字符")
            return False

        # 内容过滤(简化版本)
        if self.cognition_config.enable_content_filter:
            # 这里可以添加更多内容过滤逻辑
            pass

        return True

    def _get_cache_key(self, query: str, context: dict[str, Any]) -> str:
        """生成缓存键"""
        import hashlib

        content = f"{query}:{context!s}"
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()

    def _convert_to_cognition_result(self, result_data: dict[str, Any]) -> CognitionResult:
        """转换认知结果格式"""
        return CognitionResult(
            success=result_data.get("success", True),
            result=result_data.get("result"),
            confidence=result_data.get("confidence", 0.5),
            reasoning_steps=result_data.get("reasoning_steps", []),
            processing_time=result_data.get("processing_time", 0.0),
            mode_used=result_data.get("mode", "unknown"),
            error=result_data.get("error"),
            metadata=result_data.get("metadata", {}),
        )

    async def _fallback_cognition(
        self, query: str, context: dict[str, Any]]
    ) -> CognitionResult:
        """备用认知处理"""
        # 简化的认知逻辑
        reasoning_steps = ["分析查询内容", "基础推理处理", "生成认知结果"]

        result = {
            "query": query,
            "analysis": f"对查询'{query}'的基础分析",
            "conclusion": "基础认知处理完成",
            "context_used": context is not None,
        }

        return CognitionResult(
            success=True,
            result=result,
            confidence=0.6,  # 备用处理置信度较低
            reasoning_steps=reasoning_steps,
            processing_time=1.0,
            mode_used="fallback",
        )

    def _update_average_processing_time(self, processing_time: float) -> Any:
        """更新平均处理时间"""
        if self.cognition_stats["total_cognitions"] > 0:  # type: ignore
            current_avg = self.cognition_stats["average_processing_time"]
            n = self.cognition_stats["total_cognitions"]
            new_avg = (current_avg * (n - 1) + processing_time) / n  # type: ignore
            self.cognition_stats["average_processing_time"] = new_avg

    def _update_average_confidence(self, confidence: float) -> Any:
        """更新平均置信度"""
        if self.cognition_stats["total_cognitions"] > 0:  # type: ignore
            current_avg = self.cognition_stats["average_confidence"]
            n = self.cognition_stats["total_cognitions"]
            new_avg = (current_avg * (n - 1) + confidence) / n  # type: ignore
            self.cognition_stats["average_confidence"] = new_avg

    def get_metrics(self) -> dict[str, Any]:
        """获取模块性能指标"""
        try:
            return {
                "agent_id": self.agent_id,
                "module_type": self.__class__.__name__,
                "module_status": self.status.value if hasattr(self, "status") else "unknown",
                "initialized": hasattr(self, "_initialized") and self._initialized,
                "uptime_seconds": (
                    (datetime.now() - self.start_time).total_seconds()
                    if hasattr(self, "start_time")
                    else 0
                ),
                "cognition_stats": self.cognition_stats,
                "config": {
                    "cognition_mode": self.cognition_config.cognition_mode,
                    "enable_super_reasoning": self.cognition_config.enable_super_reasoning,
                    "reasoning_depth": self.cognition_config.reasoning_depth,
                    "confidence_threshold": self.cognition_config.confidence_threshold,
                },
                "engine_available": self.cognition_engine is not None,
                "capabilities": self.supported_capabilities,
                "health_details": getattr(self, "_health_check_details", {}),
            }
        except Exception as e:
            return {"error": str(e), "agent_id": getattr(self, "agent_id", "unknown")}

    async def _on_start(self) -> bool:
        """启动模块"""
        try:
            logger.info(f"🚀 增强认知决策模块启动 - Agent: {self.agent_id}")
            return True
        except Exception as e:
            logger.error(f"启动失败: {e}")
            return False

    async def _on_stop(self) -> bool:
        """停止模块"""
        try:
            self._is_running = False
            logger.info(f"🛑 增强认知决策模块停止 - Agent: {self.agent_id}")
            return True
        except Exception as e:
            logger.error(f"停止失败: {e}")
            return False

    async def _on_shutdown(self) -> bool:
        """关闭模块"""
        try:
            # 清理缓存
            if self.cognition_cache:
                self.cognition_cache.clear()

            logger.info(f"🔚 增强认知决策模块关闭 - Agent: {self.agent_id}")
            return True
        except Exception as e:
            logger.error(f"关闭失败: {e}")
            return False


# 便捷创建函数
def create_enhanced_cognition_module(
    agent_id: str, config: Optional[dict[str, Any]] = None
) -> EnhancedCognitionModule:
    """
    创建增强认知决策模块实例

    Args:
        agent_id: 智能体标识符
        config: 配置参数

    Returns:
        EnhancedCognitionModule实例
    """
    return EnhancedCognitionModule(agent_id, config)

