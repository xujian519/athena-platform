# XiaonuoContextAssembler 实现方案

> **版本**: 1.0
> **创建日期**: 2026-04-21
> **状态**: 详细设计

---

## 📋 文档说明

本文档详细设计`XiaonuoContextAssembler`类的实现方案，包括：
1. 类设计
2. 上下文组装流程
3. L0编排层提示词模板
4. 宝宸知识库动态加载机制
5. 渐进式加载策略
6. 缓存机制

---

## 1. XiaonuoContextAssembler 类设计

### 1.1 类结构

```python
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
import json
from pathlib import Path

class Scenario(Enum):
    """业务场景枚举"""
    PATENT_SEARCH = "patent_search"
    TECHNICAL_ANALYSIS = "technical_analysis"
    CREATIVITY_ANALYSIS = "creativity_analysis"
    NOVELTY_ANALYSIS = "novelty_analysis"
    INFRINGEMENT_ANALYSIS = "infringement_analysis"
    PATENT_DRAFTING = "patent_drafting"
    OA_RESPONSE = "oa_response"
    INVALIDATION_REQUEST = "invalidation_request"
    INVALIDATION_RESPONSE = "invalidation_response"
    PRE_SUBMISSION_REVIEW = "pre_submission_review"
    WRITING_QUALITY_REVIEW = "writing_quality_review"

class AgentType(Enum):
    """智能体类型枚举"""
    RETRIEVER = "retriever"
    ANALYZER = "analyzer"
    CREATIVITY_ANALYZER = "creativity_analyzer"
    NOVELTY_ANALYZER = "novelty_analyzer"
    INFRINGEMENT_ANALYZER = "infringement_analyzer"
    APPLICATION_DOCUMENT_REVIEWER = "application_document_reviewer"
    WRITING_REVIEWER = "writing_reviewer"
    INVALIDATION_ANALYZER = "invalidation_analyzer"

@dataclass
class SessionContext:
    """会话上下文"""
    session_id: str
    cwd: str
    user_id: str
    conversation_history: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    available_agents: List[str]
    available_tools: List[str]
    available_knowledge_bases: List[str]

class XiaonuoContextAssembler:
    """
    小诺上下文组装器 - v5.0五层架构实现
    
    负责为不同的智能体和场景动态组装上下文（提示词）。
    采用五层架构：L0编排 + L1基础 + L2知识 + L3能力 + L4业务 + L5交互
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化上下文组装器
        
        Args:
            config: 配置字典，包含：
                - prompt_root: 提示词根目录（默认: "prompts/"）
                - knowledge_root: 知识库根目录（默认: "宝宸知识库/"）
                - cache_enabled: 是否启用缓存（默认: True）
                - progressive_loading: 是否启用渐进式加载（默认: True）
        """
        self.config = config or {}
        self.prompt_root = Path(self.config.get("prompt_root", "prompts/"))
        self.knowledge_root = Path(self.config.get("knowledge_root", "/Users/xujian/Library/Mobile Documents/iCloud~md~obsidian/Documents/宝宸知识库/Wiki/"))
        self.cache_enabled = self.config.get("cache_enabled", True)
        self.progressive_loading = self.config.get("progressive_loading", True)
        
        # 缓存机制
        self._static_cache: Dict[str, str] = {}  # 静态层缓存
        self._knowledge_cache: Dict[str, str] = {}  # 知识层缓存
        self._capability_cache: Dict[str, str] = {}  # 能力层缓存
        
        # 场景优先级配置（用于新颖性分析限制）
        self.scenario_priority = {
            Scenario.OA_RESPONSE: 1,
            Scenario.PATENT_DRAFTING: 2,
            Scenario.PATENT_SEARCH: 3,
            Scenario.CREATIVITY_ANALYSIS: 4,
            Scenario.TECHNICAL_ANALYSIS: 5,
            Scenario.NOVELTY_ANALYSIS: 6,  # ⚠️ 仅在明确指示时执行
            Scenario.INFRINGEMENT_ANALYSIS: 7,
        }
    
    async def assemble_context(
        self,
        agent_type: AgentType,
        scenario: Scenario,
        user_input: str,
        session_context: SessionContext
    ) -> str:
        """
        组装完整的上下文（提示词）
        
        Args:
            agent_type: 智能体类型
            scenario: 业务场景
            user_input: 用户输入
            session_context: 会话上下文
        
        Returns:
            完整的提示词字符串
        """
        # L0: 编排层（小诺专用，其他智能体跳过）
        orchestration_prompt = ""
        if agent_type == AgentType.ANALYZER:  # 假设小诺使用Analyzer作为协调者
            orchestration_prompt = await self._load_orchestration_layer(
                scenario, user_input, session_context
            )
        
        # L1: 基础层（智能体身份、核心原则）
        foundation_prompt = await self._load_foundation_layer(agent_type)
        
        # L2: 知识层（宝宸知识库动态注入）
        knowledge_prompt = await self._load_knowledge_layer(
            scenario, agent_type, user_input, session_context
        )
        
        # L3: 能力层（具体能力定义、whenToUse触发）
        capability_prompt = await self._load_capability_layer(
            agent_type, scenario
        )
        
        # L4: 业务层（业务逻辑、输出格式）
        business_prompt = await self._load_business_layer(
            scenario, agent_type
        )
        
        # L5: 交互层（小诺专用，其他智能体跳过）
        interaction_prompt = ""
        if agent_type == AgentType.ANALYZER:  # 假设小诺使用Analyzer作为协调者
            interaction_prompt = await self._load_interaction_layer(
                scenario, user_input, session_context
            )
        
        # 组装完整提示词
        full_prompt = self._assemble_full_prompt(
            orchestration_prompt=orchestration_prompt,
            foundation_prompt=foundation_prompt,
            knowledge_prompt=knowledge_prompt,
            capability_prompt=capability_prompt,
            business_prompt=business_prompt,
            interaction_prompt=interaction_prompt
        )
        
        return full_prompt
    
    def _assemble_full_prompt(
        self,
        orchestration_prompt: str,
        foundation_prompt: str,
        knowledge_prompt: str,
        capability_prompt: str,
        business_prompt: str,
        interaction_prompt: str
    ) -> str:
        """
        组装完整提示词
        
        组装顺序：
        1. L0: 编排层（如果存在）
        2. L1: 基础层
        3. L2: 知识层
        4. L3: 能力层
        5. L4: 业务层
        6. L5: 交互层（如果存在）
        """
        parts = []
        
        if orchestration_prompt:
            parts.append(orchestration_prompt)
            parts.append("\n---\n")
        
        parts.append(foundation_prompt)
        parts.append("\n---\n")
        
        if knowledge_prompt:
            parts.append(knowledge_prompt)
            parts.append("\n---\n")
        
        parts.append(capability_prompt)
        parts.append("\n---\n")
        
        parts.append(business_prompt)
        
        if interaction_prompt:
            parts.append("\n---\n")
            parts.append(interaction_prompt)
        
        return "\n".join(parts)
    
    async def _load_orchestration_layer(
        self,
        scenario: Scenario,
        user_input: str,
        session_context: SessionContext
    ) -> str:
        """
        加载L0编排层（小诺专用）
        
        内容：
        - 场景识别结果
        - 执行计划
        - 用户确认机制
        """
        # 场景识别
        scenario_info = await self._identify_scenario(user_input, session_context)
        
        # 执行计划
        execution_plan = await self._create_execution_plan(
            scenario, scenario_info, session_context
        )
        
        # 组装L0提示词
        orchestration_prompt = f"""# 小诺编排层（L0）

## 当前场景识别

**场景类型**: {scenario.value}
**场景描述**: {scenario_info.get('description', '')}
**场景优先级**: {self.scenario_priority.get(scenario, 99)}

**⚠️ 特殊注意**:
{scenario_info.get('special_notes', '')}

---

## 执行计划

{execution_plan}

---

**下一步**: 等待用户确认后执行
"""
        return orchestration_prompt
    
    async def _identify_scenario(
        self,
        user_input: str,
        session_context: SessionContext
    ) -> Dict[str, Any]:
        """
        识别场景
        
        Returns:
            场景信息字典
        """
        # 简化实现：使用关键词匹配
        # 实际实现应该使用更复杂的NLP模型
        
        user_input_lower = user_input.lower()
        
        # 优先级匹配（按照场景优先级）
        scenario_patterns = {
            Scenario.OA_RESPONSE: ["审查意见", "答复审查", "oa"],
            Scenario.PATENT_DRAFTING: ["撰写专利", "写专利", "申请文件"],
            Scenario.PATENT_SEARCH: ["检索专利", "查找专利", "prior art"],
            Scenario.NOVELTY_ANALYSIS: ["新颖性", "判断新颖性", "novelty"],  # ⚠️ 仅在明确指示时
            Scenario.CREATIVITY_ANALYSIS: ["创造性", "分析专利", "非显而易见", "inventive"],
            Scenario.INFRINGEMENT_ANALYSIS: ["侵权", "判断侵权", "fto", "infringement"],
            Scenario.TECHNICAL_ANALYSIS: ["技术分析", "分析技术"],
            Scenario.PRE_SUBMISSION_REVIEW: ["提交前审查", "申请文件审查"],
            Scenario.WRITING_QUALITY_REVIEW: ["撰写质量", "改进撰写"],
            Scenario.INVALIDATION_REQUEST: ["无效宣告请求", "无效风险"],
            Scenario.INVALIDATION_RESPONSE: ["无效宣告答辩", "无效答辩"],
        }
        
        # 按优先级顺序匹配
        for scenario, patterns in sorted(
            scenario_patterns.items(),
            key=lambda x: self.scenario_priority.get(x[0], 99)
        ):
            if any(pattern in user_input_lower for pattern in patterns):
                return {
                    "scenario": scenario,
                    "description": self._get_scenario_description(scenario),
                    "special_notes": self._get_scenario_special_notes(scenario)
                }
        
        # 默认场景：创造性分析
        return {
            "scenario": Scenario.CREATIVITY_ANALYSIS,
            "description": self._get_scenario_description(Scenario.CREATIVITY_ANALYSIS),
            "special_notes": self._get_scenario_special_notes(Scenario.CREATIVITY_ANALYSIS)
        }
    
    def _get_scenario_description(self, scenario: Scenario) -> str:
        """获取场景描述"""
        descriptions = {
            Scenario.PATENT_SEARCH: "专利检索：从多个数据源检索相关专利和非专利文献",
            Scenario.TECHNICAL_ANALYSIS: "技术分析：纯技术分析，提取技术特征和技术总结",
            Scenario.CREATIVITY_ANALYSIS: "创造性分析：三步法判断技术方案的创造性高度",
            Scenario.NOVELTY_ANALYSIS: "新颖性分析：单独对比原则判断新颖性（⚠️ 仅在明确指示时执行）",
            Scenario.INFRINGEMENT_ANALYSIS: "侵权分析：全面覆盖原则和等同原则判断侵权风险",
            Scenario.PATENT_DRAFTING: "专利撰写：撰写专利申请文件",
            Scenario.OA_RESPONSE: "审查意见答复：答复审查意见",
            Scenario.INVALIDATION_REQUEST: "无效宣告请求：分析无效宣告请求和证据",
            Scenario.INVALIDATION_RESPONSE: "无效宣告答辩：制定无效宣告答辩策略",
            Scenario.PRE_SUBMISSION_REVIEW: "提交前审查：审查专利申请文件的形式和实质",
            Scenario.WRITING_QUALITY_REVIEW: "撰写质量审查：审查专利撰写的语言和逻辑质量",
        }
        return descriptions.get(scenario, "未知场景")
    
    def _get_scenario_special_notes(self, scenario: Scenario) -> str:
        """获取场景特殊注意"""
        special_notes = {
            Scenario.NOVELTY_ANALYSIS: "⚠️ 新颖性分析是最难的业务任务，必须确保对比文献的完整性和准确性",
            Scenario.INVALIDATION_REQUEST: "⚠️ 无效宣告是最复杂的专利法律程序，需要最高水平的分析能力",
            Scenario.INVALIDATION_RESPONSE: "⚠️ 无效宣告答辩需要极其严谨的论证",
        }
        return special_notes.get(scenario, "")
    
    async def _create_execution_plan(
        self,
        scenario: Scenario,
        scenario_info: Dict[str, Any],
        session_context: SessionContext
    ) -> str:
        """
        创建执行计划
        
        Returns:
            执行计划文本
        """
        # 根据场景创建执行计划
        # 这里简化实现，实际应该根据场景动态生成
        
        plans = {
            Scenario.CREATIVITY_ANALYSIS: """**执行模式**: 串行执行

**执行步骤**:
1. 识别最接近现有技术（预计30秒）
2. 确定区别特征（预计1分钟）
3. 分析技术效果（预计2-3分钟）
4. 判断技术启示（预计2-3分钟）
5. 综合判断创造性（预计1分钟）

**预计总时间**: 6-8分钟

**调用的智能体**: 创造性分析智能体（CreativityAnalyzerAgent）

**前置要求**: 必须先完成检索（检索者提供对比文献）""",
            
            Scenario.NOVELTY_ANALYSIS: """**执行模式**: 串行执行

**⚠️ 重要提示**: 新颖性分析是最难的业务任务，需要仔细对比技术特征。

**执行步骤**:
1. 选择对比文件（预计1分钟）
2. 逐一对比技术特征（预计5-10分钟）
3. **[可选] 判断上位下位概念**
4. **[可选] 判断惯用手段置换**
5. 综合判断新颖性（预计2分钟）

**预计总时间**: 8-13分钟

**调用的智能体**: 新颖性分析智能体（NoveltyAnalyzerAgent）

**前置要求**: 必须先完成全面检索（检索者提供完整对比文献）

**⚠️ 对比文献必须完整**，如有缺失需要补充检索""",
        }
        
        return plans.get(scenario, f"执行计划：{scenario.value}")
    
    async def _load_foundation_layer(self, agent_type: AgentType) -> str:
        """
        加载L1基础层
        
        内容：
        - 智能体身份定义
        - 核心原则
        - 约束重复
        """
        # 从静态缓存加载
        cache_key = f"foundation_{agent_type.value}"
        if self.cache_enabled and cache_key in self._static_cache:
            return self._static_cache[cache_key]
        
        # 从文件加载
        foundation_file = self.prompt_root / f"foundation_{agent_type.value}.md"
        
        if foundation_file.exists():
            foundation_prompt = foundation_file.read_text(encoding="utf-8")
        else:
            # 默认基础层提示词
            foundation_prompt = self._get_default_foundation_prompt(agent_type)
        
        # 缓存
        if self.cache_enabled:
            self._static_cache[cache_key] = foundation_prompt
        
        return foundation_prompt
    
    def _get_default_foundation_prompt(self, agent_type: AgentType) -> str:
        """获取默认基础层提示词"""
        # 这里返回简化的默认提示词
        # 实际实现应该从PHASE1_AGENT_PROMPTS.md等文件中提取
        return f"""# {agent_type.value} 基础层（L1）

## 身份定义

你是{agent_type.value}智能体。

## 核心原则

1. 专业性原则
2. 准确性原则
3. 完整性原则

**约束重复**: 以上原则必须严格遵守。
"""
    
    async def _load_knowledge_layer(
        self,
        scenario: Scenario,
        agent_type: AgentType,
        user_input: str,
        session_context: SessionContext
    ) -> str:
        """
        加载L2知识层
        
        内容：
        - 宝宸知识库动态注入
        - 根据场景和智能体类型选择知识内容
        """
        # 从知识缓存加载
        cache_key = f"knowledge_{scenario.value}_{agent_type.value}"
        if self.cache_enabled and cache_key in self._knowledge_cache:
            return self._knowledge_cache[cache_key]
        
        # 根据场景和智能体类型选择知识文件
        knowledge_files = self._map_knowledge_files(scenario, agent_type)
        
        # 加载知识内容
        knowledge_content = await self._load_knowledge_files(knowledge_files)
        
        # 组装知识层提示词
        knowledge_prompt = f"""# 知识层（L2）

## 当前场景：{scenario.value}

## 知识库内容

{knowledge_content}

---
"""
        # 缓存
        if self.cache_enabled:
            self._knowledge_cache[cache_key] = knowledge_prompt
        
        return knowledge_prompt
    
    def _map_knowledge_files(
        self,
        scenario: Scenario,
        agent_type: AgentType
    ) -> List[Path]:
        """
        映射知识文件
        
        根据场景和智能体类型，返回需要加载的知识文件列表
        """
        # 知识文件映射表
        knowledge_mapping = {
            (Scenario.CREATIVITY_ANALYSIS, AgentType.CREATIVITY_ANALYZER): [
                self.knowledge_root / "专利实务/创造性/三步法审查指南.md",
                self.knowledge_root / "专利实务/创造性/创造性判断案例.md",
                self.knowledge_root / "专利实务/创造性/公知常识库.md",
            ],
            (Scenario.NOVELTY_ANALYSIS, AgentType.NOVELTY_ANALYZER): [
                self.knowledge_root / "专利实务/新颖性/单独对比原则指南.md",
                self.knowledge_root / "专利实务/新颖性/上位下位概念判断.md",
            ],
            (Scenario.INFRINGEMENT_ANALYSIS, AgentType.INFRINGEMENT_ANALYZER): [
                self.knowledge_root / "专利实务/侵权/全面覆盖原则指南.md",
                self.knowledge_root / "专利实务/侵权/等同原则测试方法.md",
            ],
        }
        
        return knowledge_mapping.get(
            (scenario, agent_type),
            []
        )
    
    async def _load_knowledge_files(self, knowledge_files: List[Path]) -> str:
        """
        加载知识文件内容
        
        Args:
            knowledge_files: 知识文件路径列表
        
        Returns:
            知识内容字符串
        """
        knowledge_parts = []
        
        for knowledge_file in knowledge_files:
            if knowledge_file.exists():
                content = knowledge_file.read_text(encoding="utf-8")
                knowledge_parts.append(f"### {knowledge_file.name}\n\n{content}\n")
        
        if not knowledge_parts:
            return "暂无相关知识库内容"
        
        return "\n".join(knowledge_parts)
    
    async def _load_capability_layer(
        self,
        agent_type: AgentType,
        scenario: Scenario
    ) -> str:
        """
        加载L3能力层
        
        内容：
        - 具体能力定义
        - whenToUse触发条件
        - 输出格式
        """
        # 从能力缓存加载
        cache_key = f"capability_{agent_type.value}_{scenario.value}"
        if self.cache_enabled and cache_key in self._capability_cache:
            return self._capability_cache[cache_key]
        
        # 从文件加载
        capability_file = self.prompt_root / f"capability_{agent_type.value}_{scenario.value}.md"
        
        if capability_file.exists():
            capability_prompt = capability_file.read_text(encoding="utf-8")
        else:
            # 默认能力层提示词
            capability_prompt = self._get_default_capability_prompt(agent_type, scenario)
        
        # 缓存
        if self.cache_enabled:
            self._capability_cache[cache_key] = capability_prompt
        
        return capability_prompt
    
    def _get_default_capability_prompt(self, agent_type: AgentType, scenario: Scenario) -> str:
        """获取默认能力层提示词"""
        # 这里返回简化的默认提示词
        # 实际实现应该从PHASE1_AGENT_PROMPTS.md等文件中提取
        return f"""# 能力层（L3）

## 核心能力

根据当前场景（{scenario.value}），{agent_type.value}将使用以下能力：

1. 理解用户输入
2. 执行核心任务
3. 生成输出

**输出格式**: 双格式输出（JSON + Markdown）
"""
    
    async def _load_business_layer(
        self,
        scenario: Scenario,
        agent_type: AgentType
    ) -> str:
        """
        加载L4业务层
        
        内容：
        - 业务流程
        - 输出质量标准
        - 约束重复
        """
        # 从文件加载（业务层通常不缓存，因为可能频繁修改）
        business_file = self.prompt_root / f"business_{agent_type.value}_{scenario.value}.md"
        
        if business_file.exists():
            business_prompt = business_file.read_text(encoding="utf-8")
        else:
            # 默认业务层提示词
            business_prompt = self._get_default_business_prompt(agent_type, scenario)
        
        return business_prompt
    
    def _get_default_business_prompt(self, agent_type: AgentType, scenario: Scenario) -> str:
        """获取默认业务层提示词"""
        # 这里返回简化的默认提示词
        # 实际实现应该从PHASE1_AGENT_PROMPTS.md等文件中提取
        return f"""# 业务层（L4）

## 业务流程

当前场景：{scenario.value}

**执行流程**:
1. 理解用户输入
2. 执行核心任务
3. 生成输出

## 输出质量标准

1. 准确性
2. 完整性
3. 专业性

**约束重复**: 必须严格遵守以上原则。
"""
    
    async def _load_interaction_layer(
        self,
        scenario: Scenario,
        user_input: str,
        session_context: SessionContext
    ) -> str:
        """
        加载L5交互层（小诺专用）
        
        内容：
        - 计划展示
        - 用户确认选项
        - 控制按钮
        """
        interaction_prompt = f"""# 交互层（L5）

## 用户确认

**自动确认场景**:
- 用户输入明确
- 场景简单

**手动确认场景**:
- 场景复杂
- 需要调整计划

**控制按钮**:
- 暂停
- 继续
- 调整计划
- 停止

**下一步**: 请确认执行计划

[ ] 继续执行
[ ] 调整计划
[ ] 取消任务
"""
        return interaction_prompt
    
    def clear_cache(self, cache_type: Optional[str] = None):
        """
        清除缓存
        
        Args:
            cache_type: 缓存类型（"static", "knowledge", "capability"），None表示清除所有
        """
        if cache_type is None or cache_type == "static":
            self._static_cache.clear()
        
        if cache_type is None or cache_type == "knowledge":
            self._knowledge_cache.clear()
        
        if cache_type is None or cache_type == "capability":
            self._capability_cache.clear()
```

---

## 2. L0编排层提示词模板

### 2.1 场景识别提示词

```markdown
# 小诺场景识别（L0-1）

## 任务：识别用户意图的场景

**用户输入**: {user_input}

**会话历史**:
{conversation_history}

---

## 场景列表

请从以下场景中选择最匹配的一个：

1. **PATENT_SEARCH** - 专利检索
   - 触发词："检索专利"、"查找专利"、"prior art"
   - 优先级：3

2. **TECHNICAL_ANALYSIS** - 技术分析
   - 触发词："技术分析"、"分析技术"
   - 优先级：5

3. **CREATIVITY_ANALYSIS** - 创造性分析（默认场景）
   - 触发词："创造性"、"分析专利"、"非显而易见"
   - 优先级：4

4. **NOVELTY_ANALYSIS** - 新颖性分析
   - 触发词："新颖性"、"判断新颖性"
   - 优先级：6（⚠️ 仅在明确指示时执行）

5. **INFRINGEMENT_ANALYSIS** - 侵权分析
   - 触发词："侵权"、"判断侵权"、"FTO"
   - 优先级：7

6. **PATENT_DRAFTING** - 专利撰写
   - 触发词："撰写专利"、"写专利"、"申请文件"
   - 优先级：2

7. **OA_RESPONSE** - 审查意见答复
   - 触发词："审查意见"、"答复审查"、"OA"
   - 优先级：1

8. **INVALIDATION_REQUEST** - 无效宣告请求
   - 触发词："无效宣告请求"、"无效风险"
   - 优先级：8

9. **INVALIDATION_RESPONSE** - 无效宣告答辩
   - 触发词："无效宣告答辩"、"无效答辩"
   - 优先级：8

---

## 输出格式

请输出JSON格式：

```json
{{
  "scenario": "场景名称",
  "confidence": 0.95,
  "reason": "选择理由",
  "special_notes": "特殊注意（如有）"
}}
```

---

**约束重复**: 必须按照优先级选择场景，如果用户明确指示新颖性分析，则选择NOVELTY_ANALYSIS。
```

---

### 2.2 计划制定提示词

```markdown
# 小诺计划制定（L0-2）

## 任务：制定执行计划

**场景**: {scenario}

**用户输入**: {user_input}

**可用的智能体**: {available_agents}

---

## 计划制定原则

1. **0号原则**: 先规划再执行，必须向用户展示计划并获得确认
2. **智能选择**: 根据场景选择合适的智能体
3. **效率优先**: 尽量并行执行独立任务
4. **质量优先**: 专利法律业务以质量为最高原则

---

## 执行模式

请选择以下执行模式之一：

1. **串行（Sequential）**: 步骤按顺序依次执行
   - 适用：简单任务、强依赖关系

2. **并行（Parallel）**: 多个步骤同时执行
   - 适用：多数据源检索、多专利同时分析

3. **迭代（Iterative）**: 某个步骤循环执行直到满足条件
   - 适用：迭代式搜索、多轮分析

4. **混合（Hybrid）**: 组合多种执行模式
   - 适用：复杂任务

---

## 计划模板

```json
{{
  "execution_mode": "串行",
  "estimated_time": "6-8分钟",
  "steps": [
    {{
      "step_number": 1,
      "description": "步骤描述",
      "agent": "智能体名称",
      "estimated_time": "预计时间",
      "dependencies": []
    }}
  ],
  "output": "输出描述",
  "requires_confirmation": true
}}
```

---

## 输出要求

1. 计划必须清晰、具体
2. 必须包含预计时间
3. 必须说明调用的智能体
4. 必须说明依赖关系
5. 如果需要用户确认，必须标记

---

**约束重复**: 计划必须符合0号原则，必须向用户展示并获得确认。
```

---

### 2.3 用户确认提示词

```markdown
# 小诺用户确认（L0-3）

## 任务：获取用户确认

**执行计划**:

{execution_plan}

---

## 确认方式

请选择以下确认方式之一：

### 1. 自动确认

**适用场景**:
- 用户输入明确
- 计划简单
- 无风险操作

**确认方式**: 直接执行，无需等待用户确认

---

### 2. 手动确认

**适用场景**:
- 计划复杂
- 涉及重要决策
- 需要用户选择

**确认方式**: 展示计划，等待用户确认

**确认选项**:
- [ ] 继续执行
- [ ] 调整计划
- [ ] 取消任务

---

### 3. 交互式选择

**适用场景**:
- 多个执行选项
- 需要用户偏好

**确认方式**: 提供多个选项，用户选择

**选项示例**:
- A. 快速分析（6-8分钟）
- B. 深度分析（15-20分钟）
- C. 自定义分析

---

## 输出格式

请输出JSON格式：

```json
{{
  "confirmation_type": "自动 / 手动 / 交互式",
  "options": ["选项1", "选项2"],
  "default_option": "选项1",
  "wait_for_user": false
}}
```

---

**约束重复**: 必须根据任务复杂度选择合适的确认方式。
```

---

## 3. 宝宸知识库动态加载机制

### 3.1 知识库映射表

```python
KNOWLEDGE_BASE_MAPPING = {
    # 创造性分析
    "creativity_analysis": {
        "path": "宝宸知识库/专利实务/创造性/",
        "files": [
            "三步法审查指南.md",
            "创造性判断案例.md",
            "公知常识库.md",
            "技术启示判断标准.md",
        ],
        "priority": [1, 2, 3, 4],  # 加载优先级
    },
    
    # 新颖性分析
    "novelty_analysis": {
        "path": "宝宸知识库/专利实务/新颖性/",
        "files": [
            "单独对比原则指南.md",
            "上位下位概念判断.md",
            "惯用手段直接置换判断.md",
        ],
        "priority": [1, 2, 3],
    },
    
    # 侵权分析
    "infringement_analysis": {
        "path": "宝宸知识库/专利实务/侵权/",
        "files": [
            "全面覆盖原则指南.md",
            "等同原则测试方法.md",
            "抗辩事由识别.md",
        ],
        "priority": [1, 2, 3],
    },
    
    # 审查意见答复
    "oa_response": {
        "path": "宝宸知识库/专利实务/审查意见/",
        "files": [
            "审查意见答复指南.md",
            "审查员观点分析方法.md",
            "常见反驳论点.md",
        ],
        "priority": [1, 2, 3],
    },
    
    # 无效宣告
    "invalidation": {
        "path": "宝宸知识库/复审无效/",
        "files": [
            "创造性/无效决定裁判规则分析.md",
            "新颖性/单独对比原则应用.md",
            "证据/证据组合分析.md",
        ],
        "priority": [1, 2, 3],
    },
}
```

---

### 3.2 渐进式加载策略

```python
class ProgressiveKnowledgeLoader:
    """
    渐进式知识加载器
    
    策略：
    1. 首次加载：只加载核心知识（~5K tokens）
    2. 按需加载：根据任务需要加载更多知识
    3. 智能压缩：使用摘要和关键点提取
    """
    
    async def load_progressively(
        self,
        scenario: Scenario,
        agent_type: AgentType,
        task_complexity: str = "standard"
    ) -> str:
        """
        渐进式加载知识
        
        Args:
            scenario: 业务场景
            agent_type: 智能体类型
            task_complexity: 任务复杂度（"simple", "standard", "complex"）
        
        Returns:
            知识内容字符串
        """
        # 阶段1：加载核心知识（~5K tokens）
        core_knowledge = await self._load_core_knowledge(
            scenario, agent_type
        )
        
        if task_complexity == "simple":
            return core_knowledge
        
        # 阶段2：加载扩展知识（~10K tokens）
        extended_knowledge = await self._load_extended_knowledge(
            scenario, agent_type
        )
        
        if task_complexity == "standard":
            return f"{core_knowledge}\n\n{extended_knowledge}"
        
        # 阶段3：加载完整知识（~20K tokens）
        full_knowledge = await self._load_full_knowledge(
            scenario, agent_type
        )
        
        return f"{core_knowledge}\n\n{extended_knowledge}\n\n{full_knowledge}"
    
    async def _load_core_knowledge(
        self,
        scenario: Scenario,
        agent_type: AgentType
    ) -> str:
        """加载核心知识"""
        # 只加载最高优先级的知识文件
        mapping = KNOWLEDGE_BASE_MAPPING.get(
            f"{scenario.value}_{agent_type.value}",
            {}
        )
        
        core_files = [
            f for f, p in zip(
                mapping.get("files", []),
                mapping.get("priority", [])
            )
            if p == 1
        ]
        
        return await self._load_knowledge_files(core_files)
    
    async def _load_extended_knowledge(
        self,
        scenario: Scenario,
        agent_type: AgentType
    ) -> str:
        """加载扩展知识"""
        # 加载优先级2-3的知识文件
        mapping = KNOWLEDGE_BASE_MAPPING.get(
            f"{scenario.value}_{agent_type.value}",
            {}
        )
        
        extended_files = [
            f for f, p in zip(
                mapping.get("files", []),
                mapping.get("priority", [])
            )
            if p in [2, 3]
        ]
        
        return await self._load_knowledge_files(extended_files)
    
    async def _load_full_knowledge(
        self,
        scenario: Scenario,
        agent_type: AgentType
    ) -> str:
        """加载完整知识"""
        # 加载所有知识文件
        mapping = KNOWLEDGE_BASE_MAPPING.get(
            f"{scenario.value}_{agent_type.value}",
            {}
        )
        
        all_files = mapping.get("files", [])
        
        return await self._load_knowledge_files(all_files)
```

---

## 4. 缓存机制

### 4.1 缓存策略

```python
class PromptCache:
    """
    提示词缓存
    
    策略：
    1. 静态层（L1、L3）：永久缓存，除非手动清除
    2. 知识层（L2）：LRU缓存，容量限制
    3. 业务层（L4）：不缓存，频繁修改
    """
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.static_cache: Dict[str, str] = {}
        self.knowledge_cache: Dict[str, str] = {}
        self.capability_cache: Dict[str, str] = {}
        self.knowledge_lru: List[str] = []
    
    def get(self, cache_type: str, key: str) -> Optional[str]:
        """获取缓存"""
        if cache_type == "static":
            return self.static_cache.get(key)
        
        elif cache_type == "knowledge":
            if key in self.knowledge_cache:
                # 更新LRU
                self.knowledge_lru.remove(key)
                self.knowledge_lru.append(key)
                return self.knowledge_cache[key]
        
        elif cache_type == "capability":
            return self.capability_cache.get(key)
        
        return None
    
    def set(self, cache_type: str, key: str, value: str):
        """设置缓存"""
        if cache_type == "static":
            self.static_cache[key] = value
        
        elif cache_type == "knowledge":
            # LRU淘汰
            if len(self.knowledge_cache) >= self.max_size:
                oldest = self.knowledge_lru.pop(0)
                del self.knowledge_cache[oldest]
            
            self.knowledge_cache[key] = value
            self.knowledge_lru.append(key)
        
        elif cache_type == "capability":
            self.capability_cache[key] = value
    
    def clear(self, cache_type: Optional[str] = None):
        """清除缓存"""
        if cache_type is None or cache_type == "static":
            self.static_cache.clear()
        
        if cache_type is None or cache_type == "knowledge":
            self.knowledge_cache.clear()
            self.knowledge_lru.clear()
        
        if cache_type is None or cache_type == "capability":
            self.capability_cache.clear()
```

---

## 5. 使用示例

### 5.1 基本使用

```python
# 初始化上下文组装器
assembler = XiaonuoContextAssembler(config={
    "prompt_root": "prompts/",
    "knowledge_root": "/Users/xujian/Library/Mobile Documents/iCloud~md~obsidian/Documents/宝宸知识库/Wiki/",
    "cache_enabled": True,
    "progressive_loading": True,
})

# 创建会话上下文
session_context = SessionContext(
    session_id="SESSION_001",
    cwd="/Users/xujian/Athena工作平台",
    user_id="user_001",
    conversation_history=[],
    user_preferences={},
    available_agents=["retriever", "analyzer", "creativity_analyzer"],
    available_tools=["patent_search", "technical_analysis"],
    available_knowledge_bases=["宝宸知识库"],
)

# 组装上下文
prompt = await assembler.assemble_context(
    agent_type=AgentType.CREATIVITY_ANALYZER,
    scenario=Scenario.CREATIVITY_ANALYSIS,
    user_input="帮我分析专利CN123456789A的创造性",
    session_context=session_context,
)

print(prompt)
```

---

### 5.2 清除缓存

```python
# 清除所有缓存
assembler.clear_cache()

# 只清除知识层缓存
assembler.clear_cache(cache_type="knowledge")
```

---

## 6. 下一步工作

1. ✅ XiaonuoContextAssembler类设计
2. ✅ L0编排层提示词模板
3. ✅ 宝宸知识库动态加载机制
4. ✅ 渐进式加载策略
5. ✅ 缓存机制
6. ⏳ 实现完整的提示词文件（L1-L5）
7. ⏳ 集成到小诺智能体
8. ⏳ 编写单元测试和集成测试

---

**End of Document**
