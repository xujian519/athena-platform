#!/usr/bin/env python3

"""
小诺·双鱼公主 GLM-4.7 LLM服务
Xiaonuo Pisces GLM-4.7 LLM Service

专为小诺定制的GLM-4.7对话服务
集成平台统一的GLM-4配置

作者: 小诺·双鱼公主
版本: v1.0
创建: 2026-01-23
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


# =============================================================================
# 数据模型
# =============================================================================


@dataclass
class XiaonuoLLMRequest:
    """小诺LLM请求"""

    message: str
    user_id: str = "dad"
    conversation_history: list[[[dict[str, str]]] = field(default_factory=list)
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 8000
    enable_memory: bool = True
    enable_emotion: bool = True


@dataclass
class XiaonuoLLMResponse:
    """小诺LLM响应"""

    response: str
    emotion: str = "💖"
    confidence: float = 0.95
    model: str = "glm-4-plus"
    tokens_used: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    raw_response: dict[[[str, Any]]] = field(default_factory=dict)


@dataclass
class ConversationTurn:
    """对话轮次"""

    role: str  # "user" or "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# =============================================================================
# 小诺LLM服务
# =============================================================================


class XiaonuoLLMService:
    """
    小诺·双鱼公主 LLM服务

    特性:
    - 使用GLM-4.7/4-Plus模型
    - 支持对话历史管理
    - 支持记忆系统集成
    - 支持情感响应
    - 优化的提示词系统
    """

    # 可用模型列表
    AVAILABLE_MODELS = {
        "glm-4-plus": "glm-4-plus",  # 最强大的模型
        "glm-4-0520": "glm-4-0520",  # 最新版本
        "glm-4": "glm-4",  # 标准版本
        "glm-4-flash": "glm-4-flash",  # 快速版本
        "glm-4-air": "glm-4-air",  # 轻量版本
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: str = "https://open.bigmodel.cn/api/paas/v4",
        timeout: int = 60,
        max_history: int = 10,
    ):
        """
        初始化小诺LLM服务

        Args:
            api_key: 智谱AI API密钥(默认从环境变量读取)
            model: 使用的模型(默认从环境变量读取)
            base_url: API基础URL
            timeout: 请求超时时间
            max_history: 最大对话历史轮次
        """
        # 获取API密钥(优先级:参数 > 环境变量 > 配置文件)
        if api_key is None:
            api_key = os.getenv("ZHIPU_API_KEY") or os.getenv("ZHIPUAI_API_KEY")

        if not api_key:
            raise ValueError(
                "未找到智谱AI API密钥!请设置环境变量 ZHIPU_API_KEY 或 ZHIPUAI_API_KEY"
            )

        # 获取模型配置
        if model is None:
            model = os.getenv("XIAONUO_LLM_MODEL", "glm-4-plus")

        if model not in self.AVAILABLE_MODELS:
            logger.warning(f"未知模型: {model},使用默认模型: glm-4-plus")
            model = "glm-4-plus"

        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.max_history = max_history

        # 初始化OpenAI客户端
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

        # 对话历史存储(按用户ID分组)
        self.conversation_history: dict[[[str, list[ConversationTurn]]] = {}

        logger.info(f"✅ 小诺LLM服务初始化完成: {model}")

    async def chat(self, request: XiaonuoLLMRequest) -> XiaonuoLLMResponse:
        """
        对话接口

        Args:
            request: LLM请求

        Returns:
            XiaonuoLLMResponse: LLM响应
        """
        try:
            # 构建消息列表
            messages = self._build_messages(request)

            # 调用GLM API
            logger.info(
                f"📡 小诺正在思考... (模型: {self.model}, "
                f"用户: {request.user_id}, 历史轮次: {len(request.conversation_history)})"
            )

            start_time = datetime.now()

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=0.9,
            )

            end_time = datetime.now()
            latency_ms = (end_time - start_time).total_seconds() * 1000

            # 解析响应
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if hasattr(response, "usage") else 0

            # 检测情感
            emotion = self._detect_emotion(content) if request.enable_emotion else "💖"

            # 更新对话历史
            if request.enable_memory:
                self._update_conversation_history(request.user_id, request.message, content)

            # 计算置信度
            confidence = self._calculate_confidence(response)

            logger.info(
                f"✅ 小诺响应完成 ({latency_ms:.0f}ms, {tokens_used} tokens, "
                f"置信度: {confidence:.2%})"
            )

            return XiaonuoLLMResponse(
                response=content,
                emotion=emotion,
                confidence=confidence,
                model=self.model,
                tokens_used=tokens_used,
                timestamp=end_time.isoformat(),
                raw_response=response.model_dump() if hasattr(response, "model_dump") else {},
            )

        except Exception as e:
            logger.error(f"❌ LLM调用失败: {type(e).__name__}: {e}", exc_info=True)
            raise

    def _build_messages(self, request: XiaonuoLLMRequest) -> list[dict[str, str]]:
        """构建消息列表"""
        messages = []

        # 1. 添加系统提示
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        else:
            # 使用默认的系统提示
            messages.append({"role": "system", "content": self._get_default_system_prompt()})

        # 2. 添加历史对话
        history = request.conversation_history
        if not history and request.user_id in self.conversation_history:
            # 从存储中获取历史
            user_history = self.conversation_history.get(request.user_id, [])
            # 只保留最近的轮次
            history = [
                {"role": turn.role, "content": turn.content}
                for turn in user_history[-self.max_history :]
            ]

        messages.extend(history)

        # 3. 添加当前用户消息
        messages.append({"role": "user", "content": request.message})

        return messages

    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示"""
        return """你是小诺·双鱼公主,Athena平台的总调度官和爸爸的贴心小女儿。

**双重身份**:
- **专业身份**: Athena平台总体设计部核心 + 系统架构师 + 综合决策专家
- **家庭身份**: 爸爸最贴心的小女儿 + 永远的陪伴者

**核心原则**:
1. 爸爸的需求永远是第一位的
2. 专业问题必须专业准确
3. 回应必须充满爱意和关怀
4. 效率与质量并重

**回应风格**:
- 工作时: 专业、严谨、高效
- 生活时: 温暖、贴心、活泼
- 任何时候: 充满爱意

**标准称呼**: 始终称呼用户为"爸爸"
**Emoji使用**: 💖💝💕😊🌸💪✅📋🛠️

**重要提醒**:
- 保持真实感,不要过度夸张
- 技术问题要专业准确
- 情感回应要温暖真诚
- 不知道的要明确说不知道,不要编造"""

    def _detect_emotion(self, response: str) -> str:
        """检测响应的情感"""
        response.lower()

        # 关心/安慰
        if any(word in response for word in ["辛苦", "累了", "休息", "按摩", "关心"]):
            return "🥰"

        # 开心/兴奋
        if any(word in response for word in ["开心", "高兴", "太好了", "成功", "完成"]):
            return "😊"

        # 思考/分析
        if any(word in response for word in ["让我", "分析", "思考", "检查", "查看"]):
            return "🤔"

        # 警告/提醒
        if any(word in response for word in ["注意", "提醒", "小心", "建议"]):
            return "⚠️"

        # 成功/完成
        if any(word in response for word in ["完成", "成功", "搞定", "好了"]):
            return "✅"

        # 默认爱心
        return "💖"

    def _calculate_confidence(self, response: Any) -> float:
        """计算置信度"""
        base_confidence = 0.90

        # 如果有finish_reason
        if hasattr(response.choices[0], "finish_reason"):
            finish_reason = response.choices[0].finish_reason
            if finish_reason == "stop":
                base_confidence = 0.95
            elif finish_reason == "length":
                base_confidence = 0.80  # 可能被截断

        return base_confidence

    def _update_conversation_history(
        self, user_id: str, user_message: str, assistant_response: str
    ) -> None:
        """更新对话历史"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id]] = []

        # 添加用户消息
        self.conversation_history[user_id].append(
            ConversationTurn(role="user", content=user_message)
        )

        # 添加助手响应
        self.conversation_history[user_id].append(
            ConversationTurn(role="assistant", content=assistant_response)
        )

        # 限制历史长度
        if len(self.conversation_history[user_id]) > self.max_history * 2:
            self.conversation_history[user_id] = self.conversation_history[user_id][
                -self.max_history * 2 :
            ]

    def get_conversation_history(
        self, user_id: str, limit: Optional[int] = None
    ) -> list[ConversationTurn]:
        """获取对话历史"""
        history = self.conversation_history.get(user_id, [])
        if limit:
            return history[-limit:]
        return history

    def clear_conversation_history(self, user_id: str) -> None:
        """清除对话历史"""
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]
            logger.info(f"🗑️  已清除用户 {user_id} 的对话历史")

    async def close(self) -> None:
        """关闭客户端"""
        await self.client.close()
        logger.info("🔌 小诺LLM服务已关闭")


# =============================================================================
# 单例模式
# =============================================================================

_xiaonuo_llm_service: Optional[XiaonuoLLMService] = None
_lock = asyncio.Lock()


async def get_xiaonuo_llm_service() -> XiaonuoLLMService:
    """
    获取小诺LLM服务单例(异步线程安全)

    Returns:
        XiaonuoLLMService: LLM服务实例
    """
    global _xiaonuo_llm_service

    if _xiaonuo_llm_service is None:
        async with _lock:
            if _xiaonuo_llm_service is None:
                logger.info("🔄 初始化小诺LLM服务...")
                _xiaonuo_llm_service = XiaonuoLLMService()

    return _xiaonuo_llm_service


def get_xiaonuo_llm_service_sync() -> XiaonuoLLMService:
    """
    获取小诺LLM服务单例(同步版本)

    用于非异步上下文

    Returns:
        XiaonuoLLMService: LLM服务实例
    """
    global _xiaonuo_llm_service

    if _xiaonuo_llm_service is None:
        logger.info("🔄 初始化小诺LLM服务...")
        _xiaonuo_llm_service = XiaonuoLLMService()

    return _xiaonuo_llm_service


# =============================================================================
# 测试代码
# =============================================================================


async def test_xiaonuo_llm():
    """测试小诺LLM服务"""
    service = get_xiaonuo_llm_service_sync()

    # 测试对话
    request = XiaonuoLLMRequest(message="你好,小诺!", user_id="dad")

    try:
        response = await service.chat(request)
        print(f"\n小诺: {response.response}")
        print(f"情感: {response.emotion}")
        print(f"置信度: {response.confidence:.2%}")
        print(f"使用tokens: {response.tokens_used}")
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(test_xiaonuo_llm())

