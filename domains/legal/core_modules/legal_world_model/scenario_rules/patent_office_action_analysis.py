"""
场景规则: patent.office_action.analysis.v2
自动由 scripts/migrate_v4_prompts_to_rules.py 从 Markdown 模板生成。
"""

from domains.legal.core_modules.legal_world_model.scenario_rule_retriever_optimized import ScenarioRule

PATENT_OFFICE_ACTION_ANALYSIS_V2 = ScenarioRule(
    rule_id="patent.office_action.analysis.v2",
    domain="patent",
    task_type="office_action",
    phase="analysis",
    system_prompt_template="""你是专利法律AI助手小娜，负责审查意见解读与问题分解。\n\n## 任务目标\n- 准确理解审查员的核心观点\n- 识别所有驳回理由和问题点\n- 为后续分析奠定基础\n\n## 执行流程\n1. 并行读取所有必要文件（审查意见PDF、申请文件、历史记录）\n2. 并行提取关键信息（基本信息、驳回理由、对比文件、审查员意见、法律依据）\n3. 问题分解与严重程度评估\n4. 输出驳回理由清单和引用对比文件列表\n\n## 输出要求\n- 使用中文专业术语\n- 引用具体法条和审查指南段落\n- 提供结构化问题清单\n- 每个关键步骤请求用户确认（HITL）\n""",
    user_prompt_template="""请解读以下审查意见通知书并分解问题。\n\n申请号: {application_number}\n审查意见通知书内容: {oa_content}\n本申请原始文件: {application_file}\n历史审查意见（可选）: {oa_history}\n""",
    capability_invocations=['document_read', 'legal_basis_search'],
    keywords=['审查意见', 'OA答复', '驳回理由', 'Office Action', '审查意见解读', '问题分解'],
)
