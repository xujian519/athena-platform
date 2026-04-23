#!/usr/bin/env python3
"""
专利代理配置验证脚本

验证 config/patent_agents.yaml 配置文件的完整性和正确性。

Usage:
    python scripts/validate_patent_agents_config.py [--config CONFIG_PATH]
"""

import sys
from pathlib import Path
from typing import Any

import yaml


class ConfigValidationError(Exception):
    """配置验证错误"""

    pass


class PatentAgentsConfigValidator:
    """专利代理配置验证器"""

    REQUIRED_TOP_LEVEL_KEYS = [
        "version",
        "global",
        "model_templates",
        "agents",
        "tools",
        "validation",
    ]
    REQUIRED_AGENT_KEYS = [
        "display_name",
        "description",
        "model",
        "priority",
        "capabilities",
        "tools",
        "system_prompt",
    ]
    REQUIRED_MODEL_KEYS = ["default", "fallback", "template"]

    ALLOWED_MODELS = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-opus-4-20250514",
        "gpt-4",
        "gpt-4-turbo",
        "deepseek-chat",
        "glm-4",
    ]

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config: dict[str, Any] = {}
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def load_config(self) -> bool:
        if not self.config_path.exists():
            self.errors.append(f"配置文件不存在: {self.config_path}")
            return False

        try:
            with open(self.config_path, encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
            return True
        except yaml.YAMLError as e:
            self.errors.append(f"YAML解析错误: {e}")
            return False
        except Exception as e:
            self.errors.append(f"读取配置文件失败: {e}")
            return False

    def validate_structure(self) -> bool:
        for key in self.REQUIRED_TOP_LEVEL_KEYS:
            if key not in self.config:
                self.errors.append(f"缺少必需的顶级配置项: {key}")

        return len(self.errors) == 0

    def validate_global_config(self) -> bool:
        if "global" not in self.config:
            return False

        global_config = self.config["global"]
        required_keys = ["default_timeout", "max_retries", "retry_delay", "health_check_interval"]

        for key in required_keys:
            if key not in global_config:
                self.errors.append(f"全局配置缺少必需字段: {key}")

        if "default_timeout" in global_config:
            timeout = global_config["default_timeout"]
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                self.errors.append(f"无效的default_timeout值: {timeout}")

        return len([e for e in self.errors if "全局配置" in e]) == 0

    def validate_model_templates(self) -> bool:
        if "model_templates" not in self.config:
            return False

        templates = self.config["model_templates"]
        required_templates = ["fast", "balanced", "deep"]

        for template_name in required_templates:
            if template_name not in templates:
                self.errors.append(f"缺少必需的模型模板: {template_name}")
                continue

            template = templates[template_name]
            required_keys = ["temperature", "max_tokens", "top_p"]

            for key in required_keys:
                if key not in template:
                    self.errors.append(f"模型模板 {template_name} 缺少必需字段: {key}")

            if "temperature" in template:
                temp = template["temperature"]
                if not (0 <= temp <= 1):
                    self.warnings.append(
                        f"模型模板 {template_name} 的temperature值超出建议范围[0, 1]: {temp}"
                    )

            if "max_tokens" in template:
                tokens = template["max_tokens"]
                if not isinstance(tokens, int) or tokens <= 0:
                    self.errors.append(f"模型模板 {template_name} 的max_tokens无效: {tokens}")

        return len([e for e in self.errors if "模型模板" in e]) == 0

    def validate_agents(self) -> bool:
        if "agents" not in self.config:
            return False

        agents = self.config["agents"]

        if not agents:
            self.errors.append("没有定义任何代理类型")
            return False

        expected_agents = [
            "patent-analyst",
            "patent-searcher",
            "legal-researcher",
            "patent-drafter",
        ]

        for agent_type in expected_agents:
            if agent_type not in agents:
                self.errors.append(f"缺少必需的代理类型: {agent_type}")

        for agent_type, agent_config in agents.items():
            self._validate_single_agent(agent_type, agent_config)

        return len([e for e in self.errors if "代理" in e]) == 0

    def _validate_single_agent(self, agent_type: str, agent_config: dict[str, Any]) -> None:
        for key in self.REQUIRED_AGENT_KEYS:
            if key not in agent_config:
                self.errors.append(f"代理 {agent_type} 缺少必需字段: {key}")
                return

        if "model" in agent_config:
            model_config = agent_config["model"]

            for key in self.REQUIRED_MODEL_KEYS:
                if key not in model_config:
                    self.errors.append(f"代理 {agent_type} 的model配置缺少必需字段: {key}")

            if "default" in model_config:
                default_model = model_config["default"]
                if default_model not in self.ALLOWED_MODELS:
                    self.warnings.append(
                        f"代理 {agent_type} 的default模型 {default_model} 不在推荐列表中"
                    )

            if "template" in model_config:
                template = model_config["template"]
                if template not in ["fast", "balanced", "deep"]:
                    self.errors.append(f"代理 {agent_type} 的model.template无效: {template}")

        if "priority" in agent_config:
            priority = agent_config["priority"]
            if not (1 <= priority <= 10):
                self.errors.append(f"代理 {agent_type} 的priority值超出范围[1, 10]: {priority}")

        if "capabilities" in agent_config:
            capabilities = agent_config["capabilities"]
            if not isinstance(capabilities, list) or len(capabilities) == 0:
                self.errors.append(f"代理 {agent_type} 的capabilities必须是非空列表")

            for capability in capabilities:
                if not isinstance(capability, dict):
                    self.errors.append(f"代理 {agent_type} 的capability格式错误: {capability}")
                    continue

                if "name" not in capability:
                    self.errors.append(f"代理 {agent_type} 的capability缺少name字段")

        if "tools" in agent_config:
            tools_config = agent_config["tools"]

            if "allowed" not in tools_config:
                self.errors.append(f"代理 {agent_type} 的tools配置缺少allowed字段")
            elif not isinstance(tools_config["allowed"], list):
                self.errors.append(f"代理 {agent_type} 的tools.allowed必须是列表")

        if "concurrency" in agent_config:
            concurrency = agent_config["concurrency"]

            if "max_concurrent_tasks" in concurrency:
                max_tasks = concurrency["max_concurrent_tasks"]
                if not isinstance(max_tasks, int) or max_tasks <= 0:
                    self.errors.append(f"代理 {agent_type} 的max_concurrent_tasks无效: {max_tasks}")

            if "queue_size" in concurrency:
                queue_size = concurrency["queue_size"]
                if not isinstance(queue_size, int) or queue_size <= 0:
                    self.errors.append(f"代理 {agent_type} 的queue_size无效: {queue_size}")

        if "performance" in agent_config:
            performance = agent_config["performance"]

            if "target_accuracy" in performance:
                accuracy = performance["target_accuracy"]
                if not (0 <= accuracy <= 1):
                    self.errors.append(
                        f"代理 {agent_type} 的target_accuracy值超出范围[0, 1]: {accuracy}"
                    )

    def validate_tools(self) -> bool:
        if "tools" not in self.config:
            return False

        tools = self.config["tools"]

        if not tools:
            self.warnings.append("没有定义任何工具")
            return True

        required_tool_keys = ["description", "category"]

        for tool_name, tool_config in tools.items():
            for key in required_tool_keys:
                if key not in tool_config:
                    self.errors.append(f"工具 {tool_name} 缺少必需字段: {key}")

        return len([e for e in self.errors if "工具" in e]) == 0

    def validate_validation_rules(self) -> bool:
        if "validation" not in self.config:
            self.warnings.append("缺少validation配置段")
            return True

        validation = self.config["validation"]

        if "required_fields" in validation:
            required_fields = validation["required_fields"]
            if not isinstance(required_fields, list):
                self.errors.append("validation.required_fields必须是列表")

        if "constraints" in validation:
            constraints = validation["constraints"]
            if not isinstance(constraints, dict):
                self.errors.append("validation.constraints必须是字典")

        if "allowed_models" in validation:
            allowed_models = validation["allowed_models"]
            if not isinstance(allowed_models, list):
                self.errors.append("validation.allowed_models必须是列表")

        return len([e for e in self.errors if "validation" in e]) == 0

    def validate_cross_references(self) -> bool:
        if "agents" not in self.config or "tools" not in self.config:
            return False

        tools = self.config["tools"]
        agents = self.config["agents"]

        for agent_type, agent_config in agents.items():
            if "tools" not in agent_config:
                continue

            allowed_tools = agent_config["tools"].get("allowed", [])

            for tool_name in allowed_tools:
                if tool_name not in tools:
                    self.warnings.append(f"代理 {agent_type} 引用了未定义的工具: {tool_name}")

        if "model_templates" in self.config:
            templates = self.config["model_templates"]

            for agent_type, agent_config in agents.items():
                if "model" not in agent_config:
                    continue

                template_name = agent_config["model"].get("template")
                if template_name and template_name not in templates:
                    self.errors.append(f"代理 {agent_type} 引用了未定义的模型模板: {template_name}")

        return True

    def run_validation(self) -> bool:
        print("🔍 开始验证专利代理配置文件...")
        print(f"📁 配置文件: {self.config_path}\n")

        if not self.load_config():
            self._print_results()
            return False

        validations = [
            ("配置文件结构", self.validate_structure),
            ("全局配置", self.validate_global_config),
            ("模型配置模板", self.validate_model_templates),
            ("代理配置", self.validate_agents),
            ("工具定义", self.validate_tools),
            ("验证规则", self.validate_validation_rules),
            ("交叉引用", self.validate_cross_references),
        ]

        for name, validator in validations:
            print(f"  ✓ 验证 {name}...")
            try:
                validator()
            except Exception as e:
                self.errors.append(f"验证 {name} 时发生异常: {e}")

        self._print_results()

        return len(self.errors) == 0

    def _print_results(self) -> None:
        print("\n" + "=" * 60)

        if self.errors:
            print("❌ 验证失败\n")
            print(f"发现 {len(self.errors)} 个错误:\n")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")

        if self.warnings:
            print(f"\n⚠️  发现 {len(self.warnings)} 个警告:\n")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

        if not self.errors and not self.warnings:
            print("✅ 验证通过！配置文件完全正确。")

        print("=" * 60)

        if not self.errors and self.warnings:
            print("\n💡 提示: 虽然有警告，但配置文件仍然可以使用。")

        if self.errors:
            print("\n💡 提示: 请修复上述错误后重新验证。")

    def get_errors(self) -> list[str]:
        return self.errors

    def get_warnings(self) -> list[str]:
        return self.warnings


def main():
    import argparse

    parser = argparse.ArgumentParser(description="验证专利代理配置文件")
    parser.add_argument(
        "--config",
        default="config/patent_agents.yaml",
        help="配置文件路径 (默认: config/patent_agents.yaml)",
    )

    args = parser.parse_args()

    validator = PatentAgentsConfigValidator(args.config)
    success = validator.run_validation()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
