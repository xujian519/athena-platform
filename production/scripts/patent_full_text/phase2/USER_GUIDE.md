# 专利全文本处理系统 - 用户操作手册

**Athena平台 - Phase 2 专利处理管道**

版本: 1.0.0
更新时间: 2025-12-25

---

## 目录

1. [系统概述](#系统概述)
2. [快速开始](#快速开始)
3. [配置管理](#配置管理)
4. [功能模块](#功能模块)
5. [使用示例](#使用示例)
6. [故障排除](#故障排除)
7. [最佳实践](#最佳实践)

---

## 系统概述

### 架构图

```
专利PDF → PDF提取 → 权利要求解析 → 向量化(Qdrant) → 知识图谱(NebulaGraph) → PostgreSQL更新
   ↓         ↓          ↓              ↓                  ↓                  ↓
 原始文件   结构化文本    解析结果       密集+稀疏向量        实体关系网络        完整记录
```

### 核心功能

| 模块 | 功能 | 输出 |
|------|------|------|
| 专利下载 | 从Google Patents下载PDF | PDF文件 |
| PDF提取 | 提取结构化文本内容 | 标题、摘要、权利要求、说明书 |
| 权利要求解析 | 解析独立/从属权利要求 | 结构化权利要求数据 |
| 向量化 | BGE模型生成1024维向量（BGE-M3） | 密集向量 + 稀疏向量(BM25) |
| 知识图谱构建 | 构建专利实体关系网络 | 顶点、边 |
| 数据库更新 | 同步处理结果到PostgreSQL | 完整记录 |

### 技术栈

- **Python**: 3.10+
- **向量模型**: BGE-base-zh-v1.5 (1024维（BGE-M3）)
- **向量数据库**: Qdrant
- **图数据库**: NebulaGraph
- **关系数据库**: PostgreSQL

---

## 快速开始

### 1. 环境准备

```bash
# 确保Python 3.10+
python3 --version

# 安装依赖
pip install pdfplumber PyPDF2 sentence-transformers psycopg2-binary nebula3 qdrant-client requests
```

### 2. 数据库启动

```bash
# Qdrant向量数据库
docker run -p 6333:6333 qdrant/qdrant

# NebulaGraph图数据库
docker run -p 9669:9669 -p 9668:9668 vesoft/nebula-graph

# PostgreSQL
brew services start postgresql@14
```

### 3. 基础使用

```python
from production.scripts.patent_full_text.phase2.pipeline import PatentFullTextPipeline

# 创建处理管道
pipeline = PatentFullTextPipeline()

# 处理单个PDF
result = pipeline.process_pdf(
    pdf_path="/path/to/patent.pdf",
    metadata={
        "patent_number": "CN112233445A",
        "patent_name": "一种智能路障规避方法"
    }
)

print(f"完成率: {result.completion_rate}%")
```

---

## 配置管理

### 配置优先级

1. **环境变量** (最高优先级)
2. **配置文件** (~/.athena/patent_phase2_config.yaml)
3. **默认值** (代码中的默认配置)

### 环境变量配置

```bash
# Qdrant配置
export QDRANT_HOST="localhost"
export QDRANT_PORT="6333"
export QDRANT_COLLECTION="patent_full_text"

# NebulaGraph配置
export NEBULA_HOSTS="127.0.0.1:9669"
export NEBULA_USERNAME="root"
export NEBULA_PASSWORD="xiaonuo@Athena"
export NEBULA_SPACE="patent_full_text"

# PostgreSQL配置
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_DATABASE="patent_db"
export POSTGRES_USER="xujian"
export POSTGRES_PASSWORD="xiaonuo@Athena"

# BGE模型配置
export BGE_MODEL_PATH="/path/to/bge-base-zh-v1.5"
export BGE_DEVICE="cpu"  # cpu, cuda, mps
```

### YAML配置文件

创建 `~/.athena/patent_phase2_config.yaml`:

```yaml
qdrant:
  host: localhost
  port: 6333
  collection_name: patent_full_text
  vector_size = 1024  # BGE-M3向量维度（已更新）
  distance: COSINE
  enable_sparse: true

nebula:
  hosts: 127.0.0.1:9669
  username: root
  password: xiaonuo@Athena
  space_name: patent_full_text

postgresql:
  host: localhost
  port: 5432
  database: patent_db
  user: xujian
  password: xiaonuo@Athena

bge_model:
  model_path: /path/to/"BAAI/bge-m3"
  device: cpu
  chunk_size: 500
  chunk_overlap: 50

pdf_processor:
  pdf_output_dir: /Users/xujian/apps/apps/patents/PDF
  text_output_dir: /Users/xujian/apps/apps/patents/text
  preferred_backend: pdfplumber
```

### 代码中使用配置

```python
from production.scripts.patent_full_text.phase2.config import get_config
from production.scripts.patent_full_text.phase2.pipeline import PatentFullTextPipeline

# 获取配置
config = get_config()

# 使用配置创建管道
pipeline = PatentFullTextPipeline(config=config)
```

---

## 功能模块

### 1. 专利下载

```python
from production.scripts.patent_full_text.phase2.patent_downloader_client import PatentDownloaderClient

# 创建下载器
client = PatentDownloaderClient(output_dir="/Users/xujian/apps/apps/patents/PDF")

# 下载单个专利
result = client.download_patent("CN112233445A")
print(f"下载成功: {result['success']}")
print(f"文件路径: {result['file_path']}")

# 批量下载
batch_result = client.download_patents([
    "CN112233445A",
    "US8460931B2",
    "WO2013078254A1"
])
print(f"成功: {batch_result['successful']}/{batch_result['total']}")

# 获取专利信息
info = client.get_patent_info("CN112233445A")
print(f"标题: {info['title']}")
print(f"申请人: {info['assignee']}")
```

### 2. PDF文本提取

```python
from production.scripts.patent_full_text.phase2.pdf_extractor import PDFExtractor

extractor = PDFExtractor()

# 提取PDF内容
content = extractor.extract_pdf("/path/to/patent.pdf")

print(f"标题: {content.title}")
print(f"摘要: {content.abstract[:100]}...")
print(f"权利要求数量: {len(content.claims)}")
```

### 3. 权利要求解析

```python
from production.scripts.patent_full_text.phase2.claim_parser import ClaimParser

parser = ClaimParser()

# 解析权利要求
parsed = parser.parse(claims_text)

print(f"独立权利要求: {parsed.independent_count}")
print(f"从属权利要求: {parsed.dependent_count}")
print(f"技术类别: {parsed.technical_category}")

# 遍历权利要求
for claim in parsed.independent_claims:
    print(f"权利要求{claim.claim_number}: {claim.text[:50]}...")
```

### 4. 向量化处理

```python
from production.scripts.patent_full_text.phase2.vector_processor import BGEVectorizer

# 创建向量化器
vectorizer = BGEVectorizer(
    collection_name="patent_full_text",
    enable_hybrid=True  # 启用混合检索
)

# 向量化专利文本
result = vectorizer.vectorize_patent(
    patent_number="CN112233445A",
    title="一种智能路障规避方法",
    abstract="本发明公开了一种...",
    claims=["1. 一种方法...", "2. 根据权利要求1..."],
    description="具体实施方式..."
)

print(f"向量ID: {result.vector_id}")
print(f"分块数量: {result.chunk_count}")
```

### 5. 知识图谱构建

```python
from production.scripts.patent_full_text.phase2.kg_builder import PatentKGBuilder

# 构建知识图谱
builder = PatentKGBuilder()

result = builder.build_patent_kg(
    patent_number="CN112233445A",
    patent_name="一种智能路障规避方法",
    application_number="CN202110001234",
    applicant="上海思寒环保科技有限公司",
    inventor="张三;李四",
    ipc_main_class="G06F",
    abstract="本发明公开了一种...",
    claims_text="1. 一种方法..."
)

print(f"创建顶点: {result.vertices_created}")
print(f"创建边: {result.edges_created}")
```

### 6. 完整处理管道

```python
from production.scripts.patent_full_text.phase2.pipeline import PatentFullTextPipeline

# 创建管道
pipeline = PatentFullTextPipeline()

# 处理单个PDF
result = pipeline.process_pdf(
    pdf_path="/Users/xujian/apps/apps/patents/PDF/CN112233445A.pdf",
    metadata={
        "patent_number": "CN112233445A",
        "patent_name": "一种智能路障规避方法",
        "application_number": "CN202110001234"
    }
)

# 检查结果
if result.success:
    print(f"✅ 处理成功")
    print(f"   PDF提取: {'✅' if result.pdf_extracted else '❌'}")
    print(f"   权利要求解析: {'✅' if result.claims_parsed else '❌'}")
    print(f"   向量化: {'✅' if result.vectorized else '❌'}")
    print(f"   知识图谱: {'✅' if result.kg_built else '❌'}")
    print(f"   数据库更新: {'✅' if result.db_updated else '❌'}")
    print(f"   完成率: {result.completion_rate:.1f}%")
else:
    print(f"❌ 处理失败: {result.error_message}")

# 批量处理
batch_results = pipeline.process_batch([
    "/Users/xujian/apps/apps/patents/PDF/CN112233445A.pdf",
    "/Users/xujian/apps/apps/patents/PDF/US8460931B2.pdf"
])

for result in batch_results:
    print(f"{result.patent_number}: {result.completion_rate:.1f}%")
```

---

## 使用示例

### 示例1: 完整流程

```python
import sys
sys.path.insert(0, "/Users/xujian/Athena工作平台")

from production.scripts.patent_full_text.phase2.patent_downloader_client import PatentDownloaderClient
from production.scripts.patent_full_text.phase2.pipeline import PatentFullTextPipeline

# 1. 下载专利PDF
downloader = PatentDownloaderClient()
download_result = downloader.download_patent("CN112233445A")

if download_result["success"]:
    pdf_path = download_result["file_path"]

    # 2. 创建处理管道
    pipeline = PatentFullTextPipeline()

    # 3. 处理PDF
    result = pipeline.process_pdf(
        pdf_path=pdf_path,
        metadata={
            "patent_number": "CN112233445A",
            "patent_name": "一种智能路障规避方法"
        }
    )

    print(f"处理完成: {result.completion_rate:.1f}%")
```

### 示例2: 使用配置文件

```python
import os
# 设置环境变量
os.environ["QDRANT_HOST"] = "192.168.1.100"
os.environ["NEBULA_HOSTS"] = "192.168.1.100:9669"

from production.scripts.patent_full_text.phase2.config import get_config
from production.scripts.patent_full_text.phase2.pipeline import PatentFullTextPipeline

# 获取配置（会自动合并环境变量）
config = get_config()

# 创建管道
pipeline = PatentFullTextPipeline(config=config)

# 处理PDF
result = pipeline.process_pdf(pdf_path, metadata)
```

### 示例3: 向量检索

```python
from production.scripts.patent_full_text.phase2.vector_processor import BGEVectorizer
from qdrant_client import QdrantClient

# 创建向量化器
vectorizer = BGEVectorizer()

# 生成查询向量
query_text = "人工智能图像识别方法"
query_vector = vectorizer.model.encode(query_text)

# 搜索相似专利
client = QdrantClient(url="http://localhost:6333")
search_result = client.search(
    collection_name="patent_full_text",
    query_vector=query_vector,
    limit=5
)

for hit in search_result:
    print(f"专利号: {hit.payload['patent_number']}")
    print(f"相似度: {hit.score:.3f}")
```

---

## 故障排除

### 问题1: BGE模型找不到

**症状**: `BGE model path does not exist`

**解决方案**:
```python
# 检查模型路径
from pathlib import Path
model_path = "/path/to/bge-base-zh-v1.5"
print(Path(model_path).exists())

# 下载模型
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('shibing624/text2vec-base-chinese')
model.save(model_path)
```

### 问题2: Qdrant连接失败

**症状**: `Connection refused to Qdrant`

**解决方案**:
```bash
# 检查Qdrant是否运行
curl http://localhost:6333/collections

# 启动Qdrant
docker run -p 6333:6333 qdrant/qdrant
```

### 问题3: NebulaGraph连接超时

**症状**: `NebulaGraph connection timeout`

**解决方案**:
```bash
# 检查NebulaGraph状态
docker ps | grep nebula

# 重新启动NebulaGraph
docker restart <container_id>
```

### 问题4: PostgreSQL连接失败

**症状**: `FATAL: database "patent_db" does not exist`

**解决方案**:
```bash
# 创建数据库
psql -U xujian -c "CREATE DATABASE patent_db;"

# 创建表（参考schema.sql）
psql -U xujian -d patent_db -f schema.sql
```

### 问题5: PDF提取失败

**症状**: `PDF extraction failed`

**解决方案**:
```python
# 尝试不同的后端
extractor = PDFExtractor(preferred_backend="pypdf2")
content = extractor.extract_pdf(pdf_path)

# 或检查PDF是否损坏
import PyPDF2
with open(pdf_path, 'rb') as f:
    reader = PyPDF2.PdfReader(f)
    print(f"页数: {len(reader.pages)}")
```

---

## 最佳实践

### 1. 配置管理

- 使用环境变量管理敏感信息（密码）
- 使用YAML文件管理非敏感配置
- 定期备份配置文件

### 2. 批量处理

```python
# 使用批处理接口提高效率
pipeline = PatentFullTextPipeline()

# 限制并发数避免内存溢出
batch_size = 10
for i in range(0, len(pdf_list), batch_size):
    batch = pdf_list[i:i+batch_size]
    results = pipeline.process_batch(batch)
```

### 3. 错误处理

```python
# 启用继续处理模式
config.processing.continue_on_error = True
pipeline = PatentFullTextPipeline(config=config)

# 检查失败原因
for result in results:
    if not result.success:
        print(f"{result.patent_number}: {result.error_message}")
```

### 4. 性能优化

- 使用本地BGE模型而非API
- 启用GPU加速（`BGE_DEVICE=cuda`）
- 调整`chunk_size`平衡精度和性能
- 使用Qdrant批量插入

### 5. 监控日志

```python
# 设置日志级别
import logging
logging.basicConfig(level=logging.DEBUG)

# 保存日志到文件
config.processing.log_file = "/path/to/pipeline.log"
```

---

## 附录

### A. 配置文件模板

```yaml
# ~/.athena/patent_phase2_config.yaml
qdrant:
  host: localhost
  port: 6333
  collection_name: patent_full_text

nebula:
  hosts: 127.0.0.1:9669
  username: root
  password: your_password
  space_name: patent_full_text

postgresql:
  host: localhost
  port: 5432
  database: patent_db
  user: xujian
  password: your_password

bge_model:
  model_path: /path/to/"BAAI/bge-m3"
  device: cpu
  chunk_size: 500
  chunk_overlap: 50
```

### B. 常用命令

```bash
# 运行单元测试
python3 /Users/xujian/Athena工作平台/production/dev/scripts/patent_full_text/phase2/test_units.py

# 检查配置
python3 /Users/xujian/Athena工作平台/production/dev/scripts/patent_full_text/phase2/config.py

# 快速测试
python3 /Users/xujian/Athena工作平台/production/dev/scripts/patent_full_text/phase2/quick_test.py
```

### C. 相关文档

- [配置管理模块](./config.py)
- [处理管道](./pipeline.py)
- [单元测试](./test_units.py)
- [Phase 2完成报告](./PHASE2_COMPLETION_REPORT.md)

---

**文档版本**: 1.0.0
**最后更新**: 2025-12-25
**维护团队**: Athena平台团队
