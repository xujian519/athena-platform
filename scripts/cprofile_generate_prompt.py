#!/usr/bin/env python3
"""
cProfile 性能分析脚本 — generate_prompt 关键路径（Python 3.11）

用法:
    python3.11 -m cProfile -s cumulative scripts/cprofile_generate_prompt.py
    python3.11 -m cProfile -o reports/cprofile_stats.raw scripts/cprofile_generate_prompt.py

输出:
    reports/cprofile_stats.txt   — 文本火焰图 + pstats 排序统计
"""
from __future__ import annotations

import cProfile
import io
import json
import os
import pstats
import sys
from pathlib import Path
from unittest.mock import MagicMock

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("LEGAL_PROMPT_FUSION_ENABLED", "false")

# 加载真实组件
from core.legal_world_model.scenario_identifier_optimized import ScenarioIdentifierOptimized
from core.prompt_engine.sanitizer import PromptSanitizer
from core.prompt_engine.schema import PromptSchema, VariableSpec, VariableType
from core.prompt_engine.validators import VariableValidator
from core.capabilities.prompt_template_cache import PromptTemplateCache
from core.legal_world_model.scenario_rule_retriever_optimized import ScenarioRule, ScenarioRuleRetrieverOptimized

# 压测数据集（与 tests/load/payloads 一致）
PAYLOADS = [
    {
        "user_input": "请分析这份审查意见通知书，申请号CN202310123456.7，审查员认为权利要求1不具备创造性，引用了对比文件D1（CN201910000001.2）和D2（CN202010000002.3）。",
        "additional_context": {
            "application_number": "CN202310123456.7",
            "office_action_type": "第一次审查意见通知书",
            "rejection_reason": "创造性",
            "cited_documents": ["CN201910000001.2", "CN202010000002.3"],
            "claim_numbers": [1, 3, 5],
            "technical_field": "人工智能/自然语言处理",
        },
    },
    {
        "user_input": "解读该审查意见，申请号CN202320987654.1，审查员指出权利要求2和4不符合专利法第26条第4款的规定，说明书公开不充分。",
        "additional_context": {
            "application_number": "CN202320987654.1",
            "office_action_type": "第二次审查意见通知书",
            "rejection_reason": "公开不充分",
            "article_26_4": True,
            "claim_numbers": [2, 4],
            "technical_field": "生物信息学/数据压缩",
        },
    },
    {
        "user_input": "分析审查意见，申请号CN202310555888.9，审查员以专利法第22条第2款（新颖性）驳回权利要求1，仅引用一篇对比文件D1（US20220001111A1）。",
        "additional_context": {
            "application_number": "CN202310555888.9",
            "office_action_type": "第一次审查意见通知书",
            "rejection_reason": "新颖性",
            "cited_documents": ["US20220001111A1"],
            "claim_numbers": [1],
            "technical_field": "新能源材料/固态电池",
        },
    },
    {
        "user_input": "请评估该技术方案的创造性，涉及一种基于区块链的供应链溯源系统。",
        "additional_context": {
            "application_number": "CN202340111222.3",
            "technical_field": "区块链/供应链",
            "claim_numbers": [1, 2, 3],
        },
    },
    {
        "user_input": "对比权利要求1与现有技术的新颖性，现有技术公开了一种相似的数据处理方法。",
        "additional_context": {
            "application_number": "CN202350333444.5",
            "technical_field": "数据处理/云计算",
            "cited_documents": ["CN202010000002.3"],
        },
    },
]

# 构建一个高频规则，模拟 retriever 返回
SAMPLE_RULE = ScenarioRule(
    rule_id="patent-office_action-exam-001",
    domain="patent",
    task_type="office_action",
    phase="examination",
    system_prompt_template=(
        "你是一名专利审查意见分析专家。\n"
        "申请号: {application_number}\n"
        "技术领域: {technical_field}\n"
        "审查意见类型: {office_action_type}\n\n"
        "请根据以下用户输入提供专业的审查意见分析。"
    ),
    user_prompt_template="{user_input}",
    variables={
        "application_number": '{"type": "string", "required": true}',
        "technical_field": '{"type": "string", "required": true}',
        "office_action_type": '{"type": "string", "required": false}',
    },
)


def _mock_db_manager():
    """返回最小可用的 db_manager mock，避免真实 Neo4j 连接。"""
    return MagicMock()


def _run_critical_path(iterations: int = 500):
    """
    模拟 generate_prompt 关键路径（无 HTTP / FastAPI 开销）。
    覆盖：场景识别 → 规则检索(mock) → 变量治理 → 缓存检查 → 模板渲染 → 缓存写入
    """
    identifier = ScenarioIdentifierOptimized()
    sanitizer = PromptSanitizer()
    validator = VariableValidator()
    cache = PromptTemplateCache(max_size=500, ttl_seconds=3600)
    db_manager = _mock_db_manager()
    retriever = ScenarioRuleRetrieverOptimized(
        db_manager=db_manager,
        enable_preload=False,   # 禁用预加载，避免 mock 副作用
        preload_on_init=False,
    )
    # 将高频规则直接注入 retriever 本地缓存，跳过 Neo4j
    retriever._cache[("patent", "office_action", "examination")] = (SAMPLE_RULE, __import__('datetime').datetime.now())
    retriever._cache[("patent", "creativity_analysis", "examination")] = (SAMPLE_RULE, __import__('datetime').datetime.now())
    retriever._cache[("patent", "novelty_analysis", "examination")] = (SAMPLE_RULE, __import__('datetime').datetime.now())

    for i in range(iterations):
        payload = PAYLOADS[i % len(PAYLOADS)]

        # 1. 场景识别（真实 BGE-M3 / 意图分类路径；但模型未加载，走 regex fallback）
        ctx = identifier.identify_scenario(
            payload["user_input"], payload.get("additional_context")
        )

        # 2. 规则检索（mock DB，真实缓存 + 验证路径）
        try:
            rule = retriever.retrieve_rule(
                ctx.domain.value, ctx.task_type.value, ctx.phase.value
            )
        except Exception:
            # identifier 可能返回 typo task_type（如 novelity_analysis），回退到样本规则
            rule = None
        if rule is None:
            rule = SAMPLE_RULE

        # 3. 变量准备
        all_variables = {
            **(ctx.extracted_variables or {}),
            **(payload.get("additional_context") or {}),
        }

        # 4. 变量治理（真实校验 + 清洗）
        schema_vars = []
        if hasattr(rule, "variables") and rule.variables:
            for var_name, var_info in rule.variables.items():
                schema_vars.append(
                    VariableSpec(
                        name=var_name,
                        type=VariableType.STRING,
                        required=True,
                    )
                )
        schema = PromptSchema(
            rule_id=rule.rule_id,
            template_version="1.0.0",
            variables=schema_vars,
        )
        validation = validator.validate(schema, all_variables)
        if validation.valid:
            sanitized_vars, _ = sanitizer.sanitize_variables(all_variables, schema=schema)
            all_variables = sanitized_vars

        # 5. 缓存查询
        cached = cache.get(
            domain=ctx.domain.value,
            task_type=ctx.task_type.value,
            phase=ctx.phase.value,
            variables=all_variables,
        )
        if cached:
            continue

        # 6. 模板渲染（真实 substitute_variables）
        system_prompt, user_prompt = rule.substitute_variables(all_variables)

        # 7. 缓存写入
        cache.set(
            domain=ctx.domain.value,
            task_type=ctx.task_type.value,
            phase=ctx.phase.value,
            variables=all_variables,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            scenario_rule_id=rule.rule_id,
        )


def _text_flame_graph(stats: pstats.Stats, top_n: int = 40) -> str:
    """
    将 pstats 数据格式化为文本火焰图（缩进树形， cumtime 占比）。
    """
    # 按 cumtime 排序获取 top 函数
    stats.sort_stats(pstats.SortKey.CUMULATIVE)
    stream = io.StringIO()
    stats.stream = stream
    stats.print_stats(top_n)
    summary = stream.getvalue()

    # 构建 call-tree 视图（caller -> callee）
    stream2 = io.StringIO()
    stats.stream = stream2
    stats.print_callers(top_n)
    callers = stream2.getvalue()

    stream3 = io.StringIO()
    stats.stream = stream3
    stats.print_callees(top_n)
    callees = stream3.getvalue()

    header = (
        "-" * 80 + "\n" +
        "  cProfile 文本火焰图 -- generate_prompt 关键路径\n" +
        "-" * 80 + "\n" +
        f"Python: {sys.version}\n" +
        f"工作目录: {os.getcwd()}\n" +
        f"分析命令: python3.11 -m cProfile -s cumulative scripts/cprofile_generate_prompt.py\n" +
        "\n" +
        "说明:\n" +
        "  - 每行格式: [ncalls] tottime percall cumtime percall function\n" +
        "  - print_callers / print_callees 展示调用关系（文本级火焰图）\n" +
        "  - 瓶颈定位：cumtime 高 + 自身 tottime 占比高 = 热点函数\n" +
        "-" * 80 + "\n\n"
    )

    return header + "--- 按 CUMULATIVE TIME 排序 TOP {} ---\n".format(top_n) + summary + "\n\n" + \
           "--- CALLERS（谁调用了热点函数）---\n" + callers + "\n\n" + \
           "--- CALLEES（热点函数调用了谁）---\n" + callees


def main():
    report_dir = project_root / "reports"
    report_dir.mkdir(exist_ok=True)
    raw_path = report_dir / "cprofile_stats.raw"
    txt_path = report_dir / "cprofile_stats.txt"

    print("[*] 预热（排除模块导入 JIT 开销）...")
    _run_critical_path(iterations=20)

    print(f"[*] 开始 cProfile: 500 次关键路径迭代 ...")
    profiler = cProfile.Profile()
    profiler.enable()
    _run_critical_path(iterations=500)
    profiler.disable()

    # 保存原始 stats（可用 snakeviz / gprof2dot 进一步可视化）
    profiler.dump_stats(str(raw_path))
    print(f"[*] 原始 stats 已保存: {raw_path}")

    # 生成文本报告
    stats = pstats.Stats(profiler)
    text_report = _text_flame_graph(stats, top_n=50)
    txt_path.write_text(text_report, encoding="utf-8")
    print(f"[*] 文本火焰图已保存: {txt_path}")

    # 控制台简版
    print("\n--- 关键热点（cumtime 排序 TOP 20）---")
    stats.sort_stats(pstats.SortKey.CUMULATIVE)
    stats.print_stats(20)


if __name__ == "__main__":
    main()
