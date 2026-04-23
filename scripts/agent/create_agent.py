#!/usr/bin/env python3
"""
Agent脚手架工具
==============

快速创建符合Athena统一接口标准的Agent。

使用方法:
    python tools/agent_scaffold.py create              # 交互式创建
    python tools/agent_scaffold.py create --name MyAgent  # 指定名称
    python tools/agent_scaffold.py list               # 列出模板
    python tools/agent_scaffold.py validate <path>    # 验证Agent

作者: Athena平台团队
版本: 1.0.0
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ==================== 颜色输出 ====================

class Colors:
    """终端颜色代码"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def success(msg: str) -> str:
        return f"{Colors.OKGREEN}✓ {msg}{Colors.ENDC}"

    @staticmethod
    def error(msg: str) -> str:
        return f"{Colors.FAIL}✗ {msg}{Colors.ENDC}"

    @staticmethod
    def warning(msg: str) -> str:
        return f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}"

    @staticmethod
    def info(msg: str) -> str:
        return f"{Colors.OKCYAN}ℹ {msg}{Colors.ENDC}"

    @staticmethod
    def header(msg: str) -> str:
        return f"{Colors.HEADER}{msg}{Colors.ENDC}"


# ==================== Agent模板 ====================

AGENT_TEMPLATE_PY = '''"""
{agent_title} - {description}
{header_line}

{agent_description_long}

生成时间: {generation_time}
作者: {author}
版本: 1.0.0
类别: {category}

文档链接：
- 统一接口标准: docs/design/UNIFIED_AGENT_INTERFACE_STANDARD.md
- 开发指南: docs/guides/AGENT_INTERFACE_IMPLEMENTATION_GUIDE.md
"""

from typing import Any, Dict, List, Optional
import logging
import asyncio
from datetime import datetime

from core.framework.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)

logger = logging.getLogger(__name__)


class {AgentName}(BaseXiaonaComponent):
    """
    {description}

    {docstring_details}

    Attributes:
        config: 配置参数字典

    Examples:
        >>> agent = {AgentName}(agent_id="{agent_id}")
        >>> result = await agent.execute(context)
        >>> assert result.status == AgentStatus.COMPLETED
    """

    __version__ = "1.0.0"
    __category__ = "{category}"

    def _initialize(self) -> None:
        """初始化Agent"""
        # 注册能力
        self._register_capabilities([
{capabilities_code}
        ])

        # 初始化配置
        {init_config_code}

        # 初始化LLM（可选）
        # from core.ai.llm.unified_llm_manager import UnifiedLLMManager
        # self.llm = UnifiedLLMManager()

        # 初始化工具（可选）
        # from core.tools.unified_registry import get_unified_registry
        # self.tool_registry = get_unified_registry()

        # 初始化其他
        self.cache: Dict[str, Any] = {{}}
        self.stats: Dict[str, Any] = {{
            "total_tasks": 0,
            "success_tasks": 0,
            "error_tasks": 0,
        }}

        self.logger.info(
            f"{AgentName}初始化完成: {{self.agent_id}}, "
            f"能力数: {{len(self.get_capabilities())}}"
        )

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是{AgentName}，{role}。

核心能力：
{capabilities_list}

工作原则：
{principles_list}

输出格式：
{output_format}
"""

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """执行任务"""
        start_time = datetime.now()
        self.stats["total_tasks"] += 1

        try:
            # 验证输入
            if not self.validate_input(context):
                self.stats["error_tasks"] += 1
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.ERROR,
                    error_message="输入验证失败",
                    execution_time=(datetime.now() - start_time).total_seconds(),
                )

            # 获取输入
            {input_extraction_code}

            # 执行任务
            result = await self._do_work(context.input_data, context.config)

            # 返回结果
            execution_time = (datetime.now() - start_time).total_seconds()
            self.stats["success_tasks"] += 1

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=result,
                execution_time=execution_time,
                metadata={{
                    "start_time": start_time.isoformat(),
                }},
            )

        except Exception as e:
            self.stats["error_tasks"] += 1
            self.logger.exception(f"任务执行失败: {{context.task_id}}")
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                error_message=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    async def _do_work(
        self,
        input_data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """实际的工作逻辑"""
        # 实现你的具体逻辑
        result = {{
            "status": "success",
            "message": "任务完成",
        }}

        # 示例：调用LLM
        # if hasattr(self, 'llm'):
        #     response = await self.llm.generate(...)
        #     result["response"] = response

        # 示例：使用工具
        # if hasattr(self, 'tool_registry'):
        #     tool = self.tool_registry.get("tool_name")
        #     if tool:
        #         result = await tool.function(...)

        return result

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()


def create_{agent_lower}(agent_id: str) -> {AgentName}:
    """创建{AgentName}实例"""
    return {AgentName}(agent_id=agent_id)


async def main():
    """测试入口"""
    agent = {AgentName}(agent_id="{agent_id}")

    print("=== {AgentName}测试 ===")
    info = agent.get_info()
    print(f"Agent ID: {{info['agent_id']}}")
    print(f"类型: {{info['agent_type']}}")
    print(f"能力: {{[c['name'] for c in info['capabilities']}}")


if __name__ == "__main__":
    asyncio.run(main())
'''

# ==================== 测试模板 ====================

TEST_TEMPLATE_PY = '''"""
{test_title}测试套件
{header_line}

生成时间: {generation_time}
"""

import pytest
import asyncio
from datetime import datetime

from core.framework.agents.{agent_file}.{AgentName} import {AgentName}, create_{agent_lower}
from core.framework.agents.xiaona.base_component import (
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)


@pytest.fixture
def agent():
    """创建Agent实例"""
    return {AgentName}(agent_id="test_agent_001")


@pytest.fixture
def execution_context():
    """创建执行上下文"""
    return AgentExecutionContext(
        session_id="TEST_SESSION",
        task_id="TEST_TASK",
        input_data={{"test": "data"}},
        config={{}},
        metadata={{}},
    )


class Test{AgentName}:
    """{AgentName}测试类"""

    def test_initialization(self, agent):
        """测试初始化"""
        assert agent.agent_id == "test_agent_001"
        assert agent.status == AgentStatus.IDLE
        assert len(agent.get_capabilities()) > 0

    def test_get_info(self, agent):
        """测试获取信息"""
        info = agent.get_info()
        assert "agent_id" in info
        assert "agent_type" in info
        assert "capabilities" in info

    def test_get_system_prompt(self, agent):
        """测试获取系统提示词"""
        prompt = agent.get_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_validate_input(self, agent, execution_context):
        """测试输入验证"""
        # 正常输入
        assert agent.validate_input(execution_context) == True

        # 缺少session_id
        execution_context.session_id = ""
        assert agent.validate_input(execution_context) == False

    @pytest.mark.asyncio
    async def test_execute(self, agent, execution_context):
        """测试执行"""
        result = await agent.execute(execution_context)
        assert isinstance(result, AgentExecutionResult)
        assert result.agent_id == "test_agent_001"

    def test_has_capability(self, agent):
        """测试能力检查"""
        capabilities = agent.get_capabilities()
        if capabilities:
            first_capability = capabilities[0].name
            assert agent.has_capability(first_capability) == True

    def test_get_stats(self, agent):
        """测试统计信息"""
        stats = agent.get_stats()
        assert "total_tasks" in stats
        assert "success_tasks" in stats
        assert "error_tasks" in stats


@pytest.mark.integration
class Test{AgentName}Integration:
    """{AgentName}集成测试"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流"""
        # 创建Agent
        agent = create_{agent_lower}("integration_test_agent")

        # 创建上下文
        context = AgentExecutionContext(
            session_id="INTEGRATION_TEST",
            task_id="FULL_WORKFLOW_TEST",
            input_data={{"test": "integration"}},
            config={{}},
            metadata={{}},
        )

        # 执行
        result = await agent._execute_with_monitoring(context)

        # 验证
        assert result.agent_id == "integration_test_agent"
        assert isinstance(result.execution_time, float)
'''

# ==================== README模板 ====================

README_TEMPLATE_MD = '''# {Agent_name}

{description}

## 基本信息

- **版本**: 1.0.0
- **作者**: {author}
- **类别**: {category}
- **生成时间**: {generation_time}

## 能力

{capabilities_markdown}

## 快速开始

```python
from core.framework.agents.{agent_file} import create_{agent_lower}

# 创建Agent实例
agent = create_{agent_lower}("my_agent_001")

# 查看Agent信息
info = agent.get_info()
print(info)

# 执行任务
from core.framework.agents.xiaona.base_component import AgentExecutionContext

context = AgentExecutionContext(
    session_id="SESSION_001",
    task_id="TASK_001",
    input_data={{"your": "input"}},
    config={{}},
    metadata={{}},
)

result = await agent.execute(context)
print(result.output_data)
```

## 配置选项

{config_options}

## 测试

```bash
# 运行测试
pytest tests/agents/test_{agent_lower}.py -v

# 查看覆盖率
pytest tests/agents/test_{agent_lower}.py --cov=core.agents.{agent_file} --cov-report=html
```

## 文档

- [统一接口标准](../../../docs/design/UNIFIED_AGENT_INTERFACE_STANDARD.md)
- [开发指南](../../../docs/guides/AGENT_INTERFACE_IMPLEMENTATION_GUIDE.md)
- [最佳实践](../../../docs/guides/AGENT_INTERFACE_BEST_PRACTICES.md)

## 变更日志

### 1.0.0 ({generation_time})
- 初始版本
'''

# ==================== 脚手架工具类 ====================

class AgentScaffoldTool:
    """Agent脚手架工具"""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or PROJECT_ROOT
        self.agents_dir = self.project_root / "core" / "agents"
        self.tests_dir = self.project_root / "tests" / "agents"
        self.examples_dir = self.project_root / "examples" / "agents"

        # 确保目录存在
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        self.tests_dir.mkdir(parents=True, exist_ok=True)
        self.examples_dir.mkdir(parents=True, exist_ok=True)

    def create_agent(
        self,
        name: str,
        description: str,
        category: str = "general",
        author: str = "Athena Developer",
        capabilities: list[dict[str, Any] | None = None,
        role: str | None = None,
        with_tests: bool = True,
        with_example: bool = True,
    ) -> dict[str, Path]:
        """
        创建Agent

        Args:
            name: Agent名称（PascalCase）
            description: 描述
            category: 类别
            author: 作者
            capabilities: 能力列表
            role: 角色描述
            with_tests: 是否创建测试文件
            with_example: 是否创建示例文件

        Returns:
            创建的文件路径字典
        """
        print(Colors.header(f"\n创建Agent: {name}"))

        # 规范化输入
        agent_name = self._to_pascal_case(name)
        agent_lower = self._to_snake_case(name)
        agent_file = agent_lower

        # 默认能力
        if capabilities is None:
            capabilities = [
                {
                    "name": "process",
                    "description": "处理输入数据",
                    "input_types": ["文本输入"],
                    "output_types": ["处理结果"],
                    "estimated_time": 5.0,
                }
            ]

        # 默认角色
        if role is None:
            role = f"一个专业的{description}"

        # 生成代码
        agent_code = self._generate_agent_code(
            agent_name=agent_name,
            agent_lower=agent_lower,
            agent_file=agent_file,
            description=description,
            category=category,
            author=author,
            capabilities=capabilities,
            role=role,
        )

        # 确定输出目录
        if category == "example":
            output_dir = self.examples_dir
        else:
            output_dir = self.agents_dir

        # 创建目录
        agent_dir = output_dir / agent_file
        agent_dir.mkdir(exist_ok=True)

        # 写入Agent文件
        agent_path = agent_dir / f"{agent_file}.py"
        agent_path.write_text(agent_code, encoding="utf-8")
        print(Colors.success(f"创建Agent文件: {agent_path.relative_to(self.project_root)}"))

        # 创建__init__.py
        init_path = agent_dir / "__init__.py"
        init_code = f'''"""{agent_name}模块"""

from .{agent_file} import {agent_name}, create_{agent_lower}

__all__ = ["{agent_name}", "create_{agent_lower}"]
'''
        init_path.write_text(init_code, encoding="utf-8")
        print(Colors.success(f"创建__init__.py: {init_path.relative_to(self.project_root)}"))

        created_files = {"agent": agent_path, "init": init_path}

        # 创建测试文件
        if with_tests:
            test_code = self._generate_test_code(
                agent_name=agent_name,
                agent_lower=agent_lower,
                agent_file=agent_file,
            )
            test_path = self.tests_dir / f"test_{agent_lower}.py"
            test_path.write_text(test_code, encoding="utf-8")
            print(Colors.success(f"创建测试文件: {test_path.relative_to(self.project_root)}"))
            created_files["test"] = test_path

        # 创建README
        readme_code = self._generate_readme(
            agent_name=agent_name,
            agent_lower=agent_lower,
            agent_file=agent_file,
            description=description,
            category=category,
            author=author,
            capabilities=capabilities,
        )
        readme_path = agent_dir / "README.md"
        readme_path.write_text(readme_code, encoding="utf-8")
        print(Colors.success(f"创建README: {readme_path.relative_to(self.project_root)}"))
        created_files["readme"] = readme_path

        print(Colors.success(f"\nAgent '{agent_name}' 创建完成!"))
        print(Colors.info(f"位置: {agent_dir.relative_to(self.project_root)}"))
        print(Colors.info(f"测试: pytest {test_path.relative_to(self.project_root)} -v" if with_tests else ""))

        return created_files

    def _generate_agent_code(
        self,
        agent_name: str,
        agent_lower: str,
        agent_file: str,
        description: str,
        category: str,
        author: str,
        capabilities: list[dict[str, Any],
        role: str,
    ) -> str:
        """生成Agent代码"""

        # 生成能力代码
        capabilities_code = "            AgentCapability(\n"
        capabilities_code += f'                name="{capabilities[0]["name"]}",\n'
        capabilities_code += f'                description="{capabilities[0]["description"]}",\n'
        capabilities_code += f'                input_types={capabilities[0]["input_types"]},\n'
        capabilities_code += f'                output_types={capabilities[0]["output_types"]},\n'
        capabilities_code += f'                estimated_time={capabilities[0]["estimated_time"]},\n'
        capabilities_code += "            ),"

        # 生成初始化配置代码
        init_config_code = "# 可从config获取配置\n        # self.max_retries = self.config.get('max_retries', 3)"

        # 生成能力列表
        capabilities_list = "\n".join([f"- {cap['name']}: {cap['description']}" for cap in capabilities])

        # 生成原则列表
        principles_list = "- 准确理解用户需求\n- 返回结构化结果\n- 处理异常情况"

        # 生成输出格式
        output_format = "JSON格式的结构化数据"

        # 生成输入提取代码
        input_extraction_code = "# user_input = context.input_data.get('input', '')"

        # 生成标题行
        header_line = "=" * (len(agent_name) + len(description) + 3)

        return AGENT_TEMPLATE_PY.format(
            agent_title=agent_name,
            header_line=header_line,
            agent_name=agent_name,
            agent_lower=agent_lower,
            agent_file=agent_file,
            description=description,
            agent_description_long=f"{description}。\n\n这个Agent遵循Athena平台的统一接口标准。",
            docstring_details=f"适用于: {category}领域",
            agent_id=f"{agent_lower}_001",
            generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            author=author,
            category=category,
            AgentName=agent_name,
            capabilities_code=capabilities_code,
            init_config_code=init_config_code,
            capabilities_list=capabilities_list,
            principles_list=principles_list,
            output_format=output_format,
            role=role,
            input_extraction_code=input_extraction_code,
        )

    def _generate_test_code(
        self,
        agent_name: str,
        agent_lower: str,
        agent_file: str,
    ) -> str:
        """生成测试代码"""
        header_line = "=" * (len(agent_name) + 4)
        return TEST_TEMPLATE_PY.format(
            test_title=agent_name,
            header_line=header_line,
            agent_name=agent_name,
            agent_lower=agent_lower,
            agent_file=agent_file,
            generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            AgentName=agent_name,
        )

    def _generate_readme(
        self,
        agent_name: str,
        agent_lower: str,
        agent_file: str,
        description: str,
        category: str,
        author: str,
        capabilities: list[dict[str, Any],
    ) -> str:
        """生成README"""
        capabilities_markdown = "\n".join([
            f"- **{cap['name']}**: {cap['description']}"
            for cap in capabilities
        ])

        config_options = """
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| max_retries | int | 3 | 最大重试次数 |
| timeout | float | 30.0 | 超时时间（秒） |
"""

        return README_TEMPLATE_MD.format(
            Agent_name=agent_name,
            description=description,
            generation_time=datetime.now().strftime("%Y-%m-%d"),
            author=author,
            category=category,
            agent_lower=agent_lower,
            agent_file=agent_file,
            capabilities_markdown=capabilities_markdown,
            config_options=config_options,
        )

    def _to_pascal_case(self, name: str) -> str:
        """转换为PascalCase"""
        # 移除特殊字符
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)

        # 处理snake_case
        if '_' in name:
            parts = name.split('_')
            return ''.join(p.capitalize() for p in parts if p)

        # 处理camelCase - 在大写字母前加下划线，然后分割
        # 例如: myAgent -> my_Agent -> My Agent
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        parts = s2.split('_')
        return ''.join(p.capitalize() for p in parts if p)

    def _to_snake_case(self, name: str) -> str:
        """转换为snake_case"""
        # 移除特殊字符
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)

        # 处理PascalCase/camelCase - 在大写字母前加下划线
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)

        # 转换为小写
        name = s2.lower()

        # 移除多余的下划线
        name = re.sub(r'_+', '_', name)
        name = name.strip('_')

        # 确保不以数字开头
        if name and name[0].isdigit():
            name = f"agent_{name}"

        return name if name else "agent"

    def list_templates(self) -> None:
        """列出可用的Agent类型模板"""
        print(Colors.header("\n可用的Agent类型模板:"))
        templates = {
            "simple": {
                "name": "简单Agent",
                "description": "最简单的Agent，不依赖外部服务",
                "capabilities": [
                    {"name": "echo", "description": "回显输入", "input_types": ["文本"], "output_types": ["文本"], "estimated_time": 1.0}
                ],
            },
            "llm": {
                "name": "LLM Agent",
                "description": "使用LLM的Agent，需要配置LLM密钥",
                "capabilities": [
                    {"name": "chat", "description": "对话能力", "input_types": ["用户消息"], "output_types": ["AI回复"], "estimated_time": 5.0}
                ],
            },
            "patent": {
                "name": "专利Agent",
                "description": "专利分析Agent，继承专利相关能力",
                "capabilities": [
                    {"name": "analyze", "description": "分析专利", "input_types": ["专利号"], "output_types": ["分析报告"], "estimated_time": 15.0},
                    {"name": "search", "description": "检索专利", "input_types": ["关键词"], "output_types": ["专利列表"], "estimated_time": 10.0},
                ],
            },
            "tool": {
                "name": "工具Agent",
                "description": "使用工具系统的Agent",
                "capabilities": [
                    {"name": "web_search", "description": "网络搜索", "input_types": ["查询词"], "output_types": ["搜索结果"], "estimated_time": 8.0},
                ],
            },
        }

        for key, template in templates.items():
            print(f"\n  {Colors.OKBLUE}{key}{Colors.ENDC} - {Colors.BOLD}{template['name']}{Colors.ENDC}")
            print(f"    {template['description']}")
            print(f"    能力: {', '.join([c['name'] for c in template['capabilities'])}")

    def validate_agent(self, path: Path) -> bool:
        """
        验证Agent是否符合接口标准

        Args:
            path: Agent文件路径

        Returns:
            是否通过验证
        """
        print(Colors.header(f"\n验证Agent: {path}"))

        issues = []

        # 检查文件存在
        if not path.exists():
            print(Colors.error(f"文件不存在: {path}"))
            return False

        # 读取文件内容
        content = path.read_text(encoding="utf-8")

        # 检查必要的导入
        required_imports = [
            "BaseXiaonaComponent",
            "AgentCapability",
            "AgentExecutionContext",
            "AgentExecutionResult",
            "AgentStatus",
        ]

        for imp in required_imports:
            if imp not in content:
                issues.append(f"缺少导入: {imp}")

        # 检查必要的类方法
        required_methods = [
            "def _initialize(self)",
            "async def execute(self",
            "def get_system_prompt(self)",
        ]

        for method in required_methods:
            if method not in content:
                issues.append(f"缺少方法: {method}")

        # 检查能力注册
        if "_register_capabilities" not in content:
            issues.append("未注册能力（缺少 _register_capabilities 调用）")

        # 检查错误处理
        if "AgentExecutionResult" not in content:
            issues.append("未返回 AgentExecutionResult")

        # 输出结果
        if not issues:
            print(Colors.success("验证通过！Agent符合统一接口标准"))
            return True
        else:
            print(Colors.error("验证失败，发现以下问题:"))
            for issue in issues:
                print(f"  - {issue}")
            return False


# ==================== 交互式创建 ====================

def interactive_create(tool: AgentScaffoldTool) -> None:
    """交互式创建Agent"""
    print(Colors.header("""
    ╔══════════════════════════════════════════════════════════╗
    ║           Athena Agent 脚手架工具                        ║
    ║           快速创建符合标准的Agent                         ║
    ╚══════════════════════════════════════════════════════════╝
    """))

    # Agent名称
    while True:
        name = input(Colors.info("请输入Agent名称（如: MyAgent）: ")).strip()
        if name:
            break
        print(Colors.warning("名称不能为空"))

    # 描述
    description = input(Colors.info("请输入Agent描述（如: 数据处理Agent）: ")).strip() or f"{name} Agent"

    # 类别
    print(Colors.info("\n请选择类别:"))
    print("  1. general - 通用Agent")
    print("  2. patent - 专利相关")
    print("  3. legal - 法律相关")
    print("  4. example - 示例Agent")

    category_map = {"1": "general", "2": "patent", "3": "legal", "4": "example"}
    category_choice = input(Colors.info("选择 [1-4]，默认[1]: ")).strip() or "1"
    category = category_map.get(category_choice, "general")

    # 作者
    author = input(Colors.info("\n请输入作者名称（默认: Athena Developer）: ")).strip() or "Athena Developer"

    # 能力
    print(Colors.info("\n是否添加能力？(y/n，默认: n)"))
    if input().strip().lower() == 'y':
        capabilities = []
        while True:
            cap_name = input(Colors.info("  能力名称（如: analyze）: ")).strip()
            if not cap_name:
                break
            cap_desc = input(Colors.info("  能力描述: ")).strip() or cap_name
            capabilities.append({
                "name": cap_name,
                "description": cap_desc,
                "input_types": ["输入数据"],
                "output_types": ["输出结果"],
                "estimated_time": 5.0,
            })
            print(Colors.info("继续添加能力？(y/n)"))
            if input().strip().lower() != 'y':
                break
    else:
        capabilities = None

    # 确认
    print(Colors.header("\n即将创建:"))
    print(f"  名称: {tool._to_pascal_case(name)}")
    print(f"  描述: {description}")
    print(f"  类别: {category}")
    print(f"  作者: {author}")

    if input(Colors.info("\n确认创建？(y/n): ")).strip().lower() == 'y':
        tool.create_agent(
            name=name,
            description=description,
            category=category,
            author=author,
            capabilities=capabilities,
        )
    else:
        print(Colors.warning("已取消"))


# ==================== 主函数 ====================

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Athena Agent脚手架工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 交互式创建
  python tools/agent_scaffold.py create

  # 快速创建
  python tools/agent_scaffold.py create --name MyAgent --desc "我的Agent"

  # 使用模板
  python tools/agent_scaffold.py create --template patent --name PatentAnalyzer

  # 列出模板
  python tools/agent_scaffold.py list

  # 验证Agent
  python tools/agent_scaffold.py validate core/agents/my_agent/my_agent.py
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # create命令
    create_parser = subparsers.add_parser("create", help="创建新Agent")
    create_parser.add_argument("--name", "-n", help="Agent名称")
    create_parser.add_argument("--desc", "-d", help="Agent描述")
    create_parser.add_argument("--category", "-c", default="general",
                               choices=["general", "patent", "legal", "example"],
                               help="Agent类别")
    create_parser.add_argument("--author", "-a", default="Athena Developer", help="作者")
    create_parser.add_argument("--template", "-t",
                               choices=["simple", "llm", "patent", "tool"],
                               help="使用模板")
    create_parser.add_argument("--no-tests", action="store_true", help="不创建测试文件")
    create_parser.add_argument("--interactive", "-i", action="store_true", help="交互式模式")

    # list命令
    subparsers.add_parser("list", help="列出可用模板")

    # validate命令
    validate_parser = subparsers.add_parser("validate", help="验证Agent")
    validate_parser.add_argument("path", help="Agent文件路径")

    args = parser.parse_args()

    # 创建工具实例
    tool = AgentScaffoldTool()

    # 执行命令
    if args.command == "create":
        if args.interactive or not args.name:
            interactive_create(tool)
        else:
            # 使用模板
            if args.template:
                templates = {
                    "simple": {
                        "description": "简单Agent",
                        "category": "example",
                        "capabilities": [
                            {"name": "echo", "description": "回显输入", "input_types": ["文本"], "output_types": ["文本"], "estimated_time": 1.0}
                        ],
                    },
                    "llm": {
                        "description": "LLM对话Agent",
                        "category": "general",
                        "capabilities": [
                            {"name": "chat", "description": "对话能力", "input_types": ["用户消息"], "output_types": ["AI回复"], "estimated_time": 5.0}
                        ],
                    },
                    "patent": {
                        "description": "专利分析Agent",
                        "category": "patent",
                        "capabilities": [
                            {"name": "analyze", "description": "分析专利", "input_types": ["专利号"], "output_types": ["分析报告"], "estimated_time": 15.0},
                            {"name": "search", "description": "检索专利", "input_types": ["关键词"], "output_types": ["专利列表"], "estimated_time": 10.0},
                        ],
                    },
                    "tool": {
                        "description": "工具使用Agent",
                        "category": "general",
                        "capabilities": [
                            {"name": "web_search", "description": "网络搜索", "input_types": ["查询词"], "output_types": ["搜索结果"], "estimated_time": 8.0},
                        ],
                    },
                }
                template = templates.get(args.template, templates["simple"])
                description = args.desc or template["description"]
                capabilities = template["capabilities"]
                category = template["category"]
            else:
                description = args.desc or f"{args.name} Agent"
                capabilities = None
                category = args.category

            tool.create_agent(
                name=args.name,
                description=description,
                category=category,
                author=args.author,
                capabilities=capabilities,
                with_tests=not args.no_tests,
            )

    elif args.command == "list":
        tool.list_templates()

    elif args.command == "validate":
        tool.validate_agent(Path(args.path))

    else:
        # 默认交互式创建
        interactive_create(tool)


if __name__ == "__main__":
    main()
