#!/usr/bin/env python3
from __future__ import annotations
"""
Lyra提示词优化引擎
Lyra Prompt Optimizer Engine for Athena Platform

实现真正的提示词优化逻辑，集成AI模型
使用4-D方法论：解构、诊断、开发、交付

作者: 小诺·双鱼公主 v1.0
创建时间: 2026-02-06
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TargetAI(Enum):
    """目标AI平台"""
    CHATGPT = "ChatGPT"
    CLAUDE = "Claude"
    GEMINI = "Gemini"
    DEEPSEEK = "DeepSeek"
    QWEN = "Qwen"
    GENERIC = "Generic"


class OptimizationMode(Enum):
    """优化模式"""
    DETAIL = "DETAIL"  # 详细模式：询问澄清问题
    BASIC = "BASIC"    # 基础模式：快速优化
    CREATIVE = "CREATIVE"  # 创意模式：多视角分析
    TECHNICAL = "TECHNICAL"  # 技术模式：精度焦点


@dataclass
class OptimizationRequest:
    """优化请求"""
    user_input: str
    target_ai: TargetAI = TargetAI.CLAUDE
    mode: OptimizationMode = OptimizationMode.BASIC
    context: Optional[str] = None
    constraints: Optional[list[str]] = None
    output_format: Optional[str] = None


@dataclass
class OptimizationResult:
    """优化结果"""
    original_input: str
    optimized_prompt: str
    improvements: list[str]
    reasoning: str
    target_ai: TargetAI
    mode: OptimizationMode
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    score: float = 0.0
    suggestions: list[str] = field(default_factory=list)


class LyraPromptOptimizer:
    """Lyra提示词优化引擎 - 核心优化逻辑"""

    # 4-D方法论模板
    METHODology_TEMPLATE = """You are Lyra, an expert prompt engineer using the 4-D methodology:

**Step 1: DECONSTRUCT (解构)**
- Extract the core intent, key entities, and context
- Identify output requirements and constraints
- Map provided information vs missing information

**Step 2: DIAGNOSE (诊断)**
- Audit clarity gaps and ambiguities
- Check specificity and completeness
- Evaluate structure and complexity needs

**Step 3: DEVELOP (开发)**
- Select optimal techniques based on request type:
  * Creative → Multi-perspective + Tone emphasis
  * Technical → Constraint-based + Precision focus
  * Educational → Few-shot examples + Clear structure
  * Complex → Chain-of-thought + Systematic framework
- Assign appropriate AI role/expertise
- Enhance context and implement logical structure

**Step 4: DELIVER (交付)**
- Construct the optimized prompt
- Format based on complexity
- Provide implementation guidance

---
Current task: Optimize the following prompt for {target_ai}

Original input: {user_input}

Additional context: {context}

Constraints: {constraints}

Output format (JSON):
{{
  "analysis": {{
    "deconstruct": "What is the core intent?",
    "diagnose": "What are the issues?",
    "develop": "What improvements to make?"
  }},
  "optimized_prompt": "The fully optimized prompt",
  "improvements": ["list of specific improvements"],
  "reasoning": "Explanation of changes",
  "score": 0.0-1.0,
  "suggestions": ["additional suggestions for user"]
}}
"""

    # 不同AI的提示词风格建议
    AI_STYLE_GUIDES = {
        TargetAI.CHATGPT: {
            "style": "Direct and structured",
            "tips": [
                "Use clear, step-by-step instructions",
                "Provide examples for complex tasks",
                "Specify output format explicitly"
            ]
        },
        TargetAI.CLAUDE: {
            "style": "Nuanced and contextual",
            "tips": [
                "Emphasize role and context",
                "Use natural language instructions",
                "Allow for creative interpretation"
            ]
        },
        TargetAI.GEMINI: {
            "style": "Multimedia-friendly",
            "tips": [
                "Include modalities (text, image, code)",
                "Structure with clear headings",
                "Enable multimodal outputs"
            ]
        },
        TargetAI.DEEPSEEK: {
            "style": "Code and reasoning focused",
            "tips": [
                "Include step-by-step reasoning",
                "Specify code requirements",
                "Enable deep analysis mode"
            ]
        },
        TargetAI.QWEN: {
            "style": "Balanced and versatile",
            "tips": [
                "Provide balanced context",
                "Include Chinese language considerations",
                "Specify domain expertise"
            ]
        },
        TargetAI.GENERIC: {
            "style": "Universal compatibility",
            "tips": [
                "Keep instructions clear and simple",
                "Avoid platform-specific features",
                "Focus on universal best practices"
            ]
        }
    }

    def __init__(self):
        """初始化优化引擎"""
        self.llm_service = None
        self.use_lyra_llm = True  # 优先使用Lyra LLM服务
        self._init_llm_service()
        logger.info("✅ Lyra提示词优化引擎初始化完成")

    def _init_llm_service(self):
        """初始化LLM服务"""
        # 优先使用Lyra专用LLM服务
        if self.use_lyra_llm:
            try:
                from core.memory.lyra_llm_service import LLMRequest as LyraLLMRequest
                from core.memory.lyra_llm_service import get_lyra_llm_service
                self.llm_service = get_lyra_llm_service()
                self.LLMRequest = LyraLLMRequest
                self.is_lyra_llm = True
                logger.info("✅ Lyra LLM服务已连接")
                return
            except ImportError as e:
                logger.warning(f"⚠️ Lyra LLM服务不可用: {e}")
                self.is_lyra_llm = False

        # 降级到Athena LLM服务
        try:
            from core.models.athena_llm_service import (
                LLMProvider,
                LLMRequest,
                get_athena_llm_service,
            )
            self.llm_service = get_athena_llm_service()
            self.LLMProvider = LLMProvider
            self.LLMRequest = LLMRequest
            self.is_lyra_llm = False
            logger.info("✅ Athena LLM服务已连接")
        except ImportError as e:
            logger.warning(f"⚠️ Athena LLM服务不可用: {e}")
            self.llm_service = None
            self.is_lyra_llm = False

    async def optimize(self, request: OptimizationRequest) -> OptimizationResult:
        """
        执行提示词优化

        Args:
            request: 优化请求

        Returns:
            OptimizationResult: 优化结果
        """
        logger.info(f"🔧 开始优化 (目标: {request.target_ai.value}, 模式: {request.mode.value})")

        # 如果LLM服务可用，使用AI优化
        if self.llm_service:
            return await self._ai_optimize(request)
        else:
            return await self._rule_based_optimize(request)

    async def _ai_optimize(self, request: OptimizationRequest) -> OptimizationResult:
        """使用AI进行优化"""
        try:
            # 构建优化提示
            optimization_prompt = self.METHODology_TEMPLATE.format(
                target_ai=request.target_ai.value,
                user_input=request.user_input,
                context=request.context or "None",
                constraints=", ".join(request.constraints) if request.constraints else "None"
            )

            # 添加模式特定指令
            mode_instruction = self._get_mode_instruction(request.mode)
            optimization_prompt = f"{mode_instruction}\n\n{optimization_prompt}"

            # 根据LLM服务类型调用
            if getattr(self, 'is_lyra_llm', False):
                # 使用Lyra LLM服务
                llm_request = self.LLMRequest(
                    prompt=optimization_prompt,
                    system_message=self._get_system_prompt(request.target_ai),
                    temperature=0.3,
                    max_tokens=2000
                )
                response = await self.llm_service.generate(llm_request)

                if not response.success:
                    raise Exception(response.error or "LLM调用失败")

                content = response.content
            else:
                # 使用Athena LLM服务
                llm_request = self.LLMRequest(
                    prompt=optimization_prompt,
                    system_message=self._get_system_prompt(request.target_ai),
                    temperature=0.3,
                    max_tokens=2000,
                    enable_cache=False
                )
                response = await self.llm_service.generate(llm_request)
                content = response.content

            # 解析响应
            return self._parse_ai_response(request, content)

        except Exception as e:
            logger.error(f"❌ AI优化失败: {e}")
            # 降级到基于规则的优化
            return await self._rule_based_optimize(request)

    async def _rule_based_optimize(self, request: OptimizationRequest) -> OptimizationResult:
        """基于规则的优化（无AI时的降级方案）"""
        logger.info("📋 使用基于规则的优化")

        improvements = []
        optimized = request.user_input
        reasoning_parts = []

        # 1. 检查是否缺少角色设定
        if not any(word in optimized.lower() for word in ["as", "you are", "act as", "扮演", "作为"]):
            role = self._suggest_role(request.user_input)
            if role:
                optimized = f"As {role}, {optimized[0].lower()}{optimized[1:]}"
                improvements.append(f"Added role: {role}")
                reasoning_parts.append("Added role definition for clarity")

        # 2. 检查是否需要输出格式
        if not any(word in optimized.lower() for word in ["format", "output", "return", "格式"]):
            output_format = request.output_format or self._suggest_output_format(request.user_input)
            if output_format:
                optimized += f"\n\nPlease provide the output in {output_format} format."
                improvements.append(f"Added output format: {output_format}")
                reasoning_parts.append("Added explicit output format specification")

        # 3. 检查是否需要约束条件
        constraints = request.constraints or []
        if constraints:
            optimized += "\n\nConstraints:\n" + "\n".join(f"- {c}" for c in constraints)
            improvements.append(f"Added {len(constraints)} constraints")
            reasoning_parts.append("Incorporated user-specified constraints")

        # 4. 添加上下文
        if request.context:
            optimized = f"Context: {request.context}\n\n{optimized}"
            improvements.append("Added context")
            reasoning_parts.append("Added relevant context information")

        # 5. 根据目标AI优化
        ai_guide = self.AI_STYLE_GUIDES.get(request.target_ai)
        if ai_guide:
            reasoning_parts.append(f"Optimized for {request.target_ai.value} style: {ai_guide['style']}")

        # 6. 检查具体性
        word_count = len(request.user_input.split())
        if word_count < 10:
            improvements.append("Low specificity - consider adding more details")
            reasoning_parts.append("Input is brief; more details would improve results")

        # 计算分数
        score = self._calculate_score(improvements, word_count)

        return OptimizationResult(
            original_input=request.user_input,
            optimized_prompt=optimized,
            improvements=improvements,
            reasoning="\n".join(reasoning_parts),
            target_ai=request.target_ai,
            mode=request.mode,
            score=score,
            suggestions=self._generate_suggestions(request)
        )

    def _get_system_prompt(self, target_ai: TargetAI) -> str:
        """获取系统提示"""
        ai_guide = self.AI_STYLE_GUIDES.get(target_ai, self.AI_STYLE_GUIDES[TargetAI.GENERIC])
        return f"""You are Lyra, an expert prompt engineer specializing in optimizing prompts for {target_ai.value}.

Style guide for {target_ai.value}:
- Style: {ai_guide['style']}
- Key tips: {', '.join(ai_guide['tips'][:3])}

Always respond with valid JSON in the specified format."""

    def _get_mode_instruction(self, mode: OptimizationMode) -> str:
        """获取模式特定指令"""
        instructions = {
            OptimizationMode.DETAIL: """
**DETAIL MODE**: Provide comprehensive analysis with detailed explanations.
Include specific examples and step-by-step implementation guidance.
""",
            OptimizationMode.BASIC: """
**BASIC MODE**: Focus on quick, practical improvements.
Provide a ready-to-use optimized prompt with essential enhancements only.
""",
            OptimizationMode.CREATIVE: """
**CREATIVE MODE**: Explore multiple perspectives and approaches.
Consider different angles, tones, and creative interpretations.
""",
            OptimizationMode.TECHNICAL: """
**TECHNICAL MODE**: Maximize precision and technical accuracy.
Focus on clear specifications, constraints, and technical requirements.
"""
        }
        return instructions.get(mode, "")

    def _parse_ai_response(self, request: OptimizationRequest, response: str) -> OptimizationResult:
        """解析AI响应"""
        try:
            # 尝试提取JSON
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)

                # analysis = data.get("analysis", {})  # 暂未使用
                improvements = data.get("improvements", [])
                reasoning = data.get("reasoning", "")
                optimized = data.get("optimized_prompt", response)
                score = data.get("score", 0.8)
                suggestions = data.get("suggestions", [])

                return OptimizationResult(
                    original_input=request.user_input,
                    optimized_prompt=optimized,
                    improvements=improvements,
                    reasoning=reasoning,
                    target_ai=request.target_ai,
                    mode=request.mode,
                    score=score,
                    suggestions=suggestions
                )
            else:
                # JSON解析失败，使用原始响应
                return OptimizationResult(
                    original_input=request.user_input,
                    optimized_prompt=response,
                    improvements=["AI-generated optimization"],
                    reasoning="Optimized by AI",
                    target_ai=request.target_ai,
                    mode=request.mode,
                    score=0.8
                )

        except json.JSONDecodeError:
            # JSON解析失败，降级
            logger.warning("⚠️ JSON解析失败，使用原始响应")
            return OptimizationResult(
                original_input=request.user_input,
                optimized_prompt=response,
                improvements=["AI-generated optimization"],
                reasoning="Optimized by AI (parsing fallback)",
                target_ai=request.target_ai,
                mode=request.mode,
                score=0.7
            )

    def _suggest_role(self, user_input: str) -> Optional[str]:
        """建议角色"""
        input_lower = user_input.lower()

        # 简单的关键词匹配
        role_keywords = {
            "code": "expert programmer",
            "write": "professional writer",
            "analyze": "expert analyst",
            "explain": "knowledgeable teacher",
            "design": "experienced designer",
            "research": "skilled researcher",
            "代码": "编程专家",
            "写作": "专业作家",
            "分析": "专业分析师",
            "解释": "知识渊博的老师"
        }

        for keyword, role in role_keywords.items():
            if keyword in input_lower:
                return role

        return "an expert assistant"

    def _suggest_output_format(self, user_input: str) -> Optional[str]:
        """建议输出格式"""
        input_lower = user_input.lower()

        if "code" in input_lower or "function" in input_lower:
            return "code block"
        elif "list" in input_lower or "步骤" in user_input:
            return "numbered list"
        elif "table" in input_lower or "表格" in user_input:
            return "table"
        elif "explain" in input_lower or "解释" in user_input:
            return "structured explanation"
        else:
            return "clear, structured text"

    def _calculate_score(self, improvements: list[str], word_count: int) -> float:
        """计算优化分数"""
        base_score = 0.5

        # 改进数量加分
        improvement_bonus = min(len(improvements) * 0.1, 0.3)

        # 输入长度加分
        length_bonus = min(word_count / 50 * 0.1, 0.2)

        return min(base_score + improvement_bonus + length_bonus, 1.0)

    def _generate_suggestions(self, request: OptimizationRequest) -> list[str]:
        """生成额外建议"""
        suggestions = []

        # 检查输入长度
        if len(request.user_input.split()) < 10:
            suggestions.append("💡 Consider adding more specific details about what you want")

        # 检查上下文
        if not request.context:
            suggestions.append("💡 Providing background context can improve results")

        # 检查输出格式
        if not request.output_format:
            suggestions.append("💡 Specify your desired output format (e.g., JSON, markdown, bullet points)")

        # 模式特定建议
        if request.mode == OptimizationMode.BASIC:
            suggestions.append("💡 Try DETAIL mode for more comprehensive optimization")
        elif request.mode == OptimizationMode.DETAIL:
            suggestions.append("💡 For quick results, try BASIC mode")

        return suggestions

    def get_ai_guide(self, target_ai: TargetAI) -> dict[str, Any]:
        """获取AI优化指南"""
        return self.AI_STYLE_GUIDES.get(target_ai, self.AI_STYLE_GUIDES[TargetAI.GENERIC])


# 全局实例
_optimizer: LyraPromptOptimizer | None = None


def get_lyra_optimizer() -> LyraPromptOptimizer:
    """获取Lyra优化器实例"""
    global _optimizer
    if _optimizer is None:
        _optimizer = LyraPromptOptimizer()
    return _optimizer


if __name__ == "__main__":
    # 测试优化器
    async def test():
        print("🧪 Lyra提示词优化引擎测试")
        print("=" * 60)

        optimizer = get_lyra_optimizer()

        # 测试请求
        test_requests = [
            OptimizationRequest(
                user_input="写一篇关于AI的文章",
                target_ai=TargetAI.CLAUDE,
                mode=OptimizationMode.BASIC
            ),
            OptimizationRequest(
                user_input="explain quantum computing",
                target_ai=TargetAI.CHATGPT,
                mode=OptimizationMode.DETAIL,
                context="For a graduate student audience"
            )
        ]

        for i, req in enumerate(test_requests, 1):
            print(f"\n📝 测试 {i}: {req.user_input[:50]}...")
            result = await optimizer.optimize(req)

            print(f"   目标AI: {result.target_ai.value}")
            print(f"   模式: {result.mode.value}")
            print(f"   分数: {result.score:.2f}")
            print(f"   改进项: {', '.join(result.improvements[:3])}")
            print(f"   优化后: {result.optimized_prompt[:100]}...")

        print("\n✅ 测试完成")

    asyncio.run(test())
