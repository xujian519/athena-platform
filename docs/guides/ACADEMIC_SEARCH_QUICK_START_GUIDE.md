# 学术搜索工具 - 快速启动指南

> **最后更新**: 2026-04-19
> **版本**: v1.0.0
> **作者**: Athena平台团队

---

## 📋 目录

1. [概述](#概述)
2. [安装配置](#安装配置)
3. [基本使用](#基本使用)
4. [高级功能](#高级功能)
5. [API参考](#api参考)
6. [故障排查](#故障排查)
7. [最佳实践](#最佳实践)

---

## 概述

学术搜索工具为Athena平台提供学术论文和文献搜索能力，支持：

- ✅ **Google Scholar**: 全球最大的学术搜索引擎
- ✅ **Semantic Scholar**: AI驱动的学术搜索平台
- ✅ **多数据源合并**: 自动去重和结果合并
- ✅ **智能降级**: 优先使用免费API，失败时自动切换
- ✅ **异步支持**: 高性能并发查询

### 典型应用场景

| 场景 | 说明 |
|-----|------|
| **专利现有技术检索** | 查找相关学术论文作为对比文件 |
| **法律研究** | 检索学术文章作为法理依据 |
| **技术趋势分析** | 了解某领域的研究热点 |
| **证据收集** | 为无效宣告或侵权分析提供学术支持 |

---

## 安装配置

### 1. 环境要求

**Python依赖**（已包含在平台中）：
```bash
pip install aiohttp
```

**可选配置**（增强功能）：
```bash
# 配置Serper API密钥（用于Google Scholar）
export SERPER_API_KEY=your_api_key_here
```

### 2. 获取API密钥（可选）

#### Semantic Scholar API（免费）

- **免费额度**: 5000次请求/5分钟
- **无需注册**: 直接使用
- **文档**: https://api.semanticscholar.org/api-docs/

#### Serper API（Google Scholar，付费）

1. 访问 https://serper.dev/
2. 注册账号
3. 获取API密钥
4. 设置环境变量:
   ```bash
   export SERPER_API_KEY=your_api_key_here
   ```

**免费额度**: 100次/天
**文档**: https://serper.dev/api-documentation

### 3. 验证安装

```python
# 测试基本功能
python -c "
import asyncio
from core.tools.handlers.academic_search_handler import search_papers

async def test():
    result = await search_papers('artificial intelligence', limit=3)
    print(f'成功: {result[\"success\"]}')
    print(f'结果数: {result[\"total_results\"]}')

asyncio.run(test())
"
```

预期输出：
```
成功: True
结果数: 3
```

---

## 基本使用

### 方式一：直接使用Handler

```python
from core.tools.handlers.academic_search_handler import academic_search_handler

# 同步上下文
import asyncio

async def search():
    result = await academic_search_handler(
        query="artificial intelligence",
        limit=10
    )

    if result["success"]:
        for paper in result["results"]:
            print(f"{paper['title']} ({paper['year']})")

asyncio.run(search())
```

### 方式二：使用便捷函数

```python
from core.tools.handlers.academic_search_handler import search_papers

async def search():
    result = await search_papers(
        query="machine learning",
        limit=5
    )

    # 结果自动处理
    for paper in result["results"]:
        print(f"📄 {paper['title']}")
        print(f"   作者: {', '.join(paper['authors'])}")
        print(f"   引用: {paper['citations']}")
        print()

asyncio.run(search())
```

### 方式三：通过统一工具注册表（推荐）

```python
from core.tools.unified_registry import get_unified_registry

async def search():
    registry = get_unified_registry()
    tool = registry.get("academic_search")

    result = await tool.function(
        query="deep learning",
        limit=10
    )

    print(f"找到 {result['total_results']} 篇论文")

asyncio.run(search())
```

---

## 高级功能

### 1. 指定数据源

```python
# 仅使用Semantic Scholar（免费）
result = await academic_search_handler(
    query="neural networks",
    source="semantic_scholar",
    limit=10
)

# 仅使用Google Scholar（需要API密钥）
result = await academic_search_handler(
    query="patent law",
    source="google_scholar",
    limit=10
)

# 同时使用两个数据源并合并
result = await academic_search_handler(
    query="intellectual property",
    source="both",
    limit=20
)
```

### 2. 年份过滤

```python
# 仅搜索2024年的论文
result = await academic_search_handler(
    query="quantum computing",
    year="2024",
    limit=10
)
```

### 3. 研究领域过滤

```python
# 限定计算机科学领域
result = await academic_search_handler(
    query="algorithms",
    field="computer_science",
    limit=10
)
```

### 4. 保存结果

```python
import json
from pathlib import Path

result = await academic_search_handler(
    query="blockchain",
    limit=50
)

# 保存到JSON文件
output_file = Path("/tmp/papers.json")
output_file.write_text(
    json.dumps(result, indent=2, ensure_ascii=False),
    encoding='utf-8'
)

print(f"✅ 结果已保存到: {output_file}")
```

### 5. 批量搜索

```python
keywords = [
    "machine learning",
    "deep learning",
    "neural networks"
]

all_results = []

for keyword in keywords:
    result = await academic_search_handler(
        query=keyword,
        limit=10
    )

    if result["success"]:
        all_results.extend(result["results"])

print(f"总共找到 {len(all_results)} 篇论文")
```

---

## API参考

### academic_search_handler()

统一学术搜索接口

**参数**:

| 参数 | 类型 | 必需 | 说明 |
|-----|------|------|------|
| `query` | str | ✅ | 搜索关键词 |
| `source` | str | ❌ | 数据源（auto/google_scholar/semantic_scholar/both） |
| `limit` | int | ❌ | 返回结果数（1-100，默认: 10） |
| `year` | str | ❌ | 限定年份（如: "2024"） |
| `field` | str | ❌ | 研究领域（如: "computer_science"） |

**返回**:

```python
{
    "success": True,
    "query": "artificial intelligence",
    "source": "semantic_scholar",
    "total_results": 10,
    "results": [
        {
            "index": 1,
            "title": "论文标题",
            "authors": ["作者1", "作者2"],
            "year": 2024,
            "venue": "期刊/会议名称",
            "url": "论文链接",
            "abstract": "摘要",
            "citations": 100,
            "paper_id": "Semantic Scholar ID"
        }
    ],
    "timestamp": "2026-04-19T22:45:00Z"
}
```

### search_papers()

便捷搜索函数

**参数**:

| 参数 | 类型 | 必需 | 说明 |
|-----|------|------|------|
| `query` | str | ✅ | 搜索关键词 |
| `limit` | int | ❌ | 返回结果数（默认: 10） |
| `source` | str | ❌ | 数据源（默认: auto） |

**返回**: 同`academic_search_handler()`

---

## 故障排查

### 问题1: 搜索失败

**现象**:
```python
{"success": False, "error": "..."}
```

**解决方案**:
1. 检查网络连接
2. 验证查询参数是否正确
3. 查看详细错误信息

### 问题2: Google Scholar搜索失败

**现象**:
```python
{"error": "未配置SERPER_API_KEY环境变量"}
```

**解决方案**:
```bash
# 设置API密钥
export SERPER_API_KEY=your_api_key_here

# 或在Python中设置
import os
os.environ["SERPER_API_KEY"] = "your_api_key_here"
```

### 问题3: API限流

**现象**:
```python
{"error": "API rate limit exceeded"}
```

**解决方案**:
1. 减少请求频率
2. 使用缓存避免重复查询
3. 升级API套餐

### 问题4: 结果为空

**现象**:
```python
{"success": True, "total_results": 0}
```

**解决方案**:
1. 检查关键词拼写
2. 尝试更通用的关键词
3. 移除年份或领域过滤

---

## 最佳实践

### 1. 选择合适的数据源

| 场景 | 推荐数据源 | 原因 |
|-----|-----------|------|
| 快速检索 | Semantic Scholar | 免费，无需配置 |
| 覆盖面广 | Google Scholar | 包含更多语言和地区 |
| 高质量结果 | both | 合并去重，结果更全 |

### 2. 优化查询关键词

**好的查询**:
- ✅ "machine learning patents"
- ✅ "artificial intelligence patentability"
- ✅ "deep learning image recognition"

**不好的查询**:
- ❌ "ml" (太短)
- ❌ "a study on something" (太模糊)
- ❌ "专利" (使用英文更准确)

### 3. 合理设置limit

```python
# 快速预览
limit=5

# 正常使用
limit=10  # 默认值

# 深度分析
limit=50

# 最大值（避免超时）
limit=100
```

### 4. 使用缓存

```python
# 简单缓存实现
from functools import lru_cache
import hashlib

_cache = {}

async def cached_search(query: str, limit: int = 10):
    # 生成缓存键
    cache_key = hashlib.md5(f"{query}:{limit}".encode()).hexdigest()

    # 检查缓存
    if cache_key in _cache:
        print("✅ 从缓存获取结果")
        return _cache[cache_key]

    # 执行搜索
    result = await academic_search_handler(query=query, limit=limit)

    # 缓存结果
    if result["success"]:
        _cache[cache_key] = result

    return result
```

### 5. 错误处理

```python
async def safe_search(query: str, max_retries: int = 3):
    """带重试的搜索"""
    for attempt in range(max_retries):
        try:
            result = await academic_search_handler(query=query)

            if result["success"]:
                return result
            else:
                print(f"⚠️ 搜索失败: {result['error']}")

        except Exception as e:
            print(f"❌ 异常: {e}")

        if attempt < max_retries - 1:
            print(f"🔄 重试 {attempt + 1}/{max_retries}...")
            await asyncio.sleep(1)

    return {"success": False, "error": "达到最大重试次数"}
```

---

## 示例代码

完整示例代码请参考：

- **基本使用**: `examples/academic_search_usage_examples.py`
- **测试用例**: `tests/core/tools/test_academic_search_handler.py`
- **验证报告**: `docs/reports/ACADEMIC_SEARCH_TOOL_VERIFICATION_REPORT_20260419.md`

---

## 常见问题

**Q: Semantic Scholar免费吗？**
A: 是的，免费层每5分钟可请求5000次，足够个人使用。

**Q: 必须配置API密钥吗？**
A: 不是必须的。Semantic Scholar无需密钥，但Google Scholar需要Serper API密钥。

**Q: 如何获取更多结果？**
A: 使用`source="both"`合并两个数据源，或多次搜索并合并结果。

**Q: 结果可以导出吗？**
A: 可以，返回的是标准Python字典，可轻松导出为JSON、CSV等格式。

**Q: 支持中文搜索吗？**
A: 支持，但英文搜索结果更准确。建议使用英文关键词。

---

## 联系方式

**问题反馈**: xujian519@gmail.com
**技术支持**: Athena平台团队
**更新日志**: 详见 `docs/reports/ACADEMIC_SEARCH_TOOL_VERIFICATION_REPORT_20260419.md`

---

**文档结束**

*最后更新: 2026-04-19*
*版本: v1.0.0*
