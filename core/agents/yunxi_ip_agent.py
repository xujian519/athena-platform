#!/usr/bin/env python3
"""
云熙·IP管理智能体 v2.0
Yunxi IP Manager v2.0 - 基于BaseAgent统一接口

专业IP管理智能体，负责专利组合管理、年费提醒、价值评估等。
"""
import logging
from typing import Any, Dict, Optional

from core.agents.base import (
    AgentCapability,
    AgentMetadata,
    AgentRequest,
    AgentResponse,
    BaseAgent,
    HealthStatus,
    AgentStatus,
)

logger = logging.getLogger(__name__)


class YunxiIPAgent(BaseAgent):
    """云熙·IP管理智能体 v2.0"""

    # 实现name属性
    @property
    def name(self) -> str:
        """智能体名称"""
        return "yunxi-ip"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化云熙Agent"""
        super().__init__(config=config)

        # 初始化专利组合管理器
        try:
            from core.patent.portfolio import PortfolioManager
            self.portfolio_manager = PortfolioManager()
            self.portfolio_available = True
        except ImportError:
            self.portfolio_available = False
            logger.warning("⚠️ 专利组合管理器不可用")

        logger.info("💼 云熙·IP管理智能体初始化完成")

    def _load_metadata(self) -> AgentMetadata:
        """加载Agent元数据"""
        return AgentMetadata(
            name=self.name,
            version="2.0.0",
            description="专业知识产权管理智能体，提供专利组合管理、价值评估、维持决策等服务",
            author="Athena Team",
            tags=["ip-management", "portfolio", "valuation"]
        )

    def _register_capabilities(self) -> list[AgentCapability]:
        """注册能力列表"""
        return [
            AgentCapability(
                name="portfolio-management",
                description="专利组合管理 - 专利清单、分类分级、价值评估",
                parameters={
                    "patent_id": {"type": "string", "description": "专利号"},
                    "action": {"type": "string", "description": "操作类型"}
                },
                examples=[
                    {
                        "patent_id": "CN123456789A",
                        "action": "analyze"
                    }
                ]
            ),
            AgentCapability(
                name="patent-valuation",
                description="专利价值评估 - 动态价值评估和维持建议",
                parameters={
                    "patent_id": {"type": "string", "description": "专利号"},
                    "market_data": {"type": "object", "description": "市场数据"}
                }
            ),
            AgentCapability(
                name="deadline-tracking",
                description="期限跟踪 - 年费缴纳期限提醒",
                parameters={
                    "days": {"type": "integer", "description": "提前天数"}
                }
            )
        ]

    async def initialize(self) -> None:
        """初始化Agent"""
        logger.info("✅ 云熙Agent初始化完成")
        self._status = AgentStatus.READY

    async def shutdown(self) -> None:
        """关闭Agent"""
        logger.info("💼 云熙Agent正在关闭...")
        self._status = AgentStatus.SHUTDOWN

    async def health_check(self) -> HealthStatus:
        """健康检查"""
        return HealthStatus(
            status=self._status,
            message="云熙Agent运行正常",
            details={
                "portfolio_available": self.portfolio_available,
                "total_requests": self._stats["total_requests"],
                "successful_requests": self._stats["successful_requests"],
                "failed_requests": self._stats["failed_requests"]
            }
        )

    async def process(self, request: AgentRequest) -> AgentResponse:
        """处理请求"""
        logger.info(f"💼 云熙处理请求: {request.action}")

        try:
            # 路由到具体的处理方法
            if request.action == "portfolio-management":
                result = await self._handle_portfolio_management(request.parameters)
            elif request.action == "patent-valuation":
                result = await self._handle_patent_valuation(request.parameters)
            elif request.action == "deadline-tracking":
                result = await self._handle_deadline_tracking(request.parameters)
            else:
                result = {"error": f"未知操作: {request.action}"}

            return AgentResponse(
                request_id=request.request_id,
                success=True,
                data=result
            )

        except Exception as e:
            logger.error(f"❌ 处理失败: {e}", exc_info=True)
            return AgentResponse(
                request_id=request.request_id,
                success=False,
                error=str(e)
            )

    async def _handle_portfolio_management(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理专利组合管理"""
        if not self.portfolio_available:
            return {"error": "专利组合管理器不可用"}

        action = params.get("action", "analyze")
        patent_id = params.get("patent_id", "")

        if action == "analyze" and patent_id:
            return self.portfolio_manager.analyze_patent(patent_id)
        elif action == "summary":
            return self.portfolio_manager.get_portfolio_summary()
        else:
            return {"error": "无效的参数"}

    async def _handle_patent_valuation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理专利价值评估"""
        if not self.portfolio_available:
            return {"error": "专利组合管理器不可用"}

        patent_id = params.get("patent_id", "")
        if not patent_id:
            return {"error": "缺少专利号"}

        return self.portfolio_manager.analyze_patent(patent_id)

    async def _handle_deadline_tracking(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理期限跟踪"""
        if not self.portfolio_available:
            return {"error": "专利组合管理器不可用"}

        days = params.get("days", 30)
        deadlines = self.portfolio_manager.get_upcoming_deadlines(days)

        return {
            "upcoming_deadlines": deadlines,
            "count": len(deadlines)
        }


# 测试代码
async def test_yunxi_agent():
    """测试云熙Agent"""
    agent = YunxiIPAgent()
    await agent.initialize()

    print("\n" + "="*80)
    print("💼 云熙Agent测试")
    print("="*80)

    # 测试添加专利
    patent_data = {
        "patent_id": "CN123456789A",
        "patent_type": "invention",
        "title": "基于人工智能的智能控制系统",
        "application_date": "2020-01-15",
        "grant_date": "2022-03-20",
        "status": "maintained",
        "annual_fee_due": "2026-03-20",
        "annual_fee_amount": 1200,
        "inventor": "张三",
        "applicant": "××科技公司",
        "category": "人工智能",
        "value_score": 0.8
    }

    agent.portfolio_manager.add_patent(patent_data)

    # 测试分析请求
    request = AgentRequest(
        request_id="test_001",
        action="portfolio-management",
        parameters={
            "patent_id": "CN123456789A",
            "action": "analyze"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ 处理结果:")
    print(f"   成功: {response.success}")
    if response.success:
        analysis = response.data
        print(f"   专利号: {analysis.get('patent_id')}")
        print(f"   技术领域: {analysis.get('classification', {}).get('technology_field')}")
        print(f"   专利等级: {analysis.get('grading', {}).get('grade')}")
        print(f"   维持决策: {analysis.get('decision', {}).get('decision')}")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_yunxi_agent())
