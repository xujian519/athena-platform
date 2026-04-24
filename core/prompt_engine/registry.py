"""
PromptSchemaRegistry - 提示词 Schema 注册表与版本管理
"""

from typing import Any, Optional

from core.prompt_engine.schema import PromptSchema

# Import all domain schemas
from core.prompt_engine.schemas.business import *  # noqa: F401,F403
from core.prompt_engine.schemas.capability import *  # noqa: F401,F403
from core.prompt_engine.schemas.data import *  # noqa: F401,F403
from core.prompt_engine.schemas.foundation import *  # noqa: F401,F403
from core.prompt_engine.schemas.root import *  # noqa: F401,F403
from core.prompt_engine.schemas.skills import *  # noqa: F401,F403


class VersionCompatibilityError(Exception):
    """版本不兼容异常。"""
    pass


class PromptSchemaRegistry:
    """提示词 Schema 注册表。

    支持功能:
    - 通过 schema_id 检索 Schema
    - 按 domain / status 过滤
    - 版本兼容性检查（向后兼容原则）
    - 变量升级迁移
    """

    def __init__(self) -> None:
        self._schemas: dict[str, PromptSchema] = {}
        self._domain_index: dict[str, list[str]] = {}
        self._register_builtin_schemas()

    def _register_builtin_schemas(self) -> None:
        """自动注册所有内置 Schema（从各 domain 模块导入）。"""
        self.register(IMPLEMENTATION_SUMMARY_SCHEMA)
        self.register(README_SCHEMA)
        self.register(README_V4_ARCHITECTURE_SCHEMA)
        self.register(XIAONUO_COMPLETE_CAPABILITY_LIST_SCHEMA)
        self.register(XIAONUO_QUICK_REFERENCE_SCHEMA)
        self.register(HITL_SAFETY_BLOCK_SCHEMA)
        self.register(PATENT_INVENTIVE_ANALYSIS_V2_SCHEMA)
        self.register(PATENT_OFFICE_ACTION_ANALYSIS_V2_SCHEMA)
        self.register(BUSINESS_TASK05_INVENTIVE_SCHEMA)
        self.register(BUSINESS_TASK07_INVALID_STRATEGY_SCHEMA)
        self.register(BUSINESS_TASK_1_1_UNDERSTAND_DISCLOSURE_SCHEMA)
        self.register(BUSINESS_TASK_1_2_PRIOR_ART_SEARCH_SCHEMA)
        self.register(BUSINESS_TASK_1_3_WRITE_SPECIFICATION_SCHEMA)
        self.register(BUSINESS_TASK_1_4_WRITE_CLAIMS_SCHEMA)
        self.register(BUSINESS_TASK_1_5_WRITE_ABSTRACT_SCHEMA)
        self.register(BUSINESS_TASK_2_1_ANALYZE_OFFICE_ACTION_SCHEMA)
        self.register(BUSINESS_TASK_2_1_OA_ANALYSIS_V2_WITH_PARALLEL_SCHEMA)
        self.register(BUSINESS_TASK_2_2_ANALYZE_REJECTION_SCHEMA)
        self.register(BUSINESS_TASK_2_3_DEVELOP_RESPONSE_STRATEGY_SCHEMA)
        self.register(BUSINESS_TASK_2_4_WRITE_RESPONSE_SCHEMA)
        self.register(BUSINESS_XIAONA_L4_BUSINESS_V2_OPTIMIZED_SCHEMA)
        self.register(BUSINESS_XIAONUO_L4_BUSINESS_SCHEMA)
        self.register(BUSINESS_XIAONUO_L4_BUSINESS_V2_SCHEMA)
        self.register(BUSINESS_XIAONUO_L4_BUSINESS_V2_OPTIMIZED_SCHEMA)
        self.register(CAPABILITY_CAP01_RETRIEVAL_SCHEMA)
        self.register(CAPABILITY_CAP02_ANALYSIS_SCHEMA)
        self.register(CAPABILITY_CAP02_TECHNICAL_DEEP_ANALYSIS_V2_ENHANCED_SCHEMA)
        self.register(CAPABILITY_CAP03_WRITING_SCHEMA)
        self.register(CAPABILITY_CAP04_DISCLOSURE_EXAM_SCHEMA)
        self.register(CAPABILITY_CAP04_INVENTIVE_SCHEMA)
        self.register(CAPABILITY_CAP04_INVENTIVE_V2_WITH_WHENTOUSE_SCHEMA)
        self.register(CAPABILITY_CAP04_INVENTIVE_V3_LLM_INTEGRATION_SCHEMA)
        self.register(CAPABILITY_CAP05_CLARITY_EXAM_SCHEMA)
        self.register(CAPABILITY_CAP05_INVALID_SCHEMA)
        self.register(CAPABILITY_CAP06_PRIOR_ART_IDENT_SCHEMA)
        self.register(CAPABILITY_CAP06_RESPONSE_SCHEMA)
        self.register(CAPABILITY_CAP07_FORMAL_EXAM_SCHEMA)
        self.register(CAPABILITY_XIAONA_L3_CAPABILITY_V2_OPTIMIZED_SCHEMA)
        self.register(CAPABILITY_XIAONUO_L3_CAPABILITY_SCHEMA)
        self.register(CAPABILITY_XIAONUO_L3_CAPABILITY_V2_SCHEMA)
        self.register(CAPABILITY_XIAONUO_L3_CAPABILITY_V2_OPTIMIZED_SCHEMA)
        self.register(DATA_XIAONA_L2_DATABASE_SCHEMA)
        self.register(DATA_XIAONA_L2_GRAPH_SCHEMA)
        self.register(DATA_XIAONA_L2_OVERVIEW_SCHEMA)
        self.register(DATA_XIAONA_L2_OVERVIEW_V2_OPTIMIZED_SCHEMA)
        self.register(DATA_XIAONA_L2_SEARCH_SCHEMA)
        self.register(DATA_XIAONA_L2_SEARCH_V2_OPTIMIZED_SCHEMA)
        self.register(DATA_XIAONA_L2_VECTORS_SCHEMA)
        self.register(DATA_XIAONUO_L2_DATA_SCHEMA)
        self.register(FOUNDATION_HITL_PROTOCOL_SCHEMA)
        self.register(FOUNDATION_HITL_PROTOCOL_V2_OPTIMIZED_SCHEMA)
        self.register(FOUNDATION_HITL_PROTOCOL_V3_MANDATORY_SCHEMA)
        self.register(FOUNDATION_HITL_PROTOCOL_V4_CONSTRAINT_REPEAT_SCHEMA)
        self.register(FOUNDATION_XIAONA_CORE_V3_COMPRESSED_SCHEMA)
        self.register(FOUNDATION_XIAONA_L1_FOUNDATION_SCHEMA)
        self.register(FOUNDATION_XIAONA_L1_FOUNDATION_V2_OPTIMIZED_SCHEMA)
        self.register(FOUNDATION_XIAONUO_CORE_V3_COMPRESSED_SCHEMA)
        self.register(FOUNDATION_XIAONUO_DECISION_METHOD_V1_SCHEMA)
        self.register(FOUNDATION_XIAONUO_L1_FOUNDATION_SCHEMA)
        self.register(FOUNDATION_XIAONUO_L1_FOUNDATION_V2_OPTIMIZED_SCHEMA)
        self.register(FOUNDATION_XIAONUO_L5_HITL_SCHEMA)
        self.register(SKILLS_SKILL_TEMPLATE_SCHEMA)
        self.register(SKILLS_LEGAL_WORLD_MODEL_INSTALL_SCHEMA)
        self.register(SKILLS_LEGAL_WORLD_MODEL_README_SCHEMA)
        self.register(SKILLS_LEGAL_WORLD_MODEL_SKILL_SCHEMA)
        self.register(SKILLS_PATENT_RETRIEVAL_README_SCHEMA)
        self.register(SKILLS_PATENT_RETRIEVAL_SKILL_SCHEMA)
        self.register(SKILLS_PATENT_RETRIEVAL_REFERENCES_DATABASE_SCHEMA_SCHEMA)
        self.register(SKILLS_PUBLIC_HELLO_WORLD_SKILL_SCHEMA)

    def register(self, schema: PromptSchema) -> None:
        """注册一个 Schema。"""
        self._schemas[schema.rule_id] = schema
        domain = schema.rule_id.split('/')[0] if '/' in schema.rule_id else 'root'
        self._domain_index.setdefault(domain, []).append(schema.rule_id)

    def get(self, schema_id: str) -> Optional[PromptSchema]:
        """通过 schema_id 获取 Schema。"""
        return self._schemas.get(schema_id)

    def list_all(self) -> list[str]:
        """返回所有已注册的 schema_id 列表。"""
        return list(self._schemas.keys())

    def list_by_domain(self, domain: str) -> list[str]:
        """返回指定 domain 下的所有 schema_id。"""
        return self._domain_index.get(domain, [])

    def get_by_status(self, status: str) -> list[PromptSchema]:
        """按状态过滤 Schema（基于 template_version 前缀推断）。

        状态与版本映射:
        - production  -> 1.0.x
        - staging     -> 0.9.x
        - draft       -> 0.1.x
        - deprecated  -> 0.0.x
        """
        result: list[PromptSchema] = []
        version_map = {"production": "1.0", "staging": "0.9", "draft": "0.1", "deprecated": "0.0"}
        prefix = version_map.get(status, '')
        for schema in self._schemas.values():
            if schema.template_version.startswith(prefix):
                result.append(schema)
        return result

    def is_compatible(
        self,
        schema_id: str,
        target_version: str,
    ) -> bool:
        """检查目标版本是否与当前注册版本向后兼容。

        向后兼容原则（语义化版本）:
        - 主版本号（MAJOR）必须相同
        - 当前次版本号（MINOR） >= 目标次版本号
        - 修订号（PATCH）不参与兼容性判断
        """
        schema = self.get(schema_id)
        if schema is None:
            return False
        return schema.is_compatible_with(target_version)

    def upgrade_variables(
        self,
        schema_id: str,
        variables: dict[str, Any],
    ) -> dict[str, Any]:
        """根据 Schema 定义升级/规范化变量字典。

        - 填充默认值（对可选变量）
        - 保留已传入的值
        """
        schema = self.get(schema_id)
        if schema is None:
            return variables
        return schema.upgrade_variables(variables)

    def get_coverage_report(self) -> dict[str, Any]:
        """生成 Schema 覆盖率报告。"""
        total = len(self._schemas)
        with_vars = sum(1 for s in self._schemas.values() if s.variables)
        without_vars = total - with_vars
        domains = {d: len(ids) for d, ids in self._domain_index.items()}
        return {
            "total_schemas": total,
            "schemas_with_variables": with_vars,
            "schemas_without_variables": without_vars,
            "coverage_rate": round(with_vars / total, 4) if total else 0.0,
            "domains": domains,
        }
