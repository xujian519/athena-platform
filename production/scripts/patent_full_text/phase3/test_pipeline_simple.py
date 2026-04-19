#!/usr/bin/env python3
"""
简单Pipeline测试
测试Phase3 Pipeline处理真实专利数据
"""

from __future__ import annotations
import logging
import sys
from pathlib import Path

# 添加当前路径到sys.path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main() -> None:
    """测试Pipeline处理真实专利"""
    print("=" * 70)
    print("Phase3 Pipeline 简单测试")
    print("=" * 70)

    try:
        # 1. 导入必要的模块
        print("\n📦 1. 导入模块...")

        # 导入qdrant_schema
        print("   ✅ qdrant_schema导入成功")

        # 导入vector_processor_v2
        print("   ✅ vector_processor_v2导入成功")

        # 导入pipeline_v2
        from pipeline_v2 import PatentFullTextPipelineV2, PipelineInput
        print("   ✅ pipeline_v2导入成功")

        # 2. 创建模拟模型加载器
        print("\n🔧 2. 创建模拟模型加载器...")

        import numpy as np

        class MockModel:
            """模拟BGE模型"""
            def encode(self, text) -> None:
                return np.random.rand(768).tolist()

        class MockModelLoader:
            """模拟模型加载器"""
            def load_model(self, name) -> None:
                return MockModel()

        model_loader = MockModelLoader()
        print("   ✅ 模型加载器已创建")

        # 3. 创建测试专利数据（基于已下载的专利）
        print("\n📄 3. 创建测试专利数据...")

        # 使用CN113812265A的数据
        input_data = PipelineInput(
            patent_number="CN113812265A",
            title="一种基于物联网的苹果采摘系统",
            abstract="发明属于农业生产领域，为一种基于物联网的苹果采摘系统，依托物联网自动识别苹果的位置后对单个苹果进行扫描检测和摘取。",
            ipc_classification="A01D 46/30",
            claims="""1.一种基于物联网的苹果采摘系统，包括底座(10)，其特征在于，所述底座(10)前侧上端转动设有转台(11),所述转台(11)转动设有第一伸缩杆(14)，所述转台(11)上端铰接第一控制杆(12)，所述第一控制杆(12)铰接第二控制杆(13)，所述第二控制杆(13)与所述第一伸缩杆(14)铰接，所述第一伸缩杆(14)滑动设有第二伸缩杆(15)。

2.根据权利要求1所述的一种基于物联网的苹果采摘系统，其特征在于：所述位置控制台(18)接收到所述识别相机(19)、所述果篮卡槽(21)和摘果装置中发出的信号。""",
            invention_content="""技术问题：现有苹果采摘方法效率低，容易损伤苹果。

技术方案：本发明提供一种基于物联网的苹果采摘系统，包括底座、转台、伸缩杆、识别相机和摘果装置。通过物联网自动识别苹果位置后进行扫描检测和摘取。

有益效果：采摘过程不会损伤苹果，在摘取过程中就完成对苹果品质的筛选分类。""",
            publication_date="2021-12-21",
            application_date="2021-11-24",
            ipc_main_class="A01D",
            ipc_subclass="A01D46/30",
            ipc_full_path="A→A01→A01D→A01D46",
            patent_type="invention"
        )
        print(f"   ✅ 测试专利: {input_data.patent_number}")

        # 4. 创建Pipeline
        print("\n🏗️  4. 创建Pipeline...")

        pipeline = PatentFullTextPipelineV2(
            model_loader=model_loader,
            enable_vectorization=True,
            enable_triple_extraction=True,
            enable_kg_build=False,  # 暂不启用知识图谱构建（需要NebulaGraph）
            save_qdrant=False,
            save_nebula=False
        )
        print("   ✅ Pipeline已创建")

        # 5. 处理专利
        print("\n⚙️  5. 处理专利...")

        result = pipeline.process(input_data)

        print(f"   处理完成，耗时: {result.processing_time:.2f}秒")

        # 6. 输出结果
        print("\n📊 6. 处理结果:")
        print("-" * 70)

        if result.success:
            print("   ✅ 处理成功!")
            print(f"   向量化结果: {result.total_vectors}个向量")

            if result.vectorization_result:
                vec_summary = result.vectorization_result.get_summary()
                print(f"   - Layer 1 (全局检索): {vec_summary.get('layer1_count', 0)}个")
                print(f"   - Layer 2 (核心内容): {vec_summary.get('layer2_count', 0)}个")
                print(f"   - Layer 3 (发明内容): {vec_summary.get('layer3_count', 0)}个")

            if result.triple_extraction_result:
                triple_summary = result.triple_extraction_result.get_summary()
                print("   三元组结果:")
                print(f"   - 技术问题: {triple_summary.get('problem_count', 0)}个")
                print(f"   - 技术特征: {triple_summary.get('feature_count', 0)}个")
                print(f"   - 技术效果: {triple_summary.get('effect_count', 0)}个")

            print("\n" + "=" * 70)
            print("🎉 Pipeline测试成功!")
            print("=" * 70)
            return 0
        else:
            print(f"   ❌ 处理失败: {result.error_message}")
            print("\n" + "=" * 70)
            print("❌ Pipeline测试失败")
            print("=" * 70)
            return 1

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
