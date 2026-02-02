#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单监控示例
Simple Monitor Example

显示系统状态和性能指标
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

# 导入按需启动AI系统
sys.path.append(str(Path.cwd()))
from ready_on_demand_system import ai_system

class SimpleMonitor:
    """简单监控器"""

    def __init__(self):
        self.start_time = datetime.now()

    async def show_status(self):
        """显示系统状态"""
        try:
            # 初始化系统
            print("🚀 初始化系统...")
            await ai_system.initialize()

            # 获取状态
            status = ai_system.get_status()

            print("\n📊 系统状态报告")
            print("=" * 50)
            print(f"⏰ 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🏠 运行智能体: {status['running_agents']}/{status['total_agents']}")
            print(f"💾 内存使用: {status['memory_usage_mb']} MB")
            print(f"📈 资源效率: {status['resource_efficiency']}")
            print(f"📝 处理任务: {status['total_tasks']}")
            print(f"🚀 智能体启动: {status['agent_starts']}次")
            print(f"💰 节省内存: {status['memory_saved_mb']} MB")

            # 运行中的智能体
            if 'running_agent_names' in status:
                print(f"\n🤖 当前运行的智能体:")
                for agent in status['running_agent_names']:
                    print(f"   ✅ {agent}")

            # 性能分析
            total_possible_memory = 350  # 4个智能体全部运行的内存
            current_memory = status['memory_usage_mb']
            saved_memory = total_possible_memory - current_memory
            saved_percentage = (saved_memory / total_possible_memory) * 100

            print(f"\n💡 性能分析:")
            print(f"   理论最大内存: {total_possible_memory} MB")
            print(f"   当前使用内存: {current_memory} MB")
            print(f"   节省内存: {saved_memory} MB ({saved_percentage:.1f}%)")

            # 状态评估
            print(f"\n📋 状态评估:")
            if saved_percentage > 50:
                print("   ✅ 优秀: 内存节省率超过50%")
            elif saved_percentage > 30:
                print("   ✅ 良好: 内存节省率超过30%")
            else:
                print("   ⚠️  一般: 可以进一步优化内存使用")

            if status['resource_efficiency'] > 75:
                print("   ✅ 优秀: 资源效率很高")
            elif status['resource_efficiency'] > 50:
                print("   ✅ 良好: 资源效率合理")
            else:
                print("   ⚠️  一般: 资源利用率可以提升")

            # 保存报告
            report = {
                "timestamp": datetime.now().isoformat(),
                "status": status,
                "analysis": {
                    "memory_saved_percentage": saved_percentage,
                    "total_possible_memory": total_possible_memory,
                    "current_memory": current_memory
                }
            }

            with open('monitor_report.json', 'w') as f:
                json.dump(report, f, indent=2)

            print(f"\n📄 报告已保存到: monitor_report.json")

            return True

        except Exception as e:
            print(f"❌ 监控错误: {e}")
            return False

async def demo_workload():
    """演示工作负载"""
    print("\n🔄 模拟工作负载...")
    print("-" * 30)

    tasks = [
        ("基础对话", "你好"),
        ("专利分析", "请分析这个专利的权利要求"),
        ("IP查询", "查询案卷状态"),
        ("内容创作", "写一篇技术文章"),
        ("混合查询", "帮我分析专利并写总结")
    ]

    for task_name, task_content in tasks:
        print(f"📝 处理: {task_name}")

        if "专利" in task_content:
            response = await ai_system.patent_analysis(task_content)
        elif "案卷" in task_content:
            response = await ai_system.ip_management(task_content)
        elif "写" in task_content:
            response = await ai_system.content_creation(task_content)
        else:
            response = await ai_system.chat(task_content)

        print(f"   ✅ 完成 ({len(response)}字符)")

async def main():
    """主函数"""
    monitor = SimpleMonitor()

    print("🔍 简单监控系统")
    print("=" * 50)

    # 显示初始状态
    await monitor.show_status()

    # 模拟一些工作负载
    await demo_workload()

    # 再次显示状态
    print("\n📊 工作负载后状态")
    await monitor.show_status()

    print("\n🎉 监控完成!")
    print("💡 建议:")
    print("   1. 定期运行此脚本检查系统状态")
    print("   2. 监控内存使用趋势")
    print("   3. 根据使用模式调整配置")
    print("   4. 关注系统资源使用情况")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 监控已停止")
    except Exception as e:
        print(f"❌ 运行错误: {e}")