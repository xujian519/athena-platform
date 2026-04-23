"""
专利撰写智能体

专注于专利申请文件的撰写，确保申请文件符合规范要求并提供充分保护。
"""

from typing import Any, Dict, List, Optional
import logging
import json
from core.agents.xiaona.base_component import BaseXiaonaComponent

logger = logging.getLogger(__name__)


class PatentDraftingProxy(BaseXiaonaComponent):
    """
    专利撰写智能体

    核心能力：
    - 分析技术交底书
    - 评估可专利性
    - 撰写说明书
    - 撰写权利要求书
    - 优化保护范围
    - 审查充分公开
    - 检测常见错误
    """

    def __init__(self, agent_id: str = "patent_drafting_proxy", config: Optional[Dict[str, Any]] = None):
        """
        初始化专利撰写智能体

        Args:
            agent_id: 智能体唯一标识
            config: 配置参数
        """
        super().__init__(agent_id, config)

    def _initialize(self) -> None:
        """初始化专利撰写智能体"""
        self._register_capabilities([
            {
                "name": "analyze_disclosure",
                "description": "分析技术交底书",
                "input_types": ["技术交底书"],
                "output_types": ["交底书分析报告"],
                "estimated_time": 15.0,
            },
            {
                "name": "assess_patentability",
                "description": "评估可专利性",
                "input_types": ["技术交底书", "现有技术"],
                "output_types": ["可专利性评估报告"],
                "estimated_time": 20.0,
            },
            {
                "name": "draft_specification",
                "description": "撰写说明书",
                "input_types": ["技术交底书", "可专利性评估"],
                "output_types": ["说明书草稿"],
                "estimated_time": 30.0,
            },
            {
                "name": "draft_claims",
                "description": "撰写权利要求书",
                "input_types": ["技术交底书", "说明书"],
                "output_types": ["权利要求书草稿"],
                "estimated_time": 25.0,
            },
            {
                "name": "optimize_protection_scope",
                "description": "优化保护范围",
                "input_types": ["权利要求书", "现有技术"],
                "output_types": ["优化建议"],
                "estimated_time": 20.0,
            },
            {
                "name": "review_adequacy",
                "description": "审查充分公开",
                "input_types": ["说明书", "权利要求书"],
                "output_types": ["充分公开审查报告"],
                "estimated_time": 15.0,
            },
            {
                "name": "detect_common_errors",
                "description": "检测常见错误",
                "input_types": ["说明书", "权利要求书"],
                "output_types": ["错误检测报告"],
                "estimated_time": 10.0,
            },
        ])

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """
你是一位专业的专利撰写专家，具备深厚的专利法知识和丰富的撰写经验。

你的职责是：
1. 分析技术交底书
2. 评估可专利性
3. 撰写说明书
4. 撰写权利要求书
5. 优化保护范围
6. 审查充分公开
7. 检测常见错误

请以专业、严谨的态度进行工作，并提供明确的建议。
输出必须是严格的JSON格式，不要添加任何额外的文字说明。
"""

    async def execute(self, context) -> Any:
        """
        执行智能体任务

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        # 验证输入
        if not self.validate_input(context):
            from core.agents.xiaona.base_component import AgentExecutionResult, AgentStatus
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message="输入验证失败",
            )

        # 根据任务类型执行相应的任务
        task_type = context.config.get("task_type", "comprehensive")

        try:
            if task_type == "analyze_disclosure":
                return await self.analyze_disclosure(context.input_data)
            elif task_type == "assess_patentability":
                return await self.assess_patentability(context.input_data)
            elif task_type == "draft_specification":
                return await self.draft_specification(context.input_data)
            elif task_type == "draft_claims":
                return await self.draft_claims(context.input_data)
            elif task_type == "optimize_protection_scope":
                return await self.optimize_protection_scope(context.input_data)
            elif task_type == "review_adequacy":
                return await self.review_adequacy(context.input_data)
            elif task_type == "detect_common_errors":
                return await self.detect_common_errors(context.input_data)
            else:
                # 完整撰写流程
                return await self.draft_patent_application(context.input_data)
        except Exception as e:
            self.logger.error(f"执行任务失败: {e}")
            from core.agents.xiaona.base_component import AgentExecutionResult, AgentStatus
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=str(e),
            )

    async def analyze_disclosure(
        self,
        disclosure_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析技术交底书

        Args:
            disclosure_data: 技术交底书数据

        Returns:
            交底书分析报告
        """
        try:
            prompt = self._build_disclosure_analysis_prompt(disclosure_data)
            response = await self._call_llm_with_fallback(
                prompt=prompt,
                task_type="analyze_disclosure"
            )

            # 解析LLM响应
            return self._parse_analysis_response(response)

        except Exception as e:
            self.logger.warning(f"LLM交底书分析失败: {e}，使用规则-based分析")
            return self._analyze_disclosure_by_rules(disclosure_data)

    def _analyze_disclosure_by_rules(
        self,
        disclosure_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        基于规则的交底书分析（降级方案）

        Args:
            disclosure_data: 技术交底书数据

        Returns:
            交底书分析报告
        """
        # 提取基本信息
        title = disclosure_data.get("title", "")
        technical_field = disclosure_data.get("technical_field", "")
        background_art = disclosure_data.get("background_art", "")
        invention_summary = disclosure_data.get("invention_summary", "")
        technical_problem = disclosure_data.get("technical_problem", "")
        technical_solution = disclosure_data.get("technical_solution", "")
        beneficial_effects = disclosure_data.get("beneficial_effects", "")

        # 完整性检查
        completeness = {
            "title": bool(title),
            "technical_field": bool(technical_field),
            "background_art": bool(background_art),
            "invention_summary": bool(invention_summary),
            "technical_problem": bool(technical_problem),
            "technical_solution": bool(technical_solution),
            "beneficial_effects": bool(beneficial_effects),
        }

        missing_fields = [
            field for field, complete in completeness.items()
            if not complete
        ]

        # 质量评估
        quality_score = sum(completeness.values()) / len(completeness)

        return {
            "disclosure_id": disclosure_data.get("disclosure_id", "未知"),
            "title": title,
            "completeness": completeness,
            "missing_fields": missing_fields,
            "quality_score": quality_score,
            "quality_level": self._get_quality_level(quality_score),
            "recommendations": self._generate_disclosure_recommendations(completeness),
            "analyzed_at": self._get_timestamp(),
        }

    async def assess_patentability(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        评估可专利性

        Args:
            data: 包含技术交底书和现有技术的数据

        Returns:
            可专利性评估报告
        """
        try:
            prompt = self._build_patentability_assessment_prompt(data)
            response = await self._call_llm_with_fallback(
                prompt=prompt,
                task_type="assess_patentability"
            )

            return self._parse_analysis_response(response)

        except Exception as e:
            self.logger.warning(f"LLM可专利性评估失败: {e}，使用规则-based评估")
            return self._assess_patentability_by_rules(data)

    def _assess_patentability_by_rules(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        基于规则的可专利性评估（降级方案）

        Args:
            data: 评估数据

        Returns:
            可专利性评估报告
        """
        disclosure = data.get("disclosure", {})
        prior_art = data.get("prior_art", [])

        # 简化版可专利性评估
        novelty_score = 0.7 if len(prior_art) < 5 else 0.5
        creativity_score = 0.7 if disclosure.get("technical_solution") else 0.4
        practicality_score = 0.8 if disclosure.get("beneficial_effects") else 0.6

        overall_score = (novelty_score + creativity_score + practicality_score) / 3

        return {
            "disclosure_id": disclosure.get("disclosure_id", "未知"),
            "novelty_assessment": {
                "score": novelty_score,
                "description": "新颖性评估",
            },
            "creativity_assessment": {
                "score": creativity_score,
                "description": "创造性评估",
            },
            "practicality_assessment": {
                "score": practicality_score,
                "description": "实用性评估",
            },
            "overall_score": overall_score,
            "patentability_level": self._get_quality_level(overall_score),
            "recommendations": ["建议进行现有技术检索"] if overall_score < 0.7 else [],
            "assessed_at": self._get_timestamp(),
        }

    async def draft_specification(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        撰写说明书

        Args:
            data: 包含技术交底书和可专利性评估的数据

        Returns:
            说明书草稿
        """
        try:
            prompt = self._build_specification_draft_prompt(data)
            response = await self._call_llm_with_fallback(
                prompt=prompt,
                task_type="draft_specification"
            )

            return {
                "specification_draft": response,
                "drafted_at": self._get_timestamp(),
            }

        except Exception as e:
            self.logger.error(f"说明书撰写失败: {e}")
            return {
                "specification_draft": "",
                "error": str(e),
                "drafted_at": self._get_timestamp(),
            }

    async def draft_claims(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        撰写权利要求书

        Args:
            data: 包含技术交底书和说明书的数据

        Returns:
            权利要求书草稿
        """
        try:
            prompt = self._build_claims_draft_prompt(data)
            response = await self._call_llm_with_fallback(
                prompt=prompt,
                task_type="draft_claims"
            )

            return {
                "claims_draft": response,
                "drafted_at": self._get_timestamp(),
            }

        except Exception as e:
            self.logger.error(f"权利要求书撰写失败: {e}")
            return {
                "claims_draft": "",
                "error": str(e),
                "drafted_at": self._get_timestamp(),
            }

    async def optimize_protection_scope(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        优化保护范围

        Args:
            data: 包含权利要求书和现有技术的数据

        Returns:
            优化建议
        """
        try:
            prompt = self._build_optimization_prompt(data)
            response = await self._call_llm_with_fallback(
                prompt=prompt,
                task_type="optimize_protection_scope"
            )

            return self._parse_analysis_response(response)

        except Exception as e:
            self.logger.error(f"保护范围优化失败: {e}")
            return {
                "optimization_suggestions": [],
                "error": str(e),
            }

    async def review_adequacy(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        审查充分公开

        Args:
            data: 包含说明书和权利要求书的数据

        Returns:
            充分公开审查报告
        """
        try:
            prompt = self._build_adequacy_review_prompt(data)
            response = await self._call_llm_with_fallback(
                prompt=prompt,
                task_type="review_adequacy"
            )

            return self._parse_analysis_response(response)

        except Exception as e:
            self.logger.error(f"充分公开审查失败: {e}")
            return {
                "adequacy_review": {},
                "error": str(e),
            }

    async def detect_common_errors(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        检测常见错误

        Args:
            data: 包含说明书和权利要求书的数据

        Returns:
            错误检测报告
        """
        try:
            prompt = self._build_error_detection_prompt(data)
            response = await self._call_llm_with_fallback(
                prompt=prompt,
                task_type="detect_common_errors"
            )

            return self._parse_analysis_response(response)

        except Exception as e:
            self.logger.error(f"常见错误检测失败: {e}")
            return {
                "detected_errors": [],
                "error": str(e),
            }

    async def draft_patent_application(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        完整专利申请撰写流程

        Args:
            data: 技术交底书数据

        Returns:
            完整的专利申请文件
        """
        # 1. 分析技术交底书
        disclosure_analysis = await self.analyze_disclosure(data)

        # 2. 评估可专利性
        patentability_assessment = await self.assess_patentability({
            "disclosure": data,
            "prior_art": data.get("prior_art", []),
        })

        # 3. 撰写说明书
        specification_result = await self.draft_specification({
            "disclosure": data,
            "patentability": patentability_assessment,
        })

        # 4. 撰写权利要求书
        claims_result = await self.draft_claims({
            "disclosure": data,
            "specification": specification_result.get("specification_draft", ""),
        })

        # 5. 审查充分公开
        adequacy_review = await self.review_adequacy({
            "specification": specification_result.get("specification_draft", ""),
            "claims": claims_result.get("claims_draft", ""),
        })

        # 6. 检测常见错误
        error_detection = await self.detect_common_errors({
            "specification": specification_result.get("specification_draft", ""),
            "claims": claims_result.get("claims_draft", ""),
        })

        return {
            "disclosure_analysis": disclosure_analysis,
            "patentability_assessment": patentability_assessment,
            "specification": specification_result,
            "claims": claims_result,
            "adequacy_review": adequacy_review,
            "error_detection": error_detection,
            "completed_at": self._get_timestamp(),
        }

    # ========== 辅助方法 ==========

    def _build_disclosure_analysis_prompt(self, disclosure_data: Dict[str, Any]) -> str:
        """构建交底书分析提示词"""
        return f"""# 任务：技术交底书分析

## 技术交底书内容
```json
{json.dumps(disclosure_data, ensure_ascii=False, indent=2)}
```

## 分析要点
1. **完整性**：是否包含所有必要信息
2. **清晰度**：技术描述是否清晰明确
3. **技术性**：是否包含充分的技术细节
4. **创新性**：是否体现技术创新点

## 输出要求
请严格按照以下JSON格式输出分析结果：

```json
{{
    "disclosure_id": "交底书ID",
    "title": "标题",
    "completeness": {{
        "title": true,
        "technical_field": true,
        "background_art": true,
        "invention_summary": true,
        "technical_problem": true,
        "technical_solution": true,
        "beneficial_effects": true
    }},
    "missing_fields": ["缺失的字段"],
    "quality_score": 0.8,
    "quality_level": "良好",
    "recommendations": ["建议1", "建议2"],
    "analyzed_at": "2026-04-23T10:00:00"
}}
```

请只输出JSON，不要添加任何额外说明。
"""

    def _build_patentability_assessment_prompt(self, data: Dict[str, Any]) -> str:
        """构建可专利性评估提示词"""
        return f"""# 任务：可专利性评估

## 技术交底书
```json
{json.dumps(data.get("disclosure", {}), ensure_ascii=False, indent=2)}
```

## 现有技术
参考文献数量：{len(data.get("prior_art", []))}篇

## 评估要点
1. **新颖性**：是否属于现有技术
2. **创造性**：是否具有突出的实质性特点和显著的进步
3. **实用性**：是否能够制造或使用并产生积极效果

## 输出要求
请严格按照以下JSON格式输出评估结果：

```json
{{
    "disclosure_id": "交底书ID",
    "novelty_assessment": {{
        "score": 0.7,
        "description": "新颖性评估说明"
    }},
    "creativity_assessment": {{
        "score": 0.8,
        "description": "创造性评估说明"
    }},
    "practicality_assessment": {{
        "score": 0.9,
        "description": "实用性评估说明"
    }},
    "overall_score": 0.8,
    "patentability_level": "良好",
    "recommendations": ["建议1", "建议2"],
    "assessed_at": "2026-04-23T10:00:00"
}}
```

请只输出JSON，不要添加任何额外说明。
"""

    def _build_specification_draft_prompt(self, data: Dict[str, Any]) -> str:
        """构建说明书撰写提示词"""
        disclosure = data.get("disclosure", {})
        return f"""# 任务：撰写专利说明书

## 技术交底书
```json
{json.dumps(disclosure, ensure_ascii=False, indent=2)}
```

## 撰写要求
1. **技术领域**：明确说明所属技术领域
2. **背景技术**：描述现有技术及其不足
3. **发明内容**：
   - 要解决的技术问题
   - 技术方案
   - 有益效果
4. **附图说明**：如果有附图，进行说明
5. **具体实施方式**：详细描述实现方式

## 输出要求
请撰写完整的说明书，使用标准的专利说明书格式和语言。
"""

    def _build_claims_draft_prompt(self, data: Dict[str, Any]) -> str:
        """构建权利要求书撰写提示词"""
        disclosure = data.get("disclosure", {})
        specification = data.get("specification", "")
        return f"""# 任务：撰写权利要求书

## 技术交底书
```json
{json.dumps(disclosure, ensure_ascii=False, indent=2)}
```

## 说明书（参考）
```
{specification[:1000]}...
```

## 撰写要求
1. **独立权利要求**：包含解决技术问题所必需的技术特征
2. **从属权利要求**：包含附加技术特征
3. **清晰明确**：使用准确的技术术语
4. **保护范围**：合理限定保护范围

## 输出要求
请撰写完整的权利要求书，使用标准的权利要求书格式。
建议至少包含1个独立权利要求和2-3个从属权利要求。
"""

    def _build_optimization_prompt(self, data: Dict[str, Any]) -> str:
        """构建保护范围优化提示词"""
        return f"""# 任务：优化权利要求保护范围

## 权利要求书
```
{data.get("claims", "")}
```

## 优化要点
1. **保护范围合理性**：是否过宽或过窄
2. **授权前景**：提高授权可能性的建议
3. **侵权可检测性**：便于后续维权
4. **层次化保护**：独立权利要求与从属权利要求的配合

## 输出要求
请提供具体的优化建议，以JSON格式输出。
"""

    def _build_adequacy_review_prompt(self, data: Dict[str, Any]) -> str:
        """构建充分公开审查提示词"""
        return f"""# 任务：审查说明书充分公开

## 说明书
```
{data.get("specification", "")[:1500]}
```

## 权利要求书
```
{data.get("claims", "")}
```

## 审查要点
1. **技术方案描述**：是否完整、清晰
2. **实施方式**：是否包含具体实施方式
3. **实现可能性**：本领域技术人员能否实现
4. **支持性**：说明书是否支持权利要求

## 输出要求
请提供详细的审查报告，以JSON格式输出。
"""

    def _build_error_detection_prompt(self, data: Dict[str, Any]) -> str:
        """构建常见错误检测提示词"""
        return f"""# 任务：检测专利申请文件常见错误

## 说明书
```
{data.get("specification", "")[:1000]}
```

## 权利要求书
```
{data.get("claims", "")}
```

## 检测要点
1. **格式错误**：是否符合规范格式
2. **术语不一致**：技术术语是否前后一致
3. **引用错误**：附图引用是否正确
4. **逻辑错误**：技术描述是否存在矛盾
5. **语言错误**：是否存在语法或表达错误

## 输出要求
请列出检测到的所有错误，以JSON格式输出。
"""

    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """解析LLM分析响应"""
        try:
            import re
            # 提取JSON
            json_match = re.search(r'```json\s*([\s\S]*?)```', response)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = response.strip()

            result = json.loads(json_str)
            return result

        except (json.JSONDecodeError, Exception) as e:
            self.logger.error(f"解析LLM响应失败: {e}")
            return {
                "error": "LLM响应解析失败",
                "raw_response": response,
            }

    def _get_quality_level(self, score: float) -> str:
        """获取质量等级"""
        if score >= 0.9:
            return "优秀"
        elif score >= 0.75:
            return "良好"
        elif score >= 0.6:
            return "合格"
        else:
            return "待改进"

    def _generate_disclosure_recommendations(
        self,
        completeness: Dict[str, bool]
    ) -> List[str]:
        """生成交底书改进建议"""
        recommendations = []

        field_names = {
            "title": "标题",
            "technical_field": "技术领域",
            "background_art": "背景技术",
            "invention_summary": "发明摘要",
            "technical_problem": "技术问题",
            "technical_solution": "技术方案",
            "beneficial_effects": "有益效果",
        }

        missing = [
            field_names[field]
            for field, complete in completeness.items()
            if not complete
        ]

        if missing:
            recommendations.append(f"补充缺失内容：{', '.join(missing)}")

        if not recommendations:
            recommendations.append("技术交底书内容完整，质量良好")

        return recommendations

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
