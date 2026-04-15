#!/usr/bin/env python3
"""
DSPy LM后端配置
DSPy Language Model Backend Configuration

支持GLM-4系列和DeepSeek系列模型
Supports GLM-4 series and DeepSeek series models

作者: 小娜·天秤女神
创建时间: 2025-12-29
版本: 1.0.0
"""

from __future__ import annotations
import logging
import os
from typing import Any

import dspy

logger = logging.getLogger(__name__)


# 模型配置映射
MODEL_CONFIGS = {
    # GLM系列 (智谱AI) - 使用zai前缀(LiteLLM格式)
    # 根据https://docs.litellm.ai/docs/providers/zai
    "glm-4-plus": {
        "model_str": "zai/glm-4-plus",
        "api_key_env": "ZHIPUAI_API_KEY",
    },
    "glm-4.5": {
        "model_str": "zai/glm-4.5",
        "api_key_env": "ZHIPUAI_API_KEY",
    },
    "glm-4.6": {
        "model_str": "zai/glm-4.6",
        "api_key_env": "ZHIPUAI_API_KEY",
    },
    "glm-4.7": {
        "model_str": "zai/glm-4.7",
        "api_key_env": "ZHIPUAI_API_KEY",
    },
    "glm-4-air": {
        "model_str": "zai/glm-4-air",
        "api_key_env": "ZHIPUAI_API_KEY",
    },
    "glm-4-flash": {
        "model_str": "zai/glm-4-flash",
        "api_key_env": "ZHIPUAI_API_KEY",
    },
    "glm-4.7-flash": {
        "model_str": "zai/glm-4.7-flash",
        "api_key_env": "ZHIPUAI_API_KEY",
    },
    # DeepSeek系列
    "deepseek-chat": {
        "model_str": "deepseek/deepseek-chat",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "deepseek-coder": {
        "model_str": "deepseek/deepseek-coder",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    # OpenAI系列 (备用)
    "gpt-4o": {
        "model_str": "openai/gpt-4o",
        "api_key_env": "OPENAI_API_KEY",
    },
    "gpt-4o-mini": {
        "model_str": "openai/gpt-4o-mini",
        "api_key_env": "OPENAI_API_KEY",
    },
}


def create_lm(model_name: str = "glm-4-plus", api_key: str | None = None, **kwargs) -> dspy.LM:
    """创建DSPy LM实例

    Args:
        model_name: 模型名称,默认为glm-4-plus
        api_key: API密钥,如果为None则从环境变量读取
        **kwargs: 其他LM参数

    Returns:
        dspy.LM实例

    Raises:
        ValueError: 如果模型名称不支持
    """
    if model_name not in MODEL_CONFIGS:
        available = ", ".join(MODEL_CONFIGS.keys())
        raise ValueError(f"不支持的模型: {model_name}. 可用模型: {available}")

    config = MODEL_CONFIGS[model_name]

    # 获取API密钥
    if api_key is None:
        api_key = os.getenv(config["api_key_env"])
        if not api_key:
            logger.warning(f"未找到环境变量 {config['api_key_env']},使用测试密钥")
            api_key = "test-key-for-development"

    # 构建LM参数
    lm_kwargs = {"model": config["model_str"], "api_key": api_key, **kwargs}

    # 创建LM实例
    try:
        lm = dspy.LM(**lm_kwargs)
        logger.info(f"成功创建LM: {model_name} ({config['model_str']})")
        return lm
    except Exception as e:
        logger.error(f"创建LM失败: {e}")
        raise


def configure_dspy_lm(model_name: str = "glm-4-plus", max_workers: int = 4, **lm_kwargs) -> dspy.LM:
    """配置DSPy全局LM

    Args:
        model_name: 模型名称,默认为glm-4-plus
        max_workers: 最大工作线程数
        **lm_kwargs: LM参数

    Returns:
        配置的dspy.LM实例
    """
    # 创建LM
    lm = create_lm(model_name, **lm_kwargs)

    # 配置DSPy
    dspy.configure(lm=lm, max_workers=max_workers)

    logger.info(f"DSPy已配置: {model_name}, max_workers={max_workers}")
    return lm


def configure_dspy_lm_with_fallback(
    primary_model: str = "glm-4-plus",
    fallback_model: str = "deepseek-chat",
    max_workers: int = 4,
    **lm_kwargs,
) -> dspy.LM:
    """配置DSPy全局LM,支持回退

    Args:
        primary_model: 主模型
        fallback_model: 回退模型
        max_workers: 最大工作线程数
        **lm_kwargs: LM参数

    Returns:
        配置的dspy.LM实例
    """
    # 尝试主模型
    try:
        return configure_dspy_lm(primary_model, max_workers, **lm_kwargs)
    except Exception as e:
        logger.warning(f"主模型 {primary_model} 配置失败: {e}")
        logger.info(f"尝试回退模型: {fallback_model}")

        try:
            return configure_dspy_lm(fallback_model, max_workers, **lm_kwargs)
        except Exception as fallback_error:
            logger.error(f"回退模型 {fallback_model} 也配置失败: {fallback_error}")
            raise


def get_available_models() -> list[str]:
    """获取所有可用的模型列表

    Returns:
        模型名称列表
    """
    return list(MODEL_CONFIGS.keys())


def get_model_info(model_name: str) -> dict[str, Any]:
    """获取模型配置信息

    Args:
        model_name: 模型名称

    Returns:
        模型配置字典
    """
    if model_name not in MODEL_CONFIGS:
        raise ValueError(f"不支持的模型: {model_name}")

    return MODEL_CONFIGS[model_name].copy()


# 便捷配置函数
def setup_glm_4_plus(api_key: str | None = None) -> dspy.LM:
    """快速设置GLM-4-Plus

    Args:
        api_key: API密钥

    Returns:
        dspy.LM实例
    """
    return configure_dspy_lm("glm-4-plus", api_key=api_key)


def setup_deepseek_chat(api_key: str | None = None) -> dspy.LM:
    """快速设置DeepSeek Chat

    Args:
        api_key: API密钥

    Returns:
        dspy.LM实例
    """
    return configure_dspy_lm("deepseek-chat", api_key=api_key)


# 主程序测试
def main() -> None:
    """测试LM配置"""
    import argparse

    parser = argparse.ArgumentParser(description="DSPy LM配置测试")
    parser.add_argument(
        "--model",
        default="glm-4-plus",
        help=f"模型名称 (可选: {', '.join(get_available_models())})",
    )
    parser.add_argument("--test", action="store_true", help="运行简单测试")

    args = parser.parse_args()

    # 配置LM
    print(f"配置DSPy LM: {args.model}")
    lm = configure_dspy_lm(args.model)

    print("✓ LM配置成功")
    print(f"  模型: {lm.model}")

    # 运行测试
    if args.test:
        print("\n运行简单测试...")
        from dspy.primitives.example import Example

        test_example = Example(
            background="测试背景信息", technical_field="测试领域", patent_number="TEST123"
        )

        print(f"测试示例: {test_example}")
        print("✓ 测试完成")

    return lm


if __name__ == "__main__":
    main()
