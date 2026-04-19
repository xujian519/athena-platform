"""
模型API能力矩阵

参考 kode-agent 的 ModelCapabilities 设计，定义模型在 API 层面的能力差异。
包括 API 架构、参数命名、工具调用模式、状态管理等维度的能力声明。

用途：让适配器层根据能力矩阵自动选择正确的 API 参数和调用方式，
而不是为每个模型硬编码适配逻辑。

Author: Athena Team
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ModelAPICapabilities:
    """
    模型API能力定义

    描述一个模型在 API 层面的具体能力，用于适配器自动选择正确的调用方式。
    参考 kode-agent 的 ModelCapabilities 接口设计。

    Example:
        cap = MODEL_API_CAPABILITIES['deepseek-chat']
        max_tokens_field = cap.max_tokens_field  # 'max_tokens'
        if cap.supports_parallel_calls:
            # 可以在一个请求中发送多个工具调用
    """

    # API架构
    api_architecture: str = 'chat_completions'
    # 'chat_completions' - OpenAI Chat Completions API（最通用）
    # 'responses_api' - OpenAI Responses API（GPT-5等新模型）

    # 参数命名约定
    max_tokens_field: str = 'max_tokens'
    # 'max_tokens' - 标准命名
    # 'max_completion_tokens' - o1系列模型
    # 'max_output_tokens' - GPT-5系列模型

    # 温度参数模式
    temperature_mode: str = 'flexible'
    # 'flexible' - 支持自定义温度
    # 'fixed_one' - 固定为1（o1系列等推理模型）
    # 'restricted' - 受限范围

    # 推理能力
    supports_reasoning_effort: bool = False  # 是否支持 reasoning_effort 参数
    supports_verbosity: bool = False         # 是否支持 verbosity 参数
    supports_thinking: bool = False          # 是否支持深度思考模式

    # 工具调用
    tool_calling_mode: str = 'function_calling'
    # 'none' - 不支持工具调用
    # 'function_calling' - 标准 function calling
    # 'custom_tools' - 自定义工具格式（Responses API）

    supports_parallel_calls: bool = True     # 是否支持并行工具调用
    supports_allowed_tools: bool = False     # 是否支持 allowed_tools 过滤

    # 状态管理
    supports_response_id: bool = False       # 是否支持 response_id
    supports_conversation_chaining: bool = False  # 是否支持对话链式

    # 流式输出
    supports_streaming: bool = True
    streaming_includes_usage: bool = True    # 流式响应是否包含 usage

    def get_temperature(self) -> float | None:
        """根据能力返回合适的温度值"""
        if self.temperature_mode == 'fixed_one':
            return None  # 不设置温度，让API使用默认值
        if self.temperature_mode == 'restricted':
            return 0.7
        return 0.7  # flexible

    def get_max_tokens_param_name(self) -> str:
        """获取 max_tokens 参数名"""
        return self.max_tokens_field


# ============================================================
# 模型 → 能力映射注册表
# 使用工厂函数确保每个模型获取独立的 capability 实例
# ============================================================

# 能力模板工厂（避免共享可变实例）
def _make_deepseek_chat_caps() -> ModelAPICapabilities:
    return ModelAPICapabilities(
        api_architecture='chat_completions',
        max_tokens_field='max_tokens',
        temperature_mode='flexible',
        supports_thinking=False,
        supports_streaming=True,
        streaming_includes_usage=True,
        supports_parallel_calls=True,
    )

def _make_deepseek_reasoner_caps() -> ModelAPICapabilities:
    return ModelAPICapabilities(
        api_architecture='chat_completions',
        max_tokens_field='max_tokens',
        temperature_mode='flexible',
        supports_thinking=True,
        supports_reasoning_effort=False,
        supports_streaming=True,
        streaming_includes_usage=True,
        supports_parallel_calls=True,
    )

def _make_glm4_caps() -> ModelAPICapabilities:
    return ModelAPICapabilities(
        api_architecture='chat_completions',
        max_tokens_field='max_tokens',
        temperature_mode='flexible',
        tool_calling_mode='function_calling',
        supports_streaming=True,
        streaming_includes_usage=True,
        supports_parallel_calls=True,
    )

def _make_qwen_caps() -> ModelAPICapabilities:
    return ModelAPICapabilities(
        api_architecture='chat_completions',
        max_tokens_field='max_tokens',
        temperature_mode='flexible',
        supports_streaming=True,
        streaming_includes_usage=True,
        supports_parallel_calls=True,
    )


MODEL_API_CAPABILITIES: dict[str, ModelAPICapabilities] = {
    # DeepSeek 系列
    'deepseek-chat': _make_deepseek_chat_caps(),
    'deepseek-coder-v2': _make_deepseek_chat_caps(),
    'deepseek-reasoner': _make_deepseek_reasoner_caps(),

    # GLM 系列
    'glm-4-plus': _make_glm4_caps(),
    'glm-4-flash': _make_glm4_caps(),
    'glm47flash': _make_glm4_caps(),

    # Qwen 云端
    'qwen-plus': _make_qwen_caps(),
    'qwen-max': _make_qwen_caps(),
    'qwen-vl-max': _make_qwen_caps(),
    'qwen-vl-plus': _make_qwen_caps(),

    # 本地 Qwen
    'qwen3.5': _make_qwen_caps(),
    'qwen2.5-7b-instruct-gguf': _make_qwen_caps(),
}

# 能力缓存（避免重复推断，线程安全）
_capability_cache: dict[str, ModelAPICapabilities] = {}
_cache_lock = threading.Lock()


def get_model_api_capabilities(model_id: str) -> ModelAPICapabilities:
    """
    获取模型的API能力定义

    优先级：
    1. 精确匹配注册表
    2. 名称模式推断（如包含 'deepseek'）
    3. 默认返回标准 Chat Completions 能力

    Args:
        model_id: 模型ID

    Returns:
        ModelAPICapabilities: 模型API能力定义
    """
    # 快速路径：检查缓存（无锁读）
    if model_id in _capability_cache:
        return _capability_cache[model_id]

    with _cache_lock:
        # 双重检查
        if model_id in _capability_cache:
            return _capability_cache[model_id]

        caps = _resolve_capabilities(model_id)
        _capability_cache[model_id] = caps
        return caps


def _resolve_capabilities(model_id: str) -> ModelAPICapabilities:
    """解析模型能力（在锁内调用）"""
    # 精确匹配
    if model_id in MODEL_API_CAPABILITIES:
        return MODEL_API_CAPABILITIES[model_id]

    # 名称模式推断
    lower = model_id.lower()

    if 'deepseek' in lower and ('reason' in lower or 'r1' in lower):
        caps = _make_deepseek_reasoner_caps()
    elif 'deepseek' in lower:
        caps = _make_deepseek_chat_caps()
    elif 'glm' in lower:
        caps = _make_glm4_caps()
    elif 'qwen' in lower:
        caps = _make_qwen_caps()
    elif 'mlx' in lower or model_id in ('glm47flash',):
        caps = ModelAPICapabilities(
            api_architecture='chat_completions',
            max_tokens_field='max_tokens',
            temperature_mode='flexible',
            supports_streaming=True,
            streaming_includes_usage=False,
            supports_parallel_calls=False,
        )
    elif 'ollama' in lower:
        caps = ModelAPICapabilities(
            api_architecture='chat_completions',
            max_tokens_field='max_tokens',
            temperature_mode='flexible',
            supports_streaming=True,
            streaming_includes_usage=False,
            supports_parallel_calls=False,
        )
    else:
        # 默认使用标准 Chat Completions 能力
        caps = ModelAPICapabilities()

    return caps


def register_model_api_capabilities(model_id: str, caps: ModelAPICapabilities) -> None:
    """
    注册模型的API能力定义

    Args:
        model_id: 模型ID
        caps: API能力定义
    """
    MODEL_API_CAPABILITIES[model_id] = caps
    _capability_cache.pop(model_id, None)  # 清除缓存
    logger.info(f"✅ 注册模型API能力: {model_id}")


def list_model_api_capabilities() -> dict[str, dict[str, Any]]:
    """列出所有已注册模型的API能力摘要"""
    result = {}
    for model_id, caps in MODEL_API_CAPABILITIES.items():
        result[model_id] = {
            'api_architecture': caps.api_architecture,
            'max_tokens_field': caps.max_tokens_field,
            'temperature_mode': caps.temperature_mode,
            'supports_thinking': caps.supports_thinking,
            'supports_parallel_calls': caps.supports_parallel_calls,
            'supports_streaming': caps.supports_streaming,
        }
    return result
