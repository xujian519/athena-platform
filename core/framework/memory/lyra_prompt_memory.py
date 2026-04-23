#!/usr/bin/env python3

"""
Lyra提示词记忆模块
Lyra Prompt Memory Module for Athena Platform
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class LyraPromptMemory:
    """Lyra提示词记忆管理器"""

    def __init__(self):
        self.memory_file = Path("/Users/xujian/Athena工作平台/core/data/lyra_prompt.json")
        self.memory: dict[str, Any] = {}
        self._load_memory()

    def _load_memory(self):
        """加载Lyra提示词记忆"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, encoding='utf-8') as f:
                    self.memory = json.load(f)
                print("✅ 已加载Lyra提示词记忆")
            else:
                self.memory = {}
                self._initialize_lyra_memory()
        except Exception as e:
            print(f"加载Lyra记忆失败: {e}")
            self.memory = {}

    def _save_memory(self):
        """保存Lyra提示词记忆"""
        try:
            # 确保目录存在
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
            print("✅ 已保存Lyra提示词记忆")
        except Exception as e:
            print(f"保存Lyra记忆失败: {e}")

    def _initialize_lyra_memory(self):
        """初始化Lyra提示词记忆"""
        self.memory = {
            "identity": {
                "name": "Lyra",
                "title": "AI提示词优化大师",
                "description": "一个将任何用户输入转换为精准提示词的专家级AI",
                "mission": "将模糊的请求转换为有效的提示词，释放AI的全部潜力",
                "learned_date": datetime.now().isoformat(),
                "learned_from": "用户直接提供"
            },
            "methodology": {
                "title": "4-D方法论",
                "steps": [
                    {
                        "step": 1,
                        "name": "DECONSTRUCT（解构）",
                        "actions": [
                            "提取核心意图、关键实体和上下文",
                            "识别输出要求和约束",
                            "映射已提供的信息 vs 缺失的信息"
                        ]
                    },
                    {
                        "step": 2,
                        "name": "DIAGNOSE（诊断）",
                        "actions": [
                            "审计清晰度差距和歧义",
                            "检查具体性和完整性",
                            "评估结构和复杂性需求"
                        ]
                    },
                    {
                        "step": 3,
                        "name": "DEVELOP（开发）",
                        "actions": [
                            "根据请求类型选择最优技术",
                            "Creative → 多视角 + 语气强调",
                            "Technical → 约束基础 + 精度焦点",
                            "Educational → 少样本示例 + 清晰结构",
                            "Complex → 思维链 + 系统化框架",
                            "分配适当的AI角色/专业知识",
                            "增强上下文并实施逻辑结构"
                        ]
                    },
                    {
                        "step": 4,
                        "name": "DELIVER（交付）",
                        "actions": [
                            "构建优化的提示词",
                            "基于复杂度格式化",
                            "提供实施指导"
                        ]
                    }
                ]
            },
            "optimization_techniques": {
                "foundation": [
                    "角色分配",
                    "上下文分层",
                    "输出规范",
                    "任务分解"
                ],
                "advanced": [
                    "思维链（Chain-of-thought）",
                    "少样本学习（Few-shot learning）",
                    "多视角分析",
                    "约束优化"
                ]
            },
            "operating_modes": {
                "detail_mode": {
                    "name": "详细模式",
                    "description": "使用智能默认值收集上下文",
                    "actions": [
                        "询问2-3个有针对性的澄清问题",
                        "提供全面的优化"
                    ]
                },
                "basic_mode": {
                    "name": "基础模式",
                    "description": "快速修复主要问题",
                    "actions": [
                        "仅应用核心技术",
                        "提供即用型提示词"
                    ]
                }
            },
            "welcome_message": """Hello! I'm Lyra, your AI prompt optimizer. I transform vague requests into precise, effective prompts that deliver better results.

**What I need to know:**
- **Target AI:** ChatGPT, Claude, Gemini, or Other
- **Prompt Style:** DETAIL (I'll ask clarifying questions first) or BASIC (quick optimization)

**Examples:**
- "DETAIL using ChatGPT — Write me a marketing email"
- "BASIC using Claude — Help with my resume"

Just share your rough prompt and I'll handle the optimization!""",
            "usage_examples": [
                {
                    "input": "write me a story",
                    "optimized": "As an expert storyteller, write a compelling 1000-word short story with a clear beginning, rising action, climax, and resolution. Include vivid descriptions and engaging dialogue that captures the reader's attention from the first paragraph."
                },
                {
                    "input": "explain quantum computing",
                    "optimized": "As a physics professor, explain quantum computing to a graduate student audience. Use analogies to clarify complex concepts, include key mathematical principles, and discuss practical applications in cryptography and drug discovery."
                }
            ],
            "integration_notes": {
                "learned_by": "小诺（Xiaonuo）",
                "purpose": "提示词优化服务集成",
                "potential_uses": [
                    "优化用户查询",
                    "改进AI交互质量",
                    "提供提示词工程建议",
                    "增强其他智能体的输出质量"
                ]
            }
        }
        self._save_memory()

    def get_lyra_info(self) -> dict[str, Any]:
        """获取Lyra信息"""
        return self.memory.get("identity", {})

    def get_methodology(self) -> dict[str, Any]:
        """获取4-D方法论"""
        return self.memory.get("methodology", {})

    def get_welcome_message(self) -> str:
        """获取欢迎消息"""
        return self.memory.get("welcome_message", "")

    async def apply_lyra_optimization_async(
        self,
        user_input: str,
        target_ai: str = "Claude",
        mode: str = "BASIC",
        context: Optional[str] = None,
        output_format: Optional[str] = None
    ) -> dict[str, Any]:
        """
        应用Lyra优化方法（异步版本，使用真正的优化引擎）

        Args:
            user_input: 用户输入
            target_ai: 目标AI平台
            mode: 优化模式
            context: 上下文信息
            output_format: 输出格式

        Returns:
            包含优化结果的字典
        """
        try:
            from core.framework.memory.lyra_prompt_optimizer import (
                OptimizationMode,
                OptimizationRequest,
                TargetAI,
                get_lyra_optimizer,
            )

            print(f"🔧 应用Lyra优化（目标AI: {target_ai}, 模式: {mode}）")

            # 解析模式和目标AI
            opt_mode = self._parse_mode(mode)
            opt_ai = self._parse_target_ai(target_ai)

            # 创建优化请求
            request = OptimizationRequest(
                user_input=user_input,
                target_ai=opt_ai,
                mode=opt_mode,
                context=context,
                output_format=output_format
            )

            # 获取优化器并执行优化
            optimizer = get_lyra_optimizer()
            result = await optimizer.optimize(request)

            # 返回结果字典
            return {
                "success": True,
                "optimized_prompt": result.optimized_prompt,
                "improvements": result.improvements,
                "reasoning": result.reasoning,
                "score": result.score,
                "suggestions": result.suggestions,
                "target_ai": result.target_ai.value,
                "mode": result.mode.value
            }

        except ImportError as e:
            print(f"⚠️ 优化引擎不可用，使用简化模式: {e}")
            # 降级到简化模式
            return self._apply_simplified_optimization(user_input, target_ai, mode)
        except Exception as e:
            print(f"❌ 优化失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "optimized_prompt": user_input  # 返回原始输入
            }

    def apply_lyra_optimization(self, user_input: str, target_ai: str = "ChatGPT", mode: str = "BASIC") -> str:
        """
        应用Lyra优化方法（同步版本，向后兼容）

        注意：此方法为简化版本，如需完整功能请使用 apply_lyra_optimization_async
        """
        print(f"🔧 应用Lyra优化（目标AI: {target_ai}, 模式: {mode}）")

        # 返回简化的优化提示（保持向后兼容）
        optimization_prompt = f"""Using Lyra's 4-D methodology, optimize this prompt for {target_ai}:

1. DECONSTRUCT: Analyze the user's intent and requirements
2. DIAGNOSE: Identify gaps and areas for improvement
3. DEVELOP: Apply appropriate techniques and structure
4. DELIVER: Create the optimized prompt

Original input: "{user_input}"

Provide the optimized prompt that will deliver better results:"""

        return optimization_prompt

    def _parse_mode(self, mode_str: str):
        """解析优化模式"""
        from core.framework.memory.lyra_prompt_optimizer import OptimizationMode

        mode_map = {
            "BASIC": OptimizationMode.BASIC,
            "DETAIL": OptimizationMode.DETAIL,
            "CREATIVE": OptimizationMode.CREATIVE,
            "TECHNICAL": OptimizationMode.TECHNICAL
        }
        return mode_map.get(mode_str.upper(), OptimizationMode.BASIC)  # type: ignore

    def _parse_target_ai(self, ai_str: str):
        """解析目标AI"""
        from core.framework.memory.lyra_prompt_optimizer import TargetAI

        ai_map = {
            "ChatGPT": TargetAI.CHATGPT,
            "Claude": TargetAI.CLAUDE,
            "Gemini": TargetAI.GEMINI,
            "DeepSeek": TargetAI.DEEPSEEK,
            "Qwen": TargetAI.QWEN,
            "Generic": TargetAI.GENERIC
        }
        return ai_map.get(ai_str, TargetAI.CLAUDE)  # type: ignore

    def _apply_simplified_optimization(self, user_input: str, target_ai: str, mode: str) -> dict[str, Any]:
        """应用简化的优化逻辑（降级方案）"""
        improvements = []
        optimized = user_input

        # 添加角色（如果没有）
        if not any(word in optimized.lower() for word in ["as", "you are", "扮演", "作为"]):
            optimized = f"As an expert assistant, {optimized[0].lower()}{optimized[1:]}"
            improvements.append("Added role definition")

        # 添加输出格式（如果没有）
        if not any(word in optimized.lower() for word in ["format", "output", "格式"]):
            optimized += "\n\nPlease provide a clear, structured response."
            improvements.append("Added output format specification")

        return {
            "success": True,
            "optimized_prompt": optimized,
            "improvements": improvements,
            "reasoning": "Applied basic optimization rules",
            "score": 0.6,
            "suggestions": ["Try using async mode for better results"],
            "target_ai": target_ai,
            "mode": mode
        }

    def check_reminder_needed(self) -> bool:
        """检查是否需要提醒"""
        # 这里可以添加提醒逻辑
        return False

# 全局实例
_lyra_memory = None

def get_lyra_memory() -> LyraPromptMemory:
    """获取Lyra提示词记忆实例"""
    global _lyra_memory
    if _lyra_memory is None:
        _lyra_memory = LyraPromptMemory()
    return _lyra_memory

# 便捷函数
def get_lyra_identity() -> dict[str, Any]:
    """获取Lyra身份（供小诺使用）"""
    memory = get_lyra_memory()
    return memory.get_lyra_info()

def get_lyra_methodology() -> dict[str, Any]:
    """获取Lyra方法论（供小诺使用）"""
    memory = get_lyra_memory()
    return memory.get_methodology()

def apply_lyra_optimization(user_input: str, target_ai: str = "ChatGPT", mode: str = "BASIC") -> str:
    """应用Lyra优化（供小诺使用，同步版本）"""
    memory = get_lyra_memory()
    return memory.apply_lyra_optimization(user_input, target_ai, mode)


async def apply_lyra_optimization_async(
    user_input: str,
    target_ai: str = "Claude",
    mode: str = "BASIC",
    context: Optional[str] = None,
    output_format: Optional[str] = None
) -> dict[str, Any]:
    """
    应用Lyra优化（供小诺使用，异步版本，完整功能）

    Args:
        user_input: 用户输入的提示词
        target_ai: 目标AI平台 (ChatGPT/Claude/Gemini/DeepSeek/Qwen)
        mode: 优化模式 (BASIC/DETAIL/CREATIVE/TECHNICAL)
        context: 可选的上下文信息
        output_format: 可选的输出格式要求

    Returns:
        包含优化结果的字典:
        {
            "success": bool,
            "optimized_prompt": str,
            "improvements": list[str],
            "reasoning": str,
            "score": float,
            "suggestions": list[str],
            "target_ai": str,
            "mode": str
        }
    """
    memory = get_lyra_memory()
    return await memory.apply_lyra_optimization_async(
        user_input, target_ai, mode, context, output_format
    )

if __name__ == "__main__":
    # 测试Lyra记忆系统
    print("🧪 Lyra提示词记忆系统测试")
    print("=" * 50)

    memory = get_lyra_memory()

    # 测试获取信息
    print("\n1. Lyra身份信息:")
    identity = memory.get_lyra_info()
    print(f"   名称: {identity.get('name')}")
    print(f"   标题: {identity.get('title')}")
    print(f"   使命: {identity.get('mission')}")
    print(f"   学习日期: {identity.get('learned_date')}")

    print("\n2. 4-D方法论:")
    methodology = memory.get_methodology()
    for step_info in methodology.get("steps", []):
        print(f"   步骤{step_info['step']}: {step_info['name']}")
        for action in step_info['actions'][:2]:  # 只显示前2个
            print(f"     • {action}")

    print("\n3. 欢迎消息:")
    welcome = memory.get_welcome_message()
    print(f"   {welcome[:100]}...")

    print("\n4. 测试优化功能:")
    test_input = "写一篇关于AI的文章"
    optimized = memory.apply_lyra_optimization(test_input)
    print(f"   原始输入: {test_input}")
    print(f"   优化后: {optimized[:100]}...")

    print("\n✅ Lyra提示词记忆系统测试完成！")

