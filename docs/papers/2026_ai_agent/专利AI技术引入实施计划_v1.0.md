# Athena平台专利AI技术引入实施计划 v1.0

> **基于学术搜索论文深度分析**
> **制定日期**: 2026-03-23
> **版本**: v1.0
> **制定人**: 徐健 (xujian519@gmail.com)

---

## 一、背景与目标

### 1.1 项目背景

基于对以下学术论文的深度分析，结合Athena平台现有能力，制定本实施计划：

| 论文 | 核心技术 | 引入价值 |
|------|---------|---------|
| AutoSpec (2025) | 多Agent专利说明书撰写框架 | 🔴极高 |
| PatentVision (2025) | 多模态专利附图分析 | 🔴极高 |
| 权利要求范围测量 (2023) | 信息论方法测量保护范围 | 🔴极高 |
| LLM高质量权利要求 (2024) | 基于说明书的权利要求生成 | 🔴极高 |
| Missing vs Unused Knowledge (2025) | 知识激活诊断框架 | 🟡高 |
| 专利NLP综述 (2024) | 专利生命周期任务分类 | 🟡高 |

### 1.2 总体目标

- **Phase 1 (1-2周)**: 完成高优先级技术原型开发
- **Phase 2 (3-4周)**: 完成核心功能集成与优化

### 1.3 平台现有能力盘点

| 能力 | 现有模块 | 成熟度 | 论文结合潜力 |
|------|---------|--------|-------------|
| 权利要求生成 | `claim_generator.py` | ⭐⭐⭐⭐ | 可升级 |
| 演化式撰写 | `evolutionary_drafting.py` | ⭐⭐⭐⭐ | 可升级 |
| 质量评估 | `quality_assessor.py` | ⭐⭐⭐⭐⭐ | 已实现六维框架 |
| 多模态处理 | `services/multimodal/` | ⭐⭐⭐ | 需增强 |
| 专利检索 | `enhanced_patent_retriever.py` | ⭐⭐⭐⭐ | 可升级 |
| 法律知识图谱 | `legal_knowledge_graph_builder.py` | ⭐⭐⭐⭐ | 可升级 |

---

## 二、Phase 1: 高优先级原型开发 (1-2周)

### 2.1 任务P1-1: 权利要求范围测量系统

**论文来源**: "A novel approach to measuring the scope of patent claims based on probabilities obtained from (large) language models" (2023)

**技术原理**:
```
Scope = 1 / Self-Information(claim)
Self-Information = -log(P(claim))
P(claim) 由LLM计算权利要求文本的出现概率
```

**实现方案**:

```python
# 文件: core/patent/ai_services/claim_scope_analyzer.py

class ClaimScopeAnalyzer:
    """
    基于信息论的权利要求保护范围测量系统

    核心原理:
    - 越"惊喜"的权利要求(低概率) → 越窄的保护范围
    - 越"常见"的权利要求(高概率) → 越宽的保护范围
    """

    def __init__(self, llm_manager: UnifiedLLMManager):
        self.llm_manager = llm_manager
        # 使用平台现有模型
        self.models = {
            "fast": "qwen3.5",           # 快速分析
            "accurate": "deepseek-reasoner"  # 精确分析
        }

    async def analyze_scope(
        self,
        claim_text: str,
        mode: str = "balanced"  # fast/balanced/accurate
    ) -> ScopeAnalysisResult:
        """
        分析权利要求保护范围

        返回:
        - scope_score: 范围得分 (0-100, 越高越宽)
        - self_information: 自信息值
        - probability: LLM估算的出现概率
        - risk_level: 风险等级 (low/medium/high)
        - recommendations: 优化建议
        """
        pass

    async def compare_claims(
        self,
        claims: list[str]
    ) -> list[ScopeComparison]:
        """
        批量比较多个权利要求的保护范围
        用于专利组合分析
        """
        pass
```

**与现有模块集成**:
- 集成到 `claim_quality_system.py` 作为第七维度
- 为 `interactive_improver.py` 提供范围优化建议
- 为 `comprehensive_analyzer.py` 提供量化指标

---

### 2.2 任务P1-2: 多模态专利附图分析模块

**论文来源**: "PatentVision: A multimodal method for drafting patent applications" (2025)

**实现方案**:

```python
# 文件: core/patent/ai_services/drawing_analyzer.py

class PatentDrawingAnalyzer:
    """
    专利附图智能分析系统

    基于PatentVision论文，整合:
    - 视觉语言模型 (qwen-vl-max)
    - 专利领域知识
    - 图文对齐技术
    """

    def __init__(self):
        # 使用平台已有模型
        self.vl_model = "qwen-vl-max"     # 视觉理解
        self.reasoning_model = "deepseek-reasoner"  # 深度分析

    async def analyze_drawing(
        self,
        image_path: str,
        claim_context: str | None = None
    ) -> DrawingAnalysisResult:
        """
        分析专利附图

        输出:
        - components: 识别的技术组件列表
        - connections: 组件间的功能连接
        - annotations: 自动生成的附图标记
        - description: 附图说明文字
        """
        pass

    async def generate_figure_description(
        self,
        drawing: DrawingAnalysisResult,
        figure_number: str
    ) -> str:
        """
        生成标准格式的附图说明

        输出格式:
        "图1是本发明实施例提供的XXX装置的结构示意图；
         图中：1-底座；2-支撑架；3-驱动装置..."
        """
        pass
```

**与现有模块集成**:
- 扩展 `services/multimodal/` 功能
- 为 `evolutionary_drafting.py` 提供附图支持
- 集成到专利说明书生成流程

---

### 2.3 任务P1-3: 专利说明书自动撰写Agent框架

**论文来源**: "AutoSpec: An Agentic Framework for Automatically Drafting Patent Specification" (2025)

**实现方案**:

```python
# 文件: core/patent/ai_services/autospec_drafter.py

class AutoSpecDrafter:
    """
    基于AutoSpec论文的多Agent专利说明书撰写框架

    核心设计:
    - 任务分解: 将撰写分解为可管理的子任务
    - 小模型+工具: 使用开源模型+专用工具
    - 安全性: 保护保密信息，不依赖闭源模型
    """

    # 子Agent定义
    SUB_AGENTS = {
        "invention_understander": {
            "role": "发明理解",
            "model": "qwen3.5",  # 本地模型
            "output": "TechnicalFeatures"
        },
        "structure_planner": {
            "role": "结构规划",
            "model": "deepseek-reasoner",
            "output": "DocumentStructure"
        },
        "content_generator": {
            "role": "内容生成",
            "model": "deepseek-reasoner",
            "output": "SectionContent"
        },
        "quality_checker": {
            "role": "质量审核",
            "model": "glm-4-plus",
            "output": "QualityReport"
        }
    }

    async def draft_specification(
        self,
        invention_disclosure: dict,
        options: DraftOptions | None = None
    ) -> SpecificationDraft:
        """
        端到端生成专利说明书

        流程:
        1. 发明理解 → 提取技术特征
        2. 结构规划 → 设计章节框架
        3. 内容生成 → 逐章节撰写
        4. 质量审核 → 法律合规检查
        5. 迭代优化 → 基于审核结果改进
        """
        pass
```

---

### 2.4 任务P1-4: 高质量权利要求生成优化

**论文来源**: "Can Large Language Models Generate High-quality Patent Claims?" (2024)

**核心发现应用**:
- 基于说明书生成 > 基于摘要生成
- 独立权利要求质量高，从属权利要求需增强
- 微调可提升: 特征完整性、概念清晰度、特征关联性

**实现方案**:

```python
# 文件: core/patent/claim_generator_v2.py
# 基于 claim_generator.py 升级

class EnhancedClaimGenerator:
    """
    增强版权利要求生成器

    基于论文发现优化:
    - 优先使用完整说明书(非摘要)
    - 独立权利要求+从属权利要求分步生成
    - 多模型对比验证
    """

    async def generate_claims(
        self,
        specification: str,  # 完整说明书
        invention_type: str,
        num_independent: int = 1,
        num_dependent: int = 5
    ) -> ClaimsSet:
        """
        生成权利要求书

        流程:
        1. 从说明书中提取核心特征
        2. 生成独立权利要求 (使用高质量模型)
        3. 生成从属权利要求 (增强策略)
        4. 质量验证和优化
        """
        pass
```

---

## 三、Phase 2: 核心功能集成与优化 (3-4周)

### 3.1 任务P2-1: 知识激活诊断系统

**论文来源**: "Missing vs. Unused Knowledge Hypothesis for Language Model Bottlenecks in Patent Understanding" (2025)

**技术原理**:
```
错误类型分解:
- Missing Knowledge: 模型真正缺少的知识
- Unused Knowledge: 模型有知识但未激活

诊断流程:
1. 原始任务执行
2. 生成澄清问题
3. 模型自答(激活内部知识)
4. 对比外部知识注入
5. 判断错误类型
```

**实现方案**:

```python
# 文件: core/patent/ai_services/knowledge_diagnosis.py

class KnowledgeActivationDiagnoser:
    """
    知识激活诊断系统

    用于:
    - 专利分类错误诊断
    - 检索质量优化
    - 模型能力评估
    """

    async def diagnose(
        self,
        task: str,
        model_response: str,
        ground_truth: str | None = None
    ) -> DiagnosisResult:
        """
        诊断错误来源

        输出:
        - error_type: "missing_knowledge" / "unused_knowledge"
        - clarification_questions: 澄清问题列表
        - self_answers: 模型自答结果
        - external_answers: 外部知识(如RAG)
        - improvement_strategy: 优化策略
        """
        pass
```

---

### 3.2 任务P2-2: 专利分析任务分类系统

**论文来源**: "A Survey on Patent Analysis: From NLP to Multimodal AI" (2024)

**任务分类体系**:

```
专利生命周期任务分类:

1. 申请前阶段 (Pre-filing)
   ├── 技术领域识别 (Technology Domain Classification)
   ├── 现有技术检索 (Prior Art Search)
   ├── 专利性分析 (Patentability Analysis)
   └── 撰写辅助 (Drafting Assistance)

2. 审查阶段 (Examination)
   ├── 审查意见分析 (Office Action Analysis)
   ├── 答复策略生成 (Response Strategy Generation)
   └── 权利要求修订 (Claim Amendment)

3. 授权后阶段 (Post-grant)
   ├── 侵权分析 (Infringement Analysis)
   ├── 无效分析 (Invalidity Analysis)
   └── 价值评估 (Valuation)

4. 组合管理 (Portfolio Management)
   ├── 技术趋势分析 (Technology Trend Analysis)
   ├── 竞争对手分析 (Competitor Analysis)
   └── 许可策略 (Licensing Strategy)
```

**实现方案**:

```python
# 文件: core/patent/task_classifier.py

class PatentTaskClassifier:
    """
    专利任务自动分类器

    基于论文分类体系，实现:
    - 意图识别
    - 任务分解
    - 流程映射
    """

    async def classify_task(
        self,
        user_input: str
    ) -> TaskClassification:
        """
        分类用户任务

        返回:
        - lifecycle_stage: 生命周期阶段
        - task_type: 具体任务类型
        - required_tools: 所需工具列表
        - recommended_workflow: 推荐工作流
        """
        pass
```

---

### 3.3 任务P2-3: 综合质量评估增强

**基于现有模块增强**:

```python
# 扩展: core/patent/quality_assessor.py

# 新增维度
class EnhancedQualityDimension(Enum):
    # 原有六维
    NOVELTY = "novelty"
    CLARITY = "clarity"
    COMPLETENESS = "completeness"
    SUPPORT = "support"
    SCOPE_APPROPRIATENESS = "scope_appropriateness"
    LEGAL_COMPLIANCE = "legal_compliance"

    # 新增维度 (基于论文)
    SCOPE_MEASURABILITY = "scope_measurability"  # 保护范围可测量性
    FEATURE_LINKAGE = "feature_linkage"          # 特征关联性
    TECHNICAL_COHERENCE = "technical_coherence"  # 技术连贯性
```

---

### 3.4 任务P2-4: 多模态检索增强

**实现方案**:

```python
# 文件: core/patent/multimodal_retriever.py

class MultimodalPatentRetriever:
    """
    多模态专利检索系统

    支持:
    - 文本检索 (现有)
    - 图像检索 (图纸相似性)
    - 混合检索 (图文结合)
    """

    async def search_by_drawing(
        self,
        image_path: str,
        top_k: int = 10
    ) -> list[PatentSearchResult]:
        """基于附图的专利检索"""
        pass

    async def hybrid_search(
        self,
        text_query: str,
        image_path: str | None = None,
        weights: dict = None
    ) -> list[PatentSearchResult]:
        """混合检索"""
        pass
```

---

## 四、任务清单

### Phase 1 任务清单 (1-2周)

| 编号 | 任务名称 | 优先级 | 预计工时 | 依赖任务 | 负责模块 |
|------|---------|--------|---------|---------|---------|
| P1-1 | 权利要求范围测量系统 | 🔴P0 | 16h | 无 | core/patent/ai_services/ |
| P1-2 | 多模态专利附图分析 | 🔴P0 | 20h | 无 | core/patent/ai_services/ |
| P1-3 | AutoSpec撰写框架 | 🔴P0 | 24h | P1-1, P1-2 | core/patent/ai_services/ |
| P1-4 | 高质量权利要求生成优化 | 🔴P0 | 16h | 无 | core/patent/ |
| P1-5 | 单元测试编写 | 🟡P1 | 8h | P1-1~P1-4 | tests/unit/patent/ |
| P1-6 | 集成测试 | 🟡P1 | 8h | P1-5 | tests/integration/ |
| P1-7 | 文档更新 | 🟡P1 | 4h | P1-1~P1-4 | docs/ |

**Phase 1 总工时**: ~96小时 (约12人天)

---

### Phase 2 任务清单 (3-4周)

| 编号 | 任务名称 | 优先级 | 预计工时 | 依赖任务 | 负责模块 |
|------|---------|--------|---------|---------|---------|
| P2-1 | 知识激活诊断系统 | 🟡P1 | 20h | P1-1 | core/patent/ai_services/ |
| P2-2 | 专利任务分类系统 | 🟡P1 | 16h | 无 | core/patent/ |
| P2-3 | 综合质量评估增强 | 🟡P1 | 16h | P1-1, P1-4 | core/patent/ |
| P2-4 | 多模态检索增强 | 🟡P1 | 20h | P1-2 | core/patent/ |
| P2-5 | API接口开发 | 🟡P1 | 12h | P2-1~P2-4 | core/api/ |
| P2-6 | 性能优化 | 🟢P2 | 12h | P2-1~P2-4 | - |
| P2-7 | 端到端测试 | 🟢P2 | 12h | P2-1~P2-6 | tests/e2e/ |
| P2-8 | 文档完善 | 🟢P2 | 8h | P2-1~P2-7 | docs/ |

**Phase 2 总工时**: ~116小时 (约15人天)

---

## 五、检查清单

### Phase 1 检查清单

#### P1-1: 权利要求范围测量系统

- [ ] **设计阶段**
  - [ ] 完成技术方案设计文档
  - [ ] 定义 `ScopeAnalysisResult` 数据结构
  - [ ] 设计LLM概率计算策略

- [ ] **实现阶段**
  - [ ] 实现 `ClaimScopeAnalyzer` 核心类
  - [ ] 实现单权利要求分析功能
  - [ ] 实现批量比较功能
  - [ ] 实现风险等级评估
  - [ ] 集成到现有质量评估系统

- [ ] **测试阶段**
  - [ ] 单元测试覆盖率 >80%
  - [ ] 与论文示例对比验证
  - [ ] 性能测试: 单次分析 <3秒

- [ ] **文档阶段**
  - [ ] API文档
  - [ ] 使用示例
  - [ ] 算法说明

#### P1-2: 多模态专利附图分析

- [ ] **设计阶段**
  - [ ] 完成技术方案设计
  - [ ] 定义 `DrawingAnalysisResult` 数据结构
  - [ ] 设计图文对齐策略

- [ ] **实现阶段**
  - [ ] 实现 `PatentDrawingAnalyzer` 核心类
  - [ ] 实现组件识别功能
  - [ ] 实现连接关系提取
  - [ ] 实现附图说明生成
  - [ ] 集成qwen-vl-max模型

- [ ] **测试阶段**
  - [ ] 准备测试图纸集(10+张)
  - [ ] 准确率测试 >85%
  - [ ] 处理时间 <5秒/张

- [ ] **文档阶段**
  - [ ] 支持的图纸类型说明
  - [ ] 最佳实践指南

#### P1-3: AutoSpec撰写框架

- [ ] **设计阶段**
  - [ ] 完成多Agent架构设计
  - [ ] 定义子Agent职责和接口
  - [ ] 设计任务分解策略

- [ ] **实现阶段**
  - [ ] 实现 `AutoSpecDrafter` 主类
  - [ ] 实现发明理解Agent
  - [ ] 实现结构规划Agent
  - [ ] 实现内容生成Agent
  - [ ] 实现质量审核Agent
  - [ ] 实现迭代优化流程

- [ ] **测试阶段**
  - [ ] 准备测试发明披露(5+个)
  - [ ] 端到端测试
  - [ ] 质量评估 >7.5/10

- [ ] **文档阶段**
  - [ ] 使用指南
  - [ ] 最佳实践
  - [ ] 与演化式撰写对比

#### P1-4: 高质量权利要求生成优化

- [ ] **设计阶段**
  - [ ] 分析现有 `claim_generator.py`
  - [ ] 设计增强方案

- [ ] **实现阶段**
  - [ ] 创建 `claim_generator_v2.py`
  - [ ] 实现基于说明书的生成
  - [ ] 优化从属权利要求生成
  - [ ] 添加多模型验证

- [ ] **测试阶段**
  - [ ] 对比v1和v2质量
  - [ ] 专家评估

- [ ] **文档阶段**
  - [ ] 升级指南
  - [ ] 性能对比报告

---

### Phase 2 检查清单

#### P2-1: 知识激活诊断系统

- [ ] **设计阶段**
  - [ ] 完成诊断框架设计
  - [ ] 定义错误分类标准

- [ ] **实现阶段**
  - [ ] 实现澄清问题生成
  - [ ] 实现自答激活机制
  - [ ] 实现错误类型判断
  - [ ] 实现优化策略推荐

- [ ] **测试阶段**
  - [ ] 准备诊断测试集
  - [ ] 准确率 >80%

- [ ] **文档阶段**
  - [ ] 诊断报告格式说明

#### P2-2: 专利任务分类系统

- [ ] **设计阶段**
  - [ ] 完善任务分类体系
  - [ ] 设计分类规则

- [ ] **实现阶段**
  - [ ] 实现 `PatentTaskClassifier`
  - [ ] 实现意图识别
  - [ ] 实现工作流映射

- [ ] **测试阶段**
  - [ ] 分类准确率 >90%

#### P2-3: 综合质量评估增强

- [ ] **设计阶段**
  - [ ] 设计新增维度评估标准

- [ ] **实现阶段**
  - [ ] 添加3个新评估维度
  - [ ] 更新权重配置
  - [ ] 优化评分算法

- [ ] **测试阶段**
  - [ ] 对比原版质量评估
  - [ ] 专家验证

#### P2-4: 多模态检索增强

- [ ] **设计阶段**
  - [ ] 设计图文混合检索策略

- [ ] **实现阶段**
  - [ ] 实现图纸向量化
  - [ ] 实现相似图纸检索
  - [ ] 实现混合检索融合

- [ ] **测试阶段**
  - [ ] 检索准确率测试
  - [ ] 性能测试 <2秒

---

## 六、里程碑与交付物

### Phase 1 里程碑

| 里程碑 | 时间点 | 交付物 |
|--------|-------|--------|
| M1.1 | Day 3 | 权利要求范围测量模块原型 |
| M1.2 | Day 5 | 多模态附图分析模块原型 |
| M1.3 | Day 8 | AutoSpec框架基础版本 |
| M1.4 | Day 10 | 高质量权利要求生成器v2 |
| M1.5 | Day 14 | Phase 1 完整交付 |

### Phase 2 里程碑

| 里程碑 | 时间点 | 交付物 |
|--------|-------|--------|
| M2.1 | Day 18 | 知识激活诊断模块 |
| M2.2 | Day 21 | 专利任务分类系统 |
| M2.3 | Day 24 | 综合质量评估增强版 |
| M2.4 | Day 28 | 多模态检索系统 |
| M2.5 | Day 30 | Phase 2 完整交付 |

---

## 七、风险评估与缓解

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| LLM概率估算不准确 | 中 | 高 | 使用多模型对比，引入校准机制 |
| 多模态模型性能不足 | 中 | 中 | 准备备选模型，降级方案 |
| 专利数据质量不一 | 高 | 中 | 建立数据清洗流程 |
| 集成冲突 | 中 | 中 | 模块化设计，接口隔离 |
| 性能不达标 | 低 | 高 | 缓存优化，异步处理 |

---

## 八、资源需求

### 8.1 计算资源

| 资源 | 用途 | 规格 |
|------|------|------|
| 本地推理 | qwen3.5 | Ollama, 8GB+ VRAM |
| 云端API | deepseek-reasoner, glm-4-plus | API密钥 |
| 多模态推理 | qwen-vl-max | API密钥 |

### 8.2 数据资源

| 数据 | 用途 | 来源 |
|------|------|------|
| 专利全文 | 测试与验证 | 平台现有数据 |
| 专利附图 | 多模态测试 | 平台现有数据 |
| 审查意见 | 质量评估 | 平台现有数据 |

---

## 九、验收标准

### Phase 1 验收标准

1. **功能完整性**
   - [ ] 所有P1-1~P1-4任务完成
   - [ ] 所有API接口可用
   - [ ] 所有文档更新

2. **质量标准**
   - [ ] 单元测试覆盖率 >80%
   - [ ] 无P0级Bug
   - [ ] 代码通过Ruff检查

3. **性能标准**
   - [ ] 权利要求范围分析 <3秒
   - [ ] 附图分析 <5秒
   - [ ] 说明书生成 <60秒

### Phase 2 验收标准

1. **功能完整性**
   - [ ] 所有P2-1~P2-4任务完成
   - [ ] 端到端流程可用
   - [ ] 与现有系统集成

2. **质量标准**
   - [ ] 集成测试通过
   - [ ] 性能测试达标
   - [ ] 用户验收测试通过

3. **文档标准**
   - [ ] API文档完整
   - [ ] 使用指南完整
   - [ ] 部署文档完整

---

## 十、后续规划

### Phase 3 (5-8周): 优化与扩展

1. **模型微调**
   - 专利领域专用模型微调
   - 基于反馈的持续优化

2. **性能优化**
   - 推理加速
   - 缓存优化
   - 并行处理

3. **用户反馈闭环**
   - 收集使用数据
   - 分析改进点
   - 迭代优化

---

**文档维护**:
- 每周五更新进度
- 每完成一个里程碑更新文档
- 问题及时记录到Issue

---

*制定日期: 2026-03-23*
*最后更新: 2026-03-23*
