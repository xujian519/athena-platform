#!/usr/bin/env python3
"""
专利代理类型配置验证脚本
Patent Agents Configuration Validator

验证config/patent/patent_agents.yaml配置文件的正确性。

作者: Agent-3 (domain-adapter-tester)
版本: 1.0.0
创建日期: 2026-04-05
"""

import sys
from pathlib import Path

import yaml


class ConfigValidator:
    """配置验证器"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = None
        self.errors = []
        self.warnings = []

    def load_config(self) -> bool:
        """加载配置文件"""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
            print(f"✅ 成功加载配置文件: {self.config_path}")
            return True
        except FileNotFoundError:
            self.errors.append(f"配置文件不存在: {self.config_path}")
            return False
        except yaml.YAMLError as e:
            self.errors.append(f"YAML解析错误: {e}")
            return False

    def validate_structure(self) -> bool:
        """验证配置结构"""
        print("\n📋 验证配置结构...")

        # 检查顶级键
        required_keys = ["patent_agent_types", "global", "version"]
        for key in required_keys:
            if key not in self.config:
                self.errors.append(f"缺少必需的顶级键: {key}")

        # 检查专利代理类型
        if "patent_agent_types" in self.config:
            agent_types = self.config["patent_agent_types"]
            required_agent_types = [
                "patent-analyst",
                "patent-searcher",
                "legal-researcher",
                "patent-drafter",
            ]

            for agent_type in required_agent_types:
                if agent_type not in agent_types:
                    self.errors.append(f"缺少代理类型: {agent_type}")

        return len(self.errors) == 0

    def validate_patent_analyst(self) -> bool:
        """验证专利分析师配置"""
        print("\n🔬 验证专利分析师配置...")

        agent = self.config["patent_agent_types"].get("patent-analyst", {})

        # 基本信息
        required_fields = [
            "name",
            "description",
            "version",
            "model",
            "tools",
            "capabilities",
            "workflows",
            "performance",
        ]
        for field in required_fields:
            if field not in agent:
                self.errors.append(f"patent-analyst缺少字段: {field}")

        # 模型配置
        if "model" in agent:
            model = agent["model"]
            if "primary" not in model:
                self.errors.append("patent-analyst.model缺少primary字段")
            elif model["primary"] not in ["haiku", "sonnet", "opus"]:
                self.errors.append(f"patent-analyst.model.primary无效: {model['primary']}")

            if "fallback" not in model:
                self.warnings.append("patent-analyst.model缺少fallback字段")

        # 工具配置
        if "tools" in agent:
            tools = agent["tools"]
            required_tool_types = ["required", "optional"]
            for tool_type in required_tool_types:
                if tool_type not in tools:
                    self.warnings.append(f"patent-analyst.tools缺少{tool_type}字段")

            # 检查必需工具
            if "required" in tools:
                required_tools = tools["required"]
                required_tool_names = [
                    "patent-search",
                    "patent-analysis",
                    "knowledge-graph-query",
                    "embedding-search",
                ]
                for tool_name in required_tool_names:
                    if not any(tool.get("name") == tool_name for tool in required_tools):
                        self.errors.append(f"patent-analyst缺少必需工具: {tool_name}")

        # 能力配置
        if "capabilities" in agent:
            capabilities = agent["capabilities"]
            required_capabilities = [
                "patent-technical-analysis",
                "patent-innovation-assessment",
                "patent-comparative-analysis",
            ]
            for capability in required_capabilities:
                if not any(cap.get("name") == capability for cap in capabilities):
                    self.warnings.append(f"patent-analyst缺少能力: {capability}")

        # 性能配置
        if "performance" in agent:
            perf = agent["performance"]
            if "max_execution_time" not in perf:
                self.warnings.append("patent-analyst.performance缺少max_execution_time")
            if "max_tool_calls" not in perf:
                self.warnings.append("patent-analyst.performance缺少max_tool_calls")

        return len(self.errors) == 0

    def validate_patent_searcher(self) -> bool:
        """验证专利检索专家配置"""
        print("\n🔍 验证专利检索专家配置...")

        agent = self.config["patent_agent_types"].get("patent-searcher", {})

        # 模型配置验证
        if "model" in agent:
            model = agent["model"]
            if model.get("primary") != "haiku":
                self.warnings.append(
                    f"patent-searcher建议使用haiku模型,当前: {model.get('primary')}"
                )

        # 工具配置
        if "tools" in agent:
            tools = agent["tools"]
            if "required" in tools:
                required_tools = tools["required"]
                required_tool_names = ["patent-search", "patent-filter", "patent-export"]
                for tool_name in required_tool_names:
                    if not any(tool.get("name") == tool_name for tool in required_tools):
                        self.errors.append(f"patent-searcher缺少必需工具: {tool_name}")

        # 性能配置
        if "performance" in agent:
            perf = agent["performance"]
            if not perf.get("run_in_background"):
                self.warnings.append("patent-searcher建议支持后台运行")

        return len(self.errors) == 0

    def validate_legal_researcher(self) -> bool:
        """验证法律研究员配置"""
        print("\n⚖️ 验证法律研究员配置...")

        agent = self.config["patent_agent_types"].get("legal-researcher", {})

        # 模型配置验证
        if "model" in agent:
            model = agent["model"]
            if model.get("primary") != "opus":
                self.warnings.append(
                    f"legal-researcher建议使用opus模型,当前: {model.get('primary')}"
                )

        # 工具配置
        if "tools" in agent:
            tools = agent["tools"]
            if "required" in tools:
                required_tools = tools["required"]
                required_tool_names = ["legal-knowledge-query", "case-law-search", "statute-lookup"]
                for tool_name in required_tool_names:
                    if not any(tool.get("name") == tool_name for tool in required_tools):
                        self.errors.append(f"legal-researcher缺少必需工具: {tool_name}")

        return len(self.errors) == 0

    def validate_patent_drafter(self) -> bool:
        """验证专利撰写专家配置"""
        print("\n✍️ 验证专利撰写专家配置...")

        agent = self.config["patent_agent_types"].get("patent-drafter", {})

        # 模型配置验证
        if "model" in agent:
            model = agent["model"]
            if model.get("primary") != "opus":
                self.warnings.append(f"patent-drafter建议使用opus模型,当前: {model.get('primary')}")

        # 工具配置
        if "tools" in agent:
            tools = agent["tools"]
            if "required" in tools:
                required_tools = tools["required"]
                required_tool_names = ["patent-drafting", "patent-review", "patent-formatting"]
                for tool_name in required_tool_names:
                    if not any(tool.get("name") == tool_name for tool in required_tools):
                        self.errors.append(f"patent-drafter缺少必需工具: {tool_name}")

        return len(self.errors) == 0

    def validate_global_config(self) -> bool:
        """验证全局配置"""
        print("\n🌐 验证全局配置...")

        if "global" not in self.config:
            self.errors.append("缺少global配置")
            return False

        global_config = self.config["global"]

        # 检查工具映射
        if "tool_mappings" not in global_config:
            self.warnings.append("global配置缺少tool_mappings")
        else:
            tool_mappings = global_config["tool_mappings"]
            required_tools = [
                "patent-search",
                "patent-analysis",
                "knowledge-graph-query",
                "search-strategy-builder",
                "legal-knowledge-query",
                "case-law-search",
                "patent-drafting",
            ]
            for tool in required_tools:
                if tool not in tool_mappings:
                    self.errors.append(f"tool_mappings缺少工具映射: {tool}")

        # 检查模型映射
        if "model_mappings" not in global_config:
            self.warnings.append("global配置缺少model_mappings")
        else:
            model_mappings = global_config["model_mappings"]
            required_models = ["haiku", "sonnet", "opus"]
            for model in required_models:
                if model not in model_mappings:
                    self.errors.append(f"model_mappings缺少模型映射: {model}")

        # 检查默认配置
        if "defaults" not in global_config:
            self.warnings.append("global配置缺少defaults")
        else:
            defaults = global_config["defaults"]
            required_defaults = ["timeout", "max_retries", "max_concurrent_tasks"]
            for default in required_defaults:
                if default not in defaults:
                    self.warnings.append(f"defaults缺少{default}")

        return len(self.errors) == 0

    def validate_workflows(self) -> bool:
        """验证工作流配置"""
        print("\n🔄 验证工作流配置...")

        agent_types = self.config["patent_agent_types"]
        expected_workflows = {
            "patent-analyst": ["patent-analysis-workflow"],
            "patent-searcher": ["patent-search-workflow"],
            "legal-researcher": ["legal-research-workflow"],
            "patent-drafter": ["patent-drafting-workflow"],
        }

        for agent_type, workflow_names in expected_workflows.items():
            agent = agent_types.get(agent_type, {})
            if "workflows" not in agent:
                self.errors.append(f"{agent_type}缺少workflows配置")
                continue

            workflows = agent["workflows"]
            for workflow_name in workflow_names:
                if not any(wf.get("name") == workflow_name for wf in workflows):
                    self.errors.append(f"{agent_type}缺少工作流: {workflow_name}")

                # 验证工作流步骤
                for workflow in workflows:
                    if workflow.get("name") == workflow_name:
                        if "steps" not in workflow:
                            self.errors.append(f"{agent_type}.{workflow_name}缺少steps配置")
                        else:
                            steps = workflow["steps"]
                            for i, step in enumerate(steps):
                                if "step" not in step:
                                    self.warnings.append(
                                        f"{agent_type}.{workflow_name}.step{i}缺少step序号"
                                    )
                                if "name" not in step:
                                    self.errors.append(
                                        f"{agent_type}.{workflow_name}.step{i}缺少name字段"
                                    )
                                if "tool" not in step:
                                    self.errors.append(
                                        f"{agent_type}.{workflow_name}.step{i}缺少tool字段"
                                    )

        return len(self.errors) == 0

    def validate_version(self) -> bool:
        """验证版本信息"""
        print("\n📌 验证版本信息...")

        if "version" not in self.config:
            self.errors.append("配置文件缺少version字段")
            return False

        version = self.config["version"]
        print(f"   配置版本: {version}")

        # 检查必需的元数据
        required_metadata = ["created_at", "updated_at", "author", "description"]
        for meta in required_metadata:
            if meta not in self.config:
                self.warnings.append(f"配置文件缺少{meta}字段")

        return True

    def print_summary(self) -> None:
        """打印验证摘要"""
        print("\n" + "=" * 60)
        print("📊 验证摘要")
        print("=" * 60)

        if len(self.errors) == 0:
            print("\n✅ 配置验证通过！没有发现错误。")
        else:
            print(f"\n❌ 发现 {len(self.errors)} 个错误:")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")

        if len(self.warnings) > 0:
            print(f"\n⚠️  发现 {len(self.warnings)} 个警告:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")

        print("\n" + "=" * 60)
        if len(self.errors) == 0:
            print("✅ 配置文件可以正常使用！")
        else:
            print("❌ 配置文件需要修复错误后才能使用。")
        print("=" * 60 + "\n")

    def validate(self) -> bool:
        """执行完整验证"""
        print("🔍 开始验证专利代理类型配置...")
        print(f"📁 配置文件: {self.config_path}")

        # 加载配置
        if not self.load_config():
            return False

        # 验证各个部分
        self.validate_structure()
        self.validate_version()
        self.validate_patent_analyst()
        self.validate_patent_searcher()
        self.validate_legal_researcher()
        self.validate_patent_drafter()
        self.validate_global_config()
        self.validate_workflows()

        # 打印摘要
        self.print_summary()

        return len(self.errors) == 0


def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python3 validate_patent_config.py <config_file>")
        print("示例: python3 validate_patent_config.py config/patent/patent_agents.yaml")
        sys.exit(1)

    config_path = sys.argv[1]
    validator = ConfigValidator(config_path)

    success = validator.validate()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
