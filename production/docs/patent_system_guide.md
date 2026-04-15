# 专利复审无效知识图谱和向量库系统

## 系统概述

本系统专门针对专利复审和无效宣告决策构建知识图谱和向量数据库，提供专业的专利分析和检索能力。

## 目录结构

```
production/
├── dev/scripts/
│   ├── patent_review_invalid_builder.py    # 知识图谱构建器
│   ├── patent_vector_builder.py            # 向量库构建器
│   └── backup_existing_data.py            # 数据备份脚本
├── data/
│   ├── processed/                          # 处理后的数据
│   ├── metadata/                           # 元数据
│   ├── knowledge_graph/                    # 知识图谱数据
│   └── vector_db/                           # 向量数据库
└── docs/
    └── patent_system_guide.md             # 本文档

dev/tools/
└── patent_data/                            # 专利原始数据
    ├── patent_review/                       # 专利复审决定
    ├── invalid_decision/                    # 无效宣告决定
    ├── evidence/                            # 证据材料
    ├── prior_art/                          # 对比文件/现有技术
    ├── technical_analysis/                 # 技术分析报告
    └── ipc_classification/                  # IPC分类表
```

## 数据类型说明

### 1. 专利复审决定 (patent_review/)
- 复审请求书
- 复审决定通知书
- 复审程序文档

### 2. 无效宣告决定 (invalid_decision/)
- 无效宣告请求书
- 无效宣告决定
- 口头审理记录

### 3. 证据材料 (evidence/)
- 技术证据
- 证人证言
- 专家意见

### 4. 对比文件 (prior_art/)
- 现有技术文献
- 在先专利
- 公开出版物

### 5. 技术分析 (technical_analysis/)
- 技术特征分析
- 对比分析报告
- 侵权分析报告

## 实体类型

- **PATENT**: 专利
- **APPLICATION**: 专利申请
- **CLAIM**: 权利要求
- **PRIOR_ART**: 对比文件/现有技术
- **DECISION**: 决定
- **EVIDENCE**: 证据
- **LEGAL_BASIS**: 法律依据
- **REVIEWER**: 审查员
- **APPLICANT**: 申请人
- **IPC_CLASS**: IPC分类
- **TECH_FIELD**: 技术领域
- **NOVELTY**: 新颖性
- **INVENTIVE_STEP**: 创造性
- **INDUSTRIAL_APPLICABILITY**: 实用性

## 关系类型

- **HAS_CLAIM**: 包含权利要求
- **CITES_PRIOR_ART**: 引用对比文件
- **BASED_ON**: 基于证据
- **ACCORDING_TO**: 根据法律依据
- **DECLARES**: 宣告（无效/有效）
- **REVIEWS**: 审查
- **INVALIDATES**: 无效
- **MAINTAINS**: 维持（有效）
- **CHALLENGES**: 挑战
- **PROVES**: 证明

## 构建步骤

### 1. 数据准备
将专利相关文档放入对应目录：
```bash
# 示例：将复审决定JSON文件放入
cp 复审决定.json dev/tools/patent_data/patent_review/

# 示例：将无效宣告决定放入
cp 无效决定.txt dev/tools/patent_data/invalid_decision/
```

### 2. 构建知识图谱
```bash
cd production
python3 dev/scripts/patent_review_invalid_builder.py
```

### 3. 构建向量库
```bash
cd production
python3 dev/scripts/patent_vector_builder.py
```

### 4. 导入数据
- 向量数据：导入Qdrant
- 知识图谱：导入NebulaGraph

## 查询示例

### 1. 专利有效性查询
```
查询：专利CN202310000000.0的新颖性争议
预期：找到相关的对比文件和无效决定
```

### 2. 法律依据查询
```
查询：基于专利法第22条第3款的创造性判断
预期：找到相关决定和法律依据
```

### 3. 技术领域查询
```
查询：人工智能领域的专利创造性案例
预期：找到相关技术分析和决定
```

## 系统特点

1. **专业性**：针对专利复审无效流程设计
2. **全面性**：涵盖决定、证据、对比文件等
3. **智能化**：自动提取实体和关系
4. **可扩展**：支持添加新的数据类型

## 性能指标

- 支持百万级专利文档
- 毫秒级向量检索
- 复杂图谱查询
- 准确的实体关系识别

## 注意事项

1. 确保专利数据的完整性
2. 保持文档格式的一致性
3. 定期更新数据和索引
4. 备份重要数据

## 后续优化

1. 集成专业专利分析模型
2. 添加专利法律知识库
3. 支持多语言专利文档
4. 增强可视化分析功能