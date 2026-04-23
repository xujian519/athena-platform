#!/usr/bin/env python3
from __future__ import annotations
"""
统一提示词管理器 - Lyra与L1-L4系统的统一管理
Unified Prompt Manager - Unified Management for Lyra and L1-L4 Systems

集成两个提示词系统:
1. L1-L4系统 - 智能体角色定义和提示词 (角色层)
2. Lyra系统 - 提示词优化和输出层优化 (输出层)

核心理念:
- L1-L4定义"智能体是谁,会什么"
- Lyra优化"智能体应该怎么说"
- 两者互补,协同工作

作者: 小诺·双鱼公主
创建时间: 2026-01-07
版本: v1.0.0
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 导入L1-L4系统
try:
    from core.agents.prompts.xiaona_prompts import XiaonaPrompts

    L1L4_AVAILABLE = True
except ImportError:
    L1L4_AVAILABLE = False
    logging.warning("L1-L4系统未找到,将使用备用方案")

# 导入Lyra系统 - 使用依赖注入
# TODO: 迁移到依赖注入模式
# from core.interfaces.prompt_optimizer import PromptOptimizer
# from config.dependency_injection import DIContainer
try:
    # TODO: ARCHITECTURE - 需要迁移到依赖注入模式
from services.ai_services.lyra_claude_integration import LyraClaudeIntegration
    LYRA_AVAILABLE = True
    # 暂时保留直接导入，待后续重构为依赖注入
except ImportError:
    LYRA_AVAILABLE = False
    logging.warning("Lyra系统未找到,将使用备用方案")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class PromptFormat(Enum):
    """提示词格式"""

    MARKDOWN = "markdown"  # L1-L4系统使用
    JSON = "json"  # Lyra系统使用


class PromptType(Enum):
    """提示词类型"""

    AGENT_ROLE = "agent_role"  # 智能体角色定义 (L1-L4)
    OUTPUT_OPTIMIZATION = "output_opt"  # 输出优化 (Lyra)
    COMBINED = "combined"  # 组合使用


@dataclass
class PromptLoadRequest:
    """提示词加载请求"""

    agent: str  # 智能体名称 (xiaonuo, xiaona, etc.)
    layers: Optional[list[str]] = None  # L1-L4层列表
    format: PromptFormat = PromptFormat.MARKDOWN
    type: PromptType = PromptType.AGENT_ROLE


@dataclass
class PromptOptimizeRequest:
    """提示词优化请求 (Lyra)"""

    content: str  # 要优化的内容
    target_ai: str = "ChatGPT"  # 目标AI
    mode: str = "BASIC"  # BASIC/DETAIL
    context: Optional[str] = None  # 上下文
    constraints: Optional[list[str]] = None  # 约束条件


@dataclass
class UnifiedPromptResult:
    """统一提示词结果"""

    status: str  # success/error
    content: str  # 提示词内容
    format: PromptFormat  # 格式类型
    type: PromptType  # 提示词类型
    metadata: dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    quality_score: float = 0.0
    suggestions: list[str] = field(default_factory=list)


class UnifiedPromptManager:
    """
    统一提示词管理器

    核心功能:
    1. 统一加载接口 - 加载L1-L4或Lyra提示词
    2. 统一优化接口 - 使用Lyra优化提示词
    3. 组合处理流程 - L1-L4定义角色 + Lyra优化输出
    4. 格式转换 - JSON ↔ Markdown
    5. 缓存管理 - 提升性能
    """

    def __init__(self):
        """初始化统一提示词管理器"""
        logger.info("=" * 60)
        logger.info("🎀 统一提示词管理器初始化 v1.0.0")
        logger.info("=" * 60)

        # 1. L1-L4系统初始化
        self.l1l4_systems = {}
        if L1L4_AVAILABLE:
            self._init_l1l4_systems()
        else:
            logger.warning("⚠️ L1-L4系统未加载")

        # 2. Lyra系统初始化
        self.lyra_integration = None
        if LYRA_AVAILABLE:
            self._init_lyra_system()
        else:
            logger.warning("⚠️ Lyra系统未加载")

        # 3. 缓存
        self.prompt_cache: dict[str, UnifiedPromptResult] = {}
        self.cache_ttl = 3600  # 1小时

        # 4. 统计信息
        self.stats = {
            "total_loads": 0,
            "total_optimizations": 0,
            "total_combined": 0,
            "l1l4_loads": 0,
            "lyra_optimizations": 0,
        }

        logger.info(f"✅ L1-L4系统: {'已加载' if L1L4_AVAILABLE else '未加载'}")
        logger.info(f"✅ Lyra系统: {'已加载' if LYRA_AVAILABLE else '未加载'}")
        logger.info("=" * 60)
        logger.info("🎉 统一提示词管理器初始化完成!")
        logger.info("=" * 60)

    def _init_l1l4_systems(self) -> Any:
        """初始化L1-L4系统"""
        try:
            # 小娜提示词
            self.l1l4_systems["xiaona"] = XiaonaPrompts()

            # 可以添加更多智能体
            # self.l1l4_systems['xiaonuo'] = XiaonuoPrompts()

            logger.info(f"✅ 已加载 {len(self.l1l4_systems)} 个L1-L4系统")
        except Exception as e:
            logger.error(f"❌ L1-L4系统初始化失败: {e}")

    def _init_lyra_system(self) -> Any:
        """初始化Lyra系统"""
        try:
            self.lyra_integration = LyraClaudeIntegration()
            logger.info("✅ Lyra系统已加载")
        except Exception as e:
            logger.error(f"❌ Lyra系统初始化失败: {e}")

    async def load_prompt(
        self,
        agent: str,
        layers: Optional[list[str]] = None,
        format: PromptFormat = PromptFormat.MARKDOWN,
    ) -> UnifiedPromptResult:
        """
        统一加载接口 - 加载智能体提示词 (L1-L4系统)

        Args:
            agent: 智能体名称 (xiaona, xiaonuo, etc.)
            layers: 要加载的层 (L1, L2, L3, L4), None表示全部
            format: 格式类型 (MARKDOWN/JSON)

        Returns:
            UnifiedPromptResult: 提示词结果
        """
        start_time = datetime.now()
        self.stats["total_loads"] += 1
        self.stats["l1l4_loads"] += 1

        logger.info(f"📥 加载提示词: {agent}, 层: {layers or '全部'}")

        try:
            # 检查系统可用性
            if not L1L4_AVAILABLE:
                return UnifiedPromptResult(
                    status="error",
                    content="L1-L4系统未加载",
                    format=format,
                    type=PromptType.AGENT_ROLE,
                    metadata={"error": "L1L4_NOT_AVAILABLE"},
                )

            # 检查智能体是否存在
            if agent not in self.l1l4_systems:
                return UnifiedPromptResult(
                    status="error",
                    content=f"智能体 {agent} 不存在",
                    format=format,
                    type=PromptType.AGENT_ROLE,
                    metadata={"error": "AGENT_NOT_FOUND"},
                )

            # 加载提示词
            prompt_system = self.l1l4_systems[agent]

            if layers is None:
                # 加载全部层
                content = prompt_system.get_full_prompt()
            else:
                # 加载指定层
                content_parts = []
                for layer in layers:
                    layer_content = prompt_system.get_layer_prompt(layer)
                    if layer_content:
                        content_parts.append(layer_content)
                content = "\n\n".join(content_parts)

            processing_time = (datetime.now() - start_time).total_seconds()

            result = UnifiedPromptResult(
                status="success",
                content=content,
                format=format,
                type=PromptType.AGENT_ROLE,
                metadata={
                    "agent": agent,
                    "layers": layers or ["L1", "L2", "L3", "L4"],
                    "source": "l1l4_system",
                },
                processing_time=processing_time,
                quality_score=1.0,  # 静态提示词默认满分
                suggestions=["提示词已优化,可以直接使用"],
            )

            logger.info(f"✅ 提示词加载成功: {agent}, 耗时: {processing_time:.2f}秒")

            return result

        except Exception as e:
            logger.error(f"❌ 提示词加载失败: {e}")
            return UnifiedPromptResult(
                status="error",
                content=str(e),
                format=format,
                type=PromptType.AGENT_ROLE,
                metadata={"error": str(e)},
                processing_time=(datetime.now() - start_time).total_seconds(),
            )

    async def optimize_prompt(
        self,
        content: str,
        target_ai: str = "ChatGPT",
        mode: str = "BASIC",
        context: Optional[str] = None,
        constraints: Optional[list[str]] = None,
    ) -> UnifiedPromptResult:
        """
        统一优化接口 - 使用Lyra优化提示词

        Args:
            content: 要优化的内容
            target_ai: 目标AI模型
            mode: 优化模式 (BASIC/DETAIL)
            context: 上下文信息
            constraints: 约束条件

        Returns:
            UnifiedPromptResult: 优化结果
        """
        start_time = datetime.now()
        self.stats["total_optimizations"] += 1
        self.stats["lyra_optimizations"] += 1

        logger.info(f"🎨 优化提示词: 目标AI={target_ai}, 模式={mode}")

        try:
            # 检查系统可用性
            if not LYRA_AVAILABLE or self.lyra_integration is None:
                return UnifiedPromptResult(
                    status="error",
                    content="Lyra系统未加载",
                    format=PromptFormat.JSON,
                    type=PromptType.OUTPUT_OPTIMIZATION,
                    metadata={"error": "LYRA_NOT_AVAILABLE"},
                )

            # 调用Lyra优化
            result = self.lyra_integration.optimize_for_claude(
                user_input=content,
                target_ai=target_ai,
                mode=mode,
                context=context,
                constraints=constraints,
            )

            if result["status"] == "success":
                processing_time = (datetime.now() - start_time).total_seconds()

                return UnifiedPromptResult(
                    status="success",
                    content=result["optimized_prompt"],
                    format=PromptFormat.JSON,
                    type=PromptType.OUTPUT_OPTIMIZATION,
                    metadata={
                        "target_ai": target_ai,
                        "mode": mode,
                        "improvements": result["quality_metrics"]["improvements"],
                    },
                    processing_time=processing_time,
                    quality_score=result["quality_metrics"]["score"],
                    suggestions=result["suggestions"],
                )
            else:
                return UnifiedPromptResult(
                    status="error",
                    content=result.get("error", "优化失败"),
                    format=PromptFormat.JSON,
                    type=PromptType.OUTPUT_OPTIMIZATION,
                    metadata={"error": result.get("error")},
                    processing_time=(datetime.now() - start_time).total_seconds(),
                )

        except Exception as e:
            logger.error(f"❌ 提示词优化失败: {e}")
            return UnifiedPromptResult(
                status="error",
                content=str(e),
                format=PromptFormat.JSON,
                type=PromptType.OUTPUT_OPTIMIZATION,
                metadata={"error": str(e)},
                processing_time=(datetime.now() - start_time).total_seconds(),
            )

    async def process_with_both(
        self, user_request: str, agent: str = "xiaonuo", optimize: bool = True
    ) -> UnifiedPromptResult:
        """
        组合处理流程 - L1-L4定义角色 + Lyra优化输出

        工作流程:
        1. 加载智能体角色提示词 (L1-L4)
        2. 结合用户请求生成响应
        3. 使用Lyra优化响应表达
        4. 返回最终结果

        Args:
            user_request: 用户请求
            agent: 智能体名称
            optimize: 是否使用Lyra优化

        Returns:
            UnifiedPromptResult: 最终结果
        """
        start_time = datetime.now()
        self.stats["total_combined"] += 1

        logger.info(f"🔄 组合处理: 智能体={agent}, 优化={optimize}")
        logger.info(f"📝 用户请求: {user_request[:100]}...")

        try:
            # 步骤1: 加载智能体提示词
            prompt_result = await self.load_prompt(agent)

            if prompt_result.status != "success":
                return prompt_result

            logger.info(f"✅ 已加载智能体提示词: {agent}")

            # 步骤2: 结合用户请求 (模拟生成响应)
            # 实际应该调用LLM生成响应
            # 这里简化处理,直接返回提示词+请求
            base_response = f"""
# {agent}的响应

基于智能体提示词和用户请求,这里是响应内容:

**用户请求**: {user_request}

**智能体角色**: {agent}

**处理结果**: [这里应该是实际的响应内容]

[注: 这是组合处理的示例,实际应该调用LLM生成完整响应]
            """.strip()

            # 步骤3: 使用Lyra优化 (如果需要)
            if optimize and LYRA_AVAILABLE:
                logger.info("🎨 使用Lyra优化响应...")
                optimize_result = await self.optimize_prompt(
                    content=base_response,
                    target_ai="Claude",
                    mode="BASIC",
                    context=f"智能体: {agent}, 用户请求: {user_request[:50]}...",
                )

                if optimize_result.status == "success":
                    final_content = optimize_result.content
                    quality_score = optimize_result.quality_score
                    suggestions = optimize_result.suggestions
                else:
                    logger.warning(f"⚠️ Lyra优化失败,使用原始响应: {optimize_result.content}")
                    final_content = base_response
                    quality_score = 0.5
                    suggestions = ["Lyra优化失败,使用原始响应"]
            else:
                final_content = base_response
                quality_score = 0.8
                suggestions = ["未使用Lyra优化"]

            processing_time = (datetime.now() - start_time).total_seconds()

            result = UnifiedPromptResult(
                status="success",
                content=final_content,
                format=PromptFormat.MARKDOWN,
                type=PromptType.COMBINED,
                metadata={
                    "agent": agent,
                    "user_request": user_request,
                    "optimized": optimize,
                    "workflow": "load_agent_prompt + generate_response + optimize_output",
                },
                processing_time=processing_time,
                quality_score=quality_score,
                suggestions=suggestions,
            )

            logger.info(f"✅ 组合处理完成,耗时: {processing_time:.2f}秒")

            return result

        except Exception as e:
            logger.error(f"❌ 组合处理失败: {e}")
            return UnifiedPromptResult(
                status="error",
                content=str(e),
                format=PromptFormat.MARKDOWN,
                type=PromptType.COMBINED,
                metadata={"error": str(e)},
                processing_time=(datetime.now() - start_time).total_seconds(),
            )

    def convert_format(
        self, content: str, from_format: PromptFormat, to_format: PromptFormat
    ) -> str:
        """
        格式转换 - JSON ↔ Markdown

        Args:
            content: 内容
            from_format: 源格式
            to_format: 目标格式

        Returns:
            str: 转换后的内容
        """
        if from_format == to_format:
            return content

        try:
            if from_format == PromptFormat.JSON and to_format == PromptFormat.MARKDOWN:
                # JSON → Markdown
                data = json.loads(content)

                # 转换为Markdown
                md_lines = []

                if "identity" in data:
                    id_data = data["identity"]
                    md_lines.append(f"# {id_data.get('name', 'Untitled')}")
                    md_lines.append(f"**{id_data.get('title', '')}**")
                    md_lines.append(f"> {id_data.get('description', '')}")
                    md_lines.append("")

                if "methodology" in data:
                    method_data = data["methodology"]
                    md_lines.append(f"## {method_data.get('title', 'Methodology')}")
                    md_lines.append("")

                    if "steps" in method_data:
                        for step in method_data["steps"]:
                            md_lines.append(f"### {step['name']}")
                            for action in step.get("actions", []):
                                md_lines.append(f"- {action}")
                            md_lines.append("")

                return "\n".join(md_lines)

            elif from_format == PromptFormat.MARKDOWN and to_format == PromptFormat.JSON:
                # Markdown → JSON (简化实现,实际需要更复杂的解析)
                # 这是一个简化版本,实际应该使用Markdown解析器
                return content  # 简化处理,保留原文

            else:
                return content

        except Exception as e:
            logger.error(f"❌ 格式转换失败: {e}")
            return content

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "statistics": self.stats,
            "systems": {
                "l1l4_available": L1L4_AVAILABLE,
                "lyra_available": LYRA_AVAILABLE,
                "l1l4_systems": len(self.l1l4_systems),
                "lyra_loaded": self.lyra_integration is not None,
            },
            "cache": {"cached_items": len(self.prompt_cache), "cache_ttl": self.cache_ttl},
            "generated_at": datetime.now().isoformat(),
        }


# ============================================================================
# 便捷函数
# ============================================================================

_manager_instance: UnifiedPromptManager | None = None


def get_unified_prompt_manager() -> UnifiedPromptManager:
    """获取统一提示词管理器单例"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = UnifiedPromptManager()
    return _manager_instance


async def load_agent_prompt(agent: Optional[str] = None, layers: Optional[list[str]] | None = None) -> str:
    """便捷函数: 加载智能体提示词"""
    manager = get_unified_prompt_manager()
    result = await manager.load_prompt(agent, layers)

    if result.status == "success":
        return result.content
    else:
        raise Exception(f"加载失败: {result.content}")


async def optimize_prompt(content: str, target_ai: str = "ChatGPT", mode: str = "BASIC") -> str:
    """便捷函数: 优化提示词"""
    manager = get_unified_prompt_manager()
    result = await manager.optimize_prompt(content, target_ai, mode)

    if result.status == "success":
        return result.content
    else:
        raise Exception(f"优化失败: {result.content}")


async def process_request(user_request: str, agent: str = "xiaonuo", optimize: bool = True) -> str:
    """便捷函数: 组合处理请求"""
    manager = get_unified_prompt_manager()
    result = await manager.process_with_both(user_request, agent, optimize)

    if result.status == "success":
        return result.content
    else:
        raise Exception(f"处理失败: {result.content}")


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "PromptFormat",
    "PromptLoadRequest",
    "PromptOptimizeRequest",
    "PromptType",
    "UnifiedPromptManager",
    "UnifiedPromptResult",
    "get_unified_prompt_manager",
    "load_agent_prompt",
    "optimize_prompt",
    "process_request",
]
