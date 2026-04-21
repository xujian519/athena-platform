"""
小诺·智能体编排者 - 集成统一记忆系统

增强版编排者，集成统一记忆系统：
1. 初始化时加载用户偏好和项目上下文
2. 编排时读取历史协作经验
3. 完成后保存协作记录
4. 学习最佳编排策略
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

from core.agents.base_agent import BaseAgent
from core.memory.unified_memory_system import (
    get_project_memory,
    MemoryType,
    MemoryCategory
)

logger = logging.getLogger(__name__)


class OrchestrationStrategy(Enum):
    """编排策略"""
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"     # 并行执行
    HIERARCHICAL = "hierarchical"  # 层级执行


@dataclass
class OrchestrationPlan:
    """编排计划"""
    scenario: str                    # 场景
    strategy: OrchestrationStrategy  # 策略
    agents: List[str]                # 智能体列表
    steps: List[Dict[str, Any]]     # 执行步骤
    estimated_time: float           # 预估时间


@dataclass
class OrchestrationResult:
    """编排结果"""
    success: bool
    scenario: str
    strategy: OrchestrationStrategy
    agent_results: Dict[str, Any]  # 各智能体结果
    execution_time: float
    lessons_learned: List[str]      # 经验教训


class XiaonuoOrchestratorWithMemory(BaseAgent):
    """
    小诺·智能体编排者 - 集成统一记忆系统

    核心功能：
    - 自动加载用户偏好和项目上下文
    - 根据历史经验制定编排计划
    - 保存智能体协作记录
    - 学习最佳编排策略
    """

    def __init__(
        self,
        name: str = "xiaonuo_orchestrator",
        role: str = "智能体编排者",
        project_path: Optional[str] = None,
        **_kwargs  # noqa: ARG001
    ):
        """
        初始化小诺编排者

        Args:
            name: 智能体名称
            role: 智能体角色
            project_path: 项目路径（用于记忆系统）
            **_kwargs  # noqa: ARG001: 其他参数
        """
        # 初始化基类（包含记忆系统）
        super().__init__(
            name=name,
            role=role,
            project_path=project_path,
            **_kwargs  # noqa: ARG001
        )

        # 编排历史（从记忆系统加载）
        self.orchestration_history: List[OrchestrationResult] = []

        # 用户偏好缓存
        self.user_preferences: Dict[str, Any] = {}

        # 项目上下文缓存
        self.project_context: Dict[str, Any] = {}

        # 加载历史经验
        if self._memory_enabled:
            self._load_orchestration_history()
            self._load_user_preferences()
            self._load_project_context()

    def _load_orchestration_history(self) -> None:
        """加载历史编排经验"""
        try:
            history_content = self.load_memory(
                MemoryType.PROJECT,
                MemoryCategory.AGENT_COLLABORATION,
                "orchestration_history"
            )

            if history_content:
                # 解析历史记录
                try:
                    history_data = json.loads(history_content)
                    self.orchestration_history = [
                        OrchestrationResult(**entry) for entry in history_data
                    ]
                    logger.info(f"加载编排历史: {len(self.orchestration_history)} 条记录")
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"编排历史格式错误: {e}")
                    self.orchestration_history = []
            else:
                logger.info("未找到历史编排记录")

        except Exception as e:
            logger.error(f"加载编排历史失败: {e}")

    def _load_user_preferences(self) -> None:
        """加载用户偏好"""
        try:
            preferences_content = self.get_user_preferences()
            if preferences_content:
                # 解析用户偏好（假设为YAML格式）
                try:
                    import yaml
                    self.user_preferences = yaml.safe_load(preferences_content)
                    logger.info("用户偏好加载成功")
                except ImportError:
                    # 如果没有yaml，尝试JSON
                    self.user_preferences = json.loads(preferences_content)
                    logger.info("用户偏好加载成功（JSON格式）")

        except Exception as e:
            logger.error(f"加载用户偏好失败: {e}")

    def _load_project_context(self) -> None:
        """加载项目上下文"""
        try:
            context_content = self.get_project_context()
            if context_content:
                # 解析项目上下文
                try:
                    import yaml
                    self.project_context = yaml.safe_load(context_content)
                    logger.info("项目上下文加载成功")
                except ImportError:
                    self.project_context = json.loads(context_content)
                    logger.info("项目上下文加载成功（JSON格式）")

        except Exception as e:
            logger.error(f"加载项目上下文失败: {e}")

    def process(self, input_text: str, **_kwargs) -> str:  # noqa: ARG001
        """
        处理用户请求（集成记忆系统）

        Args:
            input_text: 输入文本
            **_kwargs  # noqa: ARG001: 其他参数

        Returns:
            响应文本
        """
        try:
            # 1. 场景识别
            scenario = self._detect_scenario(input_text)
            logger.info(f"识别场景: {scenario}")

            # 2. 制定编排计划（考虑历史经验）
            plan = self._create_orchestration_plan(scenario, input_text)

            # 3. 执行编排
            result = self._execute_orchestration(plan)

            # 4. 保存协作记录
            if self._memory_enabled:
                self._save_collaboration_record(plan, result)

            # 5. 保存工作历史
            if self._memory_enabled:
                self.save_work_history(
                    task=f"编排任务: {scenario}",
                    result=f"成功，使用策略: {plan.strategy.value}",
                    status="success" if result.success else "failed"
                )

            # 6. 生成响应
            return self._format_response(result)

        except Exception as e:
            error_msg = f"编排失败: {e}"
            logger.error(error_msg)

            # 保存失败记录
            if self._memory_enabled:
                self.save_work_history(
                    task=f"编排任务: {input_text[:100]}",
                    result=error_msg,
                    status="failed"
                )

            return error_msg

    def _detect_scenario(self, input_text: str) -> str:
        """检测业务场景"""
        # 简化版场景识别
        if "专利" in input_text and "分析" in input_text:
            return "patent_analysis"
        elif "检索" in input_text:
            return "patent_search"
        elif "撰写" in input_text:
            return "document_writing"
        else:
            return "general_task"

    def _create_orchestration_plan(
        self,
        scenario: str,
        input_text: str
    ) -> OrchestrationPlan:
        """创建编排计划（考虑历史经验）"""
        # 从历史中查找相似场景
        similar_experiences = [
            exp for exp in self.orchestration_history
            if exp.scenario == scenario and exp.success
        ]

        # 根据经验选择策略
        if similar_experiences:
            # 使用最成功的策略
            best_exp = max(similar_experiences, key=lambda x: x.execution_time)
            strategy = best_exp.strategy
            logger.info(f"使用历史策略: {strategy.value}")
        else:
            # 默认策略
            strategy = OrchestrationStrategy.SEQUENTIAL
            logger.info("使用默认策略: sequential")

        # 确定需要的智能体
        agents = self._select_agents(scenario)

        # 构建执行步骤
        steps = self._build_steps(scenario, agents)

        return OrchestrationPlan(
            scenario=scenario,
            strategy=strategy,
            agents=agents,
            steps=steps,
            estimated_time=len(agents) * 30.0  # 简化估算
        )

    def _select_agents(self, scenario: str) -> List[str]:
        """选择需要的智能体"""
        # 简化版智能体选择
        scenario_agent_map = {
            "patent_analysis": ["xiaona_retriever", "xiaona_analyzer"],
            "patent_search": ["xiaona_retriever"],
            "document_writing": ["xiaona_writer"],
            "general_task": ["xiaona_analyzer"]
        }
        return scenario_agent_map.get(scenario, ["xiaona_analyzer"])

    def _build_steps(self, scenario: str, agents: List[str]) -> List[Dict[str, Any]]:
        """构建执行步骤"""
        steps = []
        for i, agent in enumerate(agents):
            steps.append({
                "step": i + 1,
                "agent": agent,
                "action": f"执行{scenario}任务",
                "dependencies": [] if i == 0 else [agents[i - 1]]
            })
        return steps

    def _execute_orchestration(self, plan: OrchestrationPlan) -> OrchestrationResult:
        """执行编排（简化版）"""
        start_time = datetime.now()

        # 简化版执行（实际应调用各智能体）
        agent_results = {}
        for agent in plan.agents:
            agent_results[agent] = {
                "status": "success",
                "output": f"{agent} 执行完成"
            }

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        # 提取经验教训
        lessons_learned = self._extract_lessons_learned(plan, agent_results)

        result = OrchestrationResult(
            success=True,
            scenario=plan.scenario,
            strategy=plan.strategy,
            agent_results=agent_results,
            execution_time=execution_time,
            lessons_learned=lessons_learned
        )

        # 添加到历史
        self.orchestration_history.append(result)

        return result

    def _extract_lessons_learned(
        self,
        plan: OrchestrationPlan,
        agent_results: Dict[str, Any]
    ) -> List[str]:
        """提取经验教训"""
        lessons = []

        # 分析执行时间
        if plan.estimated_time > 0:
            actual_time = sum(
                r.get("execution_time", 0)
                for r in agent_results.values()
            )
            if actual_time < plan.estimated_time:
                lessons.append(f"执行效率高于预期 {((plan.estimated_time - actual_time) / plan.estimated_time * 100):.1f}%")

        # 分析成功率
        failed_agents = [
            agent for agent, result in agent_results.items()
            if result.get("status") != "success"
        ]
        if failed_agents:
            lessons.append(f"失败的智能体: {', '.join(failed_agents)}")

        return lessons

    def _save_collaboration_record(
        self,
        plan: OrchestrationPlan,
        result: OrchestrationResult
    ) -> None:
        """保存协作记录"""
        try:
            # 构建Markdown内容
            content = f"""# 智能体协作记录

**时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**场景**: {plan.scenario}
**策略**: {plan.strategy.value}

## 编排计划

- 智能体: {', '.join(plan.agents)}
- 预估时间: {plan.estimated_time:.1f}秒

## 执行结果

- 成功: {result.success}
- 实际时间: {result.execution_time:.1f}秒
- 智能体结果:
"""

            for agent, agent_result in result.agent_results.items():
                content += f"  - {agent}: {agent_result.get('status', 'unknown')}\n"

            if result.lessons_learned:
                content += "\n## 经验教训\n\n"
                for lesson in result.lessons_learned:
                    content += f"- {lesson}\n"

            content += f"\n---\n\n*由小诺编排者生成*"

            # 保存到协作记录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.save_memory(
                MemoryType.PROJECT,
                MemoryCategory.AGENT_COLLABORATION,
                f"collaboration_{timestamp}",
                content,
                metadata={
                    "scenario": plan.scenario,
                    "strategy": plan.strategy.value,
                    "success": result.success,
                    "timestamp": timestamp
                }
            )

            # 更新编排历史
            self._update_orchestration_history()

            logger.info(f"协作记录已保存: collaboration_{timestamp}")

        except Exception as e:
            logger.error(f"保存协作记录失败: {e}")

    def _update_orchestration_history(self) -> None:
        """更新编排历史"""
        try:
            # 转换为可序列化格式
            history_data = [
                {
                    "success": exp.success,
                    "scenario": exp.scenario,
                    "strategy": exp.strategy.value,
                    "agent_results": exp.agent_results,
                    "execution_time": exp.execution_time,
                    "lessons_learned": exp.lessons_learned
                }
                for exp in self.orchestration_history
            ]

            content = json.dumps(
                history_data,
                ensure_ascii=False,
                indent=2
            )

            self.save_memory(
                MemoryType.PROJECT,
                MemoryCategory.AGENT_COLLABORATION,
                "orchestration_history",
                content,
                metadata={
                    "entries_count": len(self.orchestration_history)
                }
            )

        except Exception as e:
            logger.error(f"更新编排历史失败: {e}")

    def _format_response(self, result: OrchestrationResult) -> str:
        """格式化响应"""
        response_parts = [
            f"## 编排完成\n",
            f"**场景**: {result.scenario}",
            f"**策略**: {result.strategy.value}",
            f"**状态**: {'成功' if result.success else '失败'}",
            f"**执行时间**: {result.execution_time:.1f}秒\n",
        ]

        if result.lessons_learned:
            response_parts.append("**经验教训**:")
            for lesson in result.lessons_learned:
                response_parts.append(f"- {lesson}")

        return "\n".join(response_parts)

    def get_orchestration_statistics(self) -> Dict[str, Any]:
        """获取编排统计信息"""
        if not self.orchestration_history:
            return {"total": 0}

        total = len(self.orchestration_history)
        successful = sum(1 for exp in self.orchestration_history if exp.success)
        avg_time = sum(exp.execution_time for exp in self.orchestration_history) / total

        # 场景分布
        scenario_counts: Dict[str, int] = {}
        for exp in self.orchestration_history:
            scenario_counts[exp.scenario] = scenario_counts.get(exp.scenario, 0) + 1

        return {
            "total": total,
            "successful": successful,
            "success_rate": f"{(successful / total * 100):.1f}%",
            "avg_time": f"{avg_time:.1f}s",
            "scenario_distribution": scenario_counts
        }


# 使用示例
def example_usage():
    """使用示例"""

    # 1. 创建带记忆的小诺编排者
    xiaonuo = XiaonuoOrchestratorWithMemory(
        name="xiaonuo",
        role="智能体编排者",
        project_path="/Users/xujian/Athena工作平台"
    )

    # 2. 处理任务（自动加载用户偏好和项目上下文）
    result = xiaonuo.process("帮我分析专利CN123456789A的创造性")
    print(result)

    # 3. 查看编排统计
    stats = xiaonuo.get_orchestration_statistics()
    print(f"\n编排统计: {stats}")


if __name__ == "__main__":
    example_usage()
