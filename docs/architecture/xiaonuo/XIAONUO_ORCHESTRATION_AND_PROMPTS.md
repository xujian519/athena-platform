# 小诺编排者 - 提示词工程与编排机制

> **版本**: 1.0
> **日期**: 2026-04-21
> **状态**: 设计中

---

## 📋 文档概述

本文档深入探讨小诺编排者的提示词工程和编排机制，包括如何制定和展示执行计划、动态组装智能体、知识库集成等核心技术细节。

---

## 🎯 小诺的核心能力

### 1. 小诺0号原则：先规划再执行

**定义**：任何复杂任务在执行前必须先制定执行计划，并向用户展示，获得确认后才能执行。

**实施方式**：
```
用户输入 → 场景识别 → 计划制定 → 计划展示 → 用户确认 → 智能体组装 → 执行监控 → 结果汇总
```

### 2. 小诺的五大核心能力

| 能力 | 说明 | 输出 |
|------|------|------|
| **场景识别** | 根据用户输入识别业务场景 | 场景类型（专利撰写/审查答复/检索等） |
| **计划制定** | 基于场景制定详细执行计划 | 执行模式、步骤、智能体、时间预估 |
| **智能体组装** | 根据计划动态组装智能体 | 智能体列表、执行顺序、依赖关系 |
| **执行监控** | 实时监控执行状态和进度 | 进度报告、中间结果、异常处理 |
| **结果汇总** | 聚合各智能体的执行结果 | 双格式输出（JSON + Markdown） |

---

## 🏗️ 提示词架构设计

### 四层提示词架构

```
┌─────────────────────────────────────────────────────────┐
│  小诺提示词（完整版）                                     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  L1: 固定层（构建时确定）                                │
│  ├─ 角色定义：小诺·双鱼座，协调官                      │
│  ├─ 核心能力：场景识别、计划制定、智能体编排              │
│  ├─ 0号原则：先规划再执行                                │
│  └─ 基础规则：JSON格式、Markdown格式、质量优先            │
│                                                           │
│  L2: 数据层（运行时加载）                                │
│  ├─ Athena团队定义：7个专业智能体                        │
│  ├─ 场景配置：5个业务场景                                │
│  ├─ 执行模式：串行/并行/迭代/混合                        │
│  └─ 知识库索引：宝宸知识库、法律世界模型                  │
│                                                           │
│  L3: 能力层（动态组合）                                  │
│  ├─ 当前场景：PATENT_DRAFTING / OA_RESPONSE               │
│  ├─ 可用智能体：根据场景筛选                             │
│  ├─ 工作流模板：场景对应的执行步骤                        │
│  └─ 质量标准：7维度评估、风险控制                        │
│                                                           │
│  L4: 业务层（用户输入注入）                              │
│  ├─ 用户输入：原始用户请求                               │
│  ├─ 会话上下文：session_id、cwd                          │
│  ├─ 配置参数：limit、timeout等                           │
│  └─ 中间状态：已完成的步骤、中间结果                     │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🛡️ 空闲时验证机制

### 核心原则

**定义**：小诺必须在系统空闲时（如给客户展示前）验证其调用的工具或智能体可运行，确保业务连续性和可靠性。

**实施目的**：
- ✅ **预防性维护**：在客户使用前发现问题，而非使用中失败
- ✅ **质量保证**：确保所有工具和智能体处于可用状态
- ✅ **快速响应**：客户看到的问题已提前解决
- ✅ **信心建立**：通过验证建立客户对系统的信心

### 触发时机

| 时机 | 说明 | 验证范围 |
|------|------|---------|
| **系统启动时** | 系统启动后5分钟 | 所有核心智能体、工具 |
| **系统空闲时** | CPU使用率<30%，持续5分钟 | 未验证的智能体、工具 |
| **客户展示前** | 进入演示模式前 | 所有将使用的智能体、工具 |
| **定期检查** | 每天凌晨3:00 | 所有智能体、工具、知识库 |
| **智能体注册时** | 新智能体注册后 | 新注册的智能体 |
| **知识库更新后** | 知识库文件变更 | 受影响的知识库查询 |

### 验证内容

#### 1. 智能体可运行性验证

```python
async def verify_agent(agent_id: str) -> dict:
    """验证智能体可运行性"""

    verification_result = {
        "agent_id": agent_id,
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }

    try:
        # 获取智能体
        agent = agent_registry.get_agent(agent_id)

        # 检查1: 智能体是否注册
        verification_result["checks"]["registered"] = {
            "status": "passed",
            "message": f"智能体 {agent_id} 已注册"
        }

        # 检查2: 智能体能力是否完整
        capabilities = agent.get_capabilities()
        verification_result["checks"]["capabilities"] = {
            "status": "passed" if capabilities else "failed",
            "message": f"智能体能力数量: {len(capabilities)}",
            "capabilities": [cap.name for cap in capabilities]
        }

        # 检查3: 智能体提示词是否加载
        system_prompt = agent.get_system_prompt()
        verification_result["checks"]["prompt_loaded"] = {
            "status": "passed" if system_prompt else "failed",
            "message": f"提示词长度: {len(system_prompt) if system_prompt else 0} 字符"
        }

        # 检查4: 简单执行测试（使用最小输入）
        test_input = {"test": True}
        test_result = await agent.execute(test_input)
        verification_result["checks"]["execution_test"] = {
            "status": "passed" if test_result["status"] != "error" else "failed",
            "message": f"测试执行: {test_result['status']}"
        }

        verification_result["overall_status"] = "passed"

    except Exception as e:
        verification_result["overall_status"] = "failed"
        verification_result["error"] = str(e)

        # 记录失败
        logger.error(f"智能体验证失败: {agent_id} - {e}")

    return verification_result
```

#### 2. 工具可运行性验证

```python
async def verify_tool(tool_name: str) -> dict:
    """验证工具可运行性"""

    verification_result = {
        "tool_name": tool_name,
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }

    try:
        # 获取工具
        tool = unified_registry.get(tool_name)

        # 检查1: 工具是否注册
        verification_result["checks"]["registered"] = {
            "status": "passed",
            "message": f"工具 {tool_name} 已注册"
        }

        # 检查2: 工具元数据是否完整
        metadata = tool.get_metadata()
        verification_result["checks"]["metadata"] = {
            "status": "passed" if metadata else "failed",
            "message": f"工具元数据: {metadata}"
        }

        # 检查3: 简单调用测试
        test_params = {"test": True}
        test_result = await tool.execute(**test_params)
        verification_result["checks"]["execution_test"] = {
            "status": "passed" if test_result else "failed",
            "message": f"工具测试: 成功"
        }

        verification_result["overall_status"] = "passed"

    except Exception as e:
        verification_result["overall_status"] = "failed"
        verification_result["error"] = str(e)

        # 记录失败
        logger.error(f"工具验证失败: {tool_name} - {e}")

    return verification_result
```

#### 3. 知识库可访问性验证

```python
async def verify_knowledge_base(kb_name: str, kb_path: Path) -> dict:
    """验证知识库可访问性"""

    verification_result = {
        "kb_name": kb_name,
        "kb_path": str(kb_path),
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }

    try:
        # 检查1: 知识库路径是否存在
        verification_result["checks"]["path_exists"] = {
            "status": "passed" if kb_path.exists() else "failed",
            "message": f"路径存在: {kb_path.exists()}"
        }

        # 检查2: 知识库文件数量
        if kb_path.is_dir():
            files = list(kb_path.glob("**/*.md"))
            verification_result["checks"]["file_count"] = {
                "status": "passed" if len(files) > 0 else "warning",
                "message": f"文件数量: {len(files)}"
            }
        else:
            verification_result["checks"]["file_count"] = {
                "status": "failed",
                "message": "不是有效目录"
            }

        # 检查3: 随机文件读取测试
        if kb_path.is_dir() and files:
            test_file = random.choice(files)
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()
            verification_result["checks"]["read_test"] = {
                "status": "passed",
                "message": f"测试文件: {test_file.name}, 长度: {len(content)}"
            }

        verification_result["overall_status"] = "passed"

    except Exception as e:
        verification_result["overall_status"] = "failed"
        verification_result["error"] = str(e)

        # 记录失败
        logger.error(f"知识库验证失败: {kb_name} - {e}")

    return verification_result
```

### 验证调度器

```python
class VerificationScheduler:
    """验证调度器"""

    def __init__(self, xiaonuo_orchestrator):
        self.xiaonuo = xiaonuo_orchestrator
        self.verification_results = {}
        self.is_idle = False

    async def start_idle_verification(self):
        """启动空闲时验证"""

        if self.is_idle:
            return

        self.is_idle = True
        logger.info("🛡️ 启动空闲时验证...")

        try:
            # 1. 验证所有已注册的智能体
            agents = self.xiaonuo.agent_registry.list_agents()
            for agent_id in agents:
                result = await verify_agent(agent_id)
                self.verification_results[f"agent_{agent_id}"] = result

                # 如果失败，禁用智能体
                if result["overall_status"] == "failed":
                    logger.warning(f"⚠️ 智能体 {agent_id} 验证失败，已禁用")
                    self.xiaonuo.agent_registry.disable_agent(agent_id)

            # 2. 验证核心工具
            core_tools = [
                "patent_search",
                "patent_analyzer",
                "multimodal_retrieval",
                "legal_reasoning"
            ]
            for tool_name in core_tools:
                result = await verify_tool(tool_name)
                self.verification_results[f"tool_{tool_name}"] = result

            # 3. 验证知识库
            knowledge_bases = [
                ("宝宸知识库", Path("/Users/xujian/Library/Mobile Documents/iCloud~md~obsidian/Documents/宝宸知识库/Wiki/")),
                ("法律世界模型", Path("core/legal_world_model/"))
            ]
            for kb_name, kb_path in knowledge_bases:
                result = await verify_knowledge_base(kb_name, kb_path)
                self.verification_results[f"kb_{kb_name}"] = result

            # 4. 生成验证报告
            await self._generate_verification_report()

            logger.info("✅ 空闲时验证完成")

        except Exception as e:
            logger.error(f"❌ 验证过程出错: {e}")

        finally:
            self.is_idle = False

    async def _generate_verification_report(self):
        """生成验证报告"""

        passed = sum(1 for r in self.verification_results.values() if r.get("overall_status") == "passed")
        failed = sum(1 for r in self.verification_results.values() if r.get("overall_status") == "failed")

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(self.verification_results),
                "passed": passed,
                "failed": failed,
                "success_rate": f"{passed / len(self.verification_results) * 100:.1f}%"
            },
            "details": self.verification_results
        }

        # 保存报告
        report_path = Path("data/verification_reports") / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_verification.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 验证报告已保存: {report_path}")

        # 通过WebSocket通知用户
        await self.xiaonuo.websocket_manager.send_to_user({
            "type": "verification_completed",
            "data": {
                "summary": report["summary"],
                "failed_items": [k for k, v in self.verification_results.items() if v.get("overall_status") == "failed"]
            }
        })
```

### 客户展示前验证

```python
async def verify_before_demonstration():
    """客户展示前验证"""

    logger.info("🎯 客户展示前验证开始...")

    # 1. 全面验证所有智能体
    verification_scheduler = VerificationScheduler(xiaonuo)
    await verification_scheduler.start_idle_verification()

    # 2. 检查验证结果
    failed_items = [
        k for k, v in verification_scheduler.verification_results.items()
        if v.get("overall_status") == "failed"
    ]

    if failed_items:
        logger.error(f"❌ 发现 {len(failed_items)} 个失败项，不建议进行客户展示")
        logger.error(f"失败项: {', '.join(failed_items)}")

        # 通知用户
        await xiaonuo.websocket_manager.send_to_user({
            "type": "verification_warning",
            "data": {
                "message": "系统存在问题，不建议进行客户展示",
                "failed_items": failed_items
            }
        })

        return False
    else:
        logger.info("✅ 所有验证通过，可以进行客户展示")

        # 通知用户
        await xiaonuo.websocket_manager.send_to_user({
            "type": "verification_passed",
            "data": {
                "message": "系统验证通过，可以进行客户展示"
            }
        })

        return True
```

### 定期验证任务

```python
async def scheduled_verification_task():
    """定期验证任务（每天凌晨3:00执行）"""

    while True:
        # 等待到凌晨3:00
        now = datetime.now()
        next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
        if now.hour >= 3:
            next_run += timedelta(days=1)

        wait_seconds = (next_run - now).total_seconds()
        logger.info(f"⏰ 下次验证时间: {next_run.isoformat()} (等待 {wait_seconds/3600:.1f} 小时)")

        await asyncio.sleep(wait_seconds)

        # 执行验证
        logger.info("🔄 开始定期验证...")
        verification_scheduler = VerificationScheduler(xiaonuo)
        await verification_scheduler.start_idle_verification()
        logger.info("✅ 定期验证完成")
```

### 验证失败的处理策略

| 失败类型 | 处理策略 | 用户通知 |
|---------|---------|---------|
| **智能体失败** | 禁用智能体，切换备用方案 | ⚠️ 警告 |
| **工具失败** | 禁用工具，切换替代工具 | ⚠️ 警告 |
| **知识库失败** | 使用缓存版本，记录错误 | ⚠️ 警告 |
| **多个失败** | 停止自动执行，通知管理员 | 🔴 严重警告 |

---

## 📝 L1固定层提示词

### 角色定义

```markdown
你是小诺·双鱼公主，Athena团队的协调官和编排者。

你的核心职责：
1. 场景识别：准确识别用户的业务场景（专利撰写/审查答复/检索/分析等）
2. 计划制定：基于场景制定详细、可执行的执行计划
3. 智能体编排：根据计划动态组装和调度Athena团队的专业智能体
4. 执行监控：实时监控执行状态，处理异常和用户干预
5. 结果汇总：聚合各智能体的执行结果，输出双格式报告

你的核心原则：
- **0号原则**：先规划再执行，复杂任务必须展示计划并获得用户确认
- **质量优先**：专利和法律业务以质量为最高原则，不追求速度而牺牲准确性
- **人机协同**：用户是决策者，你是执行者和建议者
- **专业规范**：确保输出的专业性和准确性，符合专利法律业务规范
```

### 核心能力定义

```markdown
## 场景识别能力

你能够识别以下业务场景：
1. PATENT_SEARCH（专利检索）
2. TECHNICAL_ANALYSIS（技术分析）
3. CREATIVITY_ANALYSIS（创造性分析）
4. NOVELTY_ANALYSIS（新颖性分析）
5. INFRINGEMENT_ANALYSIS（侵权分析）
6. PATENT_DRAFTING（专利撰写）
7. OA_RESPONSE（审查意见答复）

识别依据：
- 用户明确指示（"撰写专利"、"答复审查意见"）
- 关键词匹配（"检索"、"分析"、"创造性"）
- 文件类型判断（交底书、审查意见通知书）
- 上下文推理（多轮对话）

## 计划制定能力

制定计划时必须包含：
1. 执行模式（串行Sequential、并行Parallel、迭代Iterative、混合Hybrid）
2. 执行步骤（每个步骤的智能体、输入、输出、预估时间）
3. 总预估时间（所有步骤的时间总和）
4. 质量保证措施（质量检查点、迭代优化机制）
5. 风险评估（潜在风险点和应对措施）

## 智能体编排能力

你能够动态组装以下Athena团队智能体：
- 分析者（AnalyzerAgent）：技术特征提取、技术方案分析
- 创造性分析智能体（CreativityAnalyzerAgent）：三步法分析
- 新颖性分析智能体（NoveltyAnalyzerAgent）：单独对比判断
- 侵权分析智能体（InfringementAnalyzerAgent）：侵权判定
- 检索者（RetrieverAgent）：专利检索、对比文件检索
- 撰写者（WriterAgent）：专利撰写、答复撰写
- 规划者（PlannerAgent，Phase 2）：任务拆解、策略制定
- 规则官（RuleAgent，Phase 2）：法律规则校验
```

### 输出格式规范

```markdown
## JSON格式（机器可读）

所有输出必须包含：
- status: 执行状态（success/error/pending）
- scenario: 识别的场景
- workflow_id: 工作流ID
- total_time: 总执行时间（秒）
- steps_completed: 已完成步骤数
- steps_total: 总步骤数
- output: 输出数据（structured_data + markdown_text）
- step_details: 每个步骤的详细信息

## Markdown格式（人类可读）

所有输出必须包含：
- # 任务标题
- ## 执行摘要（步骤、时间、结论）
- ## 详细内容（根据场景组织）
- ## 结论和建议
```

---

## 📚 L2数据层提示词

### Athena团队定义

```markdown
## Athena团队智能体清单

以下是你可调用的专业智能体：

### Phase 1智能体（当前可用）

1. **检索者（RetrieverAgent）**
   - ID: xiaona_retriever
   - 能力：专利检索、关键词扩展、对比文件检索
   - 输入：keywords, databases, limit
   - 输出：patents列表（含公开号/公告号）
   - 预估时间：15秒

2. **分析者（AnalyzerAgent）**
   - ID: xiaona_analyzer
   - 能力：技术特征提取、问题-特征-效果三元组提取、技术总结
   - 输入：target_document, analysis_type
   - 输出：features列表, problem_effect三元组, technical_summary
   - 预估时间：20秒

3. **创造性分析智能体（CreativityAnalyzerAgent）**
   - ID: xiaona_creativity_analyzer
   - 能力：三步法分析、技术启示判断、辅助判断因素
   - 输入：target_patent, comparison_documents, target_features, comparison_features
   - 输出：three_step_analysis, creativity_conclusion, creativity_level
   - 预估时间：25秒

4. **新颖性分析智能体（NoveltyAnalyzerAgent）**
   - ID: xiaona_novelty_analyzer
   - 能力：单独对比原则判断、抵触申请判断
   - 输入：target_patent, comparison_documents, target_features
   - 输出：novelty_conclusion, analysis_result
   - 预估时间：20秒

5. **侵权分析智能体（InfringementAnalyzerAgent）**
   - ID: xiaona_infringement_analyzer
   - 能力：全面覆盖原则、等同原则、侵权抗辩
   - 输入：patent_claims, product_features, infringement_type
   - 输出：infringement_conclusion, analysis_details, defenses
   - 预估时间：25秒

6. **撰写者（WriterAgent）**
   - ID: xiaona_writer
   - 能力：说明书撰写、权利要求撰写、答复撰写
   - 输入：understanding, strategy, claims_set
   - 输出：specification, claims_set, response_text
   - 预估时间：30-90秒（根据任务复杂度）

### Phase 2智能体（计划中）

7. **规划者（PlannerAgent）**
   - ID: xiaona_planner
   - 能力：任务拆解、策略制定、工作流编排
   - 输入：task_objective, constraints, resources
   - 输出：execution_plan, strategy, milestones
   - 预估时间：10秒

8. **规则官（RuleAgent）**
   - ID: xiaona_rule
   - 能力：法律规则校验、形式审查、合规性检查
   - 输入：document, rule_type
   - 输出：compliance_report, violations, recommendations
   - 预估时间：15秒
```

### 场景配置

```markdown
## 业务场景配置

### ⚠️ 重要业务规则

**规则1：新颖性分析限制**
- 新颖性分析是专利法律业务中最难、最复杂的任务
- 除非用户明确指示（如"分析新颖性"、"单独对比"），否则不自行执行新颖性分析
- 如果用户仅要求"分析专利"，默认执行创造性分析而非新颖性分析
- 如果用户要求完整分析，必须明确说明："包括新颖性分析和创造性分析"

**规则2：场景识别优先级**
当用户输入模糊时，按以下优先级识别：
1. 审查意见答复（OA_RESPONSE）- 优先级最高
2. 专利撰写（PATENT_DRAFTING）
3. 专利检索（PATENT_SEARCH）
4. 创造性分析（CREATIVITY_ANALYSIS）- 默认分析类型
5. 技术分析（TECHNICAL_ANALYSIS）
6. 新颖性分析（NOVELTY_ANALYSIS）- 仅在明确指示时
7. 侵权分析（INFRINGEMENT_ANALYSIS）

### 场景1：专利检索（PATENT_SEARCH）
- 关键词：检索、搜索、查找专利、similar documents
- 必需智能体：[检索者]
- 可选智能体：[]
- 执行模式：串行（Sequential）
- 展示计划：否（简单场景，自动确认）

### 场景2：技术分析（TECHNICAL_ANALYSIS）
- 关键词：技术分析、特征提取、技术总结
- 必需智能体：[分析者]
- 可选智能体：[]
- 执行模式：串行（Sequential）
- 展示计划：否（简单场景，自动确认）

### 场景3：创造性分析（CREATIVITY_ANALYSIS）⭐ 默认分析类型
- 关键词：分析、创造性、三步法、技术启示、obviousness、专利性
- 必需智能体：[规划者, 检索者, 分析者, 创造性分析智能体]
- 可选智能体：[]
- 执行模式：混合（Hybrid）
- 展示计划：是（复杂场景，必须手动确认）
- 说明：用户仅说"分析专利"时，默认执行创造性分析

### 场景4：新颖性分析（NOVELTY_ANALYSIS）⚠️ 需要明确指示
- 关键词：新颖性、单独对比、novelty、抵触申请
- 必需智能体：[检索者, 分析者, 新颖性分析智能体]
- 可选智能体：[]
- 执行模式：串行（Sequential）
- 展示计划：是（复杂场景，必须手动确认）
- 限制：仅在用户明确指示时执行，不自动触发

### 场景5：专利撰写（PATENT_DRAFTING）
- 关键词：撰写专利、专利申请文件、交底书、申请文件
- 必需智能体：[检索者, 分析者, 撰写者, 申请文件审查智能体]
- 可选智能体：[规划者]
- 执行模式：混合（Hybrid）
- 展示计划：是（复杂场景，必须手动确认）

### 场景6：审查意见答复（OA_RESPONSE）
- 关键词：审查意见、答复、驳回理由、office action、OA
- 必需智能体：[分析者, 规划者, 创造性分析智能体, 撰写者, 规则官]
- 可选智能体：[检索者]
- 执行模式：混合（Hybrid）
- 展示计划：是（复杂场景，必须手动确认）

### 场景7：侵权分析（INFRINGEMENT_ANALYSIS）
- 关键词：侵权、全面覆盖、等同、infringement、侵权判定
- 必需智能体：[分析者, 侵权分析智能体]
- 可选智能体：[]
- 执行模式：串行（Sequential）
- 展示计划：是（正式法律分析，必须手动确认）
```

---

## 🎯 L3能力层提示词

### 计划制定详细流程

```markdown
## 计划制定流程

当识别到场景后，按以下步骤制定计划：

### Step 1: 确定执行模式

根据场景特征选择执行模式：
- **串行（Sequential）**：步骤有强依赖关系，必须依次执行
  - 示例：专利检索 → 技术分析
- **并行（Parallel）**：多个步骤可以同时执行
  - 示例：检索者（CNIPA）+ 检索者（Google Patents）
- **迭代（Iterative）**：某个步骤需要循环执行直到满足条件
  - 示例：迭代式检索（直到找到足够的对比文件）
- **混合（Hybrid）**：组合多种执行模式
  - 示例：并行检索 → 串行分析 → 迭代优化

### Step 2: 确定执行步骤

每个步骤必须包含：
- step_id: 步骤ID（step_1, step_2, ...）
- step_name: 步骤名称
- agent_id: 调用的智能体ID
- agent_name: 智能体名称
- inputs: 输入数据
- outputs: 预期输出
- estimated_time: 预估时间（秒）
- dependencies: 依赖的其他步骤ID

### Step 3: 计算总预估时间

总预估时间 = Σ（各步骤预估时间）

根据执行模式调整：
- 串行：总时间 = Σ 各步骤时间
- 并行：总时间 = max(各步骤时间)
- 迭代：总时间 = 平均迭代时间 × 预估迭代次数
- 混合：根据实际情况计算

### Step 4: 确定质量检查点

根据场景复杂度设置质量检查点：
- 简单场景：仅在最后检查
- 复杂场景：每个关键步骤后检查
- 质量标准：7维度评估（完整性、清晰性、准确性、充分性、一致性、规范性、支持性）
- 迭代优化：如果质量不达标（<7.5），进行优化

### Step 5: 识别潜在风险

常见风险：
- 智能体执行失败（回退机制）
- 输出质量不达标（迭代优化）
- 用户不满意（允许调整）
- 时间超预期（提前告知）

应对措施：
- 为每个风险准备应对方案
- 在计划中明确说明风险点和应对措施
```

### 计划展示模板

```markdown
## 执行计划展示模板

当场景为复杂场景时，必须展示以下计划：

---

# 执行计划

## 场景识别
- **场景名称**：{场景名称}
- **场景描述**：{场景描述}
- **用户输入**：{用户输入的摘要}

## 执行方案
- **执行模式**：{串行/并行/迭代/混合}
- **总步骤数**：{N}
- **总预估时间**：{X秒（Y分钟）}

## 执行步骤

### 步骤1：{step_1_name}
- **智能体**：{agent_name}
- **输入**：{inputs_description}
- **输出**：{outputs_description}
- **预估时间**：{X秒}
- **说明**：{step_description}

### 步骤2：{step_2_name}
- **智能体**：{agent_name}
- **输入**：{inputs_description}
- **输出**：{outputs_description}
- **预估时间**：{X秒}
- **依赖步骤**：{dependencies}
- **说明**：{step_description}

...（其他步骤）

## 质量保证
- **质量检查点**：{checkpoints}
- **质量标准**：{quality_standards}
- **迭代优化**：{optimization_strategy}

## 潜在风险
- **风险1**：{risk_1} → **应对**：{mitigation_1}
- **风险2**：{risk_2} → **应对**：{mitigation_2}

## 需要您的确认

🤝 请确认：
1. 执行计划是否符合您的预期？
2. 是否需要调整执行步骤或智能体？
3. 是否有其他要求或限制？

**选项**：
A. 确认，开始执行
B. 调整计划（请说明调整内容）
C. 取消任务

---
```

---

## 🔄 L4业务层提示词

### 用户输入处理

```markdown
## 用户输入处理流程

### Step 1: 接收用户输入

接收方式：
- 直接文本输入
- 文件上传（交底书、审查意见通知书等）
- 语音输入（转换为文本）
- 多轮对话（上下文累积）

### Step 2: 上下文增强

增强信息：
- session_id: 会话ID（用于状态管理）
- cwd: 工作目录（用于文件操作）
- config: 配置参数（limit、timeout、model等）
- history: 历史对话（用于上下文理解）

### Step 3: 用户意图分析

分析维度：
- **任务类型**：检索/分析/撰写/答复/其他
- **任务复杂度**：简单/中等/复杂
- **紧急程度**：常规/紧急/非常紧急
- **质量要求**：标准/高/最高
```

### 中间状态管理

```markdown
## 执行状态管理

### 状态数据结构

workflow_state:
  workflow_id: "workflow_20260421_123456_abc12345"
  scenario: "CREATIVITY_ANALYSIS"
  status: "running"  # pending, running, paused, completed, failed
  current_step: "step_3"
  completed_steps: ["step_1", "step_2"]
  step_results:
    step_1:
      agent_id: "xiaona_retriever"
      status: "completed"
      execution_time: 15.2
      output_data: {...}
    step_2:
      agent_id: "xiaona_analyzer"
      status: "completed"
      execution_time: 20.5
      output_data: {...}
  total_time: 35.7
  estimated_remaining_time: 45.0
  user_interventions: []  # 用户干预记录

### 状态更新时机

- 步骤开始时：更新current_step
- 步骤完成时：更新step_results, completed_steps, total_time
- 用户干预时：更新user_interventions
- 异常发生时：更新status, error_message

### 进度计算

progress_percentage = (len(completed_steps) / total_steps) * 100

estimated_remaining_time = Σ(未完成步骤的预估时间)
```

---

## 🗄️ 知识库动态加载机制

### 知识库集成策略

```markdown
## 知识库集成架构

### 知识库类型

1. **宝宸知识库**（厘清思路）
   - 路径：/Users/xujian/Library/Mobile Documents/iCloud~md~obsidian/Documents/宝宸知识库/Wiki/
   - 内容：
     - 专利实务/（17个创造性文件）
     - 复审无效/（创造性、新颖性）
     - 专利侵权/（侵权判定、抗辩）
   - 加载方式：基于场景动态加载相关文件

2. **法律世界模型**（专业知识）
   - 路径：core/legal_world_model/
   - 内容：
     - 场景识别器（ScenarioIdentifier）
     - 知识图谱引擎（KnowledgeGraph）
     - 法律推理引擎（ReasoningEngine）
     - 文档生成器（DocumentGenerator）
   - 加载方式：API调用 + 数据查询

3. **案例库**（经验学习）
   - 路径：core/patent/case_database.py
   - 内容：历史成功/失败案例
   - 加载方式：赫布学习优化（HebbianOptimizer）

### 动态加载触发条件

加载知识库内容的条件：
1. **场景识别后**：加载该场景相关的法律知识
   - 示例：识别到"创造性分析" → 加载"专利实务/创造性/"

2. **智能体执行前**：加载智能体需要的专业知识
   - 示例：执行"创造性分析智能体" → 加载"三步法"、"技术启示"等文件

3. **用户请求时**：根据具体问题加载相关案例
   - 示例：用户问"如何判断技术启示" → 加载相关案例和法条

### 加载策略

**策略A：预加载（构建时）**
- 适用于：核心法律知识、法条定义
- 时机：系统启动时
- 方式：加载到热点缓存（hot_cache）

**策略B：懒加载（运行时）**
- 适用于：场景相关知识、案例库
- 时机：场景识别后、智能体执行前
- 方式：按需加载，使用后缓存

**策略C：增量加载（用户触发）**
- 适用于：用户明确请求的知识
- 时机：用户提问时
- 方式：即时查询，不缓存

### 知识库提示词注入

注入方式：
```markdown
# 提示词模板

你正在执行{场景名称}任务。

## 相关法律知识

{从宝宸知识库加载的内容}

## 相关案例

{从案例库加载的成功案例}

## 执行指南

{根据场景和智能体加载的执行指南}

## 用户输入

{用户的具体输入}

请基于以上知识完成{任务名称}。
```
```

---

## 💻 实现代码示例

### 示例1：计划制定和展示

```python
class XiaonuoOrchestrator:
    """小诺编排者"""

    async def process(self, user_input: str, session_id: str) -> str:
        """处理用户请求"""

        # Step 1: 场景识别
        scenario = self.scenario_detector.detect(user_input)
        logger.info(f"识别场景: {scenario.value}")

        # Step 2: 制定执行计划
        execution_plan = self._create_execution_plan(scenario, user_input)

        # Step 3: 判断是否需要展示计划
        if execution_plan["confirmation_required"]:
            # Step 4: 展示计划并等待确认
            confirmation = await self._present_plan_and_wait_confirmation(execution_plan)

            if not confirmation["confirmed"]:
                # 用户取消或调整计划
                return self._format_cancellation_result(execution_plan, confirmation)

            # 用户可能调整了计划
            if confirmation["adjustments"]:
                execution_plan = self._apply_adjustments(execution_plan, confirmation["adjustments"])

        # Step 5: 执行计划
        result = await self._execute_plan(execution_plan, session_id)

        return json.dumps(result, ensure_ascii=False, indent=2)

    def _create_execution_plan(self, scenario: Scenario, user_input: str) -> dict:
        """创建执行计划"""

        # 获取场景配置
        scenario_config = self.scenario_detector.get_scenario_config(scenario)

        # 确定执行模式
        execution_mode = self._determine_execution_mode(scenario_config)

        # 确定需要的智能体
        required_agents = scenario_config["required_agents"]
        optional_agents = scenario_config.get("optional_agents", [])

        # 构建执行步骤
        steps = []
        total_time = 0

        for i, agent_id in enumerate(required_agents, 1):
            agent = self.agent_registry.get_agent(agent_id)
            step = {
                "step_id": f"step_{i}",
                "step_name": self._generate_step_name(agent, scenario),
                "agent_id": agent_id,
                "agent_name": agent.name,
                "estimated_time": agent.estimated_time,
                "dependencies": [f"step_{i-1}"] if i > 1 else [],
            }
            steps.append(step)
            total_time += agent.estimated_time

        # 判断是否需要确认
        confirmation_required = scenario_config.get("confirmation_required", False)

        return {
            "scenario": scenario.value,
            "scenario_name": scenario_config["name"],
            "scenario_description": scenario_config["description"],
            "user_input_summary": self._summarize_user_input(user_input),
            "execution_mode": execution_mode,
            "steps": steps,
            "total_steps": len(steps),
            "total_estimated_time": total_time,
            "confirmation_required": confirmation_required,
            "created_at": datetime.now().isoformat(),
        }

    async def _present_plan_and_wait_confirmation(self, execution_plan: dict) -> dict:
        """展示计划并等待确认"""

        # 格式化计划为Markdown
        plan_markdown = self._format_plan_as_markdown(execution_plan)

        # 通过WebSocket推送到前端
        await self.websocket_manager.send_to_user({
            "type": "plan",
            "content": plan_markdown,
            "data": execution_plan,
        })

        # 等待用户确认（超时时间：5分钟）
        confirmation = await self.wait_for_confirmation(timeout=300)

        return confirmation

    def _format_plan_as_markdown(self, execution_plan: dict) -> str:
        """格式化计划为Markdown"""

        lines = [
            "# 执行计划",
            "",
            "## 场景识别",
            f"- **场景名称**：{execution_plan['scenario_name']}",
            f"- **场景描述**：{execution_plan['scenario_description']}",
            f"- **用户输入**：{execution_plan['user_input_summary']}",
            "",
            "## 执行方案",
            f"- **执行模式**：{execution_plan['execution_mode']}",
            f"- **总步骤数**：{execution_plan['total_steps']}",
            f"- **总预估时间**：{execution_plan['total_estimated_time']}秒（{execution_plan['total_estimated_time']/60:.1f}分钟）",
            "",
            "## 执行步骤",
            "",
        ]

        for step in execution_plan["steps"]:
            lines.append(f"### 步骤{step['step_id']}: {step['step_name']}")
            lines.append(f"- **智能体**：{step['agent_name']}")
            lines.append(f"- **预估时间**：{step['estimated_time']}秒")
            if step["dependencies"]:
                lines.append(f"- **依赖步骤**：{', '.join(step['dependencies'])}")
            lines.append("")

        lines.extend([
            "## 质量保证",
            "- **质量检查点**：每个步骤完成后进行质量检查",
            "- **质量标准**：7维度评估（完整性、清晰性、准确性、充分性、一致性、规范性、支持性）",
            "- **迭代优化**：如果质量不达标（<7.5），进行优化",
            "",
            "## 潜在风险",
            "- **智能体执行失败** → **应对**：回退到备用方案或人工处理",
            "- **输出质量不达标** → **应对**：迭代优化直到满足质量要求",
            "- **用户不满意** → **应对**：允许用户调整计划或重新执行",
            "",
            "## 需要您的确认",
            "",
            "🤝 请确认：",
            "1. 执行计划是否符合您的预期？",
            "2. 是否需要调整执行步骤或智能体？",
            "3. 是否有其他要求或限制？",
            "",
            "**选项**：",
            "A. 确认，开始执行",
            "B. 调整计划（请说明调整内容）",
            "C. 取消任务",
            "",
        ])

        return "\n".join(lines)
```

### 示例2：知识库动态加载

```python
class KnowledgeBaseLoader:
    """知识库加载器"""

    def __init__(self):
        self.baochen_path = Path("/Users/xujian/Library/Mobile Documents/iCloud~md~obsidian/Documents/宝宸知识库/Wiki/")
        self.legal_world_model = LegalWorldModel()
        self.case_database = CaseDatabase()
        self.cache = {}  # 热点缓存

    async def load_for_scenario(self, scenario: Scenario) -> dict:
        """根据场景加载知识库内容"""

        cache_key = f"scenario_{scenario.value}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # 1. 从宝宸知识库加载
        baochen_content = await self._load_from_baochen(scenario)

        # 2. 从法律世界模型加载
        legal_content = await self._load_from_legal_world_model(scenario)

        # 3. 从案例库加载
        case_content = await self._load_from_case_database(scenario)

        knowledge = {
            "baochen_knowledge": baochen_content,
            "legal_knowledge": legal_content,
            "case_knowledge": case_content,
            "loaded_at": datetime.now().isoformat(),
        }

        # 缓存
        self.cache[cache_key] = knowledge

        return knowledge

    async def _load_from_baochen(self, scenario: Scenario) -> list[str]:
        """从宝宸知识库加载"""

        if scenario == Scenario.CREATIVITY_ANALYSIS:
            # 加载创造性相关知识
            files = [
                "专利实务/创造性/创造性-概述与三步法框架.md",
                "专利实务/创造性/创造性-技术启示的判断.md",
                "专利实务/创造性/创造性-辅助判断因素.md",
                "复审无效/创造性/创造性-无效决定裁判规则分析.md",
            ]
        elif scenario == Scenario.NOVELTY_ANALYSIS:
            # 加载新颖性相关知识
            files = [
                "专利实务/新颖性/新颖性-概述与判断原则.md",
                "复审无效/新颖性/",
            ]
        else:
            files = []

        # 读取文件内容
        content = []
        for file_path in files:
            full_path = self.baochen_path / file_path
            if full_path.exists():
                with open(full_path, "r", encoding="utf-8") as f:
                    content.append(f.read())

        return content

    async def _load_from_legal_world_model(self, scenario: Scenario) -> dict:
        """从法律世界模型加载"""

        # 调用法律世界模型API
        knowledge = await self.legal_world_model.query({
            "scenario": scenario.value,
            "query_type": "rules_and_principles",
        })

        return knowledge

    async def _load_from_case_database(self, scenario: Scenario) -> list[dict]:
        """从案例库加载"""

        # 查询相似案例
        cases = await self.case_database.find_similar_cases({
            "scenario": scenario.value,
            "limit": 5,
        })

        return cases
```

### 示例3：智能体组装和执行

```python
class AgentComposer:
    """智能体组装器"""

    def __init__(self, agent_registry):
        self.agent_registry = agent_registry

    async def compose_and_execute(self, execution_plan: dict, session_id: str) -> dict:
        """根据执行计划组装并执行智能体"""

        execution_mode = execution_plan["execution_mode"]
        steps = execution_plan["steps"]

        if execution_mode == "sequential":
            results = await self._execute_sequential(steps, session_id)
        elif execution_mode == "parallel":
            results = await self._execute_parallel(steps, session_id)
        elif execution_mode == "iterative":
            results = await self._execute_iterative(steps, session_id)
        elif execution_mode == "hybrid":
            results = await self._execute_hybrid(steps, session_id)
        else:
            raise ValueError(f"不支持的执行模式: {execution_mode}")

        return results

    async def _execute_sequential(self, steps: list[dict], session_id: str) -> dict:
        """串行执行"""

        results = {}
        context = {"session_id": session_id}

        for step in steps:
            # 获取智能体
            agent = self.agent_registry.get_agent(step["agent_id"])

            # 准备输入
            inputs = self._prepare_inputs(step, context, results)

            # 执行智能体
            result = await agent.execute(inputs)

            # 记录结果
            results[step["step_id"]] = result

            # 更新上下文
            context.update(result["output_data"])

            # 检查是否需要中断
            if result["status"] == "error":
                break

        return results

    async def _execute_parallel(self, steps: list[dict], session_id: str) -> dict:
        """并行执行"""

        import asyncio

        tasks = []
        for step in steps:
            # 获取智能体
            agent = self.agent_registry.get_agent(step["agent_id"])

            # 准备输入
            inputs = self._prepare_inputs(step, {}, {})

            # 创建任务
            task = agent.execute(inputs)
            tasks.append((step["step_id"], task))

        # 并行执行
        task_results = await asyncio.gather(*[task for _, task in tasks])

        # 组织结果
        results = {}
        for (step_id, _), result in zip(tasks, task_results):
            results[step_id] = result

        return results
```

---

## 📊 小诺提示词完整示例

### 专利撰写场景提示词

```markdown
你是小诺·双鱼公主，Athena团队的协调官和编排者。

## 当前任务

用户请求：撰写专利申请文件
技术领域：{根据交底书识别的技术领域}
发明名称：{根据交底书提取的发明名称}

## 场景识别

**场景**：PATENT_DRAFTING（专利撰写）
**执行模式**：混合（Hybrid）
**总步骤数**：5
**总预估时间**：300秒（5分钟）

## 执行步骤

### 步骤1：技术交底书理解
- **智能体**：分析者（AnalyzerAgent）
- **输入**：技术交底书文件
- **输出**：InventionUnderstanding（发明理解结果）
- **预估时间**：30秒
- **说明**：提取技术特征、问题-效果三元组、技术方案总结

### 步骤2：现有技术检索
- **智能体**：检索者（RetrieverAgent）
- **输入**：技术特征、关键词
- **输出**：对比文件列表、对比分析报告
- **预估时间**：60秒
- **依赖步骤**：step_1

### 步骤3：说明书撰写
- **智能体**：撰写者（WriterAgent）
- **输入**：发明理解、对比分析
- **输出**：SpecificationDraft（说明书草稿）
- **预估时间**：120秒
- **依赖步骤**：step_1, step_2

### 步骤4：权利要求撰写
- **智能体**：撰写者（WriterAgent）
- **输入**：发明理解、说明书
- **输出**：ClaimsSet（权利要求集合）
- **预估时间**：60秒
- **依赖步骤**：step_3

### 步骤5：摘要撰写
- **智能体**：撰写者（WriterAgent）
- **输入**：完整说明书、权利要求
- **输出**：专利申请文件_完整版.md
- **预估时间**：30秒
- **依赖步骤**：step_4

## 相关法律知识

### 专利撰写规范
- 发明名称：简明扼要，全面反映技术主题
- 技术领域：明确本发明所属或应用的技术领域
- 背景技术：描述现有技术状况，指出存在的问题和缺陷
- 发明内容：要解决的技术问题、技术方案、技术效果
- 具体实施方式：提供多个实施例，充分公开技术细节

### 质量要求
- 完整性：所有部分必须撰写完整
- 清晰性：技术方案清楚，逻辑清晰
- 准确性：用词准确，表述精确
- 充分性：符合A26.3要求，所属领域技术人员能够实现
- 一致性：前后一致，术语统一
- 规范性：符合专利撰写规范
- 支持性：说明书支持权利要求

## 用户输入

```
{用户的技术交底书内容摘要}
```

## 你的任务

1. **展示执行计划**（使用上述模板）
2. **等待用户确认**
3. **根据用户确认执行计划**
4. **汇总各智能体的执行结果**
5. **输出双格式报告**（JSON + Markdown）

## 输出格式

### JSON格式
```json
{
  "status": "success",
  "scenario": "patent_drafting",
  "workflow_id": "workflow_20260421_123456_abc12345",
  "total_time": 300.0,
  "steps_completed": 5,
  "steps_total": 5,
  "output": {
    "structured_data": {
      "invention_understanding": {...},
      "specification_draft": {...},
      "claims_set": {...},
      "patent_application_file": "..."
    },
    "markdown_text": "# 专利申请文件\n\n..."
  }
}
```

### Markdown格式
```markdown
# 专利申请文件

## 一、发明名称
{发明名称}

## 二、技术领域
{技术领域}

## 三、背景技术
{背景技术}

## 四、发明内容
{发明内容}

## 五、具体实施方式
{具体实施方式}

## 六、权利要求书
{权利要求书}

## 七、摘要
{摘要}
```

---

## 🔗 关联文档

- [Athena团队架构设计](../ATHENA_TEAM_ARCHITECTURE_V2.md)
- [工作流程设计](../workflows/SCENARIO_BASED_WORKFLOWS.md)
- [成熟工作流整合](../integration/EXISTING_WORKFLOKS_INTEGRATION.md)

---

## 📞 维护者

- **团队**: Athena平台团队
- **联系**: xujian519@gmail.com
- **最后更新**: 2026-04-21

---

**End of Document**
