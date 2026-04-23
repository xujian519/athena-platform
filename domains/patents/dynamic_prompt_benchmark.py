#!/usr/bin/env python3
from __future__ import annotations

"""
动态提示词效果基准测试框架
Dynamic Prompt Effectiveness Benchmark Framework

用于建立和评估动态提示词系统的性能基准

功能:
1. 定义标准测试用例
2. 建立性能基准线
3. 自动化基准测试执行
4. 生成基准测试报告

作者: 小诺·双鱼公主
创建时间: 2026-01-26
版本: v0.1.0
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

logger = setup_logging()


@dataclass
class BenchmarkTestCase:
    """基准测试用例"""

    case_id: str
    name: str
    description: str

    # 输入数据
    office_action: dict[str, Any]
    patent_info: dict[str, Any] | None = None
    knowledge_graph: dict[str, Any] | None = None

    # 预期结果
    expected_confidence_min: float = 0.7  # 最低置信度
    expected_sources_count_min: int = 2  # 最少数据源数量
    expected_dimensions_count_min: int = 5  # 最少维度数量


@dataclass
class BenchmarkResult:
    """基准测试结果"""

    case_id: str
    case_name: str

    # 执行信息
    execution_time: float
    success: bool
    error_message: str | None = None

    # 性能指标
    generation_duration: float | None = None
    confidence_score: float | None = None
    sources_count: int = 0
    dimensions_count: int = 0

    # 质量评估
    meets_confidence_requirement: bool = False
    meets_sources_requirement: bool = False
    meets_dimensions_requirement: bool = False
    overall_pass: bool = False

    # 详细数据
    dynamic_prompt_data: dict[str, Any] | None = None


@dataclass
class BenchmarkReport:
    """基准测试报告"""

    test_date: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    success_rate: float

    # 性能统计
    avg_generation_time: float
    avg_confidence_score: float
    min_confidence_score: float
    max_confidence_score: float

    # 质量统计
    confidence_pass_rate: float
    sources_pass_rate: float
    dimensions_pass_rate: float

    # 详细结果
    results: list[BenchmarkResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "test_date": self.test_date,
            "summary": {
                "total_cases": self.total_cases,
                "passed_cases": self.passed_cases,
                "failed_cases": self.failed_cases,
                "success_rate": self.success_rate,
            },
            "performance": {
                "avg_generation_time": self.avg_generation_time,
                "avg_confidence_score": self.avg_confidence_score,
                "min_confidence_score": self.min_confidence_score,
                "max_confidence_score": self.max_confidence_score,
            },
            "quality": {
                "confidence_pass_rate": self.confidence_pass_rate,
                "sources_pass_rate": self.sources_pass_rate,
                "dimensions_pass_rate": self.dimensions_pass_rate,
            },
            "results": [
                {
                    "case_id": r.case_id,
                    "case_name": r.case_name,
                    "success": r.success,
                    "overall_pass": r.overall_pass,
                    "generation_duration": r.generation_duration,
                    "confidence_score": r.confidence_score,
                    "sources_count": r.sources_count,
                }
                for r in self.results
            ],
        }


class DynamicPromptBenchmark:
    """
    动态提示词基准测试框架

    功能:
    1. 管理测试用例
    2. 执行基准测试
    3. 评估测试结果
    4. 生成测试报告
    """

    def __init__(self):
        """初始化基准测试框架"""
        self.name = "动态提示词基准测试框架"
        self.version = "v0.1.0"

        self.test_cases: list[BenchmarkTestCase] = []
        self._load_default_test_cases()

        logger.info(f"📊 {self.name} ({self.version}) 初始化完成")

    def _load_default_test_cases(self):
        """加载默认测试用例"""
        # 用例1: 新颖性驳回 - 计算机视觉
        self.test_cases.append(
            BenchmarkTestCase(
                case_id="TC_001",
                name="新颖性驳回-深度学习图像识别",
                description="测试深度学习图像识别专利的新颖性驳回场景",
                office_action={
                    "oa_id": "OA_BENCHMARK_001",
                    "rejection_type": "novelty",
                    "rejection_reason": "权利要求1不具备新颖性",
                    "prior_art_references": ["CN112345678A", "US20210012345A1"],
                    "examiner_arguments": [
                        "对比文件D1公开了相同技术特征",
                        "权利要求1与D1的区别不属于实质性区别",
                    ],
                },
                patent_info={
                    "patent_id": "PAT_BENCHMARK_001",
                    "title": "基于深度学习的图像识别方法",
                    "abstract": "本发明涉及一种使用卷积神经网络和注意力机制的图像识别方法",
                    "technical_field": "计算机视觉",
                    "ipc_code": "G06V 10/00",
                },
                expected_confidence_min=0.7,
                expected_sources_count_min=2,
                expected_dimensions_count_min=5,
            )
        )

        # 用例2: 创造性驳回 - 自然语言处理
        self.test_cases.append(
            BenchmarkTestCase(
                case_id="TC_002",
                name="创造性驳回-NLP文本分类",
                description="测试自然语言处理专利的创造性驳回场景",
                office_action={
                    "oa_id": "OA_BENCHMARK_002",
                    "rejection_type": "inventiveness",
                    "rejection_reason": "权利要求1-3不具备创造性",
                    "prior_art_references": ["CN109876543A"],
                    "examiner_arguments": [
                        "权利要求1的技术方案是本领域的常规技术手段",
                        "权利要求2-3的附加技术特征不具有突出的实质性特点",
                    ],
                },
                patent_info={
                    "patent_id": "PAT_BENCHMARK_002",
                    "title": "基于Transformer的文本分类方法",
                    "abstract": "本发明涉及一种使用自注意力机制的文本分类方法",
                    "technical_field": "自然语言处理",
                    "ipc_code": "G06N 3/00",
                },
                expected_confidence_min=0.6,
                expected_sources_count_min=1,
                expected_dimensions_count_min=4,
            )
        )

        # 用例3: 实用性驳回 - 人工智能
        self.test_cases.append(
            BenchmarkTestCase(
                case_id="TC_003",
                name="实用性驳回-机器学习模型",
                description="测试机器学习模型专利的实用性驳回场景",
                office_action={
                    "oa_id": "OA_BENCHMARK_003",
                    "rejection_type": "utility",
                    "rejection_reason": "权利要求1不具备实用性",
                    "prior_art_references": [],
                    "examiner_arguments": [
                        "说明书未充分公开技术方案",
                        "本领域技术人员无法根据说明书实现该技术方案",
                    ],
                },
                patent_info={
                    "patent_id": "PAT_BENCHMARK_003",
                    "title": "基于强化学习的决策方法",
                    "abstract": "本发明涉及一种使用深度强化学习的智能决策方法",
                    "technical_field": "人工智能",
                    "ipc_code": "G06N 20/00",
                },
                expected_confidence_min=0.5,
                expected_sources_count_min=1,
                expected_dimensions_count_min=3,
            )
        )

        logger.info(f"✅ 已加载 {len(self.test_cases)} 个默认测试用例")

    def add_test_case(self, test_case: BenchmarkTestCase):
        """
        添加测试用例

        Args:
            test_case: 测试用例
        """
        self.test_cases.append(test_case)
        logger.info(f"✅ 已添加测试用例: {test_case.case_id} - {test_case.name}")

    async def run_benchmark(
        self, specific_case_ids: list[str] | None = None
    ) -> BenchmarkReport:
        """
        运行基准测试

        Args:
            specific_case_ids: 指定要运行的测试用例ID，None表示运行所有用例

        Returns:
            基准测试报告
        """
        logger.info("🚀 开始运行基准测试...")

        # 确定要运行的测试用例
        if specific_case_ids:
            test_cases_to_run = [tc for tc in self.test_cases if tc.case_id in specific_case_ids]
        else:
            test_cases_to_run = self.test_cases

        if not test_cases_to_run:
            logger.warning("⚠️ 没有找到要运行的测试用例")
            return self._create_empty_report()

        # 导入SmartOfficeActionResponder
        try:
            from core.patents.smart_oa_responder import SmartOfficeActionResponder

            responder = SmartOfficeActionResponder()
        except Exception as e:
            logger.error(f"❌ 无法初始化SmartOfficeActionResponder: {e}")
            return self._create_empty_report()

        # 运行测试用例
        results: list[BenchmarkResult] = []
        for test_case in test_cases_to_run:
            result = await self._run_single_test_case(responder, test_case)
            results.append(result)

        # 生成报告
        report = self._generate_report(results)
        logger.info(f"✅ 基准测试完成: {report.passed_cases}/{report.total_cases} 通过")

        return report

    async def _run_single_test_case(
        self, responder: Any, test_case: BenchmarkTestCase
    ) -> BenchmarkResult:
        """
        运行单个测试用例

        Args:
            responder: SmartOfficeActionResponder实例
            test_case: 测试用例

        Returns:
            测试结果
        """
        start_time = datetime.now()

        try:
            # 生成动态提示词
            dynamic_prompt_data = await responder._generate_dynamic_prompt(
                office_action=test_case.office_action,
                patent_info=test_case.patent_info,
                knowledge_graph=test_case.knowledge_graph,
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            if dynamic_prompt_data is None:
                # 生成失败
                return BenchmarkResult(
                    case_id=test_case.case_id,
                    case_name=test_case.name,
                    execution_time=execution_time,
                    success=False,
                    error_message="动态提示词生成失败",
                )

            # 评估结果
            confidence_score = dynamic_prompt_data.get("confidence_score", 0.0)
            sources_count = len(dynamic_prompt_data.get("sources", []))
            dimensions_count = sum(
                1
                for key in [
                    "system_prompt",
                    "context_prompt",
                    "patent_rules_prompt",
                    "technical_terms_prompt",
                    "knowledge_prompt",
                    "sqlite_knowledge_prompt",
                    "action_prompt",
                    "search_strategy_prompt",
                ]
                if dynamic_prompt_data.get(key)
            )

            meets_confidence = confidence_score >= test_case.expected_confidence_min
            meets_sources = sources_count >= test_case.expected_sources_count_min
            meets_dimensions = dimensions_count >= test_case.expected_dimensions_count_min
            overall_pass = meets_confidence and meets_sources and meets_dimensions

            return BenchmarkResult(
                case_id=test_case.case_id,
                case_name=test_case.name,
                execution_time=execution_time,
                success=True,
                generation_duration=execution_time,
                confidence_score=confidence_score,
                sources_count=sources_count,
                dimensions_count=dimensions_count,
                meets_confidence_requirement=meets_confidence,
                meets_sources_requirement=meets_sources,
                meets_dimensions_requirement=meets_dimensions,
                overall_pass=overall_pass,
                dynamic_prompt_data=dynamic_prompt_data,
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ 测试用例 {test_case.case_id} 执行失败: {e}")

            return BenchmarkResult(
                case_id=test_case.case_id,
                case_name=test_case.name,
                execution_time=execution_time,
                success=False,
                error_message=str(e),
            )

    def _generate_report(self, results: list[BenchmarkResult]) -> BenchmarkReport:
        """生成基准测试报告"""
        total_cases = len(results)
        passed_cases = sum(1 for r in results if r.overall_pass)
        failed_cases = total_cases - passed_cases

        successful_results = [r for r in results if r.success and r.generation_duration]

        # 性能统计
        if successful_results:
            avg_generation_time = sum(r.generation_duration for r in successful_results) / len(successful_results)
            avg_confidence = sum(r.confidence_score for r in successful_results if r.confidence_score) / len(successful_results)
            min_confidence = min((r.confidence_score for r in successful_results if r.confidence_score), default=0.0)
            max_confidence = max((r.confidence_score for r in successful_results if r.confidence_score), default=0.0)
        else:
            avg_generation_time = 0.0
            avg_confidence = 0.0
            min_confidence = 0.0
            max_confidence = 0.0

        # 质量统计
        confidence_pass_rate = (
            sum(1 for r in results if r.meets_confidence_requirement) / total_cases if total_cases > 0 else 0.0
        )
        sources_pass_rate = (
            sum(1 for r in results if r.meets_sources_requirement) / total_cases if total_cases > 0 else 0.0
        )
        dimensions_pass_rate = (
            sum(1 for r in results if r.meets_dimensions_requirement) / total_cases if total_cases > 0 else 0.0
        )

        return BenchmarkReport(
            test_date=datetime.now().isoformat(),
            total_cases=total_cases,
            passed_cases=passed_cases,
            failed_cases=failed_cases,
            success_rate=passed_cases / total_cases if total_cases > 0 else 0.0,
            avg_generation_time=avg_generation_time,
            avg_confidence_score=avg_confidence,
            min_confidence_score=min_confidence,
            max_confidence_score=max_confidence,
            confidence_pass_rate=confidence_pass_rate,
            sources_pass_rate=sources_pass_rate,
            dimensions_pass_rate=dimensions_pass_rate,
            results=results,
        )

    def _create_empty_report(self) -> BenchmarkReport:
        """创建空报告"""
        return BenchmarkReport(
            test_date=datetime.now().isoformat(),
            total_cases=0,
            passed_cases=0,
            failed_cases=0,
            success_rate=0.0,
            avg_generation_time=0.0,
            avg_confidence_score=0.0,
            min_confidence_score=0.0,
            max_confidence_score=0.0,
            confidence_pass_rate=0.0,
            sources_pass_rate=0.0,
            dimensions_pass_rate=0.0,
        )

    def save_report(self, report: BenchmarkReport, output_path: str):
        """
        保存基准测试报告

        Args:
            report: 基准测试报告
            output_path: 输出文件路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 基准测试报告已保存: {output_path}")

    def generate_markdown_report(self, report: BenchmarkReport) -> str:
        """
        生成Markdown格式的基准测试报告

        Args:
            report: 基准测试报告

        Returns:
            Markdown报告字符串
        """
        md_lines = [
            "# 📊 动态提示词基准测试报告\n",
            f"**测试日期**: {report.test_date}",
            f"**版本**: {self.version}\n",
            "---\n",
            "## 📈 测试摘要\n",
            f"- **总用例数**: {report.total_cases}",
            f"- **通过用例**: {report.passed_cases}",
            f"- **失败用例**: {report.failed_cases}",
            f"- **成功率**: {report.success_rate:.1%}\n",
            "## ⚡ 性能指标\n",
            f"- **平均生成时间**: {report.avg_generation_time:.3f}秒",
            f"- **平均置信度**: {report.avg_confidence_score:.2f}",
            f"- **最低置信度**: {report.min_confidence_score:.2f}",
            f"- **最高置信度**: {report.max_confidence_score:.2f}\n",
            "## 🎯 质量指标\n",
            f"- **置信度达标率**: {report.confidence_pass_rate:.1%}",
            f"- **数据源达标率**: {report.sources_pass_rate:.1%}",
            f"- **维度达标率**: {report.dimensions_pass_rate:.1%}\n",
            "## 📋 详细结果\n",
        ]

        for result in report.results:
            status_icon = "✅" if result.overall_pass else "❌"
            md_lines.extend([
                f"### {status_icon} {result.case_name} (`{result.case_id}`)\n",
                f"- **执行时间**: {result.execution_time:.3f}秒",
                f"- **生成耗时**: {result.generation_duration:.3f}秒" if result.generation_duration else "",
                f"- **置信度**: {result.confidence_score:.2f}" if result.confidence_score else "",
                f"- **数据源数量**: {result.sources_count}",
                f"- **维度数量**: {result.dimensions_count}",
                f"- **通过**: {'是' if result.overall_pass else '否'}",
                "",
            ])

        return "\n".join(md_lines)


# ===== 全局单例 =====

_benchmark_instance: DynamicPromptBenchmark | None = None


def get_dynamic_prompt_benchmark() -> DynamicPromptBenchmark:
    """获取基准测试框架单例"""
    global _benchmark_instance
    if _benchmark_instance is None:
        _benchmark_instance = DynamicPromptBenchmark()
    return _benchmark_instance


# ===== 测试代码 =====

async def main():
    """运行基准测试"""

    print("\n" + "=" * 70)
    print("📊 动态提示词基准测试")
    print("=" * 70 + "\n")

    benchmark = get_dynamic_prompt_benchmark()

    # 运行基准测试
    report = await benchmark.run_benchmark()

    # 生成报告
    print(benchmark.generate_markdown_report(report))

    # 保存报告
    output_path = f"benchmark_reports/dynamic_prompt_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    benchmark.save_report(report, output_path)

    print("\n✅ 基准测试完成!")


if __name__ == "__main__":
    asyncio.run(main())
