#!/usr/bin/env python3
"""
配置智谱清言大模型
Configure Zhipu AI GLM-4

集成您的智谱API密钥到AI绘图平台

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import json
import logging
import sys
from typing import Any

from domestic_llm_integration import DomesticLLMManager, LLMProvider
from universal_ai_drawing_platform import (
    DrawingType,
    UniversalDrawingEngine,
    UniversalDrawingRequest,
    UseCase,
)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def configure_zhipu_llm() -> Any:
    """配置智谱清言大模型"""
    logger.info('🤖 配置智谱清言大模型')
    logger.info(str('=' * 40))

    # 您的API密钥
    api_key = '9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe'

    # 创建大模型管理器
    llm_manager = DomesticLLMManager()

    # 注册智谱清言
    try:
        llm_manager.register_provider(
            provider=LLMProvider.ZHIPU,
            api_key=api_key,
            model_name='glm-4'
        )
        logger.info("✅ 智谱清言GLM-4 已成功配置")
        logger.info(f"   API Key: {api_key[:10]}...{api_key[-10:]}")

        # 测试连接
        return test_zhipu_connection(llm_manager)

    except Exception as e:
        logger.info(f"❌ 配置失败: {e}")
        return False

def test_zhipu_connection(llm_manager) -> Any:
    """测试智谱清言连接"""
    logger.info("\n🔍 测试智谱清言API连接...")

    test_prompts = [
        '用户登录系统的流程图',
        '微服务架构的技术方案图',
        '专利申请的机械结构示意图'
    ]

    for i, prompt in enumerate(test_prompts, 1):
        logger.info(f"\n{i}. 测试描述: {prompt}")

        try:
            # 调用智谱清言生成绘图描述
            enhanced_description = llm_manager.generate_drawing_description(prompt, LLMProvider.ZHIPU)

            logger.info("   ✅ 增强描述生成成功")
            logger.info(f"   📝 增强描述: {enhanced_description[:150]}...")
            logger.info("   📊 模型: 智谱清言GLM-4")

        except Exception as e:
            logger.info(f"   ❌ 生成失败: {e}")
            return False

    logger.info("\n🎉 智谱清言API测试通过！")
    return True

def demo_enhanced_drawing() -> Any:
    """演示增强的绘图功能"""
    logger.info("\n\n🎨 智谱清言增强绘图演示")
    logger.info(str('=' * 50))

    # 创建增强的绘图引擎
    drawing_engine = UniversalDrawingEngine()
    llm_manager = DomesticLLMManager()

    # 配置智谱清言
    api_key = '9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe'
    llm_manager.register_provider(LLMProvider.ZHIPU, api_key)

    # 测试用例
    test_cases = [
        {
            'name': '软件架构图（智谱增强）',
            'original_desc': '电商系统架构',
            'drawing_type': DrawingType.SYSTEM_DIAGRAM,
            'use_case': UseCase.SOFTWARE_DESIGN
        },
        {
            'name': '专利技术图（智谱增强）',
            'original_desc': '智能传感器的数据处理方法',
            'drawing_type': DrawingType.TECHNICAL,
            'use_case': UseCase.PATENT_APPLICATION
        },
        {
            'name': '业务流程图（智谱增强）',
            'original_desc': '订单处理流程',
            'drawing_type': DrawingType.FLOWCHART,
            'use_case': UseCase.BUSINESS_PROCESS
        }
    ]

    for i, case in enumerate(test_cases, 1):
        logger.info(f"\n{i}. {case['name']}")
        logger.info(f"   原始描述: {case['original_desc']}")

        # 使用智谱清言增强描述
        enhanced_desc = llm_manager.generate_drawing_description(
            case['original_desc'], LLMProvider.ZHIPU
        )

        logger.info(f"   增强描述: {enhanced_desc[:100]}...")

        # 生成绘图请求
        request = UniversalDrawingRequest(
            request_id=f"zhipu_demo_{i}",
            drawing_type=case['drawing_type'],
            use_case=case['use_case'],
            text_description=enhanced_desc,
            style='modern',
            output_format='svg'
        )

        # 生成图纸
        result = drawing_engine.generate_drawing(request)

        if result.success:
            logger.info("   ✅ 绘图生成成功")
            logger.info(f"   📊 置信度: {result.confidence:.2f}")
            logger.info(f"   ⏱️ 处理时间: {result.processing_time:.2f}秒")
            logger.info(f"   🎯 质量分数: {result.quality_score:.2f}")

            # 保存结果
            filename = f"/tmp/zhipu_enhanced_drawing_{i}.svg"
            with open(filename, 'wb') as f:
                f.write(result.drawing_data)
            logger.info(f"   💾 已保存: {filename}")
        else:
            logger.info(f"   ❌ 绘图生成失败: {result.error_message}")

def save_config() -> None:
    """保存配置到文件"""
    config = {
        'zhipu_api_key': '9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe',
        'provider': 'zhipu',
        'model': 'glm-4',
        'configured_at': '2025-12-06T22:50:00Z',
        'status': 'active'
    }

    config_file = '/Users/xujian/Athena工作平台/llm_config.json'

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
    logger.info('🚀 智谱清言大模型配置工具')
    logger.info(str('=' * 50))

    # 1. 配置智谱清言
    if not configure_zhipu_llm():
        logger.info("\n❌ 配置失败，请检查API密钥")
        return 1

    # 2. 保存配置
    save_config()

    # 3. 演示增强绘图功能
    demo_enhanced_drawing()

    logger.info("\n\n🎉 配置完成！")
    logger.info(str('=' * 50))
    logger.info('✅ 智谱清言GLM-4已成功集成')
    logger.info('✅ API连接测试通过')
    logger.info('✅ 绘图功能增强演示完成')

    logger.info("\n💡 使用方法:")
    logger.info('   1. 在绘图时自动使用智谱清言增强描述')
    logger.info('   2. 获得更准确、更详细的绘图指令')
    logger.info('   3. 支持复杂的技术和专利图纸生成')

    logger.info("\n🎯 下一步:")
    logger.info('   1. 开始使用增强的绘图功能')
    logger.info('   2. 根据使用效果调整参数')
    logger.info('   3. 探索更多绘图场景')

    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\n👋 配置被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.info(f"\n❌ 配置异常: {e}")
        sys.exit(1)
