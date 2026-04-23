"""
Domain: data
Generated schemas for 8 prompt(s).
"""

from core.prompt_engine.schema import PromptSchema, VariableSpec, VariableType

# --- data/xiaona_l2_database (staging) ---
DATA_XIAONA_L2_DATABASE_SCHEMA = PromptSchema(
    rule_id="data/xiaona_l2_database",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="摘要关键部分",
            source="system",
        ),
        VariableSpec(
            name="文献种类代码",
            source="system",
        ),
        VariableSpec(
            name="标题",
            source="system",
        ),
    ],
)

# --- data/xiaona_l2_graph (staging) ---
DATA_XIAONA_L2_GRAPH_SCHEMA = PromptSchema(
    rule_id="data/xiaona_l2_graph",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="APPLIES",
            source="system",
        ),
        VariableSpec(
            name="BELONGS_TO",
            source="system",
        ),
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

# --- data/xiaona_l2_overview (staging) ---
DATA_XIAONA_L2_OVERVIEW_SCHEMA = PromptSchema(
    rule_id="data/xiaona_l2_overview",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="academic",
            source="system",
        ),
        VariableSpec(
            name="id",
            source="system",
        ),
        VariableSpec(
            name="manuals",
            source="system",
        ),
        VariableSpec(
            name="profile",
            source="document",
        ),
        VariableSpec(
            name="publication_number",
            type=VariableType.INT,
            source="system",
        ),
        VariableSpec(
            name="standards",
            source="system",
        ),
    ],
)

# --- data/xiaona_l2_overview_v2_optimized (staging) ---
DATA_XIAONA_L2_OVERVIEW_V2_OPTIMIZED_SCHEMA = PromptSchema(
    rule_id="data/xiaona_l2_overview_v2_optimized",
    template_version="0.9.0",
    variables=[
    ],
)

# --- data/xiaona_l2_search (staging) ---
DATA_XIAONA_L2_SEARCH_SCHEMA = PromptSchema(
    rule_id="data/xiaona_l2_search",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="citation",
            source="system",
        ),
        VariableSpec(
            name="技术特征",
            source="system",
        ),
        VariableSpec(
            name="技术问题",
            source="user_input",
        ),
        VariableSpec(
            name="技术领域",
            source="system",
        ),
        VariableSpec(
            name="核心术语",
            source="system",
        ),
    ],
)

# --- data/xiaona_l2_search_v2_optimized (staging) ---
DATA_XIAONA_L2_SEARCH_V2_OPTIMIZED_SCHEMA = PromptSchema(
    rule_id="data/xiaona_l2_search_v2_optimized",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="主要应用",
            source="system",
        ),
        VariableSpec(
            name="关联",
            source="system",
        ),
        VariableSpec(
            name="分类",
            source="system",
        ),
        VariableSpec(
            name="原理",
            source="system",
        ),
        VariableSpec(
            name="参数",
            source="system",
        ),
    ],
)

# --- data/xiaona_l2_vectors (staging) ---
DATA_XIAONA_L2_VECTORS_SCHEMA = PromptSchema(
    rule_id="data/xiaona_l2_vectors",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="三步法详解",
            source="system",
        ),
        VariableSpec(
            name="具体争议点",
            source="system",
        ),
        VariableSpec(
            name="具体标准",
            source="system",
        ),
        VariableSpec(
            name="内容",
            source="system",
        ),
    ],
)

# --- data/xiaonuo_l2_data (staging) ---
DATA_XIAONUO_L2_DATA_SCHEMA = PromptSchema(
    rule_id="data/xiaonuo_l2_data",
    template_version="0.9.0",
    variables=[
    ],
)
