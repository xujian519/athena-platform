
# 在XiaonuoIntegratedEnhanced类中添加以下代码:
from core.cognition.agentic_task_planner import AgenticTaskPlanner
from core.planning.unified_planning_interface import UnifiedPlanningInterface
from integration.xiaonuo_planning_integration import XiaonuoPlanningIntegration


class XiaonuoIntegratedEnhanced(XiaonuoEnhancedAgent):
    def __init__(self, config: Dict[str, Any] | None = None):
        super().__init__(config)

        # 初始化规划器相关组件
        self.task_planner = None
        self.planning_integration = None
        self.unified_planner = None
        self.active_plans = {}

    async def initialize(self):
        # 调用父类初始化
        await super().initialize()

        # 初始化规划器
        await self._initialize_planner()

        # 初始化决策模型
        await self._initialize_decision_model()

        # 初始化认知决策协同器
        await self._initialize_cognition_decision_coordinator()

    async def _initialize_planner(self):
        """初始化规划器"""
        try:
            # 创建任务规划器
            self.task_planner = AgenticTaskPlanner()
            self.planning_integration = XiaonuoPlanningIntegration(self)
            self.unified_planner = UnifiedPlanningInterface()

            # 初始化统一规划接口
            await self.unified_planner.initialize()

            logger.info("✅ 规划器初始化完成")
            self.log_optimization("规划器集成", "成功", "任务规划器已集成到主系统")

        except Exception as e:
            logger.error(f"规划器初始化失败: {e}")
            self.log_optimization("规划器集成", "失败", str(e))

    async def create_execution_plan(self, goal: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """创建执行计划"""
        if self.unified_planner:
            return await self.unified_planner.create_plan(goal, context)
        return {"error": "规划器未初始化"}

    async def execute_plan(self, plan_id: str) -> Dict[str, Any]:
        """执行计划"""
        if self.unified_planner:
            return await self.unified_planner.execute_plan(plan_id)
        return {"error": "规划器未初始化"}
