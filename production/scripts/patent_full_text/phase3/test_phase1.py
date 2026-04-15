#!/usr/bin/env python3
"""
Phase 1: 基础设施搭建 - 单元测试

验证Qdrant和NebulaGraph Schema创建是否成功

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import logging
import sys
from pathlib import Path
from typing import Any

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_qdrant_schema() -> Any:
    """测试Qdrant Schema定义"""
    print("=" * 70)
    print("测试1: Qdrant Schema定义")
    print("=" * 70)

    try:
        # 使用相对导入
        from qdrant_schema import (
            VectorPayload,
            VectorType,
            get_default_config,
            get_schema_manager,
        )

        # 1. 测试配置创建
        print("\n✅ 1.1 测试配置创建")
        config = get_default_config()
        assert config.collection_name == "patent_full_text_v2"
        assert config.vector_size == 768
        print(f"   集合名称: {config.collection_name}")
        print(f"   向量维度: {config.vector_size}")

        # 2. 测试Schema管理器
        print("\n✅ 1.2 测试Schema管理器")
        manager = get_schema_manager()
        assert manager.config.collection_name == "patent_full_text_v2"
        print("   管理器已创建")

        # 3. 测试向量类型枚举
        print("\n✅ 1.3 测试向量类型枚举")
        vector_types = [vt.value for vt in VectorType]
        assert "title" in vector_types
        assert "abstract" in vector_types
        assert "independent_claim" in vector_types
        assert "technical_problem" in vector_types
        print(f"   向量类型数量: {len(vector_types)}")

        # 4. 测试Payload创建
        print("\n✅ 1.4 测试Payload创建")
        payload = VectorPayload(
            patent_number="CN112233445A",
            publication_date=20210815,
            application_date=20201201,
            ipc_main_class="G06F",
            ipc_subclass="G06F40/00",
            ipc_full_path="G→G06→G06F→G06F40",
            patent_type="invention",
            vector_type="abstract",
            section="摘要",
            text="一种基于人工智能的图像识别方法...",
            token_count=156
        )
        assert payload.patent_number == "CN112233445A"
        assert payload.vector_type == "abstract"
        print(f"   Payload已创建: {payload.patent_number}")

        # 5. 测试Payload转换
        print("\n✅ 1.5 测试Payload转换")
        payload_dict = payload.to_dict()
        assert "patent_number" in payload_dict
        assert "vector_type" in payload_dict
        print("   Payload转字典成功")

        print("\n" + "=" * 70)
        print("✅ Qdrant Schema测试通过")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n❌ Qdrant Schema测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_nebula_schema() -> Any:
    """测试NebulaGraph Schema定义"""
    print("\n" + "=" * 70)
    print("测试2: NebulaGraph Schema定义")
    print("=" * 70)

    try:
        # 使用相对导入
        from nebula_schema import (
            NebulaSchemaDefinitions,
            NebulaSchemaManager,
            TechnicalEffect,
            TechnicalFeature,
            TechnicalProblem,
            Triple,
            TripleExtractionResult,
        )

        # 1. 测试Schema管理器创建
        print("\n✅ 2.1 测试Schema管理器创建")
        manager = NebulaSchemaManager()
        assert manager.space_name == "patent_full_text_v2"
        print(f"   空间名称: {manager.space_name}")

        # 2. 测试空间创建SQL
        print("\n✅ 2.2 测试空间创建SQL")
        space_sql = manager.get_create_space_sql()
        assert "CREATE SPACE" in space_sql
        assert "patent_full_text_v2" in space_sql
        print("   SQL已生成")

        # 3. 测试TAG定义
        print("\n✅ 2.3 测试TAG定义")
        tag_count = len(NebulaSchemaDefinitions.TAGS)
        assert "patent" in NebulaSchemaDefinitions.TAGS
        assert "technical_problem" in NebulaSchemaDefinitions.TAGS
        assert "technical_feature" in NebulaSchemaDefinitions.TAGS
        assert "technical_effect" in NebulaSchemaDefinitions.TAGS
        print(f"   TAG数量: {tag_count}")

        # 4. 测试EDGE定义
        print("\n✅ 2.4 测试EDGE定义")
        edge_count = len(NebulaSchemaDefinitions.EDGES)
        assert "SOLVES" in NebulaSchemaDefinitions.EDGES
        assert "ACHIEVES" in NebulaSchemaDefinitions.EDGES
        assert "RELATES_TO" in NebulaSchemaDefinitions.EDGES
        print(f"   EDGE数量: {edge_count}")

        # 5. 测试数据模型
        print("\n✅ 2.5 测试数据模型")

        problem = TechnicalProblem(
            id="p_001",
            description="现有图像识别方法精度低",
            problem_type="efficiency",
            source_section="background",
            severity=0.8
        )
        assert problem.problem_type == "efficiency"
        print(f"   TechnicalProblem: {problem.description}")

        feature = TechnicalFeature(
            id="f_001",
            description="基于深度学习的特征提取模块",
            feature_category="structural",
            feature_type="component",
            source_claim=1,
            importance=0.9
        )
        assert feature.feature_category == "structural"
        print(f"   TechnicalFeature: {feature.description}")

        effect = TechnicalEffect(
            id="e_001",
            description="提高图像识别准确率",
            effect_type="direct",
            quantifiable=True,
            metrics="10%"
        )
        assert effect.effect_type == "direct"
        print(f"   TechnicalEffect: {effect.description}")

        # 6. 测试三元组
        print("\n✅ 2.6 测试三元组")
        triple = Triple(
            subject=feature.id,
            relation="SOLVES",
            object=problem.id,
            confidence=0.95
        )
        assert triple.relation == "SOLVES"
        print(f"   Triple: {triple.subject} --[{triple.relation}]--> {triple.object}")

        # 7. 测试提取结果
        print("\n✅ 2.7 测试提取结果")
        result = TripleExtractionResult(
            patent_number="CN112233445A",
            success=True,
            problems=[problem],
            features=[feature],
            effects=[effect],
            triples=[triple],
            extraction_confidence=0.92
        )
        summary = result.get_summary()
        assert summary["problem_count"] == 1
        assert summary["feature_count"] == 1
        assert summary["triple_count"] == 1
        print(f"   提取结果摘要: {summary}")

        print("\n" + "=" * 70)
        print("✅ NebulaGraph Schema测试通过")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n❌ NebulaGraph Schema测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_loader() -> Any:
    """测试模型加载器"""
    print("\n" + "=" * 70)
    print("测试3: 模型加载器")
    print("=" * 70)

    try:
        # 使用相对导入
        from model_loader import get_model_loader

        # 1. 测试模型加载器创建
        print("\n✅ 3.1 测试模型加载器创建")
        loader = get_model_loader()
        assert loader is not None
        print("   加载器已创建")

        # 2. 测试模型注册
        print("\n✅ 3.2 测试已注册的模型")
        models = loader.models
        assert "BAAI/bge-m3" in models
        assert "chinese_legal_electra" in models
        print(f"   已注册模型数量: {len(models)}")

        # 3. 测试BGE模型加载（快速测试）
        print("\n✅ 3.3 测试BGE模型加载（可能需要10-20秒）")
        import time
        start_time = time.time()

        bge_model = loader.load_model("BAAI/bge-m3")
        load_time = time.time() - start_time

        assert bge_model is not None
        print(f"   BGE模型加载成功 (耗时: {load_time:.2f}秒)")

        # 4. 测试向量化
        print("\n✅ 3.4 测试向量化")
        test_text = "这是一种基于人工智能的图像识别方法"
        embedding = bge_model.encode(test_text)
        assert len(embedding) == 768
        print(f"   向量维度: {len(embedding)}")
        print("   测试通过")

        print("\n" + "=" * 70)
        print("✅ 模型加载器测试通过")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n❌ 模型加载器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config() -> Any:
    """测试配置文件"""
    print("\n" + "=" * 70)
    print("测试4: 配置文件")
    print("=" * 70)

    try:
        # 导入配置模块 - 使用importlib避免命名冲突
        import importlib.util
        phase2_path = Path(__file__).parent.parent / "phase2"
        spec = importlib.util.spec_from_file_location(
            "patent_config",
            phase2_path / "config.py"
        )
        patent_config = importlib.util.module_from_spec(spec)
        sys.modules["patent_config"] = patent_config  # 添加到sys.modules避免相对导入问题
        spec.loader.exec_module(patent_config)
        get_config = patent_config.get_config

        # 1. 测试配置加载
        print("\n✅ 4.1 测试配置加载")
        cfg = get_config()
        assert cfg is not None
        print("   配置已加载")

        # 2. 测试Phase 3配置
        print("\n✅ 4.2 测试Phase 3配置")
        assert hasattr(cfg, 'triple_extraction')
        assert hasattr(cfg, 'vectorization_v2')
        print(f"   triple_extraction: {cfg.triple_extraction.enable_rule_extraction}")
        print(f"   vectorization_v2: {cfg.vectorization_v2.enable_layer1}")

        # 3. 测试Qdrant配置更新
        print("\n✅ 4.3 测试Qdrant配置更新")
        assert cfg.qdrant.collection_name == "patent_full_text_v2"
        assert cfg.qdrant.enable_layered_vectorization == True
        print(f"   集合名称: {cfg.qdrant.collection_name}")

        # 4. 测试NebulaGraph配置更新
        print("\n✅ 4.4 测试NebulaGraph配置更新")
        assert cfg.nebula.space_name == "patent_full_text_v2"
        assert "technical_problem" in cfg.nebula.vertex_types
        assert "SOLVES" in cfg.nebula.edge_types
        print(f"   空间名称: {cfg.nebula.space_name}")
        print(f"   顶点类型数量: {len(cfg.nebula.vertex_types)}")
        print(f"   边类型数量: {len(cfg.nebula.edge_types)}")

        print("\n" + "=" * 70)
        print("✅ 配置文件测试通过")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n❌ 配置文件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main() -> None:
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("Phase 1: 基础设施搭建 - 单元测试")
    print("=" * 70)
    print("开始时间: 2025-12-25")
    print()

    results = {}

    # 运行测试
    results["Qdrant Schema"] = test_qdrant_schema()
    results["NebulaGraph Schema"] = test_nebula_schema()
    results["模型加载器"] = test_model_loader()
    results["配置文件"] = test_config()

    # 汇总结果
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)

    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {test_name}: {status}")

    total = len(results)
    passed = sum(results.values())

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 Phase 1 基础设施搭建完成！")
        print("\n下一步: 可以开始Phase 2 - 向量化实现")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查")

    print("=" * 70)


if __name__ == "__main__":
    main()
