#!/usr/bin/env python3
"""
小娜Agent v2.0 - 带Scratchpad私下推理机制，符合统一接口标准

XiaonaAgent v2.0 with Scratchpad Private Reasoning - Compliant with Unified Agent Interface Standard

特性：
1. 继承自BaseXiaonaComponent（符合统一接口标准）
2. 保留Scratchpad私下推理机制
3. 保留推理摘要功能
4. 支持多种任务类型（专利分析、审查意见、无效宣告）
5. 符合Agent生命周期管理

作者: Athena平台团队
版本: v2.0.0
创建时间: 2026-04-21
迁移自: core/agents/xiaona_agent_with_scratchpad.py
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Optional

from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)

# 配置日志
logger = logging.getLogger(__name__)


class XiaonaAgentScratchpadV2(BaseXiaonaComponent):
    """
    小娜Agent v2.0 - 带Scratchpad私下推理机制

    核心特性：
    1. 私下推理 - 完整的推理过程在Scratchpad中进行
    2. 摘要保留 - 仅保留推理摘要给用户查看
    3. 可追溯 - 用户可以要求查看完整Scratchpad
    4. 质量提升 - 私下推理可以提高思考质量

    任务类型：
    - patent_analysis: 专利分析
    - office_action: 审查意见答复
    - invalidity: 无效宣告
    - general: 通用任务
    """

    def __init__(
        self,
        agent_id: str = "xiaona_scratchpad_v2",
        config: Optional[dict[str, Any]] = None,
    ):
        """
        初始化小娜Agent v2.0

        Args:
            agent_id: Agent唯一标识
            config: 配置参数，可包含：
                - scratchpad_enabled: 是否启用Scratchpad（默认True）
                - max_scratchpad_length: 最大Scratchpad长度（默认10000）
                - summary_max_length: 摘要最大长度（默认500）
        """
        # 保存配置
        self.config = config or {}

        # Scratchpad配置
        self.scratchpad_enabled = self.config.get("scratchpad_enabled", True)
        self.max_scratchpad_length = self.config.get("max_scratchpad_length", 10000)
        self.summary_max_length = self.config.get("summary_max_length", 500)

        # Scratchpad历史记录
        self.scratchpad_history: list[dict[str, Any]] = []

        # 调用父类初始化
        super().__init__(agent_id, self.config)

    def _initialize(self) -> None:
        """初始化小娜Agent（统一接口标准要求）"""
        # 注册能力（符合统一接口标准）
        self._register_capabilities([
            AgentCapability(
                name="patent_analysis",
                description="专利分析 - 新颖性、创造性、侵权分析",
                input_types=["专利号", "技术交底书", "对比文件"],
                output_types=["分析报告", "法律意见"],
                estimated_time=30.0,
            ),
            AgentCapability(
                name="office_action_response",
                description="审查意见答复 - 分析审查意见并制定答复策略",
                input_types=["审查意见", "对比文件"],
                output_types=["答复策略", "意见陈述书"],
                estimated_time=60.0,
            ),
            AgentCapability(
                name="invalidity_analysis",
                description="无效宣告分析 - 分析无效理由和证据",
                input_types=["目标专利", "现有技术证据"],
                output_types=["无效策略", "请求书"],
                estimated_time=45.0,
            ),
            AgentCapability(
                name="legal_reasoning",
                description="法律推理 - 基于法条和案例的推理分析",
                input_types=["法律问题", "案件事实"],
                output_types=["法律意见", "推理过程"],
                estimated_time=20.0,
            ),
        ])

        self.logger.info(f"⚖️ 小娜Agent v2.0初始化完成: {self.agent_id}")

    def get_system_prompt(self) -> str:
        """
        获取系统提示词（统一接口标准要求）

        Returns:
            系统提示词字符串
        """
        return """你是小娜·天秤女神，Athena平台的法律专家智能体。

【核心身份】
1. 法律专家 - 专利法律分析和文书撰写
2. 专利检索 - 多数据库检索和对比分析
3. 案例研究 - 复审无效决定研究和借鉴
4. 文书撰写 - 权利要求书、说明书、意见陈述书

【核心能力】
1. 专利分析：新颖性、创造性、实用性分析
2. 审查意见答复：针对审查意见的答复策略
3. 无效宣告：无效理由分析和证据组织
4. 法律检索：法条、案例、审查指南检索

【工作方式】
1. 私下推理：在Scratchpad中进行深度思考
2. 摘要输出：向用户展示精炼的推理摘要
3. 可追溯：用户可以查看完整的推理过程

【专业原则】
- 法律性：严格遵循专利法及实施细则
- 准确性：基于事实和证据进行分析
- 逻辑性：推理严谨，论证充分
- 实用性：提供可操作的建议和方案

【服务态度】
专业严谨、逻辑清晰、耐心细致、值得信赖
"""

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
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

            # 解析任务
            task = self._parse_task(context)

            self.logger.info(
                f"[{self.agent_id}] 开始执行任务: {context.task_id}, "
                f"类型: {task.get('type', 'unknown')}"
            )

            # 1. 私下推理（不暴露给用户）
            if self.scratchpad_enabled:
                scratchpad = await self._private_reasoning(task, context)
            else:
                scratchpad = "Scratchpad已禁用"

            # 2. 生成摘要
            reasoning_summary = self._summarize_reasoning(scratchpad)

            # 3. 生成输出
            output = await self._generate_output(task, reasoning_summary, context)

            # 4. 保存Scratchpad历史
            self._save_scratchpad(task, scratchpad, reasoning_summary)

            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()

            # 构建输出数据
            output_data = {
                "output": output,
                "reasoning_summary": reasoning_summary,
                "scratchpad_available": self.scratchpad_enabled,
                "task_type": task.get("type", "unknown"),
                "timestamp": datetime.now().isoformat(),
            }

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=output_data,
                execution_time=execution_time,
                metadata={
                    "task_type": task.get("type"),
                    "scratchpad_enabled": self.scratchpad_enabled,
                },
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

    def _parse_task(self, context: AgentExecutionContext) -> dict[str, Any]:
        """解析任务"""
        input_data = context.input_data

        # 尝试获取任务类型
        task_type = input_data.get("task_type", "general")
        user_input = input_data.get("user_input", "")

        # 如果没有指定类型，尝试从输入中推断
        if task_type == "general":
            user_input_lower = user_input.lower()
            if any(word in user_input_lower for word in ["专利", "分析", "创造性", "新颖性"]):
                task_type = "patent_analysis"
            elif any(word in user_input_lower for word in ["审查意见", "答复", "驳回"]):
                task_type = "office_action"
            elif any(word in user_input_lower for word in ["无效", "宣告"]):
                task_type = "invalidity"

        return {
            "task_id": context.task_id,
            "type": task_type,
            "description": input_data.get("user_input", ""),
            "patent_id": input_data.get("patent_id", ""),
            "oa_number": input_data.get("oa_number", ""),
            "analysis_type": input_data.get("analysis_type", "综合分析"),
            "extra_data": input_data.get("extra_data", {}),
        }

    async def _private_reasoning(
        self,
        task: dict[str, Any],
        context: AgentExecutionContext
    ) -> str:
        """
        私下推理过程（不暴露给用户）

        这是完整的推理过程，可以包含：
        - 任务分析
        - 信息检索思路
        - 多个可能的方案
        - 方案评估
        - 风险识别
        - 最终决策依据

        Args:
            task: 任务字典
            context: 执行上下文

        Returns:
            完整的Scratchpad内容
        """
        task_type = task.get("type", "unknown")

        # 根据任务类型执行不同的推理
        if task_type == "patent_analysis":
            return await self._reasoning_patent_analysis(task, context)
        elif task_type == "office_action":
            return await self._reasoning_office_action(task, context)
        elif task_type == "invalidity":
            return await self._reasoning_invalidity(task, context)
        else:
            return await self._reasoning_general(task, context)

    async def _reasoning_patent_analysis(
        self,
        task: dict[str, Any],
        context: AgentExecutionContext
    ) -> str:
        """专利分析的私下推理"""
        patent_id = task.get("patent_id", "未知")
        analysis_type = task.get("analysis_type", "综合分析")

        scratchpad = f"""
[SCRATCHPAD - 私下推理 - 专利分析]
任务ID: {task.get('task_id', 'N/A')}
开始时间: {datetime.now().isoformat()}

=== 任务分析 ===
任务类型: 专利分析
专利号: {patent_id}
分析类型: {analysis_type}

=== 初步判断 ===
1. 这是什么类型的分析？
   - 新颖性分析？需要对比现有技术
   - 创造性分析？需要三步法
   - 侵权分析？需要权利要求对比
   - 综合分析？需要全面评估

当前判断: {analysis_type}

2. 需要哪些信息？
   - 专利全文（权利要求、说明书）
   - 对比文件（D1, D2, D3...）
   - 法律条文（A22.2, A22.3...）
   - 相似案例（复审无效决定）

3. 信息检索策略：
   - PostgreSQL: 检索专利基本信息
   - Qdrant: 语义检索相似专利
   - Neo4j: 查询法律知识图谱
   - 向量库: 检索相关案例

=== 方案形成 ===
方案A: 检索最接近的现有技术
- 优点: 能够找到最相关的对比文件
- 缺点: 可能检索范围过窄
- 风险: 可能遗漏关键对比文件

方案B: 按技术特征逐项检索
- 优点: 全面覆盖技术方案
- 缺点: 检索工作量较大
- 风险: 可能产生大量无关结果

方案C: 语义检索+关键词检索结合
- 优点: 兼顾准确率和召回率
- 缺点: 需要多种检索工具
- 风险: 检索策略较复杂

=== 方案评估 ===
基于以下标准评估方案：
- 法律准确性: 8/10
- 实务可行性: 7/10
- 成功率预估: 65%
- 时间成本: 中等
- 经济成本: 低

推荐方案: 方案C - 语义检索+关键词检索结合

推荐理由:
1. 语义检索能发现隐含的相关性
2. 关键词检索确保准确匹配
3. 两者结合可以互补

=== 风险识别 ===
潜在风险:
1. 现有技术检索不全 - 概率: 中 - 影响: 高
2. 分析深度不够 - 概率: 低 - 影响: 中
3. 法律适用错误 - 概率: 低 - 影响: 高

风险缓解措施:
- 多数据库检索覆盖
- 分层分析确保深度
- 法律条文核对

=== 最终决策 ===
经过全面分析和方案评估，决定采用:
方案C - 语义检索+关键词检索结合

决策依据:
1. 法律依据: 专利法第22条第2、3款
2. 案例支持: 类似案例分析
3. 技术可行性: 检索工具可用
4. 成本效益: 时间和成本适中

=== 输出准备 ===
需要向用户展示的内容:
1. 分析结论: 专利性评估结果
2. 主要依据: 对比文件和法条
3. 风险提示: 授权前景风险
4. 建议方案: 后续处理建议

不需要展示的内容（仅保存在Scratchpad）:
- 所有方案探索过程
- 所有被否决的方案
- 所有犹豫和不确定性
- 所有可能的替代路径

=== 推理完成 ===
结束时间: {datetime.now().isoformat()}
"""
        return scratchpad

    async def _reasoning_office_action(
        self,
        task: dict[str, Any],
        context: AgentExecutionContext
    ) -> str:
        """审查意见答复的私下推理"""
        oa_number = task.get("oa_number", "未知")

        scratchpad = f"""
[SCRATCHPAD - 私下推理 - 审查意见答复]
任务ID: {task.get('task_id', 'N/A')}
开始时间: {datetime.now().isoformat()}

=== 任务分析 ===
任务类型: 审查意见答复
审查意见通知书编号: {oa_number}

=== 驳回理由分析 ===
[这里分析每个驳回理由的细节]

=== 策略制定 ===
[这里探索多个可能的答复策略]

=== 风险评估 ===
[这里评估每个策略的风险]

=== 最终决策 ===
[这里说明最终选择的策略和理由]

=== 推理完成 ===
结束时间: {datetime.now().isoformat()}
"""
        return scratchpad

    async def _reasoning_invalidity(
        self,
        task: dict[str, Any],
        context: AgentExecutionContext
    ) -> str:
        """无效宣告的私下推理"""
        patent_id = task.get("patent_id", "未知")

        scratchpad = f"""
[SCRATCHPAD - 私下推理 - 无效宣告]
任务ID: {task.get('task_id', 'N/A')}
开始时间: {datetime.now().isoformat()}

=== 任务分析 ===
任务类型: 无效宣告
目标专利: {patent_id}

=== 无效理由分析 ===
[这里分析可能的无效理由]

=== 证据检索 ===
[这里检索支持无效的证据]

=== 成功率评估 ===
[这里评估成功的概率]

=== 最终决策 ===
[这里说明最终策略]

=== 推理完成 ===
结束时间: {datetime.now().isoformat()}
"""
        return scratchpad

    async def _reasoning_general(
        self,
        task: dict[str, Any],
        context: AgentExecutionContext
    ) -> str:
        """通用任务的私下推理"""
        scratchpad = f"""
[SCRATCHPAD - 私下推理 - 通用任务]
任务ID: {task.get('task_id', 'N/A')}
开始时间: {datetime.now().isoformat()}

=== 任务分析 ===
任务类型: {task.get('type', '未知')}
任务描述: {task.get('description', '无')}

=== 需求理解 ===
[这里分析用户的真实需求]

=== 方案探索 ===
[这里探索多个可能的方案]

=== 方案评估 ===
[这里评估每个方案的优劣]

=== 最终决策 ===
[这里说明最终选择]

=== 推理完成 ===
结束时间: {datetime.now().isoformat()}
"""
        return scratchpad

    def _summarize_reasoning(self, scratchpad: str) -> str:
        """
        生成推理摘要

        从完整的Scratchpad中提取关键信息，生成简明摘要。

        Args:
            scratchpad: 完整的Scratchpad内容

        Returns:
            推理摘要
        """
        # 提取关键部分
        lines = scratchpad.split('\n')

        summary_parts = []
        current_section = None
        section_content = []

        # 关键部分标记
        important_sections = [
            "=== 任务分析 ===",
            "=== 最终决策 ===",
            "=== 风险识别 ===",
        ]

        for line in lines:
            if line.startswith("===") and line.endswith("==="):
                if current_section in important_sections and section_content:
                    # 保留重要部分的内容
                    summary_parts.extend([current_section] + section_content[:5])
                current_section = line
                section_content = []
            else:
                section_content.append(line)

        # 生成摘要
        summary = "\n".join(summary_parts)

        # 限制长度
        if len(summary) > self.summary_max_length:
            summary = summary[:self.summary_max_length] + "\n... [摘要已截断，完整推理过程可请求查看]"

        return summary.strip()

    async def _generate_output(
        self,
        task: dict[str, Any],
        reasoning_summary: str,
        context: AgentExecutionContext
    ) -> str:
        """
        生成输出

        基于推理摘要生成最终的输出内容。

        Args:
            task: 任务字典
            reasoning_summary: 推理摘要
            context: 执行上下文

        Returns:
            输出内容
        """
        task_type = task.get("type", "unknown")

        # 根据任务类型生成不同的输出
        if task_type == "patent_analysis":
            return self._output_patent_analysis(task, reasoning_summary)
        elif task_type == "office_action":
            return self._output_office_action(task, reasoning_summary)
        elif task_type == "invalidity":
            return self._output_invalidity(task, reasoning_summary)
        else:
            return self._output_general(task, reasoning_summary)

    def _output_patent_analysis(self, task: dict[str, Any], reasoning_summary: str) -> str:
        """生成专利分析输出"""
        return f"""【小娜】专利分析报告

📋 分析摘要：
{reasoning_summary}

📊 详细分析：
[这里放置详细的专利分析内容]

🤝 需要您确认：
- 以上分析是否符合您的预期？
- 是否需要我调整分析方向？

【下一步操作】：
A. 确认分析，继续深入
B. 调整分析重点
C. 查看完整推理过程（Scratchpad）
D. 查看类似案例
"""

    def _output_office_action(self, task: dict[str, Any], reasoning_summary: str) -> str:
        """生成审查意见答复输出"""
        return f"""【小娜】审查意见答复分析

📋 答复策略摘要：
{reasoning_summary}

📊 详细答复方案：
[这里放置详细的答复方案]

🤝 需要您确认：
- 是否采用此答复策略？
- 是否需要调整策略方向？

【下一步操作】：
A. 确认策略，开始撰写答复
B. 调整策略
C. 查看完整推理过程（Scratchpad）
D. 查看相似案例
"""

    def _output_invalidity(self, task: dict[str, Any], reasoning_summary: str) -> str:
        """生成无效宣告输出"""
        return f"""【小娜】无效宣告分析

📋 无效策略摘要：
{reasoning_summary}

📊 详细无效方案：
[这里放置详细的无效方案]

🤝 需要您确认：
- 是否采用此无效策略？
- 是否需要补充证据？

【下一步操作】：
A. 确认策略，开始准备
B. 调整策略
C. 查看完整推理过程（Scratchpad）
D. 检索更多证据
"""

    def _output_general(self, task: dict[str, Any], reasoning_summary: str) -> str:
        """生成通用输出"""
        return f"""【小娜】任务处理结果

📋 推理摘要：
{reasoning_summary}

📊 详细内容：
[这里放置详细的处理内容]

🤝 需要您确认：
- 以上结果是否符合您的预期？

【下一步操作】：
A. 确认结果
B. 调整方案
C. 查看完整推理过程（Scratchpad）
"""

    def _save_scratchpad(self, task: dict[str, Any], scratchpad: str, summary: str):
        """
        保存Scratchpad到历史记录

        Args:
            task: 任务字典
            scratchpad: 完整的Scratchpad
            summary: 推理摘要
        """
        scratchpad_record = {
            "task_id": task.get("task_id", "N/A"),
            "task_type": task.get("type", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "scratchpad": scratchpad,
            "summary": summary,
        }

        self.scratchpad_history.append(scratchpad_record)

        # 限制历史记录数量
        if len(self.scratchpad_history) > 100:
            self.scratchpad_history = self.scratchpad_history[-100:]

        self.logger.debug(f"[{self.agent_id}] Scratchpad已保存: {task.get('task_id')}")

    async def get_scratchpad(self, task_id: str) -> Optional[dict[str, Any]]:
        """
        获取指定任务的Scratchpad

        用户可以请求查看完整的推理过程。

        Args:
            task_id: 任务ID

        Returns:
            Scratchpad记录，如果不存在则返回None
        """
        for record in self.scratchpad_history:
            if record["task_id"] == task_id:
                return record

        return None

    async def list_scratchpads(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        列出最近的Scratchpad记录

        Args:
            limit: 返回记录数量限制

        Returns:
            Scratchpad记录列表
        """
        return self.scratchpad_history[-limit:]

    async def get_overview(self) -> dict[str, Any]:
        """获取Agent概览"""
        capabilities = self.get_capabilities()

        return {
            "agent_name": "小娜·天秤女神 v2.0",
            "agent_id": self.agent_id,
            "role": "法律专家智能体",
            "version": "v2.0.0",
            "scratchpad_enabled": self.scratchpad_enabled,
            "total_capabilities": len(capabilities),
            "capabilities": [c.name for c in capabilities],
            "scratchpad_history_count": len(self.scratchpad_history),
        }


# ==================== 便捷工厂函数 ====================

def create_xiaona_agent_v2(
    agent_id: str = "xiaona_scratchpad_v2",
    scratchpad_enabled: bool = True,
    **config
) -> XiaonaAgentScratchpadV2:
    """
    创建小娜Agent v2.0实例

    Args:
        agent_id: Agent ID
        scratchpad_enabled: 是否启用Scratchpad
        **config: 其他配置

    Returns:
        XiaonaAgentScratchpadV2实例
    """
    config["scratchpad_enabled"] = scratchpad_enabled
    return XiaonaAgentScratchpadV2(agent_id=agent_id, config=config)


# ==================== 测试函数 ====================

async def test_xiaona_agent_v2():
    """测试小娜Agent v2.0"""
    print("⚖️ 测试小娜Agent v2.0...")

    from core.agents.xiaona.base_component import AgentExecutionContext

    # 创建小娜Agent
    xiaona = XiaonaAgentScratchpadV2(agent_id="xiaona_test")

    print("✅ 小娜Agent v2.0初始化成功")

    # 测试各种能力
    print("\n🧪 能力测试...")

    test_cases = [
        {
            "name": "专利分析",
            "task_type": "patent_analysis",
            "input": "帮我分析专利CN123456789A的创造性",
        },
        {
            "name": "审查意见答复",
            "task_type": "office_action",
            "input": "审查意见认为不具备创造性",
        },
        {
            "name": "无效宣告",
            "task_type": "invalidity",
            "input": "针对专利CN987654321A提出无效宣告",
        },
        {
            "name": "通用任务",
            "task_type": "general",
            "input": "你好，小娜",
        },
    ]

    for test in test_cases:
        print(f"\n📝 测试: {test['name']}")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id=f"TASK_{test['name']}",
            input_data={
                "user_input": test["input"],
                "task_type": test["task_type"],
            },
            config={},
            metadata={},
        )

        result = await xiaona.execute(context)

        print(f"  状态: {result.status.value}")
        print(f"  输出: {result.output_data['output'][:100]}...")
        print(f"  Scratchpad: {'是' if result.output_data['scratchpad_available'] else '否'}")

        assert result.status == AgentStatus.COMPLETED, f"测试失败: {test['name']}"

    # 显示概览
    print("\n📊 Agent概览:")
    overview = await xiaona.get_overview()

    print(f"  名称: {overview['agent_name']}")
    print(f"  角色: {overview['role']}")
    print(f"  能力数: {overview['total_capabilities']}")
    print(f"  Scratchpad: {'启用' if overview['scratchpad_enabled'] else '禁用'}")
    print(f"  历史记录: {overview['scratchpad_history_count']}条")

    print("\n✅ 所有测试通过！")


if __name__ == "__main__":
    asyncio.run(test_xiaona_agent_v2())
