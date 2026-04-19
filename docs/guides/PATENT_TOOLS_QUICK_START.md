# 专利工具快速使用指南

> **更新日期**: 2026-04-19
> **状态**: ✅ 核心功能可用

---

## 🚀 立即可用的功能

### 1. 专利PDF下载（推荐）

最简单、最可靠的功能，**无需任何配置**。

#### 方式A: 直接使用下载器

```python
from tools.google_patents_downloader import download_patent_pdf

# 下载单个专利
file_path = download_patent_pdf("US20230012345A1")
print(f"✅ 下载到: {file_path}")

# 指定输出路径
file_path = download_patent_pdf(
    "CN112345678A",
    output_path="/tmp/my_patents/CN112345678A.pdf"
)
```

#### 方式B: 使用统一接口

```python
from core.tools.patent_download import download_patent

# 单个下载
result = await download_patent("US20230012345A1")

if result['success']:
    print(f"✅ 下载成功")
    print(f"路径: {result['file_path']}")
    print(f"大小: {result['file_size_mb']} MB")
    print(f"耗时: {result['download_time']} 秒")

# 批量下载
from core.tools.patent_download import download_patents

results = await download_patents([
    "US20230012345A1",
    "CN112345678A",
    "EP1234567B1"
], output_dir="/tmp/patents")

for result in results:
    if result['success']:
        print(f"✅ {result['patent_number']}: {result['file_path']}")
```

**实际测试**: ✅ 成功下载US20230012345A1 (1557.43 KB)

---

## ⚙️ 需要配置的功能

### 2. Google Patents检索（需要Playwright）

#### 安装依赖

```bash
# 安装Playwright
pip install playwright

# 安装浏览器驱动
playwright install chromium

# 验证安装
playwright --version
```

#### 使用方式

```python
from patent_platform.core.core_programs.google_patents_retriever import GooglePatentsRetriever

# 创建检索器
retriever = GooglePatentsRetriever()

# 执行检索
results = await retriever.search(
    query="machine learning",
    max_results=10
)

# 处理结果
for result in results:
    print(f"专利号: {result.patent_id}")
    print(f"标题: {result.title}")
    print(f"摘要: {result.abstract}")
    print(f"申请人: {result.assignee}")
    print(f"链接: {result.url}")
    print()
```

#### 通过统一接口使用

```python
from core.tools.patent_retrieval import search_google_patents

# 检索
results = await search_google_patents(
    "深度学习",
    max_results=10
)

for result in results:
    print(f"{result['patent_id']}: {result['title']}")
```

---

### 3. 本地PostgreSQL检索（需要数据库表）

#### 创建数据库表

```bash
# 使用Docker执行SQL脚本
docker exec -i athena-postgres psql -U athena -d athena < scripts/create_patent_tables.sql
```

或手动执行：

```bash
# 连接到PostgreSQL
docker exec -it athena-postgres psql -U athena -d athena

# 在psql中执行
\i scripts/create_patent_tables.sql
```

#### 数据库表结构

```sql
-- 主表：patents
CREATE TABLE patents (
    id SERIAL PRIMARY KEY,
    patent_id VARCHAR(100) UNIQUE NOT NULL,
    title TEXT,
    abstract TEXT,
    publication_date DATE,
    applicant VARCHAR(500),
    inventor VARCHAR(500),
    classification VARCHAR(100),
    -- ... 更多字段
);

-- 全文检索索引
CREATE INDEX idx_patents_title_gin
ON patents USING gin(to_tsvector('chinese', title));
```

#### 导入数据

```python
# TODO: 将本地PDF文件解析后导入数据库
# 需要使用PDF解析器提取元数据
```

#### 使用方式

```python
from core.tools.patent_retrieval import search_local_patents

# 检索
results = await search_local_patents(
    "深度学习",
    max_results=10
)

for result in results:
    print(f"{result['patent_id']}: {result['title']}")
    print(f"摘要: {result['abstract'][:100]}...")
```

---

## 🔧 高级用法

### 双渠道检索（需要配置）

```python
from core.tools.patent_retrieval import search_patents, PatentRetrievalChannel

# 同时检索本地和Google（需要配置好数据库和Playwright）
results = await search_patents(
    "AI芯片",
    channel=PatentRetrievalChannel.BOTH,
    max_results=20
)

print(f"找到 {len(results)} 个结果")
```

### 通过工具系统使用

```python
from core.tools import get_tool_manager

# 获取工具管理器
manager = get_tool_manager()

# 专利检索
result = await manager.call_tool(
    "patent_search",
    parameters={
        "query": "深度学习",
        "channel": "google_patents",
        "max_results": 10
    }
)

# 专利下载
result = await manager.call_tool(
    "patent_download",
    parameters={
        "patent_numbers": ["US20230012345A1"],
        "output_dir": "/tmp/patents"
    }
)
```

---

## 📊 支持的专利号格式

| 国家/地区 | 格式示例 | 说明 |
|-----------|---------|------|
| 美国 (US) | US20230012345A1 | US + 年份 + 序号 + 代码 |
| 中国 (CN) | CN112345678A | CN + 序号 + 代码 |
| 欧洲 (EP) | EP1234567B1 | EP + 序号 + 代码 |
| 世界 (WO) | WO2023/123456 | WO + 年份 + 序号 |

---

## 🎯 使用场景推荐

### 场景1: 下载单个专利PDF（推荐）

**适合**: 已知专利号，需要下载全文

```python
from core.tools.patent_download import download_patent

result = await download_patent("US20230012345A1")
```

### 场景2: 批量下载专利PDF

**适合**: 有多个专利号需要下载

```python
from core.tools.patent_download import download_patents

patent_numbers = [
    "US20230012345A1",
    "CN112345678A",
    "EP1234567B1"
]

results = await download_patents(patent_numbers, output_dir="/tmp/patents")
```

### 场景3: Google Patents检索（需要配置）

**适合**: 需要检索最新专利、全球专利

```python
from core.tools.patent_retrieval import search_google_patents

results = await search_google_patents("machine learning", max_results=20)
```

### 场景4: 本地数据库检索（需要配置）

**适合**: 有本地专利数据库，需要快速检索

```python
from core.tools.patent_retrieval import search_local_patents

results = await search_local_patents("深度学习", max_results=10)
```

---

## 🛠️ 故障排查

### 问题1: PDF下载失败

**可能原因**:
- 专利号格式不正确
- 网络连接问题
- 专利不存在

**解决方案**:
```python
# 检查专利号格式
patent_id = "US20230012345A1"  # 正确格式
patent_id = "us20230012345a1"  # 错误：需要大写

# 添加错误处理
from tools.google_patents_downloader import download_patent_pdf

try:
    file_path = download_patent_pdf(patent_id, verbose=True)
    if file_path:
        print(f"✅ 下载成功: {file_path}")
    else:
        print(f"❌ 下载失败，请检查专利号")
except Exception as e:
    print(f"❌ 下载异常: {e}")
```

### 问题2: Google Patents检索失败

**可能原因**:
- Playwright未安装
- 浏览器驱动未安装

**解决方案**:
```bash
# 重新安装Playwright
pip install --upgrade playwright
playwright install chromium

# 验证安装
playwright --version
```

### 问题3: 本地检索失败

**可能原因**:
- 数据库表未创建
- 数据库连接失败
- 没有导入数据

**解决方案**:
```bash
# 检查数据库表
docker exec -it athena-postgres psql -U athena -d patent_db -c "\d patents"

# 检查数据量
docker exec -it athena-postgres psql -U athena -d patent_db -c "SELECT COUNT(*) FROM patents;"

# 如果没有数据，需要先导入
```

---

## 📚 相关文档

- **架构设计**: `docs/reports/PATENT_TOOLS_UNIFIED_INTERFACE_COMPLETE_20260419.md`
- **实现验证**: `docs/reports/PATENT_TOOLS_IMPLEMENTATION_VERIFIED_20260419.md`
- **工具清理**: `docs/reports/PATENT_TOOLS_CLEANUP_COMPLETE_20260419.md`
- **测试报告**: `docs/reports/PATENT_INTERFACES_TEST_COMPLETE_20260419.md`

---

## 💡 最佳实践

1. **立即可用**: 优先使用PDF下载功能，无需配置
2. **批量操作**: 使用批量下载函数，提高效率
3. **错误处理**: 添加try-except处理网络异常
4. **进度跟踪**: 对于大量下载，添加进度显示
5. **数据验证**: 下载后验证文件大小和完整性

---

**维护者**: Athena平台团队
**最后更新**: 2026-04-19
**状态**: ✅ 核心功能可用
