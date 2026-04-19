from __future__ import annotations
"""
专利任务分类系统 v1.0

基于专利NLP综述论文的任务分类体系

核心功能:
1. 意图识别 - 识别用户查询意图
2. 任务分类 - 将查询映射到预定义任务类型
3. 任务分解 - 将复杂任务分解为子任务
4. 工作流映射 - 映射到标准工作流程

专利NLP任务分类:
- 专利检索 (Prior Art Search)
- 专利分类 (Classification)
- 专利分析 (Analysis)
- 专利撰写 (Drafting)
- 专利翻译 (Translation)
- 专利问答 (Q&A)

使用模型: qwen3.5 (快速分类), deepseek-reasoner (复杂分解)

作者: Athena平台
版本: v1.0
日期: 2026-03-23
"""

import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PatentTaskType(Enum):
    """专利任务类型"""
    # 检索类
    PRIOR_ART_SEARCH = "prior_art_search"        # 现有技术检索
    SIMILARITY_SEARCH = "similarity_search"      # 相似专利检索
    PATENT_LOOKUP = "patent_lookup"              # 专利号查询

    # 分类类
    IPC_CLASSIFICATION = "ipc_classification"    # IPC分类
    CPC_CLASSIFICATION = "cpc_classification"    # CPC分类
    TECHNOLOGY_MAPPING = "technology_mapping"    # 技术领域映射

    # 分析类
    NOVELTY_ANALYSIS = "novelty_analysis"        # 新颖性分析
    INVENTIVENESS_ANALYSIS = "inventiveness_analysis"  # 创造性分析
    INFRINGEMENT_ANALYSIS = "infringement_analysis"    # 侵权分析
    INVALIDITY_ANALYSIS = "invalidity_analysis"        # 无效分析
    QUALITY_ASSESSMENT = "quality_assessment"          # 质量评估
    CLAIM_ANALYSIS = "claim_analysis"                  # 权利要求分析

    # 撰写类
    CLAIM_DRAFTING = "claim_drafting"            # 权利要求撰写
    SPECIFICATION_DRAFTING = "specification_drafting"  # 说明书撰写
    OA_RESPONSE = "oa_response"                  # 审查意见答复
    FIGURE_DESCRIPTION = "figure_description"    # 附图说明

    # 问答类
    PATENT_QA = "patent_qa"                      # 专利问答
    LAW_CONSULTATION = "law_consultation"        # 法律咨询
    PROCEDURE_GUIDE = "procedure_guide"          # 流程指导

    # 翻译类
    PATENT_TRANSLATION = "patent_translation"    # 专利翻译

    # 其他
    UNKNOWN = "unknown"                          # 未知类型


class TaskComplexity(Enum):
    """任务复杂度"""
    SIMPLE = "simple"          # 简单任务 - 单步完成
    MODERATE = "moderate"      # 中等任务 - 2-3步
    COMPLEX = "complex"        # 复杂任务 - 多步骤
    VERY_COMPLEX = "very_complex"  # 非常复杂 - 需要分解


class WorkflowStage(Enum):
    """工作流阶段"""
    DISCOVERY = "discovery"        # 发现阶段 - 了解需求
    RETRIEVAL = "retrieval"        # 检索阶段 - 收集信息
    ANALYSIS = "analysis"          # 分析阶段 - 深度分析
    GENERATION = "generation"      # 生成阶段 - 产出内容
    VALIDATION = "validation"      # 验证阶段 - 质量检查


class ExecutionPriority(Enum):
    """执行优先级"""
    URGENT = 1      # 紧急
    HIGH = 2        # 高
    NORMAL = 3      # 普通
    LOW = 4         # 低


@dataclass
class SubTask:
    """子任务"""
    subtask_id: str                  # 子任务ID
    task_type: PatentTaskType        # 任务类型
    description: str                 # 描述
    dependencies: list[str] = field(default_factory=list)  # 依赖的子任务
    estimated_time: float = 1.0      # 预估时间（分钟）
    required_tools: list[str] = field(default_factory=list)  # 所需工具
    priority: ExecutionPriority = ExecutionPriority.NORMAL

    def to_dict(self) -> dict:
        return {
            "subtask_id": self.subtask_id,
            "task_type": self.task_type.value,
            "description": self.description,
            "dependencies": self.dependencies,
            "estimated_time": self.estimated_time,
            "required_tools": self.required_tools,
            "priority": self.priority.value
        }


@dataclass
class WorkflowStep:
    """工作流步骤"""
    step_id: str                     # 步骤ID
    stage: WorkflowStage             # 工作流阶段
    subtasks: list[SubTask]          # 子任务列表
    description: str = ""            # 步骤描述
    order: int = 1                   # 执行顺序

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "stage": self.stage.value,
            "description": self.description,
            "order": self.order,
            "subtasks": [s.to_dict() for s in self.subtasks]
        }


@dataclass
class TaskClassificationResult:
    """任务分类结果"""
    classification_id: str                    # 分类ID

    # 分类结果
    primary_task_type: PatentTaskType         # 主要任务类型
    secondary_task_types: list[PatentTaskType] = field(default_factory=list)  # 次要类型
    complexity: TaskComplexity = TaskComplexity.MODERATE  # 复杂度

    # 意图识别
    detected_intent: str = ""                 # 检测到的意图
    intent_confidence: float = 0.8            # 意图置信度

    # 实体提取
    entities: dict[str, str] = field(default_factory=dict)  # 提取的实体
    # 例如: {"patent_number": "CN123456", "ipc_class": "H04L"}

    # 任务分解
    subtasks: list[SubTask] = field(default_factory=list)  # 子任务列表

    # 工作流映射
    workflow_steps: list[WorkflowStep] = field(default_factory=list)  # 工作流步骤

    # 执行建议
    recommended_tools: list[str] = field(default_factory=list)  # 推荐工具
    estimated_total_time: float = 0.0         # 预估总时间
    execution_priority: ExecutionPriority = ExecutionPriority.NORMAL

    # 元数据
    processing_time_ms: float = 0.0
    model_used: str = ""

    def to_dict(self) -> dict:
        return {
            "classification_id": self.classification_id,
            "primary_task_type": self.primary_task_type.value,
            "secondary_task_types": [t.value for t in self.secondary_task_types],
            "complexity": self.complexity.value,
            "detected_intent": self.detected_intent,
            "intent_confidence": self.intent_confidence,
            "entities": self.entities,
            "subtasks": [s.to_dict() for s in self.subtasks],
            "workflow_steps": [w.to_dict() for w in self.workflow_steps],
            "recommended_tools": self.recommended_tools,
            "estimated_total_time": self.estimated_total_time,
            "execution_priority": self.execution_priority.value,
            "processing_time_ms": self.processing_time_ms
        }


class PatentTaskClassifier:
    """
    专利任务分类系统

    识别用户查询意图，分类任务类型，并生成执行工作流。
    """

    # 模型配置
    MODEL_CONFIG = {
        "classification": {
            "model": "qwen3.5",
            "provider": "ollama",
            "temperature": 0.2,
            "max_tokens": 1000
        },
        "decomposition": {
            "model": "deepseek-reasoner",
            "provider": "deepseek",
            "temperature": 0.3,
            "max_tokens": 2000
        }
    }

    # 意图关键词映射
    INTENT_KEYWORDS = {
        PatentTaskType.PRIOR_ART_SEARCH: [
            "现有技术", "检索", "查找", "对比", "查新", "现有文献"
        ],
        PatentTaskType.SIMILARITY_SEARCH: [
            "相似", "类似", "同类", "相近"
        ],
        PatentTaskType.PATENT_LOOKUP: [
            "查询专利", "专利号", "公开号", "申请号", "查看专利"
        ],
        PatentTaskType.IPC_CLASSIFICATION: [
            "IPC分类", "分类号", "技术分类"
        ],
        PatentTaskType.NOVELTY_ANALYSIS: [
            "新颖性", "创新性", "新创性"
        ],
        PatentTaskType.INVENTIVENESS_ANALYSIS: [
            "创造性", "非显而易见", "技术进步"
        ],
        PatentTaskType.INFRINGEMENT_ANALYSIS: [
            "侵权", "是否侵权", "侵权判定", "侵权分析"
        ],
        PatentTaskType.INVALIDITY_ANALYSIS: [
            "无效", "无效宣告", "无效分析"
        ],
        PatentTaskType.QUALITY_ASSESSMENT: [
            "质量", "评估", "评分", "质量分析"
        ],
        PatentTaskType.CLAIM_ANALYSIS: [
            "权利要求", "分析", "范围"
        ],
        PatentTaskType.CLAIM_DRAFTING: [
            "撰写权利要求", "写权利要求", "起草权利要求"
        ],
        PatentTaskType.SPECIFICATION_DRAFTING: [
            "撰写说明书", "写说明书", "起草说明书"
        ],
        PatentTaskType.OA_RESPONSE: [
            "审查意见", "答复", "OA答复", "审查意见答复"
        ],
        PatentTaskType.PATENT_QA: [
            "什么是", "如何", "怎样", "请问", "问题"
        ],
        PatentTaskType.LAW_CONSULTATION: [
            "法律规定", "法条", "法律咨询", "专利法"
        ],
        PatentTaskType.PROCEDURE_GUIDE: [
            "流程", "程序", "怎么办理", "申请流程"
        ],
        PatentTaskType.PATENT_TRANSLATION: [
            "翻译", "translate"
        ]
    }

    # 工作流模板
    WORKFLOW_TEMPLATES = {
        PatentTaskType.PRIOR_ART_SEARCH: [
            WorkflowStage.DISCOVERY,
            WorkflowStage.RETRIEVAL,
            WorkflowStage.ANALYSIS,
            WorkflowStage.VALIDATION
        ],
        PatentTaskType.INFRINGEMENT_ANALYSIS: [
            WorkflowStage.DISCOVERY,
            WorkflowStage.RETRIEVAL,
            WorkflowStage.ANALYSIS,
            WorkflowStage.GENERATION,
            WorkflowStage.VALIDATION
        ],
        PatentTaskType.CLAIM_DRAFTING: [
            WorkflowStage.DISCOVERY,
            WorkflowStage.ANALYSIS,
            WorkflowStage.GENERATION,
            WorkflowStage.VALIDATION
        ],
        PatentTaskType.SPECIFICATION_DRAFTING: [
            WorkflowStage.DISCOVERY,
            WorkflowStage.ANALYSIS,
            WorkflowStage.GENERATION,
            WorkflowStage.VALIDATION
        ]
    }

    def __init__(self, llm_manager=None):
        """
        初始化任务分类器

        Args:
            llm_manager: LLM管理器实例
        """
        self.llm_manager = llm_manager
        self._init_prompts()

    def _init_prompts(self):
        """初始化提示词模板"""
        self.classification_prompt = """你是一位专利任务分类专家。请分析用户查询并识别任务类型。

【用户查询】
{query}

【任务类型列表】
- prior_art_search: 现有技术检索
- similarity_search: 相似专利检索
- patent_lookup: 专利号查询
- ipc_classification: IPC分类
- novelty_analysis: 新颖性分析
- inventiveness_analysis: 创造性分析
- infringement_analysis: 侵权分析
- invalidity_analysis: 无效分析
- quality_assessment: 质量评估
- claim_analysis: 权利要求分析
- claim_drafting: 权利要求撰写
- specification_drafting: 说明书撰写
- oa_response: 审查意见答复
- patent_qa: 专利问答
- law_consultation: 法律咨询
- procedure_guide: 流程指导
- patent_translation: 专利翻译

【输出格式】(JSON)
```json
{{
  "primary_task_type": "任务类型",
  "secondary_task_types": ["次要类型1", "次要类型2"],
  "complexity": "simple/moderate/complex/very_complex",
  "detected_intent": "检测到的意图描述",
  "entities": {{
    "patent_number": "提取的专利号",
    "ipc_class": "提取的分类号"
  }},
  "confidence": 0.85
}}
```

只输出JSON，不要其他内容。
"""

        self.decomposition_prompt = """请将以下专利任务分解为子任务。

【任务类型】
{task_type}

【任务描述】
{description}

【分解要求】
1. 将复杂任务分解为可执行的子任务
2. 标识子任务之间的依赖关系
3. 估算每个子任务的执行时间
4. 列出所需的工具

【输出格式】(JSON)
```json
{{
  "subtasks": [
    {{
      "subtask_id": "ST1",
      "task_type": "子任务类型",
      "description": "描述",
      "dependencies": [],
      "estimated_time": 2.0,
      "required_tools": ["工具1"],
      "priority": 1
    }}
  ],
  "total_estimated_time": 5.0
}}
```
"""

    # ==================== 主要公共接口 ====================

    async def classify(
        self,
        query: str,
        context: dict | None = None
    ) -> TaskClassificationResult:
        """
        分类专利任务

        Args:
            query: 用户查询
            context: 额外上下文（可选）

        Returns:
            TaskClassificationResult: 分类结果
        """
        start_time = time.time()
        classification_id = f"classify_{int(time.time() * 1000)}"

        logger.info(f"开始任务分类: {classification_id}")

        # 1. 快速规则分类
        rule_based_type = self._rule_based_classification(query)
        entities = self._extract_entities(query)

        # 2. LLM深度分类（如果有）
        if self.llm_manager:
            result = await self._llm_classification(
                query, context, classification_id
            )
        else:
            result = self._heuristic_classification(
                query, rule_based_type, entities, classification_id
            )

        # 3. 任务分解（复杂任务）
        if result.complexity in [TaskComplexity.COMPLEX, TaskComplexity.VERY_COMPLEX]:
            if self.llm_manager:
                decomposition = await self._decompose_task(
                    result.primary_task_type, query
                )
                result.subtasks = decomposition.get("subtasks", [])
                result.estimated_total_time = decomposition.get("total_estimated_time", 0.0)
            else:
                result.subtasks = self._heuristic_decomposition(result.primary_task_type)
                result.estimated_total_time = sum(s.estimated_time for s in result.subtasks)

        # 4. 工作流映射
        result.workflow_steps = self._map_to_workflow(
            result.primary_task_type, result.subtasks
        )

        # 5. 推荐工具
        result.recommended_tools = self._recommend_tools(result.primary_task_type)

        # 6. 计算处理时间
        result.processing_time_ms = (time.time() - start_time) * 1000

        return result

    async def batch_classify(
        self,
        queries: list[str]
    ) -> list[TaskClassificationResult]:
        """
        批量分类

        Args:
            queries: 查询列表

        Returns:
            List[TaskClassificationResult]: 分类结果列表
        """
        results = []
        for query in queries:
            result = await self.classify(query)
            results.append(result)
        return results

    def get_task_workflow(
        self,
        task_type: PatentTaskType
    ) -> list[WorkflowStage]:
        """
        获取任务的标准工作流

        Args:
            task_type: 任务类型

        Returns:
            List[WorkflowStage]: 工作流阶段列表
        """
        return self.WORKFLOW_TEMPLATES.get(
            task_type,
            [WorkflowStage.DISCOVERY, WorkflowStage.ANALYSIS, WorkflowStage.VALIDATION]
        )

    # ==================== 私有方法 ====================

    def _rule_based_classification(self, query: str) -> PatentTaskType:
        """基于规则的任务分类"""
        query_lower = query.lower()

        # 按优先级匹配关键词
        scores = {}
        for task_type, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                scores[task_type] = score

        if scores:
            return max(scores, key=scores.get)

        return PatentTaskType.UNKNOWN

    def _extract_entities(self, query: str) -> dict[str, str]:
        """提取实体"""
        entities = {}

        # 专利号模式
        patent_patterns = [
            r'CN\d{8,12}[A-Z]?',      # 中国专利号
            r'US\d{7,}',               # 美国专利号
            r'EP\d{7,}',               # 欧洲专利号
            r'JP\d{4}-\d{6,}',         # 日本专利号
        ]

        for pattern in patent_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                entities["patent_number"] = match.group()
                break

        # IPC分类号
        ipc_pattern = r'[A-H]\d{2}[A-Z]\s*\d+/\d+'
        ipc_match = re.search(ipc_pattern, query)
        if ipc_match:
            entities["ipc_class"] = ipc_match.group()

        # 年份
        year_pattern = r'(19|20)\d{2}年?'
        year_match = re.search(year_pattern, query)
        if year_match:
            entities["year"] = year_match.group()

        return entities

    async def _llm_classification(
        self,
        query: str,
        context: dict | None,
        classification_id: str
    ) -> TaskClassificationResult:
        """LLM深度分类"""
        try:
            prompt = self.classification_prompt.format(query=query[:500])

            response = await self.llm_manager.generate(
                message=prompt,
                task_type="task_classification",
                model_id=self.MODEL_CONFIG["classification"]["model"],
                temperature=self.MODEL_CONFIG["classification"]["temperature"]
            )

            response_text = response.content if hasattr(response, 'content') else str(response)
            result = self._parse_json_response(response_text)

            if result:
                return self._build_classification_result(
                    result, query, classification_id
                )

        except Exception as e:
            logger.warning(f"LLM分类失败: {e}")

        return self._heuristic_classification(
            query, self._rule_based_classification(query), {}, classification_id
        )

    def _heuristic_classification(
        self,
        query: str,
        rule_based_type: PatentTaskType,
        entities: dict[str, str],
        classification_id: str
    ) -> TaskClassificationResult:
        """启发式分类"""
        # 判断复杂度
        complexity = self._estimate_complexity(query, rule_based_type)

        # 推断优先级
        priority = ExecutionPriority.NORMAL
        if "紧急" in query or "尽快" in query:
            priority = ExecutionPriority.URGENT
        elif "重要" in query:
            priority = ExecutionPriority.HIGH

        return TaskClassificationResult(
            classification_id=classification_id,
            primary_task_type=rule_based_type,
            secondary_task_types=[],
            complexity=complexity,
            detected_intent=f"检测到{rule_based_type.value}意图",
            intent_confidence=0.7,
            entities=entities,
            execution_priority=priority,
            model_used="heuristic"
        )

    def _build_classification_result(
        self,
        result: dict,
        query: str,
        classification_id: str
    ) -> TaskClassificationResult:
        """构建分类结果"""
        try:
            primary_type = PatentTaskType(
                result.get("primary_task_type", "unknown")
            )
        except ValueError:
            primary_type = PatentTaskType.UNKNOWN

        try:
            complexity = TaskComplexity(
                result.get("complexity", "moderate")
            )
        except ValueError:
            complexity = TaskComplexity.MODERATE

        secondary_types = []
        for t in result.get("secondary_task_types", []):
            try:
                secondary_types.append(PatentTaskType(t))
            except ValueError:
                pass

        return TaskClassificationResult(
            classification_id=classification_id,
            primary_task_type=primary_type,
            secondary_task_types=secondary_types,
            complexity=complexity,
            detected_intent=result.get("detected_intent", ""),
            intent_confidence=result.get("confidence", 0.8),
            entities=result.get("entities", {}),
            model_used=self.MODEL_CONFIG["classification"]["model"]
        )

    def _estimate_complexity(
        self,
        query: str,
        task_type: PatentTaskType
    ) -> TaskComplexity:
        """估算任务复杂度"""
        # 基于任务类型
        complex_tasks = [
            PatentTaskType.INFRINGEMENT_ANALYSIS,
            PatentTaskType.INVALIDITY_ANALYSIS,
            PatentTaskType.SPECIFICATION_DRAFTING,
            PatentTaskType.OA_RESPONSE
        ]

        if task_type in complex_tasks:
            return TaskComplexity.COMPLEX

        # 基于查询长度
        if len(query) > 200:
            return TaskComplexity.COMPLEX
        elif len(query) > 100:
            return TaskComplexity.MODERATE
        else:
            return TaskComplexity.SIMPLE

    async def _decompose_task(
        self,
        task_type: PatentTaskType,
        description: str
    ) -> dict:
        """分解任务"""
        try:
            prompt = self.decomposition_prompt.format(
                task_type=task_type.value,
                description=description[:500]
            )

            response = await self.llm_manager.generate(
                message=prompt,
                task_type="task_decomposition",
                model_id=self.MODEL_CONFIG["decomposition"]["model"],
                temperature=self.MODEL_CONFIG["decomposition"]["temperature"]
            )

            response_text = response.content if hasattr(response, 'content') else str(response)
            result = self._parse_json_response(response_text)

            if result:
                subtasks = [
                    SubTask(
                        subtask_id=s.get("subtask_id", f"ST{i}"),
                        task_type=task_type,  # 简化处理
                        description=s.get("description", ""),
                        dependencies=s.get("dependencies", []),
                        estimated_time=s.get("estimated_time", 1.0),
                        required_tools=s.get("required_tools", []),
                        priority=ExecutionPriority(s.get("priority", 3))
                    )
                    for i, s in enumerate(result.get("subtasks", []))
                ]
                return {
                    "subtasks": subtasks,
                    "total_estimated_time": result.get("total_estimated_time", 0.0)
                }

        except Exception as e:
            logger.warning(f"任务分解失败: {e}")

        return {"subtasks": self._heuristic_decomposition(task_type), "total_estimated_time": 0.0}

    def _heuristic_decomposition(
        self,
        task_type: PatentTaskType
    ) -> list[SubTask]:
        """启发式任务分解"""
        decomposition_templates = {
            PatentTaskType.PRIOR_ART_SEARCH: [
                SubTask("ST1", PatentTaskType.PRIOR_ART_SEARCH, "提取技术特征", [], 2.0, ["feature_extractor"]),
                SubTask("ST2", PatentTaskType.SIMILARITY_SEARCH, "检索相关专利", ["ST1"], 5.0, ["patent_search"]),
                SubTask("ST3", PatentTaskType.NOVELTY_ANALYSIS, "对比分析", ["ST2"], 10.0, ["comparison_tool"])
            ],
            PatentTaskType.INFRINGEMENT_ANALYSIS: [
                SubTask("ST1", PatentTaskType.CLAIM_ANALYSIS, "解析权利要求", [], 3.0, ["claim_parser"]),
                SubTask("ST2", PatentTaskType.SIMILARITY_SEARCH, "检索被控产品", ["ST1"], 5.0, ["search"]),
                SubTask("ST3", PatentTaskType.INFRINGEMENT_ANALYSIS, "侵权比对", ["ST1", "ST2"], 10.0, ["infringement_analyzer"]),
                SubTask("ST4", PatentTaskType.QUALITY_ASSESSMENT, "生成报告", ["ST3"], 5.0, ["report_generator"])
            ],
            PatentTaskType.SPECIFICATION_DRAFTING: [
                SubTask("ST1", PatentTaskType.NOVELTY_ANALYSIS, "理解发明", [], 5.0, ["invention_analyzer"]),
                SubTask("ST2", PatentTaskType.CLAIM_DRAFTING, "撰写权利要求", ["ST1"], 10.0, ["claim_drafter"]),
                SubTask("ST3", PatentTaskType.SPECIFICATION_DRAFTING, "撰写说明书", ["ST1", "ST2"], 15.0, ["spec_drafter"]),
                SubTask("ST4", PatentTaskType.QUALITY_ASSESSMENT, "质量检查", ["ST3"], 5.0, ["quality_checker"])
            ]
        }

        return decomposition_templates.get(task_type, [
            SubTask("ST1", task_type, "执行任务", [], 5.0, [])
        ])

    def _map_to_workflow(
        self,
        task_type: PatentTaskType,
        subtasks: list[SubTask]
    ) -> list[WorkflowStep]:
        """映射到工作流"""
        stages = self.WORKFLOW_TEMPLATES.get(
            task_type,
            [WorkflowStage.DISCOVERY, WorkflowStage.ANALYSIS, WorkflowStage.VALIDATION]
        )

        workflow_steps = []

        for order, stage in enumerate(stages, 1):
            # 将子任务分配到各阶段
            stage_subtasks = []

            if stage == WorkflowStage.DISCOVERY:
                stage_subtasks = subtasks[:1] if subtasks else []
            elif stage == WorkflowStage.ANALYSIS:
                stage_subtasks = subtasks[1:-1] if len(subtasks) > 2 else subtasks
            elif stage == WorkflowStage.VALIDATION:
                stage_subtasks = subtasks[-1:] if subtasks else []

            workflow_steps.append(WorkflowStep(
                step_id=f"WS{order}",
                stage=stage,
                description=f"{stage.value}阶段",
                order=order,
                subtasks=stage_subtasks
            ))

        return workflow_steps

    def _recommend_tools(
        self,
        task_type: PatentTaskType
    ) -> list[str]:
        """推荐工具"""
        tool_recommendations = {
            PatentTaskType.PRIOR_ART_SEARCH: ["patent_database", "semantic_search", "citation_analyzer"],
            PatentTaskType.INFRINGEMENT_ANALYSIS: ["claim_parser", "product_analyzer", "comparison_tool"],
            PatentTaskType.CLAIM_DRAFTING: ["claim_generator", "quality_scorer", "scope_analyzer"],
            PatentTaskType.SPECIFICATION_DRAFTING: ["autospec_drafter", "figure_analyzer", "quality_checker"],
            PatentTaskType.QUALITY_ASSESSMENT: ["quality_scorer", "scope_analyzer", "completeness_checker"]
        }

        return tool_recommendations.get(task_type, ["generic_tool"])

    def _parse_json_response(self, response_text: str) -> dict | None:
        """解析JSON响应"""
        try:
            import json
            json_match = response_text
            if "```json" in response_text:
                json_match = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_match = response_text.split("```")[1].split("```")[0]

            return json.loads(json_match.strip())
        except Exception as e:
            logger.error(f"JSON解析失败: {e}")
            return None


# ==================== 便捷函数 ====================

async def classify_patent_task(
    query: str,
    llm_manager=None
) -> TaskClassificationResult:
    """
    便捷函数: 分类专利任务

    Args:
        query: 用户查询
        llm_manager: LLM管理器

    Returns:
        TaskClassificationResult: 分类结果
    """
    classifier = PatentTaskClassifier(llm_manager=llm_manager)
    return await classifier.classify(query)


def get_workflow_for_task(task_type: PatentTaskType) -> list[WorkflowStage]:
    """
    便捷函数: 获取任务工作流

    Args:
        task_type: 任务类型

    Returns:
        List[WorkflowStage]: 工作流阶段列表
    """
    classifier = PatentTaskClassifier()
    return classifier.get_task_workflow(task_type)


def format_classification_report(result: TaskClassificationResult) -> str:
    """
    格式化分类报告

    Args:
        result: 分类结果

    Returns:
        str: 格式化的报告
    """
    lines = [
        "=" * 60,
        "专利任务分类报告",
        "=" * 60,
        "",
        f"【分类ID】 {result.classification_id}",
        f"【主要任务类型】 {result.primary_task_type.value}",
        f"【任务复杂度】 {result.complexity.value}",
        f"【执行优先级】 {result.execution_priority.name}",
        "",
        f"【检测意图】 {result.detected_intent}",
        f"【意图置信度】 {result.intent_confidence:.0%}",
        ""
    ]

    if result.entities:
        lines.append("【提取实体】")
        for key, value in result.entities.items():
            lines.append(f"  • {key}: {value}")
        lines.append("")

    if result.subtasks:
        lines.append("【子任务分解】")
        for st in result.subtasks:
            deps = f" (依赖: {', '.join(st.dependencies)})" if st.dependencies else ""
            lines.append(f"  {st.subtask_id}: {st.description}{deps}")
            lines.append(f"      预估时间: {st.estimated_time:.1f}分钟")
        lines.append(f"  总预估时间: {result.estimated_total_time:.1f}分钟")
        lines.append("")

    if result.workflow_steps:
        lines.append("【工作流映射】")
        for step in result.workflow_steps:
            lines.append(f"  {step.order}. {step.stage.value}")

    if result.recommended_tools:
        lines.extend(["", "【推荐工具】"])
        lines.append(f"  {', '.join(result.recommended_tools)}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)
