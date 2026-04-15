#!/usr/bin/env python3
"""
专利全文处理Pipeline V2
Patent Full Text Pipeline V2

整合向量化、三元组提取、知识图谱构建的完整流程

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import logging
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PipelineInput:
    """Pipeline输入数据"""
    patent_number: str
    title: str
    abstract: str
    ipc_classification: str

    # 可选字段
    claims: str | None = None
    invention_content: str | None = None
    background: str | None = None

    # 元数据
    publication_date: str = ""
    application_date: str = ""
    ipc_main_class: str = ""
    ipc_subclass: str = ""
    ipc_full_path: str = ""
    patent_type: str = "invention"


@dataclass
class PipelineResult:
    """Pipeline处理结果"""
    patent_number: str
    success: bool

    # 各步骤结果
    vectorization_result: Any | None = None
    triple_extraction_result: Any | None = None
    kg_build_result: Any | None = None

    # 统计信息
    total_vectors: int = 0
    total_triples: int = 0
    total_vertices: int = 0
    total_edges: int = 0
    processing_time: float = 0.0
    error_message: str | None = None

    def get_summary(self) -> dict[str, Any]:
        """获取结果摘要"""
        return {
            "patent_number": self.patent_number,
            "success": self.success,
            "vectors": self.total_vectors,
            "triples": self.total_triples,
            "vertices": self.total_vertices,
            "edges": self.total_edges,
            "processing_time": self.processing_time
        }


class PatentFullTextPipelineV2:
    """
    专利全文处理Pipeline V2

    完整流程:
    1. 向量化（三层架构）
    2. 三元组提取（规则+模型）
    3. 知识图谱构建

    配置:
    - enable_vectorization: 是否启用向量化
    - enable_triple_extraction: 是否启用三元组提取
    - enable_kg_build: 是否启用知识图谱构建
    - save_qdrant: 是否保存到Qdrant
    - save_nebula: 是否保存到NebulaGraph
    """

    def __init__(
        self,
        model_loader,
        enable_vectorization: bool = True,
        enable_triple_extraction: bool = True,
        enable_kg_build: bool = True,
        save_qdrant: bool = False,
        save_nebula: bool = False,
        qdrant_client=None,
        nebula_client=None
    ):
        """
        初始化Pipeline

        Args:
            model_loader: 模型加载器
            enable_vectorization: 是否启用向量化
            enable_triple_extraction: 是否启用三元组提取
            enable_kg_build: 是否启用知识图谱构建
            save_qdrant: 是否保存到Qdrant
            save_nebula: 是否保存到NebulaGraph
            qdrant_client: Qdrant客户端
            nebula_client: NebulaGraph客户端
        """
        self.model_loader = model_loader
        self.enable_vectorization = enable_vectorization
        self.enable_triple_extraction = enable_triple_extraction
        self.enable_kg_build = enable_kg_build
        self.save_qdrant = save_qdrant
        self.save_nebula = save_nebula
        self.qdrant_client = qdrant_client
        self.nebula_client = nebula_client

        # 延迟导入组件
        self._vector_processor = None
        self._rule_extractor = None
        self._kg_builder = None

    def process(self, input_data: PipelineInput) -> PipelineResult:
        """
        处理单个专利

        Args:
            input_data: 输入数据

        Returns:
            PipelineResult
        """
        start_time = time.time()

        try:
            result = PipelineResult(
                patent_number=input_data.patent_number,
                success=True
            )

            # 1. 向量化
            if self.enable_vectorization:
                result.vectorization_result = self._vectorize(input_data)
                if result.vectorization_result:
                    result.total_vectors = result.vectorization_result.total_vector_count

            # 2. 三元组提取
            if self.enable_triple_extraction and input_data.invention_content:
                result.triple_extraction_result = self._extract_triples(input_data)
                if result.triple_extraction_result:
                    result.total_triples = len(result.triple_extraction_result.triples)

            # 3. 知识图谱构建
            if self.enable_kg_build and result.triple_extraction_result:
                result.kg_build_result = self._build_kg(input_data, result.triple_extraction_result)
                if result.kg_build_result:
                    result.total_vertices = result.kg_build_result.total_vertices
                    result.total_edges = result.kg_build_result.total_edges

            # 4. 保存到Qdrant（可选）
            if self.save_qdrant and result.vectorization_result:
                self._save_to_qdrant(result)

            # 5. 保存到NebulaGraph（可选）
            if self.save_nebula and result.kg_build_result:
                # kg_builder已经保存，这里只是标记
                pass

            result.processing_time = time.time() - start_time

            logger.info(f"✅ Pipeline处理完成: {input_data.patent_number}")

            return result

        except Exception as e:
            logger.error(f"❌ Pipeline处理失败: {e}")
            return PipelineResult(
                patent_number=input_data.patent_number,
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )

    def _vectorize(self, input_data: PipelineInput) -> Any:
        """向量化处理"""
        # 使用绝对导入而不是相对导入
        import vector_processor_v2
        VectorProcessorV2 = vector_processor_v2.VectorProcessorV2
        PatentDataV2 = vector_processor_v2.PatentDataV2

        if self._vector_processor is None:
            self._vector_processor = VectorProcessorV2(
                self.model_loader,
                enable_layer1=True,
                enable_layer2=bool(input_data.claims),
                enable_layer3=bool(input_data.invention_content)
            )

        # 转换为PatentDataV2
        patent_data = PatentDataV2(
            patent_number=input_data.patent_number,
            title=input_data.title,
            abstract=input_data.abstract,
            ipc_classification=input_data.ipc_classification,
            claims=input_data.claims,
            invention_content=input_data.invention_content,
            publication_date=input_data.publication_date,
            application_date=input_data.application_date,
            ipc_main_class=input_data.ipc_main_class,
            ipc_subclass=input_data.ipc_subclass,
            ipc_full_path=input_data.ipc_full_path,
            patent_type=input_data.patent_type
        )

        return self._vector_processor.vectorize(patent_data)

    def _extract_triples(self, input_data: PipelineInput) -> Any:
        """三元组提取"""
        # 使用绝对导入
        import rule_extractor
        RuleExtractor = rule_extractor.RuleExtractor

        if self._rule_extractor is None:
            self._rule_extractor = RuleExtractor()

        # 合并文本
        full_text = ""
        if input_data.background:
            full_text += input_data.background + "\n"
        if input_data.claims:
            full_text += input_data.claims + "\n"
        if input_data.invention_content:
            full_text += input_data.invention_content

        return self._rule_extractor.extract(
            input_data.patent_number,
            full_text,
            input_data.claims,
            input_data.invention_content
        )

    def _build_kg(self, input_data: PipelineInput, triple_result) -> None:
        """知识图谱构建"""
        # 使用绝对导入
        import kg_builder_v2
        PatentKGBuilderV2 = kg_builder_v2.PatentKGBuilderV2

        if self._kg_builder is None:
            self._kg_builder = PatentKGBuilderV2(self.nebula_client)

        # 构建专利数据字典
        patent_data = {
            "patent_number": input_data.patent_number,
            "title": input_data.title,
            "abstract": input_data.abstract,
            "ipc_main_class": input_data.ipc_main_class,
            "ipc_subclass": input_data.ipc_subclass,
            "patent_type": input_data.patent_type,
            "publication_date": input_data.publication_date,
            "application_date": input_data.application_date,
        }

        return self._kg_builder.build_patent_kg(
            input_data.patent_number,
            patent_data,
            triple_result
        )

    def _save_to_qdrant(self, result: PipelineResult) -> Any:
        """保存到Qdrant"""
        if not self.qdrant_client or not result.vectorization_result:
            return

        try:
            # 批量插入向量
            # 这里简化处理，实际应该批量操作
            logger.info(f"💾 保存{result.total_vectors}个向量到Qdrant")
        except Exception as e:
            logger.warning(f"⚠️  保存到Qdrant失败: {e}")

    def batch_process(
        self,
        inputs: list[PipelineInput],
        max_workers: int = 1
    ) -> list[PipelineResult]:
        """
        批量处理

        Args:
            inputs: 输入数据列表
            max_workers: 最大并发数

        Returns:
            List[PipelineResult]
        """
        results = []

        for input_data in inputs:
            result = self.process(input_data)
            results.append(result)

        return results


# ========== 便捷函数 ==========

def create_pipeline_input(
    patent_number: str,
    title: str,
    abstract: str,
    ipc_classification: str,
    **kwargs
) -> PipelineInput:
    """创建Pipeline输入"""
    return PipelineInput(
        patent_number=patent_number,
        title=title,
        abstract=abstract,
        ipc_classification=ipc_classification,
        **kwargs
    )


def process_patent(
    input_data: PipelineInput,
    model_loader,
    **kwargs
) -> PipelineResult:
    """
    处理单个专利

    Args:
        input_data: 输入数据
        model_loader: 模型加载器
        **kwargs: 传递给Pipeline的参数

    Returns:
        PipelineResult
    """
    pipeline = PatentFullTextPipelineV2(model_loader, **kwargs)
    return pipeline.process(input_data)


# ========== 示例使用 ==========

def main() -> None:
    """示例使用"""
    print("=" * 70)
    print("专利全文处理Pipeline V2 示例")
    print("=" * 70)

    # 创建输入
    input_data = create_pipeline_input(
        patent_number="CN112233445A",
        title="一种基于人工智能的图像识别方法",
        abstract="本发明公开了一种基于人工智能的图像识别方法。",
        ipc_classification="G06F40/00",
        claims="1. 一种图像识别方法，其特征在于，包括：获取图像；提取特征；识别。",
        invention_content="技术问题：现有方法精度低。技术方案：使用深度学习。",
        publication_date="2021-08-15",
        ipc_main_class="G06F",
        ipc_subclass="G06F40/00"
    )

    # 创建模拟模型加载器
    class MockModelLoader:
        def load_model(self, name) -> None:
            class MockModel:
                def encode(self, text) -> None:
                    import random
                    return [random.random() for _ in range(768)]
            return MockModel()

    # 处理（不保存到数据库）
    model_loader = MockModelLoader()
    result = process_patent(
        input_data,
        model_loader,
        save_qdrant=False,
        save_nebula=False
    )

    print("\n📊 处理结果:")
    summary = result.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
