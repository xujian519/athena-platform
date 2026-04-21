# Agent接口最佳实践

> **版本**: v1.0
> **日期**: 2026-04-21
> **目标受众**: Agent开发者、架构师

---

## 📋 目录

1. [命名约定](#命名约定)
2. [代码组织](#代码组织)
3. [错误处理](#错误处理)
4. [日志记录](#日志记录)
5. [性能优化](#性能优化)
6. [安全考虑](#安全考虑)
7. [测试策略](#测试策略)
8. [文档规范](#文档规范)
9. [常见反模式](#常见反模式)

---

## 命名约定

### Agent类命名

**原则**: 清晰描述Agent职责，使用`Agent`后缀

```python
# ✅ 推荐
class RetrieverAgent(BaseXiaonaComponent):
    """检索Agent"""

class AnalyzerAgent(BaseXiaonaComponent):
    """分析Agent"""

class XiaonaAgent(BaseXiaonaComponent):
    """小娜法律专家Agent"""

# ❌ 不推荐
class Agent1(BaseXiaonaComponent):
    """不清晰的命名"""

class Retriever(BaseXiaonaComponent):
    """缺少Agent后缀"""
```

### 能力命名

**原则**: 使用`动词_名词`形式，描述实际操作

```python
# ✅ 推荐
AgentCapability(
    name="patent_search",  # 动词_名词
    description="在专利数据库中检索专利",
)

AgentCapability(
    name="claim_analysis",  # 动词_名词
    description="分析权利要求",
)

# ❌ 不推荐
AgentCapability(
    name="search",  # 太模糊
    description="搜索",
)

AgentCapability(
    name="PatentSearch",  # 不应使用大写
    description="专利检索",
)
```

### 方法命名

**原则**: 公共方法使用动词开头，私有方法使用下划线前缀

```python
class MyAgent(BaseXiaonaComponent):
    # ✅ 推荐：公共方法使用清晰动词
    async def execute(self, context):
        """执行任务"""
        pass

    def get_system_prompt(self):
        """获取系统提示词"""
        pass

    def validate_input(self, context):
        """验证输入"""
        pass

    # ✅ 推荐：私有方法使用下划线
    async def _call_llm(self, prompt):
        """调用LLM（私有）"""
        pass

    def _parse_result(self, raw_result):
        """解析结果（私有）"""
        pass

    # ❌ 不推荐
    async def do_it(self, context):
        """不清晰的方法名"""
        pass

    def process(self):
        """太通用的名称"""
        pass
```

### 变量命名

**原则**: 使用描述性名称，避免单字母变量（除循环变量）

```python
# ✅ 推荐
async def execute(self, context):
    user_input = context.input_data.get("user_input", "")
    patent_data = context.input_data.get("patent_data", {})
    search_results = await self._search_patents(user_input)

    for patent in search_results:
        self._process_patent(patent)

# ❌ 不推荐
async def execute(self, context):
    d = context.input_data.get("user_input", "")
    pd = context.input_data.get("patent_data", {})
    res = await self._search(d)

    for x in res:
        self._proc(x)
```

### 常量命名

**原则**: 使用全大写+下划线

```python
# ✅ 推荐
class MyAgent(BaseXiaonaComponent):
    MAX_RETRIES = 3
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_MODEL = "kimi-k2.5"

    def _initialize(self):
        self.timeout = self.DEFAULT_TIMEOUT
        self.retries = self.MAX_RETRIES

# ❌ 不推荐
class MyAgent(BaseXiaonaComponent):
    maxRetries = 3  # 应该全大写
    default_timeout = 30.0  # 应该全大写
```

---

## 代码组织

### 文件结构

**推荐的组织方式**:

```
core/agents/my_agent/
├── __init__.py                 # 导出MyAgent
├── my_agent.py                 # 主Agent类
├── prompts.py                  # 提示词定义
├── utils.py                    # 工具函数
└── tests/
    ├── __init__.py
    ├── test_my_agent.py        # 单元测试
    └── test_integration.py     # 集成测试
```

### 类组织

**推荐的方法顺序**:

```python
class MyAgent(BaseXiaonaComponent):
    """我的Agent"""

    # 1. 魔术方法
    def __init__(self, agent_id: str):
        super().__init__(agent_id)

    # 2. 生命周期方法（必需）
    def _initialize(self) -> None:
        """初始化"""
        pass

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        pass

    async def execute(self, context):
        """执行任务"""
        pass

    # 3. 公共API
    def validate_input(self, context):
        """验证输入"""
        pass

    def get_capabilities(self):
        """获取能力"""
        pass

    # 4. 私有方法（按字母顺序）
    async def _call_llm(self, prompt):
        """调用LLM"""
        pass

    def _parse_result(self, result):
        """解析结果"""
        pass

    async def _process_data(self, data):
        """处理数据"""
        pass
```

### 导入顺序

**原则**: 标准库 → 第三方库 → 本地模块

```python
# ✅ 推荐
# 1. 标准库
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

# 2. 第三方库
import pytest
from unittest.mock import AsyncMock, Mock

# 3. 本地模块
from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentCapability,
)
from core.llm.unified_llm_manager import UnifiedLLMManager

# ❌ 不推荐（混在一起）
from core.agents.xiaona.base_component import BaseXiaonaComponent
import asyncio
from typing import Dict
from core.llm.unified_llm_manager import UnifiedLLMManager
import logging
```

---

## 错误处理

### 分层错误处理

**原则**: 不同层级的错误采用不同处理策略

```python
class MyAgent(BaseXiaonaComponent):
    async def execute(self, context):
        """执行任务 - 顶层错误处理"""
        try:
            # 业务逻辑
            result = await self._do_work(context)

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=result,
            )

        except ValueError as e:
            # 输入验证错误 - 返回清晰的错误信息
            self.logger.error(f"输入验证失败: {e}")
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                error_message=f"输入验证失败: {str(e)}",
            )

        except Exception as e:
            # 未预期错误 - 记录完整堆栈，返回通用错误
            self.logger.exception(f"任务执行失败: {context.task_id}")
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                error_message=f"任务执行失败: {str(e)}",
            )

    async def _do_work(self, context):
        """实际工作逻辑 - 中层错误处理"""
        try:
            # 调用子方法
            result = await self._call_llm(context)
            return self._parse_result(result)

        except json.JSONDecodeError as e:
            # JSON解析错误 - 可恢复的错误
            self.logger.warning(f"JSON解析失败，尝试修复: {e}")
            # 尝试修复
            fixed_result = self._try_fix_json(result)
            return self._parse_result(fixed_result)

    async def _call_llm(self, prompt):
        """调用LLM - 底层错误处理"""
        try:
            return await self.llm_manager.generate(
                prompt=prompt,
                system_prompt=self.get_system_prompt(),
            )
        except ConnectionError:
            # 连接错误 - 直接抛出，让上层处理
            raise
```

### 重试策略

**原则**: 对于可恢复的错误，实现指数退避重试

```python
import asyncio

class MyAgent(BaseXiaonaComponent):
    async def execute(self, context):
        """执行任务 - 带重试"""
        max_retries = context.config.get("max_retries", 3)
        base_delay = context.config.get("retry_delay", 1.0)

        for attempt in range(max_retries):
            try:
                result = await self._do_work(context)
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.COMPLETED,
                    output_data=result,
                )

            except ConnectionError as e:
                # 可重试的错误
                if attempt < max_retries - 1:
                    # 指数退避
                    delay = base_delay * (2 ** attempt)
                    self.logger.warning(
                        f"连接失败（{attempt + 1}/{max_retries}），"
                        f"{delay}秒后重试: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    # 最后一次重试失败
                    self.logger.error(f"重试{max_retries}次后仍失败")
                    return AgentExecutionResult(
                        agent_id=self.agent_id,
                        status=AgentStatus.ERROR,
                        error_message=f"连接失败（已重试{max_retries}次）",
                    )

            except ValueError as e:
                # 不可重试的错误（输入错误）
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.ERROR,
                    error_message=f"输入错误（不可重试）: {str(e)}",
                )
```

### 错误信息

**原则**: 提供清晰、可操作的错误信息

```python
# ✅ 推荐 - 清晰的错误信息
return AgentExecutionResult(
    agent_id=self.agent_id,
    status=AgentStatus.ERROR,
    error_message=(
        "专利ID格式错误。"
        "期望格式: CN + 数字 + 字母 (例如: CN123456A)。"
        f"实际收到: {patent_id}"
    ),
)

# ❌ 不推荐 - 模糊的错误信息
return AgentExecutionResult(
    agent_id=self.agent_id,
    status=AgentStatus.ERROR,
    error_message="错误",  # 太模糊，没有信息量
)
```

---

## 日志记录

### 日志级别使用

**原则**: 正确使用日志级别

```python
class MyAgent(BaseXiaonaComponent):
    async def execute(self, context):
        # DEBUG: 详细诊断信息
        self.logger.debug(f"输入数据: {context.input_data}")
        self.logger.debug(f"配置: {context.config}")

        # INFO: 重要事件
        self.logger.info(f"开始执行任务: {context.task_id}")
        self.logger.info("任务执行成功")

        # WARNING: 可恢复的问题
        self.logger.warning("缓存未命中，使用慢速路径")
        self.logger.warning(f"响应时间较长: {elapsed:.2f}秒")

        # ERROR: 错误，但程序可继续
        self.logger.error(f"LLM调用失败: {e}")
        self.logger.error(f"任务执行失败: {context.task_id}")

        # CRITICAL: 严重错误，程序可能无法继续
        self.logger.critical("数据库连接失败，无法继续")
```

### 结构化日志

**原则**: 使用结构化日志，便于分析

```python
# ✅ 推荐 - 结构化日志
self.logger.info(
    "任务执行成功",
    extra={
        "task_id": context.task_id,
        "session_id": context.session_id,
        "agent_id": self.agent_id,
        "execution_time": elapsed,
        "input_length": len(context.input_data.get("user_input", "")),
        "result_size": len(result),
    }
)

# ❌ 不推荐 - 非结构化日志
self.logger.info(
    f"任务 {context.task_id} 在会话 {context.session_id} 中执行成功，"
    f"耗时{elapsed}秒，输入长度{len(context.input_data.get('user_input', ''))}"
)
```

### 敏感信息处理

**原则**: 不记录敏感信息

```python
# ✅ 推荐 - 脱敏日志
def _sanitize_input(self, user_input: str) -> str:
    """脱敏输入"""
    if len(user_input) > 100:
        return user_input[:100] + "...(已截断)"
    return user_input

self.logger.info(f"处理用户输入: {self._sanitize_input(user_input)}")

# ❌ 不推荐 - 记录完整输入（可能包含敏感信息）
self.logger.info(f"处理用户输入: {user_input}")
```

---

## 性能优化

### 异步操作

**原则**: 使用async/await，不要阻塞

```python
# ✅ 推荐 - 使用异步
async def execute(self, context):
    # 并行执行独立任务
    results = await asyncio.gather(
        self._fetch_patent_data(patent_id),
        self._fetch_legal_documents(patent_id),
        self._fetch_similarity_scores(patent_id),
    )
    return self._combine_results(results)

# ❌ 不推荐 - 串行执行
async def execute(self, context):
    data1 = await self._fetch_patent_data(patent_id)
    data2 = await self._fetch_legal_documents(patent_id)
    data3 = await self._fetch_similarity_scores(patent_id)
    return self._combine_results([data1, data2, data3])
```

### 缓存策略

**原则**: 缓存昂贵操作的结果

```python
from functools import lru_cache

class MyAgent(BaseXiaonaComponent):
    def _initialize(self):
        # 缓存系统提示词
        self._system_prompt_cache = None

    def get_system_prompt(self) -> str:
        """获取系统提示词（带缓存）"""
        if self._system_prompt_cache is None:
            self._system_prompt_cache = self._load_system_prompt()
        return self._system_prompt_cache

    @lru_cache(maxsize=100)
    def _get_capability_description(self, capability_name: str) -> str:
        """获取能力描述（带缓存）"""
        # 这个结果会被缓存
        return f"能力: {capability_name}"
```

### 资源管理

**原则**: 及时释放资源

```python
# ✅ 推荐 - 使用上下文管理器
async def execute(self, context):
    async with self.llm_manager.get_client() as client:
        result = await client.generate(prompt)
    # 客户端自动释放

# ❌ 不推荐 - 手动管理资源
async def execute(self, context):
    client = self.llm_manager.get_client()
    result = await client.generate(prompt)
    # 忘记释放客户端
```

---

## 安全考虑

### 输入验证

**原则**: 验证所有输入

```python
def validate_input(self, context):
    """验证输入"""
    # 1. 必需字段检查
    if not context.session_id:
        raise ValueError("缺少session_id")

    if not context.task_id:
        raise ValueError("缺少task_id")

    # 2. 类型检查
    if not isinstance(context.input_data, dict):
        raise ValueError("input_data必须是字典")

    # 3. 内容检查
    user_input = context.input_data.get("user_input", "")
    if len(user_input) > 10000:
        raise ValueError("输入过长（最大10000字符）")

    # 4. 安全检查
    dangerous_patterns = ["<script>", "javascript:", "eval("]
    if any(pattern in user_input.lower() for pattern in dangerous_patterns):
        raise ValueError("输入包含潜在危险内容")

    return True
```

### 输出脱敏

**原则**: 脱敏敏感输出

```python
def _sanitize_output(self, output_data: dict) -> dict:
    """脱敏输出"""
    sanitized = output_data.copy()

    # 脱敏特定字段
    if "api_key" in sanitized:
        sanitized["api_key"] = "***REDACTED***"

    if "password" in sanitized:
        sanitized["password"] = "***REDACTED***"

    # 脱敏长文本
    if "full_text" in sanitized and len(sanitized["full_text"]) > 1000:
        sanitized["full_text"] = (
            sanitized["full_text"][:1000] +
            "...(已截断)"
        )

    return sanitized
```

### 权限检查

**原则**: 检查操作权限

```python
async def execute(self, context):
    """执行任务 - 带权限检查"""
    # 检查权限
    required_permission = "patent:write"
    user_permissions = context.metadata.get("permissions", [])

    if required_permission not in user_permissions:
        self.logger.warning(
            f"权限不足: 需要{required_permission}"
        )
        return AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.ERROR,
            error_message="权限不足",
        )

    # 执行任务
    result = await self._do_work(context)
    return result
```

---

## 测试策略

### 测试金字塔

**原则**: 多层测试，单元测试为主

```
        /\
       /E2E\        少量端到端测试
      /------\
     /  集成  \     适量集成测试
    /----------\
   /   单元测试  \  大量单元测试
  /--------------\
```

### 单元测试

**原则**: 测试单个方法，使用Mock隔离依赖

```python
class TestMyAgentUnit:
    """单元测试"""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """测试成功执行"""
        agent = MyAgent(agent_id="test")

        # Mock依赖
        with patch.object(agent, 'llm_manager') as mock_llm:
            mock_llm.generate = AsyncMock(
                return_value='{"result": "test"}'
            )

            # 执行
            context = AgentExecutionContext(
                session_id="SESSION_001",
                task_id="TASK_001",
                input_data={"user_input": "test"},
                config={},
                metadata={},
            )
            result = await agent.execute(context)

            # 验证
            assert result.status == AgentStatus.COMPLETED
            assert result.output_data is not None
```

### 集成测试

**原则**: 测试组件协作，减少Mock

```python
class TestMyAgentIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_with_real_llm(self):
        """测试与真实LLM的集成"""
        agent = MyAgent(agent_id="test")

        # 使用真实LLM（不Mock）
        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={"user_input": "test"},
            config={},
            metadata={},
        )
        result = await agent.execute(context)

        # 验证
        assert result.status == AgentStatus.COMPLETED
```

### 测试命名

**原则**: 使用描述性名称

```python
# ✅ 推荐
def test_execute_success_when_input_is_valid():
    """测试：输入有效时执行成功"""
    pass

def test_execute_failure_when_input_is_empty():
    """测试：输入为空时执行失败"""
    pass

# ❌ 不推荐
def test_1():
    """测试1"""
    pass

def test_execute():
    """测试执行"""
    pass
```

---

## 文档规范

### Docstring格式

**原则**: 使用Google风格docstring

```python
def analyze_patent(self, patent_id: str, config: dict) -> dict:
    """分析专利

    这是详细的段落描述，说明方法的功能、使用场景和注意事项。

    Args:
        patent_id (str): 专利ID，格式如"CN123456A"
        config (dict): 配置参数，包含:
            - model (str): 使用的模型，默认"kimi-k2.5"
            - timeout (float): 超时时间（秒），默认30.0

    Returns:
        dict: 分析结果，包含:
            - creativity_score (float): 创造性评分（0-1）
            - analysis (str): 详细分析文本

    Raises:
        ValueError: 如果patent_id格式不正确
        ConnectionError: 如果LLM连接失败

    Examples:
        >>> agent = MyAgent(agent_id="test")
        >>> result = agent.analyze_patent("CN123456A", {})
        >>> print(result["creativity_score"])
        0.85
    """
    pass
```

### 注释原则

**原则**: 注释"为什么"，而非"什么"

```python
# ✅ 推荐 - 解释"为什么"
# 使用指数退避避免过载LLM API
delay = base_delay * (2 ** attempt)
await asyncio.sleep(delay)

# ❌ 不推荐 - 重复"什么"
# 延迟是base_delay的2的attempt次方
delay = base_delay * (2 ** attempt)
await asyncio.sleep(delay)
```

### README模板

**原则**: 为每个Agent提供README

```markdown
# MyAgent

## 简介
MyAgent负责XXX任务。

## 能力
- capability1: 描述1
- capability2: 描述2

## 使用方法
\`\`\`python
from core.agents.my_agent import MyAgent

agent = MyAgent(agent_id="my_agent")
result = await agent.execute(context)
\`\`\`

## 配置参数
- param1: 描述
- param2: 描述

## 示例
详见examples/目录。
```

---

## 常见反模式

### 反模式1: 过度继承

**问题**: 不必要的继承层次

```python
# ❌ 反模式
class BaseAgent(BaseXiaonaComponent):
    pass

class LegalAgent(BaseAgent):
    pass

class PatentAgent(LegalAgent):
    pass

class RetrieverAgent(PatentAgent):
    pass  # 继承链太长

# ✅ 推荐
class RetrieverAgent(BaseXiaonaComponent):
    pass  # 直接继承基类
```

### 反模式2: God Object

**问题**: Agent承担过多职责

```python
# ❌ 反模式 - 一个Agent做太多事
class SuperAgent(BaseXiaonaComponent):
    async def execute(self, context):
        # 检索
        patents = await self._search_patents()
        # 分析
        analysis = await self._analyze_patents(patents)
        # 撰写
        document = await self._write_document(analysis)
        # 翻译
        translated = await self._translate_document(document)
        # 发送邮件
        await self._send_email(translated)
        return translated

# ✅ 推荐 - 拆分成多个Agent
class RetrieverAgent(BaseXiaonaComponent):
    """只负责检索"""
    pass

class AnalyzerAgent(BaseXiaonaComponent):
    """只负责分析"""
    pass

class WriterAgent(BaseXiaonaComponent):
    """只负责撰写"""
    pass
```

### 反模式3: 忽略错误

**问题**: 吞掉异常

```python
# ❌ 反模式
async def execute(self, context):
    try:
        result = await self._do_work()
    except Exception:
        pass  # 忽略所有错误

    return result

# ✅ 推荐 - 至少记录日志
async def execute(self, context):
    try:
        result = await self._do_work()
    except Exception as e:
        self.logger.exception(f"任务执行失败: {e}")
        return AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.ERROR,
            error_message=str(e),
        )
```

### 反模式4: 硬编码

**问题**: 硬编码配置

```python
# ❌ 反模式
async def execute(self, context):
    result = await self.llm_manager.generate(
        prompt=prompt,
        model="kimi-k2.5",  # 硬编码
        temperature=0.7,     # 硬编码
        timeout=30.0,        # 硬编码
    )

# ✅ 推荐 - 使用配置
async def execute(self, context):
    config = context.config
    result = await self.llm_manager.generate(
        prompt=prompt,
        model=config.get("model", "kimi-k2.5"),
        temperature=config.get("temperature", 0.7),
        timeout=config.get("timeout", 30.0),
    )
```

### 反模式5: 过早优化

**问题**: 过早优化导致代码复杂

```python
# ❌ 反模式 - 过早优化
class MyAgent(BaseXiaonaComponent):
    def _initialize(self):
        # 预加载所有可能的数据（可能用不上）
        self._cache = {}
        for category in ["patent", "legal", "case"]:
            self._cache[category] = self._load_category(category)

# ✅ 推荐 - 按需加载
class MyAgent(BaseXiaonaComponent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self._cache = {}  # 懒加载

    async def _get_category(self, category):
        """按需加载"""
        if category not in self._cache:
            self._cache[category] = await self._load_category(category)
        return self._cache[category]
```

---

## 附录

### A. 检查清单

**开发新Agent前**:
- [ ] 明确Agent职责
- [ ] 定义Agent能力
- [ ] 设计接口
- [ ] 规划测试

**开发新Agent时**:
- [ ] 继承BaseXiaonaComponent
- [ ] 实现_initialize
- [ ] 实现get_system_prompt
- [ ] 实现execute
- [ ] 实现validate_input
- [ ] 添加日志
- [ ] 错误处理

**开发新Agent后**:
- [ ] 编写单元测试
- [ ] 编写集成测试
- [ ] 编写文档
- [ ] 接口合规性检查
- [ ] 代码审查

### B. 相关文档

- [统一Agent接口标准](../design/UNIFIED_AGENT_INTERFACE_STANDARD.md)
- [Agent通信协议规范](../design/AGENT_COMMUNICATION_PROTOCOL_SPEC.md)
- [Agent接口实现指南](AGENT_INTERFACE_IMPLEMENTATION_GUIDE.md)
- [Agent接口迁移指南](AGENT_INTERFACE_MIGRATION_GUIDE.md)

---

**遵循最佳实践，构建高质量Agent！** 🚀

如有问题，请查阅完整文档或提交Issue。
