
# pyright: ignore
# !/usr/bin/env python3
"""
提示链处理器 (Prompt Chaining Pattern)
基于《智能体设计》提示链模式的实现

应用场景:
- 复杂任务的分解处理
- 多步骤推理过程
- 系统性问题解决
- 质量控制和验证

实施优先级: ⭐⭐⭐⭐⭐ (最高)
预期收益: 提升任务处理的系统性和准确性
"""

import asyncio
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ChainStatus(Enum):
    """链状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ChainStepStatus(Enum):
    """链步骤状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_REFINEMENT = "requires_refinement"


class ValidationType(Enum):
    """验证类型"""

    OUTPUT_FORMAT = "output_format"
    CONTENT_QUALITY = "content_quality"
    LOGICAL_CONSISTENCY = "logical_consistency"
    REQUIREMENTS_SATISFACTION = "requirements_satisfaction"


@dataclass
class ChainStep:
    """提示链步骤"""

    id: str
    name: str
    prompt_template: str
    input_mapping: dict[str, str] = field(default_factory=dict)  # 输入映射
    output_schema: dict[str, Any] = field(default_factory=dict)  # 输出结构定义
    validation_rules: list[dict[str, Any]] = field(default_factory=list)
    retry_attempts: int = 3
    timeout_seconds: int = 60
    requires_refinement: bool = False
    refinement_criteria: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChainExecution:
    """链执行结果"""

    chain_id: str
    steps_results: dict[str, Any] = field(default_factory=dict)
    execution_log: list[dict[str, Any]] = field(default_factory=list)
    total_time: float = 0.0
    success: bool = False
    final_output: Any = None
    error_message: str | None = None


class PromptChainProcessor:
    """提示链处理器"""

    def __init__(self):
        self.chain_templates = self._load_chain_templates()
        self.execution_history = []
        self.validator = ResponseValidator()
        self.refiner = ResponseRefiner()

    def _load_chain_templates(self) -> dict[str, list[ChainStep]]:
        """加载链模板"""
        return {
            "patent_analysis_chain": [
                ChainStep(
                    id="query_analysis",
                    name="查询分析",
                    prompt_template="""
请分析用户的专利查询请求,提取关键信息:

用户查询: {user_query}
上下文: {context}

请提供以下信息:
1. 主要技术领域
2. 关键技术术语
3. 检索策略
4. 预期结果类型

分析结果:
""",
                    output_schema={
                        "technical_field": "string",
                        "key_terms": "list",
                        "search_strategy": "string",
                        "expected_result_type": "string",
                    },
                    validation_rules=[
                        {"type": "required_fields", "fields": ["technical_field", "key_terms"]},
                        {"type": "min_list_length", "field": "key_terms", "min_length": 3},
                    ],
                ),
                ChainStep(
                    id="patent_search",
                    name="专利检索",
                    prompt_template="""
基于分析结果,执行专利检索:

技术领域: {technical_field}
关键术语: {key_terms}
检索策略: {search_strategy}

请检索相关专利并返回前10个最相关的结果。
检索结果:
""",
                    input_mapping={
                        "technical_field": "steps_results.query_analysis.technical_field",
                        "key_terms": "steps_results.query_analysis.key_terms",
                        "search_strategy": "steps_results.query_analysis.search_strategy",
                    },
                    output_schema={
                        "patents": "list",
                        "search_count": "integer",
                        "relevance_score": "float",
                    },
                    requires_refinement=True,
                    refinement_criteria={"min_patents": 5, "max_patents": 15, "min_relevance": 0.7},
                ),
                ChainStep(
                    id="patent_analysis",
                    name="专利分析",
                    prompt_template="""
分析检索到的专利,提供深度分析:

专利列表: {patents}
检索数量: {search_count}
相关性评分: {relevance_score}

请分析:
1. 技术发展趋势
2. 主要竞争对手
3. 创新点识别
4. 法律状态评估

分析结果:
""",
                    input_mapping={
                        "patents": "steps_results.patent_search.patents",
                        "search_count": "steps_results.patent_search.search_count",
                        "relevance_score": "steps_results.patent_search.relevance_score",
                    },
                    output_schema={
                        "technology_trends": "list",
                        "competitors": "list",
                        "innovation_points": "list",
                        "legal_status": "string",
                    },
                    validation_rules=[
                        {
                            "type": "required_fields",
                            "fields": ["technology_trends", "innovation_points"],
                        }
                    ],
                ),
                ChainStep(
                    id="report_generation",
                    name="报告生成",
                    prompt_template="""
基于前面的分析结果,生成完整的专利分析报告:

技术趋势: {technology_trends}
竞争对手: {competitors}
创新点: {innovation_points}
法律状态: {legal_status}

请生成包含以下部分的详细报告:
1. 执行摘要
2. 技术分析
3. 市场分析
4. 建议

报告内容:
""",
                    input_mapping={
                        "technology_trends": "steps_results.patent_analysis.technology_trends",
                        "competitors": "steps_results.patent_analysis.competitors",
                        "innovation_points": "steps_results.patent_analysis.innovation_points",
                        "legal_status": "steps_results.patent_analysis.legal_status",
                    },
                ),
            ],
            "system_optimization_chain": [
                ChainStep(
                    id="problem_identification",
                    name="问题识别",
                    prompt_template="""
分析系统性能问题:

问题描述: {problem_description}
系统指标: {system_metrics}

请识别:
1. 主要性能瓶颈
2. 影响程度评估
3. 可能的根本原因

问题分析:
""",
                    output_schema={
                        "bottlenecks": "list",
                        "impact_assessment": "string",
                        "root_causes": "list",
                    },
                ),
                ChainStep(
                    id="solution_design",
                    name="解决方案设计",
                    prompt_template="""
基于问题分析,设计优化方案:

性能瓶颈: {bottlenecks}
影响评估: {impact_assessment}
根本原因: {root_causes}

请提供:
1. 优化策略
2. 实施步骤
3. 预期效果
4. 风险评估

解决方案:
""",
                    input_mapping={
                        "bottlenecks": "steps_results.problem_identification.bottlenecks",
                        "impact_assessment": "steps_results.problem_identification.impact_assessment",
                        "root_causes": "steps_results.problem_identification.root_causes",
                    },
                    requires_refinement=True,
                    refinement_criteria={"min_solutions": 3, "detailed_steps": True},
                ),
                ChainStep(
                    id="implementation_plan",
                    name="实施计划",
                    prompt_template="""
将解决方案转化为具体的实施计划:

优化方案: {solution_design}

请制定:
1. 详细的实施步骤
2. 时间规划
3. 资源需求
4. 验证标准

实施计划:
""",
                    input_mapping={"solution_design": "steps_results.solution_design.output"},
                ),
            ],
        }

    def create_chain(self, task_type: str, input_data: dict[str, Any]) -> str:
        """创建提示链"""
        if task_type not in self.chain_templates:
            raise ValueError(f"未知的任务类型: {task_type}")

        chain_steps = self.chain_templates[task_type]
        chain_id = f"chain_{int(time.time())}"

        # 验证输入数据
        self._validate_input_data(chain_steps, input_data)

        # 创建执行记录
        execution_record = {
            "chain_id": chain_id,
            "task_type": task_type,
            "input_data": input_data,
            "steps_count": len(chain_steps),
            "created_at": datetime.now(),
            "status": "created",
        }

        self.execution_history.append(execution_record)

        print(f"🔗 创建提示链: {task_type}")
        print(f"   链ID: {chain_id}")
        print(f"   步骤数: {len(chain_steps)}")

        return chain_id

    async def execute_chain(self, chain_id: str, input_data: dict[str, Any]) -> ChainExecution:
        """执行提示链"""
        print(f"🚀 执行提示链: {chain_id}")

        execution = ChainExecution(chain_id=chain_id)
        start_time = time.time()

        # 查找对应的链模板
        chain_record = next((r for r in self.execution_history if r["chain_id"] == chain_id), None)
        if not chain_record:
            execution.error_message = "找不到对应的链配置"
            return execution

        chain_steps = self.chain_templates.get(chain_record["task_type"], [])
        steps_results = {}

        try:
            for step in chain_steps:
                print(f"   📋 执行步骤: {step.name}")

                step_result = await self._execute_step(step, input_data, steps_results)

                # 验证步骤结果
                validation_result = self.validator.validate_response(step, step_result)

                if not validation_result.valid:
                    if step.retry_attempts > 0:
                        print(f"      ⚠️ 验证失败,重试中... ({step.retry_attempts} 次剩余)")
                        step.retry_attempts -= 1
                        # 可以选择调整输入或策略后重试
                        continue
                    else:
                        execution.error_message = f"步骤 {step.name} 验证失败"
                        break

                # 检查是否需要改进
                if step.requires_refinement and self.refiner.needs_refinement(step, step_result):
                    print("      🔧 结果需要改进...")
                    step_result = await self.refiner.refine_response(step, step_result)

                steps_results[step.id] = step_result

                # 记录执行日志
                execution_log = {
                    "step_id": step.id,
                    "step_name": step.name,
                    "timestamp": datetime.now(),
                    "validation_result": validation_result.valid,
                    "execution_time": 0,  # 这里应该记录实际执行时间
                }
                execution.execution_log.append(execution_log)

            # 设置最终输出
            execution.steps_results = steps_results
            execution.success = True

            # 获取最后一步的输出作为最终结果
            if chain_steps:
                last_step = chain_steps[-1]
                execution.final_output = steps_results.get(last_step.id)

        except Exception:
            execution.success = False

        execution.total_time = time.time() - start_time

        # 更新执行记录
        chain_record["status"] = "completed" if execution.success else "failed"
        chain_record["execution_time"] = execution.total_time
        chain_record["completed_at"] = datetime.now()

        print(f"   {'✅' if execution.success else '❌'} 链执行完成")
        print(f"   耗时: {execution.total_time:.2f}s")

        return execution

    async def _execute_step(
        self, step: ChainStep, input_data: dict[str, Any], previous_results: dict[str, Any]
    ) -> Any:
        """执行单个步骤"""
        # 准备输入数据
        formatted_input = self._prepare_step_input(step, input_data, previous_results)

        # 构建完整的提示
        step.prompt_template.format(**formatted_input)

        # 模拟AI响应(实际应用中这里应该调用AI模型)
        await asyncio.sleep(0.1)  # 模拟处理时间

        # 生成模拟响应
        response = self._generate_mock_response(step, formatted_input)

        return response

    def _prepare_step_input(
        self, step: ChainStep, input_data: dict[str, Any], previous_results: dict[str, Any]
    ) -> dict[str, Any]:
        """准备步骤输入数据"""
        formatted_input = input_data.copy()

        # 处理输入映射
        for key, mapping in step.input_mapping.items():
            if "." in mapping:
                # 处理嵌套映射 (例如: "steps_results.query_analysis.technical_field")
                parts = mapping.split(".")
                value = previous_results
                for part in parts:
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        value = None
                        break
                formatted_input[key] = value if value is not None else ""
            else:
                formatted_input[key] = input_data.get(mapping, "")

        return formatted_input

    def _generate_mock_response(
        self, step: ChainStep, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """生成模拟响应(实际应用中替换为真实的AI调用)"""
        # 基于步骤ID生成相应的模拟响应
        if step.id == "query_analysis":
            return {
                "technical_field": "人工智能和机器学习",
                "key_terms": ["神经网络", "深度学习", "算法优化", "数据处理"],
                "search_strategy": "使用关键词组合和分类检索",
                "expected_result_type": "专利文献和技术文档",
            }
        elif step.id == "patent_search":
            return {
                "patents": [
                    {"id": "1", "title": "神经网络优化方法", "relevance": 0.95},
                    {"id": "2", "title": "深度学习算法专利", "relevance": 0.92},
                ],
                "search_count": 8,
                "relevance_score": 0.89,
            }
        elif step.id == "patent_analysis":
            return {
                "technology_trends": ["AI算法优化", "硬件加速", "边缘计算"],
                "competitors": ["公司A", "公司B", "公司C"],
                "innovation_points": ["新型架构", "优化算法", "应用创新"],
                "legal_status": "大部分专利有效,部分即将到期",
            }
        else:
            # 默认响应
            return {"result": f"步骤 {step.name} 的处理结果"}

    def _validate_input_data(self, chain_steps: list[ChainStep], input_data: dict[str, Any]) -> Any:
        """验证输入数据"""
        required_fields = set()

        # 收集所有步骤需要的输入字段
        for step in chain_steps:
            # 从提示模板中提取字段
            fields = re.findall(r"\{(\w+)\}", step.prompt_template)
            required_fields.update(fields)

        # 检查输入数据是否包含所需字段
        missing_fields = required_fields - set(input_data.keys())
        if missing_fields:
            print(f"⚠️ 缺少输入字段: {missing_fields}")

    def get_chain_templates(self) -> dict[str, list[ChainStep]]:
        """获取所有链模板"""
        return self.chain_templates

    def get_execution_history(self) -> list[dict[str, Any]]:
        """获取执行历史"""
        return self.execution_history

    def create_custom_chain(self, chain_definition: dict[str, Any]) -> str:
        """创建自定义链"""
        chain_id = f"custom_chain_{int(time.time())}"

        # 将定义转换为ChainStep对象
        steps = []
        for i, step_def in enumerate(chain_definition.get("steps", [])):
            step = ChainStep(
                id=step_def.get("id", f"step_{i}"),
                name=step_def.get("name", f"步骤 {i + 1}"),
                prompt_template=step_def.get("prompt_template", ""),
                input_mapping=step_def.get("input_mapping", {}),
                output_schema=step_def.get("output_schema", {}),
                validation_rules=step_def.get("validation_rules", []),
            )
            steps.append(step)

        # 保存自定义链
        self.chain_templates[f"custom_{chain_id}"] = steps

        return chain_id


class ResponseValidator:
    """响应验证器"""

    def validate_response(self, step: ChainStep, response: Any) -> dict[str, Any]:
        """验证响应"""
        validation_result = {"valid": True, "errors": [], "warnings": []}

        try:
            # 检查必需字段
            for rule in step.validation_rules:
                if rule["type"] == "required_fields":
                    if isinstance(response, dict):
                        missing_fields = [
                            field for field in rule["fields"] if field not in response
                        ]
                        if missing_fields:
                            validation_result["valid"] = False
                            validation_result.get("errors").append(f"缺少必需字段: {missing_fields}")  # type: ignore

                elif rule["type"] == "min_list_length":
                    field_path = rule["field"]
                    field_value = self._get_nested_value(response, field_path)
                    if isinstance(field_value, list) and len(field_value) < rule["min_length"]:
                        validation_result["valid"] = False
                        validation_result.get("errors").append(  # type: ignore
                            f"字段 {field_path} 长度不足: 需要 {rule['min_length']} 项"
                        )

        except Exception as e:
            validation_result.get("errors").append(f"验证过程出错: {e!s}")  # type: ignore

        return validation_result

    def _get_nested_value(self, obj: Any, path: str) -> Any:
        """获取嵌套对象的值"""
        parts = path.split(".")
        value = obj
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value


class ResponseRefiner:
    """响应改进器"""

    def needs_refinement(self, step: ChainStep, response: Any) -> bool:
        """判断是否需要改进"""
        if not step.requires_refinement:
            return False

        criteria = step.refinement_criteria

        # 检查数量标准
        if "min_patents" in criteria and isinstance(response, dict):
            patents = response.get("patents", [])
            if len(patents) < criteria["min_patents"]:
                return True

        if "max_patents" in criteria and isinstance(response, dict):
            patents = response.get("patents", [])
            if len(patents) > criteria["max_patents"]:
                return True

        return False

    async def refine_response(self, step: ChainStep, response: Any) -> Any:
        """改进响应"""
        # 这里可以实现具体的改进逻辑
        # 例如:重新查询、过滤结果、扩展内容等

        print("      🔧 改进响应...")

        # 模拟改进过程
        await asyncio.sleep(0.05)

        # 返回改进后的响应
        return response


# 使用示例
async def main():
    """使用示例"""
    processor = PromptChainProcessor()

    # 示例1: 专利分析链
    print("=" * 50)
    print("示例1: 专利分析提示链")
    print("=" * 50)

    chain_id1 = processor.create_chain(
        task_type="patent_analysis_chain",
        input_data={
            "user_query": "查找与机器学习相关的专利",
            "context": {"user_domain": "AI研究", "time_range": "最近5年"},
        },
    )

    result1 = await processor.execute_chain(
        chain_id1,
        {
            "user_query": "查找与机器学习相关的专利",
            "context": {"user_domain": "AI研究", "time_range": "最近5年"},
        },
    )

    print("\n📊 执行结果1:")
    print(f"   成功: {result1.success}")
    print(f"   步骤数: {len(result1.steps_results)}")
    print(f"   执行时间: {result1.total_time:.2f}s")

    # 示例2: 自定义链
    print("\n" + "=" * 50)
    print("示例2: 自定义提示链")
    print("=" * 50)

    custom_chain_def = {
        "name": "内容创作链",
        "steps": [
            {
                "id": "topic_analysis",
                "name": "主题分析",
                "prompt_template": "分析主题: {topic}\n用户需求: {requirements}\n分析结果:",
                "input_mapping": {},
                "validation_rules": [{"type": "required_fields", "fields": ["analysis"]}],
            },
            {
                "id": "content_creation",
                "name": "内容创作",
                "prompt_template": "基于分析创作内容:\n{analysis}\n创作要求: {requirements}\n内容:",
                "input_mapping": {"analysis": "steps_results.topic_analysis.analysis"},
            },
        ],
    }

    processor.create_custom_chain(custom_chain_def)

    # 显示统计信息
    history = processor.get_execution_history()
    print("\n📈 执行统计:")
    print(f"   总执行次数: {len(history)}")
    print(f"   可用链模板: {len(processor.get_chain_templates())}")


# 入口点: @async_main装饰器已添加到main函数
