# code_executor工具使用指南

**版本**: 1.0.0
**最后更新**: 2026-04-20
**作者**: Athena平台团队

---

## ⚠️ 重要安全警告

在开始使用之前，请务必阅读以下安全警告：

### 🔴 高风险工具

`code_executor`工具使用`exec()`执行Python代码，存在以下**严重安全风险**：

1. **代码注入攻击** - 恶意代码可能窃取数据或破坏系统
2. **无限循环风险** - 可能导致系统挂起
3. **文件系统访问** - 可能读取或修改敏感文件
4. **资源耗尽攻击** - 可能消耗所有CPU/内存资源
5. **沙箱逃逸风险** - 当前沙箱实现不完整

### 使用前提条件

✅ **仅在以下情况下使用**：
- 教育/演示环境
- 可信代码执行
- 受控的测试环境
- 已设置适当的隔离措施

❌ **禁止在以下情况下使用**：
- 生产环境
- 用户提交的代码
- 不受信任的代码
- 互联网公开服务

---

## 目录

1. [快速开始](#快速开始)
2. [基本用法](#基本用法)
3. [安全使用指南](#安全使用指南)
4. [API参考](#api参考)
5. [最佳实践](#最佳实践)
6. [故障排查](#故障排查)
7. [替代方案](#替代方案)

---

## 快速开始

### 安装依赖

```bash
# 无需额外依赖，使用标准库
# 确保Python版本 >= 3.9
python3 --version
```

### 启用工具

```python
# 1. 设置环境变量（授权）
import os
os.environ["CODE_EXECUTOR_AUTHORIZED"] = "true"

# 2. 导入包装器
from core.tools.code_executor_wrapper import CodeExecutorWrapper

# 3. 创建实例
wrapper = CodeExecutorWrapper()

# 4. 执行代码
result = await wrapper.execute(
    code="print('Hello, World!')",
    timeout=5,
    require_authorization=False
)

print(result['output'])  # Hello, World!
```

---

## 基本用法

### 1. 简单代码执行

```python
from core.tools.code_executor_wrapper import execute_code

# 执行简单代码
result = await execute_code(
    code="print('Hello, World!')",
    require_authorization=False
)

if result['success']:
    print(f"输出: {result['output']}")
    print(f"执行时间: {result['execution_time']:.4f}秒")
else:
    print(f"错误: {result['error']}")
```

### 2. 带变量的代码

```python
# 执行带变量的代码
code = """
x = 10
y = 20
print(f"x + y = {x + y}")
result = x * y
"""

result = await execute_code(code, require_authorization=False)
print(result['output'])  # x + y = 30
```

### 3. 错误处理

```python
# 处理代码错误
code = """
x = 1 / 0
"""

result = await execute_code(code, require_authorization=False)

if not result['success']:
    print(f"捕获到错误: {result['error']}")
    # 输出: 捕获到错误: division by zero
```

### 4. 超时设置

```python
# 设置超时时间（秒）
code = """
import time  # 注意: 实际上不能import
time.sleep(0.1)
print('Done')
"""

# 使用内置的time对象
code = """
time.sleep(0.1)
print('Done')
"""

result = await execute_code(
    code,
    timeout=5,  # 5秒超时
    require_authorization=False
)
```

---

## 安全使用指南

### 安全级别

```python
from core.tools.code_executor_wrapper import CodeExecutorWrapper

wrapper = CodeExecutorWrapper()
info = wrapper.get_security_info()

print(f"安全级别: {info['security_level']}")  # HIGH_RISK
print(f"沙箱完整性: {info['sandbox_complete']}")  # False
print(f"推荐用于生产环境: {info['recommended_for_production']}")  # False
```

### 代码验证

```python
# 验证代码安全性
code = "print('Hello')"

try:
    wrapper = CodeExecutorWrapper()
    wrapper._validate_code(code)  # 如果不安全会抛出ValueError
    print("✓ 代码验证通过")
except ValueError as e:
    print(f"✗ 代码验证失败: {e}")
```

### 授权检查

```python
# 检查是否已授权
wrapper = CodeExecutorWrapper()

if wrapper._check_authorization():
    print("✓ 已授权")
else:
    print("✗ 未授权")
    print("请设置环境变量: export CODE_EXECUTOR_AUTHORIZED=true")
```

### 沙箱限制

当前沙箱环境**允许**的操作：
- ✅ 基本数据类型（int, float, str, list, dict）
- ✅ 基本函数（print, range, len, sum, max, min）
- ✅ time对象（time.sleep等）
- ✅ sys对象（sys.stderr.write等）

当前沙箱环境**禁止**的操作：
- ❌ import语句（`import os`, `import sys`）
- ❌ 文件操作（`open()`, `file()`）
- ❌ 动态执行（`eval()`, `compile()`, `exec()`）
- ❌ 网络操作（`urllib`, `socket`）

---

## API参考

### CodeExecutorWrapper类

#### 初始化

```python
wrapper = CodeExecutorWrapper()
```

#### execute方法

```python
async def execute(
    self,
    code: str,
    timeout: int = 5,
    context: Dict[str, Any] | None = None,
    require_authorization: bool = True,
) -> Dict[str, Any]:
    """
    执行Python代码

    Args:
        code: 要执行的Python代码
        timeout: 超时时间（秒），默认5秒
        context: 上下文信息（可选）
        require_authorization: 是否需要用户授权，默认True

    Returns:
        执行结果字典，包含:
        - success: bool - 是否成功
        - output: str - 标准输出
        - error: str - 错误信息
        - execution_time: float - 执行时间（秒）

    Raises:
        ValueError: 代码不符合安全要求
        PermissionError: 未获得用户授权
    """
```

#### get_security_info方法

```python
def get_security_info(self) -> Dict[str, Any]:
    """
    获取安全信息

    Returns:
        安全信息字典，包含:
        - security_level: str - 安全级别
        - sandbox_complete: bool - 沙箱是否完整
        - timeout_protection: str - 超时保护状态
        - resource_limits: str - 资源限制状态
        - isolation: str - 隔离机制
        - recommended_for_production: bool - 是否推荐用于生产环境
        - alternatives: List[str] - 推荐的替代方案
        - risks: List[str] - 已知风险
    """
```

#### print_security_info方法

```python
def print_security_info(self) -> None:
    """打印安全信息到控制台"""
```

### 便捷函数

#### execute_code

```python
async def execute_code(
    code: str,
    timeout: int = 5,
    require_authorization: bool = True,
) -> Dict[str, Any]:
    """
    执行Python代码（便捷函数）

    Args:
        code: 要执行的Python代码
        timeout: 超时时间（秒），默认5秒
        require_authorization: 是否需要用户授权，默认True

    Returns:
        执行结果字典
    """
```

---

## 最佳实践

### 1. 始终验证代码

```python
async def safe_execute(user_code: str) -> Dict[str, Any]:
    """安全执行代码"""

    # 1. 手动验证
    dangerous_patterns = [
        "import", "open", "eval", "exec",
        "__import__", "compile", "file("
    ]

    for pattern in dangerous_patterns:
        if pattern in user_code:
            raise ValueError(f"代码包含危险操作: {pattern}")

    # 2. 限制长度
    if len(user_code) > 1000:
        raise ValueError("代码过长")

    # 3. 执行
    return await execute_code(
        user_code,
        timeout=5,
        require_authorization=False
    )
```

### 2. 设置资源限制

```python
import subprocess
import resource

# 限制内存使用（1GB）
resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))

# 限制CPU时间（5秒）
resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
```

### 3. 使用Docker隔离

```python
import docker

def execute_in_docker(code: str) -> str:
    """在Docker容器中执行代码"""

    client = docker.from_env()

    # 写入代码到文件
    with open("/tmp/script.py", "w") as f:
        f.write(code)

    # 运行容器
    container = client.containers.run(
        "python:3.9",
        "python /workspace/script.py",
        volumes={"/tmp": {"bind": "/workspace", "mode": "ro"}},
        mem_limit="512m",
        cpu_period=100000,
        cpu_quota=50000,
        network_disabled=True,
        detach=False
    )

    return container.decode("utf-8")
```

### 4. 记录执行日志

```python
import logging
from datetime import datetime

logging.basicConfig(filename="code_executor.log", level=logging.INFO)

async def logged_execute(code: str) -> Dict[str, Any]:
    """带日志记录的代码执行"""

    # 记录执行前
    timestamp = datetime.now().isoformat()
    logging.info(f"[{timestamp}] 执行代码: {code[:50]}...")

    # 执行
    result = await execute_code(code, require_authorization=False)

    # 记录结果
    if result['success']:
        logging.info(f"[{timestamp}] 执行成功, 耗时: {result['execution_time']:.4f}秒")
    else:
        logging.error(f"[{timestamp}] 执行失败: {result['error']}")

    return result
```

### 5. 错误处理

```python
async def robust_execute(code: str) -> Dict[str, Any]:
    """健壮的代码执行"""

    try:
        # 验证代码
        if len(code) > 1000:
            return {"success": False, "error": "代码过长"}

        # 检查危险操作
        if "import" in code or "open" in code:
            return {"success": False, "error": "包含危险操作"}

        # 执行代码
        result = await execute_code(
            code,
            timeout=5,
            require_authorization=False
        )

        return result

    except ValueError as e:
        return {"success": False, "error": f"验证错误: {e}"}
    except PermissionError as e:
        return {"success": False, "error": f"权限错误: {e}"}
    except Exception as e:
        return {"success": False, "error": f"未知错误: {e}"}
```

---

## 故障排查

### 问题1: PermissionError: 执行代码需要用户明确授权

**原因**: 未设置授权环境变量

**解决方案**:
```python
import os
os.environ["CODE_EXECUTOR_AUTHORIZED"] = "true"
```

或设置`require_authorization=False`（仅用于测试）

### 问题2: ValueError: 代码过长

**原因**: 代码超过1000字符限制

**解决方案**:
- 缩短代码
- 或修改限制（不推荐）

### 问题3: __import__ not found

**原因**: 尝试在代码中使用import语句

**解决方案**:
- 不要使用import语句
- 使用提供的内置对象（time, sys）

### 问题4: 代码执行超时

**原因**: 代码执行时间超过设定的超时时间

**解决方案**:
- 增加超时时间
- 优化代码性能
- 使用真正的超时机制（signal或threading）

### 问题5: 系统挂起

**原因**: 代码包含无限循环

**解决方案**:
- 使用signal.alarm()实现真正的超时
- 或使用Docker容器隔离
- 或使用threading+timeout

---

## 替代方案

### 1. RestrictedPython (推荐)

```python
from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safe_builtins

code = """
print('Hello, World!')
"""

# 编译受限代码
compiled_code = compile_restricted(code, "<string>", "exec")

# 执行
exec(compiled_code, {"__builtins__": safe_builtins})
```

**优点**:
- 专门设计的安全执行
- 丰富的安全特性
- 易于集成

**缺点**:
- 需要额外依赖
- 学习曲线

### 2. Docker容器 (推荐)

```python
import docker

client = docker.from_env()
container = client.containers.run(
    "python:3.9",
    "print('Hello')",
    mem_limit="512m",
    cpu_quota=50000,
    network_disabled=True,
    detach=False
)
```

**优点**:
- 完全隔离
- 资源限制
- 易于部署

**缺点**:
- 需要Docker环境
- 启动时间较长

### 3. 在线代码执行服务 (生产环境推荐)

**Judge0**:
```python
import requests

response = requests.post(
    "https://judge0.com/api/submissions",
    json={
        "source_code": "print('Hello')",
        "language_id": 71  # Python 3
    }
)
```

**优点**:
- 完全隔离
- 专业的安全措施
- 可扩展

**缺点**:
- 需要互联网连接
- 可能需要付费

---

## 附录

### A. 完整示例

```python
import os
import asyncio
from core.tools.code_executor_wrapper import CodeExecutorWrapper

async def main():
    """完整使用示例"""

    # 1. 设置授权
    os.environ["CODE_EXECUTOR_AUTHORIZED"] = "true"

    # 2. 创建包装器
    wrapper = CodeExecutorWrapper()

    # 3. 打印安全信息
    wrapper.print_security_info()

    # 4. 执行代码
    code = """
# 计算斐波那契数列
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)

print(f"fib(10) = {fib(10)}")
"""

    result = await wrapper.execute(
        code=code,
        timeout=5,
        require_authorization=False
    )

    # 5. 打印结果
    if result['success']:
        print(f"✓ 执行成功")
        print(f"输出:\n{result['output']}")
        print(f"执行时间: {result['execution_time']:.4f}秒")
    else:
        print(f"✗ 执行失败: {result['error']}")

    # 6. 清理
    del os.environ["CODE_EXECUTOR_AUTHORIZED"]

if __name__ == "__main__":
    asyncio.run(main())
```

### B. 相关文档

- 验证报告: `docs/reports/CODE_EXECUTOR_TOOL_VERIFICATION_REPORT_20260420.md`
- 工具系统API: `docs/api/UNIFIED_TOOL_REGISTRY_API.md`
- 代码质量标准: `docs/development/CODE_QUALITY_STANDARDS.md`

### C. 联系方式

如有问题或建议，请联系:
- **作者**: Athena平台团队
- **邮箱**: xujian519@gmail.com

---

**指南结束**
