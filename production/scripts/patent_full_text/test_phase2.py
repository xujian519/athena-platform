#!/usr/bin/env python3
"""
Phase 2 模块测试脚本
测试PDF处理管道的各个模块

作者: Athena平台团队
创建时间: 2025-12-24
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Any

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "phase2"))


def test_pdf_extractor() -> Any:
    """测试PDF提取模块"""
    print("=" * 70)
    print("测试1: PDF文本提取模块")
    print("=" * 70)

    from phase2.pdf_extractor import PDFExtractor

    extractor = PDFExtractor()

    # 查找测试PDF
    test_pdfs = list(Path("/Users/xujian/apps/apps/patents/PDF/CN").glob("*.pdf"))
    if not test_pdfs:
        print("⚠️  未找到测试PDF文件")
        return False

    test_pdf = test_pdfs[0]
    print(f"\n📄 测试PDF: {test_pdf.name}")

    try:
        content = extractor.extract(str(test_pdf))

        print("✅ PDF提取成功")
        print(f"   专利号: {content.patent_number}")
        print(f"   页数: {content.pages_count}")
        print(f"   语言: {content.language}")
        print(f"   字符数: {content.char_count}")
        print(f"   提取方法: {content.extraction_method}")

        print("\n📋 内容长度:")
        print(f"   标题: {len(content.title)} 字符")
        print(f"   摘要: {len(content.abstract)} 字符")
        print(f"   权利要求: {len(content.claims)} 字符")

        return True

    except Exception as e:
        print(f"❌ PDF提取失败: {e}")
        return False


def test_claim_parser() -> Any:
    """测试权利要求解析模块"""
    print("\n" + "=" * 70)
    print("测试2: 权利要求解析器")
    print("=" * 70)

    from phase2.claim_parser import ClaimParser

    parser = ClaimParser()

    # 测试文本
    test_claims = """
    1. 一种图像识别方法，其特征在于，包括：
    获取待识别图像；
    使用深度学习模型提取特征；
    根据特征进行分类。

    2. 根据权利要求1所述的方法，其特征在于，所述深度学习模型为卷积神经网络。

    3. 根据权利要求1所述的方法，其特征在于，还包括预处理步骤。
    """

    print(f"\n📝 测试文本: {len(test_claims)} 字符")

    try:
        parsed = parser.parse(test_claims)

        print("✅ 权利要求解析成功")
        print(f"   总数: {len(parsed.claims)}")
        print(f"   独立: {parsed.independent_count}")
        print(f"   从属: {parsed.dependent_count}")
        print(f"   语言: {parsed.language}")

        print("\n📋 权利要求列表:")
        for claim in parsed.claims:
            print(f"   [{claim.claim_number}] {claim.claim_type.value}")
            if claim.depends_on:
                print(f"       从属: 权利要求{claim.depends_on}")

        return True

    except Exception as e:
        print(f"❌ 权利要求解析失败: {e}")
        return False


def test_vector_processor() -> Any:
    """测试向量化模块"""
    print("\n" + "=" * 70)
    print("测试3: BGE向量化处理")
    print("=" * 70)

    from phase2.vector_processor import BGEVectorizer, TextChunker

    vectorizer = BGEVectorizer()
    chunker = TextChunker()

    test_text = """
    一种基于人工智能的图像识别方法，包括特征提取和分类识别步骤。
    该方法首先获取待识别的图像数据，然后对图像进行预处理操作。
    预处理包括去噪、归一化和增强处理。
    接着使用预训练的深度卷积神经网络提取图像特征。
    最后通过全连接层进行分类识别，输出识别结果。
    该方法能够有效提升识别准确率，降低计算复杂度。
    """ * 3  # 扩展文本以测试分块

    print(f"\n📝 测试文本长度: {len(test_text)} 字符")

    try:
        # 测试文本分块
        print("\n[分块测试]")
        chunks = chunker.chunk_text(test_text, "TEST001", "abstract")
        print(f"✅ 分块成功: {len(chunks)} 个块")
        for i, chunk in enumerate(chunks[:3]):
            print(f"   块{i+1}: {chunk.chunk_id}, {chunk.token_count} tokens")
            print(f"      预览: {chunk.text[:50]}...")

        # 测试向量化（如果有模型）
        if vectorizer.model:
            print("\n[向量化测试]")
            print("✅ 模型已加载")
            print(f"   模型路径: {vectorizer.model_path}")
            print(f"   向量维度: {vectorizer.vector_dimension}")

            # 测试向量化第一个块
            if chunks:
                result = vectorizer.vectorize_chunk(chunks[0], postgres_id="test-uuid-001")

                if result.success:
                    print("✅ 向量化成功")
                    print(f"   向量ID: {result.vector_id}")
                    print(f"   向量维度: {result.vector_dimension}")
                    return True
                else:
                    print(f"⚠️  向量化失败: {result.error_message}")
                    return False
        else:
            print("⚠️  模型未加载，跳过向量化测试")
            return None

    except Exception as e:
        print(f"❌ 向量化异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_kg_builder() -> Any:
    """测试知识图谱构建模块"""
    print("\n" + "=" * 70)
    print("测试4: 知识图谱构建")
    print("=" * 70)

    from phase2.kg_builder import PatentKGBuilder

    builder = PatentKGBuilder()

    if not builder.session:
        print("⚠️  NebulaGraph未连接，跳过测试")
        return None

    try:
        result = builder.build_patent_kg(
            patent_number="TEST_PATENT_001",
            patent_name="测试专利名称",
            application_number="TEST2024001",
            applicant="测试申请人",
            inventor="测试发明人",
            ipc_main_class="G06F",
            abstract="测试摘要内容",
            claims_text="1. 一种测试方法，包括测试步骤。2. 根据权利要求1所述的方法..."
        )

        if result.success:
            print("✅ 知识图谱构建成功")
            print(f"   顶点ID: {result.vertex_id}")
            print(f"   创建顶点: {result.vertices_created}")
            print(f"   创建边: {result.edges_created}")
        else:
            print(f"❌ 知识图谱构建失败: {result.error_message}")

        builder.close()
        return result.success

    except Exception as e:
        print(f"❌ 知识图谱构建异常: {e}")
        builder.close()
        return False


def test_postgresql_updater() -> Any:
    """测试PostgreSQL更新模块"""
    print("\n" + "=" * 70)
    print("测试5: PostgreSQL更新")
    print("=" * 70)

    from phase2.postgresql_updater import PostgreSQLUpdater

    updater = PostgreSQLUpdater()

    if not updater.conn:
        print("⚠️  PostgreSQL未连接，跳过测试")
        return None

    try:
        # 测试查询
        record = updater.get_patent_by_publication_number("CN112233445A")

        if record:
            print("✅ 数据库查询成功")
            print(f"   专利名称: {record.get('patent_name', 'N/A')}")
            print(f"   申请人: {record.get('applicant', 'N/A')}")
            print(f"   PDF路径: {record.get('pdf_path', 'N/A')}")
        else:
            print("⚠️  未找到专利记录")

        updater.close()
        return True

    except Exception as e:
        print(f"❌ PostgreSQL操作失败: {e}")
        updater.close()
        return False


def test_pipeline() -> Any:
    """测试完整管道"""
    print("\n" + "=" * 70)
    print("测试6: 完整处理管道")
    print("=" * 70)

    from phase2.pipeline import PatentFullTextPipeline

    pipeline = PatentFullTextPipeline()

    # 查找测试PDF
    test_pdfs = list(Path("/Users/xujian/apps/apps/patents/PDF/CN").glob("*.pdf"))
    if not test_pdfs:
        print("⚠️  未找到测试PDF文件")
        return False

    test_pdf = test_pdfs[0]
    print(f"\n📄 测试PDF: {test_pdf.name}")

    # 模拟元数据
    metadata = {
        "postgres_id": "test-uuid-001",
        "patent_name": "测试专利",
        "application_number": "TEST2024001",
        "applicant": "测试申请人",
        "inventor": "测试",
        "ipc_main_class": "G06F"
    }

    try:
        result = pipeline.process_pdf(str(test_pdf), metadata)

        print("\n📋 处理结果:")
        print(f"   成功: {result.success}")
        print(f"   完成率: {result.completion_rate:.1f}%")
        print(f"   PDF提取: {'✅' if result.pdf_extracted else '❌'}")
        print(f"   向量化: {'✅' if result.vectorized else '❌'}")
        print(f"   知识图谱: {'✅' if result.kg_built else '❌'}")
        print(f"   数据库更新: {'✅' if result.db_updated else '❌'}")

        pipeline.close()
        return result.success

    except Exception as e:
        print(f"❌ 管道处理失败: {e}")
        pipeline.close()
        return False


def main() -> None:
    """主测试函数"""
    print("\n🚀 Phase 2 模块测试")
    print("=" * 70)

    results = {}

    # 测试各模块
    results["pdf_extractor"] = test_pdf_extractor()
    results["claim_parser"] = test_claim_parser()
    results["vector_processor"] = test_vector_processor()
    results["kg_builder"] = test_kg_builder()
    results["postgresql_updater"] = test_postgresql_updater()
    results["pipeline"] = test_pipeline()

    # 输出总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)

    for name, result in results.items():
        if result is True:
            status = "✅ 通过"
        elif result is False:
            status = "❌ 失败"
        else:
            status = "⏭️  跳过"
        print(f"   {name}: {status}")

    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)

    print(f"\n总计: {len(results)}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"跳过: {skipped}")


if __name__ == "__main__":
    main()
