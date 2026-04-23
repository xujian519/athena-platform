"""
Prompt 语法升级对比测试

验证：同一份变量字典，用 legacy {var} 渲染和用 Jinja2 {{ var }} 渲染结果一致。
"""

from __future__ import annotations

import pytest
from jinja2 import Environment

from core.prompt_engine.renderer import PromptRenderer


def _legacy_render(template: str, variables: dict) -> str:
    """模拟 legacy 渲染逻辑（与 MockScenarioRule.substitute_variables 保持一致）。"""
    for key, value in variables.items():
        placeholder = "{" + key + "}"
        str_value = str(value) if value is not None else ""
        template = template.replace(placeholder, str_value)
    return template


class TestSyntaxUpgradeEquivalence:
    """验证 Jinja2 升级后的模板与 legacy 渲染结果一致。"""

    @pytest.fixture
    def jinja_env(self):
        """带 keep_trailing_newline 的 Jinja2 环境，用于精确对比。"""
        return Environment(keep_trailing_newline=True)

    def test_simple_variable(self, jinja_env: Environment):
        legacy_tpl = "申请号: {application_number}"
        jinja2_tpl = "申请号: {{ application_number }}"
        variables = {"application_number": "CN20231001"}

        legacy_result = _legacy_render(legacy_tpl, variables)
        jinja2_result = jinja_env.from_string(jinja2_tpl).render(**variables)

        assert legacy_result == jinja2_result

    def test_multiple_variables(self, jinja_env: Environment):
        legacy_tpl = (
            "申请号: {application_number}\n"
            "技术领域: {technical_field}\n"
            "权利要求: {claims}"
        )
        jinja2_tpl = (
            "申请号: {{ application_number }}\n"
            "技术领域: {{ technical_field }}\n"
            "权利要求: {{ claims }}"
        )
        variables = {
            "application_number": "CN20231001",
            "technical_field": "人工智能",
            "claims": "一种基于深度学习的...",
        }

        legacy_result = _legacy_render(legacy_tpl, variables)
        jinja2_result = jinja_env.from_string(jinja2_tpl).render(**variables)

        assert legacy_result == jinja2_result

    def test_optional_variable_with_default(self, jinja_env: Environment):
        """可选变量使用 | default('') 时应优雅处理缺失值。"""
        legacy_tpl = "历史: {oa_history}"
        jinja2_tpl = "历史: {{ oa_history | default('') }}"

        # 情况 1: 变量存在时两者一致
        variables = {"oa_history": "此前审查意见"}
        legacy_result = _legacy_render(legacy_tpl, variables)
        jinja2_result = jinja_env.from_string(jinja2_tpl).render(**variables)
        assert legacy_result == jinja2_result

        # 情况 2: 变量缺失时，legacy 保留占位符，Jinja2 使用默认值（更优）
        variables_missing = {}
        legacy_result_missing = _legacy_render(legacy_tpl, variables_missing)
        jinja2_result_missing = jinja_env.from_string(jinja2_tpl).render(**variables_missing)
        assert legacy_result_missing == "历史: {oa_history}"
        assert jinja2_result_missing == "历史: "

    def test_literal_braces(self, jinja_env: Environment):
        """验证文件中已有的 {{ / }} 字面量转义后输出一致。"""
        legacy_tpl = "```json\n{{\n    \"key\": {value}\n}}\n```"
        jinja2_tpl = "```json\n{{ '{{' }}\n    \"key\": {{ value }}\n{{ '}}' }}\n```"
        variables = {"value": "42"}

        legacy_result = _legacy_render(legacy_tpl, variables)
        jinja2_result = jinja_env.from_string(jinja2_tpl).render(**variables)

        assert legacy_result == jinja2_result

    def test_real_scenario_rule_office_action(self, jinja_env: Environment):
        """使用真实 scenario_rule 模板进行端到端对比。"""
        from pathlib import Path

        rule_file = Path(__file__).parent.parent.parent / (
            "domains/legal/core_modules/legal_world_model/"
            "scenario_rules/patent_office_action_analysis.py"
        )
        if not rule_file.exists():
            pytest.skip("scenario rule file not found")

        content = rule_file.read_text(encoding="utf-8")
        import re

        m = re.search(
            r'user_prompt_template="""(.+?)"""',
            content,
            re.DOTALL,
        )
        if not m:
            pytest.skip("user_prompt_template not found")

        jinja2_tpl = m.group(1)
        # 构造对应的 legacy 模板（将 Jinja2 语法还原）
        legacy_tpl = re.sub(r"\{\{\s+([a-z_][a-z0-9_]*)\s*\|?\s*[^}]*\}\}", r"{\1}", jinja2_tpl)

        variables = {
            "application_number": "CN20231001",
            "oa_content": "审查意见通知书内容",
            "application_file": "本申请原始文件",
            "oa_history": "历史审查意见",
        }

        legacy_result = _legacy_render(legacy_tpl, variables)
        jinja2_result = jinja_env.from_string(jinja2_tpl).render(**variables)

        assert legacy_result == jinja2_result

    def test_real_capability_inventive_v3(self, jinja_env: Environment):
        """使用真实 capability 模板进行端到端对比。"""
        import re
        from pathlib import Path

        md_file = Path(__file__).parent.parent.parent / (
            "prompts/capability/cap04_inventive_v3_llm_integration.md"
        )
        if not md_file.exists():
            pytest.skip("capability file not found")

        jinja2_tpl = md_file.read_text(encoding="utf-8")
        # 构造 legacy 模板：将 Jinja2 变量还原为 legacy，保留字面量 {{ / }}
        legacy_tpl = jinja2_tpl
        legacy_tpl = legacy_tpl.replace("{{ '{{' }}", "{{")
        legacy_tpl = legacy_tpl.replace("{{ '}}' }}", "}}")
        legacy_tpl = re.sub(r"\{\{\s+([a-z_][a-z0-9_]*)\s*\}\}", r"{\1}", legacy_tpl)

        variables = {
            "patent_data": '{"title": "测试专利"}',
            "prior_art": '{"d1": "对比文件1"}',
            "differences": '["特征A", "特征B"]',
            "technical_field": "人工智能",
        }

        legacy_result = _legacy_render(legacy_tpl, variables)
        jinja2_result = jinja_env.from_string(jinja2_tpl).render(**variables)

        assert legacy_result == jinja2_result

    def test_prompt_renderer_integration(self):
        """验证 PromptRenderer 能正确渲染升级后的语法。"""
        renderer = PromptRenderer()
        template = "申请号: {{ application_number }}，技术领域: {{ technical_field }}"
        variables = {
            "application_number": "CN20231001",
            "technical_field": "人工智能",
        }

        result = renderer.render(template, variables)
        assert "CN20231001" in result
        assert "人工智能" in result

    def test_prompt_renderer_default_filter(self):
        """验证 PromptRenderer 的 default 过滤器对 None 生效。"""
        renderer = PromptRenderer()
        template = "历史: {{ oa_history | default('无') }}"

        result = renderer.render(template, {"oa_history": None})
        assert "历史: 无" == result

        result = renderer.render(template, {"oa_history": "有历史"})
        assert "历史: 有历史" == result
