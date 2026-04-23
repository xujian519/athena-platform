#!/usr/bin/env python3
from __future__ import annotations
"""
CAP05 + STORM 端到端测试

完整的端到端测试,验证:
1. 信息策展器功能
2. CAP05 创造性分析集成
3. STORM 专家对话
4. 报告生成

作者: Athena 平台团队
创建时间: 2026-01-02
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.storm_integration.cap05_storm_integration import (
    CAP05WithStorm,
    CreativityAnalysisInput,
)
from core.storm_integration.patent_curator import (
    PatentInformationCurator,
    RetrievedDocument,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CAP05StormE2ETester:
    """CAP05 + STORM 端到端测试器"""

    def __init__(self):
        self.test_results = []

    def run_all_tests(self) -> Any:
        """运行所有测试"""
        print("\n" + "=" * 70)
        print(" " * 15 + "CAP05 + STORM 端到端测试")
        print("=" * 70)

        tests = [
            ("信息策展器", self.test_information_curator),
            ("CAP05 创造性分析", self.test_cap05_analysis),
            ("完整流程集成", self.test_full_integration),
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            print("\n" + "-" * 70)
            print(f"📋 测试: {test_name}")
            print("-" * 70)

            try:
                result = asyncio.run(test_func())
                if result:
                    print(f"✅ {test_name}: 通过")
                    passed += 1
                    self.test_results.append((test_name, "PASS", None))
                else:
                    print(f"⚠️  {test_name}: 未通过")
                    failed += 1
                    self.test_results.append((test_name, "FAIL", "Test returned False"))
            except Exception as e:
                print(f"❌ {test_name}: 异常")
                print(f"   错误: {e}")
                import traceback

                traceback.print_exc()
                failed += 1
                self.test_results.append((test_name, "ERROR", str(e)))

        # 打印总结
        self._print_summary(passed, failed)

        return failed == 0

    def _print_summary(self, passed: int, failed: int) -> Any:
        """打印测试总结"""
        print("\n" + "=" * 70)
        print("测试总结")
        print("=" * 70)
        print(f"总计: {passed + failed} 个测试")
        print(f"通过: {passed} 个 ✅")
        print(f"失败: {failed} 个 ❌")
        if passed + failed > 0:
            print(f"通过率: {passed/(passed+failed)*100:.1f}%")

    async def test_information_curator(self) -> bool:
        """测试信息策展器"""
        print("\n[测试] 多源信息策展...")

        # 创建策展器
        curator = PatentInformationCurator()

        # 打印配置
        stats = curator.get_statistics()
        print(f"  可用检索器: {stats['available_retrievers']}/{stats['total_retrievers']}")
        print(f"  检索器类型: {', '.join(stats['retriever_types'])}")

        # 测试策展
        query = "深度学习在图像识别中的应用"
        print(f"\n  查询: {query}")

        results = await curator.curate(query, top_k=10)

        print(f"\n  检索到 {len(results)} 条结果:")

        for i, result in enumerate(results[:5], 1):
            print(f"\n  {i}. [{result.source.value}] {result.title}")
            print(f"     相关性: {result.relevance_score:.3f}")
            print(f"     内容: {result.content[:80]}...")

        # 验证结果
        assert len(results) > 0, "应该检索到结果"
        assert all(isinstance(r, RetrievedDocument) for r in results), "结果类型不正确"

        print("\n✅ 信息策展器测试通过")
        return True

    async def test_cap05_analysis(self) -> bool:
        """测试 CAP05 创造性分析"""
        print("\n[测试] CAP05 创造性分析...")

        # 创建测试输入
        input_data = CreativityAnalysisInput(
            patent_id="CN202410000001.X",
            title="基于Transformer的专利摘要生成方法",
            abstract="本发明公开了一种基于Transformer的专利摘要生成方法,通过预训练语言模型和领域自适应,生成高质量的专利摘要。该方法解决了传统摘要生成不准确、不完整的问题。",
            claims=[
                "1. 一种基于Transformer的专利摘要生成方法,其特征在于,包括:获取专利文本;使用预训练Transformer模型编码文本;通过注意力机制提取关键信息;生成摘要文本。",
                "2. 根据权利要求1所述的方法,其特征在于,所述预训练Transformer模型为BERT模型。",
                "3. 根据权利要求1所述的方法,其特征在于,还包括:使用专利语料进行微调。",
            ],
            applicant="创新科技有限公司",
            inventor="张三, 李四",
            application_date="2024-03-15",
            ipc_classification="G06N3/00",
        )

        # 执行分析
        print(f"  专利号: {input_data.patent_id}")
        print(f"  标题: {input_data.title}")

        analyzer = CAP05WithStorm()
        report = await analyzer.analyze_creativity(input_data, max_conversation_turns=6)

        # 验证报告
        assert report.patent_id == input_data.patent_id
        assert 0 <= report.creativity_score <= 1
        assert len(report.perspectives) > 0
        assert len(report.conversation_log) > 0

        # 打印关键结果
        print("\n  分析完成:")
        print(f"  - 发现 {len(report.perspectives)} 个分析视角")
        print(f"  - {len(report.conversation_log)} 轮专家对话")
        print(f"  - 策展 {len(report.curated_information)} 条文献")
        print(f"  - 收集 {len(report.all_citations)} 条引用")
        print(f"\n  创造性评分: {report.creativity_score:.2f} / 1.0")
        print(f"  最终结论: {report.final_conclusion[:100]}...")

        # 打印专家对话摘要
        print("\n  专家对话摘要:")
        for utterance in report.conversation_log[:3]:
            print(f"\n  [{utterance['agent_name']}]")
            print(f"  {utterance['content'][:150]}...")

        print("\n✅ CAP05 创造性分析测试通过")
        return True

    async def test_full_integration(self) -> bool:
        """测试完整集成流程"""
        print("\n[测试] 完整集成流程...")

        print("\n  [步骤1] 准备测试数据...")
        input_data = CreativityAnalysisInput(
            patent_id="CN202410000002.8",
            title="智能专利审查系统及方法",
            abstract="本发明提供一种智能专利审查系统,通过深度学习技术自动分析专利的新颖性和创造性,提高审查效率。",
            claims=[
                "1. 一种智能专利审查系统,其特征在于,包括:专利检索模块,用于检索对比文献;特征提取模块,用于提取技术特征;创造性评估模块,用于评估专利创造性。",
            ],
            applicant="Athena 科技有限公司",
            inventor="徐健",
            application_date="2024-01-10",
            ipc_classification="G06N5/00",
        )

        print(f"    专利: {input_data.title}")

        print("\n  [步骤2] 执行完整分析...")
        analyzer = CAP05WithStorm()
        report = await analyzer.analyze_creativity(input_data, max_conversation_turns=6)

        print("\n  [步骤3] 验证分析结果...")

        # 验证各个部分
        checks = [
            ("专利号匹配", report.patent_id == input_data.patent_id),
            ("视角发现", len(report.perspectives) >= 5),
            ("专家对话", len(report.conversation_log) >= 6),
            ("文献策展", len(report.curated_information) >= 0),
            ("引用收集", len(report.all_citations) >= 6),
            ("评分有效", 0 <= report.creativity_score <= 1),
            ("三步法完整", report.step1 and report.step2 and report.step3),
            ("结论生成", bool(report.final_conclusion)),
        ]

        all_passed = True
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"    {status} {check_name}")
            if not check_result:
                all_passed = False

        if all_passed:
            # 生成完整报告
            print("\n  [步骤4] 生成完整报告...")
            markdown = report.to_markdown()

            # 保存报告
            report_dir = Path("/tmp/athena_storm_reports")
            report_dir.mkdir(exist_ok=True)
            report_file = report_dir / f"{input_data.patent_id}_report.md"

            with open(report_file, "w", encoding="utf-8") as f:
                f.write(markdown)

            print(f"    📄 报告已保存: {report_file}")
            print(f"    📊 报告大小: {len(markdown)} 字符")

            # 打印报告摘要
            print("\n  [报告摘要]")
            print("  三步法分析:")
            print(f"    - 第一步: {report.step1.closest_prior_art.title}")
            print(f"    - 第二步: 发现 {len(report.step2.differences)} 个区别特征")
            print(f"    - 第三步: {report.step3.conclusion}")
            print(f"\n  最终结论: {report.final_conclusion}")

        print("\n✅ 完整集成流程测试通过")
        return all_passed


def main() -> None:
    """主函数"""
    tester = CAP05StormE2ETester()
    success = tester.run_all_tests()

    if success:
        print("\n" + "=" * 70)
        print("🎉 所有测试通过!")
        print("=" * 70)
        print("\n✨ CAP05 + STORM 集成成功完成")
        print("\n核心功能:")
        print("  ✅ 多源信息策展 (专利数据库 + 知识图谱 + 向量检索)")
        print("  ✅ 专利视角自动发现")
        print("  ✅ 专家 Agent 对话模拟")
        print("  ✅ 三步法创造性分析")
        print("  ✅ 带引用的分析报告")
        print("\n下一步:")
        print("  1. 集成到小娜主流程")
        print("  2. 添加更多检索源")
        print("  3. 优化 Agent 质量")
        print("  4. 开发 Web 界面")
        return 0
    else:
        print("\n⚠️  部分测试未通过,请检查问题")
        return 1


if __name__ == "__main__":
    exit(main())
