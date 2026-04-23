from __future__ import annotations
"""
Athena智能路由系统

支持客户端本地预处理数据的分析和任务路由到合适的智能体
"""

import logging
from enum import Enum
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """任务类型"""

    PATENT_ANALYSIS = "patent_analysis"
    LEGAL_ANALYSIS = "legal_analysis"
    TRADEMARK_ANALYSIS = "trademark_analysis"
    GENERAL_ANALYSIS = "general_analysis"


class AgentType(str, Enum):
    """智能体类型"""

    XIAONUO = "xiaonuo"  # 小诺 - 专利专家
    XIAONA = "xiaona"  # 小娜 - 法律专家
    ATHENA = "athena"  # Athena - 通用智能体


class ClientTaskRequest(BaseModel):
    """客户端任务请求"""

    request_id: str
    client_id: str
    timestamp: str
    user_intent: dict[str, Any]
    data: dict[str, Any]
    force_cloud: bool = False
    fallback_mode: bool = False


class LocalProcessingData(BaseModel):
    """本地预处理数据"""

    ocr: Optional[dict[str, Any]] = None
    image_understanding: Optional[dict[str, Any]] = None


class RouteDecision(BaseModel):
    """路由决策"""

    agent_type: AgentType
    input_data: dict[str, Any]
    use_local_data: bool
    fallback_to_file: bool = False


class IntelligentRouter:
    """
    智能路由系统

    根据任务类型和客户端本地处理结果,路由到合适的智能体
    """

    def __init__(self):
        """初始化智能路由系统"""
        # 任务类型到智能体的映射
        self.task_to_agent_mapping = {
            TaskType.PATENT_ANALYSIS: AgentType.XIAONUO,
            TaskType.LEGAL_ANALYSIS: AgentType.XIAONA,
            TaskType.TRADEMARK_ANALYSIS: AgentType.XIAONUO,  # 商标也用小诺
            TaskType.GENERAL_ANALYSIS: AgentType.ATHENA,
        }

        # 关键词到任务类型的映射
        self.keyword_task_mapping = {
            "专利": TaskType.PATENT_ANALYSIS,
            "patent": TaskType.PATENT_ANALYSIS,
            "发明专利": TaskType.PATENT_ANALYSIS,
            "实用新型": TaskType.PATENT_ANALYSIS,
            "外观设计": TaskType.PATENT_ANALYSIS,
            "法律": TaskType.LEGAL_ANALYSIS,
            "legal": TaskType.LEGAL_ANALYSIS,
            "合同": TaskType.LEGAL_ANALYSIS,
            "法规": TaskType.LEGAL_ANALYSIS,
            "诉讼": TaskType.LEGAL_ANALYSIS,
            "侵权": TaskType.LEGAL_ANALYSIS,
            "商标": TaskType.TRADEMARK_ANALYSIS,
            "trademark": TaskType.TRADEMARK_ANALYSIS,
        }

    async def route(self, request: ClientTaskRequest) -> RouteDecision:
        """
        路由任务到合适的智能体

        Args:
            request: 客户端任务请求

        Returns:
            RouteDecision: 路由决策
        """
        # 1. 分析任务类型
        task_type = self._analyze_task_type(request)

        # 2. 确定智能体
        agent_type = self._select_agent(task_type)

        # 3. 准备输入数据
        input_data = self._prepare_input_data(request)

        # 4. 判断是否使用本地数据
        use_local_data = self._should_use_local_data(request)

        # 5. 判断是否需要降级到文件
        fallback_to_file = self._should_fallback_to_file(request, use_local_data)

        logger.info(
            f"路由决策: {request.request_id} -> {agent_type.value} "
            f"(use_local_data={use_local_data}, fallback={fallback_to_file})"
        )

        return RouteDecision(
            agent_type=agent_type,
            input_data=input_data,
            use_local_data=use_local_data,
            fallback_to_file=fallback_to_file,
        )

    def _analyze_task_type(self, request: ClientTaskRequest) -> TaskType:
        """
        分析任务类型

        Args:
            request: 客户端任务请求

        Returns:
            TaskType: 任务类型
        """
        user_intent = request.user_intent

        # 优先使用客户端检测到的任务类型
        if "task_type" in user_intent:
            task_type_str = user_intent["task_type"]
            try:
                return TaskType(task_type_str)
            except ValueError:
                pass

        # 根据关键词判断
        keywords = user_intent.get("detected_keywords", [])
        raw_input = user_intent.get("raw_input", "")

        # 检查关键词
        for keyword in [*keywords, raw_input]:
            for kw, task_type in self.keyword_task_mapping.items():
                if kw.lower() in str(keyword).lower():
                    return task_type

        # 默认为通用分析
        return TaskType.GENERAL_ANALYSIS

    def _select_agent(self, task_type: TaskType) -> AgentType:
        """
        选择智能体

        Args:
            task_type: 任务类型

        Returns:
            AgentType: 智能体类型
        """
        return self.task_to_agent_mapping.get(task_type, AgentType.ATHENA)

    def _prepare_input_data(self, request: ClientTaskRequest) -> dict[str, Any]:
        """
        准备输入数据

        Args:
            request: 客户端任务请求

        Returns:
            Dict: 准备好的输入数据
        """
        input_data = {
            "request_id": request.request_id,
            "client_id": request.client_id,
            "user_intent": request.user_intent,
        }

        # 提取本地处理结果
        local_processing = request.data.get("local_processing", {})

        if local_processing:
            # OCR文本
            if local_processing.get("ocr") and local_processing["ocr"].get("success"):
                input_data["text"] = local_processing["ocr"].get("text", "")
                input_data["ocr_confidence"] = local_processing["ocr"].get("confidence", 0.0)

            # 图片理解结果
            if local_processing.get("image_understanding") and local_processing[
                "image_understanding"
            ].get("success"):
                img_result = local_processing["image_understanding"]
                input_data["structured_data"] = img_result.get("structured_data", {})
                input_data["image_description"] = img_result.get("description", "")
                input_data["image_confidence"] = img_result.get("confidence", 0.0)

        # 如果有源文件,保留文件信息
        if "source_file" in request.data:
            input_data["source_file"] = request.data["source_file"]

        return input_data

    def _should_use_local_data(self, request: ClientTaskRequest) -> bool:
        """
        判断是否使用本地数据

        Args:
            request: 客户端任务请求

        Returns:
            bool: 是否使用本地数据
        """
        # 如果强制云端,不使用本地数据
        if request.force_cloud:
            return False

        # 如果有本地处理结果,使用本地数据
        local_processing = request.data.get("local_processing", {})
        if local_processing:
            # 检查是否有成功的结果
            ocr_success = local_processing.get("ocr", {}).get("success", False)
            img_success = local_processing.get("image_understanding", {}).get("success", False)

            return ocr_success or img_success

        return False

    def _should_fallback_to_file(self, request: ClientTaskRequest, use_local_data: bool) -> bool:
        """
        判断是否需要降级到文件处理

        Args:
            request: 客户端任务请求
            use_local_data: 是否使用本地数据

        Returns:
            bool: 是否需要降级
        """
        # 如果已经标记为降级模式,返回True
        if request.fallback_mode:
            return True

        # 如果本地数据处理失败,需要降级
        if use_local_data:
            local_processing = request.data.get("local_processing", {})
            ocr_failed = not local_processing.get("ocr", {}).get("success", True)
            img_failed = not local_processing.get("image_understanding", {}).get("success", True)

            # 如果两者都失败,需要降级
            if ocr_failed and img_failed:
                return True

        return False


# 全局路由实例
intelligent_router = IntelligentRouter()
