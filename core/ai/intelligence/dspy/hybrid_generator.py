
"""
DSPy混合提示词生成器
DSPy Hybrid Prompt Generator for Athena Platform

融合Athena现有提示词系统和DSPy优化能力
"""

import logging
from dataclasses import dataclass

from .config import configure_dspy
from .llm_backend import ATHENA_LLM_AVAILABLE, get_athena_llm_client
from .retrievers import AthenaGraphRetriever, AthenaVectorRetriever
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class HybridPromptConfig:
    """混合提示词配置"""

    use_dspy_optimization: bool = False  # 是否启用DSPy优化
    base_prompt_layer: str = "L3"  # 基础提示词层级 (L1/L2/L3/L4)
    optimization_target: str = ""  # 优化目标 (capability_2, task_1_1, etc.)
    human_review_required: bool = True  # 是否需要人工审核
    fallback_to_base: bool = True  # DSPy失败时是否回退到基线


class DSPyHybridPromptGenerator:
    """DSPy混合提示词生成器

    融合Athena手工设计的提示词和DSPy自动优化的提示词
    """

    def __init__(self, config: Optional[HybridPromptConfig] = None):
        """初始化混合提示词生成器

        Args:
            config: 混合提示词配置
        """
        self.config = config or HybridPromptConfig()
        self.dspy_config = configure_dspy()

        # 配置DSPy LLM后端
        try:
            # 使用Athena LLM客户端
            self.llm_client = get_athena_llm_client(
                model_type="patent_analysis",
                temperature=self.dspy_config.temperature,
                max_tokens=self.dspy_config.max_tokens,
            )
            self.dspy_enabled = ATHENA_LLM_AVAILABLE
            logger.info(f"DSPy LLM配置成功,Athena LLM可用: {self.dspy_enabled}")
        except Exception as e:
            logger.warning(f"DSPy配置失败: {e},将使用Athena基线")
            self.dspy_enabled = False
            self.llm_client = None

        # 导入Athena提示词生成器
        try:
            from ..dynamic_prompt_generator import DynamicPromptGenerator

            self.athena_generator = DynamicPromptGenerator()
            self.athena_available = True
            logger.info("Athena提示词生成器导入成功")
        except Exception as e:
            logger.warning(f"Athena提示词生成器导入失败: {e}")
            self.athena_available = False
            self.athena_generator = None

        # 初始化检索器
        self.vector_retriever = None
        self.graph_retriever = None

        if self.dspy_enabled and self.dspy_config.enable_vector_retrieval:
            try:
                self.vector_retriever = AthenaVectorRetriever()
                logger.info("向量检索器初始化成功")
            except Exception as e:
                logger.warning(f"向量检索器初始化失败: {e}")

        if self.dspy_enabled and self.dspy_config.enable_graph_retrieval:
            try:
                self.graph_retriever = AthenaGraphRetriever()
                logger.info("知识图谱检索器初始化成功")
            except Exception as e:
                logger.warning(f"知识图谱检索器初始化失败: {e}")

    def generate_prompt(
        self,
        user_input: str,
        task_type: Optional[str] = None,
        layer: Optional[str] = None,
        use_dspy: Optional[bool] = None,
    ) -> str:
        """生成混合提示词

        Args:
            user_input: 用户输入
            task_type: 任务类型(如capability_2, task_1_1)
            layer: 提示词层级(L1/L2/L3/L4)
            use_dspy: 是否使用DSPy优化(可选,默认根据配置决定)

        Returns:
            生成的提示词
        """
        layer = layer or self.config.base_prompt_layer

        # 判断是否应该使用DSPy
        should_use_dspy = self._should_use_dspy(layer, use_dspy)

        # 1. 使用Athena系统生成基线提示词
        base_prompt = self._generate_base_prompt(user_input, task_type, layer)

        # 2. 如果启用DSPy,进行优化
        if should_use_dspy and self.dspy_enabled and self.llm_client:
            try:
                optimized_prompt = self._optimize_with_dspy(
                    base_prompt, user_input, task_type, layer
                )

                # 人格保护检查
                if self.dspy_config.enable_persona_protection:
                    protected_prompt = self._protect_persona(base_prompt, optimized_prompt, layer)
                    optimized_prompt = protected_prompt

                # 合并基线和优化版本
                return self._merge_prompts(base_prompt, optimized_prompt)

            except Exception as e:
                logger.warning(f"DSPy优化失败: {e},使用基线提示词")
                if self.config.fallback_to_base:
                    return base_prompt

        return base_prompt

    def _should_use_dspy(self, layer: str, use_dspy: bool,) -> bool:
        """判断是否应该使用DSPy优化

        Args:
            layer: 提示词层级
            use_dspy: 用户指定的DSPy使用标志

        Returns:
            是否使用DSPy
        """
        # 用户明确指定
        if use_dspy is not None:
            return use_dspy

        # L1/L2层不使用DSPy(保护人格和领域知识)
        if layer in ["L1", "L2"]:
            return False

        # 检查配置
        return self.config.use_dspy_optimization

    def _generate_base_prompt(self, user_input: str, task_type: str, layer: str) -> str:
        """生成Athena基线提示词

        Args:
            user_input: 用户输入
            task_type: 任务类型
            layer: 提示词层级

        Returns:
            基线提示词
        """
        if not self.athena_available or self.athena_generator is None:
            # 如果Athena生成器不可用,返回简单提示词
            return f"请根据用户输入处理: {user_input}"

        try:
            # 使用Athena的提示词生成器
            prompt_data = self.athena_generator.generate_dynamic_prompt(
                user_input=user_input, business_type=task_type or layer
            )

            # 提取文本内容
            if isinstance(prompt_data, dict):
                return prompt_data.get("prompt", prompt_data.get("text", str(prompt_data)))
            elif hasattr(prompt_data, "system_prompt"):
                # DynamicPrompt对象
                parts = []
                if hasattr(prompt_data, "system_prompt") and prompt_data.system_prompt:
                    parts.append(f"系统: {prompt_data.system_prompt}")
                if hasattr(prompt_data, "context_prompt") and prompt_data.context_prompt:
                    parts.append(f"上下文: {prompt_data.context_prompt}")
                if hasattr(prompt_data, "action_prompt") and prompt_data.action_prompt:
                    parts.append(f"行动: {prompt_data.action_prompt}")
                return "\n\n".join(parts) if parts else str(prompt_data)
            else:
                return str(prompt_data)

        except Exception as e:
            logger.warning(f"Athena基线生成失败: {e}")
            return f"请处理: {user_input}"

    def _optimize_with_dspy(
        self, base_prompt: str, user_input: str, task_type: str, layer: str
    ) -> str:
        """使用DSPy优化提示词

        Args:
            base_prompt: 基线提示词
            user_input: 用户输入
            task_type: 任务类型
            layer: 提示词层级

        Returns:
            优化后的提示词
        """
        # 构建优化提示词
        optimization_prompt = f"""你是一个提示词优化专家。请优化以下提示词,使其更清晰、更有效。

基线提示词:
{base_prompt}

用户输入:
{user_input}

任务类型: {task_type or '通用'}
层级: {layer}

请提供优化后的提示词(保持原有意图,但使其更清晰有效):"""

        # 调用Athena LLM进行优化
        if self.llm_client:
            try:
                optimized = self.llm_client.generate(optimization_prompt)
                return optimized
            except Exception as e:
                logger.warning(f"DSPy优化LLM调用失败: {e}")
                return base_prompt

        return base_prompt

    def _protect_persona(self, base_prompt: str, optimized_prompt: str, layer: str) -> str:
        """保护AI人格一致性

        Args:
            base_prompt: 基线提示词
            optimized_prompt: 优化后的提示词
            layer: 提示词层级

        Returns:
            人格保护后的提示词
        """
        # L1层需要严格保护人格
        if layer == "L1":
            return base_prompt

        # 检测人格漂移
        drift = self._measure_persona_drift(base_prompt, optimized_prompt)

        # 如果漂移超过阈值,进行修正
        if drift > self.dspy_config.persona_drift_threshold:
            return self._correct_persona_drift(base_prompt, optimized_prompt)

        return optimized_prompt

    def _measure_persona_drift(self, base: str, optimized: str) -> float:
        """测量人格漂移程度

        Args:
            base: 基线提示词
            optimized: 优化后提示词

        Returns:
            漂移分数 (0-1)
        """
        # 简化实现:检查关键词变化
        base_keywords = {"小娜", "天秤女神", "专业", "严谨", "专利法律"}
        optimized_lower = optimized.lower()

        keyword_count = sum(1 for kw in base_keywords if kw in optimized_lower)
        drift = 1.0 - (keyword_count / len(base_keywords))

        return drift

    def _correct_persona_drift(self, base: str, optimized: str) -> str:
        """修正人格漂移

        Args:
            base: 基线提示词
            optimized: 优化后提示词

        Returns:
            修正后的提示词
        """
        # 简化实现:在优化后提示词前添加人格说明
        persona_intro = "你是小娜·天秤女神,专业严谨的专利法律AI助手。"
        return f"{persona_intro}\n\n{optimized}"

    def _merge_prompts(self, base: str, optimized: str) -> str:
        """合并基线和优化提示词

        Args:
            base: 基线提示词
            optimized: 优化后提示词

        Returns:
            合并后的提示词
        """
        # 简化实现:使用优化版本
        return optimized


# 便捷函数
def create_hybrid_generator(
    use_dspy: bool = False, layer: str = "L3", task_type: str = ""
) -> DSPyHybridPromptGenerator:
    """创建混合提示词生成器

    Args:
        use_dspy: 是否启用DSPy
        layer: 提示词层级
        task_type: 任务类型

    Returns:
        混合提示词生成器实例
    """
    config = HybridPromptConfig(
        use_dspy_optimization=use_dspy, base_prompt_layer=layer, optimization_target=task_type
    )

    return DSPyHybridPromptGenerator(config)


# 导出
__all__ = [
    "DSPyHybridPromptGenerator",
    "HybridPromptConfig",
    "create_hybrid_generator",
]

