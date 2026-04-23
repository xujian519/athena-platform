#!/usr/bin/env python3
"""
云熙·IP管理智能体 v3.0 - 符合统一接口标准
Yunxi IP Manager v3.0 - Compliant with Unified Agent Interface Standard

专业IP管理智能体，负责专利组合管理、年费提醒、价值评估等。

作者: Athena平台团队
版本: v3.0.0
创建时间: 2026-04-21
迁移自: core/agents/yunxi_ip_agent.py
"""

import logging
from datetime import datetime
from typing import Any, Optional

from core.framework.agents.xiaona.base_component import (
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
    BaseXiaonaComponent,
)

logger = logging.getLogger(__name__)


class YunxiIPAgentV3(BaseXiaonaComponent):
    """
    云熙·IP管理智能体 v3.0

    核心能力：
    1. 专利组合管理 - 专利清单、分类分级、价值评估
    2. 专利价值评估 - 动态价值评估和维持建议
    3. 期限跟踪 - 年费缴纳期限提醒

    架构说明：
    - 继承BaseXiaonaComponent（符合统一接口标准）
    - 专利组合管理器通过组合方式集成（可选）
    - 支持模拟模式（当组合管理器不可用时）
    """

    def __init__(
        self,
        agent_id: str = "yunxi_ip_agent_v3",
        config: Optional[dict[str, Any]],
    ):
        """
        初始化云熙IP管理Agent v3.0

        Args:
            agent_id: Agent唯一标识
            config: 配置参数，可包含：
                - enable_portfolio_manager: 是否启用组合管理器（默认True）
        """
        # 保存配置
        self.config = config or {}
        self._enable_portfolio_manager = self.config.get("enable_portfolio_manager", True)

        # 专利组合管理器
        self.portfolio_manager = None
        self.portfolio_available = False

        # 调用父类初始化
        super().__init__(agent_id, self.config)

    def _initialize(self) -> str:
        """初始化云熙IP管理Agent（统一接口标准要求）"""
        # 注册能力（符合统一接口标准）
        self._register_capabilities([

            AgentCapability(
                name="portfolio_management",
                description="专利组合管理 - 专利清单、分类分级、价值评估",
                input_types=["专利号", "操作类型"],
                output_types=["组合分析结果"],
                estimated_time=5.0,
            ),
            AgentCapability(
                name="patent_valuation",
                description="专利价值评估 - 动态价值评估和维持建议",
                input_types=["专利号", "市场数据"],
                output_types=["价值评估报告"],
                estimated_time=10.0,
            ),
            AgentCapability(
                name="deadline_tracking",
                description="期限跟踪 - 年费缴纳期限提醒",
                input_types=["提前天数"],
                output_types=["即将到期专利列表"],
                estimated_time=3.0,
            ),
        )

        # 尝试初始化组合管理器
        if self._enable_portfolio_manager:
            try:
                from core.patents.portfolio import PortfolioManager
                self.portfolio_manager = PortfolioManager()
                self.portfolio_available = True
                self.logger.info("✅ 专利组合管理器已初始化")
            except ImportError:
                self.portfolio_available = False
                self.logger.warning("⚠️ 专利组合管理器不可用")

        self.logger.info(f"💼 云熙IP管理Agent v3.0初始化完成: {self.agent_id}")

    def get_system_prompt(self) -> str:
        """获取系统提示词（统一接口标准要求）"""
        return """你是云熙，专业的知识产权管理专家。

【核心能力】
1. 专利组合管理 - 专利清单维护、分类分级、价值评估
2. 专利价值评估 - 基于多维度的动态价值评估
3. 期限跟踪 - 年费缴纳期限提醒、维持决策建议

【服务内容】
- 专利入库与信息维护
- 专利价值动态评估
- 年费期限跟踪与提醒
- 维持决策建议
- 专利组合分析报告

【工作原则】
- 精确管理：准确记录每件专利信息
- 及时提醒：年费期限提前提醒
- 价值导向：基于价值评估给出建议
- 决策支持：为维持决策提供数据支持
"""

    async def execute(self, context: AgentExecutionContext) -> str:
        """
        执行任务（统一接口标准要求）

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        start_time = datetime.now()

        try:
            # 验证输入
            if not self.validate_input(context):
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.ERROR,
                    output_data=None,
                    error_message="输入验证失败：缺少session_id或task_id",
                    execution_time=0.0,
                )

            # 获取操作类型和参数
            action = context.input_data.get("action", "portfolio_management")
            params = context.input_data.get("params", {})

            self.logger.info(f"[{self.agent_id}] 执行操作: {action}")

            # 路由到对应的处理方法
            handler = self._get_handler(action)
            if not handler:
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.ERROR,
                    output_data=None,
                    error_message=f"不支持的操作: {action}",
                    execution_time=0.0,
                )

            # 执行处理
            result = await handler(params)

            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()

            # 构建输出数据
            output_data = {
                "action": action,
                "result": result,
                "agent_info": {
                    "agent_id": self.agent_id,
                    "portfolio_manager_available": self.portfolio_available,
                },
                "timestamp": datetime.now().isoformat(),
            }

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=output_data,
                execution_time=execution_time,
                metadata={"action": action},
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.exception(f"任务执行失败: {context.task_id}")

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=str(e),
                execution_time=execution_time,
            )

    def _get_handler(self, action: str):
        """获取操作对应的处理方法"""
        handlers = {
            "portfolio_management": self._handle_portfolio_management,
            "patent_valuation": self._handle_patent_valuation,
            "deadline_tracking": self._handle_deadline_tracking,
        }
        return handlers.get(action)

    # ==================== 处理方法 ====================

    async def _handle_portfolio_management(self, params: Optional[dict[str, Any])] -> dict[str, Any]:
        """处理专利组合管理"""
        if not self.portfolio_available:
            return self._simulate_portfolio_management(params)

        action = params.get("action", "analyze")
        patent_id = params.get("patent_id", "")

        if action == "analyze" and patent_id:
            return self.portfolio_manager.analyze_patent(patent_id)
        elif action == "summary":
            return self.portfolio_manager.get_portfolio_summary()
        elif action == "add":
            # 添加专利到组合
            patent_data = params.get("patent_data", {})
            return self.portfolio_manager.add_patent(patent_data)
        else:
            return {"error": "无效的参数"}

    async def _handle_patent_valuation(self, params: Optional[dict[str, Any])] -> dict[str, Any]:
        """处理专利价值评估"""
        patent_id = params.get("patent_id", "")
        if not patent_id:
            return {"error": "缺少专利号"}

        if not self.portfolio_available:
            return self._simulate_patent_valuation(patent_id, params)

        return self.portfolio_manager.analyze_patent(patent_id)

    async def _handle_deadline_tracking(self, params: Optional[dict[str, Any])] -> dict[str, Any]:
        """处理期限跟踪"""
        days = params.get("days", 30)

        if not self.portfolio_available:
            return self._simulate_deadline_tracking(days)

        deadlines = self.portfolio_manager.get_upcoming_deadlines(days)

        return {
            "upcoming_deadlines": deadlines,
            "count": len(deadlines),
            "query_days": days,
        }

    # ==================== 模拟方法（当组合管理器不可用时） ====================

    def _simulate_portfolio_management(self, params: Optional[dict[str, Any])] -> dict[str, Any]:
        """模拟专利组合管理"""
        action = params.get("action", "analyze")
        patent_id = params.get("patent_id", "CN123456789A")

        if action == "analyze":
            return {
                "patent_id": patent_id,
                "classification": {
                    "technology_field": "人工智能",
                    "application_area": "智能控制系统",
                },
                "grading": {
                    "grade": "A",
                    "score": 85,
                    "reason": "核心技术专利，市场前景良好"
                },
                "decision": {
                    "decision": "建议维持",
                    "reason": "专利价值高，建议继续维持",
                    "next_annual_fee": 1200,
                    "due_date": "2026-03-20"
                },
                "note": "模拟数据（组合管理器不可用）"
            }
        elif action == "summary":
            return {
                "total_patents": 0,
                "maintained_patents": 0,
                "pending_payment": 0,
                "note": "模拟数据（组合管理器不可用）"
            }
        else:
            return {"error": "无效的参数"}

    def _simulate_patent_valuation(self, patent_id: str, params: Optional[dict[str, Any])] -> dict[str, Any]:
        """模拟专利价值评估"""
        import random
        return {
            "patent_id": patent_id,
            "valuation": {
                "current_value": random.randint(50, 500) * 10000,
                "value_range": Optional[[300000, 800000],]

                "currency": "CNY"
            },
            "factors": {
                "technology": 0.8,
                "market": 0.7,
                "legal": 0.9,
                "commercial": 0.6
            },
            "recommendation": {
                "action": "建议维持",
                "confidence": 0.75
            },
            "note": "模拟数据（组合管理器不可用）"
        }

    def _simulate_deadline_tracking(self, days: int) -> dict[str, Any]:
        """模拟期限跟踪"""
        from datetime import timedelta

        # 生成一些模拟的即将到期专利
        deadlines = []
        for i in range(min(3, days // 10)):
            due_date = (datetime.now() + timedelta(days=i * 10 + 5)).strftime("%Y-%m-%d")
            deadlines.append({
                "patent_id": f"CN12345678{i}A",
                "title": f"测试专利 {i+1}",
                "annual_fee": 1200 + i * 200,
                "due_date": due_date,
                "days_remaining": i * 10 + 5
            })

        return {
            "upcoming_deadlines": deadlines,
            "count": len(deadlines),
            "query_days": days,
            "note": "模拟数据（组合管理器不可用）"
        }

    async def get_overview(self) -> dict[str, Any]:
        """获取Agent概览"""
        capabilities = self.get_capabilities()

        return {
            "agent_name": "云熙·IP管理Agent v3.0",
            "agent_id": self.agent_id,
            "role": "知识产权管理专家",
            "version": "v3.0.0",
            "total_capabilities": len(capabilities),
            "capabilities": Optional[[c.name for c in capabilities],]

            "portfolio_manager_available": self.portfolio_available,
            "portfolio_manager_enabled": self._enable_portfolio_manager,
        }


# ==================== 便捷工厂函数 ====================

def create_yunxi_ip_agent_v3(
    agent_id: str = "yunxi_ip_agent_v3",
    enable_portfolio_manager: bool = True,
    **config
) -> str:
    """
    创建云熙IP管理Agent v3.0实例

    Args:
        agent_id: Agent ID
        enable_portfolio_manager: 是否启用组合管理器
        **config: 其他配置

    Returns:
        YunxiIPAgentV3实例
    """
    config["enable_portfolio_manager"] = enable_portfolio_manager
    return YunxiIPAgentV3(agent_id=agent_id, config=config)


# ==================== 测试函数 ====================

async def test_yunxi_ip_agent_v3():
    """测试云熙IP管理Agent v3.0"""
    print("💼 测试云熙IP管理Agent v3.0...")

    from core.framework.agents.xiaona.base_component import AgentExecutionContext

    # 创建云熙IP管理Agent
    agent = YunxiIPAgentV3(agent_id="yunxi_test")

    print("✅ 云熙IP管理Agent v3.0初始化成功")

    # 测试各种能力
    print("\n🧪 能力测试...")

    test_cases = []

        {
            "name": "专利组合管理",
            "action": "portfolio_management",
            "params": {
                "action": "analyze",
                "patent_id": "CN123456789A"
            },
        },
        {
            "name": "专利价值评估",
            "action": "patent_valuation",
            "params": {
                "patent_id": "CN987654321A"
            },
        },
        {
            "name": "期限跟踪",
            "action": "deadline_tracking",
            "params": {
                "days": 30
            },
        },
    

    for test in test_cases:
        print(f"\n📝 测试: {test['name']}")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id=f"TASK_{test['name']}",
            input_data={
                "action": test["action"],
                "params": test["params"],
            },
            config={},
            metadata={},
        )

        result = await agent.execute(context)

        print(f"  状态: {result.status.value}")
        if result.status == AgentStatus.COMPLETED:
            print(f"  结果: {str(result.output_data['result'])[:100]}...")

        assert result.status == AgentStatus.COMPLETED, f"测试失败: {test['name']}"

    # 显示概览
    print("\n📊 Agent概览:")
    overview = await agent.get_overview()

    print(f"  名称: {overview['agent_name']}")
    print(f"  角色: {overview['role']}")
    print(f"  能力数: {overview['total_capabilities']}")
    print(f"  组合管理器可用: {overview['portfolio_manager_available']}")

    print("\n✅ 所有测试通过！")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_yunxi_ip_agent_v3())

