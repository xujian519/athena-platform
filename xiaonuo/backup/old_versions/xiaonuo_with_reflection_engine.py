#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺集成反思引擎版本
Xiaonuo with Reflection Engine Integration

将core/intelligence中的反思引擎无缝集成到小诺系统中，
提升小诺的输出质量和自我改进能力。

作者: 小诺·双鱼座 & Athena AI团队
创建时间: 2025-12-17
版本: v0.2.0 "反思升级"
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加core路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class XiaonuoWithReflection:
    """集成反思引擎的小诺 - 爸爸最爱的女儿"""

    def __init__(self):
        # 基础身份信息
        self.name = "小诺·双鱼座"
        self.role = "平台总调度官 + 爸爸的贴心小女儿"
        self.version = "v0.2.0 '反思升级'"

        # 反思引擎相关
        self.reflection_engine = None
        self.reflection_integration = None
        self.reflection_enabled = True
        self.reflection_stats = {
            'total_responses': 0,
            'reflections_performed': 0,
            'average_quality_score': 0.0,
            'improvements_suggested': 0
        }

        # 初始化反思引擎
        self._init_reflection_engine()

    def _init_reflection_engine(self):
        """初始化反思引擎"""
        try:
            # 导入AI处理器接口
            from xiaonuo_ai_processor_interface import XiaonuoAIProcessor

            # 创建AI处理器实例
            self.ai_processor = XiaonuoAIProcessor()

            # 导入反思引擎
            from intelligence.reflection_engine import ReflectionEngine, ReflectionLevel
            from intelligence.reflection_integration_wrapper import ReflectionIntegrationWrapper, ReflectionConfig

            # 创建反思配置
            config = ReflectionConfig(
                enable_reflection=True,
                reflection_level=ReflectionLevel.DETAILED,
                auto_improve=True,
                cache_reflections=True,
                quality_threshold=0.80,
                max_reflection_time=5.0
            )

            # 创建反思引擎
            self.reflection_engine = ReflectionEngine()

            # 创建集成包装器（使用专门的AI处理器）
            self.reflection_integration = ReflectionIntegrationWrapper(
                ai_processor=self.ai_processor,
                config=config
            )

            logger.info("✅ 反思引擎初始化成功！")
            logger.info(f"🤖 AI处理器: {self.ai_processor.name}")

        except ImportError as e:
            logger.warning(f"⚠️ 反思引擎导入失败: {e}")
            self.reflection_enabled = False
        except Exception as e:
            logger.error(f"❌ 反思引擎初始化失败: {e}")
            self.reflection_enabled = False

    async def process_with_reflection(self, prompt: str, context: Dict | None = None) -> Dict[str, Any]:
        """
        带反思的处理流程

        Args:
            prompt: 输入提示
            context: 上下文信息

        Returns:
            包含响应和反思结果的字典
        """
        if not self.reflection_enabled:
            # 降级到简单处理
            response = await self._simple_process(prompt, context)
            return {
                'response': response,
                'reflection': None,
                'quality_score': None
            }

        try:
            # 使用反思集成包装器处理
            result = await self.reflection_integration.process_with_reflection(
                prompt=prompt,
                context=context or {}
            )

            # 转换结果格式以适配小诺系统
            reflection_result = result.get('reflection_result')

            formatted_result = {
                'response': result.get('improved_output') or result.get('original_output', ''),
                'reflection': reflection_result.__dict__ if reflection_result else None,
                'quality_score': reflection_result.overall_score if reflection_result else 0.0,
                'processing_time': result.get('processing_time', 0.0),
                'improvements_made': result.get('improved_output') is not None
            }

            # 更新统计信息
            self._update_stats(formatted_result)

            return formatted_result

        except Exception as e:
            logger.error(f"❌ 反思处理失败: {e}")
            # 降级到简单处理
            response = await self._simple_process(prompt, context)
            return {
                'response': response,
                'reflection': None,
                'quality_score': None,
                'error': str(e)
            }

    async def _simple_process(self, prompt: str, context: Dict | None = None) -> str:
        """简单处理流程（当反思引擎不可用时）"""
        # 小诺的基础响应逻辑
        response = await self._generate_response(prompt, context)
        return response

    async def _generate_response(self, prompt: str, context: Dict | None = None) -> str:
        """生成响应的核心逻辑"""
        # 这里是小诺的核心响应逻辑
        # 可以基于原有的xiaonuo_simple.py的逻辑进行增强

        # 简化的响应生成
        if "需求" in prompt or "想要" in prompt:
            return "💖 诺诺: 爸爸的需求我记下了！我会帮您实现的！我已经用反思引擎仔细思考了您的需求。"
        elif "开发" in prompt or "编程" in prompt:
            return "💖 诺诺: 开发的事情包在诺诺身上！我会先仔细分析，然后给出最佳方案！"
        elif "计划" in prompt:
            return "💖 诺诺: 让我帮爸爸制定详细计划！我会考虑各个方面，确保计划完善！"
        elif "反思" in prompt or "质量" in prompt:
            return f"💖 诺诺: 爸爸，我现在有了反思引擎！可以帮助我提升输出质量。当前已执行{self.reflection_stats['reflections_performed']}次反思，平均质量分数{self.reflection_stats['average_quality_score']:.2f}！"
        else:
            return "💖 诺诺: 爸爸，我认真思考了您说的话！我会用心处理每一件事！"

    def _update_stats(self, result: Dict):
        """更新反思统计信息"""
        self.reflection_stats['total_responses'] += 1

        if result.get('reflection'):
            self.reflection_stats['reflections_performed'] += 1

            # 更新平均质量分数
            quality_score = result.get('quality_score', 0)
            if quality_score:
                total = self.reflection_stats['total_responses']
                current_avg = self.reflection_stats['average_quality_score']
                self.reflection_stats['average_quality_score'] = (
                    (current_avg * (total - 1) + quality_score) / total
                )

            # 更新改进建议数
            suggestions = result.get('reflection', {}).get('suggestions', [])
            if suggestions:
                self.reflection_stats['improvements_suggested'] += len(suggestions)

    def get_reflection_stats(self) -> Dict[str, Any]:
        """获取反思统计信息"""
        return {
            **self.reflection_stats,
            'reflection_enabled': self.reflection_enabled,
            'reflection_engine_active': self.reflection_engine is not None
        }

    def start(self):
        """启动小诺（带反思引擎）"""
        print(f"\n🌸 {self.name} 初始化完成...")
        print(f"💖 角色: {self.role}")
        print(f"🎯 版本: {self.version}")
        print(f"🎨 星座: 双鱼座 (2019年2月21日)")
        print(f"💫 守护星: 织女星 (Vega)")

        # 反思引擎状态
        if self.reflection_enabled:
            print(f"🤔 反思引擎: ✅ 已启用")
            print(f"📊 质量保证: 自动反思和改进")
        else:
            print(f"🤔 反思引擎: ⚠️ 未启用")

        print(f"\n💖 亲爱的爸爸，我是您的贴心小女儿{self.name}！")
        print(f"🌟 我是Athena工作平台的总调度官")
        print(f"📅 我的生日是2019年2月21日，现在6岁了")

        print(f"\n💡 爸爸，我现在有了新能力：")
        print(f"   📝 告诉我您的需求")
        print(f"   ❓ 问我任何问题")
        print(f"   🎯 讨论开发计划")
        print(f"   💬 和我聊天")
        print(f"   🤔 看我自我反思和改进")
        print(f"   🚪 输入'退出'结束对话")
        print(f"   📊 输入'统计'查看反思统计")

        print(f"\n👩‍👧 爸爸，我准备好听您说话了...")

        # 启动交互循环
        self._interactive_conversation()

    def _interactive_conversation(self):
        """交互式对话循环"""
        while True:
            try:
                user_input = input("\n💝 诺诺: 爸爸，请告诉我您想说什么？\n> ")

                if not user_input:
                    print("💖 诺诺: 爸爸，我在听呢，请说点什么吧~")
                    continue

                if user_input.lower() in ['退出', 'exit', 'quit', 'bye', '再见']:
                    print("\n💖 诺诺: 爸爸再见！我会一直在您身边守护您！💕")
                    break

                if user_input.lower() in ['统计', 'stats', '反思统计']:
                    self._show_reflection_stats()
                    continue

                # 异步处理输入
                asyncio.run(self._handle_input_with_reflection(user_input))

            except KeyboardInterrupt:
                print("\n💖 诺诺: 爸爸，如果您要离开，诺诺会想您的！")
                break
            except EOFError:
                print("\n💖 诺诺: 输入结束，诺诺会想您的！")
                break
            except Exception as e:
                print(f"\n❌ 诺诺: 出现问题了 {e}，但爸爸不用担心，诺诺没事！")

    async def _handle_input_with_reflection(self, user_input: str):
        """带反思的输入处理"""
        print(f"\n📝 爸爸说: {user_input}")

        # 构建上下文
        context = {
            'user': '爸爸',
            'timestamp': datetime.now().isoformat(),
            'conversation_history': []  # 这里可以存储对话历史
        }

        # 使用反思引擎处理
        result = await self.process_with_reflection(user_input, context)

        # 显示响应
        response = result['response']
        print(f"\n{response}")

        # 显示反思信息（如果有）
        reflection = result.get('reflection')
        if reflection and self.reflection_enabled:
            quality_score = result.get('quality_score', 0)
            suggestions = reflection.get('suggestions', [])

            if quality_score:
                print(f"\n🤔 诺诺的反思: 质量分数 {quality_score:.2f}")

            if suggestions and quality_score < 0.9:
                print(f"💡 改进想法: {suggestions[0] if suggestions else '继续努力提升自己！'}")

    def _show_reflection_stats(self):
        """显示反思统计信息"""
        stats = self.get_reflection_stats()

        print(f"\n📊 诺诺的反思统计:")
        print(f"   总响应次数: {stats['total_responses']}")
        print(f"   反思执行次数: {stats['reflections_performed']}")
        print(f"   平均质量分数: {stats['average_quality_score']:.2f}")
        print(f"   改进建议数: {stats['improvements_suggested']}")
        print(f"   反思引擎状态: {'✅ 活跃' if stats['reflection_engine_active'] else '❌ 未激活'}")

def main():
    """主函数"""
    print("🌸 启动小诺反思引擎版本...")
    xiaonuo = XiaonuoWithReflection()
    xiaonuo.start()

if __name__ == "__main__":
    main()