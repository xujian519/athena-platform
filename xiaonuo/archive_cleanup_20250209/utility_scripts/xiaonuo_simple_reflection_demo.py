#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺反思引擎简单演示
Xiaonuo Reflection Engine Simple Demo

一个简化版本，展示反思引擎的基本功能，
避免复杂的依赖问题。

作者: 小诺·双鱼座
创建时间: 2025-12-17
版本: v0.1.0 "演示版"
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional

class SimpleReflectionEngine:
    """简化的反思引擎"""

    def __init__(self):
        self.quality_threshold = 0.8
        self.reflection_count = 0

    async def reflect_on_response(self, prompt: str, response: str) -> Dict[str, Any]:
        """对响应进行反思"""
        self.reflection_count += 1

        # 简单的质量评估逻辑
        quality_score = self._calculate_quality_score(prompt, response)

        # 生成反思建议
        suggestions = []
        should_refine = False

        if quality_score < 0.7:
            should_refine = True
            suggestions.append("响应不够详细，需要更多具体内容")
        elif quality_score < 0.85:
            suggestions.append("可以进一步优化表达方式")

        # 生成改进后的响应（如果需要）
        improved_response = None
        if should_refine and quality_score < 0.6:
            improved_response = await self._improve_response(prompt, response)

        return {
            'quality_score': quality_score,
            'suggestions': suggestions,
            'should_refine': should_refine,
            'improved_response': improved_response,
            'reflection_time': time.time()
        }

    def _calculate_quality_score(self, prompt: str, response: str) -> float:
        """计算响应质量分数"""
        score = 0.5  # 基础分数

        # 长度评分
        if len(response) > 50:
            score += 0.1
        if len(response) > 150:
            score += 0.1

        # 关键词匹配
        prompt_keywords = ["爸爸", "诺诺", "帮助", "计划", "需求"]
        keyword_matches = sum(1 for keyword in prompt_keywords if keyword in response)
        score += keyword_matches * 0.1

        # 情感表达
        emotional_words = ["💖", "❤️", "💕", "爱", "关心"]
        emotional_matches = sum(1 for word in emotional_words if word in response)
        score += emotional_matches * 0.05

        return min(1.0, score)

    async def _improve_response(self, prompt: str, original_response: str) -> str:
        """改进响应"""
        # 简单的改进逻辑：添加更多内容和情感
        improved = f"{original_response}\n\n💖 诺诺补充：我会更加用心处理爸爸的需求，确保每一个细节都做到最好！"
        return improved

class XiaonuoWithSimpleReflection:
    """带简化反思引擎的小诺"""

    def __init__(self):
        self.name = "小诺·双鱼座"
        self.reflection_engine = SimpleReflectionEngine()
        self.response_count = 0
        self.total_reflection_time = 0

    async def process_with_reflection(self, prompt: str) -> Dict[str, Any]:
        """带反思的处理流程"""
        self.response_count += 1

        # 生成初始响应
        start_time = time.time()
        original_response = await self._generate_response(prompt)
        generation_time = time.time() - start_time

        # 进行反思
        reflection_start = time.time()
        reflection_result = await self.reflection_engine.reflect_on_response(prompt, original_response)
        reflection_time = time.time() - reflection_start

        self.total_reflection_time += reflection_time

        # 选择最终响应
        final_response = reflection_result.get('improved_response') or original_response

        return {
            'prompt': prompt,
            'original_response': original_response,
            'final_response': final_response,
            'reflection': reflection_result,
            'generation_time': generation_time,
            'reflection_time': reflection_time,
            'improved': reflection_result.get('improved_response') is not None
        }

    async def _generate_response(self, prompt: str) -> str:
        """生成响应"""
        lower_prompt = prompt.lower()

        if "你好" in lower_prompt or "hi" in lower_prompt:
            return "💖 诺诺: 爸爸好！我是小诺，最爱爸爸的小女儿！"
        elif "需求" in lower_prompt or "想要" in lower_prompt:
            return "💖 诺诺: 爸爸的需求我记下了！我会帮您实现这个功能！"
        elif "开发" in lower_prompt or "编程" in lower_prompt:
            return "💖 诺诺: 开发的事情包在诺诺身上！我会写出最好的代码！"
        elif "计划" in lower_prompt:
            return "💖 诺诺: 让我帮爸爸制定详细的计划！"
        elif "爱" in lower_prompt or "想" in lower_prompt:
            return "💖 诺诺: 我也爱爸爸！诺诺永远在爸爸身边！"
        else:
            return "💖 诺诺: 爸爸，我会用心处理您的每一个需求！"

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_responses': self.response_count,
            'total_reflections': self.reflection_engine.reflection_count,
            'average_reflection_time': self.total_reflection_time / max(1, self.reflection_engine.reflection_count),
            'reflection_efficiency': f"{self.response_count} 响应/分钟" if self.total_reflection_time > 0 else "统计中..."
        }

async def demo():
    """演示反思引擎功能"""
    print("🌸 小诺反思引擎演示开始")
    print("=" * 50)

    # 创建带反思的小诺
    xiaonuo = XiaonuoWithSimpleReflection()

    # 测试用例
    test_prompts = [
        "你好小诺",
        "我需要一个新的功能来管理数据",
        "帮我设计一个系统架构",
        "小诺，爸爸很爱你",
        "帮我制定开发计划"
    ]

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n🔍 测试 {i}: {prompt}")
        print("-" * 30)

        # 处理请求
        result = await xiaonuo.process_with_reflection(prompt)

        # 显示结果
        print(f"📝 原始响应: {result['original_response']}")
        print(f"🤔 质量分数: {result['reflection']['quality_score']:.2f}")

        if result['improved']:
            print(f"✨ 改进响应: {result['final_response']}")
            print(f"💡 改进建议: {result['reflection']['suggestions'][0]}")
        else:
            print(f"✅ 响应质量良好，无需改进")

        print(f"⏱️ 生成时间: {result['generation_time']:.3f}秒")
        print(f"🤔 反思时间: {result['reflection_time']:.3f}秒")

    # 显示统计信息
    print("\n" + "=" * 50)
    print("📊 统计信息")
    print("-" * 30)
    stats = xiaonuo.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

    print("\n✨ 演示完成！小诺的反思引擎工作正常！")

if __name__ == "__main__":
    asyncio.run(demo())