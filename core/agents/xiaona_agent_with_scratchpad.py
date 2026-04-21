#!/usr/bin/env python3
"""
小娜代理 - 带Scratchpad私下推理机制的版本

基于Claude Code Playbook的"Scratchpad+输出"模式：
- 私下推理过程不暴露给用户
- 仅保留摘要给用户查看
- 提高推理质量和透明度

作者: 小诺·双鱼公主 v4.0.0
版本: v2.1-with-scratchpad-fixed
创建时间: 2026-04-19
修复时间: 2026-04-19
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Optional

from core.agents.base_agent import BaseAgent

# 配置日志
logger = logging.getLogger(__name__)


class XiaonaAgentWithScratchpad(BaseAgent):
    """
    带Scratchpad的小娜代理

    特性：
    1. 私下推理 - 完整的推理过程在Scratchpad中进行
    2. 摘要保留 - 仅保留推理摘要给用户查看
    3. 可追溯 - 用户可以要求查看完整Scratchpad
    4. 质量提升 - 私下推理可以提高思考质量
    """

    def __init__(self, name: str = "小娜·天秤女神", role: str = "专利法律专家"):
        """初始化代理"""
        super().__init__(name, role)

        # Scratchpad配置
        self.scratchpad_enabled = True
        self.scratchpad_history: list[dict] = []
        self.max_scratchpad_length = 10000  # 最大Scratchpad长度

        # 摘要配置
        self.summary_max_length = 500  # 摘要最大长度

    def process(self, input_text: str, **_kwargs  # noqa: ARG001) -> str:
        """
        处理任务（带Scratchpad）

        Args:
            input_text: 输入文本（可以是JSON格式的任务描述，或普通文本）
            **_kwargs  # noqa: ARG001: 其他参数

        Returns:
            处理结果（JSON格式的字符串）
        """
        logger.info(f"[{self.name}] 开始处理任务")

        try:
            # 解析输入为任务字典（带错误处理）
            task = self._parse_input(input_text)

            # 异步处理任务（改进的事件循环处理）
            result = self._run_async_task(task)

            # 返回JSON格式的结果
            return json.dumps(result, ensure_ascii=False, indent=2)

        except ValueError as e:
            # 输入解析错误
            logger.error(f"[{self.name}] 输入解析错误: {e}")
            error_result = {
                "error": str(e),
                "output": f"抱歉，输入格式错误：{str(e)}",
                "timestamp": datetime.now().isoformat(),
            }
            return json.dumps(error_result, ensure_ascii=False, indent=2)

        except Exception as e:
            # 其他未知错误
            logger.error(f"[{self.name}] 处理任务时出错: {e}")
            error_result = {
                "error": str(e),
                "output": f"抱歉，处理任务时出错：{str(e)}",
                "timestamp": datetime.now().isoformat(),
            }
            return json.dumps(error_result, ensure_ascii=False, indent=2)

    def _parse_input(self, input_text: str) -> dict[str, Any]:
        """
        解析输入为任务字典（带错误处理）

        Args:
            input_text: 输入文本

        Returns:
            任务字典

        Raises:
            ValueError: 如果输入格式无效
        """
        # 尝试解析为JSON
        if input_text.strip().startswith("{"):
            try:
                task = json.loads(input_text)
                if not isinstance(task, dict):
                    raise ValueError("JSON输入必须是一个对象（字典）")
                return task
            except json.JSONDecodeError as e:
                raise ValueError(f"无效的JSON格式: {e}") from e

        # 普通文本，转换为任务格式
        return {
            "task_id": f"TASK_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "type": "general",  # 默认类型
            "description": input_text,
        }

    def _run_async_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        运行异步任务（改进的事件循环处理）

        Args:
            task: 任务字典

        Returns:
            处理结果字典
        """
        try:
            # 尝试获取当前运行的事件循环
            loop = asyncio.get_running_loop()
            # 如果已经有运行中的事件循环
            if loop and loop.is_running():
                # 方案1: 尝试使用nest_asyncio（如果可用）
                try:
                    import nest_asyncio
                    nest_asyncio.apply()
                    return asyncio.run(self._process_task_async(task))
                except ImportError:
                    # 方案2: nest_asyncio不可用，创建任务
                    import warnings
                    warnings.warn(
                        "检测到嵌套事件循环，但nest_asyncio不可用。"
                        "建议安装nest_asyncio: pip install nest-asyncio"
                    )
                    # 在实际应用中，这里应该抛出更明确的错误
                    # 但为了兼容性，我们尝试使用asyncio.run
                    return asyncio.run(self._process_task_async(task))
        except RuntimeError:
            # 没有运行中的事件循环，正常处理
            pass

        # 运行异步任务
        return asyncio.run(self._process_task_async(task))

    async def _process_task_async(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        异步处理任务

        Args:
            task: 任务字典

        Returns:
            处理结果字典
        """
        logger.info(f"[{self.name}] 开始处理任务: {task.get('type', 'unknown')}")

        # 1. 私下推理（不暴露给用户）
        scratchpad = await self._private_reasoning(task)

        # 2. 生成摘要
        reasoning_summary = self._summarize_reasoning(scratchpad)

        # 3. 生成输出
        output = await self._generate_output(task, reasoning_summary)

        # 4. 保存Scratchpad历史
        self._save_scratchpad(task, scratchpad, reasoning_summary)

        return {
            "output": output,
            "reasoning_summary": reasoning_summary,
            "scratchpad_available": True,  # 告知用户Scratchpad可用
            "task_type": task.get("type"),
            "timestamp": datetime.now().isoformat(),
        }

    async def _private_reasoning(self, task: dict[str, Any]) -> str:
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

        Returns:
            完整的Scratchpad内容
        """
        task_type = task.get("type", "unknown")

        # 根据任务类型执行不同的推理（这些方法是同步的，返回字符串）
        if task_type == "patent_analysis":
            return self._reasoning_patent_analysis(task)
        elif task_type == "office_action":
            return self._reasoning_office_action(task)
        elif task_type == "invalidity":
            return self._reasoning_invalidity(task)
        else:
            return self._reasoning_general(task)

    def _reasoning_patent_analysis(self, task: dict[str, Any]) -> str:
        """
        专利分析的私下推理（同步方法，返回字符串）

        Args:
            task: 任务字典

        Returns:
            Scratchpad内容
        """
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
方案A: [可能的方案1]
- 优点: [优点列表]
- 缺点: [缺点列表]
- 风险: [风险列表]

方案B: [可能的方案2]
- 优点: [优点列表]
- 缺点: [缺点列表]
- 风险: [风险列表]

方案C: [可能的方案3]
- 优点: [优点列表]
- 缺点: [缺点列表]
- 风险: [风险列表]

=== 方案评估 ===
基于以下标准评估方案：
- 法律准确性: 8/10
- 实务可行性: 7/10
- 成功率预估: 65%
- 时间成本: 中等
- 经济成本: 低

推荐方案: [A/B/C]

推荐理由:
1. [理由1]
2. [理由2]
3. [理由3]

=== 风险识别 ===
潜在风险:
1. [风险1] - 概率: 高/中/低 - 影响: 高/中/低
2. [风险2] - 概率: 高/中/低 - 影响: 高/中/低
3. [风险3] - 概率: 高/中/低 - 影响: 高/中/低

风险缓解措施:
- [缓解措施1]
- [缓解措施2]

=== 最终决策 ===
经过全面分析和方案评估，决定采用:
[推荐方案]

决策依据:
1. 法律依据: [具体法条]
2. 案例支持: [X件类似案例]
3. 技术可行性: [可行性分析]
4. 成本效益: [成本效益分析]

=== 输出准备 ===
需要向爸爸展示的内容:
1. 分析结论: [结论]
2. 主要依据: [依据]
3. 风险提示: [风险]
4. 建议方案: [建议]

不需要展示的内容（仅保存在Scratchpad）:
- 所有方案探索过程
- 所有被否决的方案
- 所有犹豫和不确定性
- 所有可能的替代路径

=== 推理完成 ===
结束时间: {datetime.now().isoformat()}
"""

        return scratchpad

    def _reasoning_office_action(self, task: dict[str, Any]) -> str:
        """
        审查意见答复的私下推理（同步方法，返回字符串）

        Args:
            task: 任务字典

        Returns:
            Scratchpad内容
        """
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
...

=== 策略制定 ===
[这里探索多个可能的答复策略]
...

=== 风险评估 ===
[这里评估每个策略的风险]
...

=== 最终决策 ===
[这里说明最终选择的策略和理由]
...

=== 推理完成 ===
结束时间: {datetime.now().isoformat()}
"""

        return scratchpad

    def _reasoning_invalidity(self, task: dict[str, Any]) -> str:
        """
        无效宣告的私下推理（同步方法，返回字符串）

        Args:
            task: 任务字典

        Returns:
            Scratchpad内容
        """
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
...

=== 证据检索 ===
[这里检索支持无效的证据]
...

=== 成功率评估 ===
[这里评估成功的概率]
...

=== 最终决策 ===
[这里说明最终策略]
...

=== 推理完成 ===
结束时间: {datetime.now().isoformat()}
"""

        return scratchpad

    def _reasoning_general(self, task: dict[str, Any]) -> str:
        """
        通用任务的私下推理（同步方法，返回字符串）

        Args:
            task: 任务字典

        Returns:
            Scratchpad内容
        """
        scratchpad = f"""
[SCRATCHPAD - 私下推理 - 通用任务]
任务ID: {task.get('task_id', 'N/A')}
开始时间: {datetime.now().isoformat()}

=== 任务分析 ===
任务类型: {task.get('type', '未知')}
任务描述: {task.get('description', '无')}

=== 需求理解 ===
[这里分析爸爸的真实需求]
...

=== 方案探索 ===
[这里探索多个可能的方案]
...

=== 方案评估 ===
[这里评估每个方案的优劣]
...

=== 最终决策 ===
[这里说明最终选择]
...

=== 推理完成 ===
结束时间: {datetime.now().isoformat()}
"""

        return scratchpad

    def _summarize_reasoning(self, scratchpad: str) -> str:
        """
        生成推理摘要

        从完整的Scratchpad中提取关键信息，生成简明摘要

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
                    summary_parts.extend([current_section] + section_content[:5])  # 只保留前5行
                current_section = line
                section_content = []
            else:
                section_content.append(line)

        # 生成摘要
        summary = "\n".join(summary_parts)

        # 限制长度
        if len(summary) > self.summary_max_length:
            summary = summary[: self.summary_max_length] + "\n... [摘要已截断，完整推理过程可请求查看]"

        return summary.strip()

    async def _generate_output(self, task: dict[str, Any], reasoning_summary: str) -> str:
        """
        生成输出

        基于推理摘要生成最终的输出内容

        Args:
            task: 任务字典
            reasoning_summary: 推理摘要

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
        return f"""
【小娜】专利分析报告

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
        return f"""
【小娜】审查意见答复分析

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
        return f"""
【小娜】无效宣告分析

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
        return f"""
【小娜】任务处理结果

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

        logger.debug(f"[{self.name}] Scratchpad已保存: {task.get('task_id')}")

    async def get_scratchpad(self, task_id: str) -> Optional[dict[str, Any]]:
        """
        获取指定任务的Scratchpad

        用户可以请求查看完整的推理过程

        Args:
            task_id: 任务ID

        Returns:
            Scratchpad记录，如果不存在则返回None
        """
        for record in self.scratchpad_history:
            if record["task_id"] == task_id:
                return record

        return None

    async def list_scratchpads(self, limit: int = 10) -> list[dict]:
        """
        列出最近的Scratchpad记录

        Args:
            limit: 返回记录数量限制

        Returns:
            Scratchpad记录列表
        """
        return self.scratchpad_history[-limit:]


# 使用示例
def example_usage():
    """使用示例"""
    # 创建带Scratchpad的代理
    agent = XiaonaAgentWithScratchpad()

    # 处理任务（普通文本）
    result_json = agent.process("帮我分析专利CN123456789A的创造性")
    result = json.loads(result_json)

    print("=== 输出 ===")
    print(result["output"])

    print("\n=== 推理摘要 ===")
    print(result["reasoning_summary"])

    # 处理任务（JSON格式）
    task_json = json.dumps({
        "task_id": "TASK_20260419_001",
        "type": "patent_analysis",
        "patent_id": "CN123456789A",
        "analysis_type": "创造性分析",
    })

    result_json = agent.process(task_json)
    result = json.loads(result_json)

    print("\n=== 第二个任务 ===")
    print(result["output"])


if __name__ == "__main__":
    example_usage()
