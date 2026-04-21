# Athena团队架构设计 - 文档索引

> **版本**: 1.0
> **最后更新**: 2026-04-21
> **状态**: 已定稿

---

## 📋 文档概览

本文档集包含Athena团队（智能体架构重构）的完整设计文档，涵盖架构设计、智能体定义、工作流程、数据契约、人机交互、网关集成等各个方面。

---

## 🎯 快速开始

### 如果您是...

**项目负责人**：
- 阅读 [完整总结报告](../reports/ATHENA_TEAM_ARCHITECTURE_FINAL_REPORT_20260421.md)
- 了解项目目标、预期效果、下一步行动

**架构师**：
- 阅读 [架构设计文档](./ATHENA_TEAM_ARCHITECTURE_V2.md)
- 了解系统架构、核心原则、技术栈

**开发者**：
- 阅读 [智能体定义文档](../agents/PHASE1_AGENTS_DEFINITION.md)
- 阅读 [数据契约规范](./api/DATA_CONTRACT_SPECIFICATION.md)
- 了解智能体职责、接口定义

**产品经理**：
- 阅读 [人机交互设计](./workflows/USER_INTERACTION_DESIGN.md)
- 阅读 [工作流程设计](./workflows/SCENARIO_BASED_WORKFLOWS.md)
- 了解用户体验、业务流程

**运维工程师**：
- 阅读 [Go网关集成方案](./integration/GATEWAY_INTEGRATION.md)
- 了解部署配置、监控指标

---

## 📚 文档分类

### 1. 架构设计（核心）

| 文档 | 路径 | 说明 |
|------|------|------|
| **架构设计总览** | [ATHENA_TEAM_ARCHITECTURE_V2.md](./ATHENA_TEAM_ARCHITECTURE_V2.md) | 系统架构图、核心原则、技术栈 |
| **智能体定义** | [../agents/PHASE1_AGENTS_DEFINITION.md](../agents/PHASE1_AGENTS_DEFINITION.md) | 7个智能体的详细定义和职责划分 |

### 2. 工作流程（业务）

| 文档 | 路径 | 说明 |
|------|------|------|
| **场景工作流程** | [./workflows/SCENARIO_BASED_WORKFLOWS.md](./workflows/SCENARIO_BASED_WORKFLOWS.md) | 5个场景的完整工作流程定义 |
| **人机交互设计** | [./workflows/USER_INTERACTION_DESIGN.md](./workflows/USER_INTERACTION_DESIGN.md) | 计划展示、确认机制、打断机制 |

### 3. API和数据（技术）

| 文档 | 路径 | 说明 |
|------|------|------|
| **数据契约规范** | [./api/DATA_CONTRACT_SPECIFICATION.md](./api/DATA_CONTRACT_SPECIFICATION.md) | 输入输出格式、验证规则、错误处理 |

### 4. 提示词工程（核心）

| 文档 | 路径 | 说明 |
|------|------|------|
| **v5.0调整方案** | [./prompts/PROMPT_ENGINE_V5_ADJUSTMENT.md](./prompts/PROMPT_ENGINE_V5_ADJUSTMENT.md) | 从v4.0到v5.0的架构调整分析 |
| **小诺编排与提示词** | [./xiaonuo/XIAONUO_ORCHESTRATION_AND_PROMPTS.md](./xiaonuo/XIAONUO_ORCHESTRATION_AND_PROMPTS.md) | 小诺编排系统详细设计 |
| **上下文组装实现** | [./prompts/CONTEXT_ASSEMBLER_IMPLEMENTATION.md](./prompts/CONTEXT_ASSEMBLER_IMPLEMENTATION.md) | XiaonuoContextAssembler类实现方案 |
| **Phase 1智能体提示词** | [./prompts/PHASE1_AGENT_PROMPTS.md](./prompts/PHASE1_AGENT_PROMPTS.md) | 5个Phase 1智能体的详细提示词模板 |
| **Phase 2智能体提示词** | [./prompts/PHASE2_AGENT_PROMPTS.md](./prompts/PHASE2_AGENT_PROMPTS.md) | 2个Phase 2智能体的详细提示词模板 |
| **Phase 3智能体提示词** | [./prompts/PHASE3_AGENT_PROMPTS.md](./prompts/PHASE3_AGENT_PROMPTS.md) | 1个Phase 3智能体的详细提示词模板 |

### 5. 集成方案（部署）

| 文档 | 路径 | 说明 |
|------|------|------|
| **统一记忆系统** | [./memory/UNIFIED_MEMORY_SYSTEM_DESIGN.md](./memory/UNIFIED_MEMORY_SYSTEM_DESIGN.md) | 两层记忆架构（全局+项目）⭐ |
| **Gateway与智能体集成** | [./integration/GATEWAY_AGENT_INTEGRATION.md](./integration/GATEWAY_AGENT_INTEGRATION.md) | WebSocket控制平面 + gRPC数据平面 ⭐ |
| **Go网关集成** | [./integration/GATEWAY_INTEGRATION.md](./integration/GATEWAY_INTEGRATION.md) | REST API、gRPC API、WebSocket集成 |
| **成熟工作流整合** | [./integration/EXISTING_WORKFLOKS_INTEGRATION.md](./integration/EXISTING_WORKFLOKS_INTEGRATION.md) | 与现有专利撰写/审查意见答复工作流的整合方案 |
| **工具与外部接口集成** | [./integration/AGENT_TOOL_SKILL_MCP_INTEGRATION.md](./integration/AGENT_TOOL_SKILL_MCP_INTEGRATION.md) | 智能体工具配置、Skill集成、MCP集成 |
| **工具配置（修正版）** | [./integration/AGENT_TOOL_CONFIG_REVISION.md](./integration/AGENT_TOOL_CONFIG_REVISION.md) | 基于实际能力的工具配置 ⭐ |
| **法律世界模型配置** | [./integration/LEGAL_WORLD_MODEL_CONFIG_AND_PERFORMANCE.md](./integration/LEGAL_WORLD_MODEL_CONFIG_AND_PERFORMANCE.md) | 法律世界模型配置策略与性能分析 ⭐ |

### 6. 项目管理（总结）

| 文档 | 路径 | 说明 |
|------|------|------|
| **完整总结报告** | [../reports/ATHENA_TEAM_ARCHITECTURE_FINAL_REPORT_20260421.md](../reports/ATHENA_TEAM_ARCHITECTURE_FINAL_REPORT_20260421.md) | 项目概览、核心亮点、预期效果、下一步行动 |

---

## 🔍 按主题查找

### 主题：智能体定义

**相关文档**：
- [Phase 1智能体定义](../agents/PHASE1_AGENTS_DEFINITION.md)
  - 分析者（AnalyzerAgent）
  - 创造性分析智能体（CreativityAnalyzerAgent）
  - 新颖性分析智能体（NoveltyAnalyzerAgent）
  - 侵权分析智能体（InfringementAnalyzerAgent）
  - 申请文件审查智能体（ApplicationDocumentReviewerAgent）
  - 撰写审查智能体（WritingReviewerAgent）
  - 无效宣告分析智能体（InvalidationAnalyzerAgent）

### 主题：工作流程

**相关文档**：
- [场景工作流程设计](./workflows/SCENARIO_BASED_WORKFLOWS.md)
  - 专利检索（PATENT_SEARCH）
  - 技术分析（TECHNICAL_ANALYSIS）
  - 创造性分析（CREATIVITY_ANALYSIS）
  - 新颖性分析（NOVELTY_ANALYSIS）
  - 侵权分析（INFRINGEMENT_ANALYSIS）
- [执行模式](./workflows/SCENARIO_BASED_WORKFLOWS.md#执行模式详解)
  - 串行（Sequential）
  - 并行（Parallel）
  - 迭代（Iterative）
  - 混合（Hybrid）

### 主题：人机协作

**相关文档**：
- [人机交互设计](./workflows/USER_INTERACTION_DESIGN.md)
  - [计划展示](./workflows/USER_INTERACTION_DESIGN.md#计划展示)
  - [用户确认](./workflows/USER_INTERACTION_DESIGN.md#用户确认)
  - [控制按钮](./workflows/USER_INTERACTION_DESIGN.md#控制按钮)
  - [打断机制](./workflows/USER_INTERACTION_DESIGN.md#打断机制)
  - [迭代机制](./workflows/USER_INTERACTION_DESIGN.md#迭代机制)

### 主题：提示词工程

**相关文档**：
- [v5.0调整方案](./prompts/PROMPT_ENGINE_V5_ADJUSTMENT.md)
  - [五层架构](./prompts/PROMPT_ENGINE_V5_ADJUSTMENT.md#五层架构l0-l5)
  - [智能体提示词模板](./prompts/PROMPT_ENGINE_V5_ADJUSTMENT.md#智能体提示词模板)
- [小诺编排与提示词](./xiaonuo/XIAONUO_ORCHESTRATION_AND_PROMPTS.md)
  - [L0编排层](./xiaonuo/XIAONUO_ORCHESTRATION_AND_PROMPTS.md#l0-编排层提示词)
  - [场景识别](./xiaonuo/XIAONUO_ORCHESTRATION_AND_PROMPTS.md#场景识别)
  - [空闲时间验证](./xiaonuo/XIAONUO_ORCHESTRATION_AND_PROMPTS.md#空闲时间验证机制)
- [上下文组装实现](./prompts/CONTEXT_ASSEMBLER_IMPLEMENTATION.md)
  - [XiaonuoContextAssembler类](./prompts/CONTEXT_ASSEMBLER_IMPLEMENTATION.md#1-xiaonuocontextassembler-类设计)
  - [L0编排层提示词模板](./prompts/CONTEXT_ASSEMBLER_IMPLEMENTATION.md#2-l0编排层提示词模板)
  - [知识库动态加载](./prompts/CONTEXT_ASSEMBLER_IMPLEMENTATION.md#3-宝宸知识库动态加载机制)
- [Phase 1智能体提示词](./prompts/PHASE1_AGENT_PROMPTS.md)
  - [检索者](./prompts/PHASE1_AGENT_PROMPTS.md#1-检索者retrieveragent)
  - [分析者](./prompts/PHASE1_AGENT_PROMPTS.md#2-分析者analyzeragent)
  - [创造性分析智能体](./prompts/PHASE1_AGENT_PROMPTS.md#3-创造性分析智能体creativityanalyzeragent)
  - [新颖性分析智能体](./prompts/PHASE1_AGENT_PROMPTS.md#4-新颖性分析智能体noveltyanalyzeragent)
  - [侵权分析智能体](./prompts/PHASE1_AGENT_PROMPTS.md#5-侵权分析智能体infringementanalyzeragent)
- [Phase 2智能体提示词](./prompts/PHASE2_AGENT_PROMPTS.md)
  - [申请文件审查智能体](./prompts/PHASE2_AGENT_PROMPTS.md#1-申请文件审查智能体applicationdocumentrevieweragent)
  - [撰写审查智能体](./prompts/PHASE2_AGENT_PROMPTS.md#2-撰写审查智能体writingrevieweragent)
- [Phase 3智能体提示词](./prompts/PHASE3_AGENT_PROMPTS.md)
  - [无效宣告分析智能体](./prompts/PHASE3_AGENT_PROMPTS.md#1-无效宣告分析智能体invalidationanalyzeragent)

### 主题：数据格式

**相关文档**：
- [数据契约规范](./api/DATA_CONTRACT_SPECIFICATION.md)
  - [通用数据结构](./api/DATA_CONTRACT_SPECIFICATION.md#通用数据结构)
  - [智能体数据契约](./api/DATA_CONTRACT_SPECIFICATION.md#智能体数据契约)
  - [数据验证](./api/DATA_CONTRACT_SPECIFICATION.md#数据验证)

### 主题：记忆系统

**相关文档**：
- [统一记忆系统设计](./memory/UNIFIED_MEMORY_SYSTEM_DESIGN.md)
  - [两层记忆架构](./memory/UNIFIED_MEMORY_SYSTEM_DESIGN.md#-两层记忆架构)
  - [全局记忆](./memory/UNIFIED_MEMORY_SYSTEM_DESIGN.md#1️⃣-全局记忆-global-memory)
  - [项目记忆](./memory/UNIFIED_MEMORY_SYSTEM_DESIGN.md#2️⃣-项目记忆-project-memory)
  - [记忆系统API](./memory/UNIFIED_MEMORY_SYSTEM_DESIGN.md#3️⃣-记忆系统api设计)
  - [智能体集成](./memory/UNIFIED_MEMORY_SYSTEM_DESIGN.md#4️⃣-智能体集成)

### 主题：Gateway集成

**相关文档**：
- [Gateway与智能体集成方案](./integration/GATEWAY_AGENT_INTEGRATION.md)
  - [集成架构](./integration/GATEWAY_AGENT_INTEGRATION.md#-集成架构)
  - [WebSocket控制平面](./integration/GATEWAY_AGENT_INTEGRATION.md#12-websocket控制平面)
  - [gRPC数据平面](./integration/GATEWAY_AGENT_INTEGRATION.md#13-grpc数据平面)
  - [智能路由](./integration/GATEWAY_AGENT_INTEGRATION.md#2️⃣-智能路由设计)
  - [会话管理](./integration/GATEWAY_AGENT_INTEGRATION.md#3️⃣-会话管理)
  - [完整工作流程](./integration/GATEWAY_AGENT_INTEGRATION.md#5️⃣-完整工作流程)

### 主题：API集成

**相关文档**：
- [Go网关集成方案](./integration/GATEWAY_INTEGRATION.md)
  - [REST API](./integration/GATEWAY_INTEGRATION.md#rest-api兼容层)
  - [gRPC API](./integration/GATEWAY_INTEGRATION.md#grpc-api推荐)
  - [WebSocket集成](./integration/GATEWAY_INTEGRATION.md#websocket集成)

### 主题：工具与外部接口

**相关文档**：
- [工具与外部接口集成方案](./integration/AGENT_TOOL_SKILL_MCP_INTEGRATION.md)
  - [智能体工具配置](./integration/AGENT_TOOL_SKILL_MCP_INTEGRATION.md#1-智能体工具配置)
  - [工具权限控制](./integration/AGENT_TOOL_SKILL_MCP_INTEGRATION.md#2-工具权限控制)
  - [工具健康检查](./integration/AGENT_TOOL_SKILL_MCP_INTEGRATION.md#3-工具健康检查)
  - [Skill集成方案](./integration/AGENT_TOOL_SKILL_MCP_INTEGRATION.md#4-skill集成方案)
  - [MCP集成方案](./integration/AGENT_TOOL_SKILL_MCP_INTEGRATION.md#5-mcp集成方案)
  - [统一调用接口](./integration/AGENT_TOOL_SKILL_MCP_INTEGRATION.md#6-统一调用接口)

---

## 📊 核心概念速查

### 小诺0号原则

**定义**：任何复杂任务在执行前必须先制定执行计划，并向用户展示，获得确认后才能执行。

**文档**：[工作流程设计](./workflows/SCENARIO_BASED_WORKFLOWS.md#1-先规划再执行小诺0号原则)

### 双格式输出

**定义**：每个智能体必须同时输出JSON格式（机器可读）和Markdown格式（人类可读）。

**文档**：[数据契约规范](./api/DATA_CONTRACT_SPECIFICATION.md#1-双格式输出)

### 质量优先原则

**定义**：专利和法律业务以质量为最高原则，性能和成本服从于质量。

**文档**：[架构设计总览](./ATHENA_TEAM_ARCHITECTURE_V2.md#核心设计原则)

### 人机协同原则

**定义**：用户是执行复杂任务的决策者，智能体是执行者和建议者。

**文档**：[人机交互设计](./workflows/USER_INTERACTION_DESIGN.md#2-人机协同原则)

---

## 🚀 实施路径

### Phase 1（当前）

**时间**：4-6周

**智能体**：
1. 分析者（AnalyzerAgent）
2. 创造性分析智能体（CreativityAnalyzerAgent）
3. 新颖性分析智能体（NoveltyAnalyzerAgent）
4. 侵权分析智能体（InfringementAnalyzerAgent）

**文档**：
- [完整总结报告 - Phase 1实施](../reports/ATHENA_TEAM_ARCHITECTURE_FINAL_REPORT_20260421.md#phase-1实施预计4-6周)

### Phase 2（计划中）

**时间**：4-6周后

**智能体**：
1. 申请文件审查智能体（ApplicationDocumentReviewerAgent）
2. 撰写审查智能体（WritingReviewerAgent）

**文档**：
- [完整总结报告 - Phase 2实施](../reports/ATHENA_TEAM_ARCHITECTURE_FINAL_REPORT_20260421.md#phase-2实施预计4-6周后)

### Phase 3（规划中）

**时间**：8-12周后

**智能体**：
1. 无效宣告分析智能体（InvalidationAnalyzerAgent）

**文档**：
- [完整总结报告 - Phase 3实施](../reports/ATHENA_TEAM_ARCHITECTURE_FINAL_REPORT_20260421.md#phase-3实施预计8-12周后)

---

## 🔗 外部资源

### 知识库

- **宝宸知识库**：`/Users/xujian/Library/Mobile Documents/iCloud~md~obsidian/Documents/宝宸知识库/Wiki/`
  - 专利实务/创造性/（17个文件）
  - 复审无效/创造性/（无效决定裁判规则分析）

### 代码库

- **核心框架**：`/Users/xujian/Athena工作平台/core/`
  - `agents/xiaona/` - 小娜智能体
  - `orchestration/` - 编排系统

### 网关

- **Go网关**：`/Users/xujian/Athena工作平台/gateway-unified/`
  - 统一入口（端口8005）
  - gRPC通信优化

---

## 📞 联系方式

- **项目负责人**: 徐健 (xujian519@gmail.com)
- **技术支持**: Claude Code
- **文档位置**: `/Users/xujian/Athena工作平台/docs/`

---

## 📝 文档更新历史

| 版本 | 日期 | 更新内容 | 作者 |
|------|------|---------|------|
| 1.0 | 2026-04-21 | 初始版本，完整架构设计文档 | Claude Code + 徐健 |

---

**End of Index**
