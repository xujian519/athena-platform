#!/usr/bin/env python3
"""
感知模块
Perception Module

小娜智能体的感知系统

作者: 小娜·天秤女神
创建时间: 2024年12月15日
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .business_classifier import BusinessClassifier
from .legal_nlp_processor import LegalNLPProcessor

logger = logging.getLogger(__name__)

class PerceptionModule:
    """感知模块主类"""

    def __init__(self):
        """初始化感知模块"""
        self.nlp_processor = LegalNLPProcessor()
        self.business_classifier = BusinessClassifier()
        self.initialized = False

    async def initialize(self):
        """初始化感知模块"""
        try:
            await self.nlp_processor.initialize()
            await self.business_classifier.initialize()
            self.initialized = True
            logger.info("✅ 感知模块初始化完成")
        except Exception as e:
            logger.error(f"❌ 感知模块初始化失败: {str(e)}")
            self.initialized = True  # 即使失败也标记为已初始化，使用默认功能

    async def perceive(self, text: str, context: dict | None = None) -> dict[str, Any]:
        """
        感知处理

        Args:
            text: 输入文本
            context: 上下文信息

        Returns:
            感知结果
        """
        try:
            # NLP处理
            nlp_result = await self.nlp_processor.process(text)

            # 业务分类
            business_result = await self.business_classifier.classify(text, context)

            # 合并结果
            perception_result = {
                "text": text,
                "nlp_analysis": nlp_result,
                "business_type": business_result.get("type", "unknown"),
                "business_confidence": business_result.get("confidence", 0),
                "context": context or {},
                "keywords": self._extract_keywords(text),
                "timestamp": datetime.now().isoformat()
            }

            return perception_result

        except Exception as e:
            logger.error(f"感知处理失败: {str(e)}")
            return {
                "text": text,
                "nlp_analysis": {},
                "business_type": "unknown",
                "business_confidence": 0,
                "context": context or {},
                "keywords": [],
                "error": str(e)
            }

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        # 简化的关键词提取
        keywords = []
        key_terms = ["专利", "发明", "商标", "版权", "合同", "侵权", "申请", "保护"]

        for term in key_terms:
            if term in text:
                keywords.append(term)

        return keywords

__all__ = ['PerceptionModule', 'LegalNLPProcessor', 'BusinessClassifier']
