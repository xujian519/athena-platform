#!/usr/bin/env python3

"""
技术图纸分析器测试脚本

使用示例:
1. 基础图纸识别
2. 分块处理大图纸
3. 与说明书关联分析
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 测试文件允许依赖具体实现
# TODO: 考虑使用Mock对象替代真实依赖
# TODO: ARCHITECTURE - 需要迁移到依赖注入模式
from services.ai_models.glm_full_suite.glm_unified_client import ZhipuAIUnifiedClient

from core.ai.perception.technical_drawing_analyzer import AnalysisLevel, TechnicalDrawingAnalyzer


async def test_basic_analysis():
    """测试1: 基础图纸分析"""
    print("\n" + "=" * 60)
    print("🧪 测试1: 基础图纸识别")
    print("=" * 60)

    # 创建GLM客户端
    async with ZhipuAIUnifiedClient() as glm_client:
        # 创建分析器
        analyzer = TechnicalDrawingAnalyzer(
            glm_client=glm_client,
            max_image_size=2048,
            chunk_size=1024,
            enable_chunking=False,  # 先测试整体分析
        )

        # 测试图像路径(请替换为实际路径)
        test_image = (
            "/Users/xujian/工作/01_客户管理/01_正式客户/博信物流1件/说明书附图/test_drawing.jpg"
        )

        if not Path(test_image).exists():
            print(f"⚠️ 测试图像不存在: {test_image}")
            print("请提供有效的技术图纸路径")
            return

        # 执行分析
        print(f"📊 正在分析: {test_image}")
        result = await analyzer.analyze(image_path=test_image, analysis_level=AnalysisLevel.BASIC)

        # 输出结果
        print("\n✅ 分析完成!")
        print(f"   图纸类型: {result.drawing_type.value}")
        print(f"   标题: {result.title}")
        print(f"   描述: {result.description[:200]}...")
        print(f"   置信度: {result.confidence:.2f}")
        print(f"   处理时间: {result.processing_time:.2f}秒")
        print(f"   使用模型: {result.model_used}")
        print(f"   Token消耗: {result.tokens_used}")

        if result.components:
            print(f"\n🔧 识别的组件 ({len(result.components)}个):")
            for comp in result.components[:10]:
                if isinstance(comp, dict):
                    print(
                        f"   - {comp.get('name', comp.get('id', '未知'))}: {comp.get('description', '')[:50]}"
                    )

        if result.technical_features:
            print("\n⚙️ 技术特征:")
            for feature in result.technical_features:
                print(f"   - {feature}")


async def test_chunked_analysis():
    """测试2: 分块处理大图纸"""
    print("\n" + "=" * 60)
    print("🧪 测试2: 分块处理大图纸")
    print("=" * 60)

    async with ZhipuAIUnifiedClient() as glm_client:
        analyzer = TechnicalDrawingAnalyzer(
            glm_client=glm_client,
            max_image_size=4096,
            chunk_size=1024,
            enable_chunking=True,  # 启用分块
        )

        # 大图纸路径
        test_image = (
            "/Users/xujian/工作/01_客户管理/01_正式客户/博信物流1件/说明书附图/large_drawing.jpg"
        )

        if not Path(test_image).exists():
            print(f"⚠️ 测试图像不存在: {test_image}")
            return

        print(f"📊 正在分块分析: {test_image}")
        result = await analyzer.analyze(
            image_path=test_image, analysis_level=AnalysisLevel.INTERMEDIATE
        )

        print("\n✅ 分块分析完成!")
        print(f"   处理时间: {result.processing_time:.2f}秒")

        # 显示统计
        stats = analyzer.get_statistics()
        print("\n📈 统计信息:")
        print(f"   总分析数: {stats['total_analyses']}")
        print(f"   成功数: {stats['successful_analyses']}")
        print(f"   处理分块数: {stats['total_chunks_processed']}")


async def test_with_specification():
    """测试3: 与说明书关联分析"""
    print("\n" + "=" * 60)
    print("🧪 测试3: 与说明书关联分析")
    print("=" * 60)

    async with ZhipuAIUnifiedClient() as glm_client:
        analyzer = TechnicalDrawingAnalyzer(glm_client=glm_client, enable_chunking=True)

        # 准备说明书文本
        specification_text = """
        本发明涉及一种温室大棚开窗通风装置,包括:
        1. 固定框架:安装在温室大棚顶部
        2. 开窗扇:通过铰链与固定框架连接
        3. 传动机构:采用齿轮齿条传动,包括电机、齿轮、齿条
        4. 连接臂:连接齿条和开窗扇

        工作原理:电机驱动齿轮旋转,齿轮带动齿条直线运动,
        齿条通过连接臂推动开窗扇绕铰链转动,实现开启和关闭。
        开窗扇最大开启角度可达75度,确保通风效果。
        """

        # 准备权利要求
        claims = [
            "1. 一种温室大棚开窗通风装置,其特征在于,包括固定框架、开窗扇、传动机构和连接臂。",
            "2. 根据权利要求1所述的装置,其特征在于,传动机构采用齿轮齿条传动方式。",
            "3. 根据权利要求1所述的装置,其特征在于,开窗扇最大开启角度为75度。",
        ]

        test_image = "/Users/xujian/工作/01_客户管理/01_正式客户/博信物流1件/说明书附图/greenhouse_drawing.jpg"

        if not Path(test_image).exists():
            print(f"⚠️ 测试图像不存在: {test_image}")
            return

        print("📊 正在进行关联分析...")
        result = await analyzer.analyze(
            image_path=test_image,
            analysis_level=AnalysisLevel.ADVANCED,
            specification_text=specification_text,
            related_claims=claims,
        )

        print("\n✅ 关联分析完成!")
        print(f"   工作原理: {result.working_principle[:200]}...")

        if result.specification_reference:
            print(f"   说明书参考: {result.specification_reference[:100]}...")

        if result.related_claims:
            print(f"   关联权利要求: {len(result.related_claims)}条")


async def test_batch_processing():
    """测试4: 批量处理"""
    print("\n" + "=" * 60)
    print("🧪 测试4: 批量处理图纸")
    print("=" * 60)

    async with ZhipuAIUnifiedClient() as glm_client:
        analyzer = TechnicalDrawingAnalyzer(glm_client=glm_client, enable_chunking=True)

        # 批量处理目录
        drawings_dir = Path("/Users/xujian/工作/01_客户管理/01_正式客户/博信物流1件/说明书附图")

        if not drawings_dir.exists():
            print(f"⚠️ 目录不存在: {drawings_dir}")
            return

        # 查找所有图像文件
        image_files = list(drawings_dir.glob("*.jpg")) + list(drawings_dir.glob("*.png"))

        print(f"📁 找到 {len(image_files)} 个图像文件")

        results = []
        for i, image_file in enumerate(image_files[:5], 1):  # 最多处理5个
            print(f"\n[{i}/{min(5, len(image_files))}] 处理: {image_file.name}")

            try:
                result = await analyzer.analyze(
                    image_path=str(image_file), analysis_level=AnalysisLevel.INTERMEDIATE
                )
                results.append(result)

                print(f"   ✅ 类型: {result.drawing_type.value}")
                print(f"   ⏱️ 耗时: {result.processing_time:.2f}秒")

            except Exception as e:
                print(f"   ❌ 失败: {e!s}")

        # 输出汇总统计
        print("\n📊 批量处理汇总:")
        stats = analyzer.get_statistics()
        print(f"   成功处理: {stats['successful_analyses']}/{stats['total_analyses']}")
        print(f"   平均耗时: {stats['average_processing_time']:.2f}秒")

        # 按类型统计
        print("\n   图纸类型分布:")
        for dtype, count in stats["drawing_type_distribution"].items():
            print(f"   - {dtype}: {count}个")


async def main():
    """主函数"""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    print("\n" + "=" * 60)
    print("🎨 技术图纸智能分析器 - 测试套件")
    print("=" * 60)

    # 运行测试
    await test_basic_analysis()
    await test_chunked_analysis()
    await test_with_specification()
    await test_batch_processing()

    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

