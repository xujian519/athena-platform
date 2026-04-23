# Athena 沙盒系统实现指南

## 概述

Athena 沙盒系统提供安全的代码执行环境，支持容器隔离和资源限制。参考 DeerFlow 沙盒系统设计。

---

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                   沙盒系统架构                           │
│  ┌───────────────────────────────────────────────────┐  │
│  │           CodeExecutor / SafeCodeRunner           │  │
│  │              (高级执行接口)                         │  │
│  └───────────────┬───────────────────────────────────┘  │
│                  │                                       │
│  ┌───────────────▼───────────────────────────────────┐  │
│  │              SandboxManager                       │  │
│  │           (沙盒生命周期管理)                        │  │
│  └───────┬───────────────┬───────────────────────────┘  │
│          │               │                               │
│  ┌───────▼──────┐  ┌───▼────────┐  ┌─────────────────┐  │
│  │ LocalSandbox │  │DockerSandbox│ │  (未来扩展)     │  │
│  │   (开发环境)  │  │  (生产环境)  │  │ KubernetesPod   │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 核心组件

### 1. Sandbox 抽象基类

```python
from core.sandbox import Sandbox, SandboxConfig, Language

# 创建沙盒配置
config = SandboxConfig(
    max_execution_time=600,  # 10分钟
    max_memory="512m",       # 512MB
    max_cpu=1.0,            # 1个CPU核心
    enable_network=False,    # 禁用网络
    enable_file_write=True,  # 允许写入
)

# 使用沙盒（以本地沙盒为例）
sandbox = LocalSandbox(config)
await sandbox.initialize()

# 执行命令
result = await sandbox.execute_command("echo 'Hello!'")

# 执行代码
result = await sandbox.execute_code(
    code="print('Hello from Python!')",
    language=Language.PYTHON
)

# 清理
await sandbox.cleanup()
```

### 2. 代码执行器

```python
from core.sandbox import CodeExecutor, ExecutionRequest, Language

# 创建执行器
executor = CodeExecutor()

# 创建执行请求
request = ExecutionRequest(
    code="print('Hello!')",
    language=Language.PYTHON,
    timeout=30,
)

# 执行
response = await executor.execute(request)
print(response.to_dict())

# 快捷执行
result = await executor.execute_python("print('Quick!')")
```

### 3. 安全代码运行器

```python
from core.sandbox import SafeCodeRunner

# 创建运行器
runner = SafeCodeRunner()

# 运行代码
result = await runner.run(
    code="print('Safe execution!')",
    language="python",
    timeout=30
)

print(result)
```

---

## 沙盒类型

### LocalSandbox（本地沙盒）

**用途**：开发环境和测试

**特点**：
- 无容器隔离
- 直接在本地执行
- 快速启动
- 适合调试

```python
from core.sandbox import LocalSandbox, SandboxConfig

sandbox = LocalSandbox(SandboxConfig(temp_dir="/tmp/my-sandbox"))
```

### DockerSandbox（Docker 沙盒）

**用途**：生产环境

**特点**：
- 完全隔离
- 资源限制
- 安全执行
- 支持多语言

```python
from core.sandbox import DockerSandbox, SandboxConfig

config = SandboxConfig(
    container_image="python:3.11-slim",
    max_memory="512m",
    max_cpu=1.0,
    enable_network=False,
)

sandbox = DockerSandbox(config)
```

---

## 支持的编程语言

| 语言 | Language 值 | 说明 |
|------|-------------|------|
| Python | `Language.PYTHON` | Python 3.x |
| JavaScript | `Language.JAVASCRIPT` | Node.js |
| Node.js | `Language.NODE` | Node.js |
| Bash | `Language.BASH` | Bash 脚本 |
| Shell | `Language.SHELL` | Shell 脚本 |

---

## 使用示例

### 示例 1：执行 Python 代码

```python
from core.sandbox import SafeCodeRunner

runner = SafeCodeRunner()

result = await runner.run_python("""
import json
data = {"name": "Athena", "type": "AI Platform"}
print(json.dumps(data, indent=2))
""")

if result["success"]:
    print(result["output"])
else:
    print(f"Error: {result['error']}")
```

### 示例 2：执行 JavaScript 代码

```python
result = await runner.run_javascript("""
const data = { name: "Athena", type: "AI Platform" };
console.log(JSON.stringify(data, null, 2));
""")

if result["success"]:
    print(result["output"])
```

### 示例 3：带输入的执行

```python
result = await runner.run_python("""
import sys
input_data = sys.stdin.read()
print(f"Received: {input_data}")
""", input_data="Hello from stdin!")

print(result["output"])
```

### 示例 4：执行带文件的脚本

```python
from core.sandbox import ScriptExecutionSkill

skill = ScriptExecutionSkill()

result = await skill.execute_script_with_files(
    script="""
with open('input.txt', 'r') as f:
    content = f.read()
print(f'Content: {content}')

with open('output.txt', 'w') as f:
    f.write('Processed!')
""",
    files={"input.txt": "Hello from file!"},
    language="python",
    timeout=30
)

print(result["output"])
```

### 示例 5：使用会话复用沙盒

```python
from core.sandbox import CodeExecutor, ExecutionRequest, Language

executor = CodeExecutor()

# 第一次执行（创建沙盒）
request1 = ExecutionRequest(
    code="x = 1",
    language=Language.PYTHON,
    session_id="my-session",  # 指定会话 ID
)
await executor.execute(request1)

# 第二次执行（复用沙盒）
request2 = ExecutionRequest(
    code="print(f'x = {x}')",  # 可以访问之前的变量
    language=Language.PYTHON,
    session_id="my-session",  # 使用相同的会话 ID
)
response = await executor.execute(request2)

print(response.output)  # 输出: x = 1

# 清理会话
await executor.cleanup_session("my-session")
```

---

## 技能集成

### 在技能中使用沙盒

```python
from core.skills import Skill, SkillResult
from core.skills.sandbox_integration import SandboxSkillMixin

class MySandboxSkill(SandboxSkillMixin, Skill):
    """使用沙盒的技能"""

    async def execute(self, **kwargs) -> SkillResult:
        # 初始化沙盒
        await self.setup_sandbox()

        # 在沙盒中执行代码
        result = await self.execute_python_in_sandbox(
            code=kwargs.get("code", ""),
            timeout=30
        )

        return SkillResult(
            success=result["success"],
            data={"output": result["output"]},
            error=result.get("error"),
            execution_time=result["execution_time"],
        )
```

### 便捷函数

```python
from core.skills.sandbox_integration import (
    execute_code_safely,
    execute_python_safely,
    execute_javascript_safely,
)

# 快捷执行
result = await execute_python_safely("print('Hello!')")
result = await execute_javascript_safely("console.log('Hello!')")
```

---

## 安全特性

### 资源限制

```python
from core.sandbox import SandboxConfig

config = SandboxConfig(
    max_execution_time=600,  # 最大执行时间
    max_memory="512m",       # 最大内存
    max_cpu=1.0,            # 最大 CPU
    max_disk_size="1g",      # 最大磁盘使用
)
```

### 网络隔离

```python
config = SandboxConfig(
    enable_network=False,    # 禁用网络访问
)
```

### 路径映射

```python
config = SandboxConfig(
    path_mappings={
        "/mnt/data": "/actual/data/path",  # 虚拟路径 → 实际路径
        "/mnt/output": "/tmp/outputs",
    },
)
```

---

## 文件清单

| 文件 | 描述 |
|------|------|
| `core/sandbox/__init__.py` | 沙盒模块导出 |
| `core/sandbox/base.py` | 沙盒抽象基类和接口 |
| `core/sandbox/local.py` | 本地沙盒实现 |
| `core/sandbox/docker_sandbox.py` | Docker 沙盒实现 |
| `core/sandbox/executor.py` | 代码执行器 |
| `core/skills/sandbox_integration.py` | 技能沙盒集成 |
| `tests/test_sandbox_system.py` | 沙盒系统测试 |

---

## 测试结果

```
总计: 7/7 通过 🎉

✓ 本地沙盒
✓ 代码执行器
✓ 安全代码运行器
✓ 沙盒技能集成
✓ 沙盒管理器
✓ 错误处理
✓ 多语言支持
```

---

## 下一步

1. **Kubernetes 沙盒** - 实现基于 Pod 的沙盒
2. **更多语言支持** - Ruby, Go, Rust 等
3. **代码分析** - 执行前的静态分析
4. **资源监控** - 实时资源使用监控

---

## 参考

- [DeerFlow 沙盒系统](https://github.com/yamadajoe/deer-flow) - 设计参考
- [Docker Python SDK](https://docker-py.readthedocs.io/) - Docker API
- [Athena 项目文档](../README.md)
