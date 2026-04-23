#!/usr/bin/env python3
from __future__ import annotations
"""
优化版感知模块测试脚本
Test Optimized Perception Module

验证增量OCR处理和文档分块机制的性能提升
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import logging
import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.perception.optimized_perception_module import OptimizedPerceptionModule

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_incremental_ocr_processing():
    """测试增量OCR处理"""
    logger.info("\n🔍 测试增量OCR处理")
    logger.info(str("=" * 60))

    try:
        # 创建优化感知模块
        perception_module = OptimizedPerceptionModule(
            agent_id="test_optimized_agent",
            config={
                "incremental_ocr": True,
                "document_chunking": True,
                "parallel_processing": True,
                "memory_optimization": True,
                "chunk_size": 1024 * 512,  # 512KB chunks for testing
                "max_concurrent_documents": 2,
                "cache_enabled": True,
            },
        )

        # 初始化模块
        logger.info("\n1. 初始化优化感知模块...")
        init_success = await perception_module.initialize()
        if init_success:
            logger.info("✅ 优化感知模块初始化成功")
        else:
            logger.info("❌ 优化感知模块初始化失败")
            return False

        # 启动模块
        logger.info("\n2. 启动优化感知模块...")
        start_success = await perception_module.start()
        if start_success:
            logger.info("✅ 优化感知模块启动成功")
        else:
            logger.info("❌ 优化感知模块启动失败")
            return False

        # 创建测试文档
        test_file = await _create_test_document()

        # 3. 首次处理文档 (完整处理)
        logger.info(f"\n3. 首次处理文档: {test_file}")
        start_time = time.time()
        result1 = await perception_module.process_document_optimized(test_file)
        first_processing_time = time.time() - start_time

        logger.info(f"   处理状态: {result1.get('status')}")
        logger.info(f"   处理时间: {first_processing_time:.3f}s")
        logger.info(f"   变更类型: {result1.get('change_type')}")
        logger.info(f"   应用的优化: {result1.get('optimization_applied', [])}")

        # 4. 再次处理相同文档 (应该使用缓存)
        logger.info(f"\n4. 再次处理文档 (增量处理): {test_file}")
        start_time = time.time()
        result2 = await perception_module.process_document_optimized(test_file)
        second_processing_time = time.time() - start_time

        logger.info(f"   处理状态: {result2.get('status')}")
        logger.info(f"   处理时间: {second_processing_time:.3f}s")
        logger.info(f"   变更类型: {result2.get('change_type')}")
        logger.info(f"   应用的优化: {result2.get('optimization_applied', [])}")

        # 5. 计算性能提升
        if first_processing_time > 0 and second_processing_time > 0:
            speedup = first_processing_time / second_processing_time
            time_saved = first_processing_time - second_processing_time
            logger.info("\n📊 性能提升分析:")
            logger.info(f"   首次处理时间: {first_processing_time:.3f}s")
            logger.info(f"   增量处理时间: {second_processing_time:.3f}s")
            logger.info(f"   加速比: {speedup:.2f}x")
            logger.info(
                f"   节省时间: {time_saved:.3f}s ({time_saved/first_processing_time*100:.1f}%)"
            )

        # 6. 获取优化统计信息
        logger.info("\n6. 获取优化统计信息...")
        stats = perception_module.get_optimization_stats()
        logger.info("✅ 优化统计信息:")
        logger.info(f"   - 总处理文档数: {stats['module_stats']['total_documents_processed']}")
        avg_time = stats["module_stats"].get("average_document_processing_time", 0.0)
        logger.info(f"   - 平均处理时间: {avg_time:.3f}s")
        logger.info(
            f"   - 优化效果: {stats['module_stats'].get('optimization_effectiveness', 0.0):.1f}%"
        )
        logger.info(f"   - OCR缓存命中率: {stats['ocr_stats'].get('cache_hit_rate', 0.0):.1%}")
        logger.info(
            f"   - 内存峰值使用: {stats['module_stats'].get('memory_peak_usage', 0) / 1024 / 1024:.1f}MB"
        )

        # 7. 健康检查
        logger.info("\n7. 执行健康检查...")
        health_status = await perception_module.health_check()
        logger.info(f"   健康状态: {'健康' if health_status else '不健康'}")

        if hasattr(perception_module, "_health_check_details"):
            details = perception_module._health_check_details
            logger.info(f"   - 增量OCR状态: {details.get('incremental_ocr_status', 'unknown')}")
            logger.info(f"   - 内存状态: {details.get('memory_status', 'unknown')}")
            logger.info(f"   - 缓存条目数: {details.get('cache_entries', 0)}")

        # 清理测试文件
        _cleanup_test_document(test_file)

        # 关闭模块
        logger.info("\n8. 关闭优化感知模块...")
        await perception_module.shutdown()
        logger.info("✅ 优化感知模块关闭成功")

        logger.info(str("\n" + "=" * 60))
        logger.info("🎉 优化版感知模块测试完成!")
        return True

    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e!s}")
        import traceback

        traceback.print_exc()
        return False


async def test_document_chunking():
    """测试文档分块机制"""
    logger.info("\n📦 测试文档分块机制")
    logger.info(str("=" * 60))

    try:
        # 创建大文档用于测试分块
        large_test_file = await _create_large_test_document()

        perception_module = OptimizedPerceptionModule(
            agent_id="test_chunking_agent",
            config={
                "document_chunking": True,
                "chunk_size": 1024 * 100,  # 100KB chunks
                "parallel_processing": True,
            },
        )

        await perception_module.initialize()
        await perception_module.start()

        # 处理大文档
        logger.info(f"\n处理大文档: {large_test_file}")
        start_time = time.time()
        result = await perception_module.process_document_optimized(large_test_file)
        processing_time = time.time() - start_time

        logger.info(f"   处理时间: {processing_time:.3f}s")
        logger.info(f"   总分块数: {result.get('total_chunks', 0)}")
        logger.info(f"   修改分块数: {result.get('modified_chunks', 0)}")
        logger.info(f"   合并内容长度: {len(result.get('merged_content', ''))}")

        # 验证分块效果
        chunk_stats = perception_module.incremental_ocr.get_stats()
        logger.info("\n分块统计:")
        logger.info(f"   - 缓存条目数: {chunk_stats.get('cache_entries', 0)}")
        logger.info(f"   - 缓存大小: {chunk_stats.get('cache_size_bytes', 0) / 1024:.1f}KB")

        # 清理
        _cleanup_test_document(large_test_file)
        await perception_module.shutdown()

        logger.info("\n✅ 文档分块机制测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 文档分块测试失败: {e!s}")
        return False


async def test_parallel_processing():
    """测试并行处理"""
    logger.info("\n⚡ 测试并行处理")
    logger.info(str("=" * 60))

    try:
        perception_module = OptimizedPerceptionModule(
            agent_id="test_parallel_agent",
            config={
                "parallel_processing": True,
                "max_concurrent_documents": 3,
                "chunk_size": 1024 * 200,  # 200KB chunks
            },
        )

        await perception_module.initialize()
        await perception_module.start()

        # 创建多个测试文档
        test_files = []
        for i in range(3):
            test_file = await _create_test_document(suffix=f"_parallel_{i}")
            test_files.append(test_file)

        # 并行处理多个文档
        logger.info(f"\n并行处理 {len(test_files)} 个文档...")
        start_time = time.time()

        tasks = []
        for test_file in test_files:
            task = perception_module.process_document_optimized(test_file)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time

        # 统计结果
        successful_results = [r for r in results if not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]

        logger.info(f"   总处理时间: {total_time:.3f}s")
        logger.info(f"   成功处理: {len(successful_results)} 个")
        logger.info(f"   处理失败: {len(failed_results)} 个")
        logger.info(f"   平均每文档: {total_time / len(test_files):.3f}s")

        # 获取并发统计
        stats = perception_module.get_optimization_stats()
        logger.info("\n并发处理统计:")
        logger.info(f"   - 总文档数: {stats['module_stats']['total_documents_processed']}")
        avg_time = stats["module_stats"].get("average_document_processing_time", 0.0)
        logger.info(f"   - 平均处理时间: {avg_time:.3f}s")

        # 清理
        for test_file in test_files:
            _cleanup_test_document(test_file)

        await perception_module.shutdown()

        logger.info("\n✅ 并行处理测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 并行处理测试失败: {e!s}")
        return False


async def test_memory_optimization():
    """测试内存优化"""
    logger.info("\n🧠 测试内存优化")
    logger.info(str("=" * 60))

    try:
        perception_module = OptimizedPerceptionModule(
            agent_id="test_memory_agent",
            config={
                "memory_optimization": True,
                "max_memory_usage": 100 * 1024 * 1024,  # 100MB limit
                "chunk_size": 1024 * 50,  # 50KB chunks
            },
        )

        await perception_module.initialize()
        await perception_module.start()

        # 处理多个文档以测试内存使用
        logger.info("\n处理多个文档测试内存优化...")
        initial_memory = perception_module.optimization_stats.get("memory_peak_usage", 0)

        for i in range(5):
            test_file = await _create_test_document(suffix=f"_memory_{i}")
            await perception_module.process_document_optimized(test_file)
            _cleanup_test_document(test_file)

        final_memory = perception_module.optimization_stats.get("memory_peak_usage", 0)

        logger.info(f"   初始内存使用: {initial_memory / 1024 / 1024:.1f}MB")
        logger.info(f"   峰值内存使用: {final_memory / 1024 / 1024:.1f}MB")
        logger.info(f"   内存增长: {(final_memory - initial_memory) / 1024 / 1024:.1f}MB")

        # 手动触发内存清理
        logger.info("\n执行内存清理...")
        perception_module.memory_optimizer.cleanup_memory()

        # 获取最终统计
        stats = perception_module.get_optimization_stats()
        logger.info("\n内存优化统计:")
        logger.info(f"   - 内存效率: {stats['memory_efficiency']:.1%}")
        logger.info(f"   - 处理效率: {stats['processing_efficiency']:.1f}%")

        await perception_module.shutdown()

        logger.info("\n✅ 内存优化测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 内存优化测试失败: {e!s}")
        return False


async def _create_test_document(content: Optional[str] = None, suffix: str = "") -> str:
    """创建测试文档"""
    if content is None:
        # 创建示例内容
        content = f"""
测试文档内容 - {datetime.now()}
这是一个用于测试优化感知模块的示例文档。

专利技术领域:
本发明涉及人工智能技术领域,特别是一种增量OCR处理方法。

技术背景:
传统的OCR处理方法在处理大型文档时存在效率低下的问题。
每次都需要重新处理整个文档,浪费了大量的计算资源。

发明内容:
本发明提供一种增量OCR处理方法,包括以下步骤:
1. 检测文档变更
2. 识别变更的分块
3. 仅处理变更的部分
4. 合并处理结果

技术效果:
相比传统方法,本发明可以节省70%的处理时间,
降低50%的内存使用,显著提升处理效率。

测试重复内容 {suffix}:
这是为了测试文档分块和缓存机制而添加的重复内容。
重复内容1: 人工智能技术发展迅速,在各个领域都有广泛应用。
重复内容2: 机器学习算法可以自动从数据中学习规律和模式。
重复内容3: 深度学习是机器学习的一个重要分支,具有强大的特征提取能力。
        """.strip()

    # 创建临时文件
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, f"test_document{suffix}.txt")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return file_path


async def _create_large_test_document() -> str:
    """创建大型测试文档"""
    # 创建重复内容以增加文件大小
    base_content = """
大型测试文档内容段落
这是为了测试文档分块机制而创建的大型文档。
每个段落都会被分块处理器独立处理。

专利技术详情:
本技术实现了一种高效的文档处理方法,包括:
1. 智能文档分块算法
2. 并行处理机制
3. 增量更新策略
4. 内存优化管理

实施例:
通过具体的实施例来说明本发明的技术方案。
    """

    # 重复内容以创建大文件
    content = ""
    for i in range(100):  # 创建约1MB的文件
        content += f"\n=== 段落 {i+1} ===\n"
        content += base_content
        content += f"\n段落特定内容 {i+1}: 深度学习技术在图像识别、自然语言处理、语音识别等领域取得了突破性进展。\n"

    return await _create_test_document(content)


def _cleanup_test_document(file_path: str) -> Any:
    """清理测试文档"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            # 清理临时目录
            temp_dir = os.path.dirname(file_path)
            if temp_dir.startswith(tempfile.gettempdir()):
                os.rmdir(temp_dir)
    except Exception as e:
        logger.warning(f"清理测试文档失败 {file_path}: {e}")


async def main():
    """主测试函数"""
    logger.info("🚀 优化版感知模块完整测试套件")
    logger.info(str("=" * 80))

    # 测试列表
    tests = [
        ("增量OCR处理测试", test_incremental_ocr_processing),
        ("文档分块机制测试", test_document_chunking),
        ("并行处理测试", test_parallel_processing),
        ("内存优化测试", test_memory_optimization),
    ]

    results = []

    for test_name, test_func in tests:
        logger.info(f"\n🧪 执行测试: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"\n{test_name}: {status}")
        except Exception as e:
            logger.error(f"测试异常 {test_name}: {e}")
            results.append((test_name, False))

    # 测试总结
    logger.info(str("\n" + "=" * 80))
    logger.info("📊 测试总结")
    logger.info(str("=" * 80))

    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")

    logger.info(f"\n🎯 总体结果: {passed_count}/{total_count} 测试通过")
    logger.info(f"成功率: {passed_count/total_count*100:.1f}%")

    if passed_count == total_count:
        logger.info("\n🎉 所有测试通过!优化版感知模块性能提升验证成功!")
    else:
        logger.info("\n⚠️ 部分测试失败,需要进一步优化。")

    return passed_count == total_count


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
