#!/usr/bin/env python3
from __future__ import annotations
"""
任务分类器
Task Classifier - 识别任务类型(专业任务 vs 通用任务)

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 1"
"""

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TaskCategory(Enum):
    """任务分类"""

    PROFESSIONAL = "professional"  # 专业任务(需要查询规则)
    GENERAL = "general"  # 通用任务(智能推理)


class TaskDomain(Enum):
    """任务领域"""

    PATENT = "patent"  # 专利
    LEGAL = "legal"  # 法律
    TRADEMARK = "trademark"  # 商标
    COPYRIGHT = "copyright"  # 版权
    DEVELOPMENT = "development"  # 开发
    WRITING = "writing"  # 写作
    ANALYSIS = "analysis"  # 分析
    RESEARCH = "research"  # 检索
    MANAGEMENT = "management"  # 管理
    GENERAL = "general"  # 通用


@dataclass
class TaskClassification:
    """任务分类结果"""

    category: TaskCategory  # 分类:专业/通用
    domain: TaskDomain | None  # 领域
    confidence: float  # 置信度 (0-1)
    reasoning: str  # 分类理由
    suggested_agent: Optional[str]  # 建议的Agent
    requires_rules: bool  # 是否需要查询规则


class TaskClassifier:
    """任务分类器"""

    # 专业任务关键词
    PROFESSIONAL_KEYWORDS = {
        TaskDomain.PATENT: [
            "专利",
            "patent",
            "发明",
            "实用新型",
            "外观设计",
            "审查",
            "新颖性",
            "创造性",
            "实用性",
            "专利申请",
            "专利检索",
            "专利分析",
            "专利无效",
            "专利复审",
        ],
        TaskDomain.LEGAL: [
            "法律",
            "legal",
            "诉讼",
            "合同",
            "法规",
            "法条",
            "审判",
            "判决",
            "仲裁",
            "合规",
            "法律意见",
            "案件分析",
            "法律咨询",
            "合同审查",
        ],
        TaskDomain.TRADEMARK: [
            "商标",
            "trademark",
            "品牌",
            "logo",
            "商标注册",
            "商标侵权",
            "商标异议",
            "商标复审",
            "近似商标",
        ],
        TaskDomain.COPYRIGHT: [
            "版权",
            "copyright",
            "著作权",
            "侵权",
            "原创",
            "作品登记",
            "版权保护",
            "版权交易",
        ],
    }

    # 通用任务关键词
    GENERAL_KEYWORDS = [
        "写代码",
        "编程",
        "开发",
        "debug",
        "优化",
        "写文章",
        "总结",
        "翻译",
        "整理",
        "计划",
        "安排",
        "提醒",
        "管理",
    ]

    def __init__(self):
        """初始化分类器"""
        logger.info("🧠 任务分类器初始化完成")
        logger.info(f"   支持的领域: {len(list(TaskDomain))}个")
        logger.info(
            f"   专业关键词库: {sum(len(kw) for kw in self.PROFESSIONAL_KEYWORDS.values())}个"
        )

    async def classify(self, task_description: str) -> TaskClassification:
        """
        分类任务

        Args:
            task_description: 任务描述

        Returns:
            TaskClassification: 分类结果
        """
        logger.info(f"🔍 开始分类任务: {task_description[:50]}...")

        # 1. 检查是否是专业任务
        domain, confidence = self._detect_domain(task_description)

        if domain and confidence > 0.6:
            # 专业任务
            category = TaskCategory.PROFESSIONAL
            reasoning = f"检测到专业领域关键词: {domain.value},置信度{confidence:.2f}"
            suggested_agent = self._suggest_professional_agent(domain)
            requires_rules = True
        else:
            # 通用任务
            category = TaskCategory.GENERAL
            domain = TaskDomain.GENERAL
            confidence = 0.8 if confidence < 0.6 else confidence
            reasoning = "未检测到专业领域关键词,归类为通用任务"
            suggested_agent = "xiaonuo"  # 诺诺处理通用任务
            requires_rules = False

        result = TaskClassification(
            category=category,
            domain=domain,
            confidence=confidence,
            reasoning=reasoning,
            suggested_agent=suggested_agent,
            requires_rules=requires_rules,
        )

        logger.info(
            f"✅ 分类完成: {category.value} - {domain.value if domain else 'N/A'} (置信度: {confidence:.2f})"
        )

        return result

    def _detect_domain(self, task_description: str) -> tuple[TaskDomain | None, float]:
        """
        检测任务领域

        Returns:
            (domain, confidence): 领域和置信度
        """
        task_lower = task_description.lower()

        # 检查每个专业领域
        best_domain = None
        best_score = 0

        for domain, keywords in self.PROFESSIONAL_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in task_lower:
                    score += 1

            if score > best_score:
                best_score = score
                best_domain = domain

        # 计算置信度
        if best_score > 0:
            confidence = min(best_score / 3.0, 1.0)  # 最多3个关键词就100%
            return best_domain, confidence

        return None, 0.0

    def _suggest_professional_agent(self, domain: TaskDomain) -> str:
        """建议专业Agent"""
        agent_mapping = {
            TaskDomain.PATENT: "xiaona",  # 小娜·天秤女神
            TaskDomain.LEGAL: "xiaona",  # 小娜也处理法律
            TaskDomain.TRADEMARK: "xiaona",  # 小娜也处理商标
            TaskDomain.COPYRIGHT: "xiaona",  # 小娜也处理版权
        }
        return agent_mapping.get(domain, "xiaona")

    def batch_classify(self, tasks: list[str]) -> list[TaskClassification]:
        """批量分类任务"""
        import asyncio

        return asyncio.run(self._batch_classify(tasks))

    async def _batch_classify(self, tasks: list[str]) -> list[TaskClassification]:
        """异步批量分类"""
        results = []
        for task in tasks:
            result = await self.classify(task)
            results.append(result)
        return results


# 便捷函数
async def classify_task(task_description: str) -> TaskClassification:
    """
    便捷的任务分类函数

    Args:
        task_description: 任务描述

    Returns:
        TaskClassification: 分类结果

    Example:
        >>> result = await classify_task("帮我审查专利的新颖性")
        >>> print(result.category)
        TaskCategory.PROFESSIONAL
        >>> print(result.domain)
        TaskDomain.PATENT
    """
    classifier = TaskClassifier()
    return await classifier.classify(task_description)


__all__ = ["TaskCategory", "TaskClassification", "TaskClassifier", "TaskDomain", "classify_task"]
