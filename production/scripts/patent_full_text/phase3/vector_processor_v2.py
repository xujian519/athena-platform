#!/usr/bin/env python3
"""
向量化处理器 V2
Vector Processor V2

实现三层向量化架构：
- Layer 1: 全局检索层（标题/摘要/IPC）
- Layer 2: 核心内容层（分条款向量化）
- Layer 3: 发明内容层（分段向量化）

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import logging
import time
from dataclasses import dataclass
from typing import Any

# 导入类型定义
from qdrant_schema import VectorInfo, VectorizationResultV2, VectorPayload, VectorType

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

# ContentSection需要从content_chunker导入（因为分块器使用自己的枚举）
# 将在需要时动态导入

logger = logging.getLogger(__name__)


@dataclass
class PatentDataV2:
    """专利数据结构（用于向量化）"""
    patent_number: str
    title: str
    abstract: str
    ipc_classification: str

    # 可选字段
    claims: str | None = None          # 权利要求书全文
    invention_content: str | None = None  # 发明内容全文

    # 元数据
    publication_date: str = ""           # YYYY-MM-DD
    application_date: str = ""
    ipc_main_class: str = ""
    ipc_subclass: str = ""
    ipc_full_path: str = ""
    patent_type: str = "invention"


class VectorProcessorV2:
    """
    向量化处理器V2

    支持三层向量化:
    1. Layer 1: 全局检索层 - 标题/摘要/IPC向量化
    2. Layer 2: 核心内容层 - 分条款向量化
    3. Layer 3: 发明内容层 - 分段向量化
    """

    def __init__(
        self,
        model_loader,
        enable_layer1: bool = True,
        enable_layer2: bool = True,
        enable_layer3: bool = True
    ):
        """
        初始化向量化处理器

        Args:
            model_loader: 模型加载器实例
            enable_layer1: 是否启用Layer 1
            enable_layer2: 是否启用Layer 2
            enable_layer3: 是否启用Layer 3
        """
        self.model_loader = model_loader
        self.enable_layer1 = enable_layer1
        self.enable_layer2 = enable_layer2
        self.enable_layer3 = enable_layer3

        # 延迟初始化解析器（避免循环导入）
        self.claim_parser = None
        self.content_chunker = None

        # 加载BGE模型
        self.embedding_model = None
        self._load_model()

        # 初始化解析器（在模型加载后）
        if enable_layer2:
            # 使用绝对导入
            import claim_parser_v2
            ClaimParserV2 = claim_parser_v2.ClaimParserV2
            self.claim_parser = ClaimParserV2()
        if enable_layer3:
            import content_chunker
            ContentChunker = content_chunker.ContentChunker
            self.content_chunker = ContentChunker()

    def _load_model(self) -> Any:
        """加载向量化模型"""
        try:
            self.embedding_model = self.model_loader.load_model("BAAI/bge-m3")
            logger.info("✅ BGE向量化模型加载成功")
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            raise

    def vectorize(self, patent_data: PatentDataV2) -> VectorizationResultV2:
        """
        向量化单个专利

        Args:
            patent_data: 专利数据

        Returns:
            VectorizationResultV2 向量化结果
        """
        start_time = time.time()

        try:
            result = VectorizationResultV2(
                patent_number=patent_data.patent_number,
                success=True
            )

            # Layer 1: 全局检索层
            if self.enable_layer1:
                result.layer1_vectors = self._vectorize_layer1(patent_data)

            # Layer 2: 核心内容层
            if self.enable_layer2 and patent_data.claims:
                result.layer2_vectors = self._vectorize_layer2(patent_data)

            # Layer 3: 发明内容层
            if self.enable_layer3 and patent_data.invention_content:
                result.layer3_vectors = self._vectorize_layer3(patent_data)

            result.total_vector_count = len(result.all_vectors)
            result.processing_time = time.time() - start_time

            logger.info(f"✅ 向量化完成: {result.patent_number}, "
                       f"{result.total_vector_count}个向量")

            return result

        except Exception as e:
            logger.error(f"❌ 向量化失败: {e}")
            return VectorizationResultV2(
                patent_number=patent_data.patent_number,
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )

    def _vectorize_layer1(self, patent_data: PatentDataV2) -> list[VectorInfo]:
        """Layer 1: 全局检索层向量化"""
        vectors = []

        # 1. 标题向量
        if patent_data.title:
            vector = self._create_vector(
                patent_data,
                VectorType.TITLE,
                patent_data.title,
                section="标题"
            )
            vectors.append(vector)

        # 2. 摘要向量
        if patent_data.abstract:
            vector = self._create_vector(
                patent_data,
                VectorType.ABSTRACT,
                patent_data.abstract,
                section="摘要"
            )
            vectors.append(vector)

        # 3. IPC分类向量
        if patent_data.ipc_classification:
            vector = self._create_vector(
                patent_data,
                VectorType.IPC_CLASSIFICATION,
                patent_data.ipc_classification,
                section="IPC分类"
            )
            vectors.append(vector)

        return vectors

    def _vectorize_layer2(self, patent_data: PatentDataV2) -> list[VectorInfo]:
        """Layer 2: 核心内容层向量化（分条款）"""
        vectors = []

        # 解析权利要求
        parsed_claims = self.claim_parser.parse(
            patent_data.patent_number,
            patent_data.claims
        )

        if not parsed_claims.success:
            logger.warning(f"权利要求解析失败: {parsed_claims.error_message}")
            return vectors

        # 对每条权利要求向量化
        for claim in parsed_claims.all_claims:
            vector_type = (
                VectorType.INDEPENDENT_CLAIM
                if claim.claim_type.value == "independent"
                else VectorType.DEPENDENT_CLAIM
            )

            vector = self._create_vector(
                patent_data,
                vector_type,
                claim.claim_body,
                section=f"权利要求{claim.claim_number}",
                claim_number=claim.claim_number,
                claim_type=claim.claim_type.value
            )
            vectors.append(vector)

        return vectors

    def _vectorize_layer3(self, patent_data: PatentDataV2) -> list[VectorInfo]:
        """Layer 3: 发明内容层向量化（分段）"""
        vectors = []

        # 分块
        chunked_content = self.content_chunker.chunk(
            patent_data.patent_number,
            patent_data.invention_content
        )

        if not chunked_content.success:
            logger.warning(f"内容分块失败: {chunked_content.error_message}")
            return vectors

        # 动态导入ContentSection枚举（来自content_chunker模块）
        import content_chunker
        ContentSection = content_chunker.ContentSection

        # 对每个分块向量化
        for chunk in chunked_content.all_chunks:
            # 映射分段类型到向量类型
            vector_type_mapping = {
                ContentSection.TECHNICAL_PROBLEM: VectorType.TECHNICAL_PROBLEM,
                ContentSection.TECHNICAL_SOLUTION: VectorType.TECHNICAL_SOLUTION,
                ContentSection.BENEFICIAL_EFFECT: VectorType.BENEFICIAL_EFFECT,
                ContentSection.EMBODIMENT: VectorType.EMBODIMENT
            }

            vector_type = vector_type_mapping.get(chunk.section_type)

            # 跳过未映射的分段类型
            if vector_type is None:
                logger.warning(f"未知的分段类型: {chunk.section_type}")
                continue

            vector = self._create_vector(
                patent_data,
                vector_type,
                chunk.content,
                section=chunk.section_type.value,
                content_section=chunk.section_type.value,
                chunk_index=chunk.chunk_index,
                total_chunks=chunk.total_chunks
            )
            vectors.append(vector)

        return vectors

    def _create_vector(
        self,
        patent_data: PatentDataV2,
        vector_type: VectorType,
        text: str,
        **kwargs
    ) -> VectorInfo:
        """
        创建单个向量

        Args:
            patent_data: 专利数据
            vector_type: 向量类型
            text: 待向量化文本
            **kwargs: 额外的payload字段

        Returns:
            VectorInfo
        """
        # 计算向量
        embedding = self.embedding_model.encode(text)

        # 计算token数（粗略估计，中文1字≈1token）
        token_count = len(text)

        # 计算MD5
        text_hash = short_hash(text.encode())

        # 创建payload - 处理section避免重复参数
        section_value = kwargs.pop('section', vector_type.value)

        # 处理日期格式（可能为空）
        pub_date = patent_data.publication_date.replace('-', '') if patent_data.publication_date else 0
        app_date = patent_data.application_date.replace('-', '') if patent_data.application_date else 0

        payload = VectorPayload(
            patent_number=patent_data.patent_number,
            publication_date=int(pub_date) if pub_date else 0,
            application_date=int(app_date) if app_date else 0,
            ipc_main_class=patent_data.ipc_main_class or "",
            ipc_subclass=patent_data.ipc_subclass or "",
            ipc_full_path=patent_data.ipc_full_path or "",
            patent_type=patent_data.patent_type or "invention",
            vector_type=vector_type.value,
            section=section_value,
            text=text[:500],  # 只存储前500字符
            text_hash=text_hash,
            token_count=token_count,
            language='zh',
            **kwargs
        )

        # 创建向量信息
        vector_id = f"{patent_data.patent_number}_{vector_type.value}"
        if 'claim_number' in kwargs:
            vector_id += f"_{kwargs['claim_number']}"
        if 'chunk_index' in kwargs and kwargs.get('total_chunks', 1) > 1:
            vector_id += f"_{kwargs['chunk_index']}"

        return VectorInfo(
            vector_id=vector_id,
            vector_type=vector_type.value,
            patent_number=patent_data.patent_number,
            payload=payload
        )

    def batch_vectorize(
        self,
        patent_list: list[PatentDataV2],
        max_workers: int = 1
    ) -> list[VectorizationResultV2]:
        """
        批量向量化

        Args:
            patent_list: 专利数据列表
            max_workers: 最大并发数（暂不支持，预留）

        Returns:
            List[VectorizationResultV2]
        """
        results = []

        for patent_data in patent_list:
            result = self.vectorize(patent_data)
            results.append(result)

        return results


# ========== 便捷函数 ==========

def create_patent_data(
    patent_number: str,
    title: str,
    abstract: str,
    ipc_classification: str,
    **kwargs
) -> PatentDataV2:
    """创建专利数据对象"""
    return PatentDataV2(
        patent_number=patent_number,
        title=title,
        abstract=abstract,
        ipc_classification=ipc_classification,
        **kwargs
    )


def vectorize_patent(
    patent_data: PatentDataV2,
    model_loader,
    **kwargs
) -> VectorizationResultV2:
    """
    向量化单个专利

    Args:
        patent_data: 专利数据
        model_loader: 模型加载器
        **kwargs: 传递给VectorProcessorV2的参数

    Returns:
        VectorizationResultV2
    """
    processor = VectorProcessorV2(model_loader, **kwargs)
    return processor.vectorize(patent_data)


# ========== 示例使用 ==========

def main() -> None:
    """示例使用"""
    print("=" * 70)
    print("向量化处理器V2 示例")
    print("=" * 70)

    # 模拟加载模型（实际使用时需要真实的model_loader）
    class MockModelLoader:
        def load_model(self, name) -> None:
            class MockModel:
                def encode(self, text) -> None:
                    import numpy as np
                    return np.random.rand(768).tolist()
            return MockModel()

    # 示例专利数据
    patent_data = PatentDataV2(
        patent_number="CN112233445A",
        title="一种基于人工智能的图像识别方法",
        abstract="本发明公开了一种基于人工智能的图像识别方法，涉及图像处理技术领域。",
        ipc_classification="G06F40/00",
        claims="1. 一种图像识别方法，其特征在于，包括：获取图像；提取特征；识别分类。",
        invention_content="技术问题：现有方法精度低。技术方案：使用深度学习模型。",
        publication_date="2021-08-15",
        application_date="2020-12-01",
        ipc_main_class="G06F",
        ipc_subclass="G06F40/00",
        ipc_full_path="G→G06→G06F→G06F40"
    )

    # 向量化
    model_loader = MockModelLoader()
    result = vectorize_patent(patent_data, model_loader)

    print("\n📊 向量化结果:")
    summary = result.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    print("\n📦 各层向量分布:")
    print(f"  Layer 1 (全局检索): {len(result.layer1_vectors)}个")
    print(f"  Layer 2 (核心内容): {len(result.layer2_vectors)}个")
    print(f"  Layer 3 (发明内容): {len(result.layer3_vectors)}个")


if __name__ == "__main__":
    main()
