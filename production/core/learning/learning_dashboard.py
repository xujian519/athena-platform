#!/usr/bin/env python3
"""
学习引擎监控仪表板
Learning Engine Monitoring Dashboard

实时监控Athena平台所有学习引擎的性能和效果:
- 实时性能指标
- 学习进度追踪
- 优化效果分析
- 可视化报表

作者: Athena AI Team
版本: 1.0.0
创建: 2026-01-29
"""

from __future__ import annotations
import asyncio
import json

# 添加项目路径
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.logging_config import setup_logging

logger = setup_logging()


# =============================================================================
# 学习引擎监控仪表板
# =============================================================================

class LearningDashboard:
    """
    学习引擎监控仪表板

    聚合所有模块的学习数据，提供统一的监控视图
    """

    def __init__(self):
        """初始化监控仪表板"""
        self.modules = {}
        self.metrics_history = []
        self.alerts = []

        logger.info("📊 学习引擎监控仪表板初始化完成")

    def register_module(
        self,
        module_name: str,
        module_instance: Any,
    ):
        """
        注册学习模块

        Args:
            module_name: 模块名称
            module_instance: 模块实例
        """
        self.modules[module_name] = module_instance
        logger.info(f"📈 已注册学习模块: {module_name}")

    async def get_overall_metrics(self) -> dict[str, Any]:
        """
        获取整体指标

        Returns:
            整体性能指标
        """
        overall = {
            "timestamp": datetime.now().isoformat(),
            "total_modules": len(self.modules),
            "active_modules": 0,
            "total_experiences": 0,
            "overall_accuracy": 0.0,
            "overall_reward": 0.0,
            "modules": {},
        }

        total_reward = 0.0
        total_accuracy = 0.0
        module_count = 0

        for module_name, module in self.modules.items():
            try:
                # 获取模块统计
                if hasattr(module, 'get_learning_statistics'):
                    stats = module.get_learning_statistics()
                    overall["modules"][module_name] = stats

                    # 累计指标
                    if "learning_stats" in stats:
                        learning_stats = stats["learning_stats"]
                        overall["total_experiences"] += learning_stats.get("total_experiences", 0)
                        total_accuracy += learning_stats.get("accuracy", 0.0)
                        module_count += 1
                        overall["active_modules"] += 1

                    if "performance_metrics" in stats:
                        perf = stats["performance_metrics"]
                        if "avg_reward" in perf:
                            total_reward += perf["avg_reward"]

            except Exception as e:
                logger.warning(f"⚠️ 获取模块 {module_name} 指标失败: {e}")
                overall["modules"][module_name] = {"error": str(e)}

        # 计算整体指标
        if module_count > 0:
            overall["overall_accuracy"] = total_accuracy / module_count
            overall["overall_reward"] = total_reward / module_count

        # 记录历史
        self.metrics_history.append(overall)

        # 保留最近100条记录
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)

        return overall

    async def get_module_comparison(self) -> dict[str, Any]:
        """
        获取模块对比

        Returns:
            模块性能对比
        """
        comparison = {
            "timestamp": datetime.now().isoformat(),
            "modules": [],
        }

        for module_name, module in self.modules.items():
            try:
                if hasattr(module, 'get_learning_statistics'):
                    stats = module.get_learning_statistics()

                    # 提取关键指标
                    module_info = {
                        "name": module_name,
                        "experiences": 0,
                        "accuracy": 0.0,
                        "avg_reward": 0.0,
                    }

                    if "learning_stats" in stats:
                        module_info["experiences"] = stats["learning_stats"].get("total_experiences", 0)
                        module_info["accuracy"] = stats["learning_stats"].get("accuracy", 0.0)

                    if "performance_metrics" in stats:
                        module_info["avg_reward"] = stats["performance_metrics"].get("avg_reward", 0.0)

                    comparison["modules"].append(module_info)

            except Exception as e:
                logger.warning(f"⚠️ 获取模块 {module_name} 对比失败: {e}")

        # 按平均奖励排序
        comparison["modules"].sort(key=lambda x: x["avg_reward"], reverse=True)

        return comparison

    async def get_learning_progress(
        self,
        hours: int = 24,
    ) -> dict[str, Any]:
        """
        获取学习进度

        Args:
            hours: 统计最近多少小时的数据

        Returns:
            学习进度报告
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # 筛选最近的数据
        recent_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m["timestamp"]) > cutoff_time
        ]

        if not recent_metrics:
            return {
                "period_hours": hours,
                "data_points": 0,
                "message": "暂无数据",
            }

        # 计算趋势
        first = recent_metrics[0]
        last = recent_metrics[-1]

        progress = {
            "period_hours": hours,
            "data_points": len(recent_metrics),
            "start_time": first["timestamp"],
            "end_time": last["timestamp"],
            "improvement": {
                "accuracy": last["overall_accuracy"] - first["overall_accuracy"],
                "reward": last["overall_reward"] - first["overall_reward"],
            },
            "current": {
                "accuracy": last["overall_accuracy"],
                "reward": last["overall_reward"],
                "total_experiences": last["total_experiences"],
            },
        }

        return progress

    def generate_report(
        self,
        format: str = "json",
    ) -> str:
        """
        生成报告

        Args:
            format: 报告格式 (json, markdown)

        Returns:
            报告内容
        """
        # 获取最新指标
        latest_metrics = self.metrics_history[-1] if self.metrics_history else {}

        if format == "json":
            report = {
                "report_type": "learning_engine_dashboard",
                "generated_at": datetime.now().isoformat(),
                "summary": latest_metrics,
            }
            return json.dumps(report, ensure_ascii=False, indent=2)

        elif format == "markdown":
            md = f"""# 📊 学习引擎监控报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📈 整体指标

- **活跃模块**: {latest_metrics.get('active_modules', 0)} / {latest_metrics.get('total_modules', 0)}
- **总经验数**: {latest_metrics.get('total_experiences', 0)}
- **整体准确率**: {latest_metrics.get('overall_accuracy', 0.0):.1%}
- **整体奖励**: {latest_metrics.get('overall_reward', 0.0):.3f}

## 📊 各模块指标

"""

            for module_name, stats in latest_metrics.get("modules", {}).items():
                if "error" not in stats:
                    md += f"### {module_name}\n\n"
                    if "learning_stats" in stats:
                        ls = stats["learning_stats"]
                        md += f"- 经验数: {ls.get('total_experiences', 0)}\n"
                        md += f"- 准确率: {ls.get('accuracy', 0.0):.1%}\n"
                    md += "\n"

            return md

        else:
            return "不支持的报告格式"

    async def export_dashboard_data(
        self,
        filepath: str | None = None,
    ) -> str:
        """
        导出仪表板数据

        Args:
            filepath: 导出文件路径

        Returns:
            导出文件的路径
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"data/learning_dashboard_{timestamp}.json"

        # 确保目录存在
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        # 获取完整数据
        data = {
            "export_time": datetime.now().isoformat(),
            "overall_metrics": await self.get_overall_metrics(),
            "module_comparison": await self.get_module_comparison(),
            "learning_progress": await self.get_learning_progress(hours=24),
            "metrics_history": self.metrics_history[-10:],  # 最近10条
        }

        # 导出
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"📤 仪表板数据已导出: {filepath}")

        return filepath


# =============================================================================
# 全局仪表板实例
# =============================================================================

_dashboard: LearningDashboard | None = None


def get_learning_dashboard() -> LearningDashboard:
    """
    获取全局学习仪表板实例

    Returns:
        LearningDashboard: 学习仪表板实例
    """
    global _dashboard

    if _dashboard is None:
        _dashboard = LearningDashboard()

    return _dashboard


# =============================================================================
# 测试代码
# =============================================================================
if __name__ == "__main__":
    async def test_learning_dashboard():
        """测试学习监控仪表板"""
        print("=" * 80)
        print("📊 测试学习引擎监控仪表板")
        print("=" * 80)

        # 创建仪表板
        dashboard = get_learning_dashboard()

        # 模拟注册模块
        class MockModule:
            def __init__(self, name):
                self.name = name

            def get_learning_statistics(self):
                return {
                    "learning_stats": {
                        "total_experiences": 100,
                        "accuracy": 0.85,
                    },
                    "performance_metrics": {
                        "avg_reward": 0.75,
                    },
                }

        dashboard.register_module("agent", MockModule("Agent"))
        dashboard.register_module("rag", MockModule("RAG"))
        dashboard.register_module("tool", MockModule("Tool"))

        # 获取整体指标
        print("\n📈 整体指标:")
        print("-" * 80)
        overall = await dashboard.get_overall_metrics()
        print(f"活跃模块: {overall['active_modules']} / {overall['total_modules']}")
        print(f"总经验数: {overall['total_experiences']}")
        print(f"整体准确率: {overall['overall_accuracy']:.1%}")
        print(f"整体奖励: {overall['overall_reward']:.3f}")

        # 获取模块对比
        print("\n🔍 模块对比:")
        print("-" * 80)
        comparison = await dashboard.get_module_comparison()
        for module in comparison["modules"]:
            print(f"\n{module['name']}:")
            print(f"  经验数: {module['experiences']}")
            print(f"  准确率: {module['accuracy']:.1%}")
            print(f"  平均奖励: {module['avg_reward']:.3f}")

        # 生成报告
        print("\n📄 生成报告:")
        print("-" * 80)
        report = dashboard.generate_report(format="markdown")
        print(report)

        # 导出数据
        print("\n📤 导出数据...")
        export_path = await dashboard.export_dashboard_data()
        print(f"文件: {export_path}")

        print("\n" + "=" * 80)
        print("✅ 测试完成!")
        print("=" * 80)

    asyncio.run(test_learning_dashboard())
