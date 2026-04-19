# 法律世界模型技能 (Legal World Model Skill)

## 📋 简介

本技能将Athena平台的法律世界模型封装为OpenClaw可调用的技能，提供智能法律问答能力。

### 核心特性

- **三层架构**: 基础法律层、专利专业层、司法案例层
- **混合检索**: 语义向量检索 + 知识图谱推理
- **智能推理**: 支持证据链生成和多跳法律推理
- **高精度**: 45万+向量点，29万+知识图谱节点

## 🚀 快速开始

### 1. 健康检查

```bash
# 检查法律世界模型服务状态
curl http://localhost:8000/health

# 预期输出
{
  "service": "雅典娜知识图谱系统",
  "status": "running",
  "version": "v2.0.0"
}
```

### 2. 命令行使用

```bash
# 进入技能目录
cd /Users/xujian/Athena工作平台/skills/legal-world-model

# 基础问答
python scripts/legal_qa_cli.py "专利侵权判定中如何确定等同特征？"

# 指定查询类型
python scripts/legal_qa_cli.py \
  "什么是专利法中的新颖性？" \
  --query-type statute_query

# 启用推理链
python scripts/legal_qa_cli.py \
  "分析这个技术方案是否具备创造性" \
  --enable-reasoning \
  --max-evidence 15

# JSON输出
python scripts/legal_qa_cli.py \
  "查找关于等同侵权的相关案例" \
  --json

# 指定目标数据层
python scripts/legal_qa_cli.py \
  "专利复审期限是多少？" \
  --target-layers layer1 layer2

# 查看帮助
python scripts/legal_qa_cli.py --help
```

### 3. Python API使用

```python
from skills.legal_world_model.scripts.legal_qa_cli import LegalWorldModelClient

# 初始化客户端
client = LegalWorldModelClient(
    api_url="http://localhost:8000",
    timeout=30
)

# 语义问答
result = client.ask(
    question="专利法中关于新颖性的规定是什么？",
    query_type="semantic_qa"
)

# 格式化输出
print(client.format_answer(result))

# 获取原始JSON
import json
print(json.dumps(result, ensure_ascii=False, indent=2))
```

### 4. REST API调用

```bash
# 智能问答
curl -X POST http://localhost:8000/api/v1/qa/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "专利复审程序中如何修改权利要求书？",
    "query_type": "procedure",
    "options": {
      "enable_reasoning": true,
      "max_evidence": 10
    }
  }'
```

## 📊 查询类型说明

| 查询类型 | 说明 | 适用场景 |
|---------|------|----------|
| `concept` | 概念解释 | 解释法律术语、概念定义 |
| `statute_query` | 法条查询 | 查询具体法条、法律条文 |
| `case_query` | 案例查询 | 查找类似案例、判例参考 |
| `comparison` | 对比分析 | 对比不同法律、案例 |
| `liability` | 责任认定 | 认定法律责任归属 |
| `procedure` | 程序问题 | 询问程序性规定 |
| `creativity` | 创造性判断 | 创造性分析 |
| `novelty` | 新颖性判断 | 新颖性分析 |
| `semantic_qa` | 语义问答 | 综合语义理解（默认）|

## 🏗️ 数据层说明

法律世界模型采用三层架构：

| 层级 | 名称 | 内容 | 数据量 |
|------|------|------|--------|
| Layer 1 | 基础法律层 | 民法典、民诉法等通用法律 + 司法解释 | ~10,000 文档 |
| Layer 2 | 专利专业层 | 专利法、审查指南 + 复审无效决定书 | ~15,000 文档 |
| Layer 3 | 司法案例层 | 专利侵权、权属纠纷等判决文书 | ~7,000 文档 |

## 👥 智能体配置

技能已配置给以下智能体：

### 小诺 (xiaonuo) - 平台总调度官
- **优先能力**: legal_world_model, scenario_planner
- **默认配置**:
  - query_type: semantic_qa
  - max_evidence: 15
  - enable_reasoning: true

### 小娜 (xiaona) - 知识产权法律专家
- **优先能力**: legal_world_model
- **默认配置**:
  - query_type: case_query
  - max_evidence: 20
  - target_layers: [layer2, layer3]
  - enable_reasoning: true

### 云熙 (yunxi) - IP管理专家
- **优先能力**: patent_retrieval
- **默认配置**:
  - query_type: statute_query
  - max_evidence: 10

## 📈 性能指标

| 指标 | 值 |
|--------|-----|
| 平均响应时间 | ~150ms |
| 成功率 | 95%+ |
| 缓存命中率 | 85% |
| 向量检索精度 | 89.7% |

## ⚙️ 注意事项

1. **服务依赖**: 需要先启动法律世界模型服务
   ```bash
   # 启动服务
   python core/legal_qa/legal_world_qa_system.py
   ```

2. **数据库连接**: 确保PostgreSQL、Qdrant、Neo4j服务正常运行

3. **查询复杂度**: 复杂推理问题可能需要3-5秒处理时间

4. **结果缓存**: 常见问题会被缓存，提升响应速度

## 🔗 相关技能

- [Patent Retrieval](../patent-retrieval/) - 专利检索技能
- [Prompt System](../prompt-system/) - 动态提示词系统
- [Scenario Planner](../scenario-planner/) - 场景规划器

## 📚 更多资源

- 法律世界模型架构: `core/legal_world_model/constitution.py`
- 健康检查: `core/legal_world_model/health_check.py`
- API文档: http://localhost:8000/docs
- 验证报告: `docs/reports/patent_retrieval_final_report.md`
