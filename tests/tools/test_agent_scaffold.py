"""
Agent脚手架工具测试
==================

测试agent_scaffold.py的各项功能。

作者: Athena平台团队
版本: 1.0.0
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# 添加tools目录到路径
import sys
TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from create_agent import (
    AgentScaffoldTool,
    Colors,
)


# ==================== 固定装置 ====================

@pytest.fixture
def temp_dir():
    """临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def scaffold_tool(temp_dir):
    """创建测试用的脚手架工具"""
    tool = AgentScaffoldTool(project_root=temp_dir)
    return tool


# ==================== 颜色输出测试 ====================

class TestColors:
    """颜色输出测试"""

    def test_success(self):
        """测试成功消息"""
        msg = Colors.success("操作成功")
        assert "操作成功" in msg
        assert "\033[92m" in msg  # 绿色代码

    def test_error(self):
        """测试错误消息"""
        msg = Colors.error("操作失败")
        assert "操作失败" in msg
        assert "\033[91m" in msg  # 红色代码

    def test_warning(self):
        """测试警告消息"""
        msg = Colors.warning("警告信息")
        assert "警告信息" in msg
        assert "\033[93m" in msg  # 黄色代码

    def test_info(self):
        """测试信息消息"""
        msg = Colors.info("信息提示")
        assert "信息提示" in msg
        assert "\033[96m" in msg  # 青色代码


# ==================== 名称转换测试 ====================

class TestNameConversion:
    """名称转换测试"""

    def test_to_pascal_case_snake(self, scaffold_tool):
        """测试snake_case转PascalCase"""
        result = scaffold_tool._to_pascal_case("my_agent")
        assert result == "MyAgent"

    def test_to_pascal_case_camel(self, scaffold_tool):
        """测试camelCase转PascalCase"""
        result = scaffold_tool._to_pascal_case("myAgent")
        assert result == "MyAgent"

    def test_to_pascal_case_with_numbers(self, scaffold_tool):
        """测试带数字的转换"""
        result = scaffold_tool._to_pascal_case("agent_123")
        assert result == "Agent123"

    def test_to_pascal_case_with_underscores(self, scaffold_tool):
        """测试多个下划线的转换"""
        result = scaffold_tool._to_pascal_case("my_very_special_agent")
        assert result == "MyVerySpecialAgent"

    def test_to_snake_case_pascal(self, scaffold_tool):
        """测试PascalCase转snake_case"""
        result = scaffold_tool._to_snake_case("MyAgent")
        assert result == "my_agent"

    def test_to_snake_case_camel(self, scaffold_tool):
        """测试camelCase转snake_case"""
        result = scaffold_tool._to_snake_case("myAgent")
        assert result == "my_agent"

    def test_to_snake_case_starts_with_number(self, scaffold_tool):
        """测试以数字开头的转换"""
        result = scaffold_tool._to_snake_case("123Agent")
        # "123Agent" -> "123_Agent" -> "agent_123_agent"
        assert result == "agent_123_agent"


# ==================== Agent创建测试 ====================

class TestAgentCreation:
    """Agent创建测试"""

    def test_create_simple_agent(self, scaffold_tool):
        """测试创建简单Agent"""
        files = scaffold_tool.create_agent(
            name="TestAgent",
            description="测试Agent",
            category="general",
            author="Test Author",
            with_tests=False,
        )

        # 验证文件创建
        assert "agent" in files
        assert files["agent"].exists()
        assert files["agent"].name == "test_agent.py"

        # 验证__init__.py创建
        assert "init" in files
        assert files["init"].exists()

    def test_create_agent_with_capabilities(self, scaffold_tool):
        """测试创建带能力的Agent"""
        capabilities = [
            {
                "name": "test_capability",
                "description": "测试能力",
                "input_types": ["输入"],
                "output_types": ["输出"],
                "estimated_time": 5.0,
            }
        ]

        files = scaffold_tool.create_agent(
            name="CapAgent",
            description="能力测试Agent",
            capabilities=capabilities,
            with_tests=False,
        )

        # 验证能力代码被包含
        content = files["agent"].read_text(encoding="utf-8")
        assert "test_capability" in content
        assert "测试能力" in content

    def test_create_agent_with_tests(self, scaffold_tool):
        """测试创建带测试的Agent"""
        files = scaffold_tool.create_agent(
            name="TestAgent",
            description="测试Agent",
            with_tests=True,
        )

        # 验证测试文件创建
        assert "test" in files
        assert files["test"].exists()
        assert "test_test_agent" in files["test"].name

    def test_create_agent_creates_readme(self, scaffold_tool):
        """测试创建README"""
        files = scaffold_tool.create_agent(
            name="ReadmeAgent",
            description="README测试Agent",
            with_tests=False,
        )

        # 验证README创建
        assert "readme" in files
        assert files["readme"].exists()
        assert files["readme"].name == "README.md"

        # 验证README内容
        content = files["readme"].read_text(encoding="utf-8")
        assert "# ReadmeAgent" in content
        assert "README测试Agent" in content

    def test_create_patent_agent(self, scaffold_tool):
        """测试创建专利类别Agent"""
        files = scaffold_tool.create_agent(
            name="PatentAnalyzer",
            description="专利分析Agent",
            category="patent",
            with_tests=False,
        )

        # 验证类别正确设置
        content = files["agent"].read_text(encoding="utf-8")
        assert '__category__ = "patent"' in content

    def test_create_example_agent(self, scaffold_tool):
        """测试创建示例Agent"""
        files = scaffold_tool.create_agent(
            name="ExampleAgent",
            description="示例Agent",
            category="example",
            with_tests=False,
        )

        # 验证文件在examples目录
        assert "examples" in str(files["agent"])


# ==================== 代码生成测试 ====================

class TestCodeGeneration:
    """代码生成测试"""

    def test_agent_code_contains_required_imports(self, scaffold_tool):
        """测试生成的代码包含必需的导入"""
        files = scaffold_tool.create_agent(
            name="ImportAgent",
            description="导入测试",
            with_tests=False,
        )

        content = files["agent"].read_text(encoding="utf-8")

        required_imports = [
            "BaseXiaonaComponent",
            "AgentCapability",
            "AgentExecutionContext",
            "AgentExecutionResult",
            "AgentStatus",
        ]

        for imp in required_imports:
            assert imp in content, f"缺少导入: {imp}"

    def test_agent_code_contains_required_methods(self, scaffold_tool):
        """测试生成的代码包含必需的方法"""
        files = scaffold_tool.create_agent(
            name="MethodAgent",
            description="方法测试",
            with_tests=False,
        )

        content = files["agent"].read_text(encoding="utf-8")

        required_methods = [
            "def _initialize(self)",
            "async def execute(self",
            "def get_system_prompt(self)",
        ]

        for method in required_methods:
            assert method in content, f"缺少方法: {method}"

    def test_agent_code_registers_capabilities(self, scaffold_tool):
        """测试生成的代码注册能力"""
        files = scaffold_tool.create_agent(
            name="CapAgent",
            description="能力注册测试",
            with_tests=False,
        )

        content = files["agent"].read_text(encoding="utf-8")
        assert "_register_capabilities" in content

    def test_test_code_is_valid(self, scaffold_tool):
        """测试生成的测试代码有效"""
        files = scaffold_tool.create_agent(
            name="ValidTestAgent",
            description="有效测试",
            with_tests=True,
        )

        test_content = files["test"].read_text(encoding="utf-8")

        # 检查测试类
        assert "class TestValidTestAgent" in test_content
        assert "def test_initialization" in test_content
        assert "def test_execute" in test_content


# ==================== Agent验证测试 ====================

class TestAgentValidation:
    """Agent验证测试"""

    def test_validate_valid_agent(self, scaffold_tool, temp_dir):
        """测试验证有效Agent"""
        # 创建一个符合标准的Agent
        agent_code = '''
"""Test Agent"""
from typing import Dict, Any
from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)

class TestValidAgent(BaseXiaonaComponent):
    def _initialize(self) -> None:
        self._register_capabilities([
            AgentCapability(
                name="test",
                description="测试",
                input_types=["输入"],
                output_types=["输出"],
                estimated_time=1.0,
            ),
        ])

    def get_system_prompt(self) -> str:
        return "测试提示词"

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        return AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.COMPLETED,
            output_data={"result": "ok"},
        )
'''

        agent_file = temp_dir / "test_valid_agent.py"
        agent_file.write_text(agent_code, encoding="utf-8")

        result = scaffold_tool.validate_agent(agent_file)
        assert result == True

    def test_validate_missing_import(self, scaffold_tool, temp_dir):
        """测试验证缺少导入的Agent"""
        agent_code = '''
"""Invalid Agent"""
class InvalidAgent:
    pass
'''

        agent_file = temp_dir / "invalid_agent.py"
        agent_file.write_text(agent_code, encoding="utf-8")

        result = scaffold_tool.validate_agent(agent_file)
        assert result == False

    def test_validate_nonexistent_file(self, scaffold_tool):
        """测试验证不存在的文件"""
        result = scaffold_tool.validate_agent(Path("/nonexistent/file.py"))
        assert result == False


# ==================== 模板测试 ====================

class TestTemplates:
    """模板测试"""

    def test_list_templates(self, scaffold_tool, capsys):
        """测试列出模板"""
        scaffold_tool.list_templates()

        captured = capsys.readouterr()
        output = captured.out

        # 验证模板被列出
        assert "simple" in output
        assert "llm" in output
        assert "patent" in output
        assert "tool" in output

    def test_template_simple_structure(self, scaffold_tool):
        """测试simple模板结构"""
        files = scaffold_tool.create_agent(
            name="TemplateTest",
            description="模板测试",
            category="example",
            with_tests=False,
        )

        content = files["agent"].read_text(encoding="utf-8")

        # 验证基本结构
        assert '"""' in content  # 文档字符串
        assert "class TemplateTest" in content
        assert "__version__" in content
        assert "__category__" in content


# ==================== 集成测试 ====================

@pytest.mark.integration
class TestIntegration:
    """集成测试"""

    def test_full_creation_workflow(self, scaffold_tool):
        """测试完整创建流程"""
        # 创建Agent
        files = scaffold_tool.create_agent(
            name="WorkflowAgent",
            description="工作流测试Agent",
            category="general",
            author="Integration Test",
            with_tests=True,
        )

        # 验证所有文件创建
        assert files["agent"].exists()
        assert files["init"].exists()
        assert files["test"].exists()
        assert files["readme"].exists()

        # 验证代码可以编译
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "workflow_agent",
            files["agent"]
        )
        assert spec is not None

    def test_multiple_agents_creation(self, scaffold_tool):
        """测试创建多个Agent"""
        agent_names = ["Agent1", "Agent2", "Agent3"]

        for name in agent_names:
            scaffold_tool.create_agent(
                name=name,
                description=f"{name} 描述",
                with_tests=False,
            )

        # 验证所有Agent创建成功
        for name in agent_names:
            agent_name = scaffold_tool._to_snake_case(name)
            agent_file = scaffold_tool.agents_dir / agent_name / f"{agent_name}.py"
            assert agent_file.exists()


# ==================== 边界测试 ====================

class TestEdgeCases:
    """边界情况测试"""

    def test_empty_name(self, scaffold_tool):
        """测试空名称"""
        result = scaffold_tool._to_pascal_case("")
        assert result == ""

    def test_special_characters(self, scaffold_tool):
        """测试特殊字符处理"""
        result = scaffold_tool._to_pascal_case("my-agent@123")
        assert "@" not in result

    def test_very_long_name(self, scaffold_tool):
        """测试非常长的名称"""
        long_name = "a" * 100
        result = scaffold_tool._to_snake_case(long_name)
        assert len(result) <= 1024  # 合理限制

    def test_chinese_name(self, scaffold_tool):
        """测试中文名称"""
        result = scaffold_tool._to_pascal_case("中文Agent")
        # 应该能处理而不崩溃
        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
