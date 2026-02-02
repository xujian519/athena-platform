#!/usr/bin/env python3
"""
LLM缓存管理脚本
LLM Cache Management Script for Athena Platform

管理LLM缓存的查看、清理、导出等操作

作者: 小诺·双鱼座
创建时间: 2025-12-16
"""

import sys
import argparse
import json
import asyncio
from pathlib import Path
from datetime import datetime

# 添加路径
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "core" / "orchestration"))

from llm_cache_manager import LLMCacheManager, CacheConfig, CacheStrategy

class CacheManagementTool:
    """缓存管理工具"""

    def __init__(self):
        self.cache_manager = None
        self._init_cache()

    def _init_cache(self):
        """初始化缓存管理器"""
        config = CacheConfig(
            enabled=True,
            strategy=CacheStrategy.ADAPTIVE,
            max_size=10000,
            ttl=7200,
            redis_host="localhost",
            redis_port=6379,
            redis_db=0
        )
        self.cache_manager = LLMCacheManager(config)

    async def show_stats(self):
        """显示缓存统计"""
        print("📊 LLM缓存统计信息")
        print("=" * 50)

        # 获取缓存管理器统计
        cache_stats = self.cache_manager.get_cache_statistics()
        print(f"缓存状态: {'✅ 启用' if cache_stats['enabled'] else '❌ 禁用'}")
        print(f"缓存策略: {cache_stats['strategy']}")
        print(f"总请求数: {cache_stats['total_requests']}")
        print(f"缓存命中: {cache_stats['cache_hits']}")
        print(f"缓存未命中: {cache_stats['cache_misses']}")
        print(f"命中率: {cache_stats['hit_rate']}")
        print(f"语义匹配: {cache_stats['semantic_matches']}")
        print(f"缓存大小: {cache_stats['cache_size']}")
        print(f"内存使用: {cache_stats['memory_usage_mb']}")

        # 如果有路由器统计
        try:
            from xiaonuo_model_router import XiaonuoModelRouter
            router = XiaonuoModelRouter()
            router_stats = router.get_usage_statistics()
            print("\n🎯 模型路由器统计")
            print("-" * 30)
            print(f"GLM-4使用次数: {router_stats['glm4_usage']}")
            print(f"GLM-4使用率: {router_stats['glm4_ratio']:.2%}")
            print(f"总请求数: {router_stats['total_requests']}")
            if 'avg_response_time' in router_stats:
                print(f"平均响应时间: {router_stats['avg_response_time']:.3f}秒")
        except Exception as e:
            print(f"\n⚠️ 无法获取路由器统计: {e}")

    async def clear_cache(self, pattern=None, all=False):
        """清理缓存"""
        print("🧹 清理LLM缓存")
        print("=" * 30)

        if all:
            confirm = input("⚠️ 确定要清理所有缓存吗？(y/N): ")
            if confirm.lower() != 'y':
                print("操作已取消")
                return

        self.cache_manager.clear_cache(pattern)
        action = "全部" if all else f"模式: {pattern}" if pattern else "过期"
        print(f"✅ 已清理缓存: {action}")

    async def export_cache(self, filepath):
        """导出缓存"""
        print(f"📤 导出缓存到: {filepath}")
        try:
            self.cache_manager.export_cache(filepath)
            print("✅ 导出成功")
        except Exception as e:
            print(f"❌ 导出失败: {e}")

    async def import_cache(self, filepath):
        """导入缓存"""
        print(f"📥 从文件导入缓存: {filepath}")
        if not Path(filepath).exists():
            print(f"❌ 文件不存在: {filepath}")
            return

        try:
            self.cache_manager.import_cache(filepath)
            print("✅ 导入成功")
        except Exception as e:
            print(f"❌ 导入失败: {e}")

    async def analyze_cache(self):
        """分析缓存内容"""
        print("🔍 缓存内容分析")
        print("=" * 50)

        # 按任务类型分析
        task_types = {}
        models = {}

        with self.cache_manager.cache_lock:
            for entry in self.cache_manager.memory_cache.values():
                # 任务类型统计
                task_type = entry.task_type
                if task_type not in task_types:
                    task_types[task_type] = {"count": 0, "total_hits": 0}
                task_types[task_type]["count"] += 1
                task_types[task_type]["total_hits"] += entry.hit_count

                # 模型统计
                model = entry.model_name
                if model not in models:
                    models[model] = {"count": 0, "total_hits": 0}
                models[model]["count"] += 1
                models[model]["total_hits"] += entry.hit_count

        print("\n📋 按任务类型:")
        for task_type, stats in sorted(task_types.items(), key=lambda x: x[1]["count"], reverse=True):
            avg_hits = stats["total_hits"] / stats["count"] if stats["count"] > 0 else 0
            print(f"  {task_type}: {stats['count']} 条, 平均命中 {avg_hits:.1f} 次")

        print("\n🤖 按模型:")
        for model, stats in sorted(models.items(), key=lambda x: x[1]["count"], reverse=True):
            avg_hits = stats["total_hits"] / stats["count"] if stats["count"] > 0 else 0
            print(f"  {model}: {stats['count']} 条, 平均命中 {avg_hits:.1f} 次")

    async def optimize_cache(self):
        """优化缓存设置"""
        print("⚙️ 缓存优化建议")
        print("=" * 50)

        stats = self.cache_manager.get_cache_statistics()
        hit_rate = float(stats["hit_rate"].rstrip("%"))

        suggestions = []

        # 命中率分析
        if hit_rate < 30:
            suggestions.append("💡 缓存命中率较低，建议：")
            suggestions.append("   - 增加缓存大小(max_size)")
            suggestions.append("   - 延长缓存时间(ttl)")
            suggestions.append("   - 使用语义相似匹配")
        elif hit_rate > 80:
            suggestions.append("✨ 缓存命中率高，配置良好！")
            suggestions.append("   - 可以考虑降低ttl以保持内容新鲜")

        # 内存使用分析
        memory_mb = float(stats["memory_usage_mb"])
        if memory_mb > 500:
            suggestions.append("⚠️ 内存使用较高，建议：")
            suggestions.append("   - 启用Redis分布式缓存")
            suggestions.append("   - 定期清理过期缓存")
            suggestions.append("   - 减小max_size限制")

        # 缓存大小分析
        if stats["cache_size"] == 0:
            suggestions.append("📝 缓存为空，建议：")
            suggestions.append("   - 检查是否启用了缓存")
            suggestions.append("   - 确保有实际的LLM调用")

        # 输出建议
        if suggestions:
            for s in suggestions:
                print(s)
        else:
            print("✅ 当前配置合理，无需优化")

    async def benchmark(self):
        """运行性能基准测试"""
        print("🏃 缓存性能基准测试")
        print("=" * 50)

        from xiaonuo_model_router import XiaonuoModelRouter
        router = XiaonuoModelRouter()

        # 测试问题
        test_prompts = [
            ("专利的价值是什么？", "patent_analysis"),
            ("如何保护知识产权？", "legal_analysis"),
            ("Python如何实现快速排序？", "code_generation"),
            ("写一首关于春天的诗", "creative_writing"),
            ("分析一下市场趋势", "data_analysis")
        ] * 5  # 每个问题重复5次

        print(f"\n测试 {len(test_prompts)} 个请求...")

        # 第一次运行（无缓存）
        print("\n📊 第一次运行（建立缓存）:")
        start_time = asyncio.get_event_loop().time()
        for prompt, task_type in test_prompts:
            await router.call_llm_with_cache(
                prompt=prompt,
                model_name="glm-4",
                task_type=task_type,
                use_cache=False
            )
        first_time = asyncio.get_event_loop().time() - start_time
        print(f"   耗时: {first_time:.2f}秒")

        # 第二次运行（有缓存）
        print("\n📊 第二次运行（使用缓存）:")
        start_time = asyncio.get_event_loop().time()
        for prompt, task_type in test_prompts:
            await router.call_llm_with_cache(
                prompt=prompt,
                model_name="glm-4",
                task_type=task_type,
                use_cache=True
            )
        second_time = asyncio.get_event_loop().time() - start_time
        print(f"   耗时: {second_time:.2f}秒")

        # 性能提升
        if first_time > 0:
            improvement = ((first_time - second_time) / first_time) * 100
            print(f"\n✨ 性能提升: {improvement:.1f}%")

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="LLM缓存管理工具")
    parser.add_argument("command", choices=[
        "stats", "clear", "export", "import", "analyze", "optimize", "benchmark"
    ], help="要执行的命令")
    parser.add_argument("--pattern", "-p", help="清理缓存的模式")
    parser.add_argument("--all", "-a", action="store_true", help="清理所有缓存")
    parser.add_argument("--file", "-f", help="导入/导出的文件路径")

    args = parser.parse_args()

    tool = CacheManagementTool()

    if args.command == "stats":
        await tool.show_stats()
    elif args.command == "clear":
        if args.all:
            await tool.clear_cache(all=True)
        else:
            await tool.clear_cache(pattern=args.pattern)
    elif args.command == "export":
        if not args.file:
            print("❌ 请指定导出文件路径 (--file)")
            return
        await tool.export_cache(args.file)
    elif args.command == "import":
        if not args.file:
            print("❌ 请指定导入文件路径 (--file)")
            return
        await tool.import_cache(args.file)
    elif args.command == "analyze":
        await tool.analyze_cache()
    elif args.command == "optimize":
        await tool.optimize_cache()
    elif args.command == "benchmark":
        await tool.benchmark()

if __name__ == "__main__":
    asyncio.run(main())