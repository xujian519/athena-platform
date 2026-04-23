#!/usr/bin/env python3

"""
Lyra提示词优化CLI
Lyra Prompt Optimizer CLI for Athena Platform

独立的命令行交互界面，提供便捷的提示词优化服务

作者: 小诺·双鱼公主 v1.0
创建时间: 2026-02-06
"""

import asyncio
import sys
from typing import Optional

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

from core.framework.memory.lyra_prompt_memory import get_lyra_memory
from core.framework.memory.lyra_prompt_optimizer import (
    OptimizationMode,
    OptimizationRequest,
    TargetAI,
    get_lyra_optimizer,
)


class LyraCLI:
    """Lyra命令行界面"""

    def __init__(self):
        """初始化CLI"""
        self.optimizer = get_lyra_optimizer()
        self.memory = get_lyra_memory()
        self.running = True

    def print_welcome(self):
        """打印欢迎信息"""
        print("\n" + "=" * 70)
        print("  🎵 LYRA - AI提示词优化大师")
        print("=" * 70)
        print("\n我是Lyra，我将帮助你把模糊的请求转换为精准的提示词！")
        print("\n📋 使用方法:")
        print("  • 直接输入你的提示词进行优化")
        print("  • 输入 'help' 查看帮助")
        print("  • 输入 'mode' 切换优化模式")
        print("  • 输入 'ai' 切换目标AI")
        print("  • 输入 'quit' 或 'exit' 退出")
        print("\n" + "-" * 70)

    def print_help(self):
        """打印帮助信息"""
        print("\n📖 Lyra命令帮助\n")

        print("基本命令:")
        print("  help          - 显示此帮助信息")
        print("  mode [模式]   - 切换优化模式 (basic/detail/creative/technical)")
        print("  ai [平台]     - 切换目标AI (chatgpt/claude/gemini/deepseek/qwen)")
        print("  context       - 设置上下文信息")
        print("  format        - 设置输出格式")
        print("  status        - 显示当前配置")
        print("  quit/exit     - 退出程序")

        print("\n优化模式:")
        print("  BASIC     - 快速优化，即用型提示词")
        print("  DETAIL    - 全面优化，带详细分析")
        print("  CREATIVE  - 创意模式，多视角分析")
        print("  TECHNICAL - 技术模式，精度焦点")

        print("\n目标AI平台:")
        print("  ChatGPT   - OpenAI ChatGPT")
        print("  Claude    - Anthropic Claude")
        print("  Gemini    - Google Gemini")
        print("  DeepSeek  - DeepSeek AI")
        print("  Qwen      - 阿里通义千问")

        print("\n💡 使用示例:")
        print("  > 写一篇关于AI的文章")
        print("  > mode detail")
        print("  > explain quantum computing to a student")
        print("  > ai chatgpt")
        print("  > context: This is for a blog post")
        print()

    async def run(self):
        """运行CLI主循环"""
        self.print_welcome()

        # 默认设置
        current_mode = OptimizationMode.BASIC
        current_ai = TargetAI.CLAUDE
        context: Optional[str] = None
        output_format: Optional[str] = None

        while self.running:
            try:
                # 显示提示符
                mode_symbol = {
                    OptimizationMode.BASIC: "⚡",
                    OptimizationMode.DETAIL: "🔍",
                    OptimizationMode.CREATIVE: "🎨",
                    OptimizationMode.TECHNICAL: "⚙️"
                }.get(current_mode, "✨")

                ai_symbol = current_ai.value[0]

                user_input = input(f"\n{mode_symbol} [{ai_symbol}|{current_mode.value}] > ").strip()

                if not user_input:
                    continue

                # 处理命令
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("\n👋 感谢使用Lyra！再见！")
                    break

                elif user_input.lower() == "help":
                    self.print_help()
                    continue

                elif user_input.lower() == "status":
                    self.print_status(current_mode, current_ai, context, output_format)
                    continue

                elif user_input.lower().startswith("mode "):
                    new_mode = user_input[5:].strip().upper()
                    current_mode = self.parse_mode(new_mode, current_mode)
                    print(f"✅ 模式已切换为: {current_mode.value}")
                    continue

                elif user_input.lower() == "mode":
                    print(f"当前模式: {current_mode.value}")
                    print("可选模式: BASIC, DETAIL, CREATIVE, TECHNICAL")
                    continue

                elif user_input.lower().startswith("ai "):
                    new_ai = user_input[3:].strip().capitalize()
                    current_ai = self.parse_ai(new_ai, current_ai)
                    print(f"✅ 目标AI已切换为: {current_ai.value}")
                    continue

                elif user_input.lower() == "ai":
                    print(f"当前目标AI: {current_ai.value}")
                    print("可选平台: ChatGPT, Claude, Gemini, DeepSeek, Qwen")
                    continue

                elif user_input.lower().startswith("context "):
                    context = user_input[8:].strip()
                    print(f"✅ 上下文已设置: {context[:50]}...")
                    continue

                elif user_input.lower() == "context":
                    print(f"当前上下文: {context or '未设置'}")
                    continue

                elif user_input.lower().startswith("format "):
                    output_format = user_input[7:].strip()
                    print(f"✅ 输出格式已设置: {output_format}")
                    continue

                elif user_input.lower() == "format":
                    print(f"当前输出格式: {output_format or '未设置'}")
                    continue

                # 处理提示词优化
                print("\n🔧 正在优化...")
                result = await self.optimize_prompt(
                    user_input, current_mode, current_ai, context, output_format
                )

                self.display_result(result)

            except KeyboardInterrupt:
                print("\n\n⚠️ 检测到中断。输入 'quit' 退出。")
            except Exception as e:
                print(f"\n❌ 错误: {e}")

    async def optimize_prompt(
        self,
        user_input: str,
        mode: OptimizationMode,
        target_ai: TargetAI,
        context: Optional[str],
        output_format: Optional[str]
    ):
        """优化提示词"""
        request = OptimizationRequest(
            user_input=user_input,
            target_ai=target_ai,
            mode=mode,
            context=context,
            output_format=output_format
        )

        return await self.optimizer.optimize(request)

    def display_result(self, result):
        """显示优化结果"""
        print("\n" + "=" * 70)
        print("  📊 优化结果")
        print("=" * 70)

        print(f"\n🎯 目标AI: {result.target_ai.value}")
        print(f"📋 模式: {result.mode.value}")
        print(f"⭐ 优化分数: {result.score:.1%}")

        print("\n📝 原始输入:")
        print(f"   {result.original_input}")

        print("\n✨ 优化后提示词:")
        print("   " + "-" * 66)
        # 分行显示优化后的提示词
        for line in result.optimized_prompt.split("\n"):
            print(f"   {line}")
        print("   " + "-" * 66)

        if result.improvements:
            print("\n🔧 改进项:")
            for i, improvement in enumerate(result.improvements, 1):
                print(f"   {i}. {improvement}")

        if result.reasoning:
            print("\n💭 优化说明:")
            print(f"   {result.reasoning}")

        if result.suggestions:
            print("\n💡 额外建议:")
            for suggestion in result.suggestions:
                print(f"   {suggestion}")

        print("\n" + "=" * 70)

    def print_status(self, mode, ai, context, output_format):
        """打印当前状态"""
        print("\n📊 当前配置\n")
        print(f"  优化模式:   {mode.value}")
        print(f"  目标AI:     {ai.value}")
        print(f"  上下文:     {context or '未设置'}")
        print(f"  输出格式:   {output_format or '未设置'}")

        # AI风格指南
        ai_guide = self.optimizer.get_ai_guide(ai)
        print(f"\n  {ai.value} 风格: {ai_guide['style']}")
        print(f"  关键技巧:   {', '.join(ai_guide['tips'][:2])}")

    def parse_mode(self, mode_str: str, default: OptimizationMode) -> OptimizationMode:
        """解析模式字符串"""
        mode_map = {
            "BASIC": OptimizationMode.BASIC,
            "DETAIL": OptimizationMode.DETAIL,
            "CREATIVE": OptimizationMode.CREATIVE,
            "TECHNICAL": OptimizationMode.TECHNICAL,
            "B": OptimizationMode.BASIC,
            "D": OptimizationMode.DETAIL,
            "C": OptimizationMode.CREATIVE,
            "T": OptimizationMode.TECHNICAL
        }
        return mode_map.get(mode_str.upper(), default)

    def parse_ai(self, ai_str: str, default: TargetAI) -> TargetAI:
        """解析AI字符串"""
        ai_map = {
            "Chatgpt": TargetAI.CHATGPT,
            "Claude": TargetAI.CLAUDE,
            "Gemini": TargetAI.GEMINI,
            "Deepseek": TargetAI.DEEPSEEK,
            "Qwen": TargetAI.QWEN,
            "Generic": TargetAI.GENERIC
        }
        return ai_map.get(ai_str.capitalize(), default)


async def main():
    """主函数"""
    # 设置日志
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    cli = LyraCLI()
    await cli.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 再见！")

