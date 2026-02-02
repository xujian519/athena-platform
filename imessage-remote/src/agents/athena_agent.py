"""
Athena 智能体实现
负责复杂分析和推理任务
"""

import asyncio
import time
from typing import Dict, Any
import logging
import httpx

from ..core.command_parser import ParsedCommand, TaskType
from ..core.command_router import BaseAgent

logger = logging.getLogger(__name__)


class AthenaAgent(BaseAgent):
    """
    Athena 智能体

    职责：
    1. 复杂分析任务
    2. 深度推理
    3. 报告生成
    4. 综合研究
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 Athena 智能体

        Args:
            config: 配置字典
        """
        super().__init__(config)
        self.endpoint = config.get("endpoint", "http://localhost:8000/api/athena")
        self.timeout = config.get("timeout", 600)
        self.max_retries = config.get("max_retries", 2)

    async def execute(self, command: ParsedCommand) -> Dict[str, Any]:
        """
        执行命令

        Args:
            command: 解析后的命令

        Returns:
            执行结果
        """
        start_time = time.time()

        try:
            # 根据任务类型路由
            if command.task_type == TaskType.COMPLEX_ANALYSIS:
                result = await self._execute_complex_analysis(command)
            elif command.task_type == TaskType.PATENT_ANALYSIS:
                # Athena 也可以做专利分析（更深入）
                result = await self._execute_deep_patent_analysis(command)
            else:
                result = {
                    "summary": "Athena 暂不支持此任务类型",
                    "details": {"error": f"Task type not supported: {command.task_type}"}
                }

            # 添加执行时长
            result["duration"] = time.time() - start_time
            return result

        except Exception as e:
            logger.error(f"Athena agent error: {e}")
            return {
                "summary": "Athena 执行失败",
                "details": {"error": str(e)},
                "duration": time.time() - start_time
            }

    async def _execute_complex_analysis(self, command: ParsedCommand) -> Dict[str, Any]:
        """
        执行复杂分析任务

        Args:
            command: 解析后的命令

        Returns:
            分析结果
        """
        query = command.parameters.get("query", command.query)

        logger.info(f"Executing complex analysis: {query}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.endpoint}/analyze/complex",
                    json={
                        "query": query,
                        "analysis_depth": "deep",
                        "include_reasoning": True
                    }
                )
                response.raise_for_status()
                data = response.json()

            # 提取分析结果
            analysis_result = data.get("analysis", "")
            key_findings = data.get("key_findings", [])
            confidence = data.get("confidence", 0)

            # 生成智能模式摘要（详细）
            summary = f"✅ 复杂分析完成\n\n"
            summary += f"📋 分析主题：{query}\n\n"
            summary += f"🎯 关键发现：\n"
            for i, finding in enumerate(key_findings[:3], 1):
                summary += f"{i}. {finding}\n"
            summary += f"\n置信度：{confidence}%"

            # 生成详情
            details = {
                "query": query,
                "analysis_result": analysis_result,
                "key_findings": key_findings,
                "confidence": confidence,
                "reasoning_steps": data.get("reasoning_steps", []),
                "sources": data.get("sources", [])
            }

            return {
                "summary": summary,
                "details": details
            }

        except httpx.HTTPError as e:
            logger.error(f"Complex analysis API error: {e}")
            return {
                "summary": f"❌ 复杂分析失败：{str(e)}",
                "details": {"error": str(e)}
            }

    async def _execute_deep_patent_analysis(self, command: ParsedCommand) -> Dict[str, Any]:
        """
        执行深度专利分析（比小诺更深入）

        Args:
            command: 解析后的命令

        Returns:
            分析结果
        """
        patent_number = command.parameters.get("patent_number")

        if not patent_number:
            return {
                "summary": "❌ 缺少专利号",
                "details": {"error": "Patent number not provided"}
            }

        logger.info(f"Executing deep patent analysis: {patent_number}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.endpoint}/patent/analyze/deep",
                    json={
                        "patent_number": patent_number,
                        "include_comparison": True,
                        "include_legal_analysis": True
                    }
                )
                response.raise_for_status()
                data = response.json()

            # 提取深度分析结果
            creativity_score = data.get("creativity_score", 0)
            legal_risk = data.get("legal_risk", {})
            comparison = data.get("comparison_with_prior_art", [])
            recommendations = data.get("recommendations", [])

            # 生成详细摘要
            summary = f"✅ 深度专利分析完成\n\n"
            summary += f"📋 专利号：{patent_number}\n"
            summary += f"📊 创造性评分：{creativity_score}/100\n"
            summary += f"⚠️ 法律风险等级：{legal_risk.get('level', '未知')}\n\n"
            summary += f"🔍 对比分析：找到 {len(comparison)} 件对比专利\n"
            summary += f"💡 建议：{len(recommendations)} 项"

            # 生成详情
            details = {
                "patent_number": patent_number,
                "creativity_score": creativity_score,
                "creativity_breakdown": data.get("creativity_breakdown", {}),
                "legal_risk": legal_risk,
                "comparison_with_prior_art": comparison,
                "recommendations": recommendations,
                "analysis_depth": "deep"
            }

            return {
                "summary": summary,
                "details": details
            }

        except httpx.HTTPError as e:
            logger.error(f"Deep patent analysis API error: {e}")
            return {
                "summary": f"❌ 深度分析失败：{str(e)}",
                "details": {"error": str(e)}
            }
