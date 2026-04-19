#!/usr/bin/env python3
from __future__ import annotations
"""
失败案例学习系统

从失败的Agent执行中学习，改进未来的决策。

Author: Athena平台团队
Created: 2026-01-20
Version: v1.0.0
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class FailureType(str, Enum):
    """失败类型"""
    TOOL_ERROR = "tool_error"  # 工具执行错误
    TIMEOUT = "timeout"  # 超时
    INVALID_INPUT = "invalid_input"  # 无效输入
    MISSING_DEPENDENCY = "missing_dependency"  # 缺少依赖
    PERMISSION_DENIED = "permission_denied"  # 权限不足
    RESOURCE_UNAVAILABLE = "resource_unavailable"  # 资源不可用
    LOGIC_ERROR = "logic_error"  # 逻辑错误
    UNKNOWN = "unknown"  # 未知错误


@dataclass
class FailureCase:
    """
    失败案例

    记录一次失败执行的详细信息，用于学习和改进。
    """
    case_id: str
    timestamp: datetime
    task_description: str
    task_type: str
    failure_type: FailureType

    # 上下文信息
    context: dict[str, Any] = field(default_factory=dict)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    error_message: str | None = None
    stack_trace: str | None = None

    # 学习信息
    learned_lessons: list[str] = field(default_factory=list)
    suggested_fixes: list[str] = field(default_factory=list)

    # 统计信息
    occurrence_count: int = 1
    last_occurrence: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "case_id": self.case_id,
            "timestamp": self.timestamp.isoformat(),
            "task_description": self.task_description,
            "task_type": self.task_type,
            "failure_type": self.failure_type.value,
            "context": self.context,
            "tool_calls": self.tool_calls,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "learned_lessons": self.learned_lessons,
            "suggested_fixes": self.suggested_fixes,
            "occurrence_count": self.occurrence_count,
            "last_occurrence": self.last_occurrence.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'FailureCase':
        """从字典创建实例"""
        return cls(
            case_id=data["case_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            task_description=data["task_description"],
            task_type=data["task_type"],
            failure_type=FailureType(data["failure_type"]),
            context=data.get("context", {}),
            tool_calls=data.get("tool_calls", []),
            error_message=data.get("error_message"),
            stack_trace=data.get("stack_trace"),
            learned_lessons=data.get("learned_lessons", []),
            suggested_fixes=data.get("suggested_fixes", []),
            occurrence_count=data.get("occurrence_count", 1),
            last_occurrence=datetime.fromisoformat(
                data.get("last_occurrence", datetime.now().isoformat())
            )
        )

    def record_occurrence(self) -> None:
        """记录再次发生"""
        self.occurrence_count += 1
        self.last_occurrence = datetime.now()

    def add_lesson(self, lesson: str) -> None:
        """添加学习心得"""
        if lesson not in self.learned_lessons:
            self.learned_lessons.append(lesson)

    def add_fix_suggestion(self, suggestion: str) -> None:
        """添加修复建议"""
        if suggestion not in self.suggested_fixes:
            self.suggested_fixes.append(suggestion)


class FailureAnalyzer:
    """
    失败分析器

    分析失败案例，提取经验教训和修复建议。
    """

    def __init__(self):
        """初始化失败分析器"""
        self.logger = logger

        # 常见错误模式及其解决方案
        self.error_patterns = {
            # 工具错误模式
            r"tool.*not found": {
                "lesson": "工具名称可能拼写错误或未注册",
                "fix": "检查工具名称是否正确，确认工具已注册到ToolRegistry"
            },
            r"timeout": {
                "lesson": "操作超时，可能需要增加超时时间或优化性能",
                "fix": "增加超时时间，或者优化工具性能，或者使用异步执行"
            },
            r"permission denied": {
                "lesson": "权限不足，需要更高权限或正确的API密钥",
                "fix": "检查API密钥和权限配置，确保有足够的权限"
            },
            r"connection.*refused": {
                "lesson": "服务不可用，可能未启动或网络问题",
                "fix": "检查服务是否启动，网络连接是否正常"
            },
            r"invalid.*input": {
                "lesson": "输入参数验证失败",
                "fix": "检查输入参数格式和内容，确保符合工具要求"
            },
            # 逻辑错误模式
            r"key.*not found": {
                "lesson": "字典或对象中缺少预期的键",
                "fix": "检查数据结构，使用.get()或hasattr()进行防御性编程"
            },
            r"index.*out of range": {
                "lesson": "列表或数组索引越界",
                "fix": "检查索引范围，确保在有效范围内"
            },
            r"attribute.*not found": {
                "lesson": "对象缺少预期属性",
                "fix": "检查对象类型，使用hasattr()检查属性是否存在"
            }
        }

    def analyze_failure(
        self,
        task_description: str,
        error_message: str,
        stack_trace: str,
        context: dict[str, Any]
    ) -> FailureCase:
        """
        分析失败案例

        Args:
            task_description: 任务描述
            error_message: 错误消息
            stack_trace: 堆栈跟踪
            context: 上下文信息

        Returns:
            失败案例对象
        """
        import hashlib
        import re

        # 生成case_id
        case_hash = hashlib.md5(
            f"{task_description}:{error_message}".encode(),
            usedforsecurity=False
        ).hexdigest()[:8]
        case_id = f"failure_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{case_hash}"

        # 确定失败类型
        failure_type = self._classify_failure(error_message, stack_trace)

        # 分析错误模式
        learned_lessons = []
        suggested_fixes = []

        error_text = f"{error_message} {stack_trace}".lower()

        for pattern, solution in self.error_patterns.items():
            if re.search(pattern, error_text):
                learned_lessons.append(solution["lesson"])
                suggested_fixes.append(solution["fix"])

        # 如果没有匹配的模式，使用通用建议
        if not learned_lessons:
            learned_lessons.append("未知的失败模式，需要人工分析")
            suggested_fixes.append("检查错误日志和堆栈跟踪，分析根本原因")

        # 创建失败案例
        case = FailureCase(
            case_id=case_id,
            timestamp=datetime.now(),
            task_description=task_description,
            task_type=context.get("task_type", "unknown"),
            failure_type=failure_type,
            context=context,
            tool_calls=context.get("tool_calls", []),
            error_message=error_message,
            stack_trace=stack_trace,
            learned_lessons=learned_lessons,
            suggested_fixes=suggested_fixes
        )

        self.logger.info(
            f"📚 分析失败案例: {case_id} "
            f"(类型: {failure_type.value}, 教训: {len(learned_lessons)}条)"
        )

        return case

    def _classify_failure(self, error_message: str, stack_trace: str) -> FailureType:
        """
        分类失败类型

        Args:
            error_message: 错误消息
            stack_trace: 堆栈跟踪

        Returns:
            失败类型
        """
        error_text = f"{error_message} {stack_trace}".lower()

        if "timeout" in error_text:
            return FailureType.TIMEOUT
        elif "permission" in error_text or "unauthorized" in error_text:
            return FailureType.PERMISSION_DENIED
        elif "not found" in error_text and "tool" in error_text:
            return FailureType.TOOL_ERROR
        elif "invalid" in error_text and "input" in error_text:
            return FailureType.INVALID_INPUT
        elif "connection" in error_text or "refused" in error_text:
            return FailureType.RESOURCE_UNAVAILABLE
        elif "key" in error_text or "index" in error_text or "attribute" in error_text:
            return FailureType.LOGIC_ERROR
        else:
            return FailureType.UNKNOWN


class FailureKnowledgeBase:
    """
    失败案例知识库

    存储、检索和学习失败案例。
    """

    def __init__(self, storage_path: str = "data/failure_knowledge"):
        """
        初始化失败案例知识库

        Args:
            storage_path: 存储路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.cases: dict[str, FailureCase] = {}
        self.analyzer = FailureAnalyzer()

        # 加载已有案例
        self._load_cases()

    def _load_cases(self) -> None:
        """加载已有案例"""
        cases_dir = self.storage_path / "cases"
        if not cases_dir.exists():
            cases_dir.mkdir(parents=True, exist_ok=True)
            return

        case_files = list(cases_dir.glob("*.json"))
        for case_file in case_files:
            try:
                with open(case_file, encoding='utf-8') as f:
                    data = json.load(f)

                case = FailureCase.from_dict(data)
                self.cases[case.case_id] = case

            except Exception as e:
                self.logger.error(f"❌ 加载案例失败: {case_file.name}, 错误: {e}")

        self.logger.info(f"📂 已加载{len(self.cases)}个失败案例")

    def record_failure(
        self,
        task_description: str,
        error_message: str,
        stack_trace: str,
        context: dict[str, Any]
    ) -> FailureCase:
        """
        记录并分析失败案例

        Args:
            task_description: 任务描述
            error_message: 错误消息
            stack_trace: 堆栈跟踪
            context: 上下文信息

        Returns:
            失败案例对象
        """
        # 分析失败
        case = self.analyzer.analyze_failure(
            task_description=task_description,
            error_message=error_message,
            stack_trace=stack_trace,
            context=context
        )

        # 检查是否已有类似案例
        similar_case = self._find_similar_case(case)
        if similar_case:
            # 更新现有案例
            similar_case.record_occurrence()
            # 合并学习心得
            for lesson in case.learned_lessons:
                if lesson not in similar_case.learned_lessons:
                    similar_case.learned_lessons.append(lesson)
            # 合并修复建议
            for fix in case.suggested_fixes:
                if fix not in similar_case.suggested_fixes:
                    similar_case.suggested_fixes.append(fix)

            self._save_case(similar_case)
            self.logger.info(f"🔄 更新已有案例: {similar_case.case_id}")
            return similar_case
        else:
            # 新案例
            self.cases[case.case_id] = case
            self._save_case(case)
            return case

    def _find_similar_case(self, new_case: FailureCase) -> FailureCase | None:
        """
        查找相似的失败案例

        Args:
            new_case: 新案例

        Returns:
            相似案例，如果找不到则返回None
        """
        for case in self.cases.values():
            # 相同任务类型和错误类型
            if (case.task_type == new_case.task_type and
                case.failure_type == new_case.failure_type):
                # 错误消息相似度检查（简单版本）
                if (case.error_message and new_case.error_message and
                    case.error_message.split()[0] == new_case.error_message.split()[0]):
                    return case

        return None

    def _save_case(self, case: FailureCase) -> None:
        """保存案例到文件"""
        cases_dir = self.storage_path / "cases"
        cases_dir.mkdir(parents=True, exist_ok=True)

        case_file = cases_dir / f"{case.case_id}.json"

        with open(case_file, 'w', encoding='utf-8') as f:
            json.dump(case.to_dict(), f, ensure_ascii=False, indent=2)

        self.logger.debug(f"💾 案例已保存: {case_file}")

    def get_similar_failures(
        self,
        task_description: str,
        task_type: str,
        limit: int = 5
    ) -> list[FailureCase]:
        """
        获取相似的失败案例

        Args:
            task_description: 任务描述
            task_type: 任务类型
            limit: 返回数量限制

        Returns:
            相似案例列表，按发生次数排序
        """
        similar_cases = []

        for case in self.cases.values():
            if case.task_type == task_type:
                # 简单的关键词匹配
                task_words = set(task_description.lower().split())
                case_words = set(case.task_description.lower().split())

                overlap = task_words & case_words
                if overlap:
                    similar_cases.append((len(overlap), case))

        # 按相似度和发生次数排序
        similar_cases.sort(key=lambda x: (x[0], x[1].occurrence_count), reverse=True)

        return [case for _, case in similar_cases[:limit]]

    def get_lessons_learned(
        self,
        failure_type: FailureType | None = None
    ) -> list[str]:
        """
        获取经验教训

        Args:
            failure_type: 失败类型过滤器，None表示全部

        Returns:
            经验教训列表
        """
        lessons = []

        for case in self.cases.values():
            if failure_type is None or case.failure_type == failure_type:
                lessons.extend(case.learned_lessons)

        # 去重
        seen = set()
        unique_lessons = []
        for lesson in lessons:
            if lesson not in seen:
                seen.add(lesson)
                unique_lessons.append(lesson)

        return unique_lessons

    def get_statistics(self) -> dict[str, Any]:
        """获取知识库统计信息"""
        total_cases = len(self.cases)
        type_counts = {}
        total_occurrences = 0

        for case in self.cases.values():
            type_str = case.failure_type.value
            type_counts[type_str] = type_counts.get(type_str, 0) + 1
            total_occurrences += case.occurrence_count

        # 最常见的失败类型
        sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)

        return {
            "total_cases": total_cases,
            "total_occurrences": total_occurrences,
            "failure_types": type_counts,
            "most_common_failures": sorted_types[:5]
        }


__all__ = [
    'FailureAnalyzer',
    'FailureCase',
    'FailureKnowledgeBase',
    'FailureType'
]
