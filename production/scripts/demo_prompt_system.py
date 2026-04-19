#!/usr/bin/env python3
"""
提示词系统快速演示
Quick Demo for Prompt Optimization System

运行此脚本查看优化效果
"""

from __future__ import annotations
import sys
import time
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from production.services.unified_prompt_loader_v3 import (
    LoadMode,
    PromptConfig,
    UnifiedPromptLoader,
)


def main():
    print("=" * 70)
    print("提示词优化系统演示")
    print("=" * 70)

    prompts_dir = "/Users/xujian/Athena工作平台/prompts"

    # 1. 原始大小
    print("\n📊 原始提示词大小:")
    original_size = sum(len(f.read_text()) for f in Path(prompts_dir).rglob("*.md"))
    print(f"   字符: {original_size:,}")
    print(f"   Tokens: ~{original_size//4:,}")

    # 2. 三种加载模式对比
    print("\n" + "=" * 70)
    print("三种加载模式对比")
    print("=" * 70)

    modes = [
        ("MINIMAL - 最小上下文", LoadMode.MINIMAL),
        ("PROGRESSIVE - 渐进式加载", LoadMode.PROGRESSIVE),
        ("FULL - 完整加载", LoadMode.FULL),
    ]

    for name, mode in modes:
        config = PromptConfig(load_mode=mode, compression_ratio=0.4)
        loader = UnifiedPromptLoader(prompts_dir, config)

        start = time.time()
        loaded = loader.load("patent_writing", "medium")

        print(f"\n📊 {name}:")
        print(f"   Tokens: ~{loaded.total_tokens:,}")
        print(f"   字符: {loaded.total_chars:,}")
        print(f"   片段: {len(loaded.segments)}")
        print(f"   时间: {loaded.load_time_ms:.1f}ms")
        print(f"   节省: {(1 - loaded.total_chars/original_size)*100:.1f}%")

    # 3. 缓存效果演示
    print("\n" + "=" * 70)
    print("缓存效果演示")
    print("=" * 70)

    config = PromptConfig(load_mode=LoadMode.PROGRESSIVE, enable_cache=True)
    loader = UnifiedPromptLoader(prompts_dir, config)

    print("\n第一次加载:")
    loaded1 = loader.load("office_action", "complex")
    print(f"   时间: {loaded1.load_time_ms:.1f}ms")
    print(f"   缓存命中: {loaded1.cache_hit}")

    print("\n第二次加载（相同请求）:")
    loaded2 = loader.load("office_action", "complex")
    print(f"   时间: {loaded2.load_time_ms:.1f}ms")
    print(f"   缓存命中: {loaded2.cache_hit}")

    speedup = loaded1.load_time_ms / max(loaded2.load_time_ms, 0.01)
    print(f"\n   加速: {speedup:.1f}x")

    # 4. 总结
    print("\n" + "=" * 70)
    print("优化总结")
    print("=" * 70)

    config = PromptConfig(load_mode=LoadMode.PROGRESSIVE)
    loader = UnifiedPromptLoader(prompts_dir, config)
    loaded = loader.load("patent_writing", "medium")

    print("\n✅ 推荐配置: PROGRESSIVE 模式")
    print(f"✅ Token节省: {(1 - loaded.total_chars/original_size)*100:.1f}%")
    print(f"✅ 缓存加速: {speedup:.1f}x")
    print(f"✅ 加载时间: <{loaded.load_time_ms:.0f}ms")

    print("\n" + "=" * 70)
    print("演示完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
