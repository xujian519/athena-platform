# code_analyzer工具使用指南

**工具版本**: 1.0.0
**最后更新**: 2026-04-20
**维护者**: Athena平台团队

---

## 目录

1. [快速开始](#快速开始)
2. [基础用法](#基础用法)
3. [高级用法](#高级用法)
4. [API参考](#api参考)
5. [使用场景](#使用场景)
6. [最佳实践](#最佳实践)
7. [故障排除](#故障排除)

---

## 快速开始

### 安装

code_analyzer工具已集成到Athena平台统一工具注册表，无需额外安装。

### 最简单的示例

```python
from core.tools.tool_implementations import code_analyzer_handler

# 分析Python代码
result = await code_analyzer_handler(
    params={
        "code": "def hello(): print('Hi')",
        "language": "python"
    },
    context={}
)

print(result["complexity"]["level"])  # 输出: 简单
```

---

## 基础用法

### 1. Python代码分析

#### 示例1: 简单函数分析

```python
code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""

result = await code_analyzer_handler(
    params={
        "code": code,
        "language": "python",
        "style": "basic"
    },
    context={}
)

print(f"总行数: {result['statistics']['total_lines']}")       # 7
print(f"代码行: {result['statistics']['code_lines']}")        # 4
print(f"注释行: {result['statistics']['comment_lines']}")     # 0
print(f"复杂度: {result['complexity']['level']}")             # 简单
```

#### 示例2: 详细问题检测

```python
code = """
def debug_function():
    print("Debugging...")
    for i in range(100):
        print(i)
"""

result = await code_analyzer_handler(
    params={
        "code": code,
        "language": "python",
        "style": "detailed"  # 启用问题检测
    },
    context={}
)

print(result["issues"])
# 输出: ['调试代码残留: 存在print语句']
```

### 2. JavaScript代码分析

```python
code = """
class UserService {
    constructor(apiClient) {
        this.apiClient = apiClient;
    }

    async fetchUsers() {
        const response = await this.apiClient.get('/users');
        console.log('Users:', response.data);
        return response.data;
    }
}
"""

result = await code_analyzer_handler(
    params={
        "code": code,
        "language": "javascript",
        "style": "detailed"
    },
    context={}
)

print(f"复杂度: {result['complexity']['level']}")
print(f"问题: {result['issues']}")
# 输出: ['调试代码残留: 存在console.log']
```

### 3. TypeScript代码分析

```python
code = """
interface User {
    id: number;
    name: string;
}

class UserManager {
    private users: Map<number, User> = new Map();

    addUser(user: User): void {
        this.users.set(user.id, user);
    }
}
"""

result = await code_analyzer_handler(
    params={
        "code": code,
        "language": "typescript",
        "style": "basic"
    },
    context={}
)

print(f"注释比例: {result['statistics']['comment_ratio']}")
```

---

## 高级用法

### 1. 使用包装器（推荐）

包装器提供了更友好的API和类型注解。

#### 快速分析（基础模式）

```python
from core.tools.code_analyzer_wrapper import quick_analyze

result = await quick_analyze(
    code="def hello(): print('hi')",
    language="python"
)

print(f"复杂度: {result['complexity']['level']}")
```

#### 深度分析（详细模式）

```python
from core.tools.code_analyzer_wrapper import deep_analyze

result = await deep_analyze(
    code="function test() { console.log('test'); }",
    language="javascript"
)

print(f"问题: {result['issues']}")
print(f"建议: {result['suggestions']}")
```

### 2. 批量分析多个文件

```python
import asyncio
from pathlib import Path
from core.tools.code_analyzer_wrapper import deep_analyze

async def analyze_directory(directory: str, pattern: str = "*.py"):
    """分析目录下所有匹配的文件"""
    results = {}

    for file_path in Path(directory).rglob(pattern):
        code = file_path.read_text()
        result = await deep_analyze(code, "python")
        results[str(file_path)] = result

    return results

# 使用示例
results = await analyze_directory("/path/to/project", "*.py")

# 输出摘要
for file_path, result in results.items():
    print(f"{file_path}: {result['complexity']['level']}")
```

### 3. 集成到CI/CD流水线

```python
#!/usr/bin/env python3
"""
CI/CD代码质量检查脚本
"""
import asyncio
import sys
from pathlib import Path
from core.tools.code_analyzer_wrapper import deep_analyze

async def check_code_quality(directory: str, max_complexity: str = "复杂"):
    """检查代码质量，失败时返回非零退出码"""

    complexity_levels = {"简单": 1, "中等": 2, "复杂": 3, "非常复杂": 4}
    max_level = complexity_levels[max_complexity]

    issues_found = []

    for file_path in Path(directory).rglob("*.py"):
        code = file_path.read_text()
        result = await deep_analyze(code, "python")

        # 检查复杂度
        if complexity_levels[result['complexity']['level']] > max_level:
            issues_found.append(
                f"{file_path}: 复杂度过高 ({result['complexity']['level']})"
            )

        # 检查问题
        if result['issues']:
            issues_found.append(
                f"{file_path}: {', '.join(result['issues'])}"
            )

    if issues_found:
        print("❌ 代码质量检查失败:")
        for issue in issues_found:
            print(f"  - {issue}")
        return 1
    else:
        print("✅ 代码质量检查通过")
        return 0

if __name__ == "__main__":
    exit_code = asyncio.run(check_code_quality("./src"))
    sys.exit(exit_code)
```

### 4. 生成HTML报告

```python
import asyncio
from datetime import datetime
from pathlib import Path
from core.tools.code_analyzer_wrapper import deep_analyze

async def generate_html_report(directory: str, output_file: str):
    """生成HTML格式的分析报告"""

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>代码分析报告</title>
        <style>
            body { font-family: Arial, sans-serif; }
            .file { margin: 20px 0; padding: 15px; border: 1px solid #ddd; }
            .complexity-simple { color: green; }
            .complexity-medium { color: orange; }
            .complexity-complex { color: red; }
            .issues { color: red; }
        </style>
    </head>
    <body>
        <h1>代码分析报告</h1>
        <p>生成时间: {timestamp}</p>
    """

    for file_path in Path(directory).rglob("*.py"):
        code = file_path.read_text()
        result = await deep_analyze(code, "python")

        level_class = f"complexity-{result['complexity']['level']}"

        html_content += f"""
        <div class="file">
            <h2>{file_path}</h2>
            <p>复杂度: <span class="{level_class}">{result['complexity']['level']}</span></p>
            <p>代码行数: {result['statistics']['code_lines']}</p>
            <p>注释比例: {result['statistics']['comment_ratio']}</p>
        """

        if result['issues']:
            html_content += f"<p class='issues'>问题: {', '.join(result['issues'])}</p>"

        html_content += "</div>"

    html_content += """
    </body>
    </html>
    """

    Path(output_file).write_text(html_content)
    print(f"✅ 报告已生成: {output_file}")

# 使用示例
asyncio.run(generate_html_report("./src", "report.html"))
```

---

## API参考

### code_analyzer_handler

原始处理器函数，直接调用工具实现。

```python
async def code_analyzer_handler(
    params: dict[str, Any],
    context: dict[str, Any]
) -> dict[str, Any]
```

**参数**:
- `params` (dict):
  - `code` (str, 必需): 要分析的代码内容
  - `language` (str, 可选): 编程语言（默认"python"）
  - `style` (str, 可选): 分析风格（默认"basic"）

**返回**:
```python
{
    "language": str,              # 分析的语言
    "statistics": {
        "total_lines": int,       # 总行数
        "non_empty_lines": int,   # 非空行数
        "code_lines": int,        # 代码行数
        "comment_lines": int,     # 注释行数
        "comment_ratio": str      # 注释比例 (百分比字符串)
    },
    "complexity": {
        "score": int,             # 复杂度分数
        "level": str              # 复杂度等级 (简单/中等/复杂/非常复杂)
    },
    "issues": list[str],          # 检测到的问题列表（仅detailed模式）
    "suggestions": list[str],     # 改进建议列表
    "analyzed_at": str            # 分析时间 (ISO格式)
}
```

### code_analyzer（包装器）

独立包装器，提供更好的类型注解和错误处理。

```python
async def code_analyzer(
    code: str,
    language: str = "python",
    style: str = "basic"
) -> dict[str, Any]
```

**参数**:
- `code` (str): 要分析的代码内容
- `language` (str): 编程语言（默认"python"）
- `style` (str): 分析风格（默认"basic"）

**返回**: 与`code_analyzer_handler`相同

**异常**:
- `ValueError`: 如果参数无效

### quick_analyze

便捷函数：快速分析代码（基础模式）。

```python
async def quick_analyze(
    code: str,
    language: str = "python"
) -> dict[str, Any]
```

### deep_analyze

便捷函数：深度分析代码（详细模式）。

```python
async def deep_analyze(
    code: str,
    language: str = "python"
) -> dict[str, Any]
```

---

## 使用场景

### 1. 代码审查

在Pull Request中自动检查代码质量：

```python
async def review_pull_request(pr_files: list[str]):
    """审查PR中的所有Python文件"""

    for file_path in pr_files:
        code = Path(file_path).read_text()
        result = await deep_analyze(code, "python")

        if result['issues']:
            print(f"⚠️ {file_path} 发现问题:")
            for issue in result['issues']:
                print(f"  - {issue}")

        if result['complexity']['level'] in ["复杂", "非常复杂"]:
            print(f"⚠️ {file_path} 复杂度过高，建议简化")
```

### 2. 技术债务追踪

定期分析代码库，追踪技术债务：

```python
async def track_technical_debt(directory: str):
    """追踪技术债务"""

    debt_metrics = {
        "total_files": 0,
        "complex_files": 0,
        "files_with_issues": 0,
        "avg_comment_ratio": 0
    }

    for file_path in Path(directory).rglob("*.py"):
        code = file_path.read_text()
        result = await deep_analyze(code, "python")

        debt_metrics["total_files"] += 1

        if result['complexity']['level'] in ["复杂", "非常复杂"]:
            debt_metrics["complex_files"] += 1

        if result['issues']:
            debt_metrics["files_with_issues"] += 1

        # 提取注释比例数值
        comment_ratio = float(result['statistics']['comment_ratio'].rstrip('%'))
        debt_metrics["avg_comment_ratio"] += comment_ratio

    debt_metrics["avg_comment_ratio"] /= debt_metrics["total_files"]

    return debt_metrics
```

### 3. 教学辅助

帮助学生理解代码质量：

```python
async def provide_feedback(student_code: str):
    """为学生代码提供反馈"""

    result = await deep_analyze(student_code, "python")

    feedback = []
    feedback.append(f"代码复杂度: {result['complexity']['level']}")

    if result['issues']:
        feedback.append("\n发现问题:")
        feedback.extend(result['issues'])

    if result['suggestions']:
        feedback.append("\n改进建议:")
        feedback.extend(result['suggestions'])

    return "\n".join(feedback)
```

---

## 最佳实践

### 1. 选择合适的分析模式

- **basic模式**: 快速扫描，适合大量文件
- **detailed模式**: 深度分析，适合关键代码

```python
# ❌ 不好：对所有文件使用detailed模式
for file in all_files:
    await deep_analyze(code, "python")  # 太慢

# ✅ 好：先basic筛选，再detailed分析
for file in all_files:
    result = await quick_analyze(code, "python")
    if result['complexity']['level'] in ["复杂", "非常复杂"]:
        detailed_result = await deep_analyze(code, "python")
```

### 2. 处理异常

```python
# ✅ 好：处理可能的异常
try:
    result = await code_analyzer(code, language="python")
except ValueError as e:
    print(f"参数错误: {e}")
except Exception as e:
    print(f"分析失败: {e}")
```

### 3. 缓存结果

```python
import hashlib
from functools import lru_cache

def get_code_hash(code: str) -> str:
    """计算代码的哈希值"""
    return hashlib.md5(code.encode()).hexdigest()

@lru_cache(maxsize=128)
async def cached_analyze(code_hash: str, language: str):
    """带缓存的代码分析"""
    # 实际分析逻辑
    pass

# 使用
code_hash = get_code_hash(code)
result = await cached_analyze(code_hash, "python")
```

### 4. 组合使用多个工具

```python
# 结合文件操作工具
from core.tools.tool_implementations import file_operator_handler

# 读取文件
file_result = await file_operator_handler(
    params={"action": "read", "path": "example.py"},
    context={}
)

# 分析代码
code = file_result["content"]
analysis_result = await deep_analyze(code, "python")
```

---

## 故障排除

### 问题1: 不支持的语言

**症状**: 返回的复杂度始终为0

**解决方案**:
```python
# 检查语言参数
supported = ["python", "javascript", "typescript", "js", "ts"]
if language not in supported:
    print(f"不支持的语言: {language}")
    print(f"支持的语言: {', '.join(supported)}")
```

### 问题2: 详细模式无问题返回

**症状**: 使用`style="detailed"`但`issues`为空

**原因**: 代码没有检测到问题

**解决方案**:
```python
# 检查代码是否真的有问题
problematic_code = """
def func():
    print("debug")  # 这会被检测
    x = 1
"""

result = await deep_analyze(problematic_code, "python")
print(result['issues'])  # 应该有问题
```

### 问题3: 性能问题

**症状**: 分析大量文件时很慢

**解决方案**:
```python
# 使用并发分析
import asyncio

async def analyze_concurrent(files: list[str]):
    """并发分析多个文件"""
    tasks = []
    for file_path in files:
        code = Path(file_path).read_text()
        tasks.append(deep_analyze(code, "python"))

    results = await asyncio.gather(*tasks)
    return results
```

### 问题4: 复杂度计算不准确

**症状**: 复杂度分数与预期不符

**说明**: 当前复杂度基于关键词计数，不是真正的圈复杂度

**解决方案**: 等待未来版本升级或使用专业工具（如radon）

---

## 常见问题 (FAQ)

**Q: 支持哪些编程语言？**

A: 当前支持Python、JavaScript、TypeScript。更多语言正在开发中。

**Q: 复杂度是如何计算的？**

A: 基于控制流关键词（if, for, while等）的计数。未来将升级为圈复杂度。

**Q: 可以集成到IDE吗？**

A: 可以，通过调用包装器函数或直接使用handler。

**Q: 如何自定义检测规则？**

A: 当前版本不支持自定义规则，请关注未来更新。

**Q: 分析结果可以导出吗？**

A: 可以，所有结果都是字典格式，可以轻松转换为JSON、HTML等格式。

---

## 相关资源

- **验证报告**: [CODE_ANALYZER_TOOL_VERIFICATION_REPORT_20260420.md](../reports/CODE_ANALYZER_TOOL_VERIFICATION_REPORT_20260420.md)
- **统一工具注册表**: [UNIFIED_TOOL_REGISTRY_API.md](../api/UNIFIED_TOOL_REGISTRY_API.md)
- **工具系统指南**: [TOOL_SYSTEM_GUIDE.md](../guides/TOOL_SYSTEM_GUIDE.md)

---

**文档版本**: 1.0.0
**最后更新**: 2026-04-20
**维护者**: Athena平台团队
