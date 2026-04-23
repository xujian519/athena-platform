#!/usr/bin/env python3
"""
启动性能优化系统
集成响应缓存、模型预加载、上下文压缩等功能
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Any

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.performance.performance_optimizer import get_optimizer


def print_system_banner() -> Any:
    """打印系统启动横幅"""
    print("=" * 80)
    print("🚀 Athena工作平台 - 性能优化版")
    print("=" * 80)
    print("✅ 响应缓存 - 避免重复AI模型调用")
    print("✅ 模型预加载 - 启动时加载常用模型")
    print("✅ 上下文压缩 - 智能压缩对话历史")
    print("✅ 性能监控 - 实时性能指标追踪")
    print("=" * 80)
    print()


def print_startup_info(optimizer) -> Any:
    """打印启动信息"""
    print("📊 系统启动信息:")
    stats = optimizer.get_performance_stats()

    # 预加载状态
    preload_status = stats.get("preload", {})
    if preload_status.get("loading"):
        print("  🔄 模型预加载进行中...")
    elif preload_status.get("completed"):
        success_count = len(preload_status.get("success", []))
        failed_count = len(preload_status.get("failed", []))
        print(f"  ✅ 模型预加载完成: {success_count}成功, {failed_count}失败")
    else:
        print("  ⚠️ 模型预加载未启用")

    # 缓存状态
    cache_stats = stats.get("cache", {})
    print(f"  📦 响应缓存: {cache_stats.get('memory_cache_size', 0)}个内存缓存项")

    # 上下文压缩状态
    context_stats = stats.get("context_compression", {})
    print(f"  🗜️ 上下文压缩: {context_stats.get('total_compressions', 0)}次压缩")

    print()


def run_performance_test(optimizer) -> Any:
    """运行性能测试"""
    print("🧪 运行性能测试...")

    conversation_id = "performance_test"

    # 测试场景1: 重复请求缓存测试
    print("\\n1️⃣ 缓存性能测试:")
    prompts = [
        "什么是专利申请？",
        "发明专利和实用新型的区别是什么？",
        "申请专利需要多长时间？",
        "专利申请费用是多少？"
    ]

    cache_test_times = []
    for i, prompt in enumerate(prompts):
        start_time = time.time()

        # 第一次请求（缓存未命中）
        result1 = optimizer.optimize_request(
            conversation_id=conversation_id,
            prompt=prompt,
            operation_type=f"cache_test_{i}"
        )

        # 模拟AI响应
        mock_response = f"这是对'{prompt}'的详细回答..."
        optimizer.cache_response(conversation_id, prompt, mock_response)

        # 第二次请求（缓存命中）
        result2 = optimizer.optimize_request(
            conversation_id=conversation_id,
            prompt=prompt,
            operation_type=f"cache_test_{i}_cached"
        )

        total_time = time.time() - start_time
        cache_test_times.append(total_time)

        print(f"  {i+1}. '{prompt[:20]}...': 第一次{result1['response_time']:.3f}s, "
              f"缓存{result2['response_time']:.3f}s, 总计{total_time:.3f}s")

    avg_cache_time = sum(cache_test_times) / len(cache_test_times)
    print(f"   平均时间: {avg_cache_time:.3f}s")

    # 测试场景2: 上下文压缩测试
    print("\\n2️⃣ 上下文压缩测试:")

    # 模拟长对话
    long_conversation_id = "context_test"
    conversation_messages = [
        ("user", "我想申请一个专利"),
        ("assistant", "好的，请问您想申请什么类型的专利？"),
        ("user", "我想申请一个发明专利"),
        ("assistant", "发明专利保护的是新的技术方案，请告诉我您的技术创新点"),
        ("user", "我的发明是一种新型的农业机械装置"),
        ("assistant", "这个技术领域很有前景，能详细介绍一下装置的结构和功能吗？"),
        ("user", "该装置包括自动播种、智能灌溉和病虫害检测功能"),
        ("assistant", "这听起来是一个综合性的农业技术创新，很有专利申请价值"),
        ("user", "请问申请这个专利需要准备哪些材料？"),
        ("assistant", "需要准备申请书、说明书、权利要求书、附图等材料"),
        ("user", "申请流程大概需要多长时间？"),
        ("assistant", "发明专利申请通常需要2-3年，实用新型需要6-12个月"),
    ]

    context_test_times = []
    for i, (role, content) in enumerate(conversation_messages):
        start_time = time.time()

        # 添加消息并测试压缩
        optimizer.context_manager.add_message(long_conversation_id, role, content)
        compressed_context = optimizer.context_manager.get_compressed_context(long_conversation_id)

        test_time = time.time() - start_time
        context_test_times.append(test_time)

        print(f"  消息{i+1} ({role}): 原始{len(content)}字符, 压缩后{len(compressed_context)}条, "
              f"用时{test_time:.3f}s")

    # 测试场景3: 综合性能测试
    print("\\n3️⃣ 综合性能测试:")

    complex_conversation_id = "complex_test"
    complex_prompts = [
        "紧急！我需要为一个AI算法申请专利，需要多少费用？",
        "我的技术涉及机器学习和数据处理，应该如何分类？",
        "请帮我分析这个技术方案的专利可申请性",
        "我想了解专利申请的商业价值和市场前景"
    ]

    for i, prompt in enumerate(complex_prompts):
        start_time = time.time()

        result = optimizer.optimize_request(
            conversation_id=complex_conversation_id,
            prompt=prompt,
            context={"priority": "high", "user_type": "enterprise"},
            operation_type="complex_test"
        )

        test_time = time.time() - start_time
        optimizations = result.get("optimization_applied", [])

        print(f"  复杂测试{i+1}: {test_time:.3f}s, 优化: {optimizations}")

    print("\\n🎉 性能测试完成！")
    return True


def print_final_stats(optimizer) -> Any:
    """打印最终统计信息"""
    print("\\n📈 最终性能统计:")

    stats = optimizer.get_performance_stats()
    health = optimizer.get_health_status()

    print(f"  总请求数: {stats.get('total_requests', 0)}")
    print(f"  缓存命中数: {stats.get('cache_hits', 0)}")
    print(f"  缓存命中率: {stats.get('cache_hit_rate', 0):.1f}%")
    print(f"  平均响应时间: {stats.get('average_response_time', 0):.3f}s")
    print(f"  快速响应数: {stats.get('fast_responses', 0)}")
    print(f"  慢响应数: {stats.get('slow_responses', 0)}")
    print(f"  上下文压缩数: {stats.get('context_compressions', 0)}")

    if 'recent_avg_response_time' in stats:
        print(f"  最近平均响应时间: {stats['recent_avg_response_time']:.3f}s")

    print(f"\\n🏥 系统健康状态: {health['overall_status']}")
    if health['warnings']:
        for warning in health['warnings']:
            print(f"  ⚠️  {warning}")

    if health['performance_summary']:
        summary = health['performance_summary']
        print("\\n📊 性能摘要:")
        for key, value in summary.items():
            print(f"  {key}: {value}")


def export_performance_data(optimizer) -> Any:
    """导出性能数据"""
    try:
        export_file = optimizer.export_metrics()
        if export_file:
            print(f"\\n📊 性能数据已导出到: {export_file}")
        else:
            print("\\n❌ 性能数据导出失败")
    except Exception as e:
        print(f"\\n❌ 导出性能数据时出错: {e}")


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="启动性能优化系统")
    parser.add_argument("--test", action="store_true", help="运行性能测试")
    parser.add_argument("--config", help="指定配置文件路径")
    parser.add_argument("--export", action="store_true", help="导出性能数据")
    parser.add_argument("--cleanup", action="store_true", help="执行清理操作")

    args = parser.parse_args()

    print_system_banner()

    try:
        # 创建性能优化器
        print("🔧 初始化性能优化器...")
        optimizer = get_optimizer()

        # 显示启动信息
        print_startup_info(optimizer)

        # 等待预加载完成（如果正在进行）
        if optimizer.preloader.load_status.get("loading"):
            print("⏳ 等待模型预加载完成...")
            while optimizer.preloader.load_status.get("loading"):
                time.sleep(0.5)
            print_startup_info(optimizer)

        # 执行清理操作
        if args.cleanup:
            print("🧹 执行清理操作...")
            cleanup_result = optimizer.cleanup()
            print(f"清理结果: {cleanup_result}")

        # 运行性能测试
        if args.test:
            success = run_performance_test(optimizer)
            if success:
                print_final_stats(optimizer)

        # 导出性能数据
        if args.export:
            export_performance_data(optimizer)

        # 如果不是测试模式，进入交互模式
        if not args.test:
            print("💡 系统已就绪！输入 'help' 查看可用命令，输入 'exit' 退出")
            print()

            while True:
                try:
                    user_input = input("🤖 Athena> ").strip()

                    if user_input.lower() in ['exit', 'quit', '退出']:
                        print("👋 再见！")
                        break

                    elif user_input.lower() in ['help', '帮助']:
                        print("可用命令:")
                        print("  stats - 查看性能统计")
                        print("  health - 查看系统健康状态")
                        print("  test - 运行性能测试")
                        print("  cleanup - 执行清理操作")
                        print("  export - 导出性能数据")
                        print("  preload status - 查看预加载状态")
                        print("  clear - 重置统计信息")
                        print("  help - 显示帮助信息")
                        print("  exit - 退出系统")

                    elif user_input.lower() == 'stats':
                        stats = optimizer.get_performance_stats()
                        print("📊 当前性能统计:")
                        for key, value in stats.items():
                            if isinstance(value, dict):
                                print(f"  {key}:")
                                for sub_key, sub_value in value.items():
                                    print(f"    {sub_key}: {sub_value}")
                            else:
                                print(f"  {key}: {value}")

                    elif user_input.lower() == 'health':
                        health = optimizer.get_health_status()
                        print("🏥 系统健康状态:")
                        print(f"  状态: {health['overall_status']}")
                        if health['warnings']:
                            print("  警告:")
                            for warning in health['warnings']:
                                print(f"    - {warning}")
                        if health['errors']:
                            print("  错误:")
                            for error in health['errors']:
                                print(f"    - {error}")

                    elif user_input.lower() == 'test':
                        run_performance_test(optimizer)

                    elif user_input.lower() == 'cleanup':
                        cleanup_result = optimizer.cleanup()
                        print(f"清理结果: {cleanup_result}")

                    elif user_input.lower() == 'export':
                        export_performance_data(optimizer)

                    elif user_input.lower() == 'preload status':
                        status = optimizer.preloader.get_load_status()
                        print("🔄 模型预加载状态:")
                        print(f"  正在加载: {status['loading']}")
                        print(f"  已完成: {status['completed']}")
                        print(f"  成功: {status['success']}")
                        print(f"  失败: {status['failed']}")
                        if status['start_time']:
                            duration = time.time() - status['start_time']
                            print(f"  用时: {duration:.2f}秒")

                    elif user_input.lower() == 'clear':
                        optimizer.reset_stats()
                        print("📊 统计信息已重置")

                    elif user_input:
                        # 模拟AI请求处理
                        print(f"🤔 处理请求: {user_input}")
                        start_time = time.time()

                        result = optimizer.optimize_request(
                            conversation_id="interactive",
                            prompt=user_input,
                            operation_type="interactive"
                        )

                        process_time = time.time() - start_time
                        print(f"✅ 处理完成，用时: {process_time:.3f}秒")
                        print(f"   缓存命中: {result.get('from_cache', False)}")
                        print(f"   优化应用: {result.get('optimization_applied', [])}")

                        # 模拟响应
                        mock_response = f"这是对'{user_input}'的智能回答。系统已应用性能优化技术来提升响应速度。"
                        optimizer.cache_response("interactive", user_input, mock_response)
                        print(f"💬 {mock_response}")

                except KeyboardInterrupt:
                    print("\\n👋 再见！")
                    break
                except Exception as e:
                    print(f"❌ 处理请求时出错: {e}")

    except Exception as e:
        print(f"❌ 系统启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
