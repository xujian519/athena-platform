# 小娜专业代理架构文档

> **文档版本**: v1.0
> **更新日期**: 2026-04-23
> **状态**: 生产就绪

---

## 一、架构概览

### 1.1 从单一代理到专业代理矩阵

**历史演进**：
- **v1.0** (2024): 单一小娜代理 - 所有法律功能集中
- **v2.0** (2025): 小娜拆解为4个子代理 (检索、分析、写作、代理)
- **v3.0** (2026-04): **小娜拆解为9个专业代理** - 全生命周期覆盖
- **v3.1** (2026-04): **WriterAgent和PatentDraftingProxy合并为UnifiedPatentWriter** - 统一撰写能力

### 1.2 架构优势

| 维度 | v1.0 单一代理 | v3.1 专业代理矩阵 |
|------|-------------|----------------|
| **职责分离** | ❌ 混杂 | ✅ 清晰 |
| **独立部署** | ❌ 不可行 | ✅ 每个代理独立 |
| **并行调用** | ❌ 受限 | ✅ 完全支持 |
| **维护成本** | 高 | 低 |
| **扩展性** | 差 | 优秀 |
| **专业化程度** | 低 | 高 |

---

## 二、9个专业代理详解

### 2.1 基础代理（3个）

#### **RetrieverAgent - 检索代理**

**文件**: `core/agents/xiaona/retriever_agent.py`

**功能**：
- 专利检索（CN、US、EP、WO等）
- 现有技术查找
- 检索策略优化
- 检索结果排序和过滤

**核心方法**：
```python
class RetrieverAgent:
    def search_patents(query: str, databases: List[str]) -> List[Patent]
    def search_prior_art(technical_features: List[str]) -> List[Patent]
    def optimize_search_strategy(initial_results: List[Patent]) -> SearchStrategy
```

**使用场景**：
- 专利申请前的现有技术检索
- 无效宣告证据查找
- FTO分析中的自由实施检索

---

#### **AnalyzerAgent - 分析代理**

**文件**: `core/agents/xiaona/analyzer_agent.py`

**功能**：
- 专利文本分析
- 技术方案解析
- 权利要求解析
- 技术特征提取

**核心方法**：
```python
class AnalyzerAgent:
    def analyze_patent_text(patent_text: str) -> PatentAnalysis
    def parse_claims(claims_text: str) -> List[Claim]
    def extract_technical_features(description: str) -> List[Feature]
```

**使用场景**：
- 专利理解深度分析
- 技术方案对比
- 权利要求解释

---

#### **UnifiedPatentWriter - 统一撰写代理**

**文件**: `core/agents/xiaona/unified_patent_writer.py`
**状态**: ✅ 生产就绪
**版本**: 2.0.0
**质量评分**: 90/100

**功能**：
- 整合原WriterAgent和PatentDraftingProxy的所有能力
- 完整的专利申请文件撰写流程
- 从技术交底书到申请文件的端到端处理

**核心能力**（7个模块）：

| 能力 | 方法 | 说明 |
|------|------|------|
| **交底书分析** | `analyze_disclosure()` | 深度解析技术交底书 |
| **可专利性评估** | `assess_patentability()` | 新颖性、创造性、实用性评估 |
| **说明书撰写** | `draft_specification()` | 生成规范说明书 |
| **权利要求撰写** | `draft_claims()` | 生成权利要求书 |
| **保护范围优化** | `optimize_protection_scope()` | 优化权利要求保护范围 |
| **充分性审查** | `review_adequacy()` | 审查申请文件充分性 |
| **错误检测** | `detect_common_errors()` | 检测20+常见错误 |

**使用示例**：
```python
from core.agents.xiaona.unified_patent_writer import UnifiedPatentWriter

writer = UnifiedPatentWriter()

# 完整撰写流程
disclosure = writer.analyze_disclosure("交底书.docx")
patentability = writer.assess_patentability(disclosure)
claims = writer.draft_claims(disclosure, patentability)
specification = writer.draft_specification(disclosure, claims)
review = writer.review_adequacy(claims, specification)
errors = writer.detect_common_errors(claims, specification)
```

---

### 2.2 分析代理（6个）

#### **NoveltyAnalyzerProxy - 新颖性分析代理**

**文件**: `core/agents/xiaona/novelty_analyzer_proxy.py`

**功能**：
- 新颖性评估
- 现有技术对比
- 区别技术特征识别
- 新颖性意见书生成

**核心方法**：
```python
class NoveltyAnalyzerProxy:
    def assess_novelty(patent_data: dict, prior_art: List[Patent]) -> NoveltyReport
    def compare_with_prior_art claims: List[Claim], prior_art: List[Patent]) -> Comparison
    def identify_distinguishing_features(claims: List[Claim], prior_art: List[Patent]) -> List[Feature]
```

**输出示例**：
```json
{
  "novelty_level": "有新颖性",
  "distinguishing_features": [
    "特征1: 结合深度学习与传统算法",
    "特征2: 自适应权重调整机制"
  ],
  "prior_art_citations": ["D1: CN123456A", "D2: US2023xxx"],
  "conclusion": "权利要求1-3具备新颖性"
}
```

---

#### **CreativityAnalyzerProxy - 创造性分析代理**

**文件**: `core/agents/xiaona/creativity_analyzer_proxy.py`

**功能**：
- 创造性（非显而易见性）评估
- 技术问题-解决方案-效果分析
- "三步法"评估
- 创造性意见书生成

**核心方法**：
```python
class CreativityAnalyzerProxy:
    def assess_creativity(patent_data: dict, prior_art: List[Patent]) -> CreativityReport
    def apply_three_step_test closest_prior_art: Patent, claimed_invention: dict) -> StepTestResult
    def analyze_technical_effect(features: List[Feature]) -> List[Effect]
```

**评估维度**：
1. **技术问题**: 是否解决了长期存在的问题？
2. **技术启示**: 现有技术是否有改进动机？
3. **技术效果**: 是否带来了预料不到的效果？

---

#### **InfringementAnalyzerProxy - 侵权分析代理**

**文件**: `core/agents/xiaona/infringement_analyzer_proxy.py`

**功能**：
- 侵权风险评估
- 权利要求解释
- 字面侵权分析
- 等同侵权分析

**核心方法**：
```python
class InfringementAnalyzerProxy:
    def analyze_infringement(patent_claims: List[Claim], accused_product: dict) -> InfringementReport
    def interpret_claims(claims: List[Claim]) -> ClaimInterpretation
    def analyze_literal_infringement(claim_elements: List[Element], product_features: List[Feature]) -> bool
    def analyze_doctrine_of_equivalents(claim_elements: List[Element], product_features: List[Feature]) -> bool
```

**分析流程**：
```
权利要求解释 → 字面侵权分析 → 等同侵权分析 → 侵权结论
```

---

#### **InvalidationAnalyzerProxy - 无效分析代理**

**文件**: `core/agents/xiaona/invalidation_analyzer_proxy.py`

**功能**：
- 无效宣告风险评估
- 证据组合分析
- 无效理由生成
- 成功率预测

**核心方法**：
```python
class InvalidationAnalyzerProxy:
    def analyze_invalidation(patent_number: str, evidence_list: List[Patent]) -> InvalidationReport
    def evaluate_evidence_combination(evidence: List[Patent], claims: List[Claim]) -> EvidenceCombination
    def predict_success_rate(invalidation_arguments: List[Argument]) -> float
```

**实战案例**：
- 济南力邦无效案件（188个专利分析）
- 发现CN206156248U高价值证据
- 形成6个主证+从证的推荐方案

---

#### **ApplicationReviewerProxy - 申请审查代理**

**文件**: `core/agents/xiaona/application_reviewer_proxy.py`

**功能**：
- 申请文件质量审查
- 形式审查
- 实质审查预评估
- 补正建议生成

**核心方法**：
```python
class ApplicationReviewerProxy:
    def review_application_quality(application_docs: dict) -> ReviewReport
    def check_formal_requirements(application: dict) -> List[Issue]
    def pre_assess_substantive_examination(specification: str, claims: List[Claim]) -> RiskAssessment
    def generate_correction_suggestions(issues: List[Issue]) -> List[Suggestion]
```

**审查维度**：
- 形式要求：文件完整性、格式规范
- 实质要求：新颖性、创造性、实用性
- 撰写质量：清楚、完整、支持

---

#### **WritingReviewerProxy - 写作审查代理**

**文件**: `core/agents/xiaona/writing_reviewer_proxy.py`

**功能**：
- 文本质量审查
- 常见错误检测（20+类型）
- 语言表达优化
- 逻辑一致性检查

**核心方法**：
```python
class WritingReviewerProxy:
    def review_writing_quality(text: str) -> QualityReport
    def detect_common_errors(text: str) -> List[Error]
    def suggest_improvements(text: str, error_types: List[str]) -> List[Suggestion]
    def check_logical_consistency(specification: str, claims: List[Claim]) -> ConsistencyReport
```

**常见错误类型**：
1. 权利要求不清晰
2. 说明书不充分
3. 技术术语不一致
4. 实施例不支持权利要求
5. 保护范围过宽/过窄
... (共20+类型)

---

## 三、代理协作模式

### 3.1 串行协作

**示例：专利申请流程**
```
技术交底
  ↓
RetrieverAgent (现有技术检索)
  ↓
AnalyzerAgent (技术方案分析)
  ↓
UnifiedPatentWriter (撰写申请文件)
  ↓
ApplicationReviewerProxy (申请文件审查)
  ↓
定稿
```

### 3.2 并行协作

**示例：可专利性评估**
```
技术方案
  ↓
  ├──→ NoveltyAnalyzerProxy (新颖性)
  │
  └──→ CreativityAnalyzerProxy (创造性)
       ↓
   综合评估报告
```

### 3.3 混合协作

**示例：无效宣告分析**
```
目标专利
  ↓
RetrieverAgent (证据检索)
  ↓
  ├──→ InvalidationAnalyzerProxy (无效分析)
  │         ↓
  └──→ InfringementAnalyzerProxy (侵权分析)
            ↓
      综合无效报告
```

---

## 四、技术架构

### 4.1 基类设计

所有专业代理继承自 `BaseComponent`：

```python
# core/agents/xiaona/base_component.py
class BaseComponent:
    """专业代理基类"""

    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.health_status = "healthy"

    def health_check(self) -> dict:
        """健康检查"""
        return {
            "name": self.name,
            "version": self.version,
            "status": self.health_status,
            "timestamp": datetime.now().isoformat()
        }

    def get_capabilities(self) -> List[str]:
        """获取代理能力列表"""
        raise NotImplementedError
```

### 4.2 统一接口

每个专业代理都实现以下标准接口：

```python
class ProfessionalAgent(BaseComponent):
    def process(self, input_data: dict) -> dict:
        """主要处理方法"""
        pass

    def validate_input(self, input_data: dict) -> bool:
        """输入验证"""
        pass

    def format_output(self, result: dict) -> dict:
        """输出格式化"""
        pass

    def get_metadata(self) -> dict:
        """获取元数据"""
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": self.get_capabilities(),
            "health": self.health_check()
        }
```

### 4.3 配置管理

**配置文件**: `config/agent_registry.json`

```json
{
  "agents": {
    "xiaona": {
      "name": "小娜·天秤女神",
      "role": "专利法律专家模块",
      "type": "agent_module",
      "description": "专业知识产权法律服务模块，包含多个专业智能体",
      "sub_agents": [
        "RetrieverAgent",
        "AnalyzerAgent",
        "UnifiedPatentWriter",
        "NoveltyAnalyzerProxy",
        "CreativityAnalyzerProxy",
        "InfringementAnalyzerProxy",
        "InvalidationAnalyzerProxy",
        "ApplicationReviewerProxy",
        "WritingReviewerProxy"
      ],
      "deprecated": [
        {
          "name": "WriterAgent",
          "replacement": "UnifiedPatentWriter",
          "deprecated_since": "2.0.0",
          "reason": "已合并到UnifiedPatentWriter，提供统一的专利撰写能力"
        },
        {
          "name": "PatentDraftingProxy",
          "replacement": "UnifiedPatentWriter",
          "deprecated_since": "2.0.0",
          "reason": "已合并到UnifiedPatentWriter，统一专利撰写流程"
        }
      ],
      "capabilities": {
        "patent_drafting": {
          "name": "专利撰写",
          "component": "UnifiedPatentWriter",
          "version": "2.0.0",
          "quality_score": 90,
          "production_ready": true
        }
      }
    }
  }
}
```

---

## 五、部署和监控

### 5.1 健康检查

每个代理都提供健康检查接口：

```python
from core.agents.xiaona.unified_patent_writer import UnifiedPatentWriter

writer = UnifiedPatentWriter()
health = writer.health_check()
print(health)
# 输出:
# {
#   "name": "UnifiedPatentWriter",
#   "version": "2.0.0",
#   "status": "healthy",
#   "timestamp": "2026-04-23T12:00:00"
# }
```

### 5.2 监控指标

**Prometheus指标**：
- `agent_invocation_total{agent="专利撰写代理"}` - 调用次数
- `agent_execution_duration_seconds{agent="专利撰写代理"}` - 执行时长
- `agent_error_total{agent="专利撰写代理",error_type="..."}` - 错误次数
- `agent_quality_score{agent="专利撰写代理"}` - 质量评分

**Grafana仪表板**：
- 代理调用趋势
- 平均响应时间
- 错误率统计
- 质量评分趋势

### 5.3 日志记录

每个代理的日志都记录到：
- **开发环境**: `/tmp/xiaona_agents/`
- **生产环境**: `/var/log/athena/agents/`

日志格式：
```
[2026-04-23 12:00:00] [UnifiedPatentWriter] [INFO] [analyze_disclosure] 开始分析交底书: 交底书.docx
[2026-04-23 12:00:05] [UnifiedPatentWriter] [INFO] [analyze_disclosure] 分析完成，提取技术特征15个
[2026-04-23 12:00:10] [UnifiedPatentWriter] [INFO] [draft_claims] 开始撰写权利要求
```

---

## 六、最佳实践

### 6.1 选择合适的代理

| 任务 | 推荐代理 | 替代方案 |
|------|---------|---------|
| 专利检索 | RetrieverAgent | - |
| 技术分析 | AnalyzerAgent | - |
| 完整撰写 | UnifiedPatentWriter | - |
| 新颖性评估 | NoveltyAnalyzerProxy | - |
| 创造性评估 | CreativityAnalyzerProxy | - |
| 侵权分析 | InfringementAnalyzerProxy | - |
| 无效宣告 | InvalidationAnalyzerProxy | - |
| 申请审查 | ApplicationReviewerProxy | - |
| 文本审查 | WritingReviewerProxy | - |

### 6.2 性能优化

**并行调用**：
```python
# ❌ 串行调用（慢）
novelty = NoveltyAnalyzerProxy().assess_novelty(data)
creativity = CreativityAnalyzerProxy().assess_creativity(data)

# ✅ 并行调用（快）
import asyncio
results = await asyncio.gather(
    NoveltyAnalyzerProxy().assess_novelty(data),
    CreativityAnalyzerProxy().assess_creativity(data)
)
```

**缓存结果**：
```python
from functools import lru_cache

class UnifiedPatentWriter:
    @lru_cache(maxsize=100)
    def analyze_disclosure(self, disclosure_path: str):
        # 缓存交底书分析结果
        pass
```

### 6.3 错误处理

```python
from core.agents.xiaona.unified_patent_writer import UnifiedPatentWriter

try:
    writer = UnifiedPatentWriter()
    result = writer.draft_claims(disclosure_data)
except InsufficientDataError as e:
    # 数据不足，补充信息
    supplement_info = request_supplement(e.missing_fields)
    result = writer.draft_claims(disclosure_data, supplement_info)
except QualityError as e:
    # 质量问题，人工审核
    result = human_review(writer.draft_claims(disclosure_data))
```

---

## 七、未来规划

### 7.1 短期（1-3个月）

- [ ] 增加更多专业代理（如FTO分析代理）
- [ ] 优化代理间通信机制
- [ ] 增强代理学习能力

### 7.2 中期（3-6个月）

- [ ] 实现代理自主决策
- [ ] 支持代理动态组合
- [ ] 建立代理性能基准

### 7.3 长期（6-12个月）

- [ ] 多模态代理（图片、视频分析）
- [ ] 跨语言代理
- [ ] 代理市场和插件系统

---

## 八、参考文档

- **CLAUDE.md**: 项目总览
- **docs/architecture/knowledge_graph.md**: 知识图谱架构
- **docs/guides/PATENT_TOOLS_PRODUCTION_GUIDE.md**: 专利工具使用指南
- **docs/api/PATENT_DRAFTING_PROXY_API.md**: 专利撰写代理API文档（已废弃，请参考UnifiedPatentWriter）
- **docs/reports/PATENT_DRAFTING_COMPLETION_REPORT_20260423.md**: 撰写代理完成报告（历史记录）

---

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-04-23
