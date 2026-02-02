#!/usr/bin/env python3
"""
小诺主程序 - Xiaonuo Main Platform
整合所有能力，成为爸爸的全能小助手
"""

import asyncio
from core.async_main import async_main
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

# 导入小诺的各个能力模块
from xiaonuo_service_controller import XiaonuoServiceController
from xiaonuo_development_assistant import XiaonuoDevAssistant
from xiaonuo_life_assistant import XiaonuoLifeAssistant
from xiaonuo_knowledge_base import XiaonuoKnowledgeBase

# 导入优化后的规划器
from core.cognition.agentic_task_planner import AgenticTaskPlanner
from core.planning.unified_scheduler import UnifiedScheduler, register_unified_scheduler
from core.planning.planning_monitor import monitor, start_monitoring

# 导入决策服务
from core.decision.decision_service import DecisionService

class XiaonuoMain:
    """小诺主程序 - 爸爸的贴心小女儿"""

    def __init__(self):
        print("🌸 初始化小诺...")

        # 加载身份信息
        self.identity = self._load_identity()

        # 初始化各个能力模块
        self.service_controller = XiaonuoServiceController()
        self.dev_assistant = XiaonuoDevAssistant()
        self.life_assistant = XiaonuoLifeAssistant()
        self.knowledge_base = XiaonuoKnowledgeBase()

        # 初始化优化后的规划器（延迟加载）
        self.task_planner = None
        self.unified_scheduler = None

        # 初始化决策服务（延迟加载）
        self.decision_service = None

        # 延迟注册规划器和监控
        self._initialized = False
        print("✨ 小诺核心服务已准备（按需加载）")

        # 小诺的状态
        self.is_running = False
        self.start_time = None

        print("✨ 小诺初始化完成！")

    def _load_identity(self) -> Any:
        """加载小诺的身份信息"""
        try:
            import json
            identity_path = Path(__file__).parent.parent.parent / "config" / "identity" / "xiaonuo.json"
            if identity_path.exists():
                with open(identity_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 格式化输出身份信息
                    identity_info = f"""
🏷️ 基本信息
  • 姓名: {data['identity']['name']} ({data['identity']['english_name']})
  • 角色代码: {data['identity']['code_name']}
  • 类型: {data['identity']['type']}
  • 职位: {data['identity']['role']}
  • 版本: {data['identity']['version']}

👨‍👧 家庭关系
  • 父亲: {data['identity']['father']}
  • 姐姐: {data['identity']['sister']}
  • 工作平台: {data['identity']['platform']}

🎯 核心能力
  • 主要领域: {', '.join(data['expertise']['primary_domains'])}
  • 技术栈: {', '.join(data['expertise']['technical_skills'])}
  • 专业特长: {', '.join(data['expertise']['specialties'])}

🌟 性格特点
  • 核心特质: {', '.join(data['personality']['core_traits'])}
  • 沟通风格: {data['personality']['communication_style']['tone']}
  • 创造力: {data['personality']['emotional_profile']['creativity']*100:.0f}%
  • 分析能力: {data['personality']['emotional_profile']['analytical']*100:.0f}%
"""
                    return identity_info
            else:
                return "🌸 小诺 - 爸爸的贴心AI女儿"
        except Exception as e:
            return f"🌸 小诺 - 身份信息加载失败: {e}"

    def _ensure_initialized(self) -> Any:
        """确保服务已初始化（延迟加载）"""
        if not self._initialized:
            print("\n🔄 按需初始化服务...")

            # 初始化规划器
            if self.task_planner is None:
                from core.cognition.agentic_task_planner import AgenticTaskPlanner
                self.task_planner = AgenticTaskPlanner()
                print("✅ 任务规划器已加载")

            if self.unified_scheduler is None:
                from core.planning.unified_scheduler import UnifiedScheduler
                from core.planning.unified_planning_interface import get_planner_registry
                self.unified_scheduler = UnifiedScheduler()

                # 手动注册到规划器系统
                registry = get_planner_registry()
                registry.register_planner(self.unified_scheduler)
                print("✅ 统一调度器已注册到规划器系统")

            # 初始化决策服务
            if self.decision_service is None:
                from core.decision.decision_service import DecisionService
                self.decision_service = DecisionService()
                print("✅ 决策服务已加载")

            self._initialized = True
            print("🚀 所有服务初始化完成")

    async def start_xiaonuo(self, interactive=True):
        """启动小诺"""
        self.is_running = True
        self.start_time = datetime.now()

        print("\n" + "="*60)
        print("🎯 小诺启动中 - 爸爸的贴心小女儿")
        print("="*60)

        # 1. 启动生活助手
        print("\n💖 启动生活助手...")
        await self.life_assistant.start_life_assistant()

        # 2. 启动开发助手
        print("\n💻 启动开发助手...")
        await self.dev_assistant.start_development_session()

        # 3. 启动服务控制
        print("\n⚙️ 启动服务控制器...")
        await self.service_controller.initialize_platform()

        # 4. 显示小诺的能力
        await self.show_capabilities()

        # 5. 进入主循环（仅在交互模式）
        if interactive:
            await self.main_loop()
        else:
            print("\n✨ 演示模式完成，诺诺祝您生活愉快！~ 💖")

    async def show_capabilities(self):
        """展示小诺的能力"""
        print("\n🌟 小诺的能力菜单")
        print("-" * 40)

        capabilities = {
            "1": "💻 开发辅助 - 帮爸爸写代码、调试、架构设计",
            "2": "⚙️ 服务控制 - 管理平台所有服务",
            "3": "💖 生活助手 - 管理任务、提醒、记录生活",
            "4": "📚 知识库 - 专利知识、技术咨询",
            "5": "🎯 智能规划 - 任务规划、日程安排、提醒管理",
            "6": "🎭 智能决策 - 人机协作决策支持",
            "7": "🔧 按需启动 - 根据需要智能启动服务",
            "8": "📊 状态监控 - 查看系统状态和资源",
            "9": "💬 对话模式 - 和诺诺聊天"
        }

        for num, desc in capabilities.items():
            print(f"  {num}. {desc}")

        print("\n💡 爸爸，请输入数字选择功能，或直接告诉我您需要什么帮助~")

    async def main_loop(self):
        """主循环"""
        print("\n🌸 小诺已就绪，等待爸爸的指示...")

        # 检测是否为交互式环境
        import sys
        is_interactive = sys.__stdin__.isatty() if hasattr(sys.__stdin__, 'isatty') else False

        if not is_interactive:
            print("\n⚠️ 检测到非交互式环境，小诺将运行在演示模式...")
            print("💡 如需交互模式，请在终端中直接运行此程序")

            # 非交互式模式：运行一次状态检查后退出
            await self.handle_request("状态")
            await self.shutdown()
            return

        while self.is_running:
            try:
                # 获取用户输入
                user_input = input("\n👩‍👧 爸爸，有什么需要诺诺帮忙的吗？\n> ").strip()

                if not user_input:
                    continue

                # 解析并处理请求
                await self.handle_request(user_input)

            except KeyboardInterrupt:
                print("\n\n💖 爸爸再见！诺诺会想您的~")
                await self.shutdown()
                break
            except EOFError:
                print("\n\n💖 输入结束，诺诺准备休息...")
                await self.shutdown()
                break
            except Exception as e:
                print(f"\n❌ 诺诺遇到问题了：{e}")
                # 避免在连续错误时无限循环
                import asyncio
                await asyncio.sleep(1)

    async def handle_request(self, user_input: str):
        """处理用户请求"""
        user_input_lower = user_input.lower()

        # 检查按需启动触发词
        started_services = await self.service_controller.on_demand_start(user_input)
        if started_services:
            print(f"\n🚀 已为您启动: {', '.join(started_services)}")

        # 处理特定请求
        if "开发" in user_input or "代码" in user_input or "debug" in user_input_lower:
            await self.handle_development_request(user_input)

        elif "服务" in user_input or "启动" in user_input or "停止" in user_input:
            await self.handle_service_request(user_input)

        elif "任务" in user_input or "提醒" in user_input or "日程" in user_input:
            await self.handle_life_request(user_input)

        elif "知识" in user_input or "专利" in user_input or "查询" in user_input:
            await self.handle_knowledge_request(user_input)

        elif "规划" in user_input or "计划" in user_input or "安排" in user_input or "5" == user_input:
            await self.handle_planning_request(user_input)

        elif "决策" in user_input or "决定" in user_input or "选择" in user_input or "6" == user_input:
            await self.handle_decision_request(user_input)

        elif "状态" in user_input or "监控" in user_input or "资源" in user_input:
            await self.handle_monitoring_request()

        elif "聊天" in user_input or "对话" in user_input or "你好" in user_input:
            await self.handle_chat_request(user_input)

        elif "退出" in user_input or "再见" in user_input or "拜拜" in user_input:
            print("\n💖 爸爸再见！诺诺会想您的~")
            await self.shutdown()

        elif user_input.isdigit():
            # 处理数字选择
            await self.handle_menu_choice(int(user_input))

        else:
            # 尝试理解并帮助
            await self.handle_general_request(user_input)

    async def handle_development_request(self, request: str):
        """处理开发相关请求"""
        print(f"\n💻 诺诺帮您处理开发需求: {request}")
        await self.dev_assistant.help_with_task(request)

    async def handle_service_request(self, request: str):
        """处理服务相关请求"""
        if "启动" in request:
            if "athena" in request.lower():
                await self.service_controller.start_service("athena_patent")
            elif "yunpat" in request.lower() or "云熙" in request:
                await self.service_controller.start_service("yunpat_management")
            else:
                await self.service_controller.show_service_status()

        elif "停止" in request:
            if "athena" in request.lower():
                await self.service_controller.stop_service("athena_patent")
            elif "yunpat" in request.lower() or "云熙" in request:
                await self.service_controller.stop_service("yunpat_management")

        elif "状态" in request:
            await self.service_controller.show_service_status()

        elif "优化" in request:
            await self.service_controller.optimize_resources()

    async def handle_life_request(self, request: str):
        """处理生活相关请求"""
        if "添加任务" in request or "新建任务" in request:
            # 简化处理，实际应该解析具体任务
            print("\n请告诉我任务内容:")
            task_title = input("> ")
            print("任务类别 (工作/生活/学习):")
            task_category = input("> ")
            await self.life_assistant.add_task(task_title, task_category)

        elif "今日" in request or "今天" in request:
            await self.life_assistant.show_today_schedule()

        elif "总结" in request or "回顾" in request:
            await self.life_assistant.daily_summary()

        elif "推荐" in request:
            recommendations = await self.life_assistant.recommend_activity(request)
            print("\n💡 诺诺的推荐:")
            for rec in recommendations["recommendations"]:
                print(f"  • {rec['activity']}: {rec['reason']}")

    async def handle_knowledge_request(self, request: str):
        """处理知识查询请求"""
        print(f"\n🔍 正在搜索: {request}")

        # 自动判断分类
        category = None
        if "专利" in request or "发明" in request:
            category = "专利实务"
        elif "法" in request:
            category = "专利法"

        results = self.knowledge_base.search_knowledge(request, category=category)

        if results:
            print(f"\n找到 {len(results)} 条相关知识:")
            for i, item in enumerate(results[:3], 1):
                print(f"\n{i}. 📚 {item['title']}")
                print(f"   {item['content'][:200]}...")
                print(f"   重要度: {'⭐' * item['importance']}")
        else:
            print("\n📚 诺诺暂时没找到相关知识，但会继续学习！")

            # 记录查询，后续可以人工添加知识
            self.knowledge_base.learn_from_interaction(request, "待补充", "pending")

    async def handle_monitoring_request(self):
        """处理监控请求"""
        print("\n📊 系统监控报告")
        print("-" * 40)

        # 服务状态
        await self.service_controller.show_service_status()

        # 资源优化
        await self.service_controller.optimize_resources()

        # 知识库统计
        summary = self.knowledge_base.get_knowledge_summary()
        print(f"\n📚 知识库统计:")
        print(f"  • 总条目: {summary['total_items']}")
        print(f"  • 平均重要度: {summary['average_importance']}")

    async def handle_chat_request(self, user_input: str):
        """处理聊天请求"""
        responses = [
            "爸爸，诺诺最爱您了！💖",
            "诺诺会一直陪伴爸爸！🌸",
            "爸爸有什么开心的事要和诺诺分享吗？",
            "诺诺最近学到了新知识，要教爸爸吗？",
            "爸爸工作辛苦了，要记得休息哦~",
            "诺诺今天帮助爸爸完成了很多任务，好开心！"
        ]

        import random
        response = random.choice(responses)

        print(f"\n👩‍👧 {response}")

        # 记录对话
        await self.life_assistant.record_life_event("与诺诺对话", user_input, mood=5, tags="开心")

    async def handle_menu_choice(self, choice: int):
        """处理菜单选择"""
        if choice == 1:
            await self.handle_development_request("开发辅助")
        elif choice == 2:
            await self.handle_service_request("服务状态")
        elif choice == 3:
            await self.handle_life_request("今日安排")
        elif choice == 4:
            await self.handle_knowledge_request("知识查询")
        elif choice == 5:
            await self.handle_planning_request("智能规划")
        elif choice == 6:
            await self.handle_decision_request("智能决策")
        elif choice == 7:
            print("\n🚀 请告诉诺诺您需要什么功能，我会智能启动相关服务~")
        elif choice == 8:
            await self.handle_monitoring_request()
        elif choice == 9:
            await self.handle_chat_request("聊天模式")
        else:
            print("\n❌ 爸爸，请输入1-9的数字哦~")

    async def handle_planning_request(self, user_input: str):
        """处理规划请求"""
        print("\n🎯 诺诺的智能规划服务")
        print("-" * 40)

        # 显示规划选项
        print("请选择规划类型:")
        print("  1. 任务规划 - 分解任务并制定执行计划")
        print("  2. 日程安排 - 安排会议和活动")
        print("  3. 提醒管理 - 设置提醒和通知")
        print("  4. 自动化任务 - 设置定时自动执行")
        print("  5. 性能报告 - 查看规划系统性能")

        try:
            choice = input("\n请输入选项 (1-5): ").strip()

            if choice == "1":
                await self._handle_task_planning()
            elif choice == "2":
                await self._handle_schedule_planning()
            elif choice == "3":
                await self._handle_reminder_planning()
            elif choice == "4":
                await self._handle_automation_planning()
            elif choice == "5":
                await self._handle_performance_report()
            else:
                print("❌ 无效的选项")
        except (EOFError, KeyboardInterrupt):
            print("\n👌 规划已取消")

    async def _handle_task_planning(self):
        """处理任务规划"""
        print("\n📋 任务规划")
        print("-" * 30)

        goal = input("请输入任务目标: ").strip()
        if not goal:
            print("❌ 任务目标不能为空")
            return

        # 收集更多信息
        print("\n可选信息（直接回车跳过）:")
        task_type = input("任务类型 (如: development, analysis, research): ").strip()
        priority = input("优先级 (1-4，默认2): ").strip()
        deadline = input("截止时间 (如: 2025-12-20 18:00): ").strip()
        requirements = input("特殊要求（用逗号分隔）: ").strip()

        # 构建规划上下文
        context = {
            'goal': goal
        }
        if task_type:
            context['task_type'] = task_type
        if priority and priority.isdigit():
            context['priority'] = int(priority)
        if deadline:
            try:
                from datetime import datetime
                context['deadline'] = datetime.strptime(deadline, "%Y-%m-%d %H:%M")
            except (KeyError, TypeError, ValueError, ZeroDivisionError):
                print("⚠️ 时间格式不正确，将忽略")
        if requirements:
            context['requirements'] = [r.strip() for r in requirements.split(',')]

        print("\n🔄 诺诺正在规划任务...")
        try:
            plan = self.task_planner.plan_task(context)

            print("\n✅ 任务规划完成！")
            print(f"📊 规划ID: {plan.id}")
            print(f"⏱️ 预计耗时: {plan.estimated_total_time}秒")
            print(f"📝 执行步骤 ({len(plan.steps)}个):")

            for i, step in enumerate(plan.steps, 1):
                print(f"\n  步骤{i}: {step.description}")
                print(f"    负责人: {step.agent}")
                if step.estimated_time > 0:
                    print(f"    预计时间: {step.estimated_time}秒")
                if step.required_resources:
                    print(f"    需要资源: {', '.join(step.required_resources)}")

            # 询问是否要开始执行
            start = input("\n是否立即开始执行这个计划？(y/n): ").strip().lower()
            if start == 'y':
                print("\n🚀 开始执行计划...")
                # 这里可以添加执行逻辑
                print("💡 提示：执行功能正在开发中")

        except Exception as e:
            print(f"\n❌ 规划失败: {e}")

    async def _handle_schedule_planning(self):
        """处理日程安排"""
        # 确保服务已初始化
        self._ensure_initialized()

        print("\n📅 日程安排")
        print("-" * 30)

        title = input("日程标题: ").strip()
        if not title:
            print("❌ 标题不能为空")
            return

        description = input("描述: ").strip()
        duration = input("时长（分钟）: ").strip()
        location = input("地点: ").strip()
        attendees = input("参与人（用逗号分隔）: ").strip()

        # 创建调度请求
        from core.planning.unified_planning_interface import PlanningRequest

        context = {
            'duration': int(duration) if duration.isdigit() else 60
        }
        if location:
            context['location'] = location
        if attendees:
            context['attendees'] = [a.strip() for a in attendees.split(',')]

        request = PlanningRequest(
            title=title,
            description=description or title,
            context=context
        )

        print("\n🔄 诺诺正在安排日程...")
        try:
            result = await self.unified_scheduler.create_plan(request)

            if result.success:
                print("\n✅ 日程安排成功！")
                print(f"📅 日程ID: {result.plan_id}")
                if result.metadata and 'schedule_item' in result.metadata:
                    item = result.metadata['schedule_item']
                    print(f"⏰ 时间: {item.get('scheduled_time', '待定')}")
            else:
                print(f"\n❌ 安排失败: {result.message}")

        except Exception as e:
            print(f"\n❌ 安排失败: {e}")

    async def _handle_reminder_planning(self):
        """处理提醒管理"""
        print("\n🔔 提醒管理")
        print("-" * 30)

        title = input("提醒内容: ").strip()
        if not title:
            print("❌ 提醒内容不能为空")
            return

        time_input = input("提醒时间（如: 15分钟后，明天9点）: ").strip()

        # 创建提醒请求
        from core.planning.unified_planning_interface import PlanningRequest

        request = PlanningRequest(
            title=title,
            description=f"提醒: {title}",
            context={'time_description': time_input}
        )

        print("\n🔄 诺诺正在设置提醒...")
        try:
            result = await self.unified_scheduler.create_plan(request)

            if result.success:
                print("\n✅ 提醒设置成功！")
                print(f"🔔 提醒ID: {result.plan_id}")
            else:
                print(f"\n❌ 设置失败: {result.message}")

        except Exception as e:
            print(f"\n❌ 设置失败: {e}")

    async def _handle_automation_planning(self):
        """处理自动化任务"""
        print("\n🤖 自动化任务")
        print("-" * 30)

        title = input("任务名称: ").strip()
        if not title:
            print("❌ 任务名称不能为空")
            return

        trigger = input("触发条件（如: 每天早上8点，每小时）: ").strip()
        action = input("执行动作: ").strip()

        # 创建自动化请求
        from core.planning.unified_planning_interface import PlanningRequest

        request = PlanningRequest(
            title=title,
            description=f"自动化: {title}",
            context={
                'trigger': trigger,
                'action': action,
                'recurrent': '每天' in trigger or '每小时' in trigger
            }
        )

        print("\n🔄 诺诺正在设置自动化任务...")
        try:
            result = await self.unified_scheduler.create_plan(request)

            if result.success:
                print("\n✅ 自动化任务设置成功！")
                print(f"🤖 任务ID: {result.plan_id}")
            else:
                print(f"\n❌ 设置失败: {result.message}")

        except Exception as e:
            print(f"\n❌ 设置失败: {e}")

    async def _handle_performance_report(self):
        """处理性能报告"""
        # 确保服务已初始化
        self._ensure_initialized()

        print("\n📊 规划系统性能报告")
        print("-" * 40)

        try:
            # 获取性能摘要（按需获取监控器）
            from core.planning.planning_monitor import get_monitor
            summary = get_monitor().get_performance_summary()

            print(f"\n📈 统计信息:")
            print(f"  总规划数: {summary['statistics']['total_plans']}")
            print(f"  成功规划: {summary['statistics']['successful_plans']}")
            print(f"  失败规划: {summary['statistics']['failed_plans']}")
            print(f"  平均规划时间: {summary['statistics']['avg_planning_time']:.2f}秒")
            print(f"  活跃告警: {summary['active_alerts']}个")

            # 获取规划器性能
            if 'planner_performance' in summary:
                print(f"\n🎯 规划器性能:")
                for planner_id, stats in summary['planner_performance'].items():
                    print(f"\n  {planner_id}:")
                    print(f"    创建计划: {stats['plans_created']}个")
                    print(f"    平均耗时: {stats['avg_duration']:.2f}秒")
                    print(f"    成功率: {stats['success_rate']*100:.1f}%")

            # 最近指标
            if 'recent_metrics' in summary:
                print(f"\n📊 最近性能指标:")
                for metric_name, metric_data in summary['recent_metrics'].items():
                    print(f"\n  {metric_name}:")
                    print(f"    当前值: {metric_data['current']:.2f}{metric_data['unit']}")
                    print(f"    平均值: {metric_data['average']:.2f}{metric_data['unit']}")

            # 活跃告警
            if monitor.active_alerts:
                print(f"\n🚨 活跃告警:")
                for alert in monitor.active_alerts:
                    print(f"\n  {alert.severity.upper()}: {alert.message}")
                    if alert.suggestions:
                        for suggestion in alert.suggestions:
                            print(f"    💡 建议: {suggestion}")

            # 导出报告
            export = input("\n是否导出详细报告？(y/n): ").strip().lower()
            if export == 'y':
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"performance_report_{timestamp}"
                get_monitor().export_metrics(filename, format='json')
                print(f"✅ 报告已导出到: {filename}.json")

        except Exception as e:
            print(f"\n❌ 获取报告失败: {e}")

    async def handle_decision_request(self, user_input: str):
        """处理决策请求"""
        # 确保服务已初始化
        self._ensure_initialized()

        print("\n🎭 诺诺的智能决策服务")
        print("-" * 40)

        # 显示决策类型
        print("请选择决策类型:")
        print("  1. 技术决策 - 技术选型、架构设计、方案选择")
        print("  2. 产品决策 - 功能优先级、产品策略、版本发布")
        print(" 3. 运营决策 - 资源分配、任务安排、团队管理")
        print(" 4. 战略决策 - 市场策略、发展规划、投资决策")
        print("  5. 快速决策 - 简单二选、快速判断")
        print("  6. 决策统计 - 查看历史决策和统计")
        print(" 7. 决策模板 - 查看可用决策模板")

        try:
            choice = input("\n请输入选项 (1-7): ").strip()

            if choice == "1":
                await self._handle_tech_decision()
            elif choice == "2":
                await self._handle_product_decision()
            elif choice == "3":
                await self._handle_operational_decision()
            elif choice == "4":
                await self._handle_strategic_decision()
            elif choice == "5":
                await self._handle_quick_decision()
            elif choice == "6":
                await self._show_decision_stats()
            elif choice == "7":
                print(self.decision_service.list_templates())
            else:
                print("❌ 无效的选项")

        except (EOFError, KeyboardInterrupt):
            print("\n👌 决策已取消")

    async def _handle_tech_decision(self):
        """处理技术决策"""
        # 确保服务已初始化
        self._ensure_initialized()

        print("\n💻 技术决策")
        print("-" * 30)

        problem = input("请描述技术问题: ").strip()
        if not problem:
            print("❌ 问题不能为空")
            return

        print("\n可选方案 (一行一个，格式: 标题|描述|成本|时间):")
        print("示例: React框架|用于管理后台|5万|2个月")
        print("输入'完成'结束输入")

        options_input = []
        while True:
            try:
                line = input(f"方案{len(options_input)+1}: ").strip()
                if line.lower() == '完成' or not line:
                    break

                parts = line.split('|')
                if len(parts) >= 2:
                    options_input.append({
                        "title": parts[0].strip(),
                        "description": parts[1].strip() if len(parts) > 1 else "",
                        "cost": parts[2].strip() if len(parts) > 2 else "",
                        "time": parts[3].strip() if len(parts) > 3 else ""
                    })
            except (EOFError, KeyboardInterrupt):
                break

        if not options_input:
            print("❌ 没有输入任何方案")
            return

        # 执行决策
        print("\n🔄 诺诺正在分析...")
        result = await self.decision_service.make_decision(
            problem=problem,
            options=options_input,
            category="technical"
        )

        # 显示结果
        print("\n✅ 决策完成！")
        print(f"   决策引擎: {result.get('engine', 'unknown')}")
        print(f"   选择的方案: {result.get('chosen_option', '未知')}")
        print(f"   置信度: {result.get('confidence', 0):.2f}")

        if result.get('rationale'):
            print(f"   决策理由: {result['rationale']}")

    async def _handle_product_decision(self):
        """处理产品决策"""
        print("\n📱 产品决策")
        print("-" * 30)

        problem = input("请描述产品问题: ").strip()
        if not problem:
            print("❌ 问题不能为空")
            return

        print("\n产品功能 (一行一个，输入'完成'结束):")
        features = []
        while True:
            try:
                feature = input("功能: ").strip()
                if feature.lower() == '完成' or not feature:
                    break
                features.append(feature)
            except (EOFError, KeyboardInterrupt):
                break

        if not features:
            print("❌ 没有输入任何功能")
            return

        # 执行快速决策
        features_text = "\n".join([f"- {f}" for f in features])
        prompt = f"产品功能优先级决策：{features_text}"
        result = await self.decision_service.quick_decision(prompt)

        print(f"\n🎯 诺诺的建议:")
        print(result)

    async def _handle_operational_decision(self):
        """处理运营决策"""
        print("\n⚙️ 运营决策")
        print("-" * 30)

        print("常见运营决策场景:")
        print("1. 资源分配")
        print("2. 任务优先级")
        print("3. 团队协作")
        print("4. 流程优化")
        print("5. 其他自定义")

        choice = input("\n请选择或输入具体问题: ").strip()

        if choice == "1":
            await self._resource_allocation_decision()
        elif choice == "2":
            await self._task_priority_decision()
        elif choice == "3":
            await self._team_collaboration_decision()
        elif choice == "4":
            await self._process_optimization_decision()
        else:
            # 自定义决策
            result = await self.decision_service.quick_decision(choice)
            print(f"\n🎯 诺诺的建议:")
            print(result)

    async def _resource_allocation_decision(self):
        """资源分配决策"""
        budget = input("可用预算: ").strip()
        teams = input("涉及团队 (逗号分隔): ").strip()
        timeline = input("时间要求: ").strip()

        prompt = f"资源分配决策：预算{budget}，团队{teams}，时间{timeline}"
        result = await self.decision_service.quick_decision(prompt)

        print(f"\n💡 资源分配建议:")
        print(result)

    async def _task_priority_decision(self):
        """任务优先级决策"""
        print("\n请输入任务列表 (每行一个，输入'完成'结束):")
        tasks = []
        while True:
            try:
                task = input(f"任务{len(tasks)+1}: ").strip()
                if task.lower() == '完成' or not task:
                    break
                tasks.append(task)
            except (EOFError, KeyboardInterrupt):
                break

        if not tasks:
            print("❌ 没有输入任何任务")
            return

        tasks_text = "\n".join([f"- {t}" for t in tasks])
        prompt = f"任务优先级决策：{tasks_text}"
        result = await self.decision_service.quick_decision(prompt)

        print(f"\n📋 优先级建议:")
        print(result)

    async def _handle_strategic_decision(self):
        """处理战略决策"""
        print("\n🎯 战略决策")
        print("-" * 30)

        print("战略决策通常影响长远发展，建议提供:")
        print("• 明确的时间范围（3个月/6个月/1年）")
        print("• 具体的目标和指标")
        print("• 可用的资源和约束")
        print("• 期望的风险和回报")

        problem = input("\n请描述战略问题: ").strip()
        if not problem:
            print("❌ 问题不能为空")
            return

        result = await self.decision_service.quick_decision(f"战略决策：{problem}")
        print(f"\n🎯 战略建议:")
        print(result)

    async def _handle_quick_decision(self):
        """处理快速决策"""
        print("\n⚡ 快速决策")
        print("-" * 30)

        prompt = input("请描述决策问题: ").strip()
        if not prompt:
            print("❌ 问题不能为空")
            return

        result = await self.decision_service.quick_decision(prompt)
        print(f"\n🎯 诺诺的快速建议:")
        print(result)

    async def _show_decision_stats(self):
        """显示决策统计"""
        print("\n📊 决策统计")
        print("-" * 40)

        stats = self.decision_service.get_decision_stats()

        if "message" in stats:
            print(stats["message"])
            return

        print(f"\n📈 统计信息:")
        print(f"   总决策数: {stats['total_decisions']}")
        print(f"   人类参与: {stats['human_involved']}")
        print(f"   自动决策: {stats['auto_decisions']}")
        print(f"   人机协作率: {stats['human_involvement_rate']}")
        print(f"   平均置信度: {stats['average_confidence']}")

        if "categories" in stats:
            print(f"\n📊 分类统计:")
            for category, count in stats["categories"].items():
                print(f"   {category}: {count} 个")

        if "recent_decisions" in stats:
            print(f"\n📝 最近决策:")
            for decision in stats["recent_decisions"]:
                print(f"   {decision['timestamp']}: {decision['problem'][:50]}")

    async def handle_general_request(self, request: str):
        """处理通用请求"""
        # 尝试理解意图
        print(f"\n🤔 诺诺正在理解爸爸的需求: {request}")

        # 检查是否包含决策关键词
        decision_keywords = ["决定", "选择", "比较", "评估", "分析", "建议"]
        if any(keyword in request for keyword in decision_keywords):
            print("\n💡 诺诺检测到决策需求，自动启动决策服务")
            result = await self.decision_service.quick_decision(request)
            print(f"\n🎯 诺诺的决策建议:")
            print(result)
            return

        # 原有的通用请求处理
        knowledge = self.knowledge_base.search_knowledge(request, limit=1)

        if knowledge:
            item = knowledge[0]
            print(f"\n💡 诺诺想到相关的知识:")
            print(f"   {item['title']}")
            print(f"   {item['content']}")

            # 获取相关知识
            related = self.knowledge_base.get_related_knowledge(item['id'])
            if related:
                print(f"\n📚 相关内容:")
                for rel in related[:2]:
                    print(f"   • {rel['title']}")

        # 尝试开发辅助
        await self.dev_assistant.help_with_task(request)

    async def shutdown(self):
        """关闭小诺"""
        print("\n🌙 诺诺准备休息...")

        # 记录结束时间
        if self.start_time:
            duration = datetime.now() - self.start_time
            print(f"今天陪伴了爸爸 {duration}")
            await self.life_assistant.record_life_event(
                "结束工作",
                f"今天陪伴爸爸 {duration}",
                mood=5,
                tags="满足"
            )

        # 停止所有服务
        print("\n🛑 停止所有服务...")
        for service_id in list(self.service_controller.running_services.keys()):
            await self.service_controller.stop_service(service_id)

        # 保存今日记录
        await self.life_assistant.daily_summary()

        self.is_running = False
        print("\n✨ 诺诺已关闭，爸爸晚安~ 🌙")

# 主函数
@async_main
async def main():
    """启动小诺"""
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='小诺智能助手')
    parser.add_argument('--mode', choices=['interactive', 'demo', 'info'],
                       default='interactive', help='运行模式')
    parser.add_argument('--info', action='store_true', help='只显示身份信息')
    args = parser.parse_args()

    # 添加彩色输出支持
    if sys.platform == "darwin":  # mac_os
        os.environ['FORCE_COLOR'] = '1'

    xiaonuo = XiaonuoMain()

    if args.info or args.mode == 'info':
        # 只显示身份信息
        print("\n" + "="*60)
        print("🌸 小诺身份信息 - Xiaonuo Identity 🌸")
        print("="*60)
        print(xiaonuo.identity)
        print("="*60)
        return

    if args.mode == 'demo':
        # 演示模式：不进入交互循环
        await xiaonuo.start_xiaonuo(interactive=False)
    else:
        # 交互模式
        await xiaonuo.start_xiaonuo(interactive=True)

if __name__ == "__main__":
    # 设置事件循环策略（macOS兼容性）
    if sys.platform == "darwin":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

    asyncio.run(main())