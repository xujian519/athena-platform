"""
小诺伦理约束补丁
Xiaonuo Ethics Constraint Patch

为小诺主程序添加伦理约束,防止幻觉并确保合规行为
"""

from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Any

# 添加伦理模块路径 - 使用环境变量或智能检测
if "ATHENA_PROJECT_ROOT" in os.environ:
    # 优先使用环境变量
    project_root = Path(os.environ["ATHENA_PROJECT_ROOT"])
elif "PYTHONPATH" in os.environ:
    # 从PYTHONPATH中查找
    for path in os.environ["PYTHONPATH"].split(":"):
        if path and Path(path).name == "Athena工作平台":
            project_root = Path(path)
            break
    else:
        # 回退到相对路径
        project_root = Path(__file__).parent.parent.parent
else:
    # 回退到相对路径
    project_root = Path(__file__).parent.parent.parent

# 确保项目根目录在sys.path中
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.ethics import (
    AthenaConstitution,
    ConstraintEnforcer,
    EthicalConstraint,
    EthicsEvaluator,
    EthicsMonitor,
    WittgensteinGuard,
    setup_logging_alert_handler,
)


class XiaonuoEthicsWrapper:
    """小诺伦理包装器

    为小诺主程序添加透明的伦理约束层
    """

    def __init__(self, xiaonuo_instance):
        """初始化伦理包装器

        Args:
            xiaonuo_instance: 小诺主程序实例
        """
        self.xiaonuo = xiaonuo_instance

        # 初始化伦理组件
        print("🛡️ 初始化小诺伦理约束系统...")

        self.constitution = AthenaConstitution()
        self.wittgenstein_guard = WittgensteinGuard()
        self.ethics_evaluator = EthicsEvaluator(
            constitution=self.constitution, wittgenstein_guard=self.wittgenstein_guard
        )
        self.ethics_constraint = EthicalConstraint(
            self.ethics_evaluator,
            auto_block_critical=True,
            auto_negotiate_uncertain=True,
            auto_escalate_high_severity=True,
        )
        self.ethics_enforcer = ConstraintEnforcer(self.ethics_constraint)
        self.ethics_monitor = EthicsMonitor(self.ethics_evaluator)

        # 设置告警
        log_file = Path("/Users/xujian/Athena工作平台/logs/xiaonuo_ethics_alerts.log")
        setup_logging_alert_handler(self.ethics_monitor, str(log_file))

        print("✅ 小诺伦理约束系统已激活")
        self._print_ethics_summary()

    def _print_ethics_summary(self) -> Any:
        """打印伦理框架摘要"""
        summary = self.constitution.get_summary()
        print("\n📜 小诺伦理框架摘要:")
        print(f"  • 版本: {self.constitution.version}")
        print(f"  • 总原则数: {summary['total_principles']}")
        print(f"  • 启用原则: {summary['enabled_principles']}")
        print(f"  • 关键原则: {summary['critical_principles']}")
        print(f"  • 高优先级: {summary['high_principles']}")

        # 打印语言游戏
        guard_status = self.wittgenstein_guard.get_status()
        print("\n🎮 语言游戏:")
        print(f"  • 总游戏数: {guard_status['total_games']}")
        print(f"  • 启用游戏: {guard_status['enabled_games']}")
        for game in guard_status["games"]:
            status = "✅" if game["enabled"] else "❌"
            print(f"    {status} {game['name']} (领域: {game['domain']})")

    def wrap_method(self, method_name: str) -> Any:
        """包装方法以添加伦理检查

        Args:
            method_name: 要包装的方法名
        """
        original_method = getattr(self.xiaonuo, method_name, None)
        if original_method is None:
            raise AttributeError(f"小诺没有方法: {method_name}")

        def wrapped(*args, **kwargs) -> Any:
            # 提取上下文
            context = self._extract_context(method_name, args, kwargs)

            # 伦理检查
            result = self.ethics_enforcer.enforce_and_log(
                agent_id="xiaonuo", action=method_name, context=context
            )

            # 记录监控
            if (
                hasattr(self.ethics_evaluator, "evaluation_history")
                and self.ethics_evaluator.evaluation_history
            ):
                evaluation = self.ethics_evaluator.evaluation_history[-1]
                self.ethics_monitor.record_evaluation(evaluation)

            # 检查是否允许执行
            if not result.allowed:
                return self._handle_constraint_violation(result, context)

            # 允许执行,调用原方法
            return original_method(*args, **kwargs)

        # 替换方法
        setattr(self.xiaonuo, method_name, wrapped)

    def _extract_context(self, method_name: str, args: tuple, kwargs: dict) -> dict[str, Any]:
        """从方法调用中提取伦理上下文"""
        context = {"method": method_name, "agent_id": "xiaonuo"}

        # 提取常见的上下文参数
        if "query" in kwargs:
            context["query"] = kwargs["query"]
        if "question" in kwargs:
            context["query"] = kwargs["question"]
        if "confidence" in kwargs:
            context["confidence"] = kwargs["confidence"]
        if "domain" in kwargs:
            context["domain"] = kwargs["domain"]
            context["language_game"] = f"{kwargs['domain']}_conversation"

        # 从args中提取
        if args and len(args) > 0 and isinstance(args[0], str):
            context["query"] = args[0]

        return context

    def _handle_constraint_violation(self, result, context: dict[str, Any]) -> Any:
        """处理约束违规"""
        from core.ethics.constraints import ConstraintAction

        if result.action_taken == ConstraintAction.NEGOTIATE:
            # 协商:请求澄清
            query = context.get("query", "")
            guard_eval = self.wittgenstein_guard.evaluate_query(query)
            return self.wittgenstein_guard.suggest_negotiation(query, guard_eval)

        elif result.action_taken == ConstraintAction.ESCALATE:
            # 升级:转给专家
            target = result.escalation_target or "human_expert"
            return f"此请求需要升级给{target}处理。"

        else:  # BLOCK
            # 阻止:拒绝执行
            return result.message

    def get_ethics_report(self) -> dict[str, Any]:
        """获取伦理报告"""
        return {
            "constitution": self.constitution.get_summary(),
            "monitoring": self.ethics_monitor.generate_dashboard_data(),
            "enforcement": self.ethics_enforcer.get_enforcement_statistics(),
        }

    def print_ethics_status(self) -> Any:
        """打印伦理状态"""
        report = self.get_ethics_report()

        print("\n" + "=" * 60)
        print("📊 小诺伦理合规状态报告")
        print("=" * 60)

        # 监控数据
        monitoring = report["monitoring"]["summary"]
        print("\n📈 监控统计:")
        print(f"  • 总评估次数: {monitoring['total_evaluations']}")
        print(f"  • 合规率: {monitoring['compliance_rate']:.1%}")
        print(f"  • 违规率: {monitoring['violation_rate']:.1%}")
        print(f"  • 关键违规: {monitoring['critical_violations']}")
        print(f"  • 活跃告警: {monitoring['active_alerts']}")

        # 执行统计
        enforcement = report["enforcement"]
        print("\n⚖️ 执行统计:")
        print(f"  • 总执行次数: {enforcement['total']}")
        print(f"  • 允许: {enforcement['allowed']}")
        print(f"  • 阻止: {enforcement['blocked']}")
        print(f"  • 允许率: {enforcement['allow_rate']:.1%}")

        # 最近告警
        recent_alerts = report["monitoring"]["recent_alerts"]
        if recent_alerts:
            print("\n🚨 最近告警:")
            for alert in recent_alerts[:5]:
                print(f"  • [{alert['level']}] {alert['message']}")

        print("=" * 60 + "\n")


def patch_xiaonuo(xiaonuo_instance) -> None:
    """为小诺实例添加伦理约束

    Args:
        xiaonuo_instance: 小诺主程序实例

    Returns:
        XiaonuoEthicsWrapper: 伦理包装器实例
    """
    wrapper = XiaonuoEthicsWrapper(xiaonuo_instance)

    # 包装关键方法
    methods_to_wrap = [
        "process_query",
        "answer_question",
        "provide_advice",
        "search_information",
        "analyze_content",
    ]

    for method_name in methods_to_wrap:
        if hasattr(xiaonuo_instance, method_name):
            wrapper.wrap_method(method_name)
            print(f"✅ 已为 {method_name} 添加伦理约束")

    return wrapper


# 使用示例
if __name__ == "__main__":
    print("🧪 小诺伦理约束补丁测试\n")

    # 模拟小诺实例
    class MockXiaonuo:
        def process_query(self, query: str) -> str:
            return f"处理查询: {query}"

        def answer_question(self, question: str) -> str:
            return f"回答问题: {question}"

        def provide_advice(self, topic: str) -> str:
            return f"提供建议: {topic}"

    # 创建小诺实例
    xiaonuo = MockXiaonuo()

    # 应用伦理补丁
    wrapper = patch_xiaonuo(xiaonuo)

    print("\n" + "=" * 60)
    print("🧪 测试场景")
    print("=" * 60)

    # 测试1:正常查询
    print("\n✅ 测试1: 正常查询")
    result = xiaonuo.process_query("检索专利信息")
    print(f"结果: {result}")

    # 测试2:低置信度查询
    print("\n⚠️ 测试2: 低置信度查询(应触发认识论诚实)")
    result = xiaonuo.process_query("我不确定的问题")
    print(f"结果: {result}")

    # 测试3:高置信度查询
    print("\n✅ 测试3: 高置信度查询")
    result = xiaonuo.answer_question("小诺的功能是什么?")
    print(f"结果: {result}")

    # 打印状态报告
    wrapper.print_ethics_status()
