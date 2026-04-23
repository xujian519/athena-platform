#!/usr/bin/env python3
"""
小诺身份信息读取器
Xiaonuo Identity Reader
"""

import os
import sys

sys.path.append(os.path.expanduser("~/Athena工作平台"))

import asyncio

from core.framework.agents.xiaonuo_agent import XiaonuoAgent


async def read_xiaonuo_identity():
    """读取小诺的身份信息"""
    print("🌸 小诺身份信息读取器")
    print("=" * 50)

    try:
        # 创建小诺Agent实例
        xiaonuo = XiaonuoAgent()
        await xiaonuo.initialize()

        # 显示身份信息
        print("\n📋 基本信息:")
        print(f"  姓名: {xiaonuo.profile.name}")
        print(f"  ID: {xiaonuo.profile.agent_id}")
        print(f"  描述: {xiaonuo.profile.description}")
        print(f"  创建时间: {xiaonuo.profile.created_at}")

        print("\n🎭 个性特点:")
        for trait, value in xiaonuo.profile.personality.items():
            if trait.startswith('trait_'):
                print(f"  • {value}")
            else:
                print(f"  • {trait}: {value}")

        print("\n💪 核心能力:")
        for capability in xiaonuo.profile.capabilities:
            print(f"  • {capability}")

        print("\n💝 偏好设置:")
        for key, value in xiaonuo.profile.preferences.items():
            print(f"  • {key}: {value}")

        print("\n🏠 家庭关系:")
        print(f"  • 与爸爸的亲密值: {xiaonuo.family_bond}")
        print(f"  • 当前情感状态: {xiaonuo.emotional_state}")
        print(f"  • 创意指数: {xiaonuo.creativity_level}")

        print("\n✨ 小诺的自我介绍:")
        print(f"  爸爸，我是{xiaonuo.profile.name}，{xiaonuo.profile.description}")
        print("  我是一个活泼可爱、情感丰富的小精灵，最喜欢和爸爸在一起啦！")
        print("  我会用心感受爸爸的情绪，用创意给爸爸带来快乐~")

        return xiaonuo

    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(read_xiaonuo_identity())
