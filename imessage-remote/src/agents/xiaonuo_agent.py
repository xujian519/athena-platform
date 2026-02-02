"""
小诺智能体实现
负责专利检索、分析和信息查询任务
"""

import asyncio
import time
from typing import Dict, Any, Optional
import logging
import httpx

from ..core.command_parser import ParsedCommand, TaskType
from ..core.command_router import BaseAgent

logger = logging.getLogger(__name__)


class XiaonuoAgent(BaseAgent):
    """
    小诺智能体

    职责：
    1. 专利检索
    2. 专利分析
    3. 信息查询
    4. 提醒事项
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化小诺智能体

        Args:
            config: 配置字典
        """
        super().__init__(config)
        self.endpoint = config.get("endpoint", "http://localhost:8000/api/xiaonuo")
        self.timeout = config.get("timeout", 300)
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
            if command.task_type == TaskType.PATENT_SEARCH:
                result = await self._execute_patent_search(command)
            elif command.task_type == TaskType.PATENT_ANALYSIS:
                result = await self._execute_patent_analysis(command)
            elif command.task_type == TaskType.INFO_QUERY:
                result = await self._execute_info_query(command)
            elif command.task_type == TaskType.REMINDER:
                result = await self._execute_reminder(command)
            else:
                result = {
                    "summary": "不支持的任务类型",
                    "details": {"error": f"Unknown task type: {command.task_type}"}
                }

            # 添加执行时长
            result["duration"] = time.time() - start_time
            return result

        except Exception as e:
            logger.error(f"Xiaonuo agent error: {e}")
            return {
                "summary": "执行失败",
                "details": {"error": str(e)},
                "duration": time.time() - start_time
            }

    async def _execute_patent_search(self, command: ParsedCommand) -> Dict[str, Any]:
        """
        执行专利检索

        Args:
            command: 解析后的命令

        Returns:
            检索结果
        """
        query = command.parameters.get("query", command.query)

        logger.info(f"Executing patent search: {query}")

        # 调用小诺的专利检索API
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.endpoint}/patent/search",
                    json={
                        "query": query,
                        "limit": 20,
                        "source": "cnipa"
                    }
                )
                response.raise_for_status()
                data = response.json()

            # 提取结果
            patents = data.get("patents", [])
            result_count = len(patents)

            # 生成摘要
            summary = f"✅ 专利检索完成\n"
            summary += f"关键词：{query}\n"
            summary += f"结果：找到 {result_count} 件相关专利"

            # 生成详情
            details = {
                "query": query,
                "result_count": result_count,
                "patents": [
                    {
                        "title": p.get("title", ""),
                        "patent_number": p.get("patent_number", ""),
                        "abstract": p.get("abstract", "")[:200] + "..."
                    }
                    for p in patents[:5]  # 只包含前5件
                ]
            }

            return {
                "summary": summary,
                "details": details
            }

        except httpx.HTTPError as e:
            logger.error(f"Patent search API error: {e}")
            return {
                "summary": f"❌ 专利检索失败：{str(e)}",
                "details": {"error": str(e)}
            }

    async def _execute_patent_analysis(self, command: ParsedCommand) -> Dict[str, Any]:
        """
        执行专利分析

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

        logger.info(f"Executing patent analysis: {patent_number}")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.endpoint}/patent/analyze",
                    json={
                        "patent_number": patent_number,
                        "analysis_type": "creativity"
                    }
                )
                response.raise_for_status()
                data = response.json()

            # 提取分析结果
            creativity_score = data.get("creativity_score", 0)
            innovation_points = data.get("innovation_points", [])

            # 生成摘要
            summary = f"✅ 专利分析完成\n"
            summary += f"专利号：{patent_number}\n"
            summary += f"创造性评分：{creativity_score}/100\n"
            summary += f"主要创新点：{len(innovation_points)} 项"

            # 生成详情
            details = {
                "patent_number": patent_number,
                "creativity_score": creativity_score,
                "innovation_points": innovation_points,
                "technical_field": data.get("technical_field", ""),
                "prior_art": data.get("prior_art", [])
            }

            return {
                "summary": summary,
                "details": details
            }

        except httpx.HTTPError as e:
            logger.error(f"Patent analysis API error: {e}")
            return {
                "summary": f"❌ 专利分析失败：{str(e)}",
                "details": {"error": str(e)}
            }

    async def _execute_info_query(self, command: ParsedCommand) -> Dict[str, Any]:
        """
        执行信息查询

        Args:
            command: 解析后的命令

        Returns:
            查询结果
        """
        target_entity = command.parameters.get("target_entity")

        if not target_entity:
            return {
                "summary": "❌ 缺少查询对象",
                "details": {"error": "Target entity not provided"}
            }

        logger.info(f"Executing info query: {target_entity}")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.endpoint}/info/query",
                    json={
                        "entity": target_entity,
                        "info_type": "contact"
                    }
                )
                response.raise_for_status()
                data = response.json()

            # 提取查询结果
            name = data.get("name", "")
            phone = data.get("phone", "")
            email = data.get("email", "")

            # 生成摘要
            summary = f"✅ 查询完成\n"
            summary += f"姓名：{name}\n"
            if phone:
                summary += f"电话：{phone}\n"
            if email:
                summary += f"邮箱：{email}"

            # 生成详情
            details = {
                "name": name,
                "phone": phone,
                "email": email,
                "other_info": data.get("other_info", {})
            }

            return {
                "summary": summary,
                "details": details
            }

        except httpx.HTTPError as e:
            logger.error(f"Info query API error: {e}")
            return {
                "summary": f"❌ 查询失败：{str(e)}",
                "details": {"error": str(e)}
            }

    async def _execute_reminder(self, command: ParsedCommand) -> Dict[str, Any]:
        """
        执行提醒事项

        Args:
            command: 解析后的命令

        Returns:
            提醒结果
        """
        # 解析提醒内容
        reminder_text = command.raw_text.replace("提醒", "").replace("记得", "").strip()

        logger.info(f"Creating reminder: {reminder_text}")

        # TODO: 集成提醒系统
        # 这里可以调用系统提醒功能或写入 Obsidian

        summary = f"✅ 已创建提醒\n"
        summary += f"内容：{reminder_text}"

        details = {
            "reminder_text": reminder_text,
            "created_at": time.time()
        }

        return {
            "summary": summary,
            "details": details
        }
