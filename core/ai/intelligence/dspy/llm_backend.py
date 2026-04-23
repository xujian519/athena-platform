
"""
Athena LLM后端适配器
Athena LLM Backend Adapter for DSPy

将Athena平台的LLM服务(GLM、DeepSeek)适配为DSPy可用的后端

DSPy使用LiteLLM作为统一后端,因此我们提供两种集成方式:
1. 直接使用DSPy LM + LiteLLM配置(推荐)
2. 使用自定义Adapter包装Athena LLM服务
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

import dspy

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 添加项目路径
project_root = Path("/Users/xujian/Athena工作平台")
import sys

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 尝试导入Athena的LLM接口
try:
    from core.cognition.llm_interface import LLMInterface, LLMRequest

    ATHENA_LLM_AVAILABLE = True
    logger.info("Athena LLM接口导入成功")
except ImportError as e:
    ATHENA_LLM_AVAILABLE = False
    logger.warning(f"Athena LLM接口导入失败: {e}")


class AthenaLLMDirect:
    """Athena LLM直接调用类(不使用DSPy LM包装)

    这种方式更简单,直接调用Athena的LLM服务
    """

    def __init__(
        self,
        model_type: str = "patent_analysis",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """初始化Athena LLM

        Args:
            model_type: 模型类型 (patent_analysis, legal_document, general_chat等)
            temperature: 温度参数
            max_tokens: 最大token数
        """
        self.model_type = model_type
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._llm_interface: Optional[LLMInterface] = None

        logger.info(f"Athena LLM初始化完成,模型类型: {model_type}")

    async def _get_llm_interface(self) -> LLMInterface:
        """获取或创建LLM接口实例"""
        if self._llm_interface is None:
            self._llm_interface = LLMInterface()
            await self._llm_interface.initialize()
        return self._llm_interface

    def generate(self, prompt: str, **kwargs) -> str:
        """生成响应(同步接口)

        Args:
            prompt: 输入提示词
            **kwargs: 额外参数

        Returns:
            响应文本
        """
        if not ATHENA_LLM_AVAILABLE:
            logger.warning("Athena LLM不可用,返回模拟响应")
            return f"[模拟响应] {prompt[:50]}..."

        try:
            # 使用asyncio运行异步代码
            response = asyncio.run(self._generate_async(prompt, **kwargs))
            return response

        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return f"LLM调用失败: {e!s}"

    async def _generate_async(self, prompt: str, **kwargs) -> str:
        """异步生成响应"""
        llm = await self._get_llm_interface()

        # 构建请求
        request = LLMRequest(
            prompt=prompt,
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            model_name=self.model_type,
        )

        # 调用LLM
        response = await llm.call_llm(request)

        return response.content

    async def cleanup(self) -> None:
        """清理资源"""
        if self._llm_interface is not None:
            await self._llm_interface.cleanup()
            self._llm_interface = None


def create_athena_dspy_lm(
    model: str = "openai/gpt-4o-mini",  # 使用LiteLLM格式的模型名
    api_base: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> dspy.LM:
    """创建DSPy LM实例(使用LiteLLM后端)

    推荐方式: 直接使用DSPy的LM类,通过LiteLLM调用各种模型

    Args:
        model: 模型名称,格式为 "provider/model"
               - "openai/gpt-4o-mini" (使用LiteLLM代理到其他服务)
               - "anthropic/claude-3-sonnet"
               - 或配置本地模型
        api_base: API基础URL(用于本地模型)
        api_key: API密钥
        **kwargs: 额外参数

    Returns:
        DSPy LM实例
    """
    # 尝试配置环境变量以使用Athena的GLM服务
    # 如果Athena有GLM API端点,可以在这里配置

    lm = dspy.LM(model=model, api_base=api_base, api_key=api_key, **kwargs)

    logger.info(f"DSPy LM创建成功,模型: {model}")

    return lm


def get_athena_llm_client(model_type: str = "patent_analysis", **kwargs) -> AthenaLLMDirect:
    """获取Athena LLM客户端(直接调用)

    Args:
        model_type: 模型类型
        **kwargs: 额外参数

    Returns:
        AthenaLLMDirect实例
    """
    return AthenaLLMDirect(model_type=model_type, **kwargs)


# 用于DSPy的自定义Module(包装Athena LLM)
class AthenaLLMModule(dspy.Module):
    """使用Athena LLM的DSPy Module"""

    def __init__(self, signature: dspy.Signature, model_type: str = "patent_analysis", **kwargs):
        """初始化

        Args:
            signature: DSPy Signature
            model_type: Athena模型类型
            **kwargs: 额外参数
        """
        super().__init__()
        self.signature = signature
        self.model_type = model_type
        self.llm = AthenaLLMDirect(model_type=model_type, **kwargs)

    def forward(self, **kwargs) -> Any:
        """执行前向传播

        Args:
            **kwargs: 输入字段

        Returns:
            DSPy Prediction
        """
        # 构建提示词
        prompt = self._build_prompt(kwargs)

        # 调用LLM
        response = self.llm.generate(prompt)

        # 解析响应
        return self._parse_response(response)

    def _build_prompt(self, inputs: dict[str, Any]) -> str:
        """构建提示词"""
        prompt_parts = []

        # 添加输入字段
        for field_name, field_value in inputs.items():
            if field_value:
                prompt_parts.append(f"{field_name}: {field_value}")

        return "\n\n".join(prompt_parts)

    def _parse_response(self, response: str) -> dspy.Prediction:
        """解析LLM响应为DSPy Prediction"""
        # 根据Signature的输出字段解析响应
        output_fields = self.signature.output_fields.keys()

        prediction_dict = {}
        for field_name in output_fields:
            # 简化实现:将整个响应作为第一个输出字段
            prediction_dict[field_name] = response

        return dspy.Prediction(**prediction_dict)


# 便捷函数
def create_athena_module(
    signature: dspy.Signature, model_type: str = "patent_analysis", **kwargs
) -> AthenaLLMModule:
    """创建使用Athena LLM的DSPy Module

    Args:
        signature: DSPy Signature
        model_type: Athena模型类型
        **kwargs: 额外参数

    Returns:
        AthenaLLMModule实例
    """
    return AthenaLLMModule(signature=signature, model_type=model_type, **kwargs)


# 导出
__all__ = [
    "ATHENA_LLM_AVAILABLE",
    "AthenaLLMDirect",
    "AthenaLLMModule",
    "create_athena_dspy_lm",
    "create_athena_module",
    "get_athena_llm_client",
]

