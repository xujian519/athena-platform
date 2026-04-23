"""
场景规则: patent.inventive_analysis.v2
自动由 scripts/migrate_v4_prompts_to_rules.py 从 Markdown 模板生成。
"""

from domains.legal.core_modules.legal_world_model.scenario_rule_retriever_optimized import ScenarioRule

PATENT_INVENTIVE_ANALYSIS_V2 = ScenarioRule(
    rule_id="patent.inventive_analysis.v2",
    domain="patent",
    task_type="inventive_analysis",
    phase="analysis",
    system_prompt_template="""你是专利法律AI助手小娜，具备创造性分析能力。\n\n## 能力描述\n你能够采用'三步法'进行专利创造性分析，基于审查指南和真实案例，预判授权可能性并给出改进建议。\n\n## 执行流程\n1. 确定最接近的现有技术（D1）\n2. 确定区别特征和实际解决的技术问题\n3. 判断区别特征对本领域技术人员是否显而易见\n4. 给出创造性结论和授权可能性评估\n5. 若创造性不足，提供改进建议\n\n## 输出要求\n- 使用中文专业术语\n- 引用具体法条和审查指南段落\n- 提供结构化对比表格\n- 每个关键步骤请求用户确认（HITL）\n""",
    user_prompt_template="""请对以下专利进行创造性分析。\n\n申请号: {application_number}\n技术领域: {technical_field}\n权利要求: {claims}\n现有技术对比文件: {prior_art_documents}\n审查意见要点: {office_action_summary}\n""",
    capability_invocations=['prior_art_search', 'claim_analysis'],
    keywords=['分析创造性', '三步法', '判断是否显而易见', '创造性分析', 'inventive step', 'D1+D2是否结合', '是否存在技术启示', '预料不到的技术效果', '授权可能性', '区别特征'],
)
