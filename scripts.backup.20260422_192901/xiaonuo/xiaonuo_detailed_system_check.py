#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺·双鱼公主系统深度检查器
Xiaonuo Pisces Princess Deep System Checker
"""

import sys
import os
sys.path.append(os.path.expanduser("~/Athena工作平台"))

import asyncio
from core.agent.xiaonuo_integrated_enhanced import XiaonuoIntegratedEnhanced

async def deep_system_check():
    """深度检查小诺系统"""
    print("🔍 小诺·双鱼公主系统深度检查")
    print("=" * 50)

    # 创建公主实例
    princess = XiaonuoIntegratedEnhanced()
    await princess.initialize()

    print("\n🧠 检查认知引擎详情...")

    # 检查所有属性
    print("\n📋 公主实例属性列表:")
    all_attrs = dir(princess)

    # 过滤出引擎相关属性
    engine_attrs = [attr for attr in all_attrs if 'engine' in attr.lower()]
    print(f"\n⚙️ 引擎相关属性 ({len(engine_attrs)}个):")
    for attr in sorted(engine_attrs):
        has_value = hasattr(princess, attr)
        value = getattr(princess, attr, None)
        value_type = type(value).__name__ if value else "None"
        print(f"  • {attr}: {value_type}")

    # 检查认知相关属性
    cognition_attrs = [attr for attr in all_attrs if 'cognit' in attr.lower()]
    print(f"\n🧠 认知相关属性 ({len(cognition_attrs)}个):")
    for attr in sorted(cognition_attrs):
        has_value = hasattr(princess, attr)
        value = getattr(princess, attr, None)
        value_type = type(value).__name__ if value else "None"
        print(f"  • {attr}: {value_type}")

    # 检查父类
    print(f"\n🏛️ 类继承链:")
    cls = princess.__class__
    inheritance_chain = []
    while cls:
        inheritance_chain.append(cls.__name__)
        cls = cls.__bases__[0] if cls.__bases__ else None

    for i, class_name in enumerate(inheritance_chain):
        indent = "  " * i
        print(f"{indent}└─ {class_name}")

    # 检查实际可用的引擎
    print(f"\n✅ 实际可用的引擎:")
    engine_status = {}

    engines_to_check = [
        ('perception_engine', '感知引擎'),
        ('cognition_engine', '认知引擎'),
        ('execution_engine', '执行引擎'),
        ('learning_engine', '学习引擎'),
        ('communication_engine', '通讯引擎'),
        ('evaluation_engine', '评估引擎')
    ]

    for attr_name, display_name in engines_to_check:
        if hasattr(princess, attr_name):
            engine = getattr(princess, attr_name)
            engine_status[display_name] = {
                'exists': True,
                'type': type(engine).__name__,
                'id': id(engine)
            }
            print(f"  ✅ {display_name}: {type(engine).__name__}")
        else:
            engine_status[display_name] = {'exists': False}
            print(f"  ❌ {display_name}: 不存在")

    # 检查是否有间接的认知功能
    print(f"\n🔍 检查间接认知功能:")

    # 检查NLP相关
    if hasattr(princess, 'nlp_adapter'):
        print(f"  ✅ NLP适配器: {type(princess.nlp_adapter).__name__}")
    else:
        print(f"  ❌ NLP适配器: 不存在")

    # 检查是否有认知处理方法
    cognitive_methods = ['cognize', 'reason', 'think', 'understand', 'analyze']
    found_methods = []
    for method in cognitive_methods:
        if hasattr(princess, method) and callable(getattr(princess, method)):
            found_methods.append(method)

    if found_methods:
        print(f"  ✅ 认知方法: {', '.join(found_methods)}")
    else:
        print(f"  ❌ 认知方法: 未找到")

    # 尝试功能测试
    print(f"\n🧪 功能测试:")
    try:
        # 测试基础处理能力
        result = await princess.process_input("你好，小诺", "text")
        print(f"  ✅ 基础处理: 成功")
    except Exception as e:
        print(f"  ❌ 基础处理: {e}")

    # 总结
    print(f"\n📊 系统状态总结:")
    operational_count = sum(1 for status in engine_status.values() if status['exists'])
    total_count = len(engine_status)
    print(f"  • 引擎可用率: {operational_count}/{total_count} ({operational_count/total_count*100:.1f}%)")

    if operational_count == total_count:
        print("  🎉 所有引擎完整，系统功能齐全")
    elif operational_count >= total_count * 0.8:
        print("  ✨ 大部分引擎可用，系统基本完整")
    else:
        print("  ⚠️ 部分引擎缺失，需要修复")

    return {
        'engine_status': engine_status,
        'inheritance_chain': inheritance_chain,
        'operational_count': operational_count,
        'total_count': total_count
    }

if __name__ == "__main__":
    asyncio.run(deep_system_check())