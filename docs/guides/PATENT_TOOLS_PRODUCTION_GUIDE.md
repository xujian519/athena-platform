# 专利工具生产环境使用指南

> **最后更新**: 2026-04-19
> **状态**: ✅ 生产环境可用
> **版本**: v1.0.0

---

## 📋 概述

专利检索和下载工具已成功集成到Athena平台的生产环境工具库中，可通过统一的工具管理器调用。

### 集成的工具

| 工具ID | 名称 | 功能 | 状态 |
|--------|------|------|------|
| `patent_search` | 专利检索 | 统一专利检索接口，支持本地PostgreSQL和Google Patents | ✅ 已启用 |
| `patent_download` | 专利下载 | 专利PDF下载，支持批量下载 | ✅ 已启用 |

---

## 🚀 快速开始

### 1. 工具自动注册

工具在系统启动时会自动注册到全局工具管理器：

```python
from core.tools import get_tool_manager

# 获取工具管理器（自动触发工具注册）
manager = get_tool_manager()

# 查看已注册的工具
tool_ids = manager.list_tools()
print(f"已注册工具: {tool_ids}")
```

### 2. 专利检索

```python
# 通过工具管理器调用专利检索
result = await manager.call_tool(
    "patent_search",
    parameters={
        "query": "machine learning",      # 检索查询
        "channel": "google_patents",      # 检索渠道
        "max_results": 10                 # 最大结果数
    }
)

# 处理结果
if result["status"] == "success":
    results = result["result"]["results"]
    for item in results:
        print(f"{item['patent_id']}: {item['title']}")
```

### 3. 专利下载

```python
# 通过工具管理器调用专利下载
result = await manager.call_tool(
    "patent_download",
    parameters={
        "patent_numbers": ["US20230012345A1", "CN112345678A"],  # 专利号列表
        "output_dir": "/tmp/patents"                            # 输出目录
    }
)

# 处理结果
if result["status"] == "success":
    results = result["result"]["results"]
    for item in results:
        if item["success"]:
            print(f"✅ {item['patent_number']}: {item['file_path']}")
        else:
            print(f"❌ {item['patent_number']}: {item['error']}")
```

---

## 📖 详细使用指南

### 专利检索工具 (patent_search)

#### 参数说明

| 参数 | 类型 | 必需 | 说明 | 默认值 |
|------|------|------|------|--------|
| `query` | string | ✅ | 检索查询词 | - |
| `channel` | string | ❌ | 检索渠道 | `both` |
| `max_results` | integer | ❌ | 最大结果数 | `10` |

#### 检索渠道 (channel)

- **`local_postgres`**: 本地PostgreSQL数据库检索
  - 优点: 快速、稳定、无网络依赖
  - 适用: 已导入的专利数据

- **`google_patents`**: Google Patents在线检索
  - 优点: 数据最新、覆盖全球
  - 适用: 检索最新专利、全球专利

- **`both`**: 双渠道并发检索
  - 优点: 结果最全面
  - 适用: 需要全面检索的场景

#### 返回格式

```json
{
  "status": "success",
  "result": {
    "query": "machine learning",
    "channel": "google_patents",
    "total_results": 10,
    "results": [
      {
        "patent_id": "US20230012345A1",
        "title": "Machine Learning System",
        "abstract": "Abstract text...",
        "source": "google_patents",
        "url": "https://patents.google.com/patent/US20230012345A1",
        "publication_date": "2023-01-01",
        "applicant": "Example Inc.",
        "inventor": "John Doe",
        "score": 0.95
      }
    ]
  },
  "execution_time": 2.5,
  "timestamp": "2026-04-19T10:00:00Z"
}
```

#### 使用示例

```python
from core.tools import get_tool_manager

manager = get_tool_manager()

# 示例1: Google Patents检索
result = await manager.call_tool(
    "patent_search",
    parameters={
        "query": "deep learning",
        "channel": "google_patents",
        "max_results": 5
    }
)

# 示例2: 本地数据库检索
result = await manager.call_tool(
    "patent_search",
    parameters={
        "query": "深度学习",
        "channel": "local_postgres",
        "max_results": 10
    }
)

# 示例3: 双渠道并发检索
result = await manager.call_tool(
    "patent_search",
    parameters={
        "query": "AI芯片",
        "channel": "both",
        "max_results": 20
    }
)

# 处理双渠道结果
if result["status"] == "success":
    data = result["result"]
    if "local" in data:
        local_results = data["local"]
        print(f"本地结果: {len(local_results)}")
    if "google" in data:
        google_results = data["google"]
        print(f"Google结果: {len(google_results)}")
```

### 专利下载工具 (patent_download)

#### 参数说明

| 参数 | 类型 | 必需 | 说明 | 默认值 |
|------|------|------|------|--------|
| `patent_numbers` | list | ✅ | 专利号列表 | - |
| `output_dir` | string | ❌ | 输出目录 | `/tmp/patents` |

#### 专利号格式

支持以下格式：
- 美国: `US20230012345A1`
- 中国: `CN112345678A`
- 欧洲: `EP1234567B1`
- 世界: `WO2023/123456`

#### 返回格式

```json
{
  "status": "success",
  "result": {
    "total_downloaded": 2,
    "successful": 1,
    "failed": 1,
    "results": [
      {
        "patent_number": "US20230012345A1",
        "success": true,
        "file_path": "/tmp/patents/US20230012345A1.pdf",
        "file_size": 1595443,
        "file_size_mb": 1.52,
        "download_time": 10.5,
        "metadata": {
          "title": "Example Patent",
          "publication_date": "2023-01-01"
        }
      },
      {
        "patent_number": "US9999999999A1",
        "success": false,
        "error": "Patent not found",
        "download_time": 2.1
      }
    ]
  },
  "execution_time": 12.6,
  "timestamp": "2026-04-19T10:00:00Z"
}
```

#### 使用示例

```python
from core.tools import get_tool_manager

manager = get_tool_manager()

# 示例1: 单个专利下载
result = await manager.call_tool(
    "patent_download",
    parameters={
        "patent_numbers": ["US20230012345A1"],
        "output_dir": "/tmp/patents"
    }
)

# 示例2: 批量下载
result = await manager.call_tool(
    "patent_download",
    parameters={
        "patent_numbers": [
            "US20230012345A1",
            "CN112345678A",
            "EP1234567B1"
        ],
        "output_dir": "/tmp/patents/batch"
    }
)

# 处理下载结果
if result["status"] == "success":
    data = result["result"]
    total = data["total_downloaded"]
    successful = data["successful"]
    failed = data["failed"]

    print(f"总计: {total}, 成功: {successful}, 失败: {failed}")

    for item in data["results"]:
        if item["success"]:
            print(f"✅ {item['patent_number']}: {item['file_path']} ({item['file_size_mb']:.2f} MB)")
        else:
            print(f"❌ {item['patent_number']}: {item['error']}")
```

---

## 🔧 高级用法

### 1. 在Agent中使用

```python
from core.agents.base_agent import BaseAgent
from core.tools import get_tool_manager

class MyPatentAgent(BaseAgent):
    def __init__(self):
        super().__init__("patent_agent")
        self.tool_manager = get_tool_manager()

    async def search_and_download(self, query: str):
        """检索并下载专利"""
        # 1. 检索专利
        search_result = await self.tool_manager.call_tool(
            "patent_search",
            parameters={
                "query": query,
                "channel": "google_patents",
                "max_results": 5
            }
        )

        if search_result["status"] != "success":
            return {"error": "检索失败"}

        # 2. 提取专利号
        patent_ids = [
            r["patent_id"]
            for r in search_result["result"]["results"]
        ]

        # 3. 下载专利
        download_result = await self.tool_manager.call_tool(
            "patent_download",
            parameters={
                "patent_numbers": patent_ids,
                "output_dir": "/tmp/patents"
            }
        )

        return {
            "search": search_result,
            "download": download_result
        }

# 使用
agent = MyPatentAgent()
result = await agent.search_and_download("machine learning")
```

### 2. 错误处理

```python
from core.tools import get_tool_manager

manager = get_tool_manager()

async def safe_search(query: str, max_retries: int = 3):
    """带重试的专利检索"""
    for attempt in range(max_retries):
        try:
            result = await manager.call_tool(
                "patent_search",
                parameters={
                    "query": query,
                    "channel": "google_patents",
                    "max_results": 10
                }
            )

            if result["status"] == "success":
                return result
            else:
                error = result.get("error", "Unknown error")
                print(f"尝试 {attempt + 1}/{max_retries} 失败: {error}")

        except Exception as e:
            print(f"尝试 {attempt + 1}/{max_retries} 异常: {e}")

    return {"status": "error", "error": "所有重试失败"}
```

### 3. 批量处理

```python
from core.tools import get_tool_manager
import asyncio

manager = get_tool_manager()

async def batch_search(queries: list[str], concurrency: int = 3):
    """批量专利检索"""
    semaphore = asyncio.Semaphore(concurrency)

    async def search_with_limit(query: str):
        async with semaphore:
            return await manager.call_tool(
                "patent_search",
                parameters={
                    "query": query,
                    "channel": "google_patents",
                    "max_results": 5
                }
            )

    # 并发执行
    results = await asyncio.gather(
        *[search_with_limit(q) for q in queries],
        return_exceptions=True
    )

    # 处理结果
    successful = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
    print(f"批量检索完成: {successful}/{len(queries)} 成功")

    return results

# 使用
queries = ["AI", "机器学习", "deep learning"]
results = await batch_search(queries, concurrency=2)
```

---

## 📊 性能优化

### 1. 使用缓存

```python
from core.tools import get_tool_manager
import hashlib
import json

manager = get_tool_manager()

# 简单的内存缓存
_search_cache = {}

def cache_key(query: str, channel: str) -> str:
    """生成缓存键"""
    data = f"{query}:{channel}"
    return hashlib.md5(data.encode()).hexdigest()

async def cached_search(query: str, channel: str = "google_patents"):
    """带缓存的专利检索"""
    key = cache_key(query, channel)

    # 检查缓存
    if key in _search_cache:
        print(f"缓存命中: {query}")
        return _search_cache[key]

    # 执行检索
    result = await manager.call_tool(
        "patent_search",
        parameters={
            "query": query,
            "channel": channel,
            "max_results": 10
        }
    )

    # 缓存结果
    if result["status"] == "success":
        _search_cache[key] = result

    return result
```

### 2. 批量下载优化

```python
from core.tools import get_tool_manager

manager = get_tool_manager()

async def optimized_batch_download(
    patent_numbers: list[str],
    batch_size: int = 5,
    output_dir: str = "/tmp/patents"
):
    """优化的批量下载"""
    results = []

    # 分批处理
    for i in range(0, len(patent_numbers), batch_size):
        batch = patent_numbers[i:i + batch_size]
        print(f"下载批次 {i//batch_size + 1}/{(len(patent_numbers)-1)//batch_size + 1}")

        result = await manager.call_tool(
            "patent_download",
            parameters={
                "patent_numbers": batch,
                "output_dir": output_dir
            }
        )

        if result["status"] == "success":
            batch_results = result["result"]["results"]
            results.extend(batch_results)

            # 显示进度
            successful = sum(1 for r in batch_results if r["success"])
            print(f"  批次完成: {successful}/{len(batch)} 成功")

    return results
```

---

## 🔍 监控和日志

### 1. 启用日志

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 工具会自动记录日志
# 查看: /var/log/athena/patent_tools.log
```

### 2. 审计日志

```python
from core.tools import get_tool_manager

manager = get_tool_manager()

# 所有工具调用都会被记录到审计日志
# 查看: /var/log/athena/patent_audit.log

# 审计日志格式（JSON）
{
  "timestamp": "2026-04-19T10:00:00Z",
  "tool_id": "patent_search",
  "parameters": {
    "query": "machine learning",
    "channel": "google_patents",
    "max_results": 10
  },
  "result": {
    "status": "success",
    "total_results": 10
  },
  "execution_time": 2.5,
  "user": "athena"
}
```

### 3. 性能监控

```python
from core.tools import get_tool_manager

manager = get_tool_manager()

# Prometheus指标在 http://localhost:9091/metrics
# 关键指标:
# - patent_search_total: 总检索次数
# - patent_search_duration_seconds: 检索耗时
# - patent_download_total: 总下载次数
# - patent_download_duration_seconds: 下载耗时
# - patent_download_size_bytes: 下载文件大小
```

---

## 🧪 测试

### 运行生产环境测试

```bash
# 执行完整的生产环境集成测试
python3 scripts/test_patent_tools_production.py
```

测试包括：
1. ✅ 工具注册测试
2. ✅ 专利检索功能测试
3. ✅ 专利下载功能测试
4. ✅ 双渠道并发检索测试
5. ✅ 批量下载功能测试

---

## 📝 配置

### 配置文件位置

```
production/config/patent_tools_config.yaml
```

### 环境变量覆盖

```bash
# 检索配置
export PATENT_SEARCH_DEFAULT_CHANNEL=google_patents
export PATENT_SEARCH_TIMEOUT=60

# 下载配置
export PATENT_DOWNLOAD_OUTPUT_DIR=/data/patents
export PATENT_DOWNLOAD_TIMEOUT=300

# 缓存配置
export PATENT_CACHE_REDIS_HOST=localhost
export PATENT_CACHE_REDIS_PORT=6379

# 日志配置
export PATENT_LOG_LEVEL=INFO
export PATENT_LOG_FILE_PATH=/var/log/athena/patent_tools.log
```

---

## 🎯 最佳实践

### 1. 选择合适的检索渠道

| 场景 | 推荐渠道 | 原因 |
|------|---------|------|
| 检索最新专利 | `google_patents` | 数据最新 |
| 检索已导入的专利 | `local_postgres` | 速度快 |
| 全面检索 | `both` | 结果最全 |
| 内网环境 | `local_postgres` | 无网络依赖 |

### 2. 批量下载策略

```python
# 推荐: 分批下载，每批3-5个
await optimized_batch_download(
    patent_numbers,
    batch_size=5
)

# 避免: 一次下载太多专利
# 可能导致超时或内存不足
```

### 3. 错误处理

```python
# 推荐: 完善的错误处理
try:
    result = await manager.call_tool(...)
    if result["status"] != "success":
        # 处理业务错误
        logger.error(f"工具调用失败: {result.get('error')}")
except Exception as e:
    # 处理系统异常
    logger.exception(f"工具调用异常: {e}")
```

### 4. 性能优化

```python
# 推荐: 使用缓存
result = await cached_search(query)

# 推荐: 控制并发数
results = await batch_search(queries, concurrency=3)

# 推荐: 限制结果数
result = await manager.call_tool(..., max_results=10)
```

---

## 📚 相关文档

- **快速开始**: `docs/guides/PATENT_TOOLS_QUICK_START.md`
- **配置文件**: `production/config/patent_tools_config.yaml`
- **测试脚本**: `scripts/test_patent_tools_production.py`
- **最终总结**: `docs/reports/PATENT_TOOLS_OPTIMIZATION_FINAL_SUMMARY_20260419.md`
- **配置完成**: `docs/reports/PATENT_TOOLS_CONFIGURATION_COMPLETE_20260419.md`

---

## 💡 技术支持

### 问题排查

1. **工具未注册**: 检查`auto_register.py`是否正确导入
2. **检索失败**: 检查Playwright和网络连接
3. **下载失败**: 检查专利号格式和网络连接
4. **性能问题**: 检查并发数和结果数设置

### 日志查看

```bash
# 查看工具日志
tail -f /var/log/athena/patent_tools.log

# 查看审计日志
tail -f /var/log/athena/patent_audit.log

# 查看系统日志
journalctl -u athena-gateway -f
```

---

**维护者**: Athena平台团队
**最后更新**: 2026-04-19
**状态**: ✅ 生产环境可用
