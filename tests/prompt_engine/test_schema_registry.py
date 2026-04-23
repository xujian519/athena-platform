"""
Prompt Schema Registry 集成测试

覆盖:
- Schema 注册表初始化与内置 Schema 加载
- schema_id 检索
- domain / status 过滤
- 版本兼容性检查（向后兼容原则）
- 变量升级迁移
- Schema 覆盖率报告
- 高频使用 Schema 的完整性验证
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

# 隔离 core/ 中可能存在的语法错误模块
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import types

if "core" not in sys.modules:
    _core_pkg = types.ModuleType("core")
    _core_pkg.__path__ = []
    sys.modules["core"] = _core_pkg

for subpkg_path in [
    "core.legal_world_model",
    "core.database",
    "core.capabilities",
    "core.config",
    "core.legal_prompt_fusion",
    "core.prompt_engine",
]:
    if subpkg_path in sys.modules:
        continue
    mod = types.ModuleType(subpkg_path)
    mod.__path__ = [str(project_root / subpkg_path.replace(".", "/"))]
    sys.modules[subpkg_path] = mod
    parent_name, _, child_name = subpkg_path.rpartition(".")
    if parent_name in sys.modules:
        setattr(sys.modules[parent_name], child_name, mod)

# 在隔离后导入 Schema 模块
from core.prompt_engine.schema import PromptSchema, VariableSpec, VariableType
from core.prompt_engine.registry import PromptSchemaRegistry
from core.prompt_engine.validators import VariableValidator


class TestPromptSchemaRegistry:
    """PromptSchemaRegistry 核心功能测试。"""

    @pytest.fixture
    def registry(self):
        """返回全新的注册表实例。"""
        return PromptSchemaRegistry()

    def test_registry_loads_all_builtin_schemas(self, registry: PromptSchemaRegistry):
        """注册表应自动加载所有内置 Schema。"""
        all_ids = registry.list_all()
        assert len(all_ids) == 69
        # 关键 production schema 必须存在
        assert "patent.inventive_analysis.v2" in all_ids
        assert "patent.office_action.analysis.v2" in all_ids
        assert "hitl_safety_block" in all_ids
        assert "business/xiaonuo_l4_business_v2" in all_ids
        assert "capability/xiaonuo_l3_capability_v2" in all_ids
        assert "foundation/xiaonuo_decision_method_v1" in all_ids

    def test_get_existing_schema(self, registry: PromptSchemaRegistry):
        """通过 schema_id 获取已注册的 Schema。"""
        schema = registry.get("patent.inventive_analysis.v2")
        assert schema is not None
        assert schema.rule_id == "patent.inventive_analysis.v2"
        assert schema.template_version == "1.0.0"
        assert schema.version == "1.0.0"

    def test_get_nonexistent_schema_returns_none(self, registry: PromptSchemaRegistry):
        """获取不存在的 schema_id 应返回 None。"""
        assert registry.get("nonexistent.schema.id") is None

    def test_list_by_domain(self, registry: PromptSchemaRegistry):
        """按 domain 过滤 schema_id。"""
        root_ids = registry.list_by_domain("root")
        assert "patent.inventive_analysis.v2" in root_ids
        assert "README" in root_ids

        business_ids = registry.list_by_domain("business")
        assert "business/xiaonuo_l4_business_v2" in business_ids

        capability_ids = registry.list_by_domain("capability")
        assert "capability/xiaonuo_l3_capability_v2" in capability_ids

    def test_get_by_status_production(self, registry: PromptSchemaRegistry):
        """按 production 状态过滤。"""
        production_schemas = registry.get_by_status("production")
        assert len(production_schemas) == 6
        for s in production_schemas:
            assert s.template_version.startswith("1.0")

    def test_get_by_status_staging(self, registry: PromptSchemaRegistry):
        """按 staging 状态过滤。"""
        staging_schemas = registry.get_by_status("staging")
        assert len(staging_schemas) == 63
        for s in staging_schemas:
            assert s.template_version.startswith("0.9")

    def test_register_new_schema(self, registry: PromptSchemaRegistry):
        """动态注册新 Schema。"""
        new_schema = PromptSchema(
            rule_id="test/new_schema",
            template_version="0.1.0",
            variables=[VariableSpec(name="input", required=True)],
        )
        registry.register(new_schema)
        assert registry.get("test/new_schema") is new_schema
        assert "test/new_schema" in registry.list_by_domain("test")


class TestVersionCompatibility:
    """语义化版本兼容性测试（向后兼容原则）。"""

    @pytest.fixture
    def registry(self):
        return PromptSchemaRegistry()

    def test_same_version_is_compatible(self, registry: PromptSchemaRegistry):
        """相同版本完全兼容。"""
        assert registry.is_compatible("patent.inventive_analysis.v2", "1.0.0")

    def test_higher_minor_version_is_compatible(self, registry: PromptSchemaRegistry):
        """当前次版本号更高时兼容（向后兼容）。"""
        schema = registry.get("patent.inventive_analysis.v2")
        assert schema is not None
        # 模拟升级到 1.1.0（新增可选变量）
        schema.template_version = "1.1.0"
        assert registry.is_compatible("patent.inventive_analysis.v2", "1.0.0")
        assert registry.is_compatible("patent.inventive_analysis.v2", "1.1.0")

    def test_lower_minor_version_is_incompatible(self, registry: PromptSchemaRegistry):
        """当前次版本号更低时不兼容。"""
        schema = registry.get("patent.inventive_analysis.v2")
        assert schema is not None
        schema.template_version = "1.0.0"
        assert not registry.is_compatible("patent.inventive_analysis.v2", "1.1.0")

    def test_different_major_version_is_incompatible(self, registry: PromptSchemaRegistry):
        """主版本号不同完全不兼容。"""
        schema = registry.get("patent.inventive_analysis.v2")
        assert schema is not None
        schema.template_version = "2.0.0"
        assert not registry.is_compatible("patent.inventive_analysis.v2", "1.0.0")

    def test_missing_schema_returns_false(self, registry: PromptSchemaRegistry):
        """对不存在的 schema 检查兼容性应返回 False。"""
        assert not registry.is_compatible("missing.schema", "1.0.0")

    def test_schema_is_compatible_with_method(self):
        """PromptSchema.is_compatible_with 直接调用。"""
        schema = PromptSchema(rule_id="test", template_version="1.2.3")
        assert schema.is_compatible_with("1.0.0")
        assert schema.is_compatible_with("1.2.0")
        assert schema.is_compatible_with("1.2.3")
        assert not schema.is_compatible_with("2.0.0")
        assert not schema.is_compatible_with("1.3.0")


class TestVariableUpgrade:
    """变量升级迁移测试。"""

    @pytest.fixture
    def registry(self):
        return PromptSchemaRegistry()

    def test_upgrade_fills_defaults(self, registry: PromptSchemaRegistry):
        """upgrade_variables 应填充默认值。"""
        schema = PromptSchema(
            rule_id="test/upgrade",
            template_version="1.0.0",
            variables=[
                VariableSpec(name="required_var", required=True),
                VariableSpec(name="optional_var", required=False, default="default_value"),
            ],
        )
        registry.register(schema)
        result = registry.upgrade_variables("test/upgrade", {"required_var": "hello"})
        assert result["required_var"] == "hello"
        assert result["optional_var"] == "default_value"

    def test_upgrade_preserves_existing_values(self, registry: PromptSchemaRegistry):
        """已有值不应被默认值覆盖。"""
        schema = PromptSchema(
            rule_id="test/upgrade2",
            template_version="1.0.0",
            variables=[
                VariableSpec(name="var", required=False, default="default"),
            ],
        )
        registry.register(schema)
        result = registry.upgrade_variables("test/upgrade2", {"var": "custom"})
        assert result["var"] == "custom"

    def test_upgrade_missing_schema_returns_original(self, registry: PromptSchemaRegistry):
        """Schema 不存在时返回原始变量字典。"""
        original: Dict[str, Any] = {"a": 1}
        result = registry.upgrade_variables("missing", original)
        assert result == original


class TestProductionSchemaCompleteness:
    """高频使用（production）Schema 的完整性验证。"""

    @pytest.fixture
    def registry(self):
        return PromptSchemaRegistry()

    def test_patent_inventive_analysis_variables(self, registry: PromptSchemaRegistry):
        """patent.inventive_analysis.v2 应包含所有 Jinja2 变量。"""
        schema = registry.get("patent.inventive_analysis.v2")
        assert schema is not None
        required = schema.get_required_vars()
        assert "application_number" in required
        assert "technical_field" in required
        assert "claims" in required
        assert "office_action_summary" in required
        assert "prior_art_documents" in required

    def test_patent_office_action_variables(self, registry: PromptSchemaRegistry):
        """patent.office_action.analysis.v2 应包含所有 Jinja2 变量。"""
        schema = registry.get("patent.office_action.analysis.v2")
        assert schema is not None
        required = schema.get_required_vars()
        optional = schema.get_optional_vars()
        assert "application_number" in required
        assert "oa_content" in required
        assert "application_file" in required
        assert "oa_history" in optional  # 有 default 过滤器

    def test_business_xiaonuo_l4_v2_variables(self, registry: PromptSchemaRegistry):
        """business/xiaonuo_l4_business_v2 应包含 inventory 列出的变量。"""
        schema = registry.get("business/xiaonuo_l4_business_v2")
        assert schema is not None
        var_names = [v.name for v in schema.variables]
        assert "id" in var_names
        assert "role" in var_names
        assert "username" in var_names

    def test_production_schemas_pass_validation(self, registry: PromptSchemaRegistry):
        """Production Schema 配合完整变量应通过校验。"""
        validator = VariableValidator()

        # patent.inventive_analysis.v2
        inventive = registry.get("patent.inventive_analysis.v2")
        assert inventive is not None
        result = validator.validate(inventive, {
            "application_number": "CN20231001",
            "technical_field": "通信",
            "claims": "1. 一种方法...",
            "office_action_summary": "审查意见摘要",
            "prior_art_documents": ["D1", "D2"],
        })
        assert result.valid, f"Errors: {result.errors}"

        # patent.office_action.analysis.v2
        oa = registry.get("patent.office_action.analysis.v2")
        assert oa is not None
        result = validator.validate(oa, {
            "application_number": "CN20231001",
            "oa_content": "审查意见内容",
            "application_file": "申请文件",
            "oa_history": "",
        })
        assert result.valid, f"Errors: {result.errors}"

        # 不传入可选变量 oa_history 也应通过
        result = validator.validate(oa, {
            "application_number": "CN20231001",
            "oa_content": "审查意见内容",
            "application_file": "申请文件",
        })
        assert result.valid, f"Errors: {result.errors}"


class TestCoverageReport:
    """Schema 覆盖率报告测试。"""

    @pytest.fixture
    def registry(self):
        return PromptSchemaRegistry()

    def test_coverage_report_structure(self, registry: PromptSchemaRegistry):
        """覆盖率报告应包含必要字段。"""
        report = registry.get_coverage_report()
        assert "total_schemas" in report
        assert "schemas_with_variables" in report
        assert "schemas_without_variables" in report
        assert "coverage_rate" in report
        assert "domains" in report

    def test_coverage_report_values(self, registry: PromptSchemaRegistry):
        """覆盖率报告数值应正确。"""
        report = registry.get_coverage_report()
        total = report["total_schemas"]
        with_vars = report["schemas_with_variables"]
        without_vars = report["schemas_without_variables"]
        assert total == 69
        assert with_vars + without_vars == total
        assert 0.0 <= report["coverage_rate"] <= 1.0
        assert len(report["domains"]) == 6


class TestSchemaDomainModules:
    """各 domain schema 模块可独立导入测试。"""

    def test_import_root_schemas(self):
        from core.prompt_engine.schemas.root import (
            PATENT_INVENTIVE_ANALYSIS_V2_SCHEMA,
            PATENT_OFFICE_ACTION_ANALYSIS_V2_SCHEMA,
        )
        assert PATENT_INVENTIVE_ANALYSIS_V2_SCHEMA.rule_id == "patent.inventive_analysis.v2"
        assert PATENT_OFFICE_ACTION_ANALYSIS_V2_SCHEMA.rule_id == "patent.office_action.analysis.v2"

    def test_import_business_schemas(self):
        from core.prompt_engine.schemas.business import (
            BUSINESS_XIAONUO_L4_BUSINESS_V2_SCHEMA,
        )
        assert BUSINESS_XIAONUO_L4_BUSINESS_V2_SCHEMA.rule_id == "business/xiaonuo_l4_business_v2"

    def test_import_capability_schemas(self):
        from core.prompt_engine.schemas.capability import (
            CAPABILITY_XIAONUO_L3_CAPABILITY_V2_SCHEMA,
        )
        assert CAPABILITY_XIAONUO_L3_CAPABILITY_V2_SCHEMA.rule_id == "capability/xiaonuo_l3_capability_v2"

    def test_import_data_schemas(self):
        from core.prompt_engine.schemas.data import DATA_XIAONUO_L2_DATA_SCHEMA
        assert DATA_XIAONUO_L2_DATA_SCHEMA.rule_id == "data/xiaonuo_l2_data"

    def test_import_foundation_schemas(self):
        from core.prompt_engine.schemas.foundation import FOUNDATION_XIAONUO_DECISION_METHOD_V1_SCHEMA
        assert FOUNDATION_XIAONUO_DECISION_METHOD_V1_SCHEMA.rule_id == "foundation/xiaonuo_decision_method_v1"

    def test_import_skills_schemas(self):
        from core.prompt_engine.schemas.skills import SKILLS_SKILL_TEMPLATE_SCHEMA
        assert SKILLS_SKILL_TEMPLATE_SCHEMA.rule_id == "skills/SKILL_TEMPLATE"
