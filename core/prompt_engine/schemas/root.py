"""
Domain: root
Generated schemas for 8 prompt(s).
"""

from core.prompt_engine.schema import PromptSchema, VariableSpec, VariableType

# --- IMPLEMENTATION_SUMMARY (staging) ---
IMPLEMENTATION_SUMMARY_SCHEMA = PromptSchema(
    rule_id="IMPLEMENTATION_SUMMARY",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="L1基础层",
            source="system",
        ),
        VariableSpec(
            name="L2数据层",
            source="system",
        ),
        VariableSpec(
            name="L3能力层",
            source="system",
        ),
        VariableSpec(
            name="L4业务层",
            source="system",
        ),
    ],
)

# --- README (staging) ---
README_SCHEMA = PromptSchema(
    rule_id="README",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="Athena平台架构文档",
            source="system",
        ),
        VariableSpec(
            name="output",
            source="system",
        ),
        VariableSpec(
            name="reasoning_summary",
            source="system",
        ),
        VariableSpec(
            name="scratchpad",
            source="system",
        ),
    ],
)

# --- README_V4_ARCHITECTURE (staging) ---
README_V4_ARCHITECTURE_SCHEMA = PromptSchema(
    rule_id="README_V4_ARCHITECTURE",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="available_models",
            source="system",
        ),
        VariableSpec(
            name="cwd",
            source="system",
        ),
        VariableSpec(
            name="databases",
            source="system",
        ),
        VariableSpec(
            name="decision_tendency",
            source="system",
        ),
        VariableSpec(
            name="focus_area",
            source="system",
        ),
        VariableSpec(
            name="gateway_status",
            source="system",
        ),
        VariableSpec(
            name="important_reminders",
            source="system",
        ),
        VariableSpec(
            name="knowledge_graphs",
            source="system",
        ),
        VariableSpec(
            name="mcp_servers_list",
            type=VariableType.LIST,
            source="system",
        ),
        VariableSpec(
            name="mcp_tools_list",
            type=VariableType.LIST,
            source="system",
        ),
        VariableSpec(
            name="mcp_usage_guide",
            source="system",
        ),
        VariableSpec(
            name="project_context",
            source="document",
        ),
        VariableSpec(
            name="recent_work",
            source="system",
        ),
        VariableSpec(
            name="service_health",
            source="system",
        ),
        VariableSpec(
            name="session_id",
            source="system",
        ),
        VariableSpec(
            name="start_time",
            source="system",
        ),
        VariableSpec(
            name="style_preference",
            source="system",
        ),
        VariableSpec(
            name="user_info",
            source="user_input",
        ),
        VariableSpec(
            name="vector_collections",
            source="system",
        ),
    ],
)

# --- xiaonuo_complete_capability_list (staging) ---
XIAONUO_COMPLETE_CAPABILITY_LIST_SCHEMA = PromptSchema(
    rule_id="xiaonuo_complete_capability_list",
    template_version="0.9.0",
    variables=[
    ],
)

# --- xiaonuo_quick_reference (staging) ---
XIAONUO_QUICK_REFERENCE_SCHEMA = PromptSchema(
    rule_id="xiaonuo_quick_reference",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="agent_name",
            source="system",
        ),
    ],
)

# --- hitl_safety_block (production) ---
HITL_SAFETY_BLOCK_SCHEMA = PromptSchema(
    rule_id="hitl_safety_block",
    template_version="1.0.0",
    variables=[
        VariableSpec(
            name="核心内容概要",
            source="system",
        ),
        VariableSpec(
            name="确认点列表",
            source="system",
        ),
        VariableSpec(
            name="详细内容",
            source="system",
        ),
        VariableSpec(
            name="输出类型标题",
            source="system",
        ),
        VariableSpec(
            name="选项1",
            source="system",
        ),
    ],
)

# --- patent.inventive_analysis.v2 (production) ---
PATENT_INVENTIVE_ANALYSIS_V2_SCHEMA = PromptSchema(
    rule_id="patent.inventive_analysis.v2",
    template_version="1.0.0",
    variables=[
        VariableSpec(
            name="application_number",
            source="system",
        ),
        VariableSpec(
            name="claims",
            source="system",
        ),
        VariableSpec(
            name="office_action_summary",
            source="system",
        ),
        VariableSpec(
            name="prior_art_documents",
            type=VariableType.LIST,
            source="document",
        ),
        VariableSpec(
            name="technical_field",
            source="system",
        ),
    ],
)

# --- patent.office_action.analysis.v2 (production) ---
PATENT_OFFICE_ACTION_ANALYSIS_V2_SCHEMA = PromptSchema(
    rule_id="patent.office_action.analysis.v2",
    template_version="1.0.0",
    variables=[
        VariableSpec(
            name="application_file",
            source="document",
        ),
        VariableSpec(
            name="application_number",
            source="system",
        ),
        VariableSpec(
            name="oa_content",
            source="document",
        ),
        VariableSpec(
            name="oa_history",
            required=False,
            source="system",
        ),
    ],
)
