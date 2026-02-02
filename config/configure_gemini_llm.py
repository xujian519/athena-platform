#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置 Google Gemini 大模型
Configure Google Gemini LLM

将您的 Google Gemini API 密钥集成到 Athena 系统中。

作者: Athena AI 系统
创建时间: 2025年12月11日
版本: 1.0.0
"""

import json
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import logging
import sys
from datetime import datetime, timezone

from domestic_llm_integration import DomesticLLMManager, LLMProvider

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def configure_gemini_llm() -> Any:
    """配置 Google Gemini 大模型"""
    logger.info('🤖 配置 Google Gemini Pro 大模型')
    logger.info(str('=' * 40))
    
    # 提示用户输入API密钥
    api_key = input('🔑 请输入您的 Google Gemini API 密钥: ').strip()

    if not api_key:
        logger.info("❌ 未提供 API 密钥。配置已取消。\n")
        return None, None

    # 创建大模型管理器
    llm_manager = DomesticLLMManager()

    # 注册 Gemini
    try:
        llm_manager.register_provider(
            provider=LLMProvider.GEMINI,
            api_key=api_key,
            model_name='gemini-1.5-pro-latest'
        )
        logger.info(f"✅ Google Gemini 已成功配置")
        logger.info(f"   API Key: ...{api_key[-4:]}")

        # 测试连接
        if test_gemini_connection(llm_manager):
            return llm_manager, api_key
        else:
            return None, None

    except Exception as e:
        logger.info(f"❌ 配置失败: {e}")
        return None, None

def test_gemini_connection(llm_manager) -> Any:
    """测试 Gemini API 连接"""
    logger.info(f"\n🔍 测试 Google Gemini API 连接...")

    test_prompt = '请用中文简单介绍一下你自己'

    logger.info(f"\n1. 测试描述: {test_prompt}")

    try:
        # 调用 Gemini 生成文本
        # 注意：我们复用了 generate_drawing_description，但它现在是通用的
        response_text = llm_manager.generate_drawing_description(test_prompt, LLMProvider.GEMINI)

        logger.info(f"   ✅ Gemini API 调用成功")
        logger.info(f"   📝 模型回复: {response_text[:150]}...")
        logger.info(f"   📊 模型: Google Gemini 1.5 Pro")
        logger.info(f"\n🎉 Google Gemini API 测试通过！")
        return True

    except Exception as e:
        logger.info(f"   ❌ API 调用失败: {e}")
        logger.info(f"   请检查您的 API 密钥是否正确，以及网络连接是否正常。\n")
        return False

def save_config(api_key) -> None:
    """保存配置到文件"""
    if not api_key:
        return False

    config = {
        'gemini_api_key': api_key,
        'provider': 'gemini',
        'model': 'gemini-1.5-pro-latest',
        'configured_at': datetime.now(timezone.utc).isoformat(),
        'status': 'active'
    }

    # 使用相对路径
    config_file = 'config/llm_config.json'

    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        logger.info(f"\n💾 配置已保存到: {config_file}")
        return True
    except Exception as e:
        logger.info(f"\n❌ 保存配置失败: {e}")
        return False

def main() -> None:
    """主函数"""
    logger.info('🚀 Google Gemini 大模型配置工具')
    logger.info(str('=' * 50))

    # 1. 配置 Gemini
    llm_manager, api_key = configure_gemini_llm()
    if not llm_manager:
        logger.info("\n❌ Gemini 配置失败，请检查您的输入和网络。\n")
        return 1

    # 2. 保存配置
    if not save_config(api_key):
        return 1

    logger.info(f"\n\n🎉 配置完成！")
    logger.info(str('=' * 50))
    logger.info('✅ Google Gemini 1.5 Pro 已成功集成')
    logger.info('✅ API 连接测试通过')
    logger.info('✅ 配置文件已更新')

    logger.info(f"\n💡 现在，系统将默认使用 Gemini Pro 作为其核心语言模型。\n")
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\n👋 配置被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.info(f"\n❌ 配置过程中发生意外错误: {e}")
        sys.exit(1)
