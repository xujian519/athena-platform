# OpenClaw功能集成使用指南

> **版本**: v2.1.0
> **更新日期**: 2026-03-27
> **作者**: Athena平台团队

---

## 📋 概述

OpenClaw功能集成将专利撰写的9阶段流程引入Athena平台，包括：

- **9阶段完整流程** - 从发明理解到最终确认
- **审查员模拟** - 提交前自动质量检查
- **P0/P1/P2问题优先级** - 分级处理问题
- **长任务状态管理** - 支持暂停/恢复
- **授权概率估算** - 预测授权可能性

---

## 🚀 快速开始

### 1. API调用

#### 完整9阶段说明书撰写

```bash
curl -X POST "http://localhost:8005/api/v2/patent/draft/full" \
  -H "Content-Type: application/json" \
  -d '{
    "disclosure": "发明名称：一种智能床垫\n技术领域：智能家居\n...",
    "client": "测试客户",
    "enable_examiner_simulation": true
  }'
```

#### 说明书质量审查

```bash
curl -X POST "http://localhost:8005/api/v2/patent/draft/review" \
  -H "Content-Type: application/json" \
  -d '{
    "specification": {
      "case_id": "TEST-001",
      "invention_title": "一种智能床垫",
      "detailed_description": {"content": "..."}
    },
    "claims": {
      "claims": [
        {"claim_number": 1, "claim_type": "independent", "content": "..."}
      ]
    }
  }'
```

### 2. Python SDK

```python
from core.patent.ai_services.autospec_drafter import AutoSpecDrafter

# 创建撰写器
drafter = AutoSpecDrafter(
    llm_manager=None,  # 使用默认配置
    storage_dir="cases"
)

# 执行完整9阶段流程
result = await drafter.draft_specification_full(
    disclosure="技术交底书内容...",
    task_id="CASE-2026-001",
    client="客户名称",
    enable_examiner_simulation=True
)

# 查看结果
print(f"状态: {result.status}")
print(f"授权概率: {result.examiner_report.authorization_probability:.1%}")
print(f"P0问题: {result.examiner_report.p0_count}")
```

---

## 📊 9阶段流程

```
Phase 0: 发明理解 (invention_understanding)
    ↓ 解析技术交底书，提取核心创新点
Phase 1: 现有技术检索 (prior_art_search)
    ↓ 检索对比文件
Phase 2: 对比分析 (comparison_analysis)
    ↓ 分析差异点
Phase 3: 发明点确定 (inventive_point)
    ↓ 确定保护策略
Phase 4: 说明书撰写 (specification_drafting)
    ↓ 撰写各章节
Phase 5: 权利要求撰写 (claims_drafting)
    ↓ 生成权利要求
Phase 6: 审查员模拟 (examiner_simulation) ← 新增
    ↓ 自我审查，输出P0/P1/P2问题
Phase 7: 修改完善 (modification) ← 新增
    ↓ 基于审查结果修改
Phase 8: 最终确认 (final_confirmation)
    ✓ 输出完整文件
```

---

## 🔧 任务状态管理

### 创建任务

```python
from core.patent.task_state_manager import TaskStateManager

manager = TaskStateManager(storage_dir="cases")
task = manager.create_task(
    task_id="CASE-2026-001",
    client="客户名称"
)
```

### 暂停/恢复任务

```python
# 暂停
manager.pause_task("CASE-2026-001", reason="等待客户确认")

# 恢复
manager.resume_task("CASE-2026-001")
```

### 查看进度

```python
progress = manager.get_progress("CASE-2026-001")
print(f"进度: {progress['progress_percentage']}")
print(f"当前阶段: {progress['current_phase_name']}")
```

### API端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v2/patent/tasks` | GET | 任务列表 |
| `/api/v2/patent/tasks/{task_id}` | GET | 任务详情 |
| `/api/v2/patent/tasks/{task_id}/pause` | POST | 暂停任务 |
| `/api/v2/patent/tasks/{task_id}/resume` | POST | 恢复任务 |
| `/api/v2/patent/tasks/{task_id}` | DELETE | 删除任务 |

---

## 📝 质量审查器

### 使用方式

```python
from core.patent.specification_quality_reviewer import (
    SpecificationQualityReviewer
)

reviewer = SpecificationQualityReviewer()

# 执行审查
report = reviewer.review(
    specification={
        "case_id": "TEST-001",
        "invention_title": "一种智能床垫",
        "detailed_description": {"content": "..."},
        "invention_content": {"content": "..."}
    },
    claims={
        "claims": [
            {"claim_number": 1, "claim_type": "independent", "content": "..."}
        ]
    },
    prior_art=[  # 可选
        {"document_number": "CN123456", "abstract": "..."}
    ]
)

# 查看结果
print(f"整体风险: {report.overall_risk.value}")
print(f"授权概率: {report.authorization_probability:.1%}")
print(f"P0问题: {report.p0_count}")
print(f"P1问题: {report.p1_count}")

# 输出Markdown报告
print(report.to_markdown())
```

### 审查维度

| 维度 | 检查内容 | 法条依据 |
|------|---------|---------|
| 新颖性 | 与对比文件相似度 | A22.2 |
| 创造性 | 技术特征差异 | A22.3 |
| 公开充分性 | 实施方式完整性 | A26.3 |
| 权利要求清楚性 | 不确定表述检测 | A26.4 |
| 权利要求支持性 | 说明书覆盖检查 | A26.4 |
| 形式问题 | 格式规范性 | 实施细则 |

### 问题优先级

| 优先级 | 说明 | 处理建议 |
|--------|------|---------|
| **P0** | 阻断性问题 | 必须修改后才能提交 |
| **P1** | 重要问题 | 强烈建议修改 |
| **P2** | 可选优化 | 建议优化 |

---

## 📁 数据结构

### 技术特征

```python
from core.patent.data_structures import (
    TechnicalFeature,
    FeatureType
)

feature = TechnicalFeature(
    id="F1",
    description="压力传感器",
    feature_type=FeatureType.ESSENTIAL,
    component="床垫主体",
    function="检测睡姿"
)
```

### 问题-特征-效果三元组

```python
from core.patent.data_structures import ProblemFeatureEffect

triplet = ProblemFeatureEffect(
    id="T1",
    technical_problem="无法准确监测睡姿",
    technical_features=[feature],
    technical_effects=["实现精准睡姿监测"]
)
```

### 发明理解

```python
from core.patent.data_structures import (
    InventionUnderstanding,
    InventionType
)

understanding = InventionUnderstanding(
    invention_title="一种智能床垫",
    invention_type=InventionType.DEVICE,
    technical_field="智能家居",
    core_innovation="基于压力传感器的睡姿监测",
    triplets=[triplet],
    essential_features=[feature],
    confidence_score=0.85
)
```

---

## 🧪 测试

### 运行单元测试

```bash
# 运行所有OpenClaw集成测试
pytest tests/unit/patent/test_opencraw_integration.py -v

# 运行特定测试类
pytest tests/unit/patent/test_opencraw_integration.py::TestTaskStateManager -v

# 运行特定测试
pytest tests/unit/patent/test_opencraw_integration.py::TestTaskStateManager::test_create_task -v
```

### 测试覆盖率

```bash
pytest tests/unit/patent/test_opencraw_integration.py \
  --cov=core.patent.task_state_manager \
  --cov=core.patent.specification_quality_reviewer \
  --cov-report=html
```

---

## ⚙️ 配置

### 模型配置

```python
# autospec_drafter.py 中的模型配置
MODEL_CONFIG = {
    "understanding": {
        "model": "qwen3.5",
        "provider": "ollama",
        "temperature": 0.3
    },
    "generation": {
        "model": "deepseek-reasoner",
        "provider": "deepseek",
        "temperature": 0.3
    },
    "quality_check": {
        "model": "qwen3.5",
        "provider": "ollama",
        "temperature": 0.2
    }
}
```

### 存储配置

```python
# 任务状态存储目录
storage_dir = "cases"  # 默认

# 自定义存储目录
manager = TaskStateManager(storage_dir="/path/to/storage")
```

---

## 🔗 相关文档

- [专利撰写业务流程知识图谱](../business-workflows/knowledge-graph-patent-drafting.md)
- [质量评估模板](../templates/quality-assessment-template.md)
- [OpenClaw功能引入报告](../reports/OPENCLAW_FEATURES_MIGRATION_REPORT.md)
- [代码质量检查报告](../reports/NEW_CODE_QUALITY_REPORT.md)

---

## 📞 支持

如有问题，请联系Athena平台团队。

---

*最后更新: 2026-03-27*
