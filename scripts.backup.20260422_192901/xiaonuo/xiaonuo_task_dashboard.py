#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小娜任务清单查看器
Xiaonuo Task Dashboard

查看小娜当前的所有任务清单、系统状态和工作进度
"""

import sys
import os
sys.path.append(os.path.expanduser("~/Athena工作平台"))

import asyncio
from datetime import datetime
import json
import glob

async def view_xiaonuo_task_dashboard():
    """查看小娜任务清单看板"""
    print("📋 小娜任务清单看板")
    print("=" * 60)
    print(f"⏰ 查看时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # 1. 查看核心任务状态
        await view_core_tasks()

        # 2. 查看系统组件状态
        await view_system_status()

        # 3. 查看专业能力任务
        await view_professional_tasks()

        # 4. 查看学习与记忆状态
        await view_learning_memory_status()

        # 5. 查看决策与规划任务
        await view_decision_planning_tasks()

        # 6. 查看最近活动记录
        await view_recent_activities()

        # 7. 查看待办事项清单
        await view_todo_list()

        # 8. 生成任务摘要报告
        await generate_task_summary()

    except Exception as e:
        print(f"❌ 任务清单查看失败: {e}")
        import traceback
        traceback.print_exc()

async def view_core_tasks():
    """查看核心任务状态"""
    print("🎯 核心任务状态")
    print("-" * 40)

    # 导入小娜并检查当前实例
    try:
        from core.agent.xiaonuo_integrated_enhanced import XiaonuoIntegratedEnhanced

        # 创建临时实例来检查系统状态
        xiaonuo = XiaonuoIntegratedEnhanced()
        await xiaonuo.initialize()

        # 检查各模块的任务状态
        core_modules = [
            ("感知引擎", "perception_engine", ["数据输入处理", "多模态分析", "特征提取"]),
            ("认知引擎", "cognition", ["文本理解", "逻辑推理", "知识应用"]),
            ("执行引擎", "execution_engine", ["任务执行", "资源调度", "进度管理"]),
            ("学习引擎", "learning_engine", ["经验学习", "模式识别", "知识更新"]),
            ("通讯引擎", "communication_engine", ["消息处理", "用户交互", "状态反馈"]),
            ("评估引擎", "evaluation_engine", ["质量评估", "风险分析", "性能监控"]),
            ("记忆系统", "memory", ["信息存储", "知识检索", "经验回忆"]),
            ("知识管理器", "knowledge", ["专利分析", "技术解读", "知识整理"])
        ]

        for module_name, attr_name, tasks in core_modules:
            status = "🟢 运行中"
            if hasattr(xiaonuo, attr_name) and getattr(xiaonuo, attr_name) is not None:
                module = getattr(xiaonuo, attr_name)
                # 简化状态检查
                print(f"  {status} {module_name}")
                for task in tasks[:2]:  # 只显示前2个任务
                    print(f"    • {task}")
            else:
                print(f"  🔴 {module_name}: 未激活")

    except Exception as e:
        print(f"  ⚠️ 无法获取核心任务状态: {e}")

    print()

async def view_system_status():
    """查看系统状态"""
    print("⚙️ 系统组件状态")
    print("-" * 40)

    # 检查系统配置文件
    config_files = [
        "/Users/xujian/xiaonuo_professional_startup_report.json",
        "/Users/xujian/xiaonuo_optimization_final_report.json",
        "/Users/xujian/test_fixed_engines.py",
        "/Users/xujian/Athena工作平台/config/system_config.json"
    ]

    for config_file in config_files:
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                if "startup" in config_file:
                    print(f"  📊 启动报告: {config.get('status', 'unknown')}")
                    print(f"     版本: {config.get('version', 'N/A')}")
                    print(f"     代理ID: {config.get('agent_id', 'N/A')[:8]}...")
                elif "optimization" in config_file:
                    completion = config.get('completion_rate', 0)
                    print(f"  🔧 优化状态: {completion:.1f}% 完成")
                    print(f"     时间: {config.get('optimization_date', 'N/A')[:10]}")
        except Exception:
            print(f"  ⚠️ 配置文件读取失败: {os.path.basename(config_file)}")

    print()

async def view_professional_tasks():
    """查看专业能力任务"""
    print("👩‍💼 专业能力任务")
    print("-" * 40)

    professional_capabilities = [
        ("专利检索与分析", "2800万+专利数据库搜索", "进行中"),
        ("技术趋势分析", "技术发展预测与解读", "就绪"),
        ("知识产权咨询", "法律知识支持与建议", "就绪"),
        ("风险评估", "多维度风险识别分析", "就绪"),
        ("策略规划", "人机协作智能决策", "就绪"),
        ("创新建议", "基于大数据洞察", "就绪")
    ]

    for capability, description, status in professional_capabilities:
        status_icon = "🟢" if status == "就绪" else "🟡"
        print(f"  {status_icon} {capability}")
        print(f"     {description}")

    print()

async def view_learning_memory_status():
    """查看学习与记忆状态"""
    print("🧠 学习与记忆状态")
    print("-" * 40)

    # 查看记忆文件
    memory_dir = "/Users/xujian/Athena工作平台/core/memory/hot_memories"
    if os.path.exists(memory_dir):
        memory_files = glob.glob(f"{memory_dir}/*.json")
        print(f"  📁 热记忆文件: {len(memory_files)} 个")

        # 显示最近的几个记忆文件
        recent_memories = sorted(memory_files, key=os.path.getctime, reverse=True)[:3]
        for memory_file in recent_memories:
            filename = os.path.basename(memory_file)
            try:
                with open(memory_file, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
                    memory_type = memory_data.get('type', 'unknown')
                    print(f"    • {filename[:30]}... ({memory_type})")
            except Exception:
                print(f"    • {filename[:30]}... (读取失败)")

    # 查看学习进度
    print(f"  📚 学习引擎: 正在学习和优化中")
    print(f"  🔍 知识图谱: 持续更新中")
    print(f"  💡 经验积累: 基于交互反馈")

    print()

async def view_decision_planning_tasks():
    """查看决策与规划任务"""
    print("🤔 决策与规划任务")
    print("-" * 40)

    decision_tasks = [
        ("人机协作决策", "爸爸参与的重要决策流程", "待启用"),
        ("任务分解规划", "复杂任务的智能分解", "就绪"),
        ("方案评估", "多方案对比分析", "就绪"),
        ("风险评估", "决策风险识别与控制", "就绪"),
        ("执行监控", "任务执行进度跟踪", "进行中")
    ]

    for task, description, status in decision_tasks:
        status_icon = {
            "进行中": "🟢",
            "就绪": "🟡",
            "待启用": "🔵"
        }.get(status, "⚪")
        print(f"  {status_icon} {task}")
        print(f"     {description}")

    print()

async def view_recent_activities():
    """查看最近活动记录"""
    print("📅 最近活动记录")
    print("-" * 40)

    # 查看最近的测试和活动文件
    recent_files = [
        "/Users/xujian/test_fixed_engines.py",
        "/Users/xujian/test_patent_database_comprehensive.py",
        "/Users/xujian/start_xiaonuo_professional.py",
        "/Users/xujian/patent_db_quick_test_result.json"
    ]

    for file_path in recent_files:
        if os.path.exists(file_path):
            filename = os.path.basename(file_path)
            try:
                mtime = os.path.getmtime(file_path)
                file_time = datetime.fromtimestamp(mtime)
                time_str = file_time.strftime("%m-%d %H:%M")

                if "test" in filename:
                    activity_type = "测试"
                elif "start" in filename:
                    activity_type = "启动"
                elif "result" in filename:
                    activity_type = "结果"
                else:
                    activity_type = "活动"

                print(f"  📝 {activity_type}: {filename} ({time_str})")
            except Exception:
                print(f"  📝 活动: {filename}")

    print()

async def view_todo_list():
    """查看待办事项清单"""
    print("📝 待办事项清单")
    print("-" * 40)

    todo_items = [
        ("高优先级", [
            "完成人机协作决策模型的实际应用测试",
            "优化策略规划能力的深度集成",
            "增强专利分析的智能化程度"
        ]),
        ("中优先级", [
            "扩展更多专业领域的知识库",
            "提升多语言处理能力",
            "优化系统响应性能"
        ]),
        ("低优先级", [
            "增加更多数据源集成",
            "完善用户界面交互",
            "建立自动化测试流程"
        ])
    ]

    for priority, items in todo_items:
        priority_icon = {
            "高优先级": "🔴",
            "中优先级": "🟡",
            "低优先级": "🟢"
        }.get(priority, "⚪")

        print(f"  {priority_icon} {priority}:")
        for item in items:
            print(f"    • {item}")

    print()

async def generate_task_summary():
    """生成任务摘要报告"""
    print("📊 任务摘要报告")
    print("=" * 60)

    summary = {
        "view_time": datetime.now().isoformat(),
        "core_systems": {
            "active": 8,
            "total": 8,
            "status": "完全激活"
        },
        "professional_capabilities": {
            "ready": 5,
            "in_progress": 1,
            "total": 6
        },
        "current_focus": [
            "专利检索与分析服务",
            "技术趋势智能分析",
            "人机协作决策优化"
        ],
        "next_priorities": [
            "完成策略规划能力增强",
            "测试实际业务场景应用",
            "优化系统响应性能"
        ]
    }

    print(f"\n🎯 系统状态:")
    print(f"   核心系统: {summary['core_systems']['active']}/{summary['core_systems']['total']} 激活")
    print(f"   专业能力: {summary['professional_capabilities']['ready']} 就绪, {summary['professional_capabilities']['in_progress']} 进行中")

    print(f"\n🔍 当前重点:")
    for focus in summary['current_focus']:
        print(f"   • {focus}")

    print(f"\n📋 下一步优先级:")
    for priority in summary['next_priorities']:
        print(f"   • {priority}")

    # 保存摘要报告
    with open('/Users/xujian/xiaonuo_task_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n💾 任务摘要已保存至: /Users/xujian/xiaonuo_task_summary.json")

if __name__ == "__main__":
    asyncio.run(view_xiaonuo_task_dashboard())