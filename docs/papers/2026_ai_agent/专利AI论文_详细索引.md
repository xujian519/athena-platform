# 专利AI论文集 - 详细索引

> 创建时间: 2026-02-12
> 论文总数: 18篇
> 分类: AI Agent相关 (7篇) + 专利AI相关 (7篇)

---

## 📚 论文分类索引

### 🤖 第一类：AI Agent架构与安全 (7篇)

| # | 论文名 | 文件名 | 核心主题 | 领域 |
|---|--------|---------|--------|
| 1 | Trustworthy Agentic AI Requires Deterministic Architectural Boundaries | `Trustworthy_AI_Deterministic_Boundaries.pdf` | 三重防御架构(操作治理、信息流控制、权限分离) | AI安全 |
| 2 | AgentCgroup: Understanding and Controlling OS Resources of AI Agents | `paper_2602.09345.pdf` | eBPF资源控制、进程追踪、动态限制 | 操作系统 |
| 3 | Do Multi-Agents Dream of Electric Screens? (Minitap) | `Minitap_Multi_Agent_System.pdf` | 任务分解、多智能体协作、100%准确率 | 多智能体 |
| 4 | Evaluation Becomes a Side Channel | `Evaluation_Becomes_Side_Channel.pdf` | 对齐评估中的信息泄露 | AI对齐 |
| 5 | Pareto-Guided Multi-Agent for Mobile MOBA Games | `Pareto_Mobile_MOBA_Games.pdf` | 游戏AI中的多智能体协作 | 游戏AI |
| 6 | CausalArmor: Prompt Injection Guardrails | `CausalArmor_Prompt_Injection.pdf` | 因果归因防御提示注入 | AI安全 |
| 7 | From Assistant to Double Attack | `From_Assistant_Double_Attack.pdf` | AI安全攻击与防御 | AI安全 |

---

### 📜 第二类：专利AI应用 (7篇)

| # | 论文名 | 文件名 | 核心主题 | 领域 |
|---|--------|---------|--------|
| 1 | Large Language Models for Patent Classification | `LLM_Patent_Classification.pdf` | LLM在专利CPC分类中的应用，长尾效应分析 | 专利分类 |
| 2 | Patentformer: A Novel Method to Automate Generation of Patent Claims | `Patentformer_Automate_Generation.pdf` | 自动生成专利权利要求书 | 专利撰写 |
| 3 | Can Large Language Models Generate High-Quality Patent Claims? | `LLM_High_Quality_Claims.pdf` | 评估LLM生成权利要求的质量 | 专利撰写 |
| 4 | Informative Patents? Predicting Invalidity Decisions | `Predicting_Invalidity_Decisions.pdf` | 预测专利无效性决定 | 专利分析 |
| 5 | A Survey on Patent Analysis: From NLP to Multimodal AI | `Patent_Survey_NLP_Multimodal.pdf` | 专利分析全面综述(分类、检索、质量、生成) | 综述 |
| 6 | PatentSBERTa: A Deep NLP based Hybrid Model | `PatentSBERTa_Deep_NLP.pdf` | 专利语义分析混合模型 | 语义分析 |
| 7 | Predicting Bad Patents: Employing Machine Learning | `Predicting_Bad_Patents.pdf` | 机器学习预测专利质量 | 专利质量 |

---

### 🔍 第三类：其他相关论文 (4篇)

| # | 论文名 | 文件名 | 核心主题 |
|---|--------|---------|--------|
| 1 | AutoFly: Vision-Language-Action Model | `AutoFly_Vision_Language_Action.pdf` | 视觉-语言-行动模型 |
| 2 | Decentralized Intent for Multi-Robot | `Decentralized_Intent_Multi_Robot.pdf` | 多机器人去中心化意图 |
| 3 | Discovering High-Level Patterns | `Discovering_High_Level_Patterns.pdf` | 高级模式发现 |
| 4 | 未编号论文2602.09947 | `paper_2602.09947.pdf` | AI架构相关 |

---

## 🎯 与Athena平台的相关性矩阵

```
┌─────────────────────────────────────────────────────────────────────┐
│           论文与Athena平台各模块的相关性                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                               │
│  论文                  小娜(法律)  小诺(调度)  云熙(IP)  Gateway │
│  ────────────────────────────────────────────────────────────     │
│  Trinity Defense            ⭐⭐⭐⭐     ⭐⭐⭐      ⭐⭐    ⭐⭐⭐⭐⭐ │
│  AgentCgroup              ⭐⭐       ⭐⭐⭐      ⭐⭐    ⭐⭐⭐⭐  │
│  Minitap                 ⭐⭐⭐⭐    ⭐⭐⭐⭐⭐   ⭐⭐⭐   ⭐⭐⭐⭐ │
│  LLM Patent Classification  ⭐⭐⭐⭐⭐   ⭐⭐       ⭐     ⭐⭐⭐   │
│  Patentformer             ⭐⭐⭐⭐⭐   ⭐⭐       ⭐⭐    ⭐⭐    │
│  LLM High-Quality Claims  ⭐⭐⭐⭐⭐   ⭐        ⭐     ⭐      │
│  Predicting Invalidity     ⭐⭐⭐⭐    ⭐⭐       ⭐⭐    ⭐      │
│  Patent Survey           ⭐⭐⭐⭐    ⭐⭐⭐      ⭐⭐    ⭐⭐⭐   │
│  PatentSBERTa           ⭐⭐⭐⭐⭐   ⭐⭐       ⭐     ⭐⭐⭐   │
│  Predicting Bad Patents   ⭐⭐⭐⭐    ⭐⭐       ⭐⭐    ⭐      │
│                                                               │
└─────────────────────────────────────────────────────────────────────┘

图例: ⭐越多，相关性越强
```

---

## 📖 推荐学习顺序

### 第一阶段：架构基础 (优先级最高)

1. ✅ **Trustworthy AI** - Gateway安全架构设计基础
2. ✅ **AgentCgroup** - 智能体资源管理基础
3. ✅ **Minitap** - 多智能体协作模式参考

### 第二阶段：专利AI核心能力

4. **LLM Patent Classification** - 小娜的专利分类能力
5. **Patentformer** - 自动撰写权利要求
6. **PatentSBERTa** - 专利语义分析基础
7. **Patent Survey** - 全面了解专利AI技术栈

### 第三阶段：高级应用

8. **LLM High-Quality Claims** - 权利要求质量评估
9. **Predicting Invalidity** - 专利有效性预测
10. **Predicting Bad Patents** - 专利质量预测

---

## 🔗 论文来源链接

### AI Agent论文

| 论文 | 来源 | 链接 |
|------|------|------|
| Trinity Defense | arXiv | https://arxiv.org/abs/2602.09947 |
| AgentCgroup | arXiv | https://arxiv.org/abs/2602.09345 |
| Minitap | arXiv | https://arxiv.org/abs/2602.07787 |
| Evaluation Side Channel | arXiv | https://arxiv.org/abs/2602.09433 |
| CausalArmor | arXiv | https://arxiv.org/abs/2602.07918 |
| From Assistant Double Attack | - | - |

### 专利AI论文

| 论文 | 来源 | 链接 |
|------|------|------|
| LLM Patent Classification | arXiv | https://arxiv.org/abs/2601.23200 |
| Patentformer | ACL Anthology | https://aclanthology.org/2024.emnlp-industry.101 |
| LLM High-Quality Claims | arXiv | https://arxiv.org/abs/2412.02549 |
| Predicting Invalidity | Berkeley Law | [PDF](https://www.law.berkeley.edu/wp-content/uploads/2021/04/hicks_informative_patents_latest.pdf) |
| Patent Survey | ACL | https://aclanthology.org/2025.acl-long.419 |
| PatentSBERTa | arXiv | https://arxiv.org/abs/2103.11933 |
| Predicting Bad Patents | Berkeley EECS | [PDF](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2017/EECS-2017-60.pdf) |

---

## 💡 核心技术栈总结

```
┌─────────────────────────────────────────────────────────────────────┐
│           专利AI技术栈全景图                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │              基础模型层                              │     │
│  │  • BERT/RoBERTa (编码器)                             │     │
│  │  • GPT/Claude (解码器)                              │     │
│  │  • T5/BART (编码-解码器)                             │     │
│  │  • 专利专用模型: PatentBERT, PatentSBERTa            │     │
│  └─────────────────────────────────────────────────────────┘     │
│                          │                                  │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │              技术能力层                              │     │
│  │  • 文本分类: CPC/IPC分类                           │     │
│  │  • 语义检索: 向量相似度搜索                         │     │
│  │  • 文本生成: 权利要求撰写                          │     │
│  │  • 质量预测: 有效性与价值预测                       │     │
│  │  • 知识图谱: 技术关联分析                          │     │
│  └─────────────────────────────────────────────────────────┘     │
│                          │                                  │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │              应用层                                  │     │
│  │  • 专利检索: 先例 art搜索                            │     │
│  │  • 专利分析: 技术趋势、竞争分析                       │     │
│  │  • 专利撰写: 权利要求自动生成                       │     │
│  │  • 专利评估: 有效性预测、质量评分                      │     │
│  │  • 专利管理: 分类、归档、监控                        │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📊 论文统计

### 按领域分类

| 领域 | 论文数量 | 占比 |
|--------|---------|------|
| AI Agent架构 | 7 | 39% |
| 专利分析 | 4 | 22% |
| 专利生成 | 2 | 11% |
| 专利分类 | 2 | 11% |
| AI安全 | 3 | 17% |

### 按来源分类

| 来源 | 数量 |
|------|------|
| arXiv | 6 |
| ACL Anthology | 3 |
| 机构报告 | 3 |
| 其他 | 6 |

---

## 🎯 Athena平台应用建议

### 小娜(法律专家)增强

```python
# 基于论文的能力增强建议

小娜当前能力 → 论文建议增强
────────────────────────────────────────
专利检索    → PatentSBERTa语义检索
专利分析    → 专利质量预测模型
权利要求撰写  → Patentformer自动生成
分类打标    → LLM专利分类
```

### 小诺(调度官)增强

```python
# 基于Minitap的任务分解能力

@dataclass
class TaskDecomposition:
    """任务分解结构"""
    main_task: str
    subtasks: List[SubTask]
    dependencies: Dict[str, List[str]]
    estimated_time: Dict[str, float]
    
class XiaonuEnhanced:
    """增强版小诺"""
    
    def decompose_patent_task(self, task: str) -> TaskDecomposition:
        """使用LLM进行专利任务分解"""
        # 参考: Minitap论文的任务分解方法
        pass
```

### 云熙(IP管理)增强

```python
# 基于Trinity的资源管理

class YunxiResourceManager:
    """云熙资源管理器"""
    
    def track_patent_lifecycle(self, patent_id: str):
        """追踪专利全生命周期"""
        # 参考: PatentSBERTa的语义分析
        pass
    
    def predict_patent_value(self, patent: Patent) -> float:
        """预测专利价值"""
        # 参考: Predicting Bad Patents
        pass
```

---

## 📝 学习进度跟踪

- [x] Phase 1: AI Agent架构 (3篇完成)
- [x] Phase 2: 专利AI核心 (4/4完成) ✅
  - [x] LLM Patent Classification - 专利分类与长尾效应 (2026-03-20)
  - [x] Patentformer - 专利说明书自动生成 (2026-03-20)
  - [x] PatentSBERTa - 专利语义分析与嵌入 (2026-03-20)
  - [x] Patent Survey - 专利AI技术栈全面了解 (2026-03-20)
- [x] Phase 3: 高级应用 (3/3完成) ✅
  - [x] Patent-CR (LLM High-Quality Claims) - 权利要求修订数据集 (2026-03-20)
  - [x] Predicting Invalidity - 专利无效性预测 (2026-03-20)
  - [x] Predicting Bad Patents - 专利质量预测 (2026-03-20)

---

*最后更新: 2026-03-20 (Phase 3完成)*
*维护者: Athena工作平台*
*状态: 专利AI论文全部阅读完成 ✅*
