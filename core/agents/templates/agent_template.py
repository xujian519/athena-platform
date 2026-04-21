"""
{{AGENT_NAME}} - Agent模板
====================

这是一个符合Athena平台统一接口标准的Agent模板。
包含完整的结构、注释和示例代码。

生成时间: {{GENERATION_TIME}}
作者: {{AUTHOR}}

快速开始：
1. 复制此文件到 core/agents/ 目录
2. 替换 {{AGENT_NAME}} 等占位符
3. 实现 _initialize、execute、get_system_prompt 方法
4. 编写测试用例
5. 运行测试验证

文档链接：
- 统一接口标准: docs/design/UNIFIED_AGENT_INTERFACE_STANDARD.md
- 开发指南: docs/guides/AGENT_INTERFACE_IMPLEMENTATION_GUIDE.md
- 最佳实践: docs/guides/AGENT_INTERFACE_BEST_PRACTICES.md
"""

from typing import Any, Dict, List, Optional
import logging
import asyncio
from datetime import datetime

# 导入统一接口基础类
from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)

logger = logging.getLogger(__name__)


class {{AGENT_NAME}}(BaseXiaonaComponent):
    """
    {{AGENT_DESCRIPTION}}

    这是你的Agent类描述。应该清晰说明：
    - Agent的主要功能
    - 适用场景
    - 输入输出要求

    Attributes:
        config: 配置参数字典，包含Agent的运行配置

    Examples:
        >>> # 创建Agent实例
        >>> agent = {{AGENT_NAME}}(agent_id="{{AGENT_ID}}")
        >>> # 查看Agent信息
        >>> info = agent.get_info()
        >>> print(info["agent_type"])
        {{AGENT_NAME}}
        >>> # 执行任务
        >>> context = AgentExecutionContext(...)
        >>> result = await agent.execute(context)
        >>> assert result.status == AgentStatus.COMPLETED
    """

    # ==================== 类元数据 ====================
    # 版本号 - 遵循语义化版本规范 (MAJOR.MINOR.PATCH)
    __version__ = "1.0.0"

    # Agent类别 - 用于Agent注册和发现
    __category__ = "{{AGENT_CATEGORY}}"  # 如: patent, legal, general

    # ==================== 初始化方法 ====================

    def _initialize(self) -> None:
        """
        Agent初始化钩子（必须实现）

        在此方法中完成所有初始化工作：

        1. 注册能力（必须）
           - 使用 self._register_capabilities() 注册Agent的能力
           - 每个能力应该有清晰的名称和描述

        2. 初始化LLM客户端（可选）
           - 如果需要调用LLM，初始化UnifiedLLMManager
           - 示例：self.llm = UnifiedLLMManager()

        3. 加载提示词（可选）
           - 如果使用动态提示词，在此加载
           - 示例：self.prompt = self._load_prompt()

        4. 初始化工具（可选）
           - 如果需要使用工具，获取工具注册表
           - 示例：self.tool_registry = get_unified_registry()

        5. 初始化其他依赖（可选）
           - 缓存、统计、配置等
           - 示例：self.cache = {}
        """
        # ------------------------------------------------
        # 步骤1: 注册Agent能力（必须）
        # ------------------------------------------------
        self._register_capabilities([
            AgentCapability(
                name="{{CAPABILITY_1_NAME}}",
                description="{{CAPABILITY_1_DESCRIPTION}}",
                input_types=[{{CAPABILITY_1_INPUT_TYPES}}],
                output_types=[{{CAPABILITY_1_OUTPUT_TYPES}}],
                estimated_time={{CAPABILITY_1_TIME}},
            ),
            # 可以添加更多能力...
            # AgentCapability(
            #     name="another_capability",
            #     description="另一个能力描述",
            #     input_types=["输入类型1", "输入类型2"],
            #     output_types=["输出类型1"],
            #     estimated_time=10.0,
            # ),
        ])

        # ------------------------------------------------
        # 步骤2: 初始化LLM客户端（可选）
        # ------------------------------------------------
        # 取消下面的注释来启用LLM功能
        # from core.llm.unified_llm_manager import UnifiedLLMManager
        # self.llm = UnifiedLLMManager()
        # self.model = self.config.get("model", "gpt-4")
        # self.temperature = self.config.get("temperature", 0.7)
        # self.max_tokens = self.config.get("max_tokens", 2000)

        # ------------------------------------------------
        # 步骤3: 加载提示词（可选）
        # ------------------------------------------------
        # 如果提示词存储在文件中，可以在此加载
        # from pathlib import Path
        # prompt_path = Path(__file__).parent / "prompts" / "{{AGENT_LOWER}}_prompts.py"
        # if prompt_path.exists():
        #     # 动态加载提示词模块
        #     import importlib.util
        #     spec = importlib.util.spec_from_file_location("prompts", prompt_path)
        #     prompts = importlib.util.module_from_spec(spec)
        #     spec.loader.exec_module(prompts)
        #     self.system_prompt_template = prompts.get_system_prompt()

        # ------------------------------------------------
        # 步骤4: 初始化工具（可选）
        # ------------------------------------------------
        # 取消下面的注释来使用工具
        # from core.tools.unified_registry import get_unified_registry
        # self.tool_registry = get_unified_registry()

        # ------------------------------------------------
        # 步骤5: 初始化其他依赖
        # ------------------------------------------------
        self.max_retries = self.config.get("max_retries", 3)
        self.timeout = self.config.get("timeout", 30.0)
        self.cache: Dict[str, Any] = {}
        self.stats: Dict[str, Any] = {
            "total_tasks": 0,
            "success_tasks": 0,
            "error_tasks": 0,
        }

        # 记录初始化完成
        self.logger.info(
            f"{{AGENT_NAME}}初始化完成: {self.agent_id}, "
            f"能力数: {len(self.get_capabilities())}, "
            f"版本: {self.__version__}"
        )

    # ==================== 核心接口方法 ====================

    def get_system_prompt(self) -> str:
        """
        获取系统提示词（必须实现）

        返回Agent的系统提示词，用于：
        - LLM调用时的系统提示
        - Agent能力描述
        - 文档生成

        Returns:
            系统提示词字符串

        Examples:
            >>> prompt = agent.get_system_prompt()
            >>> assert isinstance(prompt, str)
            >>> assert len(prompt) > 0
        """
        return """你是{{AGENT_NAME}}，{{AGENT_ROLE}}。

核心能力：
{{CAPABILITIES_LIST}}

工作原则：
{{PRINCIPLES_LIST}}

输出格式：
{{OUTPUT_FORMAT}}

注意：
{{IMPORTANT_NOTES}}
"""

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """
        执行Agent任务（必须实现）

        这是Agent的核心方法，负责处理请求并返回结果。

        Args:
            context: 执行上下文，包含：
                - session_id: 会话ID
                - task_id: 任务ID
                - input_data: 输入数据字典
                - config: 配置参数
                - metadata: 元数据

        Returns:
            AgentExecutionResult: 执行结果，包含：
                - agent_id: Agent ID
                - status: 执行状态 (COMPLETED/ERROR)
                - output_data: 输出数据字典
                - error_message: 错误信息（如果有）
                - execution_time: 执行时间（秒）
                - metadata: 元数据

        Examples:
            >>> context = AgentExecutionContext(
            ...     session_id="SESSION_001",
            ...     task_id="TASK_001",
            ...     input_data={"query": "测试查询"},
            ...     config={},
            ...     metadata={}
            ... )
            >>> result = await agent.execute(context)
            >>> assert result.status == AgentStatus.COMPLETED
        """
        start_time = datetime.now()
        self.stats["total_tasks"] += 1

        try:
            # ------------------------------------------------
            # 步骤1: 验证输入
            # ------------------------------------------------
            if not self.validate_input(context):
                self.stats["error_tasks"] += 1
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.ERROR,
                    error_message="输入验证失败",
                    execution_time=(datetime.now() - start_time).total_seconds(),
                )

            # ------------------------------------------------
            # 步骤2: 提取输入参数
            # ------------------------------------------------
            {{INPUT_EXTRACTION_CODE}}

            # ------------------------------------------------
            # 步骤3: 执行任务
            # ------------------------------------------------
            # 根据任务类型调用不同的处理方法
            task_type = context.input_data.get("task_type", "{{DEFAULT_TASK_TYPE}}")

            if task_type == "{{TASK_TYPE_1}}":
                result = await self._handle_{{TASK_TYPE_1}}(context)
            elif task_type == "{{TASK_TYPE_2}}":
                result = await self._handle_{{TASK_TYPE_2}}(context)
            else:
                raise ValueError(f"未知的任务类型: {task_type}")

            # ------------------------------------------------
            # 步骤4: 返回成功结果
            # ------------------------------------------------
            execution_time = (datetime.now() - start_time).total_seconds()
            self.stats["success_tasks"] += 1

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=result,
                execution_time=execution_time,
                metadata={
                    "task_type": task_type,
                    "start_time": start_time.isoformat(),
                    "end_time": datetime.now().isoformat(),
                    {{METADATA_FIELDS}}
                },
            )

        except ValueError as e:
            # 业务逻辑错误 - 输入参数不符合预期
            self.stats["error_tasks"] += 1
            self.logger.error(f"输入验证失败: {e}, task_id: {context.task_id}")
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                error_message=f"输入验证失败: {str(e)}",
                execution_time=(datetime.now() - start_time).total_seconds(),
                metadata={"error_type": "ValueError"},
            )

        except TimeoutError as e:
            # 超时错误
            self.stats["error_tasks"] += 1
            self.logger.error(f"任务超时: {e}, task_id: {context.task_id}")
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                error_message=f"任务超时: {str(e)}",
                execution_time=(datetime.now() - start_time).total_seconds(),
                metadata={"error_type": "TimeoutError"},
            )

        except Exception as e:
            # 未预期的错误
            self.stats["error_tasks"] += 1
            self.logger.exception(f"任务执行失败: {context.task_id}")
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                error_message=f"执行失败: {str(e)}",
                execution_time=(datetime.now() - start_time).total_seconds(),
                metadata={"error_type": type(e).__name__},
            )

    # ==================== 输入验证 ====================

    def validate_input(self, context: AgentExecutionContext) -> bool:
        """
        验证输入数据

        在执行任务前验证输入数据的完整性和有效性。
        建议覆盖此方法以添加业务特定的验证逻辑。

        Args:
            context: 执行上下文

        Returns:
            bool: 验证是否通过

        Examples:
            >>> context = AgentExecutionContext(...)
            >>> assert agent.validate_input(context) == True
        """
        # 基础验证 - 由父类提供
        if not super().validate_input(context):
            return False

        # ------------------------------------------------
        # 业务验证 - 根据需要添加
        # ------------------------------------------------
        {{BUSINESS_VALIDATION_CODE}}

        # 示例：验证必需字段
        # required_fields = ["query", "options"]
        # for field in required_fields:
        #     if field not in context.input_data:
        #         self.logger.error(f"缺少必需字段: {field}")
        #         return False

        return True

    # ==================== 任务处理方法 ====================

    async def _handle_{{TASK_TYPE_1}}(
        self,
        context: AgentExecutionContext
    ) -> Dict[str, Any]:
        """
        处理{{TASK_TYPE_1}}类型的任务

        Args:
            context: 执行上下文

        Returns:
            处理结果字典

        Raises:
            ValueError: 输入参数无效
            TimeoutError: 处理超时
        """
        self.logger.info(f"处理{{TASK_TYPE_1}}任务: {context.task_id}")

        # 获取参数
        {{PARAM_EXTRACTION_CODE}}

        # 处理逻辑
        result = await self._do_{{TASK_TYPE_1}}_work(params, context.config)

        return result

    async def _handle_{{TASK_TYPE_2}}(
        self,
        context: AgentExecutionContext
    ) -> Dict[str, Any]:
        """
        处理{{TASK_TYPE_2}}类型的任务

        Args:
            context: 执行上下文

        Returns:
            处理结果字典
        """
        self.logger.info(f"处理{{TASK_TYPE_2}}任务: {context.task_id}")

        # 获取参数
        {{PARAM_EXTRACTION_CODE}}

        # 处理逻辑
        result = await self._do_{{TASK_TYPE_2}}_work(params, context.config)

        return result

    # ==================== 辅助方法 ====================

    async def _do_{{TASK_TYPE_1}}_work(
        self,
        params: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行{{TASK_TYPE_1}}的实际工作逻辑

        Args:
            params: 参数字典
            config: 配置字典

        Returns:
            结果字典
        """
        # 实现你的具体逻辑
        result = {
            "status": "success",
            "data": {{DEFAULT_RESULT}},
        }

        # 示例：调用LLM
        # if hasattr(self, 'llm') and self.llm:
        #     response = await self.llm.generate(
        #         prompt=params.get("query", ""),
        #         system_prompt=self.get_system_prompt(),
        #         model=self.model,
        #         temperature=self.temperature,
        #         max_tokens=self.max_tokens,
        #     )
        #     result["response"] = response

        # 示例：使用工具
        # if hasattr(self, 'tool_registry') and self.tool_registry:
        #     tool = self.tool_registry.get("tool_name")
        #     if tool:
        #         tool_result = await tool.function(**params)
        #         result["tool_output"] = tool_result

        # 示例：缓存
        # cache_key = f"{params.get('query')}"
        # if cache_key in self.cache:
        #     return self.cache[cache_key]
        # # 处理...
        # self.cache[cache_key] = result

        return result

    async def _do_{{TASK_TYPE_2}}_work(
        self,
        params: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行{{TASK_TYPE_2}}的实际工作逻辑

        Args:
            params: 参数字典
            config: 配置字典

        Returns:
            结果字典
        """
        # 实现你的具体逻辑
        return {
            "status": "success",
            "data": {{DEFAULT_RESULT}},
        }

    # ==================== 工具方法 ====================

    def get_stats(self) -> Dict[str, Any]:
        """
        获取Agent统计信息

        Returns:
            统计信息字典
        """
        return self.stats.copy()

    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = {
            "total_tasks": 0,
            "success_tasks": 0,
            "error_tasks": 0,
        }

    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache.clear()


# ==================== 便捷工厂函数 ====================

def create_{{AGENT_LOWER}}(
    agent_id: str,
    config: Optional[Dict[str, Any]] = None
) -> {{AGENT_NAME}}:
    """
    创建{{AGENT_NAME}}实例的便捷函数

    Args:
        agent_id: Agent唯一标识
        config: 可选配置参数

    Returns:
        {{AGENT_NAME}}实例

    Examples:
        >>> agent = create_{{AGENT_LOWER}}("my_agent_001")
        >>> info = agent.get_info()
        >>> print(info["agent_type"])
        {{AGENT_NAME}}
    """
    return {{AGENT_NAME}}(agent_id=agent_id, config=config)


# ==================== 测试入口 ====================

async def main():
    """
    测试入口函数

    用于快速测试Agent的基本功能。
    在生产环境中应该使用完整的测试套件。
    """
    import asyncio

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建Agent
    agent = {{AGENT_NAME}}(
        agent_id="{{AGENT_ID}}",
        config={
            "max_retries": 3,
            "timeout": 30.0,
        }
    )

    # 打印信息
    print("=" * 50)
    print("{{AGENT_NAME}} 测试")
    print("=" * 50)
    info = agent.get_info()
    print(f"Agent ID: {info['agent_id']}")
    print(f"类型: {info['agent_type']}")
    print(f"状态: {info['status']}")
    print(f"能力: {[c['name'] for c in info['capabilities']]}")
    print(f"版本: {agent.__version__}")

    # 测试执行
    print("\n" + "=" * 50)
    print("测试执行")
    print("=" * 50)

    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={
            {{TEST_INPUT_DATA}}
        },
        config={
            {{TEST_CONFIG_DATA}}
        },
        metadata={
            "test": True,
        },
    )

    result = await agent._execute_with_monitoring(context)

    print(f"\n执行结果:")
    print(f"状态: {result.status.value}")
    if result.status == AgentStatus.COMPLETED:
        print(f"输出: {result.output_data}")
        print(f"耗时: {result.execution_time:.2f}秒")
        print(f"元数据: {result.metadata}")
    else:
        print(f"错误: {result.error_message}")

    # 打印统计
    print("\n" + "=" * 50)
    print("统计信息")
    print("=" * 50)
    stats = agent.get_stats()
    print(f"总任务: {stats['total_tasks']}")
    print(f"成功: {stats['success_tasks']}")
    print(f"失败: {stats['error_tasks']}")


if __name__ == "__main__":
    asyncio.run(main())
