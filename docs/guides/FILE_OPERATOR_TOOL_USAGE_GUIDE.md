# file_operator工具使用指南

**版本**: 1.0.0
**更新日期**: 2026-04-20
**维护者**: Athena平台团队

---

## 目录

1. [简介](#简介)
2. [快速开始](#快速开始)
3. [核心功能](#核心功能)
4. [API参考](#api参考)
5. [使用示例](#使用示例)
6. [最佳实践](#最佳实践)
7. [故障排查](#故障排查)
8. [常见问题](#常见问题)

---

## 简介

file_operator是Athena平台的文件操作工具，提供简单、安全、高效的文件I/O功能。

### 核心特性

- 📝 **读取文件**: 支持文本文件读取，自动处理编码
- ✍️ **写入文件**: 自动创建父目录，支持UTF-8编码
- 📁 **列出目录**: 获取目录下所有文件和子目录
- 🔍 **搜索文件**: 支持通配符模式搜索
- ⚡ **异步操作**: 基于asyncio，不阻塞主线程
- 🛡️ **错误处理**: 完善的异常捕获和错误消息

### 适用场景

- 配置文件读写
- 日志文件处理
- 数据文件批量处理
- 文件系统管理
- 文件搜索和过滤

---

## 快速开始

### 安装

file_operator是Athena平台的内置工具，无需额外安装。

### 导入

```python
# 方式1: 使用包装器（推荐）
from core.tools.file_operator_wrapper import get_file_operator

file_op = get_file_operator()

# 方式2: 直接导入便捷函数
from core.tools.file_operator_wrapper import read_file, write_file, list_directory, search_files

# 方式3: 通过工具注册表获取
from core.tools.unified_registry import get_unified_registry

registry = get_unified_registry()
tool = registry.get("file_operator")
```

### 基本使用

```python
import asyncio

async def main():
    # 读取文件
    result = await read_file("/path/to/file.txt")
    if result["success"]:
        content = result["data"]["content"]
        print(content)
    else:
        print(f"错误: {result['message']}")

# 运行异步函数
asyncio.run(main())
```

---

## 核心功能

### 1. 读取文件 (read_file)

读取指定路径的文本文件内容。

**参数**:
- `path` (str): 文件路径（必需）

**返回**:
```json
{
  "success": true,
  "message": "成功读取文件: /path/to/file.txt",
  "data": {
    "content": "文件内容",
    "size": 100,
    "lines": 10
  }
}
```

**示例**:
```python
result = await read_file("/Users/xujian/config/app.yaml")
if result["success"]:
    content = result["data"]["content"]
    size = result["data"]["size"]
    lines = result["data"]["lines"]
    print(f"读取成功: {size}字符, {lines}行")
else:
    print(f"读取失败: {result['message']}")
```

---

### 2. 写入文件 (write_file)

向指定路径写入文本内容，自动创建父目录。

**参数**:
- `path` (str): 文件路径（必需）
- `content` (str): 文件内容（必需）

**返回**:
```json
{
  "success": true,
  "message": "成功写入文件: /path/to/file.txt",
  "data": {
    "size": 100
  }
}
```

**示例**:
```python
content = """# 配置文件
app_name: Athena
version: 1.0.0
"""

result = await write_file("/Users/xujian/config/app.yaml", content)
if result["success"]:
    print(f"写入成功: {result['data']['size']}字符")
else:
    print(f"写入失败: {result['message']}")
```

---

### 3. 列出目录 (list_directory)

列出指定目录下的所有文件和子目录。

**参数**:
- `path` (str): 目录路径（必需）

**返回**:
```json
{
  "success": true,
  "message": "成功列出目录: /path/to/dir",
  "items": [
    {
      "name": "file1.txt",
      "type": "file",
      "size": 1024
    },
    {
      "name": "subdir",
      "type": "directory",
      "size": 0
    }
  ]
}
```

**示例**:
```python
result = await list_directory("/Users/xujian/Athena工作平台/data")
if result["success"]:
    for item in result["items"]:
        name = item["name"]
        item_type = item["type"]
        size = item["size"]
        print(f"{name} ({item_type}, {size}bytes)")
else:
    print(f"列出失败: {result['message']}")
```

---

### 4. 搜索文件 (search_files)

使用通配符模式在指定目录搜索文件。

**参数**:
- `path` (str): 搜索路径（必需）
- `pattern` (str): 搜索模式，支持通配符（必需）

**返回**:
```json
{
  "success": true,
  "message": "搜索完成: 找到 5 个匹配",
  "data": {
    "matches": ["/path/to/file1.txt", "/path/to/file2.txt"],
    "count": 5
  }
}
```

**通配符支持**:
- `*` - 匹配任意字符
- `?` - 匹配单个字符
- `*.txt` - 匹配所有txt文件
- `file_*.py` - 匹配所有以file_开头的Python文件

**示例**:
```python
# 搜索所有PDF文件
result = await search_files("/Users/xujian/docs", "*.pdf")
if result["success"]:
    matches = result["data"]["matches"]
    count = result["data"]["count"]
    print(f"找到{count}个PDF文件:")
    for match in matches:
        print(f"  - {match}")
```

---

## API参考

### FileOperatorWrapper类

包装器类，提供面向对象的文件操作接口。

#### 方法

##### `async read_file(path: str) -> dict[str, Any]`

读取文件内容。

**参数**:
- `path`: 文件路径

**返回**: 操作结果字典

##### `async write_file(path: str, content: str) -> dict[str, Any]`

写入文件内容。

**参数**:
- `path`: 文件路径
- `content`: 文件内容

**返回**: 操作结果字典

##### `async list_directory(path: str) -> dict[str, Any]`

列出目录内容。

**参数**:
- `path`: 目录路径

**返回**: 操作结果字典

##### `async search_files(path: str, pattern: str) -> dict[str, Any]`

搜索文件。

**参数**:
- `path`: 搜索路径
- `pattern`: 搜索模式（支持通配符）

**返回**: 操作结果字典

##### `async execute(action: str, **kwargs) -> dict[str, Any]`

通用执行方法。

**参数**:
- `action`: 操作类型（read/write/list/search）
- `**kwargs`: 其他参数

**返回**: 操作结果字典

##### `get_metadata() -> dict[str, Any]`

获取工具元数据。

**返回**: 元数据字典

### 便捷函数

直接从`file_operator_wrapper`导入的便捷函数。

#### `async read_file(path: str) -> dict[str, Any]`

读取文件（便捷函数）。

#### `async write_file(path: str, content: str) -> dict[str, Any]`

写入文件（便捷函数）。

#### `async list_directory(path: str) -> dict[str, Any]`

列出目录（便捷函数）。

#### `async search_files(path: str, pattern: str) -> dict[str, Any]`

搜索文件（便捷函数）。

---

## 使用示例

### 示例1: 配置文件管理

```python
import asyncio
import json
from core.tools.file_operator_wrapper import read_file, write_file

async def manage_config():
    # 读取配置
    result = await read_file("/Users/xujian/config/app.json")
    if not result["success"]:
        print(f"读取配置失败: {result['message']}")
        return

    # 解析JSON
    config = json.loads(result["data"]["content"])

    # 修改配置
    config["debug"] = True
    config["version"] = "1.0.1"

    # 写回文件
    new_content = json.dumps(config, indent=2, ensure_ascii=False)
    result = await write_file("/Users/xujian/config/app.json", new_content)

    if result["success"]:
        print("配置更新成功")
    else:
        print(f"配置更新失败: {result['message']}")

asyncio.run(manage_config())
```

### 示例2: 批量文件处理

```python
import asyncio
from pathlib import Path
from core.tools.file_operator_wrapper import list_directory, read_file, write_file

async def process_logs():
    # 列出日志目录
    result = await list_directory("/Users/xujian/logs")
    if not result["success"]:
        print(f"列出目录失败: {result['message']}")
        return

    # 处理每个日志文件
    for item in result["items"]:
        if item["type"] != "file" or not item["name"].endswith(".log"):
            continue

        log_path = f"/Users/xujian/logs/{item['name']}"

        # 读取日志
        log_result = await read_file(log_path)
        if not log_result["success"]:
            continue

        # 处理日志内容（示例：统计ERROR数量）
        content = log_result["data"]["content"]
        error_count = content.count("ERROR")

        # 写入统计结果
        stats_path = f"/Users/xujian/logs/stats/{item['name']}.stats"
        await write_file(stats_path, f"Errors: {error_count}\n")

        print(f"处理完成: {item['name']} ({error_count} errors)")

asyncio.run(process_logs())
```

### 示例3: 文件搜索和过滤

```python
import asyncio
from core.tools.file_operator_wrapper import search_files, read_file

async def search_in_docs():
    # 搜索所有Markdown文件
    result = await search_files("/Users/xujian/docs", "*.md")
    if not result["success"]:
        print(f"搜索失败: {result['message']}")
        return

    matches = result["data"]["matches"]
    print(f"找到 {len(matches)} 个Markdown文件")

    # 在每个文件中搜索关键词
    keyword = "TODO"
    for match in matches:
        file_result = await read_file(match)
        if not file_result["success"]:
            continue

        content = file_result["data"]["content"]
        if keyword in content:
            count = content.count(keyword)
            print(f"  {match}: {count} 个{keyword}")

asyncio.run(search_in_docs())
```

### 示例4: 通过工具注册表使用

```python
import asyncio
from core.tools.unified_registry import get_unified_registry

async def use_via_registry():
    # 获取工具注册表
    registry = get_unified_registry()

    # 获取file_operator工具
    tool = registry.get("file_operator")
    if not tool:
        print("工具不存在")
        return

    # 调用工具
    result = await tool.function({
        "action": "read",
        "path": "/Users/xujian/config/app.yaml"
    }, context={})

    if result["success"]:
        print(result["data"]["content"])
    else:
        print(f"错误: {result['message']}")

asyncio.run(use_via_registry())
```

---

## 最佳实践

### 1. 错误处理

始终检查返回的`success`字段：

```python
result = await read_file("/path/to/file.txt")

if result["success"]:
    # 处理成功情况
    content = result["data"]["content"]
else:
    # 处理错误情况
    print(f"错误: {result['message']}")
    # 或者记录日志
    logger.error(f"文件读取失败: {result['message']}")
```

### 2. 路径处理

使用绝对路径或相对于工作目录的路径：

```python
from pathlib import Path

# 推荐使用绝对路径
config_path = Path("/Users/xujian/Athena工作平台/config/app.yaml")

# 或者相对于工作目录
work_dir = Path.cwd()
config_path = work_dir / "config" / "app.yaml"

result = await read_file(str(config_path))
```

### 3. 异步操作

在异步上下文中使用，避免阻塞：

```python
import asyncio

async def process_multiple_files():
    # 并发读取多个文件
    tasks = [
        read_file("/path/to/file1.txt"),
        read_file("/path/to/file2.txt"),
        read_file("/path/to/file3.txt"),
    ]

    results = await asyncio.gather(*tasks)

    for result in results:
        if result["success"]:
            print(f"读取成功: {result['data']['size']}字符")

asyncio.run(process_multiple_files())
```

### 4. 资源清理

处理完成后及时清理临时文件：

```python
import tempfile
from pathlib import Path

async def use_temp_file():
    # 创建临时文件
    temp_dir = tempfile.mkdtemp()
    temp_file = Path(temp_dir) / "temp.txt"

    # 写入临时文件
    await write_file(str(temp_file), "临时内容")

    try:
        # 使用临时文件
        result = await read_file(str(temp_file))
        # 处理文件...
    finally:
        # 清理临时文件
        if temp_file.exists():
            temp_file.unlink()
        Path(temp_dir).rmdir()
```

### 5. 批量操作

使用循环和列表推导式处理多个文件：

```python
async def batch_process(file_paths):
    results = []

    for file_path in file_paths:
        result = await read_file(file_path)
        if result["success"]:
            # 处理文件内容
            content = result["data"]["content"]
            processed = process_content(content)
            results.append(processed)

    return results
```

---

## 故障排查

### 常见错误及解决方案

#### 1. 文件不存在

**错误消息**: `文件不存在: /path/to/file.txt`

**原因**: 指定的文件路径不存在

**解决方案**:
- 检查文件路径是否正确
- 使用绝对路径而非相对路径
- 确认文件确实存在

```python
from pathlib import Path

file_path = Path("/path/to/file.txt")
if not file_path.exists():
    print(f"文件不存在: {file_path}")
else:
    result = await read_file(str(file_path))
```

#### 2. 权限不足

**错误消息**: `Permission denied: /path/to/file.txt`

**原因**: 没有读取或写入权限

**解决方案**:
- 检查文件权限
- 使用`chmod`修改权限（Linux/macOS）
- 以管理员权限运行程序

```bash
# Linux/macOS
chmod 644 /path/to/file.txt
```

#### 3. 编码错误

**错误消息**: `UnicodeDecodeError: 'utf-8' codec can't decode byte...`

**原因**: 文件不是UTF-8编码

**解决方案**:
- 当前版本仅支持UTF-8编码
- 使用文本编辑器转换文件编码为UTF-8
- 等待后续版本支持更多编码格式

#### 4. 路径格式错误

**错误消息**: `Invalid path: ...`

**原因**: 路径格式不正确（如Windows使用反斜杠）

**解决方案**:
- 使用`pathlib.Path`处理路径
- 使用原始字符串`r"C:\path\to\file.txt"`
- 统一使用正斜杠`/`

```python
from pathlib import Path

# 跨平台路径处理
path = Path("data") / "files" / "test.txt"
result = await read_file(str(path))
```

---

## 常见问题

### Q1: file_operator支持二进制文件吗？

**A**: 当前版本仅支持文本文件（UTF-8编码）。二进制文件支持将在后续版本中提供。

### Q2: 如何处理大文件？

**A**: 当前版本会将整个文件加载到内存。对于大文件（>100MB），建议：
1. 使用流式处理（后续版本支持）
2. 分块读取文件
3. 使用专门的文件处理库

### Q3: file_operator是线程安全的吗？

**A**: file_operator使用异步操作（asyncio），在单线程事件循环中运行。如需多线程使用，请确保每个线程有独立的事件循环。

### Q4: 如何监控文件变更？

**A**: 当前版本不支持文件监听。可以使用Python的`watchdog`库：

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".txt"):
            print(f"文件变更: {event.src_path}")

observer = Observer()
observer.schedule(MyHandler(), path="/Users/xujian/data")
observer.start()
```

### Q5: file_operator的性能如何？

**A**: 根据验证测试，file_operator的平均响应时间为31ms，性能优秀。对于大多数应用场景，性能不是瓶颈。

### Q6: 如何递归搜索子目录？

**A**: 当前版本的搜索功能不支持递归。可以结合`list_directory`和递归函数实现：

```python
async def recursive_search(directory, pattern):
    matches = []

    # 列出当前目录
    result = await list_directory(directory)
    if not result["success"]:
        return matches

    for item in result["items"]:
        path = f"{directory}/{item['name']}"

        if item["type"] == "file":
            # 检查是否匹配模式
            if Path(path).match(pattern):
                matches.append(path)
        elif item["type"] == "directory":
            # 递归搜索子目录
            matches.extend(await recursive_search(path, pattern))

    return matches
```

---

## 进阶话题

### 与其他工具集成

file_operator可以与Athena平台的其他工具配合使用：

#### 与patent_search配合

```python
from core.tools.file_operator_wrapper import write_file
from core.tools.patent_retrieval import patent_search_handler

# 搜索专利
patent_result = await patent_search_handler({
    "query": "人工智能",
    "channel": "google_patents",
    "max_results": 10
}, context={})

# 保存结果
if patent_result.get("success"):
    await write_file(
        "/Users/xujian/data/patents.json",
        json.dumps(patent_result["data"], indent=2, ensure_ascii=False)
    )
```

#### 与vector_search配合

```python
from core.tools.file_operator_wrapper import read_file
from core.tools.vector_search_handler import vector_search_handler

# 读取文档
doc_result = await read_file("/Users/xujian/docs/document.txt")

if doc_result["success"]:
    # 向量搜索
    search_result = await vector_search_handler({
        "query": doc_result["data"]["content"][:1000],  # 前1000字符
        "collection": "documents",
        "top_k": 5
    }, context={})
```

### 自定义扩展

可以基于file_operator创建更高级的工具：

```python
from core.tools.file_operator_wrapper import get_file_operator

class ConfigManager:
    def __init__(self, config_dir):
        self.config_dir = config_dir
        self.file_op = get_file_operator()

    async def load_config(self, name):
        result = await self.file_op.read_file(f"{self.config_dir}/{name}.json")
        if result["success"]:
            return json.loads(result["data"]["content"])
        return None

    async def save_config(self, name, config):
        content = json.dumps(config, indent=2, ensure_ascii=False)
        result = await self.file_op.write_file(f"{self.config_dir}/{name}.json", content)
        return result["success"]

# 使用
config_mgr = ConfigManager("/Users/xujian/config")
config = await config_mgr.load_config("app")
config["debug"] = True
await config_mgr.save_config("app", config)
```

---

## 性能优化建议

1. **批量操作**: 使用`asyncio.gather`并发处理多个文件
2. **缓存结果**: 对频繁读取的文件进行缓存
3. **异步优先**: 始终使用异步API，避免阻塞事件循环
4. **路径优化**: 使用绝对路径，避免重复解析

---

## 参考资源

- [验证报告](../reports/FILE_OPERATOR_TOOL_VERIFICATION_REPORT_20260420.md)
- [统一工具注册表API](../api/UNIFIED_TOOL_REGISTRY_API.md)
- [工具系统指南](../guides/TOOL_SYSTEM_GUIDE.md)

---

**维护者**: Athena平台团队
**最后更新**: 2026-04-20
**版本**: 1.0.0
