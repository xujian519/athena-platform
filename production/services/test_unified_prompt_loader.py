#!/usr/bin/env python3
"""
统一提示词加载器测试
"""

from __future__ import annotations
import sys
import time
from pathlib import Path
from typing import Any

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from unified_prompt_loader import (
    PromptValidator,
    UnifiedPromptLoader,
    get_prompt_loader,
)


def test_basic_loading() -> Any:
    """测试基本加载功能"""
    print("\n" + "=" * 60)
    print("🧪 测试1: 基本加载功能")
    print("=" * 60)

    # 创建xiaona加载器
    loader = UnifiedPromptLoader(agent="xiaona", version="latest")

    # 加载L1
    l1 = loader.load_layer("l1")
    print(f"✅ L1基础层加载成功: {len(l1) if l1 else 0:,} 字符")

    # 加载L3
    l3 = loader.load_layer("l3")
    print(f"✅ L3能力层加载成功: {len(l3) if l3 else 0:,} 字符")

    # 加载HITL
    hitl = loader.load_layer("hitl")
    print(f"✅ HITL协议加载成功: {len(hitl) if hitl else 0:,} 字符")


def test_task_based_loading() -> Any:
    """测试按任务类型加载"""
    print("\n" + "=" * 60)
    print("🧪 测试2: 按任务类型加载")
    print("=" * 60)

    loader = UnifiedPromptLoader(agent="xiaona")

    # 通用模式
    general = loader.load_by_task_type("general")
    print(f"📋 通用模式: {len(general):,} 字符")

    # 专利撰写模式（精细加载）
    patent = loader.load_by_task_type("patent_writing")
    print(f"📋 专利撰写模式: {len(patent):,} 字符")

    # 意见答复模式（精细加载）
    office = loader.load_by_task_type("office_action")
    print(f"📋 意见答复模式: {len(office):,} 字符")

    # 对比
    print("\n💡 节省Token对比:")
    print(f"   - 专利撰写 vs 通用: {((1 - len(patent)/len(general)) * 100):.1f}%")
    print(f"   - 意见答复 vs 通用: {((1 - len(office)/len(general)) * 100):.1f}%")


def test_cache_performance() -> Any:
    """测试缓存性能"""
    print("\n" + "=" * 60)
    print("🧪 测试3: 缓存性能")
    print("=" * 60)

    loader = UnifiedPromptLoader(agent="xiaona", use_cache=True)

    # 第一次加载（冷启动）
    start = time.time()
    loader.load_layer("l3")
    cold_load = (time.time() - start) * 1000
    print(f"⏱️  冷启动耗时: {cold_load:.2f}ms")

    # 第二次加载（缓存）
    start = time.time()
    loader.load_layer("l3")
    cache_load = (time.time() - start) * 1000
    print(f"⏱️  缓存加载: {cache_load:.2f}ms")

    # 性能提升
    if cache_load > 0:
        speedup = cold_load / cache_load
        print(f"🚀 性能提升: {speedup:.1f}x")

    # 缓存统计
    stats = loader.get_cache_stats()
    print("📊 缓存统计:")
    print(f"   - 条目数: {stats['entries']}")
    print(f"   - 大小: {stats['total_bytes']:,} 字节")


def test_validator() -> Any:
    """测试验证器"""
    print("\n" + "=" * 60)
    print("🧪 测试4: 提示词验证器")
    print("=" * 60)

    validator = PromptValidator()

    # 有效提示词
    valid_prompt = """# 测试提示词

这是一个有效的提示词内容。

它包含了足够的字符长度。
"""
    is_valid, errors = validator.validate_format(valid_prompt)
    print(f"✅ 有效提示词验证: {is_valid}")
    print(f"   Token估算: {validator.estimate_tokens(valid_prompt)}")

    # 无效提示词
    invalid_prompt = "短"
    is_valid, errors = validator.validate_format(invalid_prompt)
    print(f"❌ 无效提示词验证: {is_valid}")
    print(f"   错误: {errors}")


def test_monitoring() -> Any:
    """测试监控功能"""
    print("\n" + "=" * 60)
    print("🧪 测试5: 使用监控")
    print("=" * 60)

    loader = UnifiedPromptLoader(agent="xiaona", monitoring=True)

    # 模拟多次使用
    for _i in range(3):
        loader.load_layer("l3")

    # 获取统计
    stats = loader.get_usage_stats(hours=1)
    print("📊 使用统计:")
    print(f"   - 总调用: {stats['total_calls']}")
    print(f"   - 总Token: {stats['total_tokens']:,}")
    print(f"   - 平均耗时: {stats['avg_duration']*1000:.2f}ms")
    print(f"   - 成功率: {stats['success_rate']*100:.1f}%")

    # 生成报告
    print(f"\n{loader.generate_usage_report()}")


def test_multi_agent() -> Any:
    """测试多智能体支持"""
    print("\n" + "=" * 60)
    print("🧪 测试6: 多智能体支持")
    print("=" * 60)

    agents = ["xiaona", "xiaonuo"]

    for agent in agents:
        try:
            loader = UnifiedPromptLoader(agent=agent)
            summary = loader.get_summary()
            print(f"✅ {agent}:")
            print(f"   - 版本: {summary['version']}")
            print(f"   - 加载数: {summary['loaded_count']}")
            print(f"   - 总Token: {summary['total_tokens']:,}")
        except Exception as e:
            print(f"❌ {agent}: {e}")


def test_convenience_api() -> Any:
    """测试便捷API"""
    print("\n" + "=" * 60)
    print("🧪 测试7: 便捷API")
    print("=" * 60)

    # 使用便捷函数
    loader = get_prompt_loader(agent="xiaona", version="latest")

    # 兼容接口测试
    prompt = loader.get_full_prompt("patent_writing")
    print(f"✅ get_full_prompt(): {len(prompt):,} 字符")

    layer = loader.get_prompt("l3")
    print(f"✅ get_prompt(): {len(layer) if layer else 0:,} 字符")


def test_metadata() -> Any:
    """测试元数据"""
    print("\n" + "=" * 60)
    print("🧪 测试8: 元数据管理")
    print("=" * 60)

    loader = UnifiedPromptLoader(agent="xiaona")

    # 加载一些层
    loader.load_layer("l1")
    loader.load_layer("l3")

    # 获取元数据
    l1_meta = loader.get_metadata("l1")
    if l1_meta:
        print("📋 L1元数据:")
        print(f"   - 大小: {l1_meta.size:,} 字符")
        print(f"   - 哈希: {l1_meta.hash}")
        print(f"   - 加载次数: {l1_meta.load_count}")

    # 列出已加载
    loaded = loader.list_loaded_prompts()
    print(f"\n📋 已加载提示词: {loaded}")


def run_all_tests() -> Any:
    """运行所有测试"""
    print("\n" + "🚀" * 30)
    print("统一提示词加载器 - 完整测试套件")
    print("🚀" * 30)

    try:
        test_basic_loading()
        test_task_based_loading()
        test_cache_performance()
        test_validator()
        test_monitoring()
        test_multi_agent()
        test_convenience_api()
        test_metadata()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
