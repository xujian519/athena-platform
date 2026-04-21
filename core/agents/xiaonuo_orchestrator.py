"""
小诺·智能体编排者（增强版）

负责智能体的动态组装和工作流编排。
根据业务场景自动选择和组合专业智能体。
"""

from typing import Any, Dict, List, Optional
import logging
import uuid
from datetime import datetime

from core.agents.base_agent import BaseAgent
from core.orchestration.agent_registry import AgentRegistry, get_agent_registry
from core.orchestration.scenario_detector import ScenarioDetector, Scenario
from core.orchestration.workflow_builder import WorkflowBuilder, WorkflowStep, WorkflowResult
from core.orchestration.execution_monitor import ExecutionMonitor, execute_workflow, ExecutionMode

logger = logging.getLogger(__name__)


class XiaonuoOrchestrator(BaseAgent):
    """
    小诺·智能体编排者（增强版）

    核心职责：
    1. 场景识别：根据用户输入识别业务场景
    2. 智能体组装：根据场景选择需要的智能体
    3. 工作流构建：构建智能体执行工作流
    4. 执行监控：监控工作流执行状态
    5. 结果聚合：聚合各智能体的执行结果
    """

    def __init__(self, name: str = "xiaonuo_orchestrator", config: Optional[Dict[str, Any]] = None):
        """
        初始化小诺编排者

        Args:
            name: 智能体名称
            config: 配置参数
        """
        super().__init__(name, config)

        # 初始化编排组件
        self.agent_registry = get_agent_registry()
        self.scenario_detector = ScenarioDetector()
        self.workflow_builder = WorkflowBuilder(
            self.agent_registry,
            self.scenario_detector
        )
        self.execution_monitor = ExecutionMonitor()

        # 注册所有小娜专业智能体
        self._register_xiaona_agents()

        self.logger.info(f"小诺编排者初始化完成: {self.name}")

    def _register_xiaona_agents(self) -> None:
        """
        注册所有小娜专业智能体

        Phase 1智能体：
        - xiaona_retriever (检索者)
        - xiaona_analyzer (分析者)
        - xiaona_writer (撰写者)
        """
        try:
            from core.agents.xiaona.retriever_agent import RetrieverAgent
            from core.agents.xiaona.analyzer_agent import AnalyzerAgent
            from core.agents.xiaona.writer_agent import WriterAgent

            # 创建并注册智能体实例
            retriever = RetrieverAgent(
                agent_id="xiaona_retriever",
                config=self.config
            )
            self.agent_registry.register(retriever, phase=1)

            analyzer = AnalyzerAgent(
                agent_id="xiaona_analyzer",
                config=self.config
            )
            self.agent_registry.register(analyzer, phase=1)

            writer = WriterAgent(
                agent_id="xiaona_writer",
                config=self.config
            )
            self.agent_registry.register(writer, phase=1)

            self.logger.info("Phase 1 智能体注册完成")

        except ImportError as e:
            self.logger.error(f"智能体导入失败: {e}")

    async def process(self, user_input: str, session_id: Optional[str] = None) -> str:
        """
        处理用户请求

        Args:
            user_input: 用户输入
            session_id: 会话ID

        Returns:
            处理结果（JSON格式字符串）
        """
        try:
            # 生成会话ID
            if not session_id:
                session_id = str(uuid.uuid4())

            self.logger.info(f"处理用户请求: session={session_id}, input={user_input[:50]}...")

            # 步骤1：场景识别
            scenario = self.scenario_detector.detect(user_input)
            self.logger.info(f"识别场景: {scenario.value}")

            if scenario == Scenario.UNKNOWN:
                return self._format_error_response("无法识别业务场景，请提供更详细的描述")

            # 步骤2：构建工作流
            workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d%H%M%S')}_{session_id[:8]}"
            steps = self.workflow_builder.build_workflow(
                scenario=scenario,
                user_input=user_input,
                session_id=session_id,
                config=self._build_config(scenario, user_input)
            )

            self.logger.info(f"构建工作流: {len(steps)} 个步骤")

            # 步骤3：执行工作流
            result = await execute_workflow(
                workflow_id=workflow_id,
                steps=steps,
                agent_getter=self.agent_registry.get_agent,
                monitor=self.execution_monitor,
                execution_mode=ExecutionMode.SEQUENTIAL
            )

            # 步骤4：格式化结果
            return self._format_success_response(result, scenario)

        except Exception as e:
            self.logger.exception(f"处理请求失败")
            return self._format_error_response(str(e))

    def _build_config(self, scenario: Scenario, user_input: str) -> Dict[str, Any]:
        """
        构建配置参数

        Args:
            scenario: 场景类型
            user_input: 用户输入

        Returns:
            配置字典
        """
        config = {
            "databases": ["cnipa", "wipo", "epo"],
            "limit": 50,
        }

        # 根据场景添加特定配置
        if scenario == Scenario.CREATIVITY_ANALYSIS:
            config["analysis_type"] = "creativity"
        elif scenario == Scenario.PATENT_ANALYSIS:
            config["analysis_type"] = "novelty"
        elif scenario == Scenario.PATENT_WRITING:
            config["writing_type"] = "description"
        elif scenario == Scenario.OFFICE_ACTION_RESPONSE:
            config["writing_type"] = "office_action_response"
        elif scenario == Scenario.INVALIDATION:
            config["writing_type"] = "invalidation"

        return config

    def _format_success_response(
        self,
        result: WorkflowResult,
        scenario: Scenario
    ) -> str:
        """
        格式化成功响应

        Args:
            result: 工作流执行结果
            scenario: 场景类型

        Returns:
            JSON格式响应字符串
        """
        import json

        response = {
            "status": "success",
            "scenario": scenario.value,
            "workflow_id": result.workflow_id,
            "total_time": result.total_time,
            "steps_completed": len([s for s in result.steps.values() if s.status.value == "completed"]),
            "steps_total": len(result.steps),
            "output": result.final_output,
            "step_details": {
                step_id: {
                    "agent_id": step_result.agent_id,
                    "status": step_result.status.value,
                    "execution_time": step_result.execution_time,
                }
                for step_id, step_result in result.steps.items()
            },
        }

        return json.dumps(response, ensure_ascii=False, indent=2)

    def _format_error_response(self, error_message: str) -> str:
        """
        格式化错误响应

        Args:
            error_message: 错误信息

        Returns:
            JSON格式错误字符串
        """
        import json

        response = {
            "status": "error",
            "error": error_message,
            "timestamp": datetime.now().isoformat(),
        }

        return json.dumps(response, ensure_ascii=False, indent=2)

    def get_agent_status(self) -> Dict[str, Any]:
        """
        获取所有智能体状态

        Returns:
            智能体状态字典
        """
        import json

        # 获取注册表统计信息
        stats = self.agent_registry.get_statistics()

        # 获取所有智能体信息
        all_agents = self.agent_registry.list_all_agents()

        agent_details = {}
        for agent_id, agent_info in all_agents.items():
            agent_details[agent_id] = {
                "type": agent_info.agent_type,
                "phase": agent_info.phase,
                "enabled": agent_info.enabled,
                "capabilities": [cap.name for cap in agent_info.capabilities],
            }

        return {
            "statistics": stats,
            "agents": agent_details,
        }

    async def test_scenario_detection(self, user_input: str) -> str:
        """
        测试场景识别（用于调试）

        Args:
            user_input: 用户输入

        Returns:
            识别结果
        """
        import json

        scenario = self.scenario_detector.detect(user_input)
        required_agents = self.scenario_detector.get_required_agents(scenario)
        optional_agents = self.scenario_detector.get_optional_agents(scenario)
        execution_mode = self.scenario_detector.get_execution_mode(scenario)

        result = {
            "user_input": user_input,
            "detected_scenario": scenario.value,
            "required_agents": required_agents,
            "optional_agents": optional_agents,
            "execution_mode": execution_mode,
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    def get_supported_scenarios(self) -> List[Dict[str, Any]]:
        """
        获取支持的场景列表

        Returns:
            场景信息列表
        """
        scenarios = self.scenario_detector.list_all_scenarios()

        return [
            {
                "scenario": config.scenario.value,
                "name": config.name,
                "description": config.description,
                "keywords": config.keywords,
                "required_agents": config.required_agents,
                "execution_mode": config.execution_mode,
            }
            for config in scenarios
        ]
