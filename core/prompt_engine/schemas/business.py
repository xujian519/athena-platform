"""
Domain: business
Generated schemas for 16 prompt(s).
"""

from core.prompt_engine.schema import PromptSchema, VariableSpec, VariableType

# --- business/task05_inventive (staging) ---
BUSINESS_TASK05_INVENTIVE_SCHEMA = PromptSchema(
    rule_id="business/task05_inventive",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="依据",
            source="system",
        ),
        VariableSpec(
            name="具体信息",
            source="system",
        ),
        VariableSpec(
            name="具体风险",
            source="system",
        ),
        VariableSpec(
            name="具备_不具备",
            type=VariableType.BOOL,
            source="system",
        ),
    ],
)

# --- business/task07_invalid_strategy (staging) ---
BUSINESS_TASK07_INVALID_STRATEGY_SCHEMA = PromptSchema(
    rule_id="business/task07_invalid_strategy",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="全部_部分",
            source="system",
        ),
        VariableSpec(
            name="具备_不具备",
            type=VariableType.BOOL,
            source="system",
        ),
        VariableSpec(
            name="方案描述",
            source="system",
        ),
    ],
)

# --- business/task_1_1_understand_disclosure (staging) ---
BUSINESS_TASK_1_1_UNDERSTAND_DISCLOSURE_SCHEMA = PromptSchema(
    rule_id="business/task_1_1_understand_disclosure",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="H04B_1_00",
            source="system",
        ),
        VariableSpec(
            name="一句话概括",
            source="system",
        ),
        VariableSpec(
            name="无线通信中的信号处理",
            source="system",
        ),
        VariableSpec(
            name="电子通信",
            source="system",
        ),
    ],
)

# --- business/task_1_2_prior_art_search (staging) ---
BUSINESS_TASK_1_2_PRIOR_ART_SEARCH_SCHEMA = PromptSchema(
    rule_id="business/task_1_2_prior_art_search",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="与本申请的关联",
            source="system",
        ),
        VariableSpec(
            name="主分类",
            source="system",
        ),
        VariableSpec(
            name="主分类号",
            source="system",
        ),
        VariableSpec(
            name="从技术交底书提取",
            source="extracted",
        ),
    ],
)

# --- business/task_1_3_write_specification (staging) ---
BUSINESS_TASK_1_3_WRITE_SPECIFICATION_SCHEMA = PromptSchema(
    rule_id="business/task_1_3_write_specification",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="具体描述",
            source="system",
        ),
        VariableSpec(
            name="名称1",
            source="system",
        ),
        VariableSpec(
            name="名称2",
            source="system",
        ),
        VariableSpec(
            name="名称3",
            source="system",
        ),
    ],
)

# --- business/task_1_4_write_claims (staging) ---
BUSINESS_TASK_1_4_WRITE_CLAIMS_SCHEMA = PromptSchema(
    rule_id="business/task_1_4_write_claims",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="A_B",
            source="system",
        ),
        VariableSpec(
            name="X_Y",
            source="system",
        ),
        VariableSpec(
            name="产品_方法_装置_系统",
            source="system",
        ),
        VariableSpec(
            name="具体功能",
            source="system",
        ),
    ],
)

# --- business/task_1_5_write_abstract (staging) ---
BUSINESS_TASK_1_5_WRITE_ABSTRACT_SCHEMA = PromptSchema(
    rule_id="business/task_1_5_write_abstract",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="主要优点",
            source="system",
        ),
        VariableSpec(
            name="主要组成部分",
            source="system",
        ),
        VariableSpec(
            name="内容",
            source="system",
        ),
        VariableSpec(
            name="列表",
            source="system",
        ),
    ],
)

# --- business/task_2_1_analyze_office_action (staging) ---
BUSINESS_TASK_2_1_ANALYZE_OFFICE_ACTION_SCHEMA = PromptSchema(
    rule_id="business/task_2_1_analyze_office_action",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="X",
            source="system",
        ),
        VariableSpec(
            name="具体法条",
            source="system",
        ),
        VariableSpec(
            name="初步建议",
            source="system",
        ),
        VariableSpec(
            name="引用文件列表",
            source="system",
        ),
    ],
)

# --- business/task_2_1_oa_analysis_v2_with_parallel (staging) ---
BUSINESS_TASK_2_1_OA_ANALYSIS_V2_WITH_PARALLEL_SCHEMA = PromptSchema(
    rule_id="business/task_2_1_oa_analysis_v2_with_parallel",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="legal_basis",
            source="system",
        ),
        VariableSpec(
            name="oa_content",
            source="document",
        ),
        VariableSpec(
            name="pub_number",
            type=VariableType.INT,
            source="system",
        ),
        VariableSpec(
            name="rejections",
            source="system",
        ),
    ],
)

# --- business/task_2_2_analyze_rejection (staging) ---
BUSINESS_TASK_2_2_ANALYZE_REJECTION_SCHEMA = PromptSchema(
    rule_id="business/task_2_2_analyze_rejection",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="列举",
            source="system",
        ),
        VariableSpec(
            name="化学_医药_机械_电子",
            source="system",
        ),
        VariableSpec(
            name="审查员认为本申请相对于D1不具备新颖性的理由",
            type=VariableType.BOOL,
            source="system",
        ),
        VariableSpec(
            name="审查员认为说明书哪些部分公开不充分",
            source="document",
        ),
    ],
)

# --- business/task_2_3_develop_response_strategy (staging) ---
BUSINESS_TASK_2_3_DEVELOP_RESPONSE_STRATEGY_SCHEMA = PromptSchema(
    rule_id="business/task_2_3_develop_response_strategy",
    template_version="0.9.0",
    variables=[
    ],
)

# --- business/task_2_4_write_response (staging) ---
BUSINESS_TASK_2_4_WRITE_RESPONSE_SCHEMA = PromptSchema(
    rule_id="business/task_2_4_write_response",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="M",
            source="system",
        ),
        VariableSpec(
            name="N",
            source="system",
        ),
        VariableSpec(
            name="X",
            source="system",
        ),
        VariableSpec(
            name="Y",
            source="system",
        ),
    ],
)

# --- business/xiaona_l4_business_v2_optimized (staging) ---
BUSINESS_XIAONA_L4_BUSINESS_V2_OPTIMIZED_SCHEMA = PromptSchema(
    rule_id="business/xiaona_l4_business_v2_optimized",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="D2是否启示",
            type=VariableType.BOOL,
            source="system",
        ),
        VariableSpec(
            name="主题",
            source="system",
        ),
        VariableSpec(
            name="依据",
            source="system",
        ),
        VariableSpec(
            name="修改内容",
            source="system",
        ),
    ],
)

# --- business/xiaonuo_l4_business (staging) ---
BUSINESS_XIAONUO_L4_BUSINESS_SCHEMA = PromptSchema(
    rule_id="business/xiaonuo_l4_business",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="DOMAIN",
            source="system",
        ),
        VariableSpec(
            name="p_1_4",
            source="system",
        ),
        VariableSpec(
            name="具体内容_",
            source="system",
        ),
        VariableSpec(
            name="具体能力",
            source="system",
        ),
        VariableSpec(
            name="内容标题",
            source="system",
        ),
    ],
)

# --- business/xiaonuo_l4_business_v2 (production) ---
BUSINESS_XIAONUO_L4_BUSINESS_V2_SCHEMA = PromptSchema(
    rule_id="business/xiaonuo_l4_business_v2",
    template_version="1.0.0",
    variables=[
        VariableSpec(
            name="ETERNAL_LONG_TERM_SHORT_TERM_WORKING",
            source="system",
        ),
        VariableSpec(
            name="id",
            source="system",
        ),
        VariableSpec(
            name="p_1_10",
            source="system",
        ),
        VariableSpec(
            name="role",
            source="system",
        ),
        VariableSpec(
            name="username",
            source="user_input",
        ),
    ],
)

# --- business/xiaonuo_l4_business_v2_optimized (staging) ---
BUSINESS_XIAONUO_L4_BUSINESS_V2_OPTIMIZED_SCHEMA = PromptSchema(
    rule_id="business/xiaonuo_l4_business_v2_optimized",
    template_version="0.9.0",
    variables=[
    ],
)
