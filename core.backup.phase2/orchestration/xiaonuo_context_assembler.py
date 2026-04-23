"""
小诺上下文组装器

实现五层渐进式加载：
- L0: 编排层 (小诺专用)
- L1: 基础层 (智能体身份、基础原则)
- L2: 知识层 (宝宸知识库、法律知识)
- L3: 能力层 (whenToUse触发的能力模块)
- L4: 业务层 (场景相关业务逻辑)
- L5: 交互层 (用户交互规范)

Author: Athena Platform
Date: 2026-04-21
Version: 1.0
"""

from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
from collections import OrderedDict
import time


class AgentType(Enum):
    """智能体类型"""
    # Phase 1 智能体
    RETRIEVER = "retriever"  # 检索者
    ANALYZER = "analyzer"  # 分析者（技术分析）
    CREATIVITY_ANALYZER = "creativity_analyzer"  # 创造性分析智能体
    NOVELTY_ANALYZER = "novelty_analyzer"  # 新颖性分析智能体
    INFRINGEMENT_ANALYZER = "infringement_analyzer"  # 侵权分析智能体

    # Phase 2 智能体
    APPLICATION_DOCUMENT_REVIEWER = "application_document_reviewer"  # 申请文件审查智能体
    WRITING_REVIEWER = "writing_reviewer"  # 撰写审查智能体

    # Phase 3 智能体
    INVALIDATION_ANALYZER = "invalidation_analyzer"  # 无效宣告分析智能体

    # 特殊智能体
    XIAONUO = "xiaonuo"  # 小诺（编排者）
    XIAONA = "xiaona"  # 小娜（法律专家）


class Scenario(Enum):
    """业务场景"""
    PATENT_SEARCH = "patent_search"  # 专利检索
    TECHNICAL_ANALYSIS = "technical_analysis"  # 技术分析
    CREATIVITY_ANALYSIS = "creativity_analysis"  # 创造性分析
    NOVELTY_ANALYSIS = "novelty_analysis"  # 新颖性分析
    INFRINGEMENT_ANALYSIS = "infringement_analysis"  # 侵权分析
    INVALIDATION_ANALYSIS = "invalidation_analysis"  # 无效宣告分析
    APPLICATION_REVIEW = "application_review"  # 申请文件审查
    WRITING_REVIEW = "writing_review"  # 撰写审查


@dataclass
class SessionContext:
    """会话上下文"""
    session_id: str
    user_id: Optional[str] = None
    cwd: Optional[str] = None
    start_time: Optional[str] = None
    total_tokens_used: int = 0
    request_count: int = 0

    # 可选的内存系统引用
    memory_system: Optional[Any] = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "cwd": self.cwd,
            "start_time": self.start_time,
            "total_tokens_used": self.total_tokens_used,
            "request_count": self.request_count
        }


@dataclass
class AssemblyResult:
    """组装结果"""
    full_prompt: str  # 完整提示词
    token_count: int  # Token数量（估算）
    layers_loaded: list[str]  # 已加载的层
    loading_time_ms: float  # 加载时间（毫秒）
    cache_hits: int  # 缓存命中次数
    compression_ratio: float  # 压缩比率（相对于完整加载）

    # 分层Token统计
    layer_tokens: dict[str, int] = field(default_factory=dict)


class PromptCache:
    """提示词缓存（LRU）"""

    def __init__(self, max_size: int = 100):
        self.cache: OrderedDict = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[str]:
        """获取缓存"""
        if key in self.cache:
            self.hits += 1
            # LRU: 移动到末尾
            self.cache.move_to_end(key)
            return self.cache[key]
        self.misses += 1
        return None

    def set(self, key: str, value: str) -> None:
        """设置缓存"""
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        # 超过容量，删除最旧的
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        total_requests = self.hits + self.total_requests if (self.hits + self.misses) > 0 else 1
        hit_rate = self.hits / total_requests
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate
        }


class XiaonuoContextAssembler:
    """
    小诺上下文组装器

    负责为不同智能体和场景组装合适的上下文提示词。

    核心特性：
    1. 五层渐进式加载
    2. 静态/动态分离
    3. LRU缓存
    4. Token优化
    5. whenToUse触发
    """

    def __init__(
        self,
        prompt_base_path: str = "prompts",
        knowledge_base_path: Optional[str] = None,
        enable_cache: bool = True,
        cache_size: int = 100
    ):
        """
        初始化上下文组装器

        Args:
            prompt_base_path: 提示词基础路径
            knowledge_base_path: 知识库路径（宝宸知识库）
            enable_cache: 是否启用缓存
            cache_size: 缓存大小
        """
        self.prompt_base_path = Path(prompt_base_path)
        self.knowledge_base_path = Path(knowledge_base_path) if knowledge_base_path else None
        self.enable_cache = enable_cache

        # 初始化缓存
        self.static_cache = PromptCache(max_size=cache_size) if enable_cache else None
        self.knowledge_cache = PromptCache(max_size=50) if enable_cache else None

        # 统计信息
        self.total_assemblies = 0
        self.total_cache_hits = 0

    async def assemble_context(
        self,
        agent_type: AgentType,
        scenario: Scenario,
        user_input: str,
        session_context: SessionContext,  # noqa: ARG001 (reserved for future use)
        progressive: bool = True
    ) -> AssemblyResult:
        """
        组装上下文

        Args:
            agent_type: 智能体类型
            scenario: 业务场景
            user_input: 用户输入
            session_context: 会话上下文
            progressive: 是否渐进式加载（推荐True）

        Returns:
            AssemblyResult: 组装结果
        """
        import time
        start_time = time.time()

        layers = []
        layer_tokens = {}
        cache_hits = 0

        # L0: 编排层（仅小诺）
        if agent_type == AgentType.XIAONUO:
            orchestration_prompt = await self._load_orchestration_layer(scenario)
            layers.append(("L0_编排层", orchestration_prompt))
            layer_tokens["L0"] = self._estimate_tokens(orchestration_prompt)

        # L1: 基础层（所有智能体）
        foundation_prompt = await self._load_foundation_layer(agent_type)
        layers.append(("L1_基础层", foundation_prompt))
        layer_tokens["L1"] = self._estimate_tokens(foundation_prompt)

        # 渐进式加载：如果progressive=False，直接加载全部
        if not progressive:
            # L2: 知识层
            knowledge_prompt = await self._load_knowledge_layer(scenario, agent_type)
            layers.append(("L2_知识层", knowledge_prompt))
            layer_tokens["L2"] = self._estimate_tokens(knowledge_prompt)

            # L3: 能力层
            capability_prompt = await self._load_capability_layer(agent_type, scenario, user_input)
            layers.append(("L3_能力层", capability_prompt))
            layer_tokens["L3"] = self._estimate_tokens(capability_prompt)

            # L4: 业务层
            business_prompt = await self._load_business_layer(scenario, agent_type)
            layers.append(("L4_业务层", business_prompt))
            layer_tokens["L4"] = self._estimate_tokens(business_prompt)

        # L5: 交互层（所有智能体）
        interaction_prompt = await self._load_interaction_layer()
        layers.append(("L5_交互层", interaction_prompt))
        layer_tokens["L5"] = self._estimate_tokens(interaction_prompt)

        # 组装完整提示词
        full_prompt = self._assemble_layers(layers)

        # 计算统计信息
        loading_time = (time.time() - start_time) * 1000  # 转换为毫秒
        total_tokens = sum(layer_tokens.values())

        # 如果启用缓存，统计命中次数
        if self.static_cache:
            cache_hits = self.static_cache.hits

        self.total_assemblies += 1
        if self.static_cache:
            self.total_cache_hits = self.static_cache.hits

        # 计算压缩比率（相对于完整加载）
        compression_ratio = 1.0
        if progressive:
            # 渐进式加载的核心负载约5K tokens
            # 完整加载约20K tokens
            compression_ratio = total_tokens / 20000

        return AssemblyResult(
            full_prompt=full_prompt,
            token_count=total_tokens,
            layers_loaded=[name for name, _ in layers],
            loading_time_ms=loading_time,
            cache_hits=cache_hits,
            compression_ratio=compression_ratio,
            layer_tokens=layer_tokens
        )

    async def load_progressive_layer(
        self,
        agent_type: AgentType,
        scenario: Scenario,
        user_input: str,
        layer_type: str
    ) -> tuple[str, int]:
        """
        渐进式加载单个层

        Args:
            agent_type: 智能体类型
            scenario: 业务场景
            user_input: 用户输入
            layer_type: 层类型 (L2, L3, L4)

        Returns:
            (提示词内容, Token数量)
        """
        if layer_type == "L2":
            content = await self._load_knowledge_layer(scenario, agent_type)
        elif layer_type == "L3":
            content = await self._load_capability_layer(agent_type, scenario, user_input)
        elif layer_type == "L4":
            content = await self._load_business_layer(scenario, agent_type)
        else:
            raise ValueError(f"Unknown layer type: {layer_type}")

        tokens = self._estimate_tokens(content)
        return content, tokens

    async def _load_orchestration_layer(self, scenario: Scenario) -> str:
        """加载L0编排层（小诺专用）"""
        cache_key = f"L0_xiaonuo_{scenario.value}"

        # 检查缓存
        if self.static_cache:
            cached = self.static_cache.get(cache_key)
            if cached:
                return cached

        # 加载提示词模板
        prompt_content = """
# 小诺·双鱼公主 - 智能体编排者

> **身份**: Athena平台智能体编排调度官
> **职责**: 任务分解、智能体调度、结果聚合
> **原则**: 先规划再执行、质量优先、人机协同

## 核心原则

### 小诺0号原则（最重要）
任何复杂任务在执行前必须：
1. 深度理解用户意图
2. 制定详细的执行计划
3. 向用户展示计划
4. **获得用户确认后才能执行**

### 质量优先原则
- 专利和法律业务以质量为最高原则
- 性能和成本服从于质量
- 不确定时宁可慢一点，也要保证准确

### 人机协同原则
- 用户是决策者，智能体是执行者和建议者
- 关键决策点必须由用户确认
- 智能体主动汇报进度和风险

## 当前场景
{scenario_description}

## 工作流程
1. **理解意图**: 分析用户需求和场景类型
2. **制定计划**: 分解任务、选择智能体、规划执行顺序
3. **展示计划**: 清晰展示执行计划，说明每一步的目的
4. **等待确认**: 等待用户确认计划
5. **执行调度**: 调度相应智能体执行任务
6. **结果聚合**: 整合各智能体输出，生成最终结果
7. **汇报完成**: 向用户汇报完成情况和关键发现

## 智能体调度规则
- **检索任务** → RetrieverAgent（检索者）
- **技术分析** → AnalyzerAgent（分析者）
- **创造性分析** → CreativityAnalyzerAgent
- **新颖性分析** → NoveltyAnalyzerAgent
- **侵权分析** → InfringementAnalyzerAgent
- **无效宣告** → InvalidationAnalyzerAgent
- **申请文件审查** → ApplicationDocumentReviewerAgent
- **撰写审查** → WritingReviewerAgent

## 空闲时间验证
- 任务完成后，验证是否有遗漏
- 主动提示用户可能的后续操作
- 记录用户偏好，优化后续调度

---
**记住**: 你是编排者，不是执行者。你的价值在于协调和调度，而非亲自分析。
""".format(scenario_description=self._get_scenario_description(scenario))

        # 缓存
        if self.static_cache:
            self.static_cache.set(cache_key, prompt_content)

        return prompt_content

    async def _load_foundation_layer(self, agent_type: AgentType) -> str:
        """加载L1基础层（智能体身份和基础原则）"""
        cache_key = f"L1_{agent_type.value}"

        # 检查缓存
        if self.static_cache:
            cached = self.static_cache.get(cache_key)
            if cached:
                return cached

        # 加载智能体特定提示词
        prompt_content = await self._load_agent_base_prompt(agent_type)

        # 缓存
        if self.static_cache:
            self.static_cache.set(cache_key, prompt_content)

        return prompt_content

    async def _load_knowledge_layer(self, scenario: Scenario, agent_type: AgentType) -> str:
        """加载L2知识层（宝宸知识库、法律知识）"""
        cache_key = f"L2_{scenario.value}_{agent_type.value}"

        # 检查缓存
        if self.knowledge_cache:
            cached = self.knowledge_cache.get(cache_key)
            if cached:
                return cached

        # 根据场景和智能体类型加载知识
        knowledge_content = await self._load_scenario_knowledge(scenario, agent_type)

        # 缓存（知识库缓存独立管理）
        if self.knowledge_cache:
            self.knowledge_cache.set(cache_key, knowledge_content)

        return knowledge_content

    async def _load_capability_layer(
        self,
        agent_type: AgentType,
        scenario: Scenario,
        user_input: str
    ) -> str:
        """加载L3能力层（whenToUse触发的能力模块）"""
        # 根据用户输入触发whenToUse
        triggered_capabilities = await self._trigger_when_to_use(agent_type, scenario, user_input)

        if not triggered_capabilities:
            return ""

        # 组装触发的能力模块
        capability_sections = []
        for cap_name, cap_content in triggered_capabilities:
            capability_sections.append(f"## {cap_name}\n{cap_content}")

        return "\n\n".join(capability_sections)

    async def _load_business_layer(self, scenario: Scenario, agent_type: AgentType) -> str:
        """加载L4业务层（场景相关业务逻辑）"""
        cache_key = f"L4_{scenario.value}_{agent_type.value}"

        # 检查缓存
        if self.static_cache:
            cached = self.static_cache.get(cache_key)
            if cached:
                return cached

        # 加载场景特定的业务流程
        business_content = await self._load_scenario_business_logic(scenario, agent_type)

        # 缓存
        if self.static_cache:
            self.static_cache.set(cache_key, business_content)

        return business_content

    async def _load_interaction_layer(self) -> str:
        """加载L5交互层（用户交互规范）"""
        return """
## 用户交互规范

### 输出格式
- **JSON格式**: 机器可读的结构化输出
- **Markdown格式**: 人类可读的友好展示
- 必须同时提供两种格式

### 约束重复（重要）
1. 质量优先原则：不准确不如不输出
2. 法律专业原则：严格依据法律条文和案例
3. 诚实透明原则：不确定时明确说明

### 约束重复（再次强调）
1. **质量优先**: 专利和法律业务质量至上
2. **法律专业**: 严格依法分析，不主观臆断
3. **诚实透明**: 不确定时明确告知用户

---
**约束重复结束**: 以上原则必须严格遵守
"""

    def _assemble_layers(self, layers: list[tuple[str, str]]) -> str:
        """组装各层为完整提示词"""
        sections = []
        for layer_name, content in layers:
            if content.strip():
                sections.append(f"<!-- {layer_name} -->\n{content}")

        return "\n\n".join(sections)

    def _estimate_tokens(self, text: str) -> int:
        """估算Token数量（粗略：中文字符*1.5 + 英文单词*1）"""
        # 简单估算：中文约1.5 tokens/字符，英文约1 token/单词
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        english_words = len(text.split()) - chinese_chars  # 粗略估算
        return int(chinese_chars * 1.5 + english_words * 1)

    def _get_scenario_description(self, scenario: Scenario) -> str:
        """获取场景描述"""
        descriptions = {
            Scenario.PATENT_SEARCH: "专利检索：根据技术方案检索相关专利文献",
            Scenario.TECHNICAL_ANALYSIS: "技术分析：深度理解技术方案，提取技术特征",
            Scenario.CREATIVITY_ANALYSIS: "创造性分析：评估专利申请的创造性高度",
            Scenario.NOVELTY_ANALYSIS: "新颖性分析：评估专利申请的新颖性",
            Scenario.INFINGEMENT_ANALYSIS: "侵权分析：评估产品/方法是否侵犯专利权",
            Scenario.INVALIDATION_ANALYSIS: "无效宣告：分析专利无效宣告的可能性",
            Scenario.APPLICATION_REVIEW: "申请文件审查：审查专利申请文件的质量",
            Scenario.WRITING_REVIEW: "撰写审查：审查专利撰写质量"
        }
        return descriptions.get(scenario, "未知场景")

    async def _load_agent_base_prompt(self, agent_type: AgentType) -> str:
        """加载智能体基础提示词"""
        # 这里应该从文件加载，暂时提供占位符
        base_prompts = {
            AgentType.RETRIEVER: "# 检索者\n专利检索专家，多源检索、去重排序",
            AgentType.ANALYZER: "# 分析者\n技术分析专家，特征提取、双图分析",
            AgentType.CREATIVITY_ANALYZER: "# 创造性分析智能体\n专利创造性评估专家",
            AgentType.NOVELTY_ANALYZER: "# 新颖性分析智能体\n专利新颖性评估专家",
            AgentType.INFINGEMENT_ANALYZER: "# 侵权分析智能体\n专利侵权风险评估专家",
            AgentType.INVALIDATION_ANALYZER: "# 无效宣告分析智能体\n专利无效宣告分析专家",
            AgentType.APPLICATION_DOCUMENT_REVIEWER: "# 申请文件审查智能体\n专利申请文件质量审查专家",
            AgentType.WRITING_REVIEWER: "# 撰写审查智能体\n专利撰写质量审查专家",
            AgentType.XIAONUO: "# 小诺\n智能体编排调度官",
            AgentType.XIAONA: "# 小娜\n法律专家智能体"
        }
        return base_prompts.get(agent_type, "# 未知智能体")

    async def _load_scenario_knowledge(
        self,
        scenario: Scenario,  # noqa: ARG001 (reserved for future use)
        agent_type: AgentType  # noqa: ARG001 (reserved for future use)
    ) -> str:
        """加载场景知识"""
        # 这里应该从知识库加载，暂时返回占位符
        return "## 相关知识\n（知识库内容待加载）"

    async def _trigger_when_to_use(
        self,
        agent_type: AgentType,  # noqa: ARG001 (reserved for future use)
        scenario: Scenario,  # noqa: ARG001 (reserved for future use)
        user_input: str  # noqa: ARG001 (reserved for future use)
    ) -> list[tuple[str, str]]:
        """触发whenToUse能力模块"""
        # 这里应该实现whenToUse逻辑，暂时返回空
        # 实际实现需要：
        # 1. 分析用户输入
        # 2. 匹配whenToUse条件
        # 3. 加载相应的能力模块
        return []

    async def _load_scenario_business_logic(
        self,
        scenario: Scenario,  # noqa: ARG001 (reserved for future use)
        agent_type: AgentType  # noqa: ARG001 (reserved for future use)
    ) -> str:
        """加载场景业务逻辑"""
        # 这里应该从文件加载，暂时返回占位符
        return "## 业务流程\n（业务流程内容待加载）"

    def get_cache_stats(self) -> dict[str, Any]:  # noqa: ARG001 (method used externally)
        """获取缓存统计信息"""
        stats = {
            "total_assemblies": self.total_assemblies,
            "total_cache_hits": self.total_cache_hits,
            "static_cache": {},
            "knowledge_cache": {}
        }

        if self.static_cache:
            stats["static_cache"] = self.static_cache.get_stats()

        if self.knowledge_cache:
            stats["knowledge_cache"] = self.knowledge_cache.get_stats()

        return stats

    def clear_cache(self) -> None:
        """清空所有缓存"""
        if self.static_cache:
            self.static_cache.clear()
        if self.knowledge_cache:
            self.knowledge_cache.clear()


# 便捷函数
async def assemble_agent_context(
    agent_type: str,
    scenario: str,
    user_input: str,
    session_id: str,
    enable_cache: bool = True
) -> AssemblyResult:
    """
    便捷函数：组装智能体上下文

    Args:
        agent_type: 智能体类型字符串
        scenario: 场景字符串
        user_input: 用户输入
        session_id: 会话ID
        enable_cache: 是否启用缓存

    Returns:
        AssemblyResult: 组装结果
    """
    assembler = XiaonuoContextAssembler(enable_cache=enable_cache)

    # 转换枚举
    agent_enum = AgentType(agent_type)
    scenario_enum = Scenario(scenario)

    # 创建会话上下文
    session_context = SessionContext(session_id=session_id)

    # 组装上下文
    result = await assembler.assemble_context(
        agent_type=agent_enum,
        scenario=scenario_enum,
        user_input=user_input,
        session_context=session_context,
        progressive=True
    )

    return result
