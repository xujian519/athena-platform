#!/usr/bin/env python3
"""
小诺意图路由器
将用户消息路由到相应的平台模块

作者: Athena平台团队
创建时间: 2025-01-31
版本: 2.0.0
"""

import re
from typing import Any, Dict, Optional, Tuple

from .registry import InvokeRequest, InvokeResult
from .invoker import PlatformModuleInvoker


class XiaonuoIntentRouter:
    """小诺意图路由器"""

    # 意图模式定义
    INTENT_PATTERNS: Dict[str, Dict] = {
        "patent_search": {
            "keywords": ["搜索", "查找", "找", "专利"],
            "module": "patent.search",
            "action": "search",
        },
        "patent_analyze": {
            "keywords": ["分析", "评估", "价值", "创新性"],
            "module": "patent.analyze",
            "action": "analyze",
        },
        "knowledge_query": {
            "keywords": ["查询", "知识", "相关"],
            "module": "knowledge.vector",
            "action": "search",
        },
        "data_export": {
            "keywords": ["导出", "下载", "保存"],
            "module": "tool.export",
            "action": "export",
        },
    }

    def __init__(self, invoker: PlatformModuleInvoker):
        """
        初始化路由器

        Args:
            invoker: 平台模块调用器
        """
        self.invoker = invoker

    async def route_and_execute(
        self,
        user_message: str,
        user_id: str,
        session_id: str
    ) -> Tuple[str, Any]:
        """
        路由并执行用户意图

        Args:
            user_message: 用户消息
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            (响应消息, 原始结果数据)
        """
        # 1. 意图识别
        intent = self._recognize_intent(user_message)
        if not intent:
            return "抱歉，我不太理解您的需求。能详细说明一下吗？", None

        # 2. 提取参数
        pattern = self.INTENT_PATTERNS[intent]
        params = self._extract_params(intent, user_message)

        # 3. 构建调用请求
        request = InvokeRequest(
            session_id=session_id,
            module=pattern["module"],
            action=pattern["action"],
            params=params,
            user_id=user_id,
        )

        # 4. 执行调用
        result = await self.invoker.invoke(request)

        # 5. 格式化响应
        if result.success:
            response = await self._format_success_response(
                user_id,
                intent,
                result.data
            )
            return response, result.data
        else:
            response = await self._format_error_response(
                user_id,
                result.error or "未知错误"
            )
            return response, None

    def _recognize_intent(self, message: str) -> Optional[str]:
        """
        识别用户意图

        Args:
            message: 用户消息

        Returns:
            意图类型或None
        """
        message_lower = message.lower()

        for intent, pattern in self.INTENT_PATTERNS.items():
            keyword_count = sum(
                1 for kw in pattern["keywords"]
                if kw in message_lower
            )
            if keyword_count >= 2:  # 至少匹配2个关键词
                return intent

        return None

    def _extract_params(self, intent: str, message: str) -> Dict[str, Any]:
        """
        提取参数

        Args:
            intent: 意图类型
            message: 用户消息

        Returns:
            参数字典
        """
        if intent == "patent_search":
            keywords = message.replace("搜索", "").replace("专利", "").replace("查找", "").replace("找", "").strip()
            return {"query": keywords, "limit": 10}

        elif intent == "patent_analyze":
            # 尝试提取专利ID
            patent_id_match = re.search(r'[A-Z]{2}\d+[A-Z]?\d?', message)
            if patent_id_match:
                return {"patent_id": patent_id_match.group()}
            return {"patent_id": ""}  # 需要用户补充

        elif intent == "knowledge_query":
            query = message.replace("查询", "").replace("知识", "").strip()
            return {"query": query, "top_k": 5}

        elif intent == "data_export":
            return {"source": "session", "format": "markdown"}

        return {}

    async def _format_success_response(
        self,
        user_id: str,
        intent: str,
        data: Any
    ) -> str:
        """
        格式化成功响应

        Args:
            user_id: 用户ID
            intent: 意图类型
            data: 结果数据

        Returns:
            格式化的响应消息
        """
        address = self.invoker.identity_manager.get_address_term(user_id)

        if intent == "patent_search":
            count = len(data) if isinstance(data, list) else 0
            return f"好的{address}！找到了{count}个相关专利，请查看详情。"

        elif intent == "patent_analyze":
            return f"好的{address}！分析完成，这个专利的技术价值评估如下..."

        elif intent == "knowledge_query":
            return f"好的{address}！找到了相关资料，正在整理..."

        return "处理完成！"

    async def _format_error_response(self, user_id: str, error: str) -> str:
        """
        格式化错误响应

        Args:
            user_id: 用户ID
            error: 错误信息

        Returns:
            格式化的错误消息
        """
        address = self.invoker.identity_manager.get_address_term(user_id)
        return f"抱歉{address}，处理请求时出现了问题：{error}"

    def get_supported_intents(self) -> Dict[str, list[str]]:
        """获取支持的意图列表"""
        return {
            intent: pattern["keywords"]
            for intent, pattern in self.INTENT_PATTERNS.items()
        }
