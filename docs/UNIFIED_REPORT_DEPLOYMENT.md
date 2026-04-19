# 统一报告服务部署文档

## 📚 目录

- [概述](#概述)
- [系统架构](#系统架构)
- [部署步骤](#部署步骤)
- [API使用指南](#api使用指南)
- [Python SDK使用](#python-sdk使用)
- [配置说明](#配置说明)
- [性能优化](#性能优化)
- [故障排查](#故障排查)

---

## 概述

### 什么是统一报告服务？

统一报告服务是Athena工作平台的核心报告生成系统，整合了：

- **Dolphin文档解析**: 90%+准确率的文档理解和转换
- **NetworkX技术分析**: 深度技术图谱和创新点识别
- **Athena报告生成**: AI驱动的专业报告生成

### 核心价值

```
Dolphin (格式保持) + NetworkX (技术深度) + Athena (专业报告)
                        ↓
              高质量专业分析报告
```

---

## 系统架构

### 技术栈

| 组件 | 技术 | 版本 |
|-----|------|------|
| **文档解析** | Dolphin (ByteDance) | v2.0 |
| **图分析** | NetworkX | 3.x |
| **报告生成** | Athena | v2.0 |
| **API框架** | FastAPI | 0.100+ |
| **模板引擎** | Jinja2 | 3.x |
| **格式转换** | Pandoc | 3.x |

### 工作流程

```
┌─────────────────────────────────────────────────────────┐
│                   文档输入                               │
│            (PDF, PNG, 数据)                              │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              阶段1: Dolphin解析                          │
│  • 图片/PDF → Markdown                                  │
│  • 90%+ 准确率                                           │
│  • 表格/公式专业识别                                      │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│            阶段2: NetworkX分析                           │
│  • 技术实体提取                                           │
│  • 技术关系构建                                           │
│  • 创新点识别                                             │
│  • 重要性评估 (PageRank/HITS)                            │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│            阶段3: Athena生成                              │
│  • 专业报告模板                                           │
│  • AI内容生成                                             │
│  • 质量控制                                               │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              阶段4: 多格式输出                            │
│  • Markdown                                              │
│  • DOCX (Word)                                           │
│  • JSON                                                  │
│  • HTML (可选)                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 部署步骤

### 1. 环境准备

#### 1.1 系统要求

```yaml
硬件要求:
  CPU: 4核心以上
  内存: 8GB以上 (推荐16GB)
  磁盘: 20GB可用空间
  GPU: 可选 (NVIDIA CUDA 或 Apple MPS)

软件要求:
  操作系统: macOS, Linux, Windows
  Python: 3.9+
  Node.js: 16+ (可选，用于前端)
```

#### 1.2 依赖安装

```bash
# 进入项目目录
cd /Users/xujian/Athena工作平台

# 安装Python依赖
pip install -e .

# 安装Dolphin依赖
pip install qwen-vl-utils
pip install torch torchvision torchaudio

# 安装Pandoc (用于格式转换)
brew install pandoc  # macOS
# 或
sudo apt-get install pandoc  # Linux
```

#### 1.3 Dolphin模型准备

```bash
# 模型应该已下载到以下位置
# /Users/xujian/Athena工作平台/Dolphin/hf_model/ByteDance/Dolphin-v2

# 如果未下载，执行：
cd /Users/xujian/Athena工作平台/Dolphin
huggingface-cli download ByteDance/Dolphin-v2 --local-dir ./hf_model/ByteDance/Dolphin-v2
```

### 2. 配置文件设置

#### 2.1 创建报告服务配置文件

创建 `config/reporting_config.yaml`:

```yaml
# 统一报告服务配置

# 服务配置
service:
  name: unified_report_service
  version: "2.0"
  debug: false
  log_level: INFO

# Dolphin配置
dolphin:
  enabled: true
  model_path: /Users/xujian/Athena工作平台/Dolphin/hf_model/ByteDance/Dolphin-v2
  device: auto  # auto, cuda, mps, cpu
  max_batch_size: 8
  cache_enabled: true

# NetworkX配置
networkx:
  enabled: true
  build_graph: true
  export_graph: true
  graph_format: gexf  # gexf, graphml, json

# Athena配置
athena:
  enabled: true
  model: gpt-4
  temperature: 0.7
  max_tokens: 4096
  template_dir: templates/reports

# 输出配置
output:
  default_formats:
    - markdown
    - docx
    - json
  base_dir: /Users/xujian/Athena工作平台/data/reports
  include_original_markdown: true
  include_technical_graph: true
  include_quality_metrics: true

# API配置
api:
  host: 0.0.0.0
  port: 8000
  workers: 4
  max_concurrent_tasks: 3

# 工作流配置
workflow:
  max_concurrent_tasks: 3
  task_timeout: 600  # 10分钟
  retry_failed_tasks: true
  max_retries: 2
```

### 3. 服务启动

#### 3.1 启动Dolphin文档解析服务

```bash
# 启动Dolphin服务 (端口8090)
bash services/start_dolphin_service.sh

# 验证服务状态
curl http://localhost:8090/health
```

#### 3.2 启动Athena主服务

```bash
# 启动Athena API服务 (端口8000)
cd /Users/xujian/Athena工作平台
python -m core.api.main

# 或使用uvicorn
uvicorn core.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 3.3 验证部署

```bash
# 检查统一报告服务健康状态
curl http://localhost:8000/api/v2/reports/health

# 预期输出:
{
  "status": "healthy",
  "service": "Unified Report Service",
  "version": "2.0",
  "report_service": true,
  "workflow_processor": true
}
```

---

## API使用指南

### 1. 从上传文件生成报告

#### 请求

```bash
curl -X POST "http://localhost:8000/api/v2/reports/generate/upload" \
  -F "file=@/path/to/document.pdf" \
  -F "report_type=patent_technical_analysis" \
  -F "output_formats=markdown,docx"
```

#### 响应

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "report_type": "patent_technical_analysis",
  "input_source": "document.pdf",
  "output_files": {
    "markdown": "/Users/xujian/Athena工作平台/data/reports/2026-01/document_20260116_123456.md",
    "docx": "/Users/xujian/Athena工作平台/data/reports/2026-01/document_20260116_123456.docx"
  },
  "processing_time": 45.23,
  "quality_score": 87.5,
  "generation_time": "2026-01-16T12:34:56"
}
```

### 2. 从文档路径生成报告

#### 请求

```bash
curl -X POST "http://localhost:8000/api/v2/reports/generate/document" \
  -F "document_path=/path/to/document.pdf" \
  -F "report_type=patent_technical_analysis" \
  -F "output_dir=/path/to/output"
```

### 3. 批量生成报告

#### 请求

```bash
curl -X POST "http://localhost:8000/api/v2/reports/batch" \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.pdf" \
  -F "files=@doc3.pdf" \
  -F "report_type=patent_technical_analysis" \
  -F "max_concurrent=3"
```

#### 响应

```json
{
  "status": "success",
  "data": {
    "batch_id": "batch_20260116_123456",
    "total_files": 3,
    "report_type": "patent_technical_analysis",
    "max_concurrent": 3,
    "message": "批量任务已提交，请使用 /tasks/{batch_id} 查询进度"
  }
}
```

### 4. 文档对比分析

#### 请求

```bash
curl -X POST "http://localhost:8000/api/v2/reports/compare" \
  -F "doc1_path=/path/to/doc1.pdf" \
  -F "doc2_path=/path/to/doc2.pdf"
```

### 5. 下载生成的报告

#### 请求

```bash
curl -O "http://localhost:8000/api/v2/reports/download/{task_id}/markdown"
curl -O "http://localhost:8000/api/v2/reports/download/{task_id}/docx"
```

### 6. 查询任务状态

#### 请求

```bash
curl "http://localhost:8000/api/v2/reports/tasks/{task_id}"
```

#### 响应

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2026-01-16T12:34:00",
  "started_at": "2026-01-16T12:34:05",
  "completed_at": "2026-01-16T12:34:50",
  "error": null,
  "processing_time": 45.23
}
```

---

## Python SDK使用

### 基础使用

```python
from core.reporting.unified_report_service import (
    UnifiedReportService,
    ReportType,
    ReportConfig,
)

# 创建服务
config = ReportConfig(
    enable_dolphin_parsing=True,
    enable_networkx_analysis=True,
    enable_ai_generation=True,
)

service = UnifiedReportService(config=config)

# 从文档生成报告
result = await service.generate_from_document(
    document_path="patent.pdf",
    report_type=ReportType.PATENT_TECHNICAL_ANALYSIS,
    output_dir="./reports",
)

# 查看结果
print(f"处理时间: {result.processing_time_seconds:.2f}秒")
print(f"质量分数: {result.quality_score:.2f}/100")
print(f"输出文件: {result.output_files}")
```

### 批量处理

```python
from core.reporting.workflow_processor import batch_generate_reports

# 批量生成报告
documents = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]

results = await batch_generate_reports(
    documents=documents,
    report_type=ReportType.PATENT_TECHNICAL_ANALYSIS,
    output_dir="./reports",
    max_concurrent=3,
)

for i, result in enumerate(results):
    print(f"报告{i+1}: {result.output_files['markdown']}")
```

### 文档对比

```python
# 对比两个文档
result = await service.compare_documents(
    doc1_path="doc1.pdf",
    doc2_path="doc2.pdf",
    output_dir="./comparison",
)

print(f"对比报告: {result.output_files['markdown']}")
```

### 自定义报告数据

```python
# 从数据直接生成报告（跳过Dolphin和NetworkX）
custom_data = {
    "title": "自定义专利分析",
    "technical_entities_count": 50,
    "innovation_points": [
        {
            "text": "核心创新点",
            "innovation_score": 0.85,
        }
    ],
}

result = await service.generate_from_data(
    data=custom_data,
    report_type=ReportType.PATENT_TECHNICAL_ANALYSIS,
)
```

---

## 配置说明

### 报告类型

| 类型 | 值 | 说明 |
|-----|---|------|
| 专利技术分析 | `patent_technical_analysis` | 完整的专利技术深度分析报告 |
| 专利对比 | `patent_comparison` | 两个专利的对比分析报告 |
| 法律意见书 | `legal_opinion` | 法律专业意见书 |
| OA答复 | `oa_response` | OA答复建议书 |
| 技术趋势 | `technical_trends` | 技术趋势分析报告 |
| 文档转换 | `document_conversion` | 简单的文档格式转换 |

### 输出格式

| 格式 | 值 | 说明 |
|-----|---|------|
| Markdown | `markdown` | 标准Markdown格式 |
| Word文档 | `docx` | Microsoft Word格式 |
| PDF | `pdf` | PDF文档格式 |
| HTML | `html` | 网页HTML格式 |
| JSON | `json` | 结构化JSON数据 |

### 性能调优参数

```python
config = ReportConfig(
    # Dolphin配置
    dolphin_max_batch_size=8,  # 批处理大小 (1-16)
    # 值越大越快，但内存占用越高

    # NetworkX配置
    networkx_export_graph=True,  # 是否导出技术图谱
    # 导出图谱会增加处理时间

    # AI生成配置
    ai_temperature=0.7,  # 生成温度 (0.0-1.0)
    # 越低越确定，越高越随机

    ai_max_tokens=4096,  # 最大生成token数
    # 影响报告长度
)
```

---

## 性能优化

### 1. 批处理优化

```python
# 使用批量处理提高吞吐量
results = await batch_generate_reports(
    documents=document_list,
    max_concurrent=4,  # 根据硬件调整
)
```

### 2. 缓存启用

```python
# 启用Dolphin缓存
parser = DolphinDocumentParser(cache_enabled=True)
service = UnifiedReportService(dolphin_client=parser)
```

### 3. GPU加速

```bash
# 设置Dolphin使用GPU
export DOLPHIN_DEVICE=cuda  # NVIDIA
export DOLPHIN_DEVICE=mps    # Apple Silicon
```

### 4. 异步并发

```python
import asyncio

# 并发处理多个独立任务
tasks = [
    service.generate_from_document(doc, ReportType.PATENT_TECHNICAL_ANALYSIS)
    for doc in document_list
]

results = await asyncio.gather(*tasks)
```

---

## 故障排查

### 常见问题

#### 1. Dolphin服务无法启动

**问题**: `Error: [Errno 48] address already in use`

**解决**:
```bash
# 查找占用端口的进程
lsof -i :8090

# 杀死进程
kill -9 <PID>

# 重启服务
bash services/start_dolphin_service.sh
```

#### 2. 模型加载失败

**问题**: `No such file or directory: '...'`

**解决**:
```bash
# 检查模型路径
ls -la /Users/xujian/Athena工作平台/Dolphin/hf_model/ByteDance/Dolphin-v2

# 如模型不存在，重新下载
cd /Users/xujian/Athena工作平台/Dolphin
huggingface-cli download ByteDance/Dolphin-v2 \
    --local-dir ./hf_model/ByteDance/Dolphin-v2
```

#### 3. 内存不足

**问题**: `OutOfMemoryError` 或系统卡死

**解决**:
```python
# 减小批处理大小
config = ReportConfig(
    dolphin_max_batch_size=4,  # 从8减少到4
)

# 或禁用某些组件
config = ReportConfig(
    enable_networkx_analysis=False,  # 禁用NetworkX
    enable_ai_generation=False,      # 禁用AI生成
)
```

#### 4. 报告生成超时

**问题**: `TimeoutError` after long wait

**解决**:
```bash
# 增加超时时间
export ATHENA_REPORT_TIMEOUT=1200  # 20分钟

# 或简化报告
config = ReportConfig(
    enable_ai_generation=False,  # 跳过AI生成
    output_formats=["markdown"],  # 只输出Markdown
)
```

### 日志查看

```bash
# 查看Dolphin服务日志
tail -f /tmp/dolphin_service.log

# 查看Athena主服务日志
tail -f /tmp/athena-kg.log

# 查看统一报告服务日志
tail -f /tmp/unified_report_service.log
```

### 调试模式

```bash
# 启用调试模式
export ATHENA_DEBUG=true
export LOG_LEVEL=DEBUG

# 重启服务
python -m core.api.main
```

---

## 监控和维护

### 性能监控

```python
# 查看服务统计
from core.reporting.workflow_processor import HybridWorkflowProcessor

processor = HybridWorkflowProcessor()
stats = processor.statistics

print(f"总任务数: {stats.total_tasks}")
print(f"完成任务: {stats.completed_tasks}")
print(f"失败任务: {stats.failed_tasks}")
print(f"平均时间: {stats.average_processing_time:.2f}秒")
```

### 资源清理

```bash
# 清理临时文件
rm -rf /tmp/athena_uploads/*
rm -rf /tmp/athena_batch_uploads/*

# 清理旧报告（保留最近30天）
find /Users/xujian/Athena工作平台/data/reports -name "*.md" -mtime +30 -delete
```

---

## 总结

统一报告服务提供了完整的Dolphin + NetworkX + Athena混合工作流，可以：

- ✅ 高精度文档解析（90%+准确率）
- ✅ 深度技术分析（创新点识别、重要性评估）
- ✅ 专业报告生成（多种报告类型）
- ✅ 多格式输出（Markdown/Word/JSON）
- ✅ 批量处理支持
- ✅ API接口完整

通过本部署文档，您应该能够：
1. 成功部署统一报告服务
2. 使用API和Python SDK生成报告
3. 优化性能和排查问题

如有问题，请查看日志或联系技术支持。
