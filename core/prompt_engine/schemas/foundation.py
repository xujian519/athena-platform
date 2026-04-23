"""
Domain: foundation
Generated schemas for 12 prompt(s).
"""

from core.prompt_engine.schema import PromptSchema, VariableSpec, VariableType

# --- foundation/hitl_protocol (staging) ---
FOUNDATION_HITL_PROTOCOL_SCHEMA = PromptSchema(
    rule_id="foundation/hitl_protocol",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="X_Y",
            source="system",
        ),
        VariableSpec(
            name="下一步操作",
            source="system",
        ),
        VariableSpec(
            name="不确定性说明",
            source="system",
        ),
        VariableSpec(
            name="任务名称",
            source="system",
        ),
        VariableSpec(
            name="关键发现1",
            source="system",
        ),
    ],
)

# --- foundation/hitl_protocol_v2_optimized (staging) ---
FOUNDATION_HITL_PROTOCOL_V2_OPTIMIZED_SCHEMA = PromptSchema(
    rule_id="foundation/hitl_protocol_v2_optimized",
    template_version="0.9.0",
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

# --- foundation/hitl_protocol_v3_mandatory (staging) ---
FOUNDATION_HITL_PROTOCOL_V3_MANDATORY_SCHEMA = PromptSchema(
    rule_id="foundation/hitl_protocol_v3_mandatory",
    template_version="0.9.0",
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

# --- foundation/hitl_protocol_v4_constraint_repeat (staging) ---
FOUNDATION_HITL_PROTOCOL_V4_CONSTRAINT_REPEAT_SCHEMA = PromptSchema(
    rule_id="foundation/hitl_protocol_v4_constraint_repeat",
    template_version="0.9.0",
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

# --- foundation/xiaona_core_v3_compressed (staging) ---
FOUNDATION_XIAONA_CORE_V3_COMPRESSED_SCHEMA = PromptSchema(
    rule_id="foundation/xiaona_core_v3_compressed",
    template_version="0.9.0",
    variables=[
    ],
)

# --- foundation/xiaona_l1_foundation (staging) ---
FOUNDATION_XIAONA_L1_FOUNDATION_SCHEMA = PromptSchema(
    rule_id="foundation/xiaona_l1_foundation",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="下一步操作",
            source="system",
        ),
        VariableSpec(
            name="不确定性说明",
            source="system",
        ),
        VariableSpec(
            name="为什么重要",
            source="system",
        ),
        VariableSpec(
            name="从严_从宽",
            source="system",
        ),
    ],
)

# --- foundation/xiaona_l1_foundation_v2_optimized (staging) ---
FOUNDATION_XIAONA_L1_FOUNDATION_V2_OPTIMIZED_SCHEMA = PromptSchema(
    rule_id="foundation/xiaona_l1_foundation_v2_optimized",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="中间反馈",
            source="system",
        ),
        VariableSpec(
            name="为什么重要",
            source="system",
        ),
        VariableSpec(
            name="从严_从宽",
            source="system",
        ),
        VariableSpec(
            name="任务名称",
            source="system",
        ),
    ],
)

# --- foundation/xiaonuo_core_v3_compressed (staging) ---
FOUNDATION_XIAONUO_CORE_V3_COMPRESSED_SCHEMA = PromptSchema(
    rule_id="foundation/xiaonuo_core_v3_compressed",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="一句话描述",
            source="system",
        ),
        VariableSpec(
            name="名称",
            source="system",
        ),
        VariableSpec(
            name="进行中_已完成_等待确认",
            source="system",
        ),
    ],
)

# --- foundation/xiaonuo_decision_method_v1 (production) ---
FOUNDATION_XIAONUO_DECISION_METHOD_V1_SCHEMA = PromptSchema(
    rule_id="foundation/xiaonuo_decision_method_v1",
    template_version="1.0.0",
    variables=[
    ],
)

# --- foundation/xiaonuo_l1_foundation (staging) ---
FOUNDATION_XIAONUO_L1_FOUNDATION_SCHEMA = PromptSchema(
    rule_id="foundation/xiaonuo_l1_foundation",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="工具名称",
            source="system",
        ),
        VariableSpec(
            name="执行过程",
            source="system",
        ),
        VariableSpec(
            name="执行过程和结果",
            source="system",
        ),
        VariableSpec(
            name="指令内容",
            source="system",
        ),
        VariableSpec(
            name="时间估算",
            source="system",
        ),
    ],
)

# --- foundation/xiaonuo_l1_foundation_v2_optimized (staging) ---
FOUNDATION_XIAONUO_L1_FOUNDATION_V2_OPTIMIZED_SCHEMA = PromptSchema(
    rule_id="foundation/xiaonuo_l1_foundation_v2_optimized",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="估算",
            source="system",
        ),
        VariableSpec(
            name="工具名称",
            source="system",
        ),
        VariableSpec(
            name="步骤1_2_3",
            source="system",
        ),
        VariableSpec(
            name="理由",
            source="system",
        ),
        VariableSpec(
            name="需求概括",
            source="user_input",
        ),
    ],
)

# --- foundation/xiaonuo_l5_hitl (staging) ---
FOUNDATION_XIAONUO_L5_HITL_SCHEMA = PromptSchema(
    rule_id="foundation/xiaonuo_l5_hitl",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="下一步操作",
            source="system",
        ),
        VariableSpec(
            name="不确定性说明",
            source="system",
        ),
        VariableSpec(
            name="任务名称",
            source="system",
        ),
        VariableSpec(
            name="关键发现1",
            source="system",
        ),
        VariableSpec(
            name="关键发现2",
            source="system",
        ),
    ],
)
