#!/usr/bin/env python3
"""
Athena平台工具系统v2.0迁移指南

本指南说明如何将现有工具迁移到新的基于Claude Code架构的工具接口。

Author: Athena平台团队
Date: 2026-04-20
"""

# ============================================
# 迁移步骤
# ============================================

## 步骤1: 理解新接口的核心概念

### 1.1 BaseTool接口

新接口基于BaseTool抽象类，包含以下核心方法：

```python
class BaseTool(ABC, Generic[Input, Output, Progress]):
    @abstractmethod
    async def call(
        self,
        args: Input,
        context: ToolContext,
        can_use_tool: Callable[[str], bool],
        on_progress: Optional[Callable[[Progress], None]] = None,
    ) -> ToolResult[Output]:
        """执行工具"""
        pass
```

### 1.2 ToolMetadata

工具元数据包含：
- name: 工具名称
- description: 工具描述
- category: 工具分类
- priority: 优先级
- input_schema: Pydantic输入模式
- output_schema: Pydantic输出模式
- 安全属性：is_read_only, is_concurrency_safe, is_destructive

### 1.3 ToolContext

执行上下文包含：
- 会话信息：session_id, agent_id
- 系统配置：model, debug_mode, timeout
- 资源限制：max_result_size_chars
- MCP集成：mcp_clients, mcp_resources
- 权限和安全：permission_mode
- 取消控制：abort_controller

## 步骤2: 迁移现有工具

### 2.1 旧工具示例（使用@tool装饰器）

```python
# 旧方式
from core.tools.decorators import tool

@tool(
    name="patent_search",
    description="搜索专利",
    category="patent_search"
)
async def patent_search_handler(query: str, limit: int = 10) -> Dict[str, Any]:
    results = await search_patents(query, limit)
    return {"results": results, "count": len(results)}
```

### 2.2 新工具示例（继承BaseTool）

```python
# 新方式
from core.tools.tool_interface_v2 import BaseTool, ToolMetadata, ToolContext, ToolResult
from pydantic import BaseModel

class PatentSearchInput(BaseModel):
    """输入模式"""
    query: str
    limit: int = 10
    source: str = "cnipa"

class PatentSearchOutput(BaseModel):
    """输出模式"""
    results: List[Dict[str, Any]]
    count: int
    query: str

class PatentSearchTool(BaseTool[PatentSearchInput, PatentSearchOutput, None]):
    """专利搜索工具"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="patent_search",
            description="搜索专利",
            category="patent_search",
            priority="high",
            input_schema=PatentSearchInput,
            output_schema=PatentSearchOutput,
            is_read_only=True,
            is_concurrency_safe=True,
            timeout=30.0,
        )
        super().__init__(metadata)
    
    async def call(
        self,
        args: PatentSearchInput,
        context: ToolContext,
        can_use_tool: Callable[[str], bool],
        on_progress: Optional[Callable[[None], None]] = None,
    ) -> ToolResult[PatentSearchOutput]:
        """执行专利搜索"""
        try:
            # 执行搜索逻辑
            results = await self._search_patents(
                args.query,
                args.limit,
                args.source
            )
            
            output = PatentSearchOutput(
                results=results,
                count=len(results),
                query=args.query
            )
            
            return ToolResult(
                success=True,
                output=output,
                metadata={
                    "source": args.source,
                    "execution_time": 0.5
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    async def _search_patents(self, query: str, limit: int, source: str) -> List[Dict]:
        """实际的搜索逻辑"""
        # 实现搜索逻辑
        pass
```

## 步骤3: 注册和使用新工具

### 3.1 注册工具

```python
from core.tools.tool_interface_v2 import ToolRegistry

async def main():
    registry = ToolRegistry()
    
    # 注册工具
    tool = PatentSearchTool()
    await registry.register(tool)
    
    # 调用工具
    context = ToolContext(
        session_id="session_123",
        agent_id="agent_456",
        model="claude-sonnet-4-6",
        timeout=30.0
    )
    
    result = await registry.call_tool(
        "patent_search",
        PatentSearchInput(query="人工智能", limit=10),
        context
    )
    
    if result.success:
        print(f"找到 {result.output.count} 个专利")
    else:
        print(f"错误: {result.error}")
```

## 步骤4: 迁移检查清单

- [ ] 定义Pydantic输入/输出模式
- [ ] 创建继承BaseTool的工具类
- [ ] 实现call方法
- [ ] 设置ToolMetadata
- [ ] 配置安全属性（is_read_only等）
- [ ] 实现输入验证（如需要）
- [ ] 测试工具功能
- [ ] 更新文档

# ============================================
# 工具分类映射
# ============================================

根据Claude Code的工具分类，Athena平台工具分类映射：

| Claude Code分类 | Athena平台分类 | 说明 |
|----------------|---------------|------|
| 文件操作 | FILESYSTEM | 文件读写、编辑 |
| Shell和执行 | SYSTEM | 系统命令执行 |
| 代理和编排 | - | 智能体协调（Athena特有） |
| 任务管理 | - | 任务管理（Athena特有） |
| 规划和Worktree | - | 规划模式（Athena特有） |
| Web和搜索 | WEB_SEARCH | 网络搜索 |
| MCP集成 | MCP_SERVICE | MCP服务 |
| 配置 | SYSTEM | 配置管理 |
| 通信 | - | 通信工具（Athena特有） |
| 其他 | - | 其他工具 |

# ============================================
# 权限系统映射
# ============================================

### Claude Code权限模式

```typescript
type PermissionMode = 'default' | 'auto' | 'bypass'
```

### Athena平台权限模式

```python
class PermissionMode(Enum):
    DEFAULT = "default"  # 默认模式，未匹配规则时需要用户确认
    AUTO = "auto"  # 自动模式，未匹配规则时自动拒绝
    BYPASS = "bypass"  # 绕过模式，允许所有调用（谨慎使用）
```

### 权限规则

```python
# 工具权限规则
permission_rules = {
    "allow": [
        PermissionRule(
            rule_id="safe-read",
            pattern="*:read",
            description="允许所有读操作",
            priority=10
        )
    ],
    "deny": [
        PermissionRule(
            rule_id="dangerous-rm",
            pattern="*:*rm*",
            description="拒绝包含rm的命令",
            priority=100
        )
    ]
}
```

# ============================================
# MCP集成映射
# ============================================

### Claude Code MCP工具

```typescript
mcpInfo?: {
  serverName: string
  toolName: string
}
```

### Athena平台MCP工具

```python
@dataclass
class ToolMetadata:
    # ...
    is_mcp: bool = False
    mcp_info: Optional[Dict[str, str]] = None

# 示例
metadata = ToolMetadata(
    name="academic_search",
    description="学术论文搜索",
    category="academic_search",
    is_mcp=True,
    mcp_info={
        "server_name": "academic-search",
        "tool_name": "search_papers"
    }
)
```

# ============================================
# 迁移示例：完整工具实现
# ============================================

"""
完整的专利搜索工具实现示例
"""

from typing import Dict, List, Optional, Callable, Any
from core.tools.tool_interface_v2 import BaseTool, ToolMetadata, ToolContext, ToolResult
from pydantic import BaseModel, Field

class PatentSearchInput(BaseModel):
    """专利搜索输入"""
    query: str = Field(..., description="搜索查询")
    limit: int = Field(default=10, ge=1, le=100, description="返回结果数量")
    source: str = Field(default="cnipa", description="数据源")
    sort_by: str = Field(default="relevance", description="排序方式")

class PatentSearchOutput(BaseModel):
    """专利搜索输出"""
    results: List[Dict[str, Any]] = Field(description="搜索结果")
    count: int = Field(description="结果数量")
    query: str = Field(description="原始查询")
    source: str = Field(description="数据源")

class PatentSearchTool(BaseTool[PatentSearchInput, PatentSearchOutput, Dict[str, float]]):
    """专利搜索工具 - v2.0版本"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="patent_search",
            description="搜索专利数据库",
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
        import time
        start_time = time.time()
        
        try:
            self._logger.info(f"搜索专利: {args.query}")
            
            # 报告进度
            if on_progress:
                await on_progress({"stage": "searching", "progress": 0.2})
            
            # 执行搜索（模拟）
            results = await self._do_search(args, context)
            
            # 报告完成
            if on_progress:
                await on_progress({"stage": "completed", "progress": 1.0})
            
            execution_time = time.time() - start_time
            
            output = PatentSearchOutput(
                results=results,
                count=len(results),
                query=args.query,
                source=args.source
            )
            
            return ToolResult(
                success=True,
                output=output,
                execution_time=execution_time,
                metadata={
                    "source": args.source,
                    "sort_by": args.sort_by
                }
            )
            
        except Exception as e:
            self._logger.error(f"搜索失败: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def _do_search(
        self,
        args: PatentSearchInput,
        context: ToolContext
    ) -> List[Dict[str, Any]]:
        """执行实际的搜索逻辑"""
        # 这里实现实际的搜索逻辑
        # 可以使用context中的MCP客户端等资源
        
        # 模拟返回结果
        return [
            {
                "patent_id": "CN123456789A",
                "title": f"关于{args.query}的专利",
                "abstract": "这是一个示例专利...",
                "applicant": "某某科技公司"
            }
        ]
    
    async def description(self, input: PatentSearchInput, context: ToolContext) -> str:
        """生成工具描述"""
        return f"搜索专利数据库，查询：{input.query}，限制：{input.limit}"

# ============================================
# 使用示例
# ============================================

async def example_usage():
    """使用示例"""
    from core.tools.tool_interface_v2 import ToolRegistry, ToolContext
    
    # 创建注册表
    registry = ToolRegistry()
    
    # 注册工具
    tool = PatentSearchTool()
    await registry.register(tool)
    
    # 创建上下文
    context = ToolContext(
        session_id="session_001",
        agent_id="xiaona",
        model="claude-sonnet-4-6",
        timeout=30.0,
        permission_mode=PermissionMode.AUTO
    )
    
    # 调用工具
    input_data = PatentSearchInput(
        query="人工智能",
        limit=5,
        source="cnipa"
    )
    
    result = await registry.call_tool(
        "patent_search",
        input_data,
        context
    )
    
    if result.success:
        print(f"✅ 搜索成功")
        print(f"   找到 {result.output.count} 个专利")
        for patent in result.output.results:
            print(f"   - {patent['patent_id']}: {patent['title']}")
    else:
        print(f"❌ 搜索失败: {result.error}")

# ============================================
# 总结
# ============================================

"""
迁移总结：

1. 新接口优势：
   - 完整的类型安全（使用Pydantic和Generic）
   - 明确的输入/输出模式验证
   - 丰富的元数据和配置
   - 统一的错误处理
   - 进度回调支持
   - 权限和安全检查集成

2. 迁移要点：
   - 定义Pydantic输入/输出模式
   - 继承BaseTool并实现call方法
   - 配置ToolMetadata
   - 设置正确的安全属性
   - 使用ToolContext传递环境信息

3. 兼容性：
   - 可以与现有@tool装饰器共存
   - 可以逐步迁移工具
   - 统一工具注册表支持两种方式

4. 下一步：
   - 迁移核心工具到v2接口
   - 更新工具注册表以支持v2
   - 编写详细的工具文档
   - 提供迁移脚本
"""

if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
