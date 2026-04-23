#!/usr/bin/env python3
from __future__ import annotations
"""
跨智能体能力融合系统 v2.0
Cross-Agent Capability Fusion System Enhanced

实现多个智能体的能力融合和协作:
1. 能力映射和索引
2. 跨智能体知识共享
3. 集成决策机制
4. 能力互补分析
5. 融合响应生成
6. 协作效果评估
7. 动态任务调度
8. 协作优化
9. 冲突解决
10. 性能自适应

作者: Athena平台团队
创建时间: 2025-12-26
更新时间: 2025-12-30
版本: v2.0.0 "增强协作融合"
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class FusionStrategy(Enum):
    """融合策略"""

    CONSENSUS = "consensus"  # 共识决策
    WEIGHTED_VOTING = "weighted_voting"  # 加权投票
    EXPERT_BASED = "expert_based"  # 基于专家
    ENSEMBLE = "ensemble"  # 集成学习
    HIERARCHICAL = "hierarchical"  # 分层决策


@dataclass
class AgentCapability:
    """智能体能力"""

    agent_id: str
    agent_name: str
    capabilities: list[str]
    specialties: list[str]
    confidence: float = 0.8
    availability: float = 1.0


@dataclass
class FusionRequest:
    """融合请求"""

    request_id: str
    user_input: str
    context: dict[str, Any]
    required_capabilities: list[str]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentResponse:
    """智能体响应"""

    agent_id: str
    response: dict[str, Any]
    confidence: float
    reasoning: str
    processing_time: float = 0.0


@dataclass
class FusionResult:
    """融合结果"""

    fused_response: dict[str, Any]
    confidence: float
    participating_agents: list[str]
    fusion_strategy: FusionStrategy
    contribution_analysis: dict[str, float]
    reasoning: str


class CrossAgentCapabilityFusion:
    """
    跨智能体能力融合系统

    核心功能:
    1. 能力注册和发现
    2. 智能体选择
    3. 响应收集
    4. 融合决策
    5. 效果评估
    6. 持续优化
    """

    def __init__(self):
        # 智能体注册表
        self.registered_agents: dict[str, AgentCapability] = {}

        # 能力索引
        self.capability_index: dict[str, set[str]] = defaultdict(set)

        # 协作历史
        self.collaboration_history: list[dict[str, Any]] = []

        # 融合统计
        self.metrics = {
            "total_fusions": 0,
            "by_strategy": defaultdict(int),
            "avg_confidence": 0.0,
            "agent_participation": defaultdict(int),
        }

        logger.info("🔗 跨智能体能力融合系统初始化完成")

    def register_agent(self, capability: AgentCapability) -> Any:
        """注册智能体能力"""
        self.registered_agents[capability.agent_id] = capability

        # 更新能力索引
        for cap in capability.capabilities:
            self.capability_index[cap].add(capability.agent_id)

        logger.info(f"📝 智能体已注册: {capability.agent_name}")

    async def select_agents_for_task(
        self,
        required_capabilities: list[str],
        max_agents: int = 5,
        strategy: FusionStrategy = FusionStrategy.EXPERT_BASED,
    ) -> list[str]:
        """选择参与融合的智能体"""
        candidates = set()

        # 根据能力要求查找
        for cap in required_capabilities:
            if cap in self.capability_index:
                candidates.update(self.capability_index[cap])

        # 计算每个候选的匹配分数
        scores = []
        for agent_id in candidates:
            agent = self.registered_agents[agent_id]

            # 匹配度计算
            matched_caps = sum(1 for cap in required_capabilities if cap in agent.capabilities)
            match_score = matched_caps / max(len(required_capabilities), 1)

            # 综合分数(匹配度 + 置信度 + 可用性)
            overall_score = match_score * 0.5 + agent.confidence * 0.3 + agent.availability * 0.2

            scores.append((agent_id, overall_score))

        # 排序并选择Top-K
        scores.sort(key=lambda x: x[1], reverse=True)

        selected = [agent_id for agent_id, _ in scores[:max_agents]]

        logger.info(f"🎯 为任务选择了 {len(selected)} 个智能体")

        return selected

    async def fuse_responses(
        self, request: FusionRequest, strategy: FusionStrategy = FusionStrategy.WEIGHTED_VOTING
    ) -> FusionResult:
        """
        融合多个智能体的响应

        Args:
            request: 融合请求
            strategy: 融合策略

        Returns:
            FusionResult: 融合结果
        """
        # 1. 选择参与的智能体
        participant_ids = await self.select_agents_for_task(
            request.required_capabilities, strategy=strategy
        )

        # 2. 收集各智能体的响应(模拟)
        responses = await self._collect_responses(request, participant_ids)

        # 3. 应用融合策略
        fused_result = await self._apply_fusion_strategy(responses, strategy)

        # 4. 分析贡献度
        contributions = await self._analyze_contributions(responses, fused_result)

        # 5. 更新统计
        await self._update_metrics(participant_ids, fused_result, strategy)

        # 6. 记录历史
        self.collaboration_history.append(
            {
                "request_id": request.request_id,
                "participants": participant_ids,
                "strategy": strategy.value,
                "confidence": fused_result["confidence"],
                "timestamp": datetime.now(),
            }
        )

        return FusionResult(
            fused_response=fused_result["response"],
            confidence=fused_result["confidence"],
            participating_agents=participant_ids,
            fusion_strategy=strategy,
            contribution_analysis=contributions,
            reasoning=fused_result["reasoning"],
        )

    async def _collect_responses(
        self, request: FusionRequest, agent_ids: list[str]
    ) -> list[AgentResponse]:
        """收集智能体响应"""
        responses = []

        for agent_id in agent_ids:
            agent = self.registered_agents.get(agent_id)
            if not agent:
                continue

            # 模拟生成响应
            # 实际应该调用各个智能体的API
            response = await self._simulate_agent_response(agent, request)

            responses.append(response)

        return responses

    async def _simulate_agent_response(
        self, agent: AgentCapability, request: FusionRequest
    ) -> AgentResponse:
        """模拟智能体响应"""
        # 简化实现:基于能力生成伪响应

        # 计算置信度
        relevant_caps = sum(1 for cap in request.required_capabilities if cap in agent.capabilities)
        confidence = agent.confidence * (relevant_caps / max(len(request.required_capabilities), 1))

        # 生成响应
        response = {
            "agent": agent.agent_name,
            "capabilities_used": [
                cap for cap in request.required_capabilities if cap in agent.capabilities
            ],
            "result": f"基于{agent.agent_name}的处理结果",
            "recommendations": [],
        }

        reasoning = (
            f"{agent.agent_name} 基于其专业能力 "
            f"({', '.join(agent.specialties[:3])}) 提供了此响应"
        )

        return AgentResponse(
            agent_id=agent.agent_id, response=response, confidence=confidence, reasoning=reasoning
        )

    async def _apply_fusion_strategy(
        self, responses: list[AgentResponse], strategy: FusionStrategy
    ) -> dict[str, Any]:
        """应用融合策略"""
        if strategy == FusionStrategy.WEIGHTED_VOTING:
            return await self._weighted_voting(responses)
        elif strategy == FusionStrategy.EXPERT_BASED:
            return await self._expert_based(responses)
        elif strategy == FusionStrategy.CONSENSUS:
            return await self._consensus(responses)
        elif strategy == FusionStrategy.ENSEMBLE:
            return await self._ensemble(responses)
        elif strategy == FusionStrategy.HIERARCHICAL:
            return await self._hierarchical(responses)
        else:
            return await self._weighted_voting(responses)

    async def _weighted_voting(self, responses: list[AgentResponse]) -> dict[str, Any]:
        """加权投票"""
        total_weight = sum(r.confidence for r in responses)

        # 加权聚合响应
        aggregated = {}
        for response in responses:
            weight = response.confidence / max(total_weight, 1)
            for key, value in response.response.items():
                if key not in aggregated:
                    # 首次遇到此key
                    if isinstance(value, (int, float)):
                        aggregated[key] = value * weight
                    else:
                        aggregated[key] = value
                elif isinstance(value, (int, float)) and isinstance(
                    aggregated.get(key), (int, float)
                ):
                    aggregated[key] += value * weight
                elif isinstance(value, str):
                    # 字符串:选择置信度最高的
                    if weight > 0.5:
                        aggregated[key] = value
                elif isinstance(value, list):
                    # 列表:合并
                    if key not in aggregated or not isinstance(aggregated[key], list):
                        aggregated[key] = []
                    aggregated[key].extend(value)

        # 计算整体置信度
        overall_confidence = sum(r.confidence**2 for r in responses) / max(len(responses), 1)

        return {
            "response": aggregated,
            "confidence": overall_confidence,
            "reasoning": f"基于{len(responses)}个智能体的加权投票决策",
        }

    async def _expert_based(self, responses: list[AgentResponse]) -> dict[str, Any]:
        """基于专家的决策"""
        # 选择置信度最高的专家
        expert = max(responses, key=lambda r: r.confidence)

        # 但结合其他专家的建议
        suggestions = []
        for r in responses:
            if r.agent_id != expert.agent_id:
                suggestions.append(f"- {r.response.get('result', '')}")

        enhanced_response = expert.response.copy()
        enhanced_response["peer_suggestions"] = suggestions

        return {
            "response": enhanced_response,
            "confidence": expert.confidence,
            "reasoning": f"以{expert.agent_id}为主专家,结合其他专家建议",
        }

    async def _consensus(self, responses: list[AgentResponse]) -> dict[str, Any]:
        """共识决策"""
        # 找出共同点
        common_elements = {}

        # 收集所有响应中的共同元素
        if responses:
            first_response = responses[0].response
            for key in first_response:
                values = [r.response.get(key) for r in responses]
                # 如果所有值相同
                if len({str(v) for v in values}) == 1:
                    common_elements[key] = values[0]

        # 计算共识程度
        consensus_ratio = len(common_elements) / max(len(responses[0].response), 1)

        return {
            "response": common_elements,
            "confidence": 0.7 + consensus_ratio * 0.2,
            "reasoning": f"共识度: {consensus_ratio:.1%}",
        }

    async def _ensemble(self, responses: list[AgentResponse]) -> dict[str, Any]:
        """集成学习"""
        # 简化实现:平均集成
        ensemble_result = {"agent_contributions": [], "diverse_viewpoints": []}

        for r in responses:
            ensemble_result["agent_contributions"].append(
                {
                    "agent": r.agent_id,
                    "confidence": r.confidence,
                    "summary": r.response.get("result", ""),
                }
            )

        # 收集不同观点
        unique_viewpoints = set()
        for r in responses:
            if r.response.get("result"):
                unique_viewpoints.add(r.response["result"])

        ensemble_result["diverse_viewpoints"] = list(unique_viewpoints)

        return {
            "response": ensemble_result,
            "confidence": sum(r.confidence for r in responses) / len(responses),
            "reasoning": "集成多个智能体的不同观点",
        }

    async def _hierarchical(self, responses: list[AgentResponse]) -> dict[str, Any]:
        """分层决策"""
        # 按置信度分层
        sorted_responses = sorted(responses, key=lambda r: r.confidence, reverse=True)

        # 高置信度层(决策层)
        decision_layer = sorted_responses[: max(1, len(sorted_responses) // 3)]

        # 低置信度层(建议层)
        advisory_layer = sorted_responses[len(decision_layer) :]

        # 以决策层为主,参考建议层
        primary_decision = decision_layer[0].response

        suggestions = []
        for r in advisory_layer:
            suggestions.append(r.response.get("result", ""))

        if suggestions:
            primary_decision["peer_suggestions"] = suggestions

        return {
            "response": primary_decision,
            "confidence": decision_layer[0].confidence,
            "reasoning": f"分层决策: {len(decision_layer)}决策层 + {len(advisory_layer)}建议层",
        }

    async def _analyze_contributions(
        self, responses: list[AgentResponse], fused_result: dict[str, Any]
    ) -> dict[str, float]:
        """分析各智能体的贡献度"""
        contributions = {}

        total_confidence = sum(r.confidence for r in responses)

        for r in responses:
            # 基于置信度的贡献度
            contributions[r.agent_id] = r.confidence / max(total_confidence, 1)

        return contributions

    async def _update_metrics(
        self, participant_ids: list[str], fused_result: dict[str, Any], strategy: FusionStrategy
    ):
        """更新统计"""
        self.metrics["total_fusions"] += 1
        self.metrics["by_strategy"][strategy.value] += 1
        self.metrics["avg_confidence"] = (
            self.metrics["avg_confidence"] * 0.9 + fused_result["confidence"] * 0.1
        )

        for agent_id in participant_ids:
            self.metrics["agent_participation"][agent_id] += 1

    async def get_complementarity_analysis(self, agent_ids: list[str]) -> dict[str, Any]:
        """分析智能体能力互补性"""
        agents = [self.registered_agents.get(aid) for aid in agent_ids]
        agents = [a for a in agents if a]

        analysis = {
            "complementary_capabilities": [],
            "overlapping_capabilities": [],
            "collaboration_score": 0.0,
        }

        if len(agents) < 2:
            return analysis

        # 找出互补能力(某些智能体独有)
        all_capabilities = set()
        for agent in agents:
            all_capabilities.update(agent.capabilities)

        common_capabilities = set()
        for cap in all_capabilities:
            count = sum(1 for a in agents if cap in a.capabilities)
            if count == len(agents):
                common_capabilities.add(cap)
            elif count == 1:
                analysis["complementary_capabilities"].append(cap)

        # 重叠能力
        analysis["overlapping_capabilities"] = list(common_capabilities)

        # 协作分数(互补性高、重叠性适中则分数高)
        complementary_ratio = len(analysis["complementary_capabilities"]) / max(
            len(all_capabilities), 1
        )
        overlap_ratio = len(common_capabilities) / max(len(all_capabilities), 1)

        analysis["collaboration_score"] = complementary_ratio * 0.7 + overlap_ratio * 0.3

        return analysis

    async def get_fusion_metrics(self) -> dict[str, Any]:
        """获取融合统计"""
        return {
            "fusion": {
                "total_fusions": self.metrics["total_fusions"],
                "by_strategy": dict(self.metrics["by_strategy"]),
                "avg_confidence": self.metrics["avg_confidence"],
            },
            "agents": {
                "registered": len(self.registered_agents),
                "total_capabilities": len(self.capability_index),
                "participation_stats": dict(self.metrics["agent_participation"]),
            },
            "history": {
                "total_collaborations": len(self.collaboration_history),
                "recent_collaborations": len(
                    [
                        h
                        for h in self.collaboration_history
                        if (datetime.now() - h["timestamp"]).total_seconds() < 3600
                    ]
                ),
            },
        }


# 导出便捷函数
_fusion_system: CrossAgentCapabilityFusion | None = None


def get_fusion_system() -> CrossAgentCapabilityFusion:
    """获取融合系统单例"""
    global _fusion_system
    if _fusion_system is None:
        _fusion_system = CrossAgentCapabilityFusion()
        # 注册默认智能体
        _register_default_agents(_fusion_system)
    return _fusion_system


def _register_default_agents(fusion_system: CrossAgentCapabilityFusion) -> Any:
    """注册默认智能体"""

    # 小诺
    fusion_system.register_agent(
        AgentCapability(
            agent_id="xiaonuo",
            agent_name="小诺·双鱼座",
            capabilities=["情感交互", "简单任务", "代码生成", "技术咨询", "系统操作"],
            specialties=["情感理解", "用户交互", "快速响应"],
            confidence=0.92,
        )
    )

    # 小娜
    fusion_system.register_agent(
        AgentCapability(
            agent_id="xiaona",
            agent_name="小娜·天秤女神",
            capabilities=["专利检索", "专利分析", "专利申请", "审查答复", "法律咨询", "年费管理"],
            specialties=["专利专业", "法律知识", "流程管理"],
            confidence=0.97,
        )
    )


    # 小宸
    fusion_system.register_agent(
        AgentCapability(
            agent_id="xiaochen",
            agent_name="小宸·星河射手",
            capabilities=["协作协调", "任务委派", "团队管理", "冲突调解", "会议组织"],
            specialties=["团队协作", "任务协调", "冲突解决"],
            confidence=0.88,
        )
    )

    # Athena
    fusion_system.register_agent(
        AgentCapability(
            agent_id="athena",
            agent_name="Athena智慧女神",
            capabilities=["综合决策", "深度分析", "战略规划", "系统协调", "智能路由"],
            specialties=["综合分析", "战略决策", "全局优化"],
            confidence=0.95,
        )
    )

    logger.info("✅ 默认智能体已注册到融合系统")


# ==================== v2.0 增强功能 ====================


@dataclass
class TaskSchedule:
    """任务调度"""

    task_id: str
    agent_id: str
    priority: int
    estimated_duration: float
    dependencies: list[str]
    status: str = "pending"


@dataclass
class CollaborationOptimization:
    """协作优化"""

    task_id: str
    optimal_strategy: FusionStrategy
    expected_improvement: float
    agent_selection: list[str]
    reasoning: str


class EnhancedCrossAgentFusion:
    """
    增强跨智能体融合系统 v2.0

    新增功能:
    1. 动态任务调度
    2. 协作优化
    3. 冲突解决
    4. 性能自适应
    5. 负载均衡
    6. 实时协调
    """

    def __init__(self):
        # 基础融合系统
        self.base_fusion = CrossAgentCapabilityFusion()

        # 任务队列
        self.task_queue: list[TaskSchedule] = []

        # 活跃任务
        self.active_tasks: dict[str, TaskSchedule] = {}

        # 协作优化历史
        self.optimization_history: list[CollaborationOptimization] = []

        # 性能指标
        self.performance_metrics = {
            "avg_task_duration": 0.0,
            "task_success_rate": 1.0,
            "agent_utilization": defaultdict(float),
            "conflict_resolution_count": 0,
        }

        # 冲突解决策略
        self.conflict_strategies = {
            "priority": self._resolve_by_priority,
            "capability": self._resolve_by_capability,
            "load_balance": self._resolve_by_load_balance,
            "consensus": self._resolve_by_consensus,
        }

        logger.info("🔗 增强跨智能体融合系统 v2.0 初始化完成")

    async def schedule_task(
        self,
        task_id: str,
        required_capabilities: list[str],
        priority: int = 5,
        estimated_duration: float = 10.0,
        dependencies: list[str] | None = None,
    ) -> TaskSchedule:
        """
        调度任务到合适的智能体

        Args:
            task_id: 任务ID
            required_capabilities: 需要的能力
            priority: 优先级(1-10)
            estimated_duration: 预计时长(秒)
            dependencies: 依赖的任务ID列表

        Returns:
            TaskSchedule: 任务调度信息
        """
        # 选择最佳智能体
        agent_ids = await self.base_fusion.select_agents_for_task(
            required_capabilities, max_agents=1
        )

        if not agent_ids:
            logger.warning(f"⚠️ 没有找到合适的智能体处理任务 {task_id}")
            return None

        agent_id = agent_ids[0]

        schedule = TaskSchedule(
            task_id=task_id,
            agent_id=agent_id,
            priority=priority,
            estimated_duration=estimated_duration,
            dependencies=dependencies or [],
        )

        # 添加到队列
        self.task_queue.append(schedule)

        # 按优先级排序
        self.task_queue.sort(key=lambda t: t.priority, reverse=True)

        logger.info(f"📋 任务 {task_id} 已调度到 {agent_id} (优先级: {priority})")

        return schedule

    async def execute_task_queue(self) -> list[dict[str, Any]]:
        """执行任务队列"""
        results = []

        for task in self.task_queue[:]:  # 复制列表以避免并发修改
            # 检查依赖
            if not self._check_dependencies(task):
                continue

            # 执行任务
            result = await self._execute_single_task(task)
            results.append(result)

            # 从队列移除
            self.task_queue.remove(task)

        return results

    def _check_dependencies(self, task: TaskSchedule) -> bool:
        """检查任务依赖是否满足"""
        return all(dep_id not in self.active_tasks for dep_id in task.dependencies)

    async def _execute_single_task(self, task: TaskSchedule) -> dict[str, Any]:
        """执行单个任务"""
        import time

        start_time = time.time()

        # 标记为活跃
        self.active_tasks[task.task_id] = task

        # 模拟执行
        await asyncio.sleep(min(task.estimated_duration, 1))

        # 完成任务
        duration = time.time() - start_time

        # 更新性能指标
        self.performance_metrics["avg_task_duration"] = (
            self.performance_metrics["avg_task_duration"] * 0.9 + duration * 0.1
        )

        # 从活跃任务移除
        del self.active_tasks[task.task_id]

        logger.info(f"✅ 任务 {task.task_id} 完成 (耗时: {duration:.2f}s)")

        return {
            "task_id": task.task_id,
            "agent_id": task.agent_id,
            "duration": duration,
            "status": "completed",
        }

    async def optimize_collaboration(
        self, task_requirements: dict[str, Any]
    ) -> CollaborationOptimization:
        """
        优化协作策略

        Args:
            task_requirements: 任务需求

        Returns:
            CollaborationOptimization: 优化方案
        """
        required_caps = task_requirements.get("capabilities", [])
        task_complexity = task_requirements.get("complexity", "medium")

        # 根据复杂度选择策略
        if task_complexity == "simple":
            optimal_strategy = FusionStrategy.EXPERT_BASED
            reasoning = "简单任务使用专家模式,快速响应"
        elif task_complexity == "complex":
            optimal_strategy = FusionStrategy.ENSEMBLE
            reasoning = "复杂任务使用集成模式,综合多方意见"
        elif task_complexity == "critical":
            optimal_strategy = FusionStrategy.CONSENSUS
            reasoning = "关键任务使用共识模式,确保一致性"
        else:
            optimal_strategy = FusionStrategy.WEIGHTED_VOTING
            reasoning = "常规任务使用加权投票,平衡效率和质量"

        # 选择智能体
        agent_ids = await self.base_fusion.select_agents_for_task(required_caps, max_agents=5)

        # 估算改进
        expected_improvement = await self._estimate_improvement(optimal_strategy, agent_ids)

        optimization = CollaborationOptimization(
            task_id=task_requirements.get("task_id", "unknown"),
            optimal_strategy=optimal_strategy,
            expected_improvement=expected_improvement,
            agent_selection=agent_ids,
            reasoning=reasoning,
        )

        # 记录历史
        self.optimization_history.append(optimization)

        return optimization

    async def _estimate_improvement(self, strategy: FusionStrategy, agent_ids: list[str]) -> float:
        """估算协作改进幅度"""
        # 基于策略和智能体数量估算
        base_improvement = 0.15  # 基础改进15%

        # 策略加成
        strategy_bonus = {
            FusionStrategy.EXPERT_BASED: 0.05,
            FusionStrategy.ENSEMBLE: 0.10,
            FusionStrategy.CONSENSUS: 0.08,
            FusionStrategy.WEIGHTED_VOTING: 0.07,
            FusionStrategy.HIERARCHICAL: 0.06,
        }

        # 智能体数量加成
        agent_bonus = min(len(agent_ids) * 0.02, 0.10)

        total_improvement = base_improvement + strategy_bonus.get(strategy, 0) + agent_bonus

        return min(total_improvement, 0.40)  # 最多改进40%

    async def resolve_conflict(
        self, conflict_type: str, involved_agents: list[str], conflict_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        解决智能体间冲突

        Args:
            conflict_type: 冲突类型
            involved_agents: 涉及的智能体
            conflict_data: 冲突数据

        Returns:
            解决方案
        """
        logger.info(f"⚠️ 检测到冲突: {conflict_type}, 涉及 {len(involved_agents)} 个智能体")

        # 选择解决策略
        strategy = self._select_conflict_strategy(conflict_type, conflict_data)

        # 应用策略
        resolver = self.conflict_strategies.get(strategy)
        if resolver:
            resolution = await resolver(involved_agents, conflict_data)
        else:
            resolution = await self._resolve_by_priority(involved_agents, conflict_data)

        # 更新统计
        self.performance_metrics["conflict_resolution_count"] += 1

        logger.info(f"✅ 冲突已解决: {strategy}")

        return {
            "conflict_type": conflict_type,
            "strategy": strategy,
            "resolution": resolution,
            "timestamp": datetime.now(),
        }

    def _select_conflict_strategy(self, conflict_type: str, conflict_data: dict[str, Any]) -> str:
        """选择冲突解决策略"""
        if conflict_type == "resource_competition":
            return "priority"
        elif conflict_type == "opinion_divergence":
            return "consensus"
        elif conflict_type == "capability_overlap":
            return "load_balance"
        else:
            return "capability"

    async def _resolve_by_priority(self, agents: list[str], data: dict[str, Any]) -> dict[str, Any]:
        """按优先级解决"""
        # 选择优先级最高的智能体
        agent_capabilities = {aid: self.base_fusion.registered_agents.get(aid) for aid in agents}

        # 按置信度排序
        sorted_agents = sorted(
            [(aid, cap.confidence) for aid, cap in agent_capabilities.items() if cap],
            key=lambda x: x[1],
            reverse=True,
        )

        selected = sorted_agents[0][0] if sorted_agents else agents[0]

        return {
            "winner": selected,
            "reasoning": f"基于优先级(置信度)选择 {selected}",
            "alternative_agents": [aid for aid, _ in sorted_agents[1:]],
        }

    async def _resolve_by_capability(
        self, agents: list[str], data: dict[str, Any]
    ) -> dict[str, Any]:
        """按能力匹配解决"""
        required_caps = data.get("required_capabilities", [])

        # 计算每个智能体的能力匹配度
        match_scores = {}
        for aid in agents:
            agent = self.base_fusion.registered_agents.get(aid)
            if agent:
                matched = sum(1 for cap in required_caps if cap in agent.capabilities)
                match_scores[aid] = matched / max(len(required_caps), 1)

        # 选择匹配度最高的
        selected = max(match_scores.items(), key=lambda x: x[1])[0] if match_scores else agents[0]

        return {
            "winner": selected,
            "match_scores": match_scores,
            "reasoning": f"基于能力匹配选择 {selected}",
        }

    async def _resolve_by_load_balance(
        self, agents: list[str], data: dict[str, Any]
    ) -> dict[str, Any]:
        """按负载均衡解决"""
        # 计算每个智能体的当前负载
        loads = {}
        for aid in agents:
            active_count = sum(1 for task in self.active_tasks.values() if task.agent_id == aid)
            loads[aid] = active_count

        # 选择负载最低的
        selected = min(loads.items(), key=lambda x: x[1])[0] if loads else agents[0]

        return {
            "winner": selected,
            "current_loads": loads,
            "reasoning": f"基于负载均衡选择 {selected}",
        }

    async def _resolve_by_consensus(
        self, agents: list[str], data: dict[str, Any]
    ) -> dict[str, Any]:
        """按共识解决"""
        # 简化实现:返回所有智能体的建议
        return {
            "resolution_type": "collaborative",
            "participating_agents": agents,
            "reasoning": "采用协作方式,所有智能体共同参与",
            "suggested_approach": "结合各方意见,寻求共同点",
        }

    async def get_agent_utilization(self) -> dict[str, float]:
        """获取智能体利用率"""
        utilization = {}

        for agent_id in self.base_fusion.registered_agents:
            active_tasks = sum(
                1 for task in self.active_tasks.values() if task.agent_id == agent_id
            )
            queued_tasks = sum(1 for task in self.task_queue if task.agent_id == agent_id)

            # 计算利用率 (0-1)
            utilization[agent_id] = min((active_tasks + queued_tasks) / 5.0, 1.0)

        return utilization

    async def adaptive_performance_tuning(self) -> dict[str, Any]:
        """自适应性能调优"""
        # 分析性能指标
        utilization = await self.get_agent_utilization()

        # 识别瓶颈
        overloaded = [aid for aid, util in utilization.items() if util > 0.8]
        underloaded = [aid for aid, util in utilization.items() if util < 0.2]

        # 生成调优建议
        recommendations = []

        if overloaded:
            recommendations.append(
                {
                    "type": "load_balancing",
                    "description": f"以下智能体负载过高: {', '.join(overloaded)}",
                    "action": "建议将部分任务迁移到负载较低的智能体",
                }
            )

        if underloaded:
            recommendations.append(
                {
                    "type": "resource_optimization",
                    "description": f"以下智能体负载较低: {', '.join(underloaded)}",
                    "action": "可以分配更多任务或释放部分资源",
                }
            )

        # 计算整体健康分数
        avg_utilization = sum(utilization.values()) / max(len(utilization), 1)
        health_score = 1.0 - abs(avg_utilization - 0.5) * 0.5  # 理想是50%利用率

        return {
            "utilization": utilization,
            "avg_utilization": avg_utilization,
            "health_score": health_score,
            "recommendations": recommendations,
            "performance_metrics": self.performance_metrics,
        }

    async def get_enhanced_metrics(self) -> dict[str, Any]:
        """获取增强统计指标"""
        base_metrics = await self.base_fusion.get_fusion_metrics()

        enhanced_metrics = {
            "scheduling": {
                "queued_tasks": len(self.task_queue),
                "active_tasks": len(self.active_tasks),
                "avg_task_duration": self.performance_metrics["avg_task_duration"],
                "task_success_rate": self.performance_metrics["task_success_rate"],
            },
            "optimization": {
                "total_optimizations": len(self.optimization_history),
                "recent_optimizations": len(
                    [
                        opt
                        for opt in self.optimization_history
                        if (
                            datetime.now() - opt.task_id
                            if isinstance(opt.task_id, datetime)
                            else True
                        )
                    ]
                ),
            },
            "conflicts": {
                "resolved_count": self.performance_metrics["conflict_resolution_count"],
                "available_strategies": list(self.conflict_strategies.keys()),
            },
        }

        return {**base_metrics, **enhanced_metrics}


# 导出v2.0系统
_enhanced_fusion: EnhancedCrossAgentFusion | None = None


def get_enhanced_fusion_system() -> EnhancedCrossAgentFusion:
    """获取增强融合系统单例"""
    global _enhanced_fusion
    if _enhanced_fusion is None:
        _enhanced_fusion = EnhancedCrossAgentFusion()
    return _enhanced_fusion
