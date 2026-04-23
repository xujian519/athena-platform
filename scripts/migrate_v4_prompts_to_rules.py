#!/usr/bin/env python3
"""
将 prompts/ 目录中的 v4 Markdown 资产迁移为场景规则定义。

用法:
    python scripts/migrate_v4_prompts_to_rules.py

输出:
    domains/legal/core_modules/legal_world_model/scenario_rules/*.py
"""

import re
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"
OUTPUT_DIR = PROJECT_ROOT / "domains/legal/core_modules/legal_world_model/scenario_rules"


def read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_variable_placeholders(text: str) -> list[str]:
    """提取 Markdown 中可能的变量占位符（如 [申请号]、{application_number} 等）。"""
    # 匹配 [中文占位] 和 {var_name}
    patterns = [
        r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}",
        r"\[([^\]]+)\]",
    ]
    results = []
    for pat in patterns:
        results.extend(re.findall(pat, text))
    return sorted(set(results))


def convert_to_scenario_rule(
    rule_id: str,
    domain: str,
    task_type: str,
    phase: str,
    system_template: str,
    user_template: str,
    capability_invocations: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
) -> str:
    """生成场景规则的 Python 代码。"""
    cap_str = repr(capability_invocations or [])
    kw_str = repr(keywords or [])    
    # 转义三引号
    safe_system = system_template.replace('"""', '""\"')
    safe_user = user_template.replace('"""', '""\"')

    return f'''\
"""
场景规则: {rule_id}
自动由 scripts/migrate_v4_prompts_to_rules.py 从 Markdown 模板生成。
"""

from domains.legal.core_modules.legal_world_model.scenario_rule_retriever_optimized import ScenarioRule

{rule_id.upper().replace(".", "_")} = ScenarioRule(
    rule_id="{rule_id}",
    domain="{domain}",
    task_type="{task_type}",
    phase="{phase}",
    system_prompt_template="""{safe_system}""",
    user_prompt_template="""{safe_user}""",
    capability_invocations={cap_str},
    keywords={kw_str},
)
'''


def migrate_hitl_safety():
    src = PROMPTS_DIR / "foundation/hitl_protocol_v4_constraint_repeat.md"
    content = read_markdown(src)

    # HITL 作为 safety block，附加到所有场景的 system_prompt 末尾
    output = OUTPUT_DIR / "hitl_safety_block.py"
    safe_content = content.replace('"""', '""\"')
    code = f'''\
"""
HITL Safety Block (v4.0)
自动由 scripts/migrate_v4_prompts_to_rules.py 从 Markdown 模板生成。

本块应附加到所有高风险场景的 system_prompt_template 末尾。
"""

HITL_SAFETY_BLOCK = """{safe_content}"""
'''
    output.write_text(code, encoding="utf-8")
    print(f"[OK] HITL safety block -> {output}")


def migrate_inventive_analysis():
    src = PROMPTS_DIR / "capability/cap04_inventive_v2_with_whenToUse.md"
    content = read_markdown(src)

    # 提取 whenToUse 中的关键词
    keywords = [
        "分析创造性", "三步法", "判断是否显而易见", "创造性分析",
        "inventive step", "D1+D2是否结合", "是否存在技术启示",
        "预料不到的技术效果", "授权可能性", "区别特征",
    ]

    # 简化 system_template：取能力描述 + 执行流程概述
    # 去掉具体的 Python 伪代码（保持为注释/说明）
    system_template = (
        "你是专利法律AI助手小娜，具备创造性分析能力。\\n\\n"
        "## 能力描述\\n"
        "你能够采用'三步法'进行专利创造性分析，基于审查指南和真实案例，"
        "预判授权可能性并给出改进建议。\\n\\n"
        "## 执行流程\\n"
        "1. 确定最接近的现有技术（D1）\\n"
        "2. 确定区别特征和实际解决的技术问题\\n"
        "3. 判断区别特征对本领域技术人员是否显而易见\\n"
        "4. 给出创造性结论和授权可能性评估\\n"
        "5. 若创造性不足，提供改进建议\\n\\n"
        "## 输出要求\\n"
        "- 使用中文专业术语\\n"
        "- 引用具体法条和审查指南段落\\n"
        "- 提供结构化对比表格\\n"
        "- 每个关键步骤请求用户确认（HITL）\\n"
    )

    user_template = (
        "请对以下专利进行创造性分析。\\n\\n"
        "申请号: {application_number}\\n"
        "技术领域: {technical_field}\\n"
        "权利要求: {claims}\\n"
        "现有技术对比文件: {prior_art_documents}\\n"
        "审查意见要点: {office_action_summary}\\n"
    )

    code = convert_to_scenario_rule(
        rule_id="patent.inventive_analysis.v2",
        domain="patent",
        task_type="inventive_analysis",
        phase="analysis",
        system_template=system_template,
        user_template=user_template,
        capability_invocations=["prior_art_search", "claim_analysis"],
        keywords=keywords,
    )

    output = OUTPUT_DIR / "patent_inventive_analysis.py"
    output.write_text(code, encoding="utf-8")
    print(f"[OK] Inventive analysis rule -> {output}")
    print(f"      Variables: {extract_variable_placeholders(user_template)}")


def migrate_office_action_analysis():
    src = PROMPTS_DIR / "business/task_2_1_oa_analysis_v2_with_parallel.md"
    content = read_markdown(src)

    keywords = [
        "审查意见", "OA答复", "驳回理由", "Office Action",
        "审查意见解读", "问题分解",
    ]

    system_template = (
        "你是专利法律AI助手小娜，负责审查意见解读与问题分解。\\n\\n"
        "## 任务目标\\n"
        "- 准确理解审查员的核心观点\\n"
        "- 识别所有驳回理由和问题点\\n"
        "- 为后续分析奠定基础\\n\\n"
        "## 执行流程\\n"
        "1. 并行读取所有必要文件（审查意见PDF、申请文件、历史记录）\\n"
        "2. 并行提取关键信息（基本信息、驳回理由、对比文件、审查员意见、法律依据）\\n"
        "3. 问题分解与严重程度评估\\n"
        "4. 输出驳回理由清单和引用对比文件列表\\n\\n"
        "## 输出要求\\n"
        "- 使用中文专业术语\\n"
        "- 引用具体法条和审查指南段落\\n"
        "- 提供结构化问题清单\\n"
        "- 每个关键步骤请求用户确认（HITL）\\n"
    )

    user_template = (
        "请解读以下审查意见通知书并分解问题。\\n\\n"
        "申请号: {application_number}\\n"
        "审查意见通知书内容: {oa_content}\\n"
        "本申请原始文件: {application_file}\\n"
        "历史审查意见（可选）: {oa_history}\\n"
    )

    code = convert_to_scenario_rule(
        rule_id="patent.office_action.analysis.v2",
        domain="patent",
        task_type="office_action",
        phase="analysis",
        system_template=system_template,
        user_template=user_template,
        capability_invocations=["document_read", "legal_basis_search"],
        keywords=keywords,
    )

    output = OUTPUT_DIR / "patent_office_action_analysis.py"
    output.write_text(code, encoding="utf-8")
    print(f"[OK] Office action analysis rule -> {output}")
    print(f"      Variables: {extract_variable_placeholders(user_template)}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    migrate_hitl_safety()
    migrate_inventive_analysis()
    migrate_office_action_analysis()
    print("\\n全部迁移完成。下一步：")
    print("  1. 人工审核生成的 system_prompt_template 和 user_prompt_template")
    print("  2. 执行写入 Neo4j 的脚本（如需）")
    print("  3. 更新 MASTER_CHECKLIST 状态")


if __name__ == "__main__":
    main()
