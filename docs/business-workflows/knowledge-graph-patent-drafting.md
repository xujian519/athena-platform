# 专利撰写业务流程 - 知识图谱

> 生成时间：2026-03-27
> 平台版本：Athena v2.1.0
> 业务场景：专利申请文件撰写

---

## 📊 完整图谱

```mermaid
graph TD
    %% 核心节点
    Root[专利撰写业务流程]

    %% 核心角色
    Xiaona[小娜·天秤女神<br/>法律专家]
    Xiaonuo[小诺·双鱼公主<br/>协调官]

    %% 宪法原则
    P1[原则1: 发明理解为先]
    P2[原则2: 现有技术充分检索]
    P3[原则3: 人机交互确认]
    P4[原则4: 质量迭代优化]
    P5[原则5: 保护范围平衡]

    %% 5个主要步骤
    S1[步骤1: 技术交底书理解]
    S2[步骤2: 现有技术检索]
    S3[步骤3: 说明书撰写]
    S4[步骤4: 权利要求撰写]
    S5[步骤5: 摘要撰写]

    %% 核心模块
    M1[AutoSpecDrafter<br/>说明书自动撰写框架]
    M2[PatentClaimGenerator<br/>权利要求生成器]
    M3[ClaimScopeAnalyzer<br/>权利要求范围分析]
    M4[PatentDrawingAnalyzer<br/>附图分析器]
    M5[XiaonaPatentDrafter<br/>小娜撰写助手]

    %% LLM模型
    L1[qwen3.5<br/>发明理解/质量检查]
    L2[deepseek-reasoner<br/>结构规划/内容生成]

    %% 输出文件
    O1[InventionUnderstanding<br/>发明理解结果]
    O2[对比分析报告.md]
    O3[SpecificationDraft<br/>说明书草稿]
    O4[ClaimsSet<br/>权利要求集合]
    O5[专利申请文件_完整版.md]

    %% 核心文档
    D1[技术领域]
    D2[背景技术]
    D3[发明内容]
    D4[具体实施方式]
    D5[权利要求书]
    D6[摘要]

    %% 关系
    Root --> P1
    Root --> P2
    Root --> P3
    Root --> P4
    Root --> P5

    Root --> S1
    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 --> S5

    %% 步骤与模块
    S1 -.-> M1
    S1 -.-> L1
    S2 -.-> M4
    S3 -.-> M1
    S3 -.-> L2
    S4 -.-> M2
    S4 -.-> M3
    S5 -.-> M5

    %% 步骤与输出
    S1 --> O1
    S2 --> O2
    S3 --> O3
    S4 --> O4
    S5 --> O5

    %% 最终文档
    O3 --> D1
    O3 --> D2
    O3 --> D3
    O3 --> D4
    O4 --> D5
    O5 --> D6

    %% 角色支持
    Xiaona -.-> S2
    Xiaona -.-> S3
    Xiaona -.-> S4
    Xiaonuo -.-> S1
    Xiaonuo -.-> S5

    %% 样式
    classDef root fill:#ff6b9d,stroke:#333,stroke-width:3px,color:#fff
    classDef principle fill:#4ecdc4,stroke:#333,stroke-width:2px,color:#fff
    classDef step fill:#ffe66d,stroke:#333,stroke-width:2px,color:#333
    classDef module fill:#95e1d3,stroke:#333,stroke-width:1px,color:#333
    classDef llm fill:#a29bfe,stroke:#333,stroke-width:1px,color:#fff
    classDef output fill:#dfe6e9,stroke:#333,stroke-width:1px,color:#333
    classDef document fill:#fab1a0,stroke:#333,stroke-width:2px,color:#333
    classDef expert fill:#74b9ff,stroke:#333,stroke-width:2px,color:#fff

    class Root root
    class P1,P2,P3,P4,P5 principle
    class S1,S2,S3,S4,S5 step
    class M1,M2,M3,M4,M5 module
    class L1,L2 llm
    class O1,O2,O3,O4,O5 output
    class D1,D2,D3,D4,D5,D6 document
    class Xiaona,Xiaonuo expert
```

---

## 🔍 核心流程分解

### Phase 1: 发明理解阶段（步骤1）

```mermaid
graph LR
    A[技术交底书] --> B[步骤1: 发明理解]
    B --> C[AutoSpecDrafter]

    C --> D[技术领域识别]
    C --> E[技术问题提取]
    C --> F[技术方案解析]
    C --> G[技术效果分析]

    D --> H[InventionUnderstanding]
    E --> H
    F --> H
    G --> H

    H --> I[essential_features<br/>必要特征]
    H --> J[optional_features<br/>可选特征]

    B -.-> K[qwen3.5<br/>快速理解]

    style A fill:#ffeaa7
    style H fill:#55efc4
```

**核心数据结构**:
```python
InventionUnderstanding:
  - invention_title: str           # 发明名称
  - invention_type: InventionType  # 发明类型(device/method/product)
  - technical_field: str           # 技术领域
  - core_innovation: str           # 核心创新点
  - technical_problem: str         # 技术问题
  - technical_solution: str        # 技术方案
  - technical_effects: List[str]   # 技术效果列表
  - essential_features: List[TechnicalFeature]   # 必要特征
  - optional_features: List[TechnicalFeature]    # 可选特征
  - confidence_score: float        # 理解置信度
```

---

### Phase 2: 检索与分析阶段（步骤2）

```mermaid
graph LR
    A[InventionUnderstanding] --> B[步骤2: 现有技术检索]
    B --> C[关键词提取]

    C --> D[专利数据库检索]
    C --> E[论文数据库检索]
    C --> F[网络资源检索]

    D --> G[CN12345678A.pdf]
    E --> H[论文.pdf]
    F --> I[网页.md]

    G --> J[对比分析报告]
    H --> J
    I --> J

    J --> K[区别特征确认]
    K --> L[发明点定位]

    style A fill:#ffeaa7
    style L fill:#fd79a8
```

**API接口**:
| 接口 | 功能 | 模块 |
|------|------|------|
| `POST /api/v2/patent/classify` | 专利分类 | PatentClassifier |
| `POST /api/v2/patent/search/semantic` | 语义检索 | MultimodalRetrieval |

---

### Phase 3: 说明书撰写阶段（步骤3）

```mermaid
graph TD
    A[发明理解+对比分析] --> B[步骤3: 说明书撰写]
    B --> C[AutoSpecDrafter]

    C --> D{撰写规划}
    D --> E[技术领域 50-100字]
    D --> F[背景技术 300-500字]
    D --> G[发明内容 800-1500字]
    D --> H[具体实施方式 1500-3000字]
    D --> I[附图说明]

    E --> J[SpecificationDraft]
    F --> J
    G --> J
    H --> J
    I --> J

    C -.-> K[deepseek-reasoner<br/>高质量生成]

    J --> L[质量检查]
    L --> M{得分≥7.5?}
    M -->|是| N[通过]
    M -->|否| O[迭代优化]
    O --> C

    style J fill:#55efc4
    style N fill:#00b894
```

**模型配置**:
```python
MODEL_CONFIG = {
    "understanding": {"model": "qwen3.5", "provider": "ollama", "temperature": 0.3},
    "planning": {"model": "deepseek-reasoner", "provider": "deepseek", "temperature": 0.2},
    "generation": {"model": "deepseek-reasoner", "provider": "deepseek", "temperature": 0.3},
    "quality_check": {"model": "qwen3.5", "provider": "ollama", "temperature": 0.2}
}
```

---

### Phase 4: 权利要求撰写阶段（步骤4）

```mermaid
graph TD
    A[发明点+说明书] --> B[步骤4: 权利要求撰写]
    B --> C[PatentClaimGenerator]

    C --> D[权利要求布局规划]
    D --> E[独立权利要求撰写]
    D --> F[从属权利要求撰写]

    E --> G[ClaimsSet]
    F --> G

    G --> H[权利要求1<br/>独立-中等保护范围]
    G --> I[权利要求2-4<br/>从属-进一步限定]
    G --> J[权利要求5-10<br/>从属-具体实现]

    C -.-> K[ClaimScopeAnalyzer<br/>范围分析]

    H --> L[清晰性检查]
    I --> L
    J --> L

    L --> M{A26.4符合?}
    M -->|是| N[完成]
    M -->|否| O[修订]
    O --> C

    style G fill:#fd79a8
    style N fill:#00b894
```

**权利要求类型模板**:
| 类型 | 模板结构 |
|------|---------|
| 装置 | `一种[装置名称]，其特征在于：[组件1]，与所述[组件1]连接的[组件2]...` |
| 方法 | `一种[方法名称]，包括以下步骤：[步骤1]；[步骤2]...` |
| 系统 | `一种[系统名称]，包括：[模块1]；[模块2]；其中，[模块1]被配置为[功能]...` |
| 组合物 | `一种[组合物名称]，包括：[组分1]，其含量为[范围1]...` |

---

### Phase 5: 摘要撰写阶段（步骤5）

```mermaid
graph LR
    A[完整说明书+权利要求] --> B[步骤5: 摘要撰写]
    B --> C[XiaonaPatentDrafter]

    C --> D[提取技术要点]
    D --> E[撰写摘要<br/>300字左右]

    E --> F[摘要格式化]
    F --> G[专利申请文件_完整版.md]

    C -.-> H[qwen3.5<br/>快速生成]

    style G fill:#55efc4
```

---

## 🛠️ 核心模块依赖图谱

```mermaid
graph TD
    Root[专利撰写业务]

    subgraph 核心撰写模块
        M1[AutoSpecDrafter<br/>core/patent/ai_services/autospec_drafter.py]
        M2[PatentClaimGenerator<br/>core/patent/claim_generator.py]
        M3[EnhancedClaimGenerator<br/>core/patent/claim_generator_v2.py]
        M4[XiaonaPatentDrafter<br/>production/core/cognition/xiaona_patent_drafter.py]
    end

    subgraph 辅助分析模块
        M5[ClaimScopeAnalyzer<br/>权利要求范围分析]
        M6[PatentDrawingAnalyzer<br/>附图分析]
        M7[PatentClassifier<br/>专利分类]
        M8[MultimodalRetrieval<br/>多模态检索]
    end

    subgraph 质量评估模块
        M9[QualityReport<br/>7维度质量评估]
        M10[ClaimQualitySystem<br/>权利要求质量]
    end

    Root --> M1
    Root --> M2
    Root --> M3
    Root --> M4

    M1 --> M5
    M1 --> M6
    M2 --> M7
    M2 --> M5
    M3 --> M8

    M1 --> M9
    M2 --> M10

    style Root fill:#ff6b9d,color:#fff
    style M1 fill:#ff7675
    style M2 fill:#ff7675
    style M3 fill:#ff7675
    style M4 fill:#ff7675
```

---

## 🎯 人机协作协议

```mermaid
sequenceDiagram
    participant U as 用户(发明人/代理人)
    participant A as 智能体(小娜/小诺)
    participant M as 撰写模块
    participant L as LLM模型

    Note over U,L: 步骤1: 发明理解
    U->>A: 提供技术交底书
    A->>M: AutoSpecDrafter._understand_invention()
    M->>L: qwen3.5 发明理解
    L-->>M: InventionUnderstanding
    M-->>A: 核心特征提取结果
    A->>U: 展示三元组（<300字）
    U->>A: 确认/修改

    Note over U,L: 步骤2: 现有技术检索
    A->>M: MultimodalRetrieval
    M-->>A: 对比文件列表
    A->>U: 展示检索结果（<300字）
    U->>A: 确认/修改

    Note over U,L: 步骤3: 说明书撰写
    A->>M: AutoSpecDrafter.draft_specification()
    loop 每个章节
        M->>L: deepseek-reasoner 内容生成
        L-->>M: 章节内容
        A->>U: 展示章节（<300字）
        U->>A: 确认/修改
    end

    Note over U,L: 步骤4: 权利要求撰写
    A->>M: PatentClaimGenerator.generate()
    M->>L: 生成独立/从属权利要求
    L-->>M: ClaimsSet
    A->>U: 展示权利要求布局
    U->>A: 确认保护范围

    Note over U,L: 步骤5: 质量检查
    A->>M: QualityReport (7维度评估)
    M-->>A: 质量报告
    alt 质量不达标
        A->>M: 迭代优化
    end

    A->>U: 完整专利申请文件
    U->>A: 最终确认
```

---

## 📈 质量评估体系

### 7维度质量评估

| 维度 | 说明 | 权重 | 阈值 |
|------|------|------|------|
| **completeness** | 完整性 | 15% | ≥7.5 |
| **clarity** | 清晰性 | 15% | ≥7.5 |
| **accuracy** | 准确性 | 15% | ≥7.5 |
| **sufficiency** | 充分性(A26.3) | 20% | ≥7.5 |
| **consistency** | 一致性 | 10% | ≥7.5 |
| **compliance** | 规范性 | 10% | ≥7.5 |
| **support** | 支持性(A26.4) | 15% | ≥7.5 |

### 质量迭代流程

```mermaid
graph LR
    A[草稿生成] --> B[质量检查]
    B --> C{得分≥7.5?}
    C -->|是| D[通过]
    C -->|否| E[问题修复]
    E --> F{迭代次数<3?}
    F -->|是| A
    F -->|否| G[人工审核]
    G --> D

    style D fill:#00b894
    style G fill:#fdcb6e
```

---

## 📊 知识图谱统计

| 类型 | 数量 | 说明 |
|------|------|------|
| **核心节点** | 1 | 专利撰写业务流程 |
| **宪法原则** | 5 | 撰写核心原则 |
| **流程步骤** | 5 | 完整撰写流程 |
| **核心模块** | 5 | AutoSpec/ClaimGenerator等 |
| **LLM模型** | 2 | qwen3.5/deepseek-reasoner |
| **输出数据结构** | 5 | InventionUnderstanding/ClaimsSet等 |
| **最终文档** | 6 | 说明书各章节+权利要求+摘要 |
| **智能体角色** | 2 | 小娜/小诺 |
| **质量维度** | 7 | 7维度评估体系 |

---

## 🔗 关系类型说明

| 关系类型 | 说明 | 示例 |
|---------|------|------|
| **HAS_STEP** | 包含步骤 | 撰写流程 → 步骤1-5 |
| **REQUIRES** | 需要模块 | 步骤3 → AutoSpecDrafter |
| **USES_MODEL** | 使用模型 | 发明理解 → qwen3.5 |
| **PRODUCES** | 产出文件 | 步骤3 → SpecificationDraft |
| **SUPPORTS** | 专家支持 | 小娜 → 权利要求撰写 |
| **VALIDATES** | 质量验证 | QualityReport → 说明书 |

---

## 📁 核心文件路径

| 模块 | 路径 | 功能 |
|------|------|------|
| AutoSpecDrafter | `core/patent/ai_services/autospec_drafter.py` | 说明书自动撰写 |
| PatentClaimGenerator | `core/patent/claim_generator.py` | 权利要求生成 |
| EnhancedClaimGenerator | `core/patent/claim_generator_v2.py` | 增强版权利要求生成 |
| XiaonaPatentDrafter | `production/core/cognition/xiaona_patent_drafter.py` | 小娜撰写助手 |
| ClaimScopeAnalyzer | `core/patent/ai_services/claim_scope_analyzer.py` | 权利要求范围分析 |
| 任务1_1提示词 | `prompts/business/task_1_1_understand_disclosure.md` | 技术交底书理解 |
| 任务1_3提示词 | `prompts/business/task_1_3_write_specification.md` | 说明书撰写 |
| 任务1_4提示词 | `prompts/business/task_1_4_write_claims.md` | 权利要求撰写 |

---

## 🔌 API接口汇总

| 接口 | 方法 | 功能 | 对应论文 |
|------|------|------|---------|
| `/api/v2/patent/classify` | POST | 专利分类(CPC/IPC) | PatentSBERTa |
| `/api/v2/patent/claims/revise` | POST | 权利要求修订 | Patent-CR |
| `/api/v2/patent/quality/score` | POST | 质量评分 | 论文#20 |
| `/api/v2/patent/search/semantic` | POST | 语义检索 | - |

---

*生成工具：Mermaid + Claude*
*最后更新：2026-03-27*
