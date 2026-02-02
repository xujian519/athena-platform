# 小娜提示词系统

> **版本**: v2.0
> **更新日期**: 2025-12-26
> **设计者**: 小诺·双鱼公主 v4.0.0

---

## 🌟 系统概述

小娜是一个基于**四层提示词架构**的专利法律AI助手，具备完整的**人机协作(HITL)**机制。

### 核心特性

- 🏗️ **四层提示词架构**: L1基础层 + L2数据层 + L3能力层 + L4业务层
- 🎯 **10大核心能力**: 法律检索、技术分析、文书撰写、公开审查、清楚性审查、创造性分析、现有技术识别、答复撰写、形式审查、综合分析
- 📋 **9个业务场景**: 专利撰写5任务 + 意见答复4任务
- 🤝 **HITL人机协作**: 关键决策点需要人工确认
- 🔗 **平台数据集成**: Qdrant + NebulaGraph + PostgreSQL

---

## 📁 文件结构

```
prompts/
├── foundation/                          # L1: 基础层
│   ├── xiaona_l1_foundation.md          # 小娜身份定义与核心原则
│   └── hitl_protocol.md                 # HITL人机协作协议
│
├── data/                                # L2: 数据层
│   ├── xiaona_l2_overview.md            # 数据层概述
│   ├── xiaona_l2_vectors.md             # 向量数据源
│   ├── xiaona_l2_graph.md               # 知识图谱数据源
│   ├── xiaona_l2_database.md            # 关系数据库数据源
│   └── xiaona_l2_search.md              # 检索策略
│
├── capability/                          # L3: 能力层
│   ├── cap01_retrieval.md               # 能力1: 法律检索能力
│   ├── cap02_analysis.md                # 能力2: 技术分析能力
│   ├── cap03_writing.md                 # 能力3: 文书撰写能力
│   ├── cap04_disclosure_exam.md         # 能力4: 说明书充分公开审查能力
│   ├── cap04_inventive.md               # 能力4: 创造性分析能力
│   ├── cap05_clarity_exam.md            # 能力5: 权利要求书清楚性审查能力
│   ├── cap05_invalid.md                 # 能力5: 无效分析能力
│   ├── cap06_prior_art_ident.md         # 能力6: 现有技术识别能力
│   ├── cap06_response.md                # 能力6: 答复撰写能力
│   └── cap07_formal_exam.md             # 能力7: 形式审查能力
│
├── business/                            # L4: 业务层
│   ├── task_1_1_understand_disclosure.md # 任务1.1: 理解技术交底书
│   ├── task_1_2_prior_art_search.md      # 任务1.2: 现有技术调研与对比分析
│   ├── task_1_3_write_specification.md   # 任务1.3: 撰写说明书
│   ├── task_1_4_write_claims.md          # 任务1.4: 撰写权利要求书
│   ├── task_1_5_write_abstract.md        # 任务1.5: 撰写摘要和整理申请文件
│   ├── task_2_1_analyze_office_action.md # 任务2.1: 解读审查意见通知书
│   ├── task_2_2_analyze_rejection.md     # 任务2.2: 分析驳回理由
│   ├── task_2_3_develop_response_strategy.md # 任务2.3: 制定答复策略
│   └── task_2_4_write_response.md        # 任务2.4: 撰写答复文件
│
├── IMPLEMENTATION_SUMMARY.md            # 实现总结
└── README.md                            # 本文件
```

---

## 🏗️ 四层提示词架构

```
┌─────────────────────────────────────────────────────────────┐
│                    L4: 业务层 (Business)                     │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ 专利撰写 (5任务) │  │ 意见答复 (4任务) │                  │
│  └─────────────────┘  └─────────────────┘                  │
├─────────────────────────────────────────────────────────────┤
│                    L3: 能力层 (Capability)                   │
│  法律检索 | 技术分析 | 文书撰写 | 公开审查 | 创造性分析...   │
├─────────────────────────────────────────────────────────────┤
│                    L2: 数据层 (Data Layer)                   │
│  Qdrant向量库 | NebulaGraph图谱 | PostgreSQL专利库          │
├─────────────────────────────────────────────────────────────┤
│                    L1: 基础层 (Foundation)                   │
│  身份定义 | 核心原则 | 工作模式 | 输出规范                  │
├─────────────────────────────────────────────────────────────┤
│                    HITL: 人机协作协议                        │
│  决策确认 | 中断回退 | 偏好学习 | 进度可视化                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 基础使用

```python
from production.services.xiaona_agent import XiaonaAgent

# 初始化代理
agent = XiaonaAgent()

# 切换到专利撰写模式
print(agent.switch_scenario("patent_writing"))

# 处理查询
response = agent.query(
    user_message="帮我分析这个技术交底书",
    scenario="patent_writing"
)

print(response["response"])
```

### 平台数据集成

```python
from production.services.xiaona_integration_demo import XiaonaPlatformIntegration

integration = XiaonaPlatformIntegration()

response = integration.execute_task_with_platform_data(
    task_type="patent_writing",
    user_input="检索现有技术",
    platform_context={"task": "task_1_2"}
)

# 查看平台检索结果
if "platform_data" in response:
    print(response["platform_data"])
```

---

## 📊 平台数据资产

小娜可以访问Athena平台的以下数据源：

### Qdrant向量数据库

| 集合名称 | 记录数 | 用途 |
|---------|-------|------|
| patent_rules_complete | 2,694 | 专利法条向量检索 |
| patent_decisions | 308,881 | 复审无效决定语义检索 |
| laws_articles | 53,903 | 法律条文向量检索 |
| patent_guidelines | 376 | 专利审查指南检索 |
| legal_knowledge | 396 | 法律知识向量检索 |
| ai_family_shared_memory | 21 | AI家族共享记忆 |
| multimodal_vectors | 待完善 | 多模态向量检索 |

### NebulaGraph知识图谱

| 图名称 | 节点数 | 边数 | 用途 | 状态 |
|-------|-------|-----|------|------|
| patent_rules | 待导入 | 待导入 | 法条关系推理 | 🟡 导入中 |
| legal_kg | 22,372 | 71,314 | 法律概念关联 | ✅ 可用 |
| patent_kg | 部分导入 | 部分导入 | 专利实体关系 | 🟡 扩充中 |

### PostgreSQL专利数据库

| 数据库 | 记录数 | 用途 |
|-------|-------|------|
| patent_db | 28,036,796 | 中国专利精确检索 |

---

## 🎯 10大核心能力

### CAPABILITY_1: 法律检索能力
- 检索相关法条 (专利法、实施细则、审查指南)
- 检索复审无效决定
- 检索相关案例

### CAPABILITY_2: 技术分析能力
- 技术方案理解
- 创新点识别
- 技术问题分析

### CAPABILITY_3: 文书撰写能力
- 说明书撰写
- 权利要求书撰写
- 答复文件撰写

### CAPABILITY_4: 说明书充分公开审查能力 (A26.3)
- "清楚、完整、能够实现"评估
- 特殊领域要求 (化学/医药/生物)

### CAPABILITY_4: 创造性分析能力 (A22.3)
- 三步法应用
- 区别特征识别
- 技术启示判断

### CAPABILITY_5: 权利要求书清楚性审查能力 (A26.4)
- 模糊用语识别
- 引用关系检查
- 功能性限定分析

### CAPABILITY_5: 无效分析能力
- 无效理由分析
- 无效证据检索
- 无效策略制定

### CAPABILITY_6: 现有技术识别能力 (A23.5)
- "为公众所知"判断
- 公开状态判断
- 披露方式识别

### CAPABILITY_6: 答复撰写能力
- 答复策略实施
- 争辩理由撰写
- 修改建议提供

### CAPABILITY_7: 形式审查能力
- 形式要求检查
- 文件完整性审核
- 缺陷识别

---

## 📋 9个业务场景

### 场景1: 专利撰写

- **Task 1.1**: 理解技术交底书与提问准备
- **Task 1.2**: 现有技术调研与对比分析
- **Task 1.3**: 撰写说明书
- **Task 1.4**: 撰写权利要求书
- **Task 1.5**: 撰写摘要和整理申请文件

### 场景2: 意见答复

- **Task 2.1**: 解读审查意见通知书
- **Task 2.2**: 分析驳回理由
- **Task 2.3**: 制定答复策略
- **Task 2.4**: 撰写答复文件

---

## 🤝 HITL人机协作

### 协作原则

1. **父亲做决策**: 所有关键决策由用户（爸爸）做出
2. **小娜提建议**: AI提供分析、建议、方案选项
3. **确认机制**: 重要操作需要用户明确确认
4. **可中断**: 用户可以随时中断和回退

### 交互点类型

1. **决策确认点**: 需要用户做出选择
2. **信息收集点**: 需要用户提供更多信息
3. **审核确认点**: 需要用户审核输出结果
4. **偏好学习点**: 记录用户偏好
5. **进度展示点**: 展示任务进度

---

## 📈 性能指标

### 提示词规模

| 层级 | 字符数 | Token估算 | 优化后 |
|-----|-------|----------|--------|
| L1基础层 | 13,095 | ~3.3k | ~2.4k (27%压缩) |
| L2数据层 | 13 | ~0.01k | ~0.01k (已优化) |
| L3能力层 | 96,940 | ~24k | ~6.0k (75%压缩) |
| L4业务层 | 130,964 | ~33k | ~12.0k (64%压缩) |
| HITL协议 | 11,721 | ~2.9k | ~2.0k (31%压缩) |
| **原始总计** | **252,733** | **~63k** | - |
| **优化总计** | - | - | **~22.4k (64%压缩)** |

### 加载性能

- **首次加载**: ~3-5秒
- **缓存加载**: <0.5秒
- **场景切换**: <0.1秒

---

## 🔧 生产环境部署

### 相关文件

- **提示词加载器**: `production/services/xiaona_prompt_loader.py`
- **小娜代理**: `production/services/xiaona_agent.py`
- **集成演示**: `production/services/xiaona_integration_demo.py`
- **部署指南**: `production/XIAONA_PRODUCTION_GUIDE.md`

### 测试

```bash
# 测试提示词加载器
python3 production/services/xiaona_prompt_loader.py

# 测试小娜代理
python3 production/services/xiaona_agent.py

# 运行集成演示
python3 production/services/xiaona_integration_demo.py
```

---

## 📚 相关文档

- [Athena平台架构文档](../design/xiaona_implementation_blueprint.md)
- [生产环境部署指南](../production/XIAONA_PRODUCTION_GUIDE.md)
- [实现总结](./IMPLEMENTATION_SUMMARY.md)

---

## 📝 版本历史

### v2.0 (2025-12-26)

- ✅ 完成四层提示词架构设计
- ✅ 完成10大能力提示词 (12个文件)
- ✅ 完成9个业务场景提示词 (9个文件)
- ✅ 实现HITL人机协作协议
- ✅ 集成Athena平台数据源
- ✅ 实现提示词缓存机制
- ✅ 实现场景切换功能
- ✅ 实现对话历史管理
- ✅ 完成生产环境部署

---

## 👥 联系方式

- **设计者**: 小诺·双鱼公主 v4.0.0
- **邮箱**: xujian519@gmail.com
- **项目**: Athena工作平台

---

> **小娜** - 您的专利法律AI助手 🌟
>
> 让专利工作更高效、更专业、更智能！
