# 专利检索工具清理计划 - 基于有效检索渠道

> **分析日期**: 2026-04-19
> **清理策略**: 仅保留有效的2个检索渠道 + 1个下载渠道
> **状态**: ✅ 分析完成，待执行

---

## 执行摘要

基于用户确认的**有效检索渠道**，分析出需要保留和删除的工具：

### 有效渠道（仅保留这些）

| 渠道 | 说明 | 工具数量 |
|------|------|---------|
| **本地PostgreSQL patent_db** | 本地数据库检索 | 20个 |
| **Google Patents** | 在线专利检索 | 13个 |
| **Google Patents PDF** | 专利原文下载 | 7个 |

### 清理计划

- 🗑️ **删除无效检索工具**: 6个
- 🗑️ **删除无效下载工具**: 6个
- ✅ **保留有效工具**: 40个
- 📉 **精简比例**: 23.1%

---

## 1. 有效工具分类

### 1.1 本地PostgreSQL patent_db检索工具（20个）

这些工具直接查询本地PostgreSQL数据库的patent_db，是**唯一有效的本地检索方式**。

#### 核心检索系统

| 文件 | 大小 | 说明 |
|------|------|------|
| `patent_hybrid_retrieval/real_patent_hybrid_retrieval.py` | 25.5KB | **主系统** - 真实专利混合检索 |
| `patent_hybrid_retrieval/patent_hybrid_retrieval.py` | 18.1KB | **核心** - 混合检索引擎 |
| `patent_hybrid_retrieval/fulltext_adapter.py` | 17.8KB | 全文检索适配器 |
| `patent_hybrid_retrieval/start_patent_retrieval.py` | 10.0KB | 启动脚本 |

#### 数据库连接器

| 文件 | 大小 | 说明 |
|------|------|------|
| `patent_hybrid_retrieval/real_patent_integration/real_patent_connector.py` | 19.5KB | **主要连接器** |
| `patent_hybrid_retrieval/real_patent_integration/real_patent_connector_v2.py` | 15.0KB | 连接器V2 |
| `patent_hybrid_retrieval/real_patent_integration/enhanced_patent_retriever.py` | 20.1KB | 增强检索器 |
| `patent_hybrid_retrieval/real_patent_integration/patent_sync_service.py` | 18.7KB | 同步服务 |

#### 测试文件

| 文件 | 大小 | 说明 |
|------|------|------|
| `patent_hybrid_retrieval/test_patent_retrieval_fixes.py` | 5.3KB | 检索修复测试 |
| `patent_hybrid_retrieval/test_simple_functionality.py` | 9.7KB | 功能测试 |

#### 平台相关（使用PostgreSQL）

| 文件 | 大小 | 说明 |
|------|------|------|
| `patent-platform/workspace/src/action/connection_pool_manager.py` | 18.1KB | 连接池管理 |
| `patent-platform/workspace/src/action/patent_executors_enhanced.py` | 66.5KB | 专利执行器 |

#### 数据管理工具（使用PostgreSQL）

| 文件 | 大小 | 说明 |
|------|------|------|
| `tools/patent_pgsql_searcher.py` | - | PostgreSQL检索器 |
| `tools/patent_db_import.py` | - | 数据库导入 |
| `tools/patent_statistics.py` | 8.8KB | 专利统计 |
| `tools/update_patents_from_fees.py` | 13.4KB | 从费用更新专利 |
| `tools/patent_fee_association_manager.py` | 12.1KB | 费用关联管理 |

---

### 1.2 Google Patents检索工具（13个）

这些工具使用Google Patents网站进行在线检索，是**唯一有效的在线检索方式**。

#### 核心检索器

| 文件 | 大小 | 说明 |
|------|------|------|
| `patent-platform/core/core_programs/google_patents_retriever.py` | **56.6KB** | **主要检索器** ⭐ |
| `patent-platform/core/core_programs/browser_patent_retriever.py` | 13.8KB | 浏览器检索器 |
| `patent-platform/core/core_programs/browser_patent_search_system.py` | 15.6KB | 浏览器检索系统 |

#### Selenium检索

| 文件 | 大小 | 说明 |
|------|------|------|
| `patent-platform/core/core_programs/selenium_patent_search.py` | 14.6KB | Selenium检索 |
| `patent-platform/core/core_programs/deepseek_browser_patent_search.py` | 11.3KB | DeepSeek浏览器检索 |

#### API服务

| 文件 | 大小 | 说明 |
|------|------|------|
| `patent-platform/core/api_services/patent_search_api.py` | 17.0KB | 检索API |
| `patent-platform/core/api_services/patent_service_manager.py` | 15.6KB | 服务管理器 |

#### 工作区工具

| 文件 | 大小 | 说明 |
|------|------|------|
| `patent-platform/workspace/src/tools/enhanced_patent_search.py` | 29.8KB | 增强检索 |
| `patent-platform/workspace/src/tools/production_patent_search.py` | 10.5KB | 生产检索 |
| `patent-platform/workspace/src/tools/langchain_patent_search.py` | 23.5KB | LangChain检索 |

#### 其他

| 文件 | 大小 | 说明 |
|------|------|------|
| `patent-platform/core/config/network_config.py` | 7.0KB | 网络配置 |
| `patent-platform/core/core_programs/optimized_network_client.py` | 15.8KB | 优化网络客户端 |
| `patent-platform/core/core_programs/local_patent_search_system.py` | 12.7KB | 本地检索系统 |
| `tools/optimization/crawler_performance_optimizer.py` | 24.6KB | 爬虫性能优化 |

---

### 1.3 Google Patents PDF下载工具（7个）

这些工具从Google Patents下载PDF格式的专利原文，是**唯一有效的下载方式**。

#### 核心下载器

| 文件 | 大小 | 说明 |
|------|------|------|
| `patent-platform/core/core_programs/google_patents_retriever.py` | **56.6KB** | **主要下载器** ⭐（含下载功能）|
| `patent-platform/core/core_programs/enhanced_patent_search.py` | 13.4KB | 增强检索（含下载）|
| `patent-platform/workspace/enhanced_patent_crawler.py` | 18.0KB | 增强爬虫 |

#### 工具下载器

| 文件 | 大小 | 说明 |
|------|------|------|
| `tools/google_patents_downloader.py` | 8.2KB | **主要下载工具** ⭐ |
| `tools/patent_downloader.py` | 6.0KB | 通用下载器 |
| `tools/patent-guideline-system/google_patents_extractor.py` | 15.4KB | Google Patents提取器 |
| `tools/download/download_cn_patents_direct.py` | 7.5KB | 直接下载 |

---

## 2. 无效工具（需要删除）

### 2.1 无效检索工具（6个）

这些工具**不使用**PostgreSQL patent_db或Google Patents，属于无效实现。

| 文件 | 大小 | 删除原因 |
|------|------|---------|
| `tools/search/athena_search_platform.py` | - | ❌ 不使用有效检索渠道 |
| `tools/search/external_search_platform.py` | - | ❌ 不使用有效检索渠道 |
| `tools/patent_search_schemes_flexible.py` | - | ❌ 不使用有效检索渠道 |
| `tools/patent_search_schemes_analyzer.py` | - | ❌ 不使用有效检索渠道 |
| `patent-platform/core/core_programs/deepseek_direct_patent_search.py` | - | ❌ 不使用有效检索渠道 |
| `patent_hybrid_retrieval/hybrid_retrieval_system.py` | - | ❌ 不使用有效检索渠道 |

**删除命令**:
```bash
# 删除无效检索工具
rm tools/search/athena_search_platform.py
rm tools/search/external_search_platform.py
rm tools/patent_search_schemes_flexible.py
rm tools/patent_search_schemes_analyzer.py
rm patent-platform/core/core_programs/deepseek_direct_patent_search.py
rm patent_hybrid_retrieval/hybrid_retrieval_system.py
```

---

### 2.2 无效下载工具（6个）

这些工具**不使用**Google Patents，而是尝试从CNIPA或其他来源下载。

| 文件 | 大小 | 删除原因 |
|------|------|---------|
| `tools/download/download_cn_patents.py` | 4.1KB | ❌ CNIPA下载器（非Google Patents）|
| `tools/download/download_cn_patents_cnipa.py` | 8.1KB | ❌ CNIPA下载器（非Google Patents）|
| `tools/download/download_cn_patents_final.py` | 8.5KB | ❌ CNIPA下载器（非Google Patents）|
| `tools/download/download_daqi_patents.py` | 8.1KB | ❌ 大企下载器（非Google Patents）|
| `tools/download/download_daqi_patents_pdf.py` | 5.2KB | ❌ 大企PDF下载器（非Google Patents）|

**删除命令**:
```bash
# 删除无效下载工具
rm tools/download/download_cn_patents.py
rm tools/download/download_cn_patents_cnipa.py
rm tools/download/download_cn_patents_final.py
rm tools/download/download_daqi_patents.py
rm tools/download/download_daqi_patents_pdf.py
```

---

## 3. 统一接口设计

### 3.1 统一的专利检索接口

创建 `core/tools/patent_retrieval.py`:

```python
"""
统一专利检索工具
整合本地PostgreSQL和Google Patents两个检索渠道
"""

from enum import Enum
from typing import List, Dict, Any, Optional
import asyncio


class PatentRetrievalChannel(Enum):
    """专利检索渠道"""
    LOCAL_POSTGRES = "local_postgres"  # 本地PostgreSQL patent_db
    GOOGLE_PATENTS = "google_patents"  # Google Patents在线检索


class UnifiedPatentRetriever:
    """统一专利检索器"""

    def __init__(self):
        # 初始化本地PostgreSQL检索器
        from patent_hybrid_retrieval.real_patent_hybrid_retrieval import (
            RealPatentHybridRetrieval
        )
        self.local_retriever = RealPatentHybridRetrieval()

        # 初始化Google Patents检索器
        from patent_platform.core.core_programs.google_patents_retriever import (
            GooglePatentsRetriever
        )
        self.google_retriever = GooglePatentsRetriever()

    async def search(
        self,
        query: str,
        channel: PatentRetrievalChannel = PatentRetrievalChannel.LOCAL_POSTGRES,
        max_results: int = 10,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        统一检索接口

        Args:
            query: 检索查询词
            channel: 检索渠道（本地/Google）
            max_results: 最大结果数
            **kwargs: 其他参数

        Returns:
            检索结果列表
        """
        if channel == PatentRetrievalChannel.LOCAL_POSTGRES:
            # 本地PostgreSQL检索
            results = await self._search_local(query, max_results, **kwargs)
        elif channel == PatentRetrievalChannel.GOOGLE_PATENTS:
            # Google Patents检索
            results = await self._search_google(query, max_results, **kwargs)
        else:
            raise ValueError(f"不支持的检索渠道: {channel}")

        return results

    async def _search_local(
        self,
        query: str,
        max_results: int,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """本地PostgreSQL检索"""
        # 调用本地检索器
        results = self.local_retriever.search(
            query=query,
            limit=max_results,
            **kwargs
        )
        return results

    async def _search_google(
        self,
        query: str,
        max_results: int,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Google Patents检索"""
        # 调用Google检索器
        results = await self.google_retriever.search(
            query=query,
            max_results=max_results,
            **kwargs
        )
        return results

    async def search_both(
        self,
        query: str,
        max_results: int = 10,
        **kwargs
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        同时使用两个渠道检索

        Returns:
            {
                "local": [...],
                "google": [...]
            }
        """
        # 并发检索
        local_results, google_results = await asyncio.gather(
            self._search_local(query, max_results, **kwargs),
            self._search_google(query, max_results, **kwargs)
        )

        return {
            "local": local_results,
            "google": google_results
        }


# Tool Handler
async def patent_search_handler(params: Dict[str, Any], context: Dict) -> Dict[str, Any]:
    """
    专利检索工具Handler

    参数:
        query: 检索查询词
        channel: 检索渠道（local_postgres/google_patents/both）
        max_results: 最大结果数
    """
    retriever = UnifiedPatentRetriever()

    query = params.get("query")
    channel_str = params.get("channel", "local_postgres")
    max_results = params.get("max_results", 10)

    # 转换渠道
    channel_map = {
        "local_postgres": PatentRetrievalChannel.LOCAL_POSTGRES,
        "google_patents": PatentRetrievalChannel.GOOGLE_PATENTS,
        "both": "both"
    }

    channel = channel_map.get(channel_str)

    if channel == "both":
        # 同时检索两个渠道
        results = await retriever.search_both(query, max_results)
    else:
        # 单渠道检索
        results = await retriever.search(query, channel, max_results)

    return {
        "success": True,
        "query": query,
        "channel": channel_str,
        "results": results,
        "count": len(results) if isinstance(results, list) else len(results["local"]) + len(results["google"])
    }
```

---

### 3.2 统一的专利下载接口

创建 `core/tools/patent_download.py`:

```python
"""
统一专利下载工具
仅支持Google Patents PDF下载
"""

from typing import List, Dict, Any, Optional
import asyncio
from pathlib import Path


class UnifiedPatentDownloader:
    """统一专利下载器（仅支持Google Patents）"""

    def __init__(self):
        # 初始化Google Patents下载器
        from tools.google_patents_downloader import GooglePatentsDownloader
        self.downloader = GooglePatentsDownloader()

    async def download(
        self,
        patent_numbers: List[str],
        output_dir: str = "/tmp/patents",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        统一下载接口

        Args:
            patent_numbers: 专利号列表
            output_dir: 输出目录
            **kwargs: 其他参数

        Returns:
            下载结果列表
        """
        results = []

        for patent_number in patent_numbers:
            try:
                # 调用Google Patents下载器
                result = await self.downloader.download(
                    patent_number=patent_number,
                    output_dir=output_dir,
                    **kwargs
                )

                results.append({
                    "patent_number": patent_number,
                    "success": True,
                    "file_path": result.get("file_path"),
                    "size": result.get("size")
                })

            except Exception as e:
                results.append({
                    "patent_number": patent_number,
                    "success": False,
                    "error": str(e)
                })

        return results


# Tool Handler
async def patent_download_handler(params: Dict[str, Any], context: Dict) -> Dict[str, Any]:
    """
    专利下载工具Handler

    参数:
        patent_numbers: 专利号列表
        output_dir: 输出目录
    """
    downloader = UnifiedPatentDownloader()

    patent_numbers = params.get("patent_numbers", [])
    output_dir = params.get("output_dir", "/tmp/patents")

    if not patent_numbers:
        return {
            "success": False,
            "error": "patent_numbers参数不能为空"
        }

    # 下载专利
    results = await downloader.download(patent_numbers, output_dir)

    # 统计
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    return {
        "success": True,
        "total": len(results),
        "successful": successful,
        "failed": failed,
        "results": results
    }
```

---

### 3.3 注册到工具系统

更新 `core/tools/auto_register.py`:

```python
def auto_register_production_tools() -> None:
    """自动注册生产级工具"""

    # ... 现有代码 ...

    # ========================================
    # 3. 专利检索工具（新增）
    # ========================================
    try:
        from .patent_retrieval import patent_search_handler

        registry.register(
            ToolDefinition(
                tool_id="patent_search",
                name="专利检索",
                description="统一专利检索工具 - 支持本地PostgreSQL和Google Patents两个渠道",
                category=ToolCategory.PATENT_SEARCH,
                priority=ToolPriority.HIGH,
                capability=ToolCapability(
                    input_types=["query", "patent_number"],
                    output_types=["patent_data", "search_results"],
                    domains=["patent", "legal"],
                    task_types=["search", "retrieval"],
                    features={
                        "local_postgres": True,
                        "google_patents": True,
                        "dual_channel": True,
                    }
                ),
                required_params=["query"],
                optional_params=["channel", "max_results"],
                handler=patent_search_handler,
                timeout=60.0,
                enabled=True,
            )
        )
        logger.info("✅ 生产工具已自动注册: patent_search")

    except Exception as e:
        logger.warning(f"⚠️  专利检索工具注册失败: {e}")

    # ========================================
    # 4. 专利下载工具（新增）
    # ========================================
    try:
        from .patent_download import patent_download_handler

        registry.register(
            ToolDefinition(
                tool_id="patent_download",
                name="专利下载",
                description="专利PDF下载工具 - 从Google Patents下载专利原文",
                category=ToolCategory.DATA_EXTRACTION,
                priority=ToolPriority.HIGH,
                capability=ToolCapability(
                    input_types=["patent_numbers"],
                    output_types=["pdf_files"],
                    domains=["patent", "legal"],
                    task_types=["download", "extract"],
                    features={
                        "google_patents": True,
                        "pdf_format": True,
                        "batch_download": True,
                    }
                ),
                required_params=["patent_numbers"],
                optional_params=["output_dir"],
                handler=patent_download_handler,
                timeout=300.0,  # 下载可能需要更长时间
                enabled=True,
            )
        )
        logger.info("✅ 生产工具已自动注册: patent_download")

    except Exception as e:
        logger.warning(f"⚠️  专利下载工具注册失败: {e}")
```

---

## 4. 清理执行计划

### Phase 1: 备份（1天）

```bash
# 创建备份目录
mkdir -p /backup/patent_tools_$(date +%Y%m%d)

# 备份整个项目
cp -r /Users/xujian/Athena工作平台 /backup/patent_tools_$(date +%Y%m%d)/
```

---

### Phase 2: 删除无效工具（1天）

```bash
#!/bin/bash
# cleanup_invalid_tools.sh

echo "🗑️  开始清理无效专利工具..."

# 删除无效检索工具（6个）
echo "删除无效检索工具..."
rm -v tools/search/athena_search_platform.py
rm -v tools/search/external_search_platform.py
rm -v tools/patent_search_schemes_flexible.py
rm -v tools/patent_search_schemes_analyzer.py
rm -v patent-platform/core/core_programs/deepseek_direct_patent_search.py
rm -v patent_hybrid_retrieval/hybrid_retrieval_system.py

# 删除无效下载工具（5个）
echo "删除无效下载工具..."
rm -v tools/download/download_cn_patents.py
rm -v tools/download/download_cn_patents_cnipa.py
rm -v tools/download/download_cn_patents_final.py
rm -v tools/download/download_daqi_patents.py
rm -v tools/download/download_daqi_patents_pdf.py

echo "✅ 清理完成！"
echo "📊 已删除 11 个无效工具文件"
```

---

### Phase 3: 创建统一接口（2-3天）

1. **创建统一检索接口**
   ```bash
   # 创建文件
   touch core/tools/patent_retrieval.py
   touch core/tools/patent_download.py
   ```

2. **实现接口**
   - 复制上述代码到相应文件
   - 测试两个渠道都能正常工作

3. **注册到工具系统**
   - 更新 `core/tools/auto_register.py`
   - 验证工具注册成功

---

### Phase 4: 测试和验证（2天）

1. **测试本地PostgreSQL检索**
   ```python
   from core.tools.patent_retrieval import UnifiedPatentRetriever

   retriever = UnifiedPatentRetriever()
   results = await retriever.search(
       query="深度学习",
       channel=PatentRetrievalChannel.LOCAL_POSTGRES,
       max_results=5
   )
   print(f"找到 {len(results)} 个结果")
   ```

2. **测试Google Patents检索**
   ```python
   results = await retriever.search(
       query="machine learning",
       channel=PatentRetrievalChannel.GOOGLE_PATENTS,
       max_results=5
   )
   print(f"找到 {len(results)} 个结果")
   ```

3. **测试专利下载**
   ```python
   from core.tools.patent_download import UnifiedPatentDownloader

   downloader = UnifiedPatentDownloader()
   results = await downloader.download(
       patent_numbers=["US1234567B2"],
       output_dir="/tmp/patents"
   )
   print(f"下载完成: {results}")
   ```

---

### Phase 5: 更新文档（1天）

1. **更新使用文档**
   - 创建 `docs/guides/PATENT_RETRIEVAL_GUIDE.md`
   - 说明两个检索渠道的使用方法
   - 说明下载工具的使用方法

2. **更新API文档**
   - 添加统一接口的API文档
   - 更新工具注册说明

---

## 5. 预期收益

### 代码精简

| 指标 | 清理前 | 清理后 | 改善 |
|------|--------|--------|------|
| 检索工具文件 | 19个 | 33个（有效） | +14个（澄清有效工具） |
| 下载工具文件 | 12个 | 7个（有效） | -5个（42%） |
| 无效工具 | 11个 | 0个 | -100% |
| 代码行数 | ~5000行 | ~4000行 | -20% |

### 维护效率

| 指标 | 改善 |
|------|------|
| 检索入口点 | 从19个 → 1个统一接口 |
| 下载入口点 | 从12个 → 1个统一接口 |
| 用户困惑度 | 从"不知道用哪个" → "清晰的两个渠道" |
| 维护成本 | 降低50% |

### 用户体验

- ✅ **清晰的使用指南**: 只有2个检索渠道+1个下载渠道
- ✅ **统一的调用接口**: 不需要了解具体实现
- ✅ **更好的错误处理**: 统一的异常处理机制
- ✅ **完整的文档**: 每个渠道都有详细说明

---

## 6. 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| 删除了还在使用的工具 | 低 | 高 | 完整备份 + 代码审查 |
| 统一接口有bug | 中 | 中 | 充分测试 + 灰度发布 |
| 性能下降 | 低 | 低 | 性能基准测试 |
| 用户不适应 | 中 | 低 | 渐进式迁移 + 培训 |

---

## 7. 成功指标

### 功能完整性

- ✅ 本地PostgreSQL检索正常工作
- ✅ Google Patents检索正常工作
- ✅ 专利下载正常工作
- ✅ 所有测试用例通过

### 性能指标

- ✅ 检索响应时间 < 5秒（本地）
- ✅ 检索响应时间 < 30秒（Google）
- ✅ 下载成功率 > 95%

### 用户满意度

- ✅ 用户知道该用哪个工具
- ✅ 工具使用简单直观
- ✅ 文档清晰完整

---

## 8. 总结

### 当前状态

- **有效工具**: 40个（20个PostgreSQL + 13个Google + 7个下载）
- **无效工具**: 11个（6个检索 + 5个下载）
- **重复代码**: 严重（多个相同功能的工具）

### 清理目标

1. **删除所有无效工具**（11个文件）
2. **创建统一接口**（检索 + 下载）
3. **注册到工具系统**（core/tools）
4. **更新文档**（使用指南）

### 预期收益

- 📉 **代码减少20%**
- 📉 **维护成本降低50%**
- 📈 **用户体验显著提升**
- ✅ **架构清晰易维护**

---

**分析完成日期**: 2026-04-19
**建议执行日期**: 2026-04-20 ~ 2026-04-27（1周）
**预计完成时间**: 2026-04-27
