#!/usr/bin/env python3
"""
学习引擎 - 经验存储器
Learning Engine - Experience Store

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

from __future__ import annotations
import json
import logging
from collections import deque
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class ExperienceStore:
    """经验存储器"""

    def __init__(self, max_experiences: int = 10000):
        self.max_experiences = max_experiences
        self.experiences = deque(maxlen=max_experiences)
        self.experience_index: dict[str, list[int]] = {}  # 经验索引
        self.pattern_cache: dict[str, Any] = {}  # 模式缓存

    def add_experience(self, experience: dict[str, Any]) -> None:
        """添加经验"""
        experience_id = len(self.experiences)
        experience["id"] = experience_id
        experience["timestamp"] = datetime.now()

        self.experiences.append(experience)

        # 更新索引
        context_key = self._generate_context_key(experience.get("context", {}))
        if context_key not in self.experience_index:
            self.experience_index[context_key] = []
        self.experience_index[context_key].append(experience_id)

        logger.debug(f"添加经验 #{experience_id}: {experience.get('type', 'unknown')}")

    def get_similar_experiences(
        self, context: dict[str, Any], limit: int = 10
    ) -> list[dict[str, Any]]:
        """获取相似经验"""
        context_key = self._generate_context_key(context)
        if context_key not in self.experience_index:
            return []

        experience_ids = self.experience_index[context_key]
        experiences = [self.experiences[eid] for eid in experience_ids]

        # 按时间排序,获取最新的经验
        experiences.sort(key=lambda x: x["timestamp"], reverse=True)
        return experiences[:limit]

    def _generate_context_key(self, context: dict[str, Any]) -> str:
        """生成上下文键"""
        return json.dumps(context, sort_keys=True)


__all__ = ["ExperienceStore"]
