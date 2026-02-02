#!/usr/bin/env python3
"""
增强型NLP适配器 - 优化认知引擎与GLM-4.6的交互
Enhanced NLP Adapter - Optimizes interaction between cognition engine and GLM-4.6
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class NLPResponse:
    """NLP响应数据结构"""

    content: str
    confidence: float
    provider: str
    task_type: str
    metadata: dict[str, Any] | None = None
    timestamp: datetime = None


class EnhancedNLPAdapter:
    """增强型NLP适配器"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.nlp_service = None
        self.response_cache: dict[str, Any] = {}
        self.cache_ttl = timedelta(minutes=30)
        self.initialized = False

        # 统计信息
        self.stats = {"total_requests": 0, "cache_hits": 0, "response_times": [], "task_types": {}}

    async def initialize(self):
        """初始化增强型NLP适配器"""
        try:
            import os
            import sys

            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from nlp.universal_nlp_provider import get_nlp_service

            self.nlp_service = await get_nlp_service(self.config)
            self.initialized = True
            logger.info("✅ 增强型NLP适配器初始化成功")
        except Exception as e:
            logger.error(f"增强型NLP适配器初始化失败: {e}")
            self.nlp_service = None
            self.initialized = False

    def _get_cache_key(self, text: str, task_type: str) -> str:
        """生成缓存键"""
        import hashlib

        content = f"{task_type}:{text[:100]}"
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()

    def _get_from_cache(self, cache_key: str) -> NLPResponse | None:
        """从缓存获取响应"""
        if cache_key in self.response_cache:
            cached = self.response_cache[cache_key]
            if datetime.now() - cached.timestamp < self.cache_ttl:
                self.stats["cache_hits"] += 1
                return cached
            else:
                del self.response_cache[cache_key]
        return None

    def _store_in_cache(self, cache_key: str, response: NLPResponse) -> Any:
        """存储响应到缓存"""
        # 限制缓存大小
        if len(self.response_cache) > 1000:
            # 删除最旧的缓存项
            oldest_key = min(
                self.response_cache.keys(), key=lambda k: self.response_cache[k].timestamp
            )
            del self.response_cache[oldest_key]

        self.response_cache[cache_key] = response

    async def process_with_cache(self, text: str, task_type: str, **kwargs) -> NLPResponse:
        """带缓存的处理"""
        start_time = datetime.now()
        self.stats["total_requests"] += 1

        # 检查缓存
        cache_key = self._get_cache_key(text, task_type)
        cached_response = self._get_from_cache(cache_key)
        if cached_response:
            return cached_response

        # 处理请求
        response = await self._process_task(text, task_type, **kwargs)

        # 存储到缓存
        self._store_in_cache(cache_key, response)

        # 更新统计
        response_time = (datetime.now() - start_time).total_seconds()
        self.stats["response_times"].append(response_time)
        if task_type not in self.stats["task_types"]:
            self.stats["task_types"][task_type] = 0
        self.stats["task_types"][task_type] += 1

        return response

    async def _process_task(self, text: str, task_type: str, **kwargs) -> NLPResponse:
        """处理特定任务"""
        if not self.nlp_service:
            # 降级处理
            return NLPResponse(
                content=f"NLP服务不可用,文本:{text[:100]}...",
                confidence=0.5,
                provider="fallback",
                task_type=task_type,
                timestamp=datetime.now(),
            )

        try:
            from nlp.universal_nlp_provider import TaskType

            # 映射任务类型
            task_mapping = {
                "patent_analysis": TaskType.PATENT_ANALYSIS,
                "technical_reasoning": TaskType.TECHNICAL_REASONING,
                "emotional_analysis": TaskType.EMOTIONAL_ANALYSIS,
                "creative_writing": TaskType.CREATIVE_WRITING,
                "conversation": TaskType.CONVERSATION,
                "summarization": TaskType.SUMMARIZATION,
                "translation": TaskType.TRANSLATION,
            }

            nlp_task_type = task_mapping.get(task_type, TaskType.CONVERSATION)

            # 调用NLP服务
            result = await self.nlp_service.process(text, nlp_task_type, **kwargs)

            if result.get("success", False):
                return NLPResponse(
                    content=result.get("content", ""),
                    confidence=result.get("confidence", 0.8),
                    provider=result.get("provider", "unknown"),
                    task_type=task_type,
                    metadata=result.get("metadata", {}),
                    timestamp=datetime.now(),
                )
            else:
                # 使用降级响应
                fallback_content = result.get("content", f"无法处理:{text[:100]}...")
                return NLPResponse(
                    content=fallback_content,
                    confidence=0.3,
                    provider="fallback",
                    task_type=task_type,
                    timestamp=datetime.now(),
                )

        except Exception as e:
            logger.error(f"NLP处理失败: {e}")
            return NLPResponse(
                content=f"处理失败:{e!s}",
                confidence=0.0,
                provider="error",
                task_type=task_type,
                timestamp=datetime.now(),
            )

    async def analyze_patent_enhanced(self, patent_text: str) -> dict[str, Any]:
        """增强的专利分析"""
        response = await self.process_with_cache(patent_text, "patent_analysis")

        # 解析GLM-4.6的结构化响应
        if response.provider == "GLM-4.6" and response.content:
            try:
                # 尝试解析JSON格式的分析结果
                if "{" in response.content and "}" in response.content:
                    # 提取JSON部分
                    start = response.content.find("{")
                    end = response.content.rfind("}") + 1
                    json_str = response.content[start: end,
                    analysis = json.loads(json_str)
                else:
                    # 纯文本分析,自动提取要点
                    analysis = {
                        "summary": response.content[:200] + "...",
                        "key_points": self._extract_key_points(response.content),
                        "confidence": response.confidence,
                    }
            except (json.JSONDecodeError, TypeError, ValueError):
                analysis = {
                    "summary": response.content,
                    "key_points": [],
                    "confidence": response.confidence,
                }
        else:
            analysis = {
                "summary": response.content,
                "key_points": [],
                "confidence": response.confidence,
            }

        return {
            "success": True,
            "provider": response.provider,
            "analysis": analysis,
            "metadata": response.metadata,
        }

    def _extract_key_points(self, text: str) -> list[str]:
        """从文本中提取关键点"""
        # 简单的关键点提取逻辑
        keywords = ["创新点", "技术要点", "优势", "应用场景", "实施方式"]
        points = []

        for keyword in keywords:
            if keyword in text:
                # 提取关键词后的句子
                idx = text.find(keyword)
                if idx != -1:
                    # 找到句号或换行
                    end = text.find("。", idx)
                    if end == -1:
                        end = text.find("\n", idx)
                    if end != -1 and end - idx < 100:
                        point = text[idx : end + 1].strip()
                        points.append(point)

        return points[:5]  # 最多返回5个关键点

    async def emotional_analysis_enhanced(self, text: str, context: str = "") -> dict[str, Any]:
        """增强的情感分析"""
        # 构建更丰富的上下文
        full_text = f"{context}\n\n{text}" if context else text

        response = await self.process_with_cache(full_text, "emotional_analysis")

        # 解析情感分析结果
        if response.provider == "GLM-4.6":
            # GLM-4.6返回详细分析
            emotion_data = {
                "primary_emotion": "positive",  # 默认值
                "emotion_intensity": 0.7,
                "emotional_complexity": "rich",
                "detailed_analysis": response.content,
                "confidence": response.confidence,
            }

            # 尝试从响应中提取情感标签
            content_lower = response.content.lower()
            if "开心" in content_lower or "高兴" in content_lower or "快乐" in content_lower:
                emotion_data["primary_emotion"] = "happy"
            elif "难过" in content_lower or "伤心" in content_lower or "悲伤" in content_lower:
                emotion_data["primary_emotion"] = "sad"
            elif "爱" in content_lower or "喜欢" in content_lower:
                emotion_data["primary_emotion"] = "love"
        else:
            # 基础情感分析
            emotion_data = {
                "primary_emotion": "neutral",
                "emotion_intensity": 0.5,
                "emotional_complexity": "simple",
                "detailed_analysis": response.content,
                "confidence": response.confidence,
            }

        return {
            "success": True,
            "provider": response.provider,
            "emotion": emotion_data,
            "timestamp": response.timestamp.isoformat(),
        }

    async def creative_writing_enhanced(
        self, topic: str, style: str = "story", length: str = "medium"
    ) -> dict[str, Any]:
        """增强的创意写作"""
        # 构建详细的写作指令
        prompt = f"请写一篇关于'{topic}'的{style}"
        if length == "short":
            prompt += ",字数控制在200字以内"
        elif length == "long":
            prompt += ",字数不少于500字"

        response = await self.process_with_cache(prompt, "creative_writing")

        return {
            "success": True,
            "provider": response.provider,
            "content": response.content,
            "style": style,
            "length": length,
            "confidence": response.confidence,
            "metadata": response.metadata,
        }

    async def batch_process(self, tasks: list[dict[str, Any]) -> list[NLPResponse]:
        """批量处理任务"""
        # 并发处理多个任务
        semaphores = asyncio.Semaphore(5)  # 限制并发数

        async def process_single(task):
            async with semaphores:
                return await self.process_with_cache(
                    task["text"], task["task_type"], **task.get("kwargs", {})
                )

        return await asyncio.gather(*[process_single(task) for task in tasks])

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        avg_response_time = 0
        if self.stats["response_times"]:
            avg_response_time = sum(self.stats["response_times"]) / len(
                self.stats["response_times"]
            )

        cache_hit_rate = 0
        if self.stats["total_requests"] > 0:
            cache_hit_rate = self.stats["cache_hits"] / self.stats["total_requests"]

        return {
            "total_requests": self.stats["total_requests"],
            "cache_hits": self.stats["cache_hits"],
            "cache_hit_rate": f"{cache_hit_rate:.2%}",
            "average_response_time": f"{avg_response_time:.2f}s",
            "task_type_distribution": self.stats["task_types"],
            "cache_size": len(self.response_cache),
        }

    async def clear_cache(self):
        """清空缓存"""
        self.response_cache.clear()
        logger.info("缓存已清空")


# 导出
__all__ = ["EnhancedNLPAdapter", "NLPResponse"]
