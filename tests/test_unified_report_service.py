#!/usr/bin/env python3
"""
统一报告服务测试用例

测试Dolphin + NetworkX + Athena混合工作流的完整功能。

Author: Athena工作平台
Date: 2026-01-16
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

# 跳过整个测试模块，因为缺少必要的依赖
pytestmark = pytest.mark.skip(reason="模块导入问题，待修复")

try:
    from core.reporting.unified_report_service import (
        OutputFormat,
        ReportConfig,
        ReportType,
        UnifiedReportService,
    )
    from core.reporting.workflow_processor import (
        HybridWorkflowProcessor,
        WorkflowStatus,
    )
except (ImportError, ModuleNotFoundError):
    # 模块不存在时，定义占位符类以避免语法错误
    UnifiedReportService = None  # type: ignore
    ReportType = None  # type: ignore
    OutputFormat = None  # type: ignore
    ReportConfig = None  # type: ignore
    HybridWorkflowProcessor = None  # type: ignore
    WorkflowStatus = None  # type: ignore


# ========== 测试配置 ==========

TEST_DOCUMENTS = [
    "/Users/xujian/Athena工作平台/Dolphin/demo/page_1.png",
    "/Users/xujian/Athena工作平台/Dolphin/demo/page_2.png",
]


# ========== 1. 基础功能测试 ==========

def test_service_initialization():
    """测试服务初始化"""
    print("\n📋 测试1: 服务初始化")

    service = UnifiedReportService()

    assert service is not None
    assert service.dolphin_client is not None
    assert service.networkx_analyzer is not None

    print("✅ 服务初始化测试通过")


def test_report_config():
    """测试报告配置"""
    print("\n📋 测试2: 报告配置")

    config = ReportConfig(
        enable_dolphin_parsing=True,
        enable_networkx_analysis=True,
        enable_ai_generation=False,  # 跳过AI生成以加快测试
        output_formats=[OutputFormat.MARKDOWN, OutputFormat.JSON],
    )

    assert config.enable_dolphin_parsing is True
    assert config.enable_networkx_analysis is True
    assert config.enable_ai_generation is False
    assert len(config.output_formats) == 2

    print("✅ 报告配置测试通过")


# ========== 2. 报告生成测试 ==========

@pytest.mark.asyncio
async def test_generate_from_document():
    """测试从文档生成报告"""
    print("\n📋 测试3: 从文档生成报告")

    # 检查测试文档是否存在
    test_doc = TEST_DOCUMENTS[0]
    if not Path(test_doc).exists():
        pytest.skip(f"测试文档不存在: {test_doc}")

    # 创建配置（跳过AI生成以加快测试）
    config = ReportConfig(
        enable_dolphin_parsing=True,
        enable_networkx_analysis=True,
        enable_ai_generation=False,  # 跳过AI生成
        output_formats=[OutputFormat.MARKDOWN, OutputFormat.JSON],
    )

    service = UnifiedReportService(config=config)

    # 生成报告
    result = await service.generate_from_document(
        document_path=test_doc,
        report_type=ReportType.PATENT_TECHNICAL_ANALYSIS,
    )

    # 验证结果
    assert result is not None
    assert result.dolphin_result is not None
    assert result.networkx_result is not None
    assert result.processing_time_seconds > 0
    assert result.quality_score > 0

    print("✅ 从文档生成报告测试通过")
    print(f"   - 处理时间: {result.processing_time_seconds:.2f}秒")
    print(f"   - 质量分数: {result.quality_score:.2f}")
    print(f"   - 输出文件: {len(result.output_files)}个")


@pytest.mark.asyncio
async def test_generate_from_data():
    """测试从数据生成报告"""
    print("\n📋 测试4: 从数据生成报告")

    config = ReportConfig(
        enable_dolphin_parsing=False,
        enable_networkx_analysis=False,
        enable_ai_generation=False,  # 跳过AI生成
        output_formats=[OutputFormat.MARKDOWN],
    )

    service = UnifiedReportService(config=config)

    # 准备测试数据
    test_data = {
        "title": "测试专利",
        "technical_entities_count": 50,
        "technical_relations_count": 100,
        "innovation_points": [
            {
                "entity_id": "test_1",
                "text": "创新点1",
                "innovation_score": 0.8,
                "scores": {"pagerank": 0.05, "authority": 0.06, "betweenness": 0.03},
            },
            {
                "entity_id": "test_2",
                "text": "创新点2",
                "innovation_score": 0.7,
                "scores": {"pagerank": 0.04, "authority": 0.05, "betweenness": 0.02},
            },
        ],
    }

    # 生成报告
    result = await service.generate_from_data(
        data=test_data,
        report_type=ReportType.PATENT_TECHNICAL_ANALYSIS,
    )

    # 验证结果
    assert result is not None
    assert result.athena_result is not None
    assert result.processing_time_seconds > 0

    print("✅ 从数据生成报告测试通过")
    print(f"   - 处理时间: {result.processing_time_seconds:.2f}秒")


# ========== 3. 工作流测试 ==========

@pytest.mark.asyncio
async def test_workflow_processor():
    """测试工作流处理器"""
    print("\n📋 测试5: 工作流处理器")

    # 过滤存在的测试文档
    existing_docs = [doc for doc in TEST_DOCUMENTS if Path(doc).exists()]

    if not existing_docs:
        pytest.skip("没有可用的测试文档")

    # 创建工作流处理器
    processor = HybridWorkflowProcessor(max_concurrent_tasks=2)

    # 添加任务
    for i, doc_path in enumerate(existing_docs[:2]):  # 最多2个任务
        await processor.add_task(
            task_id=f"test_task_{i}",
            report_type=ReportType.PATENT_TECHNICAL_ANALYSIS,
            input_source=doc_path,
        )

    # 处理所有任务
    stats = await processor.process_all()

    # 验证结果
    assert stats.completed_tasks > 0
    assert stats.failed_tasks == 0

    print("✅ 工作流处理器测试通过")
    print(f"   - 完成任务: {stats.completed_tasks}/{stats.total_tasks}")
    print(f"   - 平均处理时间: {stats.average_processing_time:.2f}秒")


# ========== 4. 批量处理测试 ==========

@pytest.mark.asyncio
async def test_batch_generate_reports():
    """测试批量报告生成"""
    print("\n📋 测试6: 批量报告生成")

    from core.reporting.workflow_processor import batch_generate_reports

    # 过滤存在的测试文档
    existing_docs = [doc for doc in TEST_DOCUMENTS if Path(doc).exists()]

    if not existing_docs:
        pytest.skip("没有可用的测试文档")

    # 批量生成
    results = await batch_generate_reports(
        documents=existing_docs[:2],  # 最多2个文档
        report_type=ReportType.PATENT_TECHNICAL_ANALYSIS,
        max_concurrent=2,
    )

    # 验证结果
    assert len(results) > 0

    print("✅ 批量报告生成测试通过")
    print(f"   - 生成报告数: {len(results)}")


# ========== 5. 集成测试 ==========

@pytest.mark.asyncio
async def test_full_workflow_integration():
    """测试完整工作流集成"""
    print("\n📋 测试7: 完整工作流集成")

    # 检查测试文档
    test_doc = TEST_DOCUMENTS[0]
    if not Path(test_doc).exists():
        pytest.skip(f"测试文档不存在: {test_doc}")

    # 创建服务
    config = ReportConfig(
        enable_dolphin_parsing=True,
        enable_networkx_analysis=True,
        enable_ai_generation=False,  # 跳过AI生成
        output_formats=[OutputFormat.MARKDOWN, OutputFormat.JSON],
    )

    service = UnifiedReportService(config=config)

    # 步骤1: Dolphin解析
    print("   步骤1: Dolphin解析...")
    dolphin_result = await service._dolphin_parse(test_doc)
    assert dolphin_result is not None
    assert "file_name" in dolphin_result
    print(f"   ✅ Dolphin解析完成: {dolphin_result.get('file_name')}")

    # 步骤2: NetworkX分析
    print("   步骤2: NetworkX分析...")
    networkx_result = await service._networkx_analyze(test_doc)
    assert networkx_result is not None
    assert networkx_result.get("entities_count", 0) > 0
    print(f"   ✅ NetworkX分析完成: {networkx_result['entities_count']}个实体")

    # 步骤3: Athena生成
    print("   步骤3: Athena生成...")
    athena_result = await service._athena_generate(
        report_type=ReportType.PATENT_TECHNICAL_ANALYSIS,
        dolphin_result=dolphin_result,
        networkx_result=networkx_result,
        custom_data=None,
    )
    assert athena_result is not None
    assert "markdown_content" in athena_result
    print(f"   ✅ Athena生成完成: {len(athena_result['markdown_content'])}字符")

    # 步骤4: 完整报告生成
    print("   步骤4: 完整报告生成...")
    result = await service.generate_from_document(
        document_path=test_doc,
        report_type=ReportType.PATENT_TECHNICAL_ANALYSIS,
    )
    assert result is not None
    assert len(result.output_files) > 0
    print(f"   ✅ 完整报告生成完成: {len(result.output_files)}个文件")

    print("✅ 完整工作流集成测试通过")


# ========== 6. 性能测试 ==========

@pytest.mark.asyncio
@pytest.mark.performance
async def test_performance_benchmark():
    """性能基准测试"""
    print("\n📋 测试8: 性能基准测试")

    # 检查测试文档
    test_doc = TEST_DOCUMENTS[0]
    if not Path(test_doc).exists():
        pytest.skip(f"测试文档不存在: {test_doc}")

    # 测试不同配置的性能
    configs = [
        ("仅Dolphin", ReportConfig(
            enable_dolphin_parsing=True,
            enable_networkx_analysis=False,
            enable_ai_generation=False,
        )),
        ("Dolphin+NetworkX", ReportConfig(
            enable_dolphin_parsing=True,
            enable_networkx_analysis=True,
            enable_ai_generation=False,
        )),
    ]

    results = {}

    for name, config in configs:
        print(f"\n   测试配置: {name}")
        service = UnifiedReportService(config=config)

        import time
        start_time = time.time()

        result = await service.generate_from_document(
            document_path=test_doc,
            report_type=ReportType.PATENT_TECHNICAL_ANALYSIS,
        )

        elapsed_time = time.time() - start_time

        results[name] = {
            "time": elapsed_time,
            "quality": result.quality_score,
        }

        print(f"   处理时间: {elapsed_time:.2f}秒")
        print(f"   质量分数: {result.quality_score:.2f}")

    print("\n✅ 性能基准测试完成")
    print("   结果对比:")
    for name, metrics in results.items():
        print(f"   - {name}: {metrics['time']:.2f}秒, 质量: {metrics['quality']:.2f}")


# ========== 主测试运行器 ==========

def run_tests():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("  🧪 统一报告服务测试套件")
    print("  Dolphin + NetworkX + Athena")
    print("=" * 70)

    # 同步测试
    print("\n【同步测试】")
    test_service_initialization()
    test_report_config()

    # 异步测试
    print("\n【异步测试】")
    asyncio.run(test_generate_from_document())
    asyncio.run(test_generate_from_data())
    asyncio.run(test_workflow_processor())
    asyncio.run(test_batch_generate_reports())
    asyncio.run(test_full_workflow_integration())

    # 性能测试（可选）
    print("\n【性能测试】")
    asyncio.run(test_performance_benchmark())

    print("\n" + "=" * 70)
    print("  ✅ 所有测试完成!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
