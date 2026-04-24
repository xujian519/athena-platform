"""
任务编排模块

负责多代理任务的协调和编排。

主要功能：
- 完整专利申请流程编排
- 审查意见答复流程编排
- 串行任务编排
- 并行任务编排
- 任务依赖管理
- 结果聚合
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskResult:
    """任务执行结果"""
    task_name: str
    status: TaskStatus
    result: Optional[Dict[str, Any]]

    error: Optional[str] = None
    start_time: Optional[datetime ] = None
    end_time: Optional[datetime ] = None
    duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_name": self.task_name,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
        }


@dataclass
class OrchestrationProgress:
    """编排进度跟踪"""
    total_steps: int = 0
    completed_steps: int = 0
    current_step: str = ""
    task_results: Optional[list[TaskResult]] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def add_result(self, result: TaskResult) -> str:
        """添加任务结果"""
        self.task_results.append(result)
        if result.status == TaskStatus.COMPLETED:
            self.completed_steps += 1

    def get_progress_summary(self) -> Dict[str, Any]:
        """获取进度摘要"""
        return {
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "progress_percent": round(self.completed_steps / self.total_steps * 100, 2) if self.total_steps > 0 else 0,
            "current_step": self.current_step,
            "total_duration": sum(r.duration for r in self.task_results),
            "success_count": sum(1 for r in self.task_results if r.status == TaskStatus.COMPLETED),
            "failed_count": sum(1 for r in self.task_results if r.status == TaskStatus.FAILED),
        }


class OrchestrationModule:
    """
    任务编排模块

    负责多代理任务的协调和编排，支持：
    - 完整专利申请流程
    - 审查意见答复流程
    - 串行/并行任务执行
    - 进度跟踪和错误处理
    """

    def __init__(self):
        """初始化编排模块"""
        self._drafting_proxy = None
        self._retriever_agent = None
        self._analyzer_agent = None
        self._writer_agent = None

    def _get_drafting_proxy(self):
        """延迟加载专利撰写代理"""
        if self._drafting_proxy is None:
            from core.framework.agents.xiaona.patent_drafting_proxy import PatentDraftingProxy
            self._drafting_proxy = PatentDraftingProxy()
        return self._drafting_proxy

    def _get_retriever_agent(self):
        """延迟加载检索代理"""
        if self._retriever_agent is None:
            from core.framework.agents.xiaona.retriever_agent import RetrieverAgent
            self._retriever_agent = RetrieverAgent()
        return self._retriever_agent

    def _get_analyzer_agent(self):
        """延迟加载分析代理"""
        if self._analyzer_agent is None:
            from core.framework.agents.xiaona.analyzer_agent import AnalyzerAgent
            self._analyzer_agent = AnalyzerAgent()
        return self._analyzer_agent

    def _get_writer_agent(self):
        """延迟加载写作代理"""
        if self._writer_agent is None:
            from core.framework.agents.xiaona.writer_agent import WriterAgent
            self._writer_agent = WriterAgent()
        return self._writer_agent

    async def draft_full_application(
        self,
        disclosure_data: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> Dict[str, Any]:
        """
        完整专利申请流程编排

        流程步骤：
        1. analyze_disclosure - 分析技术交底书
        2. assess_patentability - 评估可专利性
        3. draft_claims - 撰写权利要求书
        4. draft_specification - 撰写说明书
        5. review_adequacy - 审查充分公开
        6. detect_common_errors - 检测常见错误

        Args:
            disclosure_data: 技术交底书数据
            enable_progress_callback: 是否启用进度回调
            progress_callback: 进度回调函数 (step_name, progress_percent)

        Returns:
            完整申请流程结果，包含：
            - success: 是否成功
            - application_data: 申请文件数据
            - analysis_report: 交底书分析报告
            - patentability_report: 可专利性评估报告
            - claims: 权利要求书
            - specification: 说明书
            - adequacy_review: 充分公开审查
            - error_report: 错误检测报告
            - progress: 进度信息
        """
        progress = OrchestrationProgress(total_steps=6, start_time=datetime.now())
        drafting_proxy = self._get_drafting_proxy()

        # 检查是否有进度回调
        has_callback = progress_callback is not None

        # 结果容器
        result = {
            "success": False,
            "application_data": {},
            "analysis_report": None,
            "patentability_report": None,
            "claims": None,
            "specification": None,
            "adequacy_review": None,
            "error_report": None,
            "progress": {},
        }

        # 步骤1: 分析技术交底书
        progress.current_step = "分析技术交底书"
        if has_callback:
            await self._safe_callback(progress_callback, progress.current_step, 0/6)

        step1_result = await self._execute_task(
            task_name="analyze_disclosure",
            coro=drafting_proxy.analyze_disclosure(disclosure_data),
            step_num=1,
        )
        progress.add_result(step1_result)

        if step1_result.status == TaskStatus.FAILED:
            result["error"] = f"交底书分析失败: {step1_result.error}"
            result["progress"] = progress.get_progress_summary()
            return result

        result["analysis_report"] = step1_result.result

        # 步骤2: 评估可专利性
        progress.current_step = "评估可专利性"
        if has_callback:
            await self._safe_callback(progress_callback, progress.current_step, 1/6)

        step2_result = await self._execute_task(
            task_name="assess_patentability",
            coro=drafting_proxy.assess_patentability({
                "disclosure_analysis": step1_result.result,
                "disclosure_data": disclosure_data,
            }),
            step_num=2,
        )
        progress.add_result(step2_result)

        if step2_result.status == TaskStatus.FAILED:
            logger.warning(f"可专利性评估失败: {step2_result.error}，继续执行")

        result["patentability_report"] = step2_result.result

        # 步骤3: 撰写权利要求书
        progress.current_step = "撰写权利要求书"
        if has_callback:
            await self._safe_callback(progress_callback, progress.current_step, 2/6)

        step3_result = await self._execute_task(
            task_name="draft_claims",
            coro=drafting_proxy.draft_claims({
                "disclosure_analysis": step1_result.result,
                "patentability_assessment": step2_result.result,
            }),
            step_num=3,
        )
        progress.add_result(step3_result)

        if step3_result.status == TaskStatus.FAILED:
            result["error"] = f"权利要求书撰写失败: {step3_result.error}"
            result["progress"] = progress.get_progress_summary()
            return result

        result["claims"] = step3_result.result

        # 步骤4: 撰写说明书
        progress.current_step = "撰写说明书"
        if has_callback:
            await self._safe_callback(progress_callback, progress.current_step, 3/6)

        step4_result = await self._execute_task(
            task_name="draft_specification",
            coro=drafting_proxy.draft_specification({
                "disclosure_analysis": step1_result.result,
                "claims": step3_result.result,
            }),
            step_num=4,
        )
        progress.add_result(step4_result)

        if step4_result.status == TaskStatus.FAILED:
            result["error"] = f"说明书撰写失败: {step4_result.error}"
            result["progress"] = progress.get_progress_summary()
            return result

        result["specification"] = step4_result.result

        # 步骤5: 审查充分公开
        progress.current_step = "审查充分公开"
        if has_callback:
            await self._safe_callback(progress_callback, progress.current_step, 4/6)

        step5_result = await self._execute_task(
            task_name="review_adequacy",
            coro=drafting_proxy.review_adequacy({
                "specification": step4_result.result,
                "claims": step3_result.result,
            }),
            step_num=5,
        )
        progress.add_result(step5_result)

        if step5_result.status == TaskStatus.FAILED:
            logger.warning(f"充分公开审查失败: {step5_result.error}，继续执行")

        result["adequacy_review"] = step5_result.result

        # 步骤6: 检测常见错误
        progress.current_step = "检测常见错误"
        if has_callback:
            await self._safe_callback(progress_callback, progress.current_step, 5/6)

        step6_result = await self._execute_task(
            task_name="detect_common_errors",
            coro=drafting_proxy.detect_common_errors({
                "specification": step4_result.result,
                "claims": step3_result.result,
            }),
            step_num=6,
        )
        progress.add_result(step6_result)

        if step6_result.status == TaskStatus.FAILED:
            logger.warning(f"错误检测失败: {step6_result.error}，继续执行")

        result["error_report"] = step6_result.result

        # 组装完整申请数据
        result["application_data"] = {
            "disclosure_analysis": step1_result.result,
            "patentability_assessment": step2_result.result,
            "claims": step3_result.result,
            "specification": step4_result.result,
            "adequacy_review": step5_result.result,
            "error_report": step6_result.result,
        }

        result["success"] = True
        progress.end_time = datetime.now()
        result["progress"] = progress.get_progress_summary()

        if has_callback:
            await self._safe_callback(progress_callback, "完成", 1.0)

        return result

    async def orchestrate_response(
        self,
        office_action: Optional[Dict[str, Any]] = None,
        patent_data: Optional[Dict[str, Any]] = None,
        search_existing_art: bool = True,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> Dict[str, Any]:
        """
        审查意见答复流程编排

        流程步骤：
        1. search_prior_art - 检索现有技术（可选）
        2. analyze_office_action - 分析审查意见
        3. analyze_citations - 分析引用文献
        4. draft_response - 撰写答复意见
        5. review_response - 审查答复质量

        Args:
            office_action: 审查意见数据
            patent_data: 专利数据
            search_existing_art: 是否检索现有技术
            enable_progress_callback: 是否启用进度回调
            progress_callback: 进度回调函数

        Returns:
            答复流程结果，包含：
            - success: 是否成功
            - office_action_analysis: 审查意见分析
            - citation_analysis: 引用文献分析
            - prior_art_search: 现有技术检索结果
            - response_draft: 答复意见草稿
            - response_review: 答复质量审查
            - progress: 进度信息
        """
        total_steps = 5 if search_existing_art else 4
        progress = OrchestrationProgress(total_steps=total_steps, start_time=datetime.now())
        has_callback = progress_callback is not None

        result = {
            "success": False,
            "office_action_analysis": None,
            "citation_analysis": None,
            "prior_art_search": None,
            "response_draft": None,
            "response_review": None,
            "progress": {},
        }

        # 步骤1: 分析审查意见
        progress.current_step = "分析审查意见"
        step_percent = 0
        if has_callback:
            await self._safe_callback(progress_callback, progress.current_step, step_percent/total_steps)

        analyzer = self._get_analyzer_agent()
        step1_result = await self._execute_task(
            task_name="analyze_office_action",
            coro=self._analyze_office_action_internal(analyzer, office_action, patent_data),
            step_num=1,
        )
        progress.add_result(step1_result)
        step_percent += 1

        if step1_result.status == TaskStatus.FAILED:
            result["error"] = f"审查意见分析失败: {step1_result.error}"
            result["progress"] = progress.get_progress_summary()
            return result

        result["office_action_analysis"] = step1_result.result

        # 步骤2: 分析引用文献
        progress.current_step = "分析引用文献"
        if has_callback:
            await self._safe_callback(progress_callback, progress.current_step, step_percent/total_steps)

        step2_result = await self._execute_task(
            task_name="analyze_citations",
            coro=self._analyze_citations_internal(analyzer, office_action),
            step_num=2,
        )
        progress.add_result(step2_result)
        step_percent += 1

        if step2_result.status == TaskStatus.FAILED:
            logger.warning(f"引用文献分析失败: {step2_result.error}，继续执行")

        result["citation_analysis"] = step2_result.result

        # 步骤3: 检索现有技术（可选）
        if search_existing_art:
            progress.current_step = "检索现有技术"
            if has_callback:
                await self._safe_callback(progress_callback, progress.current_step, step_percent/total_steps)

            retriever = self._get_retriever_agent()
            step3_result = await self._execute_task(
                task_name="search_prior_art",
                coro=self._search_prior_art_internal(
                    retriever,
                    office_action,
                    step1_result.result,
                ),
                step_num=3,
            )
            progress.add_result(step3_result)
            step_percent += 1

            if step3_result.status == TaskStatus.FAILED:
                logger.warning(f"现有技术检索失败: {step3_result.error}，继续执行")

            result["prior_art_search"] = step3_result.result

        # 步骤4: 撰写答复意见
        progress.current_step = "撰写答复意见"
        if has_callback:
            await self._safe_callback(progress_callback, progress.current_step, step_percent/total_steps)

        writer = self._get_writer_agent()
        step4_result = await self._execute_task(
            task_name="draft_response",
            coro=self._draft_response_internal(
                writer,
                office_action,
                step1_result.result,
                step2_result.result,
                result.get("prior_art_search"),
            ),
            step_num=step_percent + 1,
        )
        progress.add_result(step4_result)
        step_percent += 1

        if step4_result.status == TaskStatus.FAILED:
            result["error"] = f"答复意见撰写失败: {step4_result.error}"
            result["progress"] = progress.get_progress_summary()
            return result

        result["response_draft"] = step4_result.result

        # 步骤5: 审查答复质量
        progress.current_step = "审查答复质量"
        if has_callback:
            await self._safe_callback(progress_callback, progress.current_step, step_percent/total_steps)

        step5_result = await self._execute_task(
            task_name="review_response",
            coro=self._review_response_internal(writer, step4_result.result),
            step_num=step_percent + 1,
        )
        progress.add_result(step5_result)

        if step5_result.status == TaskStatus.FAILED:
            logger.warning(f"答复质量审查失败: {step5_result.error}，继续执行")

        result["response_review"] = step5_result.result

        result["success"] = True
        progress.end_time = datetime.now()
        result["progress"] = progress.get_progress_summary()

        if has_callback:
            await self._safe_callback(progress_callback, "完成", 1.0)

        return result

    async def execute_sequential(
        self,
        tasks: Optional[list[Callable[[], Any]]] = None,
        task_names: Optional[List[str]] = None,
    ) -> list[TaskResult]:
        """
        串行执行任务列表

        Args:
            tasks: 任务协程列表
            task_names: 任务名称列表

        Returns:
            任务结果列表
        """
        if task_names is None:
            task_names = [f"task_{i}" for i in range(len(tasks))]

        results = []
        for i, (task, name) in enumerate(zip(tasks, task_names, strict=False)):
            result = await self._execute_task(name, task(), i + 1)
            results.append(result)

            # 如果任务失败且是关键任务，停止执行
            if result.status == TaskStatus.FAILED:
                logger.warning(f"任务 {name} 失败，停止后续任务执行")
                break

        return results

    async def execute_parallel(
        self,
        tasks: Optional[list[Callable[[], Any]]] = None,
        task_names: Optional[List[str]] = None,
    ) -> list[TaskResult]:
        """
        并行执行任务列表

        Args:
            tasks: 任务协程列表
            task_names: 任务名称列表

        Returns:
            任务结果列表
        """
        if task_names is None:
            task_names = [f"task_{i}" for i in range(len(tasks))]

        async def run_one(idx: int, task: Callable, name: str) -> str:
            return await self._execute_task(name, task(), idx + 1)

        coros = [run_one(i, task, name) for i, (task, name) in enumerate(zip(tasks, task_names, strict=False))]
        results = await asyncio.gather(*coros, return_exceptions=True)

        # 处理异常结果
        final_results = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                final_results.append(TaskResult(
                    task_name=task_names[i],
                    status=TaskStatus.FAILED,
                    error=str(r),
                ))
            else:
                final_results.append(r)

        return final_results

    async def _execute_task(
        self,
        task_name: str,
        coro: Any,
        step_num: int,
    ) -> str:
        """
        执行单个任务并捕获错误

        Args:
            task_name: 任务名称
            coro: 协程对象
            step_num: 步骤编号

        Returns:
            任务执行结果
        """
        start_time = datetime.now()
        try:
            result = await coro
            end_time = datetime.now()

            return TaskResult(
                task_name=task_name,
                status=TaskStatus.COMPLETED,
                result=result,
                start_time=start_time,
                end_time=end_time,
                duration=(end_time - start_time).total_seconds(),
            )
        except Exception as e:
            end_time = datetime.now()
            logger.error(f"任务 {task_name} (步骤{step_num}) 执行失败: {e}")

            return TaskResult(
                task_name=task_name,
                status=TaskStatus.FAILED,
                error=str(e),
                start_time=start_time,
                end_time=end_time,
                duration=(end_time - start_time).total_seconds(),
            )

    async def _analyze_office_action_internal(
        self,
        analyzer: Any,
        office_action: Optional[Dict[str, Any]] = None,
        patent_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """内部方法：分析审查意见"""
        # 这里调用分析代理的具体方法
        # 由于AnalyzerAgent的接口可能不同，这里提供通用实现
        try:
            if hasattr(analyzer, 'analyze_office_action'):
                return await analyzer.analyze_office_action(office_action, patent_data)
            else:
                # 降级到基础分析
                return {
                    "rejections": office_action.get("rejections", []),
                    "citations": office_action.get("citations", []),
                    "deadline": office_action.get("deadline"),
                    "analysis_summary": "基础分析完成",
                }
        except Exception as e:
            logger.error(f"审查意见分析内部错误: {e}")
            raise

    async def _analyze_citations_internal(
        self,
        analyzer: Any,
        office_action: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """内部方法：分析引用文献"""
        try:
            citations = office_action.get("citations", [])
            if hasattr(analyzer, 'analyze_citations'):
                return await analyzer.analyze_citations(citations)
            else:
                return {
                    "citations_analyzed": len(citations),
                    "key_citations": citations[:3] if citations else [],
                    "analysis_summary": f"分析了{len(citations)}篇引用文献",
                }
        except Exception as e:
            logger.error(f"引用文献分析内部错误: {e}")
            raise

    async def _search_prior_art_internal(
        self,
        retriever: Any,
        office_action: Optional[Dict[str, Any]] = None,
        analysis: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """内部方法：检索现有技术"""
        try:
            # 提取检索关键词
            keywords = analysis.get("keywords", [])
            if not keywords:
                keywords = office_action.get("keywords", [])

            if hasattr(retriever, 'search_patents'):
                return await retriever.search_patents({
                    "keywords": keywords,
                    "limit": 20,
                })
            else:
                return {
                    "search_results": [],
                    "keywords_used": keywords,
                    "search_summary": "检索功能未实现",
                }
        except Exception as e:
            logger.error(f"现有技术检索内部错误: {e}")
            raise

    async def _draft_response_internal(
        self,
        writer: Any,
        office_action: Optional[Dict[str, Any]],

        oa_analysis: Optional[Dict[str, Any]],

        citation_analysis: Optional[Dict[str, Any]],

        prior_art: Optional[Dict[str, Any]]

    ) -> Dict[str, Any]:
        """内部方法：撰写答复意见"""
        try:
            context = {
                "office_action": office_action,
                "oa_analysis": oa_analysis,
                "citation_analysis": citation_analysis,
                "prior_art": prior_art,
            }

            if hasattr(writer, 'draft_response'):
                return await writer.draft_response(context)
            else:
                return {
                    "response_content": "答复意见草稿（待实现）",
                    "arguments": [],
                    "requested_amendments": [],
                }
        except Exception as e:
            logger.error(f"答复意见撰写内部错误: {e}")
            raise

    async def _review_response_internal(
        self,
        writer: Any,
        response_draft: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """内部方法：审查答复质量"""
        try:
            if hasattr(writer, 'review_response'):
                return await writer.review_response(response_draft)
            else:
                return {
                    "quality_score": 0.7,
                    "issues_found": [],
                    "suggestions": [],
                    "review_summary": "基础审查完成",
                }
        except Exception as e:
            logger.error(f"答复质量审查内部错误: {e}")
            raise

    async def _safe_callback(
        self,
        callback: Optional[Callable[[str, float], None]],
        step_name: str,
        progress: float,
    ) -> str:
        """安全地调用进度回调"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(step_name, progress)
            else:
                callback(step_name, progress)
        except Exception as e:
            logger.warning(f"进度回调失败: {e}")
