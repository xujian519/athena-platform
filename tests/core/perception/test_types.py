#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
感知模块类型系统测试
Tests for Perception Module Type System
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path

from core.perception.types import (
    # 枚举类型
    InputType,
    DocumentType,
    ModalityType,
    ConfidenceLevel,
    ProcessingMode,
    StreamType,
    DocumentChangeType,
    AgentStatus,

    # 数据类
    PerceptionResult,
    PatentPerceptionResult,
    DocumentGraph,
    PatentDocumentStructure,
)


class TestEnums:
    """测试枚举类型"""

    def test_input_type_enum(self):
        """测试输入类型枚举"""
        assert InputType.TEXT.value == "text"
        assert InputType.IMAGE.value == "image"
        assert InputType.AUDIO.value == "audio"
        assert InputType.VIDEO.value == "video"
        assert InputType.MULTIMODAL.value == "multimodal"
        assert InputType.STREAM.value == "stream"
        assert InputType.UNKNOWN.value == "unknown"

    def test_document_type_enum(self):
        """测试文档类型枚举"""
        assert DocumentType.PATENT.value == "patent"
        assert DocumentType.CONTRACT.value == "contract"
        assert DocumentType.TECH_DISCLOSURE.value == "tech_disclosure"
        assert DocumentType.TECH_MANUAL.value == "tech_manual"
        assert DocumentType.TECH_DRAWING.value == "tech_drawing"
        assert DocumentType.SPECIFICATION.value == "specification"
        assert DocumentType.IMAGE.value == "image"
        assert DocumentType.UNKNOWN.value == "unknown"

    def test_modality_type_enum(self):
        """测试模态类型枚举"""
        assert ModalityType.TEXT.value == "text"
        assert ModalityType.IMAGE.value == "image"
        assert ModalityType.TABLE.value == "table"
        assert ModalityType.FORMULA.value == "formula"
        assert ModalityType.DRAWING.value == "drawing"
        assert ModalityType.MARKUP.value == "markup"
        assert ModalityType.STRUCTURE.value == "structure"
        assert ModalityType.CAD.value == "cad"
        assert ModalityType.HANDWRITING.value == "handwriting"
        assert ModalityType.MIXED.value == "mixed"

    def test_confidence_level_enum(self):
        """测试置信度等级枚举"""
        assert ConfidenceLevel.HIGH.value == 0.9
        assert ConfidenceLevel.MEDIUM.value == 0.6
        assert ConfidenceLevel.LOW.value == 0.3

    def test_processing_mode_enum(self):
        """测试处理模式枚举"""
        assert ProcessingMode.STANDARD.value == "standard"
        assert ProcessingMode.REALTIME.value == "realtime"
        assert ProcessingMode.BATCH.value == "batch"
        assert ProcessingMode.ADAPTIVE.value == "adaptive"
        assert ProcessingMode.PIPELINE.value == "pipeline"

    def test_stream_type_enum(self):
        """测试流类型枚举"""
        assert StreamType.TEXT.value == "text"
        assert StreamType.IMAGE.value == "image"
        assert StreamType.AUDIO.value == "audio"
        assert StreamType.VIDEO.value == "video"
        assert StreamType.MULTIMODAL.value == "multimodal"

    def test_document_change_type_enum(self):
        """测试文档变更类型枚举"""
        assert DocumentChangeType.CREATED.value == "created"
        assert DocumentChangeType.MODIFIED.value == "modified"
        assert DocumentChangeType.UNCHANGED.value == "unchanged"
        assert DocumentChangeType.PARTIAL_MODIFIED.value == "partial_modified"

    def test_agent_status_enum(self):
        """测试智能体状态枚举"""
        assert AgentStatus.INACTIVE.value == "inactive"
        assert AgentStatus.STARTING.value == "starting"
        assert AgentStatus.ACTIVE.value == "active"
        assert AgentStatus.BUSY.value == "busy"
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.STOPPING.value == "stopping"
        assert AgentStatus.ERROR.value == "error"


class TestPerceptionResult:
    """测试感知结果数据类"""

    def test_creation(self):
        """测试创建感知结果"""
        result = PerceptionResult(
            input_type=InputType.TEXT,
            raw_content="test content",
            processed_content={"processed": "content"},
            features={"feature1": "value1"},
            confidence=0.9,
            metadata={"key": "value"},
            timestamp=datetime.now()
        )
        assert result.input_type == InputType.TEXT
        assert result.raw_content == "test content"
        assert result.confidence == 0.9

    def test_default_values(self):
        """测试默认值"""
        now = datetime.now()
        result = PerceptionResult(
            input_type=InputType.IMAGE,
            raw_content=b"image_data",
            processed_content=None,
            features={},
            confidence=0.5,
            metadata={},
            timestamp=now
        )
        assert result.processed_content is None
        assert len(result.features) == 0


class TestPatentPerceptionResult:
    """测试专利感知结果数据类"""

    def test_creation_minimal(self):
        """测试最小化创建"""
        result = PatentPerceptionResult()
        assert result.patent_id is None
        assert result.input_type is None
        assert result.confidence == 0.0
        assert result.verification_needed is False

    def test_creation_full(self):
        """测试完整创建"""
        now = datetime.now()
        result = PatentPerceptionResult(
            patent_id="CN123456U",
            input_type="patent_pdf",
            modality_type="mixed",
            raw_content="PDF content",
            title="测试专利",
            abstract="测试摘要",
            technical_field="测试技术领域",
            ipc_classification=["F01", "G06"],
            features=[{"name": "feature1", "value": "value1"}],
            confidence=0.85,
            metadata={"source": "test"},
            timestamp=now,
            verification_needed=True
        )
        assert result.patent_id == "CN123456U"
        assert result.title == "测试专利"
        assert result.confidence == 0.85
        assert result.verification_needed is True

    def test_validate_success(self):
        """测试验证成功"""
        result = PatentPerceptionResult(confidence=0.8)
        assert result.validate() is True

    def test_validate_failure_low(self):
        """测试验证失败-置信度过低"""
        result = PatentPerceptionResult(confidence=-0.1)
        with pytest.raises(ValueError, match="无效的置信度"):
            result.validate()

    def test_validate_failure_high(self):
        """测试验证失败-置信度过高"""
        result = PatentPerceptionResult(confidence=1.5)
        with pytest.raises(ValueError, match="无效的置信度"):
            result.validate()

    def test_default_timestamp(self):
        """测试默认时间戳"""
        before = datetime.now()
        result = PatentPerceptionResult()
        after = datetime.now()
        assert before <= result.timestamp <= after

    def test_structured_content_default(self):
        """测试结构化内容默认值"""
        result = PatentPerceptionResult()
        assert result.structured_content == {}
        assert isinstance(result.structured_content, dict)

    def test_features_default(self):
        """测试特征默认值"""
        result = PatentPerceptionResult()
        assert result.features == []
        assert isinstance(result.features, list)

    def test_cross_references_default(self):
        """测试交叉引用默认值"""
        result = PatentPerceptionResult()
        assert result.cross_references == []
        assert isinstance(result.cross_references, list)

    def test_family_comment_default(self):
        """测试家庭评论默认值"""
        result = PatentPerceptionResult()
        assert result.family_comment == ""


class TestDocumentGraph:
    """测试文档图数据类"""

    def test_creation(self):
        """测试创建文档图"""
        graph = DocumentGraph(
            document_id="doc123",
            document_type=DocumentType.PATENT,
            nodes=[{"id": "n1", "type": "entity"}],
            edges=[{"source": "n1", "target": "n2", "type": "relation"}],
            cross_modal_alignments=[],
            context_state={"key": "value"},
            knowledge_injections=[]
        )
        assert graph.document_id == "doc123"
        assert graph.document_type == DocumentType.PATENT
        assert len(graph.nodes) == 1
        assert len(graph.edges) == 1

    def test_empty_graph(self):
        """测试空图"""
        graph = DocumentGraph(
            document_id="doc456",
            document_type=DocumentType.UNKNOWN,
            nodes=[],
            edges=[],
            cross_modal_alignments=[],
            context_state={},
            knowledge_injections=[]
        )
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0


class TestPatentDocumentStructure:
    """测试专利文档结构数据类"""

    def test_creation(self):
        """测试创建专利文档结构"""
        structure = PatentDocumentStructure(
            title="专利标题",
            abstract="专利摘要",
            claims={1: "权利要求1", 2: "权利要求2"},
            description="详细描述",
            drawings=[{"id": "fig1", "type": "diagram"}],
            tables=[{"id": "table1", "rows": 5}],
            technical_specifications={"param1": "value1"}
        )
        assert structure.title == "专利标题"
        assert len(structure.claims) == 2
        assert structure.claims[1] == "权利要求1"

    def test_empty_claims(self):
        """测试空权利要求"""
        structure = PatentDocumentStructure(
            title="测试",
            abstract="摘要",
            claims={},
            description="描述",
            drawings=[],
            tables=[],
            technical_specifications={}
        )
        assert len(structure.claims) == 0

    def test_empty_collections(self):
        """测试空集合"""
        structure = PatentDocumentStructure(
            title="测试",
            abstract="摘要",
            claims={},
            description="描述",
            drawings=[],
            tables=[],
            technical_specifications={}
        )
        assert len(structure.drawings) == 0
        assert len(structure.tables) == 0


class TypeIntegrationTests:
    """类型集成测试"""

    def test_patent_result_with_structure(self):
        """测试专利结果与结构集成"""
        now = datetime.now()
        result = PatentPerceptionResult(
            patent_id="CN123456U",
            input_type="patent_pdf",
            modality_type="mixed",
            title="测试专利",
            abstract="测试摘要",
            confidence=0.9,
            timestamp=now
        )

        structure = PatentDocumentStructure(
            title=result.title,
            abstract=result.abstract,
            claims={1: "权利要求1"},
            description="描述",
            drawings=[],
            tables=[],
            technical_specifications={}
        )

        assert result.title == structure.title
        assert result.abstract == structure.abstract

    def test_document_graph_with_patent_result(self):
        """测试文档图与专利结果集成"""
        graph = DocumentGraph(
            document_id="patent_123",
            document_type=DocumentType.PATENT,
            nodes=[],
            edges=[],
            cross_modal_alignments=[],
            context_state={},
            knowledge_injections=[]
        )

        result = PatentPerceptionResult(
            patent_id=graph.document_id,
            input_type="patent_graph",
            confidence=0.85
        )

        assert result.patent_id == graph.document_id
        assert graph.document_type == DocumentType.PATENT

    def test_modality_types_with_result(self):
        """测试模态类型与结果集成"""
        result = PatentPerceptionResult(
            input_type="patent_image",
            modality_type=ModalityType.IMAGE.value,
            confidence=0.8
        )

        assert result.modality_type == ModalityType.IMAGE.value

    def test_confidence_levels(self):
        """测试置信度等级"""
        high_confidence = PatentPerceptionResult(
            confidence=ConfidenceLevel.HIGH.value
        )
        assert high_confidence.confidence >= 0.9

        medium_confidence = PatentPerceptionResult(
            confidence=ConfidenceLevel.MEDIUM.value
        )
        assert medium_confidence.confidence >= 0.6

        low_confidence = PatentPerceptionResult(
            confidence=ConfidenceLevel.LOW.value
        )
        assert low_confidence.confidence >= 0.3

    def test_processing_mode_with_result(self):
        """测试处理模式与结果集成"""
        result = PatentPerceptionResult(
            metadata={"processing_mode": ProcessingMode.BATCH.value}
        )
        assert result.metadata["processing_mode"] == ProcessingMode.BATCH.value
