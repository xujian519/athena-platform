#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动小娜增强系统
Start Xiaona Enhanced System

一键启动小娜的增强版本，集成人机协作、反思引擎和学习系统

作者: 徐健 (xujian519@gmail.com)
创建时间: 2025-12-17
版本: v2.0.0
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import json
import logging
import sys
import argparse
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.cognition.xiaona_integrated_enhanced_system import (
    XiaonaIntegratedEnhancedSystem,
    EnhancementConfig
)
from core.collaboration.human_ai_collaboration_framework import HumanExpert, TaskType

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class XiaonaEnhancedLauncher:
    """小娜增强系统启动器"""

    def __init__(self, config_file: str = None):
        self.config_file = config_file
        self.enhanced_system = None
        self.start_time = datetime.now()

    def print_startup_banner(self) -> Any:
        """打印启动横幅"""
        print("\n" + "="*80)
        print("⚖️" + " "*25 + "小娜增强系统启动器" + " "*25 + "⚖️")
        print("="*80)
        print(f"💖 启动时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 系统版本: v2.0.0 Integrated")
        print(f"👩‍⚖️ 控制者: 小娜·天秤女神 (专利法律专家)")
        print(f"📄 启动脚本: {__file__}")
        print("="*80)

    def load_configuration(self) -> EnhancementConfig:
        """加载配置"""
        config = EnhancementConfig()

        if self.config_file and Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                # 更新配置
                for key, value in config_data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)

                print(f"✅ 配置文件已加载: {self.config_file}")
            except Exception as e:
                print(f"⚠️ 加载配置文件失败: {e}, 使用默认配置")
        else:
            print("✅ 使用默认配置")

        return config

    async def initialize_system(self, config: EnhancementConfig):
        """初始化系统"""
        print("\n🚀 正在初始化小娜增强系统...")

        try:
            # 创建增强系统
            self.enhanced_system = XiaonaIntegratedEnhancedSystem(
                config=config,
                storage_path="/tmp/xiaona_enhanced_system"
            )

            print("✅ 增强系统初始化完成")
            return True

        except Exception as e:
            print(f"❌ 系统初始化失败: {e}")
            return False

    async def setup_collaboration_experts(self):
        """设置协作专家"""
        if not self.enhanced_system.collaboration_engine:
            return

        print("\n👥 正在设置协作专家...")

        # 注册专利专家
        patent_expert = HumanExpert(
            expert_id="dr_patent_expert",
            name="专利专家张博士",
            title="高级专利分析师",
            expertise=["专利分析", "专利检索", "新颖性判断", "创造性评估"],
            availability={
                "working_hours": {"start": 9, "end": 18},
                "available_days": [0, 1, 2, 3, 4]
            },
            contact_info={
                "email": "zhang@patent_expert.com",
                "phone": "+86-138-xxxx-xxxx"
            }
        )

        # 注册法律专家
        legal_expert = HumanExpert(
            expert_id="dr_legal_expert",
            name="法律专家李教授",
            title="知识产权法律顾问",
            expertise=["专利法", "商标法", "著作权法", "法律研究"],
            availability={
                "working_hours": {"start": 9, "end": 18},
                "available_days": [0, 1, 2, 3, 4, 5]
            },
            contact_info={
                "email": "li@legal_expert.com",
                "phone": "+86-139-xxxx-xxxx"
            }
        )

        # 注册专家
        self.enhanced_system.collaboration_engine.register_expert(patent_expert)
        self.enhanced_system.collaboration_engine.register_expert(legal_expert)

        print("✅ 协作专家设置完成")

    async def run_demonstration(self):
        """运行演示"""
        print("\n🎬 运行系统演示...")

        demo_tasks = [
            {
                "task_id": "demo_patent_001",
                "task_input": "分析专利CN202300123456A的新颖性和创造性",
                "task_type": "patent_analysis",
                "context": {
                    "patent_number": "CN202300123456A",
                    "technical_field": "人工智能",
                    "client_requirements": ["快速分析", "准确判断"]
                }
            },
            {
                "task_id": "demo_legal_001",
                "task_input": "研究软件专利的保护范围和侵权判定标准",
                "task_type": "legal_research",
                "context": {
                    "legal_domain": "专利法",
                    "research_focus": "软件保护",
                    "jurisdiction": "中国"
                }
            }
        ]

        for i, task in enumerate(demo_tasks, 1):
            print(f"\n📋 演示任务 {i}/{len(demo_tasks)}: {task['task_id']}")

            try:
                result = await self.enhanced_system.process_legal_task(**task)

                print(f"✅ 任务完成")
                print(f"   应用的增强: {', '.join(result.enhancement_applied)}")
                print(f"   处理时间: {result.processing_time:.2f}秒")
                print(f"   最终置信度: {result.final_confidence:.2f}")

                if result.reflection_result:
                    print(f"   反思评分: {result.reflection_result.overall_score:.2f}")

            except Exception as e:
                print(f"❌ 任务失败: {e}")

    async def interactive_mode(self):
        """交互模式"""
        print("\n💬 进入交互模式 (输入 'quit' 退出)")
        print("-" * 60)

        while True:
            try:
                # 获取用户输入
                user_input = input("\n请输入您的法律分析需求: ").strip()

                if user_input.lower() in ['quit', 'exit', '退出']:
                    break

                if not user_input:
                    print("⚠️ 请输入有效内容")
                    continue

                # 分析输入类型
                task_type = "patent_analysis" if "专利" in user_input else "legal_research"

                print(f"🔄 正在处理您的请求...")

                # 处理任务
                result = await self.enhanced_system.process_legal_task(
                    task_id=f"interactive_{int(datetime.now().timestamp())}",
                    task_input=user_input,
                    task_type=task_type
                )

                # 显示结果
                print(f"\n📊 处理结果:")
                print(f"   处理时间: {result.processing_time:.2f}秒")
                print(f"   置信度: {result.final_confidence:.2f}")
                print(f"   应用增强: {', '.join(result.enhancement_applied)}")

                if result.reflection_result and result.reflection_result.should_refine:
                    print(f"   💡 建议: {', '.join(result.reflection_result.recommendations[:2])}")

                print(f"\n📝 分析结果:")
                output = result.enhanced_output or result.initial_output
                print(output)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ 处理失败: {e}")

        print("\n👋 退出交互模式")

    def print_system_status(self) -> Any:
        """打印系统状态"""
        if not self.enhanced_system:
            return

        print("\n📊 系统状态:")
        print("-" * 60)

        status = self.enhanced_system.get_system_status()

        print(f"✅ 启用模块:")
        for module, enabled in status["enabled_modules"].items():
            status_icon = "✅" if enabled else "❌"
            print(f"   {status_icon} {module}")

        print(f"\n📈 处理统计:")
        stats = status["processing_statistics"]
        print(f"   总处理任务: {stats['total_processed']}")
        print(f"   应用反思: {stats['reflection_applied']}")
        print(f"   触发协作: {stats['collaboration_triggered']}")
        print(f"   学习事件: {stats['learning_events']}")
        print(f"   平均处理时间: {stats['average_processing_time']:.2f}秒")
        print(f"   成功率: {stats['success_rate']:.2%}")

        if "reflection_engine" in status:
            print(f"\n🔍 反思引擎:")
            ref_stats = status["reflection_engine"]
            print(f"   总反思次数: {ref_stats['total_reflections']}")
            print(f"   平均评分: {ref_stats['average_score']:.2f}")
            print(f"   改进率: {ref_stats['improvement_rate']:.2%}")

        if "collaboration_engine" in status:
            print(f"\n👥 协作引擎:")
            collab_stats = status["collaboration_engine"]
            print(f"   活跃会话: {collab_stats['active_sessions']}")
            print(f"   完成会话: {collab_stats['completed_sessions']}")
            print(f"   注册专家: {collab_stats['registered_experts']}")

        if "learning_system" in status:
            print(f"\n🧠 学习系统:")
            learn_stats = status["learning_system"]
            print(f"   知识条目: {learn_stats['knowledge_items']}")
            print(f"   学习事件: {learn_stats['learning_events']}")

        print(f"\n⏱️ 运行时间: {datetime.now() - self.start_time}")

    async def run(self, args):
        """运行启动器"""
        self.print_startup_banner()

        # 加载配置
        config = self.load_configuration()

        # 初始化系统
        if not await self.initialize_system(config):
            return 1

        # 设置协作专家
        if config.enable_collaboration:
            await self.setup_collaboration_experts()

        # 根据参数执行相应操作
        if args.demo:
            await self.run_demonstration()
        elif args.interactive:
            await self.interactive_mode()
        else:
            # 默认运行演示
            await self.run_demonstration()

        # 显示系统状态
        self.print_system_status()

        # 关闭系统
        await self.enhanced_system.shutdown()
        print("\n✅ 小娜增强系统已正常关闭")

        return 0

def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="小娜增强系统启动器")
    parser.add_argument("--config", "-c", help="配置文件路径")
    parser.add_argument("--demo", "-d", action="store_true", help="运行演示")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互模式")
    parser.add_argument("--version", "-v", action="version", version="v2.0.0")

    args = parser.parse_args()

    # 创建启动器并运行
    launcher = XiaonaEnhancedLauncher(args.config)

    try:
        exit_code = asyncio.run(launcher.run(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ 收到中断信号，正在关闭系统...")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 系统运行出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()