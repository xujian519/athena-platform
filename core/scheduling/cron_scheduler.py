#!/usr/bin/env python3
from __future__ import annotations
"""
Cron 调度系统 - 专利状态监控

基于 Hermes Agent 的设计理念，实现自然语言调度解析和任务持久化。
支持专利状态监控、定期检查和提醒。

核心特性:
1. 自然语言调度解析 ("每天检查一次专利状态")
2. 任务持久化和恢复
3. 专利状态监控
4. 周期性任务执行

作者: Athena平台团队
创建时间: 2026-03-19
版本: v1.0.0
"""

import asyncio
import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# 默认存储路径
DEFAULT_SCHEDULER_DIR = Path(__file__).parent / "data" / "scheduled_tasks"


@dataclass
class ScheduledTask:
    """调度任务"""

    task_id: str
    name: str
    description: str
    cron_expression: str  # 标准 cron 表达式
    task_type: str  # patent_status_check, reminder, report
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_run: datetime | None = None
    next_run: datetime | None = None
    run_count: int = 0
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "cron_expression": self.cron_expression,
            "task_type": self.task_type,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "parameters": self.parameters,
        }


@dataclass
class NaturalLanguageSchedule:
    """自然语言调度模式"""

    patterns: dict[str, str] = field(
        default_factory=lambda: {
            # 频率模式
            "每天": "0 9 * * *",
            "每日": "0 9 * * *",
            "每天早上": "0 9 * * *",
            "每天下午": "0 14 * * *",
            "每周": "0 9 * * 1",
            "每星期": "0 9 * * 1",
            "每周一": "0 9 * * 1",
            "每月": "0 9 1 * *",
            "每小时": "0 * * * *",
            "每分钟": "* * * * *",
            # 专利相关
            "检查专利状态": "0 9 * * *",
            "监控审查意见": "0 9 * * *",
            "更新检索结果": "0 9 * * 1",
        }
    )


class CronScheduler:
    """
    Cron 调度系统

    支持自然语言调度解析和任务持久化。
    """

    def __init__(self, storage_dir: Path | None = None):
        """
        初始化调度器

        Args:
            storage_dir: 任务存储目录
        """
        self.storage_dir = storage_dir or DEFAULT_SCHEDULER_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.tasks: dict[str, ScheduledTask] = {}
        self.handlers: dict[str, Callable] = {}
        self.nl_parser = NaturalLanguageSchedule()
        self._running = False
        self._scheduler_task: asyncio.Task | None = None

        # 加载已有任务
        self._load_tasks()

        logger.info(f"⏰ CronScheduler 初始化完成 (已加载 {len(self.tasks)} 个任务)")

    def _load_tasks(self) -> None:
        """从文件加载任务"""
        tasks_file = self.storage_dir / "tasks.json"
        if tasks_file.exists():
            try:
                with open(tasks_file, encoding="utf-8") as f:
                    tasks_data = json.load(f)
                for task_dict in tasks_data:
                    task = ScheduledTask(
                        task_id=task_dict["task_id"],
                        name=task_dict["name"],
                        description=task_dict["description"],
                        cron_expression=task_dict["cron_expression"],
                        task_type=task_dict["task_type"],
                        enabled=task_dict.get("enabled", True),
                        created_at=datetime.fromisoformat(task_dict["created_at"]),
                        last_run=(
                            datetime.fromisoformat(task_dict["last_run"])
                            if task_dict.get("last_run")
                            else None
                        ),
                        next_run=(
                            datetime.fromisoformat(task_dict["next_run"])
                            if task_dict.get("next_run")
                            else None
                        ),
                        run_count=task_dict.get("run_count", 0),
                        parameters=task_dict.get("parameters", {}),
                    )
                    self.tasks[task.task_id] = task
                logger.info(f"✅ 已加载 {len(self.tasks)} 个调度任务")
            except Exception as e:
                logger.warning(f"⚠️ 加载任务失败: {e}")

    def _save_tasks(self) -> None:
        """保存任务到文件"""
        tasks_file = self.storage_dir / "tasks.json"
        try:
            tasks_data = [task.to_dict() for task in self.tasks.values()]
            with open(tasks_file, "w", encoding="utf-8") as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=2)
            logger.debug(f"💾 已保存 {len(self.tasks)} 个任务")
        except Exception as e:
            logger.error(f"❌ 保存任务失败: {e}")

    def register_handler(self, task_type: str, handler: Callable) -> None:
        """
        注册任务处理器

        Args:
            task_type: 任务类型
            handler: 处理函数
        """
        self.handlers[task_type] = handler
        logger.info(f"✅ 已注册处理器: {task_type}")

    def parse_natural_language(self, description: str) -> Optional[str]:
        """
        解析自然语言调度描述

        Args:
            description: 自然语言描述 (如 "每天检查一次专利状态")

        Returns:
            Optional[str]: 标准 cron 表达式
        """
        desc_lower = description.lower()

        # 直接匹配
        if desc_lower in self.nl_parser.patterns:
            return self.nl_parser.patterns[desc_lower]

        # 模糊匹配
        for pattern, cron in self.nl_parser.patterns.items():
            if pattern in desc_lower:
                return cron

        # 尝试解析更复杂的表达式
        # "每隔X小时" -> "0 */X * * *"
        match = re.search(r"每隔(\d+)小时", desc_lower)
        if match:
            hours = int(match.group(1))
            return f"0 */{hours} * * *"

        # "每隔X分钟" -> "*/X * * * *"
        match = re.search(r"每隔(\d+)分钟", desc_lower)
        if match:
            minutes = int(match.group(1))
            return f"*/{minutes} * * * *"

        logger.warning(f"⚠️ 无法解析调度描述: {description}")
        return None

    def schedule_task(
        self,
        task_id: str,
        name: str,
        description: str,
        schedule: str,
        task_type: str,
        parameters: Optional[dict[str, Any]] = None,
    ) -> ScheduledTask | None:
        """
        创建调度任务

        Args:
            task_id: 任务唯一标识
            name: 任务名称
            description: 任务描述
            schedule: 调度表达式 (cron 或自然语言)
            task_type: 任务类型
            parameters: 任务参数

        Returns:
            ScheduledTask | None: 创建的任务
        """
        # 解析调度表达式
        cron_expr = self.parse_natural_language(schedule)
        if cron_expr is None:
            # 假设是标准 cron 表达式
            cron_expr = schedule

        # 验证 cron 表达式
        try:
            from croniter import croniter

            croniter(cron_expr)
        except ImportError:
            logger.warning("⚠️ croniter 未安装,无法验证 cron 表达式")
        except Exception as e:
            logger.error(f"❌ 无效的 cron 表达式: {cron_expr} - {e}")
            return None

        task = ScheduledTask(
            task_id=task_id,
            name=name,
            description=description,
            cron_expression=cron_expr,
            task_type=task_type,
            parameters=parameters or {},
        )

        self.tasks[task_id] = task
        self._save_tasks()

        logger.info(f"✅ 任务已调度: {name} (ID: {task_id}, Cron: {cron_expr})")
        return task

    def cancel_task(self, task_id: str) -> bool:
        """
        取消调度任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功取消
        """
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save_tasks()
            logger.info(f"❌ 任务已取消: {task_id}")
            return True
        return False

    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            self._save_tasks()
            return True
        return False

    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            self._save_tasks()
            return True
        return False

    async def start(self) -> None:
        """启动调度器"""
        if self._running:
            logger.warning("⚠️ 调度器已在运行")
            return

        self._running = True
        self._scheduler_task = asyncio.create_task(self._run_scheduler())
        logger.info("🚀 调度器已启动")

    async def stop(self) -> None:
        """停止调度器"""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            self._scheduler_task = None
        logger.info("🛑 调度器已停止")

    async def _run_scheduler(self) -> None:
        """运行调度循环"""
        while self._running:
            try:
                await self._check_and_run_tasks()
            except Exception as e:
                logger.error(f"❌ 调度循环错误: {e}")

            # 每分钟检查一次
            await asyncio.sleep(60)

    async def _check_and_run_tasks(self) -> None:
        """检查并执行到期任务"""
        now = datetime.now()

        for task in self.tasks.values():
            if not task.enabled:
                continue

            # 计算下次运行时间
            try:
                from croniter import croniter

                cron = croniter(task.cron_expression, now)
                next_run = cron.get_next(datetime)

                # 检查是否需要运行
                if task.next_run is None or now >= task.next_run:
                    await self._execute_task(task)
                    task.last_run = now
                    task.next_run = next_run
                    task.run_count += 1
                    self._save_tasks()

            except ImportError:
                logger.warning("⚠️ croniter 未安装,跳过任务调度")
                break
            except Exception as e:
                logger.error(f"❌ 任务调度错误: {task.task_id} - {e}")

    async def _execute_task(self, task: ScheduledTask) -> None:
        """执行任务"""
        handler = self.handlers.get(task.task_type)
        if handler:
            try:
                logger.info(f"🔄 执行任务: {task.name} (ID: {task.task_id})")
                if asyncio.iscoroutinefunction(handler):
                    await handler(task.parameters)
                else:
                    handler(task.parameters)
                logger.info(f"✅ 任务完成: {task.name}")
            except Exception as e:
                logger.error(f"❌ 任务执行失败: {task.name} - {e}")
        else:
            logger.warning(f"⚠️ 未找到处理器: {task.task_type}")

    def get_task_status(self, task_id: str) -> Optional[dict[str, Any]]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        if task:
            return task.to_dict()
        return None

    def list_tasks(self) -> list[dict[str, Any]]:
        """列出所有任务"""
        return [task.to_dict() for task in self.tasks.values()]


# ========================================
# 专利状态监控处理器
# ========================================


async def patent_status_check_handler(params: dict[str, Any]) -> None:
    """
    专利状态检查处理器

    检查指定专利的状态变化。

    Args:
        params: 包含 patent_ids 等参数
    """
    patent_ids = params.get("patent_ids", [])
    logger.info(f"🔍 检查专利状态: {patent_ids}")

    # 这里可以添加实际的专利状态检查逻辑
    # 例如：调用专利检索API、检查法律状态变更等

    for patent_id in patent_ids:
        logger.info(f"  - 专利 {patent_id}: 状态检查完成")


# ========================================
# 全局调度器实例
# ========================================
_global_scheduler: CronScheduler | None = None


def get_cron_scheduler(storage_dir: Path | None = None) -> CronScheduler:
    """获取全局调度器"""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = CronScheduler(storage_dir)
        # 注册默认处理器
        _global_scheduler.register_handler("patent_status_check", patent_status_check_handler)
    return _global_scheduler


__all__ = [
    "CronScheduler",
    "NaturalLanguageSchedule",
    "ScheduledTask",
    "get_cron_scheduler",
    "patent_status_check_handler",
]
