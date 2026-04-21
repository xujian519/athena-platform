# Athena团队 - 数据契约规范

> **版本**: 1.0
> **日期**: 2026-04-21
> **状态**: 已定稿

---

## 📋 文档概述

本文档定义Athena团队各智能体之间的数据契约，包括输入格式、输出格式、数据验证规则等。

---

## 🎯 核心原则

### 1. 双格式输出

**定义**：每个智能体必须同时输出JSON格式（机器可读）和Markdown格式（人类可读）。

**实施方式**：
```json
{
  "structured_data": { ... },  // JSON格式，机器可读
  "markdown_text": "..."       // Markdown格式，人类可读
}
```

### 2. 字段完整性

**定义**：必须字段缺失时，智能体必须报错而非继续执行。

**实施方式**：
- 输入验证：检查必须字段
- 输出验证：检查输出格式
- 错误处理：明确指出缺失字段

### 3. 类型安全

**定义**：所有字段必须明确类型，禁止隐式类型转换。

**实施方式**：
- 使用JSON Schema验证
- 明确字段类型（string、number、boolean、array、object）
- 枚举值必须符合定义

---

## 📊 通用数据结构

### 执行上下文（AgentExecutionContext）

```typescript
interface AgentExecutionContext {
  session_id: string;           // 会话ID
  user_input: string;           // 用户输入
  scenario: Scenario;           // 识别的场景
  workflow_id: string;          // 工作流ID
  step_id: string;              // 当前步骤ID
  config: Record<string, any>;  // 配置参数
  memory: MemoryContext;        // 记忆上下文
}
```

### 执行结果（AgentExecutionResult）

```typescript
interface AgentExecutionResult {
  agent_id: string;             // 智能体ID
  status: AgentStatus;          // 执行状态
  output_data: OutputData;      // 输出数据
  execution_time: number;       // 执行时间（秒）
  error_message?: string;       // 错误信息（可选）
  metadata: Record<string, any>; // 元数据
}
```

### 输出数据（OutputData）

```typescript
interface OutputData {
  structured_data: Record<string, any>;  // 结构化数据（JSON）
  markdown_text: string;                 // Markdown文本
}
```

---

## 🔍 智能体数据契约

### 1. 检索者（RetrieverAgent）

#### 输入格式

```typescript
interface RetrieverInput {
  keywords: string[];          // 检索关键词
  databases?: DatabaseType[];  // 数据库列表（可选）
  limit?: number;              // 返回数量限制（可选）
  date_range?: {               // 时间范围（可选）
    start: string;             // 开始日期（ISO 8601）
    end: string;               // 结束日期（ISO 8601）
  };
  download_fulltext?: boolean; // 是否下载全文（可选）
}
```

#### 输出格式

```typescript
interface RetrieverOutput {
  structured_data: {
    keywords: string[];        // 扩展后的关键词
    patents: PatentInfo[];     // 专利列表
    total_count: number;       // 总检索数量
    filtered_count: number;    // 筛选后数量
  };
  markdown_text: string;       // Markdown格式的检索报告
}

interface PatentInfo {
  patent_id: string;           // 专利ID（内部）
  publication_number: string;  // 公开号/公告号（必须）
  application_number: string;  // 申请号
  title: string;               // 标题
  abstract: string;            // 摘要
  applicants: string[];        // 申请人
  inventors: string[];         // 发明人
  publication_date: string;    // 公开日期（ISO 8601）
  url: string;                 // 专利链接
  fulltext_available: boolean; // 全文是否可获取
}
```

#### 必须字段

**输入必须字段**：
- `keywords`：检索关键词（至少1个）

**输出必须字段**：
- `publication_number`：公开号/公告号（核心标识）
- `title`：标题
- `abstract`：摘要

#### 验证规则

```json
{
  "type": "object",
  "required": ["keywords"],
  "properties": {
    "keywords": {
      "type": "array",
      "minItems": 1,
      "items": {"type": "string", "minLength": 1}
    },
    "limit": {
      "type": "number",
      "minimum": 1,
      "maximum": 500
    }
  }
}
```

---

### 2. 分析者（AnalyzerAgent）

#### 输入格式

```typescript
interface AnalyzerInput {
  target_document: Document;   // 目标文档
  analysis_type: AnalysisType; // 分析类型
  comparison_documents?: Document[]; // 对比文档（可选）
}
```

#### 输出格式

```typescript
interface AnalyzerOutput {
  structured_data: {
    target_features: Feature[];          // 技术特征列表
    problem_effect: ProblemEffect[];     // 特征-问题-效果列表
    technical_summary: TechnicalSummary; // 技术总结
  };
  markdown_text: string;                 // Markdown格式的分析报告
}

interface Feature {
  feature_id: string;          // 特征ID
  feature_name: string;        // 特征名称
  description: string;         // 描述
  feature_type: "结构" | "方法" | "参数"; // 特征类型
  category: "必要" | "附加" | "优选"; // 类别
}

interface ProblemEffect {
  technical_feature: string;   // 技术特征
  technical_problem: string;   // 技术问题
  technical_effect: string;    // 技术效果
}

interface TechnicalSummary {
  core_steps: string[];        // 核心步骤
  component_structure: string[]; // 部件组合
  working_principle: string;   // 工作原理
}
```

#### 必须字段

**输入必须字段**：
- `target_document`：目标文档
- `analysis_type`：分析类型

**输出必须字段**：
- `structured_data`：完整结构化数据
- `markdown_text`：完整Markdown文本

---

### 3. 创造性分析智能体（CreativityAnalyzerAgent）

#### 输入格式

```typescript
interface CreativityAnalyzerInput {
  target_patent: PatentInfo;          // 目标专利
  target_features: Feature[];         // 目标专利技术特征
  comparison_documents: Document[];   // 对比文件
  comparison_features: Feature[][];   // 对比文件技术特征
}
```

#### 输出格式

```typescript
interface CreativityAnalyzerOutput {
  structured_data: {
    three_step_analysis: ThreeStepAnalysis;      // 三步法分析
    secondary_considerations: SecondaryConsiderations; // 辅助判断因素
    creativity_conclusion: string;               // 创造性结论
    creativity_level: "高" | "中" | "低";        // 创造性水平
    reasoning: string;                           // 推理过程
  };
  markdown_text: string;                         // Markdown格式的分析报告
}

interface ThreeStepAnalysis {
  step1_closest_prior_art: string;   // Step 1: 最接近的现有技术
  step2_distinctive_features: string[]; // Step 2: 区别特征
  step2_technical_problem: string;    // Step 2: 实际解决的技术问题
  step3_obviousness: boolean;         // Step 3: 是否显而易见
  step3_technical_teaching: string;   // Step 3: 技术启示
}

interface SecondaryConsiderations {
  unexpected_effect?: string;  // 预料不到的技术效果
  technical_prejudice?: string; // 克服技术偏见
  commercial_success?: string; // 商业成功
}
```

#### 必须字段

**输入必须字段**：
- `target_patent`：目标专利
- `target_features`：目标专利技术特征
- `comparison_documents`：对比文件（至少1个）

**输出必须字段**：
- `three_step_analysis`：完整三步法分析
- `creativity_conclusion`：明确结论
- `reasoning`：完整推理过程

---

### 4. 新颖性分析智能体（NoveltyAnalyzerAgent）

#### 输入格式

```typescript
interface NoveltyAnalyzerInput {
  target_patent: PatentInfo;          // 目标专利
  target_features: Feature[];         // 目标专利技术特征
  comparison_documents: Document[];   // 对比文件
}
```

#### 输出格式

```typescript
interface NoveltyAnalyzerOutput {
  structured_data: {
    novelty_conclusion: string;       // 新颖性结论
    analysis_result: NoveltyAnalysisResult[]; // 分析结果
    conflicting_application?: ConflictingApplication; // 抵触申请（可选）
  };
  markdown_text: string;              // Markdown格式的分析报告
}

interface NoveltyAnalysisResult {
  comparison_document: string;        // 对比文件
  novelty_features: string[];         // 新颖特征
  conclusion: string;                 // 结论
}

interface ConflictingApplication {
  application_number: string;         // 申请号
  publication_number: string;         // 公开号
  publication_date: string;           // 公开日期
  same_applicant: boolean;            // 是否同一申请人
}
```

---

### 5. 侵权分析智能体（InfringementAnalyzerAgent）

#### 输入格式

```typescript
interface InfringementAnalyzerInput {
  patent_claims: Claim[];             // 权利要求
  product_features: Feature[];        // 产品技术特征
  infringement_type: "literal" | "equivalent" | "both"; // 侵权类型
}
```

#### 输出格式

```typescript
interface InfringementAnalyzerOutput {
  structured_data: {
    infringement_conclusion: string;  // 侵权结论
    analysis_details: InfringementAnalysisDetail[]; // 分析详情
    defenses: string[];               // 侵权抗辩
    risk_assessment: string;          // 风险评估
  };
  markdown_text: string;              // Markdown格式的分析报告
}

interface InfringementAnalysisDetail {
  claim_number: string;               // 权利要求编号
  all_elements_rule: boolean;         // 全面覆盖原则
  doctrine_of_equivalents: boolean;   // 等同原则
  conclusion: string;                 // 结论
}
```

---

## 🔧 数据验证

### 验证器实现

```python
from jsonschema import validate, ValidationError

class DataValidator:
    """数据验证器"""

    def validate_input(self, data: dict, schema: dict) -> bool:
        """验证输入数据"""
        try:
            validate(instance=data, schema=schema)
            return True
        except ValidationError as e:
            raise ValueError(f"输入数据验证失败: {e.message}")

    def validate_output(self, data: dict, schema: dict) -> bool:
        """验证输出数据"""
        try:
            validate(instance=data, schema=schema)
            return True
        except ValidationError as e:
            raise ValueError(f"输出数据验证失败: {e.message}")
```

### 宽松验证（Phase 1）

**定义**：只验证关键字段，非关键字段缺失时警告。

**实施方式**：
```python
class LenientValidator(DataValidator):
    """宽松验证器"""

    def validate_output(self, data: dict, schema: dict) -> bool:
        """宽松验证输出数据"""
        try:
            # 只验证必须字段
            required_fields = schema.get("required", [])
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"缺少必须字段: {field}")
            return True
        except Exception as e:
            # 非必须字段缺失时警告
            logger.warning(f"数据验证警告: {e}")
            return True
```

---

## 📋 错误处理

### 错误码定义

| 错误码 | 说明 | 处理方式 |
|--------|------|---------|
| `E001` | 缺少必须字段 | 报错，停止执行 |
| `E002` | 字段类型错误 | 报错，停止执行 |
| `E003` | 字段值超出范围 | 报错，停止执行 |
| `E004` | 数据格式错误 | 报错，停止执行 |
| `W001` | 非必须字段缺失 | 警告，继续执行 |
| `W002` | 字段值非标准 | 警告，继续执行 |

### 错误响应格式

```json
{
  "status": "error",
  "error_code": "E001",
  "error_message": "缺少必须字段: publication_number",
  "agent_id": "xiaona_retriever",
  "timestamp": "2026-04-21T12:34:56Z"
}
```

---

## 🔗 关联文档

- [Athena团队架构设计](../ATHENA_TEAM_ARCHITECTURE_V2.md)
- [Phase 1智能体定义](../agents/PHASE1_AGENTS_DEFINITION.md)
- [工作流程设计](../workflows/SCENARIO_BASED_WORKFLOWS.md)

---

**End of Document**
