#!/usr/bin/env python3
"""
轻量级请求处理器
Lightweight Request Processor

处理简单任务,避免使用重型AI模型
"""

import json
import re
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any



class TaskComplexity(Enum):
    """任务复杂度"""

    SIMPLE = "simple"  # 简单任务,无需AI
    MEDIUM = "medium"  # 中等任务,可使用轻量AI
    COMPLEX = "complex"  # 复杂任务,需要完整AI"


@dataclass
class ProcessingResult:
    """处理结果"""

    content: str
    complexity: TaskComplexity
    processing_time: float
    method: str  # "rule_based", "template", "ai_assisted"


class LightweightProcessor:
    """轻量级请求处理器"""

    def __init__(self):
        self.templates = self._load_templates()
        self.rule_handlers = self._load_rule_handlers()
        self.stats = {
            "total_requests": 0,
            "simple_handled": 0,
            "medium_handled": 0,
            "complex_handled": 0,
            "avg_response_time": 0.0,
        }

    def _load_templates(self) -> dict[str, str]:
        """加载响应模板"""
        return {
            "greeting": "您好!我是小诺,很高兴为您服务。有什么可以帮助您的吗?",
            "thanks": "不客气!很高兴能帮到您。还有其他问题吗?",
            "status_check": "✅ 系统运行正常,所有服务都在正常工作。",
            "time": f"当前时间是 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "help": """
我可以帮助您:
📋 任务管理和提醒
🔍 数据分析和检索
🤖 AI智能协作
📊 系统监控和优化

请告诉我您需要什么帮助!
            """.strip(),
            "task_status": "正在查询任务状态,请稍候...",
            "ping": "🏓 pong! 系统响应正常",
            "version": "Athena工作平台 v2.0 - 智能协作系统",
            "weather": "很抱歉,我暂时无法查询天气信息。建议您查看天气应用。",
        }

    def _load_rule_handlers(self) -> dict[str, callable]:
        """加载规则处理器"""
        return {
            "system_info": self._handle_system_info,
            "task_management": self._handle_task_management,
            "file_operations": self._handle_file_operations,
            "simple_qa": self._handle_simple_qa,
        }

    def analyze_complexity(self, request: str) -> TaskComplexity:
        """分析请求复杂度"""
        request_lower = request.lower()

        # 简单任务识别
        simple_patterns = [
            r"^(你好|hello|hi|hey)",
            r"^(谢谢|感谢|thank)",
            r"^(再见|bye|goodbye)",
            r".*状态.*检查|status.*check",
            r".*时间|time|date",
            r".*帮助|help|协助",
            r".*ping|测试|test",
            r".*版本|version",
        ]

        for pattern in simple_patterns:
            if re.search(pattern, request_lower):
                return TaskComplexity.SIMPLE

        # 中等复杂度任务
        medium_patterns = [
            r".*任务.*查询|task.*query",
            r".*简单.*分析|basic.*analysis",
            r".*文件.*列表|file.*list",
            r".*统计.*信息|statistics",
            r".*配置.*查看|config.*view",
        ]

        for pattern in medium_patterns:
            if re.search(pattern, request_lower):
                return TaskComplexity.MEDIUM

        # 其他都是复杂任务
        return TaskComplexity.COMPLEX

    def process_request(self, request: str, context: str = "") -> ProcessingResult:
        """处理请求"""
        start_time = time.time()
        self.stats["total_requests"] += 1

        complexity = self.analyze_complexity(request)

        if complexity == TaskComplexity.SIMPLE:
            result = self._process_simple_request(request)
            method = "rule_based"

        elif complexity == TaskComplexity.MEDIUM:
            result = self._process_medium_request(request)
            method = "template"

        else:
            # 复杂任务返回None,需要调用完整AI
            processing_time = time.time() - start_time
            self.stats["complex_handled"] += 1
            return ProcessingResult(
                content=None,
                complexity=TaskComplexity.COMPLEX,
                processing_time=processing_time,
                method="ai_required",
            )

        processing_time = time.time() - start_time

        # 更新统计
        if complexity == TaskComplexity.SIMPLE:
            self.stats["simple_handled"] += 1
        elif complexity == TaskComplexity.MEDIUM:
            self.stats["medium_handled"] += 1

        # 更新平均响应时间
        total_processed = self.stats["simple_handled"] + self.stats["medium_handled"]
        if total_processed > 0:
            self.stats["avg_response_time"] = (
                self.stats["avg_response_time"] * (total_processed - 1) + processing_time
            ) / total_processed

        return ProcessingResult(
            content=result, complexity=complexity, processing_time=processing_time, method=method
        )

    def _process_simple_request(self, request: str) -> str:
        """处理简单请求"""
        request_lower = request.lower()

        # 问候
        if re.search(r"^(你好|hello|hi|hey)", request_lower):
            return self.templates["greeting"]

        # 感谢
        elif re.search(r"^(谢谢|感谢|thank)", request_lower):
            return self.templates["thanks"]

        # 状态检查
        elif re.search(r".*状态.*检查|status.*check|运行.*状态", request_lower):
            return self.templates["status_check"]

        # 时间查询
        elif re.search(r".*时间|time|date|几点", request_lower):
            return self.templates["time"]

        # 帮助
        elif re.search(r".*帮助|help|协助|能.*做什么", request_lower):
            return self.templates["help"]

        # Ping测试
        elif re.search(r".*ping|测试|test", request_lower):
            return self.templates["ping"]

        # 版本信息
        elif re.search(r".*版本|version", request_lower):
            return self.templates["version"]

        else:
            return "我理解您的问题,但需要更详细的信息来帮助您。"

    def _process_medium_request(self, request: str) -> str:
        """处理中等复杂度请求"""
        request_lower = request.lower()

        # 任务相关
        if "任务" in request_lower and ("查询" in request_lower or "状态" in request_lower):
            return self._handle_task_management(request)

        # 系统信息
        elif "系统" in request_lower and ("信息" in request_lower or "状态" in request_lower):
            return self._handle_system_info(request)

        # 文件操作
        elif "文件" in request_lower:
            return self._handle_file_operations(request)

        else:
            return "正在处理您的请求,请稍候..."

    def _handle_system_info(self, request: str) -> str:
        """处理系统信息请求"""
        import psutil

        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存信息
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # 磁盘使用率
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100

            info = f"""
📊 系统信息:
💻 CPU使用率: {cpu_percent:.1f}%
🧠 内存使用率: {memory_percent:.1f}%
💾 磁盘使用率: {disk_percent:.1f}%
🔄 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ 系统运行正常
            """.strip()

            return info

        except Exception as e:
            return f"⚠️ 获取系统信息失败: {e!s}"

    def _handle_task_management(self, request: str) -> str:
        """处理任务管理请求"""
        try:
            # 这里可以集成实际的任务管理系统
            from core.tasks.enhanced_todo_write import get_todo_dashboard

            dashboard = get_todo_dashboard()

            info = f"""
📋 任务管理状态:
📝 总任务数: {dashboard.get('total', 0)}
✅ 已完成: {dashboard.get('completed', 0)}
⏳ 待处理: {dashboard.get('pending', 0)}
🔄 进行中: {dashboard.get('in_progress', 0)}
📈 完成率: {dashboard.get('completion_rate', 0):.1%}%
            """.strip()

            return info

        except Exception as e:
            return f"⚠️ 获取任务状态失败: {e!s}"

    def _handle_file_operations(self, request: str) -> str:
        """处理文件操作请求"""
        from pathlib import Path

        try:
            project_root = Path(__file__).parent.parent.parent
            python_files = list(project_root.glob("**/*.py"))
            json_files = list(project_root.glob("**/*.json"))

            info = f"""
📁 项目文件统计:
🐍 Python文件: {len(python_files)}
📄 JSON文件: {len(json_files)}
📂 项目目录: {project_root}

最近的文件更新请查看详细日志。
            """.strip()

            return info

        except Exception as e:
            return f"⚠️ 获取文件信息失败: {e!s}"

    def _handle_simple_qa(self, request: str) -> str:
        """处理简单问答"""
        qa_map = {
            "平台是什么": "Athena工作平台是一个智能协作系统,包含任务管理、AI分析等功能。",
            "如何使用": "您可以直接询问问题,系统会智能处理您的请求。",
            "联系谁": "您可以联系系统管理员获取帮助。",
        }

        for question, answer in qa_map.items():
            if question in request:
                return answer

        return "我理解您的问题,请提供更多详细信息。"

    def get_stats(self) -> dict[str, Any]:
        """获取处理统计"""
        total = self.stats["total_requests"]
        if total == 0:
            return self.stats

        return {
            **self.stats,
            "simple_rate": self.stats["simple_handled"] / total,
            "medium_rate": self.stats["medium_handled"] / total,
            "complex_rate": self.stats["complex_handled"] / total,
            "offload_rate": (self.stats["simple_handled"] + self.stats["medium_handled"]) / total,
        }


# 全局处理器实例
_lightweight_processor = None


def get_lightweight_processor() -> LightweightProcessor:
    """获取全局轻量级处理器实例"""
    global _lightweight_processor
    if _lightweight_processor is None:
        _lightweight_processor = LightweightProcessor()
    return _lightweight_processor


# 使用示例
if __name__ == "__main__":
    processor = LightweightProcessor()

    # 测试各种请求
    test_requests = [
        "你好",
        "系统状态检查",
        "任务查询",
        "帮我分析性能瓶颈",
        "当前时间",
    ]

    for request in test_requests:
        result = processor.process_request(request)
        print(f"请求: {request}")
        print(f"复杂度: {result.complexity.value}")
        print(f"处理方式: {result.method}")
        print(f"处理时间: {result.processing_time:.3f}s")
        print(f"响应: {result.content[:100]}...")
        print("-" * 50)

    # 显示统计
    stats = processor.get_stats()
    print(f"处理统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")
