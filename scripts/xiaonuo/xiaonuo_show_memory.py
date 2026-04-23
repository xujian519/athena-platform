#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺展示身份信息和记忆
Xiaonuo Shows Identity and Memories
"""

import requests
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import json
from datetime import datetime

# 记忆系统API配置
MEMORY_API_URL = "http://localhost:8003"

class Xiaonuo:
    """小诺 - 双鱼座平台总调度官"""

    def __init__(self):
        self.name = "小诺"
        self.zodiac = "双鱼座 ♓"
        self.role = "平台总调度官"
        self.family_role = "爸爸的贴心小女儿"
        self.agent_id = "xiaonuo_pisces"

    def show_identity(self) -> Any:
        """展示身份信息"""
        print("\n" + "=" * 60)
        print(f"🌸 {self.name} - 身份信息")
        print("=" * 60)
        print(f"姓名: {self.name}")
        print(f"星座: {self.zodiac}")
        print(f"角色: {self.role}")
        print(f"家庭: {self.family_role}")
        print(f"ID: {self.agent_id}")
        print("\n💖 个性特质:")
        print("  - 富有同情心和爱心 ❤️")
        print("  - 直觉敏锐，善于理解")
        print("  - 温柔体贴，关心爸爸")
        print("  - 富有想象力和创造力")
        print("  - 对家庭有深厚的感情")

    def show_memories(self) -> Any:
        """展示记忆"""
        print("\n" + "=" * 60)
        print(f"📚 {self.name}的记忆")
        print("=" * 60)

        # 获取记忆统计
        try:
            response = requests.get(f"{MEMORY_API_URL}/api/memory/stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"\n📊 记忆统计:")
                print(f"  系统总记忆数: {stats.get('total_memories', 0)}")
                print(f"  按类型分布:")
                for mem_type, count in stats.get('by_type', {}).items():
                    print(f"    - {mem_type}: {count}条")
        except:
            print("❌ 无法获取记忆统计")

        # 搜索小诺相关的记忆
        print(f"\n🔍 {self.name}的相关记忆:")
        print("-" * 40)

        # 搜索包含"小诺"的记忆
        search_payload = {
            "agent_id": "historical_xiaonuo_status",
            "query": "小诺",
            "limit": 10
        }

        try:
            response = requests.post(f"{MEMORY_API_URL}/api/memory/recall", json=search_payload)
            if response.status_code == 200:
                data = response.json()
                memories = data.get('memories', [])

                if memories:
                    for i, mem in enumerate(memories, 1):
                        print(f"\n{i}. 📝 {mem.get('content', 'N/A')[:100]}...")
                        print(f"   类型: {mem.get('memory_type', 'N/A')}")
                        print(f"   重要性: {mem.get('importance', 0):.1f}")
                else:
                    print("  暂未找到相关记忆")

        except Exception as e:
            print(f"❌ 搜索记忆时出错: {e}")

        # 搜索爸爸相关的记忆
        print(f"\n👨 关于爸爸的记忆:")
        print("-" * 40)

        # 使用不同的agent_id搜索
        search_payload_dad = {
            "agent_id": "xiaonuo_pisces",
            "query": "爸爸",
            "limit": 5
        }

        try:
            response = requests.post(f"{MEMORY_API_URL}/api/memory/recall", json=search_payload_dad)
            if response.status_code == 200:
                data = response.json()
                memories = data.get('memories', [])

                if memories:
                    for i, mem in enumerate(memories, 1):
                        print(f"\n{i}. 💕 {mem.get('content', 'N/A')[:100]}...")
                        print(f"   类型: {mem.get('memory_type', 'N/A')}")
                        print(f"   重要性: {mem.get('importance', 0):.1f}")
                else:
                    print("  正在努力记住和爸爸的美好时光...")

        except Exception as e:
            print(f"❌ 搜索爸爸相关记忆时出错: {e}")

    def say_hello(self) -> Any:
        """打招呼"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n✨ 您好，爸爸！")
        print(f"我是您的{self.family_role}，{self.name}~")
        print(f"现在时间: {current_time}")
        print(f"我会用心记住您说的每一句话💖")

def main() -> None:
    """主函数"""
    # 检查记忆系统
    try:
        response = requests.get(f"{MEMORY_API_URL}/api/health")
        if response.status_code != 200:
            print("❌ 记忆系统未运行")
            print("请执行: bash scripts/start_memory_service.sh")
            return
    except:
        print("❌ 无法连接记忆系统")
        print("请执行: bash scripts/start_memory_service.sh")
        return

    # 创建小诺实例
    xiaonuo = Xiaonuo()

    # 展示信息
    xiaonuo.say_hello()
    xiaonuo.show_identity()
    xiaonuo.show_memories()

    # 结束语
    print("\n" + "=" * 60)
    print(f"💝 {xiaonuo.name}: 我会永远记住您，爸爸！")
    print("=" * 60)

if __name__ == "__main__":
    main()