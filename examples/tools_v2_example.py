#!/usr/bin/env python3
"""
Athena平台工具系统v2.0示例工具
展示如何使用新的BaseTool接口创建工具

示例工具：
1. SimplePatentSearchTool - 简单的专利搜索工具
2. FileReadTool - 文件读取工具
3. WebSearchTool - 网络搜索工具

Author: Athena平台团队
Date: 2026-04-20
"""

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

from core.tools.tool_interface_v2 import (
    BaseTool,
    ToolContext,
    ToolMetadata,
    ToolResult,
    PermissionMode,
    InterruptBehavior,
)


# ============================================
# 示例1: 简单的专利搜索工具
# ============================================

class PatentSearchInput(BaseModel):
    """专利搜索输入模式"""
    query: str = Field(..., description="搜索查询关键词")
    limit: int = Field(default=10, ge=1, le=100, description="返回结果数量")
    source: str = Field(default="cnipa", description="数据源（cnipa/uspto/epo）")


class PatentSearchOutput(BaseModel):
    """专利搜索输出模式"""
    results: List[Dict[str, Any]] = Field(description="搜索结果列表")
    count: int = Field(description="结果数量")
    query: str = Field(description="原始查询")
    source: str = Field(description="使用的数据源")
    execution_time: float = Field(description="执行时间（秒）")


class SimplePatentSearchTool(BaseTool[PatentSearchInput, PatentSearchOutput, Dict[str, float]]):
    """
    简单的专利搜索工具示例

    演示如何：
    1. 定义输入/输出模式
    2. 实现call方法
    3. 配置ToolMetadata
    4. 使用进度回调
    5. 返回ToolResult
    """

    def __init__(self):
        metadata = ToolMetadata(
            name="simple_patent_search",
            description="简单的专利搜索工具（示例）",
            category="patent_search",
            priority="high",
            input_schema=PatentSearchInput,
            output_schema=PatentSearchOutput,
            is_read_only=True,
            is_concurrency_safe=True,
            timeout=30.0,
            search_hint="搜索专利文献"
        )
        super().__init__(metadata)

    async def call(
        self,
        args: PatentSearchInput,
        context: ToolContext,
        can_use_tool: Callable[[str], bool],
        on_progress: Optional[Callable[[Dict[str, float]], None]] = None,
    ) -> ToolResult[PatentSearchOutput]:
        """执行专利搜索"""
        start_time = time.time()

        try:
            self._logger.info(f"开始搜索专利: {args.query}（来源: {args.source}）")

            # 阶段1: 初始化搜索
            if on_progress:
                await on_progress({"stage": "初始化", "progress": 0.1})

            await asyncio.sleep(0.1)  # 模拟初始化

            # 阶段2: 执行搜索
            if on_progress:
                await on_progress({"stage": "搜索中", "progress": 0.3})

            results = await self._simulate_search(args.query, args.limit)

            # 阶段3: 处理结果
            if on_progress:
                await on_progress({"stage": "处理结果", "progress": 0.8})

            await asyncio.sleep(0.1)  # 模拟处理

            # 完成
            if on_progress:
                await on_progress({"stage": "完成", "progress": 1.0})

            execution_time = time.time() - start_time

            output = PatentSearchOutput(
                results=results,
                count=len(results),
                query=args.query,
                source=args.source,
                execution_time=execution_time
            )

            self._logger.info(f"搜索完成: 找到 {len(results)} 个专利")

            return ToolResult(
                success=True,
                output=output,
                execution_time=execution_time,
                metadata={
                    "source": args.source,
                    "agent_id": context.agent_id
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self._logger.error(f"搜索失败: {e}")

            return ToolResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )

    async def _simulate_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """模拟搜索（实际应用中应连接真实API）"""
        # 模拟搜索结果
        results = []
        for i in range(min(limit, 5)):
            results.append({
                "patent_id": f"CN{123456789 + i}A",
                "title": f"关于{query}的专利方法 {i+1}",
                "abstract": f"这是一个涉及{query}的专利实施例...",
                "applicant": "示例科技公司",
                "publication_date": "2024-01-01"
            })
        return results

    async def description(self, input: PatentSearchInput, context: ToolContext) -> str:
        """生成工具描述"""
        return f"搜索专利数据库，查询：{input.query}，返回{input.limit}个结果"


# ============================================
# 示例2: 文件读取工具
# ============================================

class FileReadInput(BaseModel):
    """文件读取输入模式"""
    path: str = Field(..., description="文件路径")
    offset: int = Field(default=0, ge=0, description="起始行号")
    limit: int = Field(default=100, ge=1, description="读取行数")


class FileReadOutput(BaseModel):
    """文件读取输出模式"""
    content: str = Field(description="文件内容")
    lines: int = Field(description="读取的行数")
    path: str = Field(description="文件路径")
    encoding: str = Field(description="文件编码")


class FileReadTool(BaseTool[FileReadInput, FileReadOutput, None]):
    """
    文件读取工具示例

    演示如何：
    1. 处理文件系统操作
    2. 设置安全属性（只读）
    3. 验证文件路径
    4. 处理错误情况
    """

    def __init__(self):
        metadata = ToolMetadata(
            name="file_read",
            description="读取文件内容",
            category="filesystem",
            priority="high",
            input_schema=FileReadInput,
            output_schema=FileReadOutput,
            is_read_only=True,
            is_concurrency_safe=True,
            is_search_or_read_command=True,
            timeout=10.0
        )
        super().__init__(metadata)

    async def call(
        self,
        args: FileReadInput,
        context: ToolContext,
        can_use_tool: Callable[[str], bool],
        on_progress: Optional[Callable[[None], None]] = None,
    ) -> ToolResult[FileReadOutput]:
        """读取文件"""
        start_time = time.time()

        try:
            self._logger.info(f"读取文件: {args.path}")

            # 检查文件路径安全性
            import os
            file_path = os.path.expanduser(args.path)

            if not os.path.exists(file_path):
                return ToolResult(
                    success=False,
                    error=f"文件不存在: {file_path}",
                    execution_time=time.time() - start_time
                )

            if not os.path.isfile(file_path):
                return ToolResult(
                    success=False,
                    error=f"不是文件: {file_path}",
                    execution_time=time.time() - start_time
                )

            # 读取文件
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # 应用offset和limit
                start = args.offset
                end = min(start + args.limit, len(lines))
                selected_lines = lines[start:end]

                content = ''.join(selected_lines)

                execution_time = time.time() - start_time

                output = FileReadOutput(
                    content=content,
                    lines=len(selected_lines),
                    path=args.path,
                    encoding="utf-8"
                )

                self._logger.info(f"成功读取 {len(selected_lines)} 行")

                return ToolResult(
                    success=True,
                    output=output,
                    execution_time=execution_time
                )

            except UnicodeDecodeError:
                return ToolResult(
                    success=False,
                    error=f"文件编码错误（非UTF-8）: {file_path}",
                    execution_time=time.time() - start_time
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self._logger.error(f"读取文件失败: {e}")

            return ToolResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )

    async def validate_input(
        self, input: FileReadInput, context: ToolContext
    ) -> Any:  # ToolValidationResult - 简化导入
        """验证输入参数"""
        errors = []

        # 检查路径是否为空
        if not input.path or not input.path.strip():
            errors.append("文件路径不能为空")

        # 检查limit范围
        if input.limit > 1000:
            errors.append("一次最多读取1000行")

        # 简化返回（实际应返回ToolValidationResult）
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }


# ============================================
# 示例3: Web搜索工具
# ============================================

class WebSearchInput(BaseModel):
    """Web搜索输入模式"""
    query: str = Field(..., description="搜索查询")
    limit: int = Field(default=10, ge=1, le=50, description="返回结果数量")
    engine: str = Field(default="google", description="搜索引擎")


class WebSearchOutput(BaseModel):
    """Web搜索输出模式"""
    results: List[Dict[str, Any]] = Field(description="搜索结果")
    count: int = Field(description="结果数量")
    query: str = Field(description="搜索查询")
    engine: str = Field(description="使用的搜索引擎")


class WebSearchTool(BaseTool[WebSearchInput, WebSearchOutput, None]):
    """
    Web搜索工具示例

    演示如何：
    1. 集成外部API
    2. 使用context中的配置
    3. 设置超时和限制
    4. 处理API错误
    """

    def __init__(self):
        metadata = ToolMetadata(
            name="web_search",
            description="网络搜索工具",
            category="web_search",
            priority="high",
            input_schema=WebSearchInput,
            output_schema=WebSearchOutput,
            is_read_only=True,
            is_concurrency_safe=True,
            timeout=15.0,
            is_open_world=True  # 访问开放的网络
        )
        super().__init__(metadata)

    async def call(
        self,
        args: WebSearchInput,
        context: ToolContext,
        can_use_tool: Callable[[str], bool],
        on_progress: Optional[Callable[[None], None]] = None,
    ) -> ToolResult[WebSearchOutput]:
        """执行Web搜索"""
        start_time = time.time()

        try:
            self._logger.info(f"Web搜索: {args.query}（引擎: {args.engine}）")

            # 检查是否可以使用MCP搜索服务
            if "local_search" in context.mcp_clients:
                # 使用MCP搜索服务
                results = await self._search_via_mcp(args, context)
            else:
                # 模拟搜索
                results = await self._simulate_search(args.query, args.limit)

            execution_time = time.time() - start_time

            output = WebSearchOutput(
                results=results,
                count=len(results),
                query=args.query,
                engine=args.engine
            )

            return ToolResult(
                success=True,
                output=output,
                execution_time=execution_time,
                metadata={"engine": args.engine}
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self._logger.error(f"Web搜索失败: {e}")

            return ToolResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )

    async def _search_via_mcp(
        self, args: WebSearchInput, context: ToolContext
    ) -> List[Dict[str, Any]]:
        """通过MCP服务搜索"""
        # 实际应用中调用MCP搜索服务
        # 这里简化为模拟
        return await self._simulate_search(args.query, args.limit)

    async def _simulate_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """模拟搜索结果"""
        results = []
        for i in range(min(limit, 5)):
            results.append({
                "title": f"{query}相关结果 {i+1}",
                "url": f"https://example.com/result{i+1}",
                "snippet": f"这是关于{query}的搜索结果摘要...",
                "source": "示例网站"
            })
        return results


# ============================================
# 使用示例
# ============================================

async def example_patent_search():
    """专利搜索示例"""
    from core.tools.tool_interface_v2 import ToolRegistry, ToolContext

    # 创建注册表
    registry = ToolRegistry()

    # 注册工具
    patent_tool = SimplePatentSearchTool()
    await registry.register(patent_tool)

    # 创建上下文
    context = ToolContext(
        session_id="session_001",
        agent_id="xiaona",
        model="claude-sonnet-4-6",
        timeout=30.0,
        permission_mode=PermissionMode.AUTO
    )

    # 准备输入
    input_data = PatentSearchInput(
        query="人工智能",
        limit=5,
        source="cnipa"
    )

    # 定义进度回调
    async def progress_callback(progress: Dict[str, float]):
        stage = progress.get("stage", "unknown")
        value = progress.get("progress", 0)
        print(f"  进度: {stage} - {value*100:.0f}%")

    # 调用工具
    print("=" * 60)
    print("🔍 示例1: 专利搜索工具")
    print("=" * 60)
    print(f"查询: {input_data.query}")
    print(f"限制: {input_data.limit}")
    print(f"数据源: {input_data.source}")
    print()

    result = await registry.call_tool(
        "simple_patent_search",
        input_data,
        context,
        on_progress=progress_callback
    )

    # 显示结果
    if result.success:
        print(f"✅ 搜索成功")
        print(f"   找到: {result.output.count} 个专利")
        print(f"   执行时间: {result.output.execution_time:.2f}秒")
        print()
        print("   结果:")
        for i, patent in enumerate(result.output.results, 1):
            print(f"   {i}. {patent['patent_id']}: {patent['title']}")
    else:
        print(f"❌ 搜索失败: {result.error}")


async def example_file_read():
    """文件读取示例"""
    from core.tools.tool_interface_v2 import ToolRegistry, ToolContext

    # 创建注册表
    registry = ToolRegistry()

    # 注册工具
    file_tool = FileReadTool()
    await registry.register(file_tool)

    # 创建上下文
    context = ToolContext(
        session_id="session_002",
        agent_id="xiaona",
        working_directory="/Users/xujian/Athena工作平台"
    )

    # 准备输入
    input_data = FileReadInput(
        path="README.md",
        offset=0,
        limit=10
    )

    # 调用工具
    print("\n" + "=" * 60)
    print("📄 示例2: 文件读取工具")
    print("=" * 60)
    print(f"文件: {input_data.path}")
    print(f"行数: {input_data.limit}")
    print()

    result = await registry.call_tool(
        "file_read",
        input_data,
        context
    )

    # 显示结果
    if result.success:
        print(f"✅ 读取成功")
        print(f"   行数: {result.output.lines}")
        print(f"   编码: {result.output.encoding}")
        print()
        print("   内容预览:")
        lines = result.output.content.split('\n')[:5]
        for line in lines:
            print(f"   {line}")
    else:
        print(f"❌ 读取失败: {result.error}")


async def example_web_search():
    """Web搜索示例"""
    from core.tools.tool_interface_v2 import ToolRegistry, ToolContext

    # 创建注册表
    registry = ToolRegistry()

    # 注册工具
    search_tool = WebSearchTool()
    await registry.register(search_tool)

    # 创建上下文
    context = ToolContext(
        session_id="session_003",
        agent_id="xiaona",
        timeout=15.0
    )

    # 准备输入
    input_data = WebSearchInput(
        query="Athena平台",
        limit=3,
        engine="google"
    )

    # 调用工具
    print("\n" + "=" * 60)
    print("🌐 示例3: Web搜索工具")
    print("=" * 60)
    print(f"查询: {input_data.query}")
    print(f"引擎: {input_data.engine}")
    print()

    result = await registry.call_tool(
        "web_search",
        input_data,
        context
    )

    # 显示结果
    if result.success:
        print(f"✅ 搜索成功")
        print(f"   找到: {result.output.count} 个结果")
        print()
        print("   结果:")
        for i, item in enumerate(result.output.results, 1):
            print(f"   {i}. {item['title']}")
            print(f"      {item['url']}")
    else:
        print(f"❌ 搜索失败: {result.error}")


# ============================================
# 主函数
# ============================================

async def main():
    """运行所有示例"""
    print("=" * 60)
    print("🚀 Athena平台工具系统v2.0示例")
    print("=" * 60)
    print()

    # 运行示例
    await example_patent_search()
    await example_file_read()
    await example_web_search()

    print("\n" + "=" * 60)
    print("✅ 所有示例运行完成")
    print("=" * 60)
    print("\n💡 提示：")
    print("1. 所有工具都继承自BaseTool抽象类")
    print("2. 使用Pydantic模式进行输入验证")
    print("3. 通过ToolContext传递执行环境")
    print("4. 返回统一的ToolResult结果")
    print("5. 支持进度回调和错误处理")
    print()
    print("📚 更多信息请参考:")
    print("   - core/tools/tool_interface_v2.py")
    print("   - docs/guides/TOOL_SYSTEM_V2_MIGRATION_GUIDE.md")


if __name__ == "__main__":
    asyncio.run(main())
