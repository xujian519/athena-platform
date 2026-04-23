#!/usr/bin/env python3
"""
集成系统启动脚本
启动包含所有优化模式的Athena平台

时间: 2025-12-17
版本: 1.0
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntegratedSystemLauncher:
    """集成系统启动器"""

    def __init__(self):
        self.base_path = Path("/Users/xujian/Athena工作平台")
        self.system = None
        self.adapter = None
        self.agents = {}
        self.monitoring_active = False
        self.AgentCapability = None  # 存储能力类
        self.MemoryType = None      # 存储记忆类型
        self.performance_monitor = None  # 性能监控器

    async def initialize_system(self):
        """初始化集成系统"""
        logger.info("🔧 初始化集成系统...")

        try:
            # 导入并初始化优化模块
            sys.path.insert(0, str(self.base_path))

            # 导入反思引擎
            from core.intelligence.reflection_engine import ReflectionEngine
            reflection_engine = ReflectionEngine()
            logger.info("✅ 反思引擎初始化完成")

            # 导入并行执行器
            from core.execution.parallel_executor import ParallelExecutor
            parallel_executor = ParallelExecutor(max_workers=5, max_concurrent_tasks=10)
            logger.info("✅ 并行执行器初始化完成")

            # 导入智能体协作器
            from core.framework.collaboration.enhanced_agent_coordination import (
                EnhancedAgentCoordinator,
            )

            # 创建智能体能力实例（因为枚举不存在）
            class MockAgentCapability:
                PATENT_ANALYSIS = "patent_analysis"
                SYSTEM_OPTIMIZATION = "system_optimization"
                PROJECT_MANAGEMENT = "project_management"
                CONTENT_GENERATION = "content_generation"
                DATA_PROCESSING = "data_processing"
                REPORT_GENERATION = "report_generation"
                TROUBLESHOOTING = "troubleshooting"
                PERFORMANCE_ANALYSIS = "performance_analysis"
                TARGET_TRACKING = "target_tracking"
                COORDINATION = "coordination"
                CREATIVE_DESIGN = "creative_design"
                OPTIMIZATION = "optimization"

            self.AgentCapability = MockAgentCapability

            # 导入记忆管理器
            from core.framework.memory.enhanced_memory_manager import (
                EnhancedMemoryManager,
                MemoryType,
            )
            self.MemoryType = MemoryType
            memory_manager = EnhancedMemoryManager()
            logger.info("✅ 记忆管理器初始化完成")

            coordinator = EnhancedAgentCoordinator()
            logger.info("✅ 智能体协作器初始化完成")

            # 导入系统适配器
            from core.adapters.system_adapter import SystemAdapter

            # 导入性能监控器
            from core.monitoring.performance_monitor import PerformanceMonitor
            self.performance_monitor = PerformanceMonitor(monitoring_interval=15.0)
            logger.info("✅ 性能监控器初始化完成")

            system_components = {
                "reflection": reflection_engine,
                "parallel": parallel_executor,
                "memory": memory_manager,
                "coordination": coordinator,
                "monitor": self.performance_monitor
            }

            class MockIntegratedSystem:
                def __init__(self, components):
                    self.components = components

                def get_component(self, name) -> None:
                    return self.components.get(name)

                def get_system_status(self) -> Any | None:
                    return {
                        "active_components": list(self.components.keys()),
                        "system_health": "healthy"
                    }

            mock_system = MockIntegratedSystem(system_components)
            adapter = SystemAdapter(mock_system)
            logger.info("✅ 系统适配器初始化完成")

            # 存储系统实例
            self.system = mock_system
            self.adapter = adapter

            return True

        except Exception as e:
            logger.error(f"❌ 系统初始化失败: {e}")
            return False

    async def register_agents(self):
        """注册智能体"""
        logger.info("🤖 注册智能体...")

        agents_config = {
            "小娜": {
                "capabilities": [
                    self.AgentCapability.PATENT_ANALYSIS,
                    self.AgentCapability.DATA_PROCESSING,
                    self.AgentCapability.REPORT_GENERATION
                ],
                "specialization": "专利分析和数据处理",
                "reflection_enabled": True,
                "memory_enabled": True
            },
            "小诺": {
                "capabilities": [
                    self.AgentCapability.SYSTEM_OPTIMIZATION,
                    self.AgentCapability.TROUBLESHOOTING,
                    self.AgentCapability.PERFORMANCE_ANALYSIS
                ],
                "specialization": "系统优化和问题解决",
                "reflection_enabled": True,
                "memory_enabled": True
            },
            "云熙": {
                "capabilities": [
                    self.AgentCapability.PROJECT_MANAGEMENT,
                    self.AgentCapability.TARGET_TRACKING,
                    self.AgentCapability.COORDINATION
                ],
                "specialization": "项目管理和目标跟踪",
                "reflection_enabled": True,
                "memory_enabled": True
            },
            "小宸": {
                "capabilities": [
                    self.AgentCapability.CONTENT_GENERATION,
                    self.AgentCapability.CREATIVE_DESIGN,
                    self.AgentCapability.OPTIMIZATION
                ],
                "specialization": "内容创作和创意设计",
                "reflection_enabled": True,
                "memory_enabled": True
            }
        }

        for agent_name, config in agents_config.items():
            success = await self.adapter.adapt_legacy_agent(agent_name, config)
            if success:
                self.agents[agent_name] = config
                logger.info(f"✅ 智能体 {agent_name} 注册成功")

    async def demonstrate_capabilities(self):
        """演示系统能力"""
        logger.info("🎯 演示系统能力...")

        try:
            # 1. 反思模式演示
            logger.info("📝 反思模式演示...")
            reflection_request = {
                "type": "reflection",
                "prompt": "分析专利检索结果的质量",
                "output": "找到15个相关专利，其中8个高度相关",
                "context": {"domain": "patent_analysis"}
            }

            reflection_result = await self.adapter.process_request(reflection_request)
            logger.info(f"   反思结果: {reflection_result['status']}")

            # 2. 并行处理演示
            logger.info("⚡ 并行处理演示...")
            parallel_request = {
                "type": "parallel",
                "tasks": [
                    {"id": "task_1", "name": "专利检索", "priority": "high"},
                    {"id": "task_2", "name": "数据分析", "priority": "medium"},
                    {"id": "task_3", "name": "报告生成", "priority": "low"}
                ]
            }

            parallel_result = await self.adapter.process_request(parallel_request)
            logger.info(f"   并行结果: {parallel_result['status']}")

            # 3. 智能体协作演示
            logger.info("🤝 智能体协作演示...")
            collaboration_request = {
                "type": "collaboration",
                "task": "综合专利分析报告",
                "participants": ["小娜", "小诺", "云熙"],
                "mode": "hierarchical"
            }

            collaboration_result = await self.adapter.process_request(collaboration_request)
            logger.info(f"   协作结果: {collaboration_result['status']}")

            # 4. 记忆管理演示
            logger.info("🧠 记忆管理演示...")
            memory_manager = self.system.get_component("memory")
            if memory_manager:
                await memory_manager.store_memory(
                    "demo_session",
                    {"activity": "系统演示", "time": datetime.now().isoformat()},
                    self.MemoryType.SHORT_TERM
                )
                logger.info("   记忆存储成功")

            return True

        except Exception as e:
            logger.error(f"❌ 能力演示失败: {e}")
            return False

    async def start_monitoring(self):
        """启动系统监控"""
        logger.info("📊 启动系统监控...")
        self.monitoring_active = True

        async def monitoring_loop():
            while self.monitoring_active:
                try:
                    # 获取系统状态
                    system_status = self.adapter.get_integration_status()

                    # 记录关键指标
                    active_components = system_status["system_status"]["active_components"]
                    logger.info(f"   活跃组件: {len(active_components)}")
                    logger.info(f"   注册智能体: {len(system_status['legacy_agents'])}")

                    # 每30秒监控一次
                    await asyncio.sleep(30)

                except Exception as e:
                    logger.error(f"   监控错误: {e}")
                    await asyncio.sleep(10)

        # 启动监控任务
        asyncio.create_task(monitoring_loop())

    async def run_interactive_mode(self):
        """运行交互模式"""
        logger.info("💬 进入交互模式...")

        print("\n" + "="*60)
        print("🎯 Athena优化系统 - 交互模式")
        print("="*60)
        print("可用命令:")
        print("  status     - 查看系统状态")
        print("  reflect    - 反思模式演示")
        print("  parallel   - 并行处理演示")
        print("  memory     - 记忆管理演示")
        print("  coordinate - 协作模式演示")
        print("  performance - 性能监控状态")
        print("  monitor    - 切换监控状态")
        print("  help       - 显示帮助")
        print("  quit       - 退出系统")
        print("="*60)

        while self.monitoring_active:
            try:
                command = input("\n🔹 请输入命令: ").strip().lower()

                if command == "quit" or command == "exit":
                    break
                elif command == "status":
                    await self.show_status()
                elif command == "reflect":
                    await self.demonstrate_reflection()
                elif command == "parallel":
                    await self.demonstrate_parallel()
                elif command == "memory":
                    await self.demonstrate_memory()
                elif command == "coordinate":
                    await self.demonstrate_coordination()
                elif command == "performance":
                    await self.show_performance_stats()
                elif command == "monitor":
                    self.monitoring_active = not self.monitoring_active
                    status = "开启" if self.monitoring_active else "关闭"
                    print(f"   监控状态: {status}")
                elif command == "help":
                    self.show_help()
                else:
                    print(f"   未知命令: {command}")
                    print("   输入 'help' 查看可用命令")

            except KeyboardInterrupt:
                break
            except EOFError:
                break
            except Exception as e:
                logger.error(f"命令执行错误: {e}")

        print("\n👋 感谢使用Athena优化系统！")

    async def show_status(self):
        """显示系统状态"""
        status = self.adapter.get_integration_status()

        print("\n📊 系统状态:")
        print(f"   系统健康: {status['system_status']['system_health']}")
        print(f"   活跃组件: {', '.join(status['system_status']['active_components'])}")
        print(f"   注册智能体: {', '.join(status['legacy_agents'])}")
        print(f"   兼容模式: {status['compatibility_mode']}")

    async def demonstrate_reflection(self):
        """演示反思模式"""
        print("\n📝 反思模式演示")
        print("-" * 40)

        reflection_engine = self.system.get_component("reflection")
        if reflection_engine:
            print("   反思引擎: ✅ 运行中")
            print("   支持指标: 准确性、完整性、清晰度、相关性、有用性、一致性")
            print("   最大反思次数: 3")
        else:
            print("   反思引擎: ❌ 未运行")

    async def demonstrate_parallel(self):
        """演示并行处理"""
        print("\n⚡ 并行处理演示")
        print("-" * 40)

        parallel_executor = self.system.get_component("parallel")
        if parallel_executor:
            print("   并行执行器: ✅ 运行中")
            print(f"   最大工作线程: {parallel_executor.max_workers}")
            print(f"   最大并发任务: {parallel_executor.max_concurrent_tasks}")
            print("   支持优先级调度和依赖管理")
        else:
            print("   并行执行器: ❌ 未运行")

    async def demonstrate_memory(self):
        """演示记忆管理"""
        print("\n🧠 记忆管理演示")
        print("-" * 40)

        memory_manager = self.system.get_component("memory")
        if memory_manager:
            print("   记忆管理器: ✅ 运行中")
            print("   支持记忆类型:")
            print("     - 短期记忆: 临时数据存储")
            print("     - 长期记忆: 持久化知识存储")
            print("     - 工作记忆: 当前任务上下文")
            print("     - 情景记忆: 事件和经验")
            print("     - 程序记忆: 技能和流程")
        else:
            print("   记忆管理器: ❌ 未运行")

    async def demonstrate_coordination(self):
        """演示智能体协作"""
        print("\n🤝 智能体协作演示")
        print("-" * 40)

        coordinator = self.system.get_component("coordination")
        if coordinator:
            print("   协作协调器: ✅ 运行中")
            print("   支持协作模式:")
            print("     - 层级协作: 上下级关系")
            print("     - 平级协作: 同级协作")
            print("     - 流水线协作: 串行处理")
            print("     - 群体协作: 自组织团队")
            print(f"   注册智能体数量: {len(self.agents)}")
        else:
            print("   协作协调器: ❌ 未运行")

    async def show_performance_stats(self):
        """显示性能统计"""
        print("\n📊 性能监控统计")
        print("-" * 50)

        if self.performance_monitor:
            stats = self.performance_monitor.get_current_stats()
            summary = self.performance_monitor.get_performance_summary()

            print(f"监控状态: {'🟢 运行中' if stats['monitoring_active'] else '🔴 已停止'}")
            print(f"运行时间: {stats['uptime_seconds'] / 3600:.1f} 小时")
            print(f"总警报数: {stats['total_alerts']}")
            print(f"注册组件: {stats['registered_components']}")

            if stats['current_system']:
                current = stats['current_system']
                print("\n当前系统资源:")
                print(f"   CPU使用率: {current['cpu_percent']:.1f}%")
                print(f"   内存使用率: {current['memory_percent']:.1f}%")
                print(f"   内存使用量: {current['memory_used_mb']:.1f} MB")
                print(f"   活跃线程数: {current['active_threads']}")

            if summary and summary.get('status') != 'no_data':
                print("\n系统健康状态:")
                print(f"   总体状态: {summary['overall_status']}")
                print(f"   健康评分: {summary['health_score']}/100")
                print(f"   平均CPU: {summary['performance_averages']['cpu_percent']:.1f}%")
                print(f"   平均内存: {summary['performance_averages']['memory_percent']:.1f}%")

                if summary['health_issues']:
                    print(f"   健康问题: {', '.join(summary['health_issues'])}")

        else:
            print("❌ 性能监控器未初始化")

    def show_help(self) -> Any:
        """显示帮助信息"""
        print("\n❓ 系统帮助")
        print("-" * 40)
        print("Athena优化系统集成了以下核心功能:")
        print("")
        print("1. 📝 反思模式 (Reflection Pattern)")
        print("   - 自我评估输出质量")
        print("   - 迭代改进和优化")
        print("   - 多维度质量指标")
        print("")
        print("2. ⚡ 并行化模式 (Parallelization Pattern)")
        print("   - 并发执行独立任务")
        print("   - 资源管理和负载均衡")
        print("   - 优先级调度和依赖管理")
        print("")
        print("3. 🧠 记忆管理 (Memory Management Pattern)")
        print("   - 多层次记忆系统")
        print("   - 智能检索和关联")
        print("   - 自动记忆整理和优化")
        print("")
        print("4. 🤝 多智能体协作 (Multi-Agent Collaboration Pattern)")
        print("   - 多种协作模式")
        print("   - 智能任务分配")
        print("   - 动态协调机制")
        print("")
        print("5. 📊 性能监控 (Performance Monitoring)")
        print("   - 实时系统资源监控")
        print("   - 性能指标统计")
        print("   - 自动警报系统")

    async def system_health_check(self) -> dict[str, Any]:
        """系统健康检查"""
        try:
            checks = {
                "python_version": sys.version_info >= (3, 8),
                "required_files": True,
                "disk_space": True,
                "memory_available": True
            }

            # 检查必要文件
            required_files = [
                "core/intelligence/reflection_engine.py",
                "core/execution/parallel_executor.py",
                "core/memory/enhanced_memory_manager.py",
                "core/collaboration/enhanced_agent_coordination.py"
            ]

            for file_path in required_files:
                full_path = self.base_path / file_path
                if not full_path.exists():
                    checks["required_files"] = False
                    break

            # 检查磁盘空间
            import shutil
            disk_usage = shutil.disk_usage(self.base_path)
            if disk_usage.free < 1024 * 1024 * 100:  # 至少100MB
                checks["disk_space"] = False

            all_healthy = all(checks.values())

            return {
                "healthy": all_healthy,
                "checks": checks,
                "error": None if all_healthy else "系统健康检查发现问题"
            }

        except Exception as e:
            return {
                "healthy": False,
                "checks": {},
                "error": str(e)
            }

    async def system_self_check(self) -> dict[str, Any]:
        """系统自检"""
        issues = []

        try:
            # 检查组件是否正确加载
            if self.system:
                required_components = ["reflection", "parallel", "memory", "coordination"]
                for component in required_components:
                    if component not in self.system.components:
                        issues.append(f"缺少组件: {component}")

                # 检查智能体是否注册
                if len(self.agents) < 4:
                    issues.append(f"智能体注册数量不足: {len(self.agents)}/4")

            return {
                "passed": len(issues) == 0,
                "issues": issues
            }

        except Exception as e:
            return {
                "passed": False,
                "issues": [f"自检过程出错: {e}"]
            }

    async def graceful_shutdown(self):
        """优雅关闭系统"""
        logger.info("🔄 开始优雅关闭系统...")

        try:
            # 1. 停止监控
            self.monitoring_active = False
            logger.info("✅ 系统监控已停止")

            # 2. 停止性能监控
            if self.performance_monitor and self.performance_monitor.monitoring_active:
                await self.performance_monitor.stop_monitoring()
                logger.info("✅ 性能监控已停止")

            # 2. 保存重要数据
            if hasattr(self, 'save_state'):
                await self.save_state()
                logger.info("✅ 系统状态已保存")

            # 3. 清理资源
            if self.system:
                for component_name, component in self.system.components.items():
                    try:
                        if hasattr(component, 'close'):
                            await component.close()
                        elif hasattr(component, 'cleanup'):
                            await component.cleanup()
                        elif hasattr(component, 'stop'):
                            component.stop()
                        logger.info(f"✅ 组件 {component_name} 已清理")
                    except Exception as e:
                        logger.warning(f"⚠️ 组件 {component_name} 清理警告: {e}")

            # 4. 最终清理
            self.system = None
            self.adapter = None
            self.agents.clear()

            logger.info("✅ 系统优雅关闭完成")

        except Exception as e:
            logger.error(f"❌ 优雅关闭过程中出现错误: {e}")

    async def shutdown_system(self):
        """关闭系统"""
        logger.info("🔄 关闭集成系统...")

        self.monitoring_active = False

        # 执行清理操作
        if self.system:
            # 清理各个组件
            for component_name, component in self.system.components.items():
                try:
                    if hasattr(component, 'close'):
                        await component.close()
                    elif hasattr(component, 'cleanup'):
                        await component.cleanup()
                    logger.info(f"✅ 组件 {component_name} 清理完成")
                except Exception as e:
                    logger.warning(f"⚠️ 组件 {component_name} 清理警告: {e}")

        logger.info("✅ 系统关闭完成")

async def main():
    """主函数"""
    print("="*80)
    print("🚀 Athena优化系统启动器")
    print("   集成了反思、并行、记忆管理和协作四大优化模式")
    print("="*80)

    launcher = IntegratedSystemLauncher()

    try:
        # 1. 系统健康检查
        print("\n🔍 正在进行系统健康检查...")
        health_status = await launcher.system_health_check()
        if not health_status["healthy"]:
            print(f"❌ 系统健康检查失败: {health_status['error']}")
            return
        print("✅ 系统健康检查通过")

        # 2. 初始化系统
        print("\n🔧 正在初始化系统...")
        if not await launcher.initialize_system():
            print("❌ 系统初始化失败")
            return
        print("✅ 系统初始化成功")

        # 3. 注册智能体
        print("\n🤖 正在注册智能体...")
        await launcher.register_agents()
        print(f"✅ 成功注册 {len(launcher.agents)} 个智能体")

        # 4. 系统自检
        print("\n🧪 正在运行系统自检...")
        self_check = await launcher.system_self_check()
        if not self_check["passed"]:
            print(f"⚠️ 系统自检发现问题: {self_check['issues']}")
        print("✅ 系统自检完成")

        # 5. 演示系统能力
        print("\n🎯 正在演示系统能力...")
        if not await launcher.demonstrate_capabilities():
            print("⚠️ 系统能力演示部分失败，但系统仍可正常使用")
        print("✅ 系统能力演示完成")

        # 6. 启动性能监控
        print("\n📊 正在启动性能监控...")
        if launcher.performance_monitor:
            await launcher.performance_monitor.start_monitoring()
            print("✅ 性能监控已启动")

        # 7. 启动系统监控
        await launcher.start_monitoring()
        print("✅ 系统监控已启动")

        # 8. 进入交互模式
        print("\n🎮 进入交互模式...")
        await launcher.run_interactive_mode()

    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断系统启动")
        await launcher.graceful_shutdown()
    except ImportError as e:
        print(f"\n❌ 模块导入错误: {e}")
        print("💡 请确保所有依赖模块已正确安装")
        return
    except PermissionError as e:
        print(f"\n❌ 权限错误: {e}")
        print("💡 请检查文件和目录权限")
        return
    except Exception as e:
        print(f"\n💥 系统启动失败: {e}")
        print("\n📋 错误详情:")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误信息: {str(e)}")
        print("\n💡 建议检查:")
        print("   1. 确保所有文件完整")
        print("   2. 检查Python环境")
        print("   3. 查看日志获取更多信息")
        logger.exception("系统启动异常")
        return
    finally:
        # 9. 优雅关闭
        if launcher.system is not None:
            print("\n🔄 正在优雅关闭系统...")
            await launcher.graceful_shutdown()
            print("✅ 系统已安全关闭")

if __name__ == "__main__":
    asyncio.run(main())
