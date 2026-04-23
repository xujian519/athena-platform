"""
Domain: capability
Generated schemas for 17 prompt(s).
"""

from core.prompt_engine.schema import PromptSchema, VariableSpec, VariableType

# --- capability/cap01_retrieval (staging) ---
CAPABILITY_CAP01_RETRIEVAL_SCHEMA = PromptSchema(
    rule_id="capability/cap01_retrieval",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="CITES",
            source="system",
        ),
        VariableSpec(
            name="SUPERIOR_LAW",
            source="system",
        ),
        VariableSpec(
            name="SUPPORTS",
            source="system",
        ),
    ],
)

# --- capability/cap02_analysis (staging) ---
CAPABILITY_CAP02_ANALYSIS_SCHEMA = PromptSchema(
    rule_id="capability/cap02_analysis",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="争议焦点",
            source="system",
        ),
        VariableSpec(
            name="技术领域",
            source="system",
        ),
        VariableSpec(
            name="支持",
            source="system",
        ),
        VariableSpec(
            name="核心法条",
            source="system",
        ),
        VariableSpec(
            name="驳回",
            source="system",
        ),
    ],
)

# --- capability/cap02_technical_deep_analysis_v2_enhanced (staging) ---
CAPABILITY_CAP02_TECHNICAL_DEEP_ANALYSIS_V2_ENHANCED_SCHEMA = PromptSchema(
    rule_id="capability/cap02_technical_deep_analysis_v2_enhanced",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="D1明确公开的内容",
            source="system",
        ),
        VariableSpec(
            name="D1未提及的关键内容",
            source="system",
        ),
        VariableSpec(
            name="D1的手段A",
            source="system",
        ),
        VariableSpec(
            name="D1的手段B",
            source="system",
        ),
    ],
)

# --- capability/cap03_writing (staging) ---
CAPABILITY_CAP03_WRITING_SCHEMA = PromptSchema(
    rule_id="capability/cap03_writing",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="与本请求相似的观点",
            source="system",
        ),
        VariableSpec(
            name="修改后的文本",
            source="system",
        ),
        VariableSpec(
            name="文书类型",
            source="system",
        ),
        VariableSpec(
            name="核心论点",
            source="system",
        ),
    ],
)

# --- capability/cap04_disclosure_exam (staging) ---
CAPABILITY_CAP04_DISCLOSURE_EXAM_SCHEMA = PromptSchema(
    rule_id="capability/cap04_disclosure_exam",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="X",
            source="system",
        ),
        VariableSpec(
            name="Y",
            source="system",
        ),
        VariableSpec(
            name="充分_基本充分_不充分",
            source="system",
        ),
        VariableSpec(
            name="具体建议",
            source="system",
        ),
    ],
)

# --- capability/cap04_inventive (staging) ---
CAPABILITY_CAP04_INVENTIVE_SCHEMA = PromptSchema(
    rule_id="capability/cap04_inventive",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="abstract",
            source="system",
        ),
        VariableSpec(
            name="application_date",
            source="system",
        ),
        VariableSpec(
            name="claims",
            source="system",
        ),
        VariableSpec(
            name="description",
            source="system",
        ),
    ],
)

# --- capability/cap04_inventive_v2_with_whenToUse (staging) ---
CAPABILITY_CAP04_INVENTIVE_V2_WITH_WHENTOUSE_SCHEMA = PromptSchema(
    rule_id="capability/cap04_inventive_v2_with_whenToUse",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="abstract",
            source="system",
        ),
        VariableSpec(
            name="application_date",
            source="system",
        ),
        VariableSpec(
            name="claims",
            source="system",
        ),
        VariableSpec(
            name="description",
            source="system",
        ),
    ],
)

# --- capability/cap04_inventive_v3_llm_integration (staging) ---
CAPABILITY_CAP04_INVENTIVE_V3_LLM_INTEGRATION_SCHEMA = PromptSchema(
    rule_id="capability/cap04_inventive_v3_llm_integration",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="differences",
            source="system",
        ),
        VariableSpec(
            name="patent_data",
            source="system",
        ),
        VariableSpec(
            name="prior_art",
            source="system",
        ),
        VariableSpec(
            name="technical_field",
            source="system",
        ),
    ],
)

# --- capability/cap05_clarity_exam (staging) ---
CAPABILITY_CAP05_CLARITY_EXAM_SCHEMA = PromptSchema(
    rule_id="capability/cap05_clarity_exam",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="X",
            source="system",
        ),
        VariableSpec(
            name="修改后的权利要求书",
            source="document",
        ),
        VariableSpec(
            name="具体建议",
            source="system",
        ),
        VariableSpec(
            name="展示修改后的完整权利要求书",
            source="document",
        ),
    ],
)

# --- capability/cap05_invalid (staging) ---
CAPABILITY_CAP05_INVALID_SCHEMA = PromptSchema(
    rule_id="capability/cap05_invalid",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="abstract",
            source="system",
        ),
        VariableSpec(
            name="application_date",
            source="system",
        ),
        VariableSpec(
            name="case_support",
            source="system",
        ),
        VariableSpec(
            name="claim_stability",
            source="system",
        ),
        VariableSpec(
            name="claims",
            source="system",
        ),
    ],
)

# --- capability/cap06_prior_art_ident (staging) ---
CAPABILITY_CAP06_PRIOR_ART_IDENT_SCHEMA = PromptSchema(
    rule_id="capability/cap06_prior_art_ident",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="技术名称_方案描述",
            source="system",
        ),
    ],
)

# --- capability/cap06_response (staging) ---
CAPABILITY_CAP06_RESPONSE_SCHEMA = PromptSchema(
    rule_id="capability/cap06_response",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="legal_basis",
            source="system",
        ),
        VariableSpec(
            name="rejection_reasons",
            source="system",
        ),
        VariableSpec(
            name="suggestion_modification",
            source="system",
        ),
        VariableSpec(
            name="target_claim",
            source="system",
        ),
    ],
)

# --- capability/cap07_formal_exam (staging) ---
CAPABILITY_CAP07_FORMAL_EXAM_SCHEMA = PromptSchema(
    rule_id="capability/cap07_formal_exam",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="art26_3",
            source="system",
        ),
        VariableSpec(
            name="art26_4",
            source="system",
        ),
        VariableSpec(
            name="art26_5",
            source="system",
        ),
        VariableSpec(
            name="cases",
            source="system",
        ),
    ],
)

# --- capability/xiaona_l3_capability_v2_optimized (staging) ---
CAPABILITY_XIAONA_L3_CAPABILITY_V2_OPTIMIZED_SCHEMA = PromptSchema(
    rule_id="capability/xiaona_l3_capability_v2_optimized",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="D1",
            source="system",
        ),
        VariableSpec(
            name="D2是否给出启示",
            type=VariableType.BOOL,
            source="system",
        ),
        VariableSpec(
            name="专利_论文_公开",
            source="system",
        ),
        VariableSpec(
            name="公开内容",
            source="system",
        ),
    ],
)

# --- capability/xiaonuo_l3_capability (staging) ---
CAPABILITY_XIAONUO_L3_CAPABILITY_SCHEMA = PromptSchema(
    rule_id="capability/xiaonuo_l3_capability",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="小娜开始执行专利撰写任务",
            source="system",
        ),
    ],
)

# --- capability/xiaonuo_l3_capability_v2 (production) ---
CAPABILITY_XIAONUO_L3_CAPABILITY_V2_SCHEMA = PromptSchema(
    rule_id="capability/xiaonuo_l3_capability_v2",
    template_version="1.0.0",
    variables=[
    ],
)

# --- capability/xiaonuo_l3_capability_v2_optimized (staging) ---
CAPABILITY_XIAONUO_L3_CAPABILITY_V2_OPTIMIZED_SCHEMA = PromptSchema(
    rule_id="capability/xiaonuo_l3_capability_v2_optimized",
    template_version="0.9.0",
    variables=[
    ],
)
