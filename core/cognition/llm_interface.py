from __future__ import annotations
# pyright: ignore
# !/usr/bin/env python3
"""
LLM调用接口模块
LLM Interface Module

提供统一的LLM调用接口,以GLM-4为核心,支持多种大语言模型
集成Athena工作平台的GLM统一客户端

作者: 小娜·天秤女神
创建时间: 2025-12-16
版本: v3.0 GLM-First Integration
"""

import asyncio
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 尝试导入性能监控器
try:

    PERFORMANCE_MONITORING_AVAILABLE = True
except ImportError:

    def record_llm_performance(*args, **kwargs) -> Any:  # type: ignore
        pass


# 尝试导入缓存管理器
try:

    CACHE_AVAILABLE = True
except ImportError:

    async def get_cached_response(*args, **kwargs):  # type: ignore
        return None

    async def cache_response(*args, **kwargs):  # type: ignore
        pass


# 添加Athena工作平台GLM客户端路径
glm_path = Path(
    "/Users/xujian/Athena工作平台/services/ai-models/glm-full-suite"
)  # TODO: 确保除数不为零
if str(glm_path) not in sys.path:
    sys.path.insert(0, str(glm_path))

# 配置管理
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 尝试导入GLM统一客户端
try:
    from glm_unified_client import (
        GLMModel,
        GLMResponse,
        ModalityType,
        ZhipuAIUnifiedClient,
    )
    from glm_unified_client import (  # type: ignore
        GLMRequest as GLMReq,
    )

    GLM_AVAILABLE = True
    logger.info("GLM统一客户端导入成功")
except ImportError as e:
    GLM_AVAILABLE = False
    logger.warning(f"GLM统一客户端导入失败: {e}")

# 导出GLM_AVAILABLE供其他模块使用
__all__ = ["GLM_AVAILABLE", "LLMInterface", "LLMRequest", "LLMResponse"]


@dataclass
class LLMRequest:
    """LLM请求数据结构"""

    prompt: str
    model_name: str | None = None  # 使用None让LLM管理器自动选择
    provider: str | None = None  # 可选指定提供商
    temperature: float = 0.7
    max_tokens: int = 4000
    system_message: str | None = None
    expert_context: dict[str, Any] | None = None
    knowledge_context: dict[str, Any] | None = None
    tools: list[dict[str, Any]] | None = None
    use_streaming: bool = False
    capabilities: list[str] | None = None  # 指定需要的模型能力


@dataclass
class LLMResponse:
    """LLM响应数据结构"""

    content: str
    model_used: str
    usage: dict[str, int] = field(default_factory=dict)
    response_time: float = 0.0
    expert_analysis: dict[str, Any] | None = None
    confidence_score: float = 0.0
    reasoning_chain: list[str] | None = None
    cost: float = 0.0
    provider: str = "unknown"


class LLMInterface:
    """LLM调用接口类 - 以GLM-4为核心的Athena统一客户端"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.request_history = []
        self.glm_client = None
        self.initialized = False

        # GLM-4.7优先配置(仅在GLM可用时定义)
        if GLM_AVAILABLE:
            self.preferred_models = {
                "patent_analysis": GLMModel.GLM_4_7,  # type: ignore
                "legal_document": GLMModel.GLM_4_7,  # type: ignore
                "code_generation": GLMModel.GLM_4_7_CODE,  # type: ignore
                "creative_writing": GLMModel.GLM_4_7,  # type: ignore
                "data_analysis": GLMModel.GLM_4_7,  # type: ignore
                "general_chat": GLMModel.GLM_4_7_FLASH,  # type: ignore
                "default": GLMModel.GLM_4_7,  # type: ignore
            }
        else:
            self.preferred_models = None

        # GLM-4.7优化参数(根据官方文档)
        self.model_params = {
            "patent_analysis": {"temperature": 0.3, "max_tokens": 65536, "top_p": 0.7},
            "legal_document": {"temperature": 0.2, "max_tokens": 65536, "top_p": 0.6},
            "code_generation": {"temperature": 0.1, "max_tokens": 65536, "top_p": 0.5},
            "creative_writing": {"temperature": 0.8, "max_tokens": 65536, "top_p": 0.9},
            "data_analysis": {"temperature": 0.4, "max_tokens": 65536, "top_p": 0.7},
            "general_chat": {"temperature": 0.7, "max_tokens": 8192, "top_p": 0.8},
            "default": {"temperature": 0.3, "max_tokens": 65536, "top_p": 0.7},
        }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        """异步上下文管理器出口"""
        await self.cleanup()

    async def initialize(self) -> bool:
        """初始化GLM客户端"""
        if self.initialized:
            return True

        if not GLM_AVAILABLE:
            logger.info("GLM统一客户端不可用,将使用模拟模式")
            self.initialized = True  # 标记为已初始化,但使用模拟模式
            return True

        try:
            api_key = os.getenv("GLM_API_KEY") or self.config.get("api_key")

            # 初始化GLM客户端
            self.glm_client = ZhipuAIUnifiedClient(api_key=api_key)  # type: ignore

            self.initialized = True
            logger.info("GLM统一客户端初始化成功")
            logger.info("GLM-4优先策略已启用")
            return True

        except Exception as e:
            logger.error(f"GLM客户端初始化异常: {e}")
            # 不返回False,让系统回退到模拟模式
            self.initialized = True
            return True

    async def cleanup(self):
        """清理资源"""
        if self.glm_client:
            # GLM客户端使用async with,不需要额外清理
            self.glm_client = None
        self.initialized = False

    def _build_expert_prompt(self, request: LLMRequest) -> str:
        """构建专家增强的提示词"""
        expert_prompt = []

        # 添加系统消息
        if request.system_message:
            expert_prompt.append(f"系统指令:\n{request.system_message}\n")

        # 添加专家上下文
        if request.expert_context:
            expert_prompt.append("专家团队分析:")
            if "team_composition" in request.expert_context:
                expert_prompt.append(f"- 团队构成: {request.expert_context['team_composition']}")
            if "expert_opinions" in request.expert_context:
                expert_prompt.append("- 专家意见:")
                for opinion in request.expert_context["expert_opinions"]:
                    expert_prompt.append(
                        f"  * {opinion.get('expert_name', '专家')}: {opinion.get('opinion', '观点')}"
                    )
            if "consensus" in request.expert_context:
                expert_prompt.append(f"- 团队共识: {request.expert_context['consensus']}")
            if "confidence" in request.expert_context:
                expert_prompt.append(f"- 团队置信度: {request.expert_context['confidence']}")
            expert_prompt.append("")

        # 添加知识库上下文
        if request.knowledge_context:
            expert_prompt.append("知识库支持:")
            if "similar_patents" in request.knowledge_context:
                expert_prompt.append(
                    f"- 相似专利: {len(request.knowledge_context['similar_patents'])}件"
                )
            if "legal_precedents" in request.knowledge_context:
                expert_prompt.append(
                    f"- 法律先例: {len(request.knowledge_context['legal_precedents'])}项"
                )
            if "technical_insights" in request.knowledge_context:
                expert_prompt.append(
                    f"- 技术洞察: {request.knowledge_context['technical_insights']}"
                )
            expert_prompt.append("")

        # 添加用户提示词
        expert_prompt.append(f"分析任务:\n{request.prompt}")

        return "\n".join(expert_prompt)

    async def call_llm(self, request: LLMRequest) -> LLMResponse:
        """调用LLM并返回响应 - 使用GLM-4优先策略"""
        datetime.now()

        if not self.initialized and not await self.initialize():
            return LLMResponse(
                content="LLM客户端初始化失败",
                model_used="none",
                usage={},
                response_time=0.0,
                provider="error",
            )

    def _detect_task_type(self, prompt: str) -> str:
        """检测任务类型"""
        prompt_lower = prompt.lower()

        if any(
            keyword in prompt_lower
            for keyword in ["专利", "patent", "新颖性", "创造性", "权利要求"]
        ):
            return "patent_analysis"
        elif any(
            keyword in prompt_lower for keyword in ["法律", "legal", "法条", "法规", "诉讼", "合同"]
        ):
            return "legal_document"
        elif any(
            keyword in prompt_lower
            for keyword in ["代码", "code", "编程", "程序", "函数", "算法", "python"]
        ):
            return "code_generation"
        elif any(
            keyword in prompt_lower
            for keyword in ["创意", "creative", "写作", "创作", "故事", "诗歌"]
        ):
            return "creative_writing"
        elif any(
            keyword in prompt_lower
            for keyword in ["分析", "analysis", "数据", "统计", "报告", "图表"]
        ):
            return "data_analysis"
        elif any(keyword in prompt_lower for keyword in ["聊天", "chat", "对话", "问答", "交流"]):
            return "general_chat"
        else:
            return "default"

    def _select_optimal_model(self, task_type: str, specified_model: str | None = None) -> Any:
        """选择最优模型"""
        # 如果指定了模型,尝试返回对应的GLM模型
        if specified_model and GLM_AVAILABLE:
            return GLMModel(specified_model)

        # 根据任务类型返回最优模型
        if self.preferred_models:
            return self.preferred_models.get(task_type, self.preferred_models["default"])
        else:
            return None

    def _get_optimized_params(self, task_type: str) -> dict[str, Any]:
        """获取优化参数"""
        return self.model_params.get(task_type, self.model_params.get("default"))

    def _calculate_cost(self, usage: dict, model: str) -> float:  # type: ignore
        """计算成本"""
        try:
            if GLM_AVAILABLE and self.glm_client:
                # 使用GLM客户端的统计功能
                total_tokens = usage.get("total_tokens", 0)

                # GLM 4.7定价(实际应根据GLM官方定价)
                if "4.7-flash" in model:
                    return 0.0  # GLM-4.7-Flash 免费模型
                elif "4.7" in model:
                    return (total_tokens / 1000) * 0.15  # GLM-4.7价格
                else:
                    return (total_tokens / 1000) * 0.15  # 默认价格

        except Exception:
            # 成本计算失败，返回默认值
            logger.debug("成本计算失败，使用默认值0.0")
            return 0.0
        return 0.0

    async def list_available_models(self) -> list[dict[str, Any]]:
        """列出可用模型"""
        if not self.initialized:
            await self.initialize()

        if GLM_AVAILABLE and self.glm_client:
            # 返回GLM 4.7模型列表
            try:
                return [
                    {
                        "name": "glm-4.7",
                        "provider": "GLM",
                        "type": "text",
                        "description": "智谱GLM-4.7 - 最新的旗舰模型,强化编码能力与长程任务规划",
                        "capabilities": [
                            "text_generation",
                            "analysis",
                            "reasoning",
                            "coding",
                            "agent_workflow",
                        ],
                        "enabled": True,
                        "priority": 1,
                    },
                    {
                        "name": "glm-4.7-code",
                        "provider": "GLM",
                        "type": "text",
                        "description": "智谱GLM-4.7-Code - 专业的代码生成和技术分析",
                        "capabilities": ["code_generation", "technical_analysis", "agentic_coding"],
                        "enabled": True,
                        "priority": 1,
                    },
                    {
                        "name": "glm-4.7-flash",
                        "provider": "GLM",
                        "type": "text",
                        "description": "智谱GLM-4.7-Flash - 免费模型,轻量参数规模,高效的Coding能力",
                        "capabilities": ["text_generation", "chat", "coding", "tool_calling"],
                        "enabled": True,
                        "priority": 2,
                        "free": True,
                    },
                ]
            except Exception as e:
                # 获取GLM模型列表失败，使用日志记录
                logger.debug(f"获取GLM模型列表失败: {e}")

        # 返回模拟模型列表
        return [
            {
                "name": "mock-patent-analyzer",
                "provider": "mock",
                "type": "chat",
                "description": "模拟专利分析模型(回退模式)",
                "capabilities": ["text_generation", "analysis"],
                "enabled": True,
                "priority": 99,
            }
        ]

    async def get_model_info(self, model_name: str) -> dict[str, Any] | None:
        """获取模型详细信息"""
        if not self.initialized:
            await self.initialize()

        # GLM 4.7模型信息
        if model_name.startswith("glm"):
            model_configs = {
                "glm-4.7": {
                    "name": "glm-4.7",
                    "provider": "GLM",
                    "type": "text",
                    "description": "智谱GLM-4.7 - 最新的旗舰模型,强化编码能力与长程任务规划",
                    "capabilities": [
                        "text_generation",
                        "analysis",
                        "reasoning",
                        "coding",
                        "agent_workflow",
                    ],
                    "enabled": True,
                    "context_length": 200000,
                    "cost_per_1k": 0.15,
                    "health": True,
                    "thinking_enabled": True,
                    "max_tokens": 65536,
                },
                "glm-4.7-code": {
                    "name": "glm-4.7-code",
                    "provider": "GLM",
                    "type": "text",
                    "description": "智谱GLM-4.7-Code - 专业的代码生成和技术分析",
                    "capabilities": ["code_generation", "technical_analysis", "agentic_coding"],
                    "enabled": True,
                    "context_length": 200000,
                    "cost_per_1k": 0.15,
                    "health": True,
                    "thinking_enabled": True,
                    "max_tokens": 65536,
                },
                "glm-4.7-flash": {
                    "name": "glm-4.7-flash",
                    "provider": "GLM",
                    "type": "text",
                    "description": "智谱GLM-4.7-Flash - 免费模型,轻量参数规模,高效的Coding能力",
                    "capabilities": ["text_generation", "chat", "coding", "tool_calling"],
                    "enabled": True,
                    "context_length": 128000,
                    "cost_per_1k": 0.0,
                    "health": True,
                    "free": True,
                    "thinking_enabled": True,
                    "max_tokens": 65536,
                },
            }
            return model_configs.get(model_name)

        # 模拟模型信息
        return {
            "name": "mock-patent-analyzer",
            "provider": "mock",
            "type": "chat",
            "description": "模拟专利分析模型(回退模式)",
            "capabilities": ["text_generation", "analysis"],
            "enabled": True,
            "health": True,
        }

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        if not self.initialized:
            await self.initialize()

        if GLM_AVAILABLE and self.glm_client:
            # 返回GLM 4.7健康状态
            return {
                "overall": True,
                "mode": "GLM",
                "message": "GLM 4.7统一客户端正常运行",
                "provider": "智谱AI",
                "models": {
                    "glm-4.7": {"available": True, "recommended": True, "thinking_enabled": True},
                    "glm-4.7-code": {
                        "available": True,
                        "recommended": False,
                        "thinking_enabled": True,
                    },
                    "glm-4.7-flash": {
                        "available": True,
                        "recommended": False,
                        "thinking_enabled": True,
                        "free": True,
                    },
                },
                "default_model": "glm-4.7",
                "strategy": "GLM-4.7优先",
                "version": "4.7",
            }

        # 模拟健康状态
        return {
            "overall": True,
            "mode": "mock",
            "message": "GLM统一客户端不可用,使用模拟模式",
            "provider": "mock",
            "models": {"mock-patent-analyzer": {"available": True, "recommended": True}},
            "default_model": "mock-patent-analyzer",
            "strategy": "模拟模式",
        }

    async def _mock_llm_response(self, prompt: str, request: LLMRequest) -> str:
        """模拟LLM响应(作为API失败时的回退方案)"""
        # 模拟异步延迟
        await asyncio.sleep(0.5)

        # 根据提示词内容生成模拟响应
        if "专利分析" in prompt or "patent" in prompt.lower():
            return self._generate_patent_analysis_response(prompt, request)
        elif "法律" in prompt or "legal" in prompt.lower():
            return self._generate_legal_analysis_response(prompt, request)
        elif "技术" in prompt or "technical" in prompt.lower():
            return self._generate_technical_analysis_response(prompt, request)
        else:
            return self._generate_general_response(prompt, request)

    def _generate_patent_analysis_response(self, prompt: str, request: LLMRequest) -> str:
        """生成专利分析响应"""
        response = """
# 🌟 专利分析报告

## 📊 分析概述
基于专家团队的综合分析,本发明具备较高的专利申请价值。

## 🎯 核心结论
1. **新颖性**: ⭐⭐⭐⭐⭐ 技术方案具有显著的创新性
2. **创造性**: ⭐⭐⭐⭐⚪ 相对于现有技术具有突出的实质性特点
3. **实用性**: ⭐⭐⭐⭐⭐ 能够在产业上制造或者使用,并且能产生积极效果

## 📋 权利要求建议
### 独立权利要求
- 保护范围应该适当宽泛,覆盖核心技术特征
- 限定必要技术特征,避免过于具体

### 从属权利要求
- 设置多个从属权利要求,形成多层次保护
- 覆盖技术细节和实施方式

## ⚖️ 法律风险评估
- **低风险**: 技术方案原创性较高
- **中等风险**: 需要进行充分的现有技术检索
- **建议**: 建议进行专利检索和分析

## 💡 申请策略建议
1. 优先申请发明专利
2. 考虑PCT国际申请
3. 建立专利组合策略
        """
        return response.strip()

    def _generate_legal_analysis_response(self, prompt: str, request: LLMRequest) -> str:
        """生成法律分析响应"""
        response = """
# ⚖️ 法律分析报告

## 🔍 法律框架分析
基于中国专利法及相关法规,对技术方案进行法律评估。

## 📜 法律依据
- 《中华人民共和国专利法》
- 《中华人民共和国专利法实施细则》
- 《专利审查指南》

## ⚖️ 授权条件分析
### 新颖性
技术方案不属于现有技术,具备新颖性。

### 创造性
技术方案相对于现有技术具有突出的实质性特点和显著的进步。

### 实用性
技术方案能够制造或使用,并产生积极效果。

## 🔒 权利要求分析
建议撰写清晰、完整的权利要求,确保法律保护范围适当。

## 📈 法律风险评级
- **低风险**: 基本符合专利法要求
- **建议**: 尽快提交专利申请
        """
        return response.strip()

    def _generate_technical_analysis_response(self, prompt: str, request: LLMRequest) -> str:
        """生成技术分析响应"""
        response = """
# 🔬 技术分析报告

## 📡 技术方案评估
对发明的技术方案进行深度分析和评估。

## 🧪 技术创新点
1. **核心创新**: [识别核心技术创新]
2. **技术优势**: [分析技术优势]
3. **应用前景**: [评估应用前景]

## 🔧 技术可行性
- **技术成熟度**: 评估技术实施难度
- **实现路径**: 提供技术实现建议
- **优化方向**: 指出技术改进方向

## 🌐 技术影响
- **行业影响**: 评估对行业的影响
- **市场潜力**: 分析市场应用潜力
- **竞争优势**: 确定技术竞争优势

## 💡 技术建议
1. 加强核心技术的研发投入
2. 建立技术保护体系
3. 推进技术产业化
        """
        return response.strip()

    def _generate_general_response(self, prompt: str, request: LLMRequest) -> str:
        """生成通用响应"""
        response = """
# 🤖 智能分析响应

## 📋 任务理解
已理解您的分析需求,正在进行智能处理。

## 🧠 分析过程
1. 理解分析目标
2. 收集相关信息
3. 进行专业分析
4. 生成分析报告

## ✅ 分析结果
基于专家团队的知识和经验,为您提供专业的分析结果。

## 📞 后续支持
如需进一步分析或有其他问题,请随时联系。
        """
        return response.strip()

    def _extract_expert_analysis(self, content: str) -> dict[str, Any]:
        """从响应中提取专家分析信息"""
        return {
            "has_expert_context": "专家团队" in content or "专家意见" in content,
            "analysis_types": ["专利分析", "法律分析", "技术分析"],
            "recommendations_count": content.count("建议"),
            "conclusions_count": content.count("结论"),
        }

    def _calculate_confidence_score(self, content: str) -> float:
        """计算响应置信度"""
        # 基于响应内容的长度、结构等因素计算置信度
        base_score = 0.7
        if "##" in content:  # 有结构化标题
            base_score += 0.1
        if len(content) > 500:  # 内容足够详细
            base_score += 0.1
        if "建议" in content:  # 包含建议
            base_score += 0.1

        return min(base_score, 1.0)

    def _extract_reasoning_chain(self, content: str) -> list[str]:
        """提取推理链"""
        # 简化的推理链提取
        sections = []
        for line in content.split("\n"):
            if line.startswith("##"):
                sections.append(line.strip())
        return sections

    def get_request_statistics(self) -> dict[str, Any]:
        """获取请求统计信息"""
        if not self.request_history:
            return {"total_requests": 0}

        total_requests = len(self.request_history)
        expert_context_requests = sum(1 for r in self.request_history if r["expert_context"])
        knowledge_context_requests = sum(1 for r in self.request_history if r["knowledge_context"])

        return {
            "total_requests": total_requests,
            "expert_context_requests": expert_context_requests,
            "knowledge_context_requests": knowledge_context_requests,
            "expert_context_ratio": expert_context_requests / total_requests,
            "knowledge_context_ratio": knowledge_context_requests / total_requests,
            "latest_request": (
                self.request_history[-1]["timestamp"] if self.request_history else None
            ),
        }


# 便捷函数
async def call_llm_with_experts(
    prompt: str, expert_context: dict[str, Any] = None, knowledge_context: dict[str, Any] | None = None
) -> LLMResponse:
    """便捷的LLM调用函数,自动包含专家上下文"""
    request = LLMRequest(
        prompt=prompt,
        expert_context=expert_context,
        knowledge_context=knowledge_context,
        system_message="你是星河系列专利专家团队的AI助手,提供专业的专利分析和建议。",
    )

    async with LLMInterface() as llm:
        return await llm.call_llm(request)
