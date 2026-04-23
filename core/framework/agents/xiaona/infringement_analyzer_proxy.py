"""
侵权分析智能体

专注于专利侵权分析，提供全面的侵权风险评估。
"""

import json
import logging
import re
from typing import Any, Optional

from core.framework.agents.xiaona.base_component import BaseXiaonaComponent

logger = logging.getLogger(__name__)


class InfringementAnalyzerProxy(BaseXiaonaComponent):
    """
    侵权分析智能体

    核心能力：
    - 权利要求解释
    - 特征比对（全面原则、等同原则）
    - 侵权判定（直接侵权、间接侵权）
    - 风险评估和规避建议
    """

    def _initialize(self) -> str:
        """初始化侵权分析智能体"""
        self._register_capabilities([

            {
                "name": "claim_interpretation",
                "description": "权利要求解释",
                "input_types": ["专利文件"],
                "output_types": ["权利要求解释"],
                "estimated_time": 15.0,
            },
            {
                "name": "feature_comparison",
                "description": "特征比对",
                "input_types": ["权利要求", "产品描述"],
                "output_types": ["比对结果"],
                "estimated_time": 20.0,
            },
            {
                "name": "infringement_determination",
                "description": "侵权判定",
                "input_types": ["比对结果"],
                "output_types": ["侵权结论"],
                "estimated_time": 25.0,
            },
            {
                "name": "risk_assessment",
                "description": "风险评估",
                "input_types": ["侵权结果"],
                "output_types": ["风险报告"],
                "estimated_time": 10.0,
            },
        )

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """
你是一位专业的专利侵权分析专家，具备深厚的专利法知识和丰富的侵权判定经验。

你的职责是：
1. 解释权利要求保护范围
2. 将被诉产品/方法与权利要求进行特征比对
3. 判定是否构成侵权（全面原则、等同原则）
4. 评估侵权风险并提供规避建议

请以专业、严谨的态度进行侵权分析，并提供明确的法律依据。
输出必须是严格的JSON格式，不要添加任何额外的文字说明。
"""

    async def execute(self, context) -> str:
        """
        执行智能体任务

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        # 根据任务类型执行相应的分析
        task_type = context.config.get("task_type", "comprehensive")

        if task_type == "interpret_claims":
            return await self.interpret_claims(context.input_data)
        elif task_type == "compare_features":
            claims = context.input_data.get("claims", [])
            product = context.input_data.get("product", {})
            return await self.compare_features(claims, product)
        elif task_type == "determine_infringement":
            comparisons = context.input_data.get("comparisons", [])
            return await self.determine_infringement(comparisons)
        elif task_type == "assess_risk":
            infringement = context.input_data.get("infringement", {})
            claim_value = context.input_data.get("claim_value", 0)
            return await self.assess_risk(infringement, claim_value)
        else:
            # 完整侵权分析
            patent = context.input_data.get("patent_data", {})
            product = context.input_data.get("product_data", {})
            return await self.analyze_infringement(patent, product)

    async def analyze_infringement(
        self,
        patent_data: Optional[dict[str, Any],]

        product_data: Optional[dict[str, Any],]

        analysis_mode: str = "comprehensive"

    )]) -> dict[str, Any]:
        """
        完整侵权分析流程

        Args:
            patent_data: 目标专利数据
            product_data: 被诉产品/方法数据
            analysis_mode: 分析模式（comprehensive/quick）

        Returns:
            完整侵权分析报告
        """
        # 1. 解释权利要求
        claims = await self.interpret_claims(patent_data)

        # 2. 特征比对
        comparisons = await self.compare_features(
            claims.get("claims", []),
            product_data
        )

        # 3. 侵权判定
        infringement = await self.determine_infringement(
            comparisons.get("comparisons", [])
        )

        # 4. 风险评估
        risk = await self.assess_risk(
            infringement,
            patent_data.get("estimated_value", 0)
        )

        # 5. 生成报告
        return {
            "patent_id": patent_data.get("patent_id", "未知"),
            "product": product_data.get("product_name", "未知"),
            "analysis_mode": analysis_mode,
            "claims_analysis": claims,
            "feature_comparison": comparisons,
            "infringement_conclusion": infringement,
            "risk_assessment": risk,
            "generated_at": self._get_timestamp(),
        }

    async def interpret_claims(
        self,
        patent_data: Optional[[dict[str, Any]]]

    ) -> dict[str, Any]:
        """
        解释权利要求，确定保护范围（LLM版本）

        Args:
            patent_data: 专利数据

        Returns:
            权利要求解释结果
        """
        # 尝试使用LLM分析
        try:
            prompt = self._build_claim_interpretation_prompt(patent_data)
            response = await self._call_llm_with_fallback(
                prompt=prompt,
                task_type="claim_interpretation"
            )

            # 解析LLM响应
            return self._parse_claim_interpretation_response(response)
        except Exception as e:
            self.logger.warning(f"LLM权利要求解释失败: {e}，使用规则-based解释")
            return self._interpret_claims_by_rules(patent_data)

    def _interpret_claims_by_rules(
        self,
        patent_data: Optional[[dict[str, Any]]]

    ) -> dict[str, Any]:
        """
        基于规则的权利要求解释（降级方案）

        Args:
            patent_data: 专利数据

        Returns:
            权利要求解释结果
        """
        patent_id = patent_data.get("patent_id", "未知")
        claims_text = patent_data.get("claims", "")

        # 提取权利要求（简化版）
        claims_list = self._parse_claims(claims_text)

        # 分析每个权利要求
        interpreted_claims = []
        for claim in claims_list:
            interpreted = {
                "claim_number": claim.get("number", 0),
                "type": claim.get("type", "independent"),
                "text": claim.get("text", ""),
                "essential_features": self._extract_essential_features(
                    claim.get("text", "")
                ),
                "protection_scope": self._determine_protection_scope(
                    claim.get("text", "")
                ),
            }
            interpreted_claims.append(interpreted)

        return {
            "patent_id": patent_id,
            "total_claims": len(interpreted_claims),
            "independent_claims": len([c for c in interpreted_claims if c["type"] == "independent"]),
            "dependent_claims": len([c for c in interpreted_claims if c["type"] == "dependent"]),
            "claims": interpreted_claims,
        }

    def _build_claim_interpretation_prompt(self, patent_data: Optional[dict[str, Any])] -> str:
        """构建权利要求解释提示词"""
        patent_id = patent_data.get("patent_id", "未知")
        claims_text = patent_data.get("claims", "")
        specification = patent_data.get("specification", "")

        return f"""# 任务：专利权利要求解释

## 专利信息
专利号：{patent_id}

## 权利要求书
```
{claims_text}
```

## 说明书（用于理解技术方案）
```
{specification[:1000]}...
```

## 解释要点
1. **保护范围确定**：根据权利要求文字确定保护范围
2. **必要技术特征**：提取每个权利要求的必要技术特征
3. **独立/从属关系**：明确独立权利要求和从属权利要求的关系
4. **功能性限定**：识别功能性限定特征
5. **上位概念**：识别上位概念和概括性表述

## 输出要求
请严格按照以下JSON格式输出解释结果：

```json
{{
    "patent_id": "{patent_id}",
    "total_claims": 5,
    "independent_claims": 1,
    "dependent_claims": 4,
    "claims": []

        {{
            "claim_number": 1,
            "type": "independent",
            "text": "权利要求1的完整文本",
            "essential_features": []

                "必要技术特征1",
                "必要技术特征2",
                "必要技术特征3"
            ,
            "protection_scope": "较宽/中等/较窄",
            "interpretation_notes": "权利要求解释说明",
            "functional_features": ["功能性限定特征列表"],
            "broad_concepts": ["上位概念列表"]
        }}

}}
```

请只输出JSON，不要添加任何额外说明。
"""

    def _parse_claim_interpretation_response(self, response: str) -> dict[str, Any]:
        """解析权利要求解释LLM响应"""
        try:
            # 提取JSON
            json_match = re.search(r'```json\s*([\s\S]*?)```', response)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = response.strip()

            result = json.loads(json_str)

            # 验证必需字段
            required_fields = ["patent_id", "total_claims", "independent_claims",]

                             "dependent_claims", "claims"
            for field in required_fields:
                if field not in result:
                    result[field] = None

            return result

        except (json.JSONDecodeError, Exception) as e:
            self.logger.error(f"解析权利要求解释响应失败: {e}")
            # 返回默认响应
            return {
                "patent_id": "未知",
                "total_claims": 0,
                "independent_claims": 0,
                "dependent_claims": 0,
                "claims": Optional[[],]

            }

    async def compare_features(
        self,
        claims: Optional[[list[dict[str, Any]]],]

        product_description: Optional[[dict[str, Any]]]

    ) -> dict[str, Any]:
        """
        将产品/方法与权利要求比对（LLM版本）

        Args:
            claims: 权利要求列表
            product_description: 产品描述

        Returns:
            特征比对结果
        """
        # 尝试使用LLM分析
        try:
            prompt = self._build_feature_comparison_prompt(claims, product_description)
            response = await self._call_llm_with_fallback(
                prompt=prompt,
                task_type="feature_comparison"
            )

            # 解析LLM响应
            return self._parse_feature_comparison_response(response)
        except Exception as e:
            self.logger.warning(f"LLM特征比对失败: {e}，使用规则-based比对")
            return self._compare_features_by_rules(claims, product_description)

    def _compare_features_by_rules(
        self,
        claims: Optional[[list[dict[str, Any]]],]

        product_description: Optional[[dict[str, Any]]]

    ) -> dict[str, Any]:
        """
        基于规则的特征比对（降级方案）

        Args:
            claims: 权利要求列表
            product_description: 产品描述

        Returns:
            特征比对结果
        """
        product_features = product_description.get("features", {})
        product_name = product_description.get("product_name", "未知产品")

        comparisons = []
        for claim in claims:
            claim_number = claim["claim_number"]
            essential_features = claim.get("essential_features", [])

            # 全面原则比对（字面侵权）
            covered_features = []
            missing_features = []

            for feature in essential_features:
                if self._feature_covered(feature, product_features):
                    covered_features.append(feature)
                else:
                    missing_features.append(feature)

            # 等同原则比对
            equivalent_features = self._find_equivalent_features(
                missing_features,
                product_features
            )

            # 判定侵权类型
            if len(missing_features) == 0:
                infringement_type = "literal_infringement"
            elif len(equivalent_features) > 0:
                infringement_type = "equivalent_infringement"
            else:
                infringement_type = "no_infringement"

            comparison = {
                "claim_number": claim_number,
                "covered_features": covered_features,
                "missing_features": missing_features,
                "equivalent_features": equivalent_features,
                "infringement_type": infringement_type,
                "coverage_ratio": len(covered_features) / len(essential_features) if essential_features else 0,
            }
            comparisons.append(comparison)

        return {
            "product": product_name,
            "comparisons": comparisons,
            "summary": self._generate_comparison_summary(comparisons),
        }

    def _build_feature_comparison_prompt(
        self,
        claims: Optional[[list[dict[str, Any]]],]

        product_description: Optional[[dict[str, Any]]]

    ) -> str:
        """构建特征比对提示词"""
        product_name = product_description.get("product_name", "未知产品")
        product_features = product_description.get("features", {})

        return f"""# 任务：专利权利要求与产品特征比对

## 产品信息
产品名称：{product_name}

## 产品技术特征
```json
{json.dumps(product_features, ensure_ascii=False, indent=2)}
```

## 权利要求信息
```json
{json.dumps(claims, ensure_ascii=False, indent=2)}
```

## 比对要点
1. **全面原则（字面侵权）**：
   - 被诉产品/方法是否包含了权利要求中的全部必要技术特征
   - 如果缺少任何一个特征，则不构成字面侵权

2. **等同原则（等同侵权）**：
   - 缺失的特征是否在被诉产品/方法中以等同的方式实现
   - 等同特征判断标准：
     a) 基本相同的手段
     b) 基本相同的功能
     c) 达到基本相同的效果
     d) 本领域普通技术人员无需经过创造性劳动就能联想到

3. **特征覆盖度**：计算被覆盖特征的比例

## 输出要求
请严格按照以下JSON格式输出比对结果：

```json
{{
    "product": "{product_name}",
    "comparisons": []

        {{
            "claim_number": 1,
            "covered_features": ["被覆盖的特征1", "被覆盖的特征2"],
            "missing_features": ["缺失的特征"],
            "equivalent_features": ["等同特征说明"],
            "infringement_type": "literal_infringement/equivalent_infringement/no_infringement",
            "coverage_ratio": 0.67,
            "analysis": "详细分析说明"
        }}
    ,
    "summary": {{
        "total_claims_compared": 5,
        "literal_infringement": 2,
        "equivalent_infringement": 1,
        "no_infringement": 2,
        "average_coverage_ratio": 0.6
    }}
}}
```

请只输出JSON，不要添加任何额外说明。
"""

    def _parse_feature_comparison_response(self, response: str) -> dict[str, Any]:
        """解析特征比对LLM响应"""
        try:
            # 提取JSON
            json_match = re.search(r'```json\s*([\s\S]*?)```', response)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = response.strip()

            result = json.loads(json_str)

            # 验证必需字段
            if "product" not in result:
                result["product"] = "未知产品"
            if "comparisons" not in result:
                result["comparisons"]] = []
            if "summary" not in result:
                result["summary"]] = {}

            return result

        except (json.JSONDecodeError, Exception) as e:
            self.logger.error(f"解析特征比对响应失败: {e}")
            return {
                "product": "未知产品",
                "comparisons": Optional[[],]

                "summary": {},
            }

    async def determine_infringement(
        self,
        comparisons: Optional[[list[dict[str, Any]]]
    ) -> dict[str, Any]:
        """
        判定是否侵权（全面原则、等同原则）（LLM版本）

        Args:
            comparisons: 特征比对结果

        Returns:
            侵权判定结论
        """
        # 尝试使用LLM分析
        try:
            prompt = self._build_infringement_determination_prompt(comparisons)
            response = await self._call_llm_with_fallback(
                prompt=prompt,
                task_type="infringement_determination"
            )

            # 解析LLM响应
            return self._parse_infringement_determination_response(response)
        except Exception as e:
            self.logger.warning(f"LLM侵权判定失败: {e}，使用规则-based判定")
            return self._determine_infringement_by_rules(comparisons)

    def _determine_infringement_by_rules(
        self,
        comparisons: Optional[[list[dict[str, Any]]]
    ) -> dict[str, Any]:
        """
        基于规则的侵权判定（降级方案）

        Args:
            comparisons: 特征比对结果

        Returns:
            侵权判定结论
        """
        # 统计侵权情况
        literal_infringed = []
        equivalent_infringed = []
        non_infringed = []

        for comp in comparisons:
            claim_number = comp["claim_number"]
            infringement_type = comp["infringement_type"]

            if infringement_type == "literal_infringement":
                literal_infringed.append(claim_number)
            elif infringement_type == "equivalent_infringement":
                equivalent_infringed.append(claim_number)
            else:
                non_infringed.append(claim_number)

        # 判定侵权结论
        total_infringed = len(literal_infringed) + len(equivalent_infringed)
        total_claims = len(comparisons)

        if total_infringed == 0:
            conclusion = "不构成侵权"
            confidence = 0.9
        elif len(literal_infringed) > 0:
            conclusion = "构成字面侵权"
            confidence = 0.85 + (0.1 * len(literal_infringed) / total_claims)
        else:
            conclusion = "构成等同侵权"
            confidence = 0.7 + (0.1 * len(equivalent_infringed) / total_claims)

        # 限制置信度范围
        confidence = min(max(confidence, 0.5), 0.95)

        return {
            "infringement_conclusion": conclusion,
            "infringed_claims": {
                "literal": literal_infringed,
                "equivalent": equivalent_infringed,
                "total": total_infringed,
            },
            "non_infringed_claims": non_infringed,
            "legal_basis": self._get_legal_basis(literal_infringed, equivalent_infringed),
            "confidence": confidence,
            "reasoning": self._generate_infringement_reasoning(comparisons),
        }

    def _build_infringement_determination_prompt(
        self,
        comparisons: Optional[[list[dict[str, Any]]]
    ) -> str:
        """构建侵权判定提示词"""
        return f"""# 任务：专利侵权判定

## 特征比对结果
```json
{json.dumps(comparisons, ensure_ascii=False, indent=2)}
```

## 判定要点
1. **全面原则（字面侵权）**：
   - 专利法第11条：发明和实用新型专利权被授予后，除本法另有规定的以外，任何单位或者个人未经专利权人许可，都不得实施其专利
   - 字面侵权：被诉侵权技术方案包含了权利要求记载的全部必要技术特征

2. **等同原则（等同侵权）**：
   - 最高人民法院《关于审理专利纠纷案件应用法律问题的若干规定》第17条
   - 等同特征：手段、功能、效果基本相同，且本领域普通技术人员无需经过创造性劳动就能够联想到
   - 显著进步的等同特征仍可能构成侵权

3. **侵权判定标准**：
   - 独立权利要求侵权是关键
   - 从属权利要求侵权作为补充
   - 需要考虑现有技术抗辩

4. **置信度评估**：
   - 字面侵权：置信度 > 0.85
   - 等同侵权：置信度 0.7-0.85
   - 不侵权：置信度 > 0.9

## 输出要求
请严格按照以下JSON格式输出侵权判定结果：

```json
{{
    "infringement_conclusion": "构成字面侵权/构成等同侵权/不构成侵权",
    "infringed_claims": {{
        "literal": Optional[[1, 2],]

        "equivalent": Optional[[3],]

        "total": 3
    }},
    "non_infringed_claims": Optional[[4, 5],]

    "legal_basis": "专利法第11条（全面原则、等同原则）",
    "confidence": 0.85,
    "reasoning": "详细的侵权判定推理过程，包括每个权利要求的分析"
}}
```

请只输出JSON，不要添加任何额外说明。
"""

    def _parse_infringement_determination_response(self, response: str) -> dict[str, Any]:
        """解析侵权判定LLM响应"""
        try:
            # 提取JSON
            json_match = re.search(r'```json\s*([\s\S]*?)```', response)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = response.strip()

            result = json.loads(json_str)

            # 验证必需字段
            required_fields = ["infringement_conclusion", "infringed_claims",]

                             "non_infringed_claims", "legal_basis", "confidence", "reasoning"
            for field in required_fields:
                if field not in result:
                    if field == "infringement_conclusion":
                        result[field] = "无法判定"
                    elif field == "infringed_claims":
                        result[field]] = {"literal": Optional[[], "equivalent": Optional[[], "total": 0}]]

                    elif field == "non_infringed_claims":
                        result[field]] = []
                    elif field == "legal_basis":
                        result[field] = "专利法第11条"
                    elif field == "confidence":
                        result[field] = 0.5
                    elif field == "reasoning":
                        result[field] = "LLM响应不完整"

            return result

        except (json.JSONDecodeError, Exception) as e:
            self.logger.error(f"解析侵权判定响应失败: {e}")
            return {
                "infringement_conclusion": "无法判定",
                "infringed_claims": {"literal": Optional[[], "equivalent": Optional[[], "total": 0},]]

                "non_infringed_claims": Optional[[],]

                "legal_basis": "专利法第11条",
                "confidence": 0.5,
                "reasoning": "LLM响应解析失败",
            }

    async def assess_risk(
        self,
        infringement_result: Optional[dict[str, Any],]

        claim_value: float
    ) -> dict[str, Any]:
        """
        评估侵权风险和赔偿（LLM版本）

        Args:
            infringement_result: 侵权判定结果
            claim_value: 专利价值/索赔金额

        Returns:
            风险评估报告
        """
        # 尝试使用LLM分析
        try:
            prompt = self._build_risk_assessment_prompt(infringement_result, claim_value)
            response = await self._call_llm_with_fallback(
                prompt=prompt,
                task_type="risk_assessment"
            )

            # 解析LLM响应
            return self._parse_risk_assessment_response(response)
        except Exception as e:
            self.logger.warning(f"LLM风险评估失败: {e}，使用规则-based评估")
            return self._assess_risk_by_rules(infringement_result, claim_value)

    def _assess_risk_by_rules(
        self,
        infringement_result: Optional[dict[str, Any],]

        claim_value: float
    ) -> dict[str, Any]:
        """
        基于规则的风险评估（降级方案）

        Args:
            infringement_result: 侵权判定结果
            claim_value: 专利价值/索赔金额

        Returns:
            风险评估报告
        """
        conclusion = infringement_result.get("infringement_conclusion", "")
        confidence = infringement_result.get("confidence", 0)
        infringement_result.get("infringed_claims", {}).get("total", 0)

        # 风险等级判定
        if "不构成侵权" in conclusion:
            risk_level = "low"
            estimated_damages = 0
            injunctive_relief_risk = 0.1
        elif "字面侵权" in conclusion and confidence > 0.8:
            risk_level = "high"
            estimated_damages = claim_value * 0.5  # 估算为专利价值的50%
            injunctive_relief_risk = 0.9
        elif "等同侵权" in conclusion:
            risk_level = "medium"
            estimated_damages = claim_value * 0.3  # 估算为专利价值的30%
            injunctive_relief_risk = 0.6
        else:
            risk_level = "medium"
            estimated_damages = claim_value * 0.2
            injunctive_relief_risk = 0.5

        # 规避设计建议
        design_around_suggestions = []
        if risk_level in ["high", "medium"]:
            design_around_suggestions = []

                "修改被控侵权产品的技术特征，使其不完全落入权利要求保护范围",
                "通过技术改进，实现与专利不同的技术方案",
                "寻求专利无效宣告或专利权评价",
                "评估许可谈判的可行性",


        return {
            "risk_level": risk_level,
            "estimated_damages": int(estimated_damages),
            "injunctive_relief_risk": injunctive_relief_risk,
            "litigation_risk": "high" if risk_level == "high" else "medium",
            "design_around_suggestions": design_around_suggestions,
            "recommended_actions": self._generate_action_recommendations(risk_level),
        }

    def _build_risk_assessment_prompt(
        self,
        infringement_result: Optional[dict[str, Any],]

        claim_value: float
    ) -> str:
        """构建风险评估提示词"""
        return f"""# 任务：专利侵权风险评估

## 侵权判定结果
```json
{json.dumps(infringement_result, ensure_ascii=False, indent=2)}
```

## 专利价值/索赔金额
{claim_value} 元

## 风险评估要点
1. **风险等级判定**：
   - 高风险：字面侵权且置信度 > 0.8
   - 中风险：等同侵权或字面侵权但置信度较低
   - 低风险：不构成侵权

2. **损害赔偿估算**：
   - 考虑因素：专利价值、侵权类型、市场影响
   - 计算方式：专利价值 × 风险系数

3. **禁令风险评估**：
   - 字面侵权：禁令风险 > 0.8
   - 等同侵权：禁令风险 0.5-0.7
   - 不侵权：禁令风险 < 0.2

4. **规避设计建议**：
   - 技术方案改进
   - 专利无效宣告
   - 许可谈判
   - 现有技术抗辩

5. **推荐行动**：
   - 立即停止侵权（高风险）
   - 准备规避设计（中风险）
   - 继续监控（低风险）

## 输出要求
请严格按照以下JSON格式输出风险评估结果：

```json
{{
    "risk_level": "high/medium/low",
    "estimated_damages": 500000,
    "injunctive_relief_risk": 0.85,
    "litigation_risk": "high/medium/low",
    "design_around_suggestions": []

        "规避设计建议1",
        "规避设计建议2"
    ,
    "recommended_actions": []

        "推荐行动1",
        "推荐行动2"
    ,
    "risk_analysis": "详细的风险分析说明"
}}
```

请只输出JSON，不要添加任何额外说明。
"""

    def _parse_risk_assessment_response(self, response: str) -> dict[str, Any]:
        """解析风险评估LLM响应"""
        try:
            # 提取JSON
            json_match = re.search(r'```json\s*([\s\S]*?)```', response)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = response.strip()

            result = json.loads(json_str)

            # 验证必需字段
            required_fields = ["risk_level", "estimated_damages", "injunctive_relief_risk",]

                             "litigation_risk", "design_around_suggestions", "recommended_actions"
            for field in required_fields:
                if field not in result:
                    if field == "risk_level":
                        result[field] = "medium"
                    elif field == "estimated_damages":
                        result[field] = 0
                    elif field == "injunctive_relief_risk":
                        result[field] = 0.5
                    elif field == "litigation_risk":
                        result[field] = "medium"
                    elif field == "design_around_suggestions":
                        result[field]] = []
                    elif field == "recommended_actions":
                        result[field]] = []

            return result

        except (json.JSONDecodeError, Exception) as e:
            self.logger.error(f"解析风险评估响应失败: {e}")
            return {
                "risk_level": "medium",
                "estimated_damages": 0,
                "injunctive_relief_risk": 0.5,
                "litigation_risk": "medium",
                "design_around_suggestions": Optional[[],]

                "recommended_actions": Optional[[],]

            }

    # 辅助方法

    def _parse_claims(self, claims_text: str) -> list[str, Any]:
        """解析权利要求文本"""
        # 简化版解析，实际应该使用更复杂的NLP
        claims = []
        lines = claims_text.split("\n")

        current_claim = None
        current_claim_number = 0  # 使用单独的计数器

        for _i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            # 检查是否是新权利要求（支持多种格式）
            # 使用正则表达式匹配数字开头
            import re
            match = re.match(r'^(\d+)[\.\、、]', line)
            is_new_claim = match is not None

            if is_new_claim and match:
                # 新权利要求
                if current_claim:
                    claims.append(current_claim)

                current_claim_number = int(match.group(1))

                # 判断是独立权利要求还是从属权利要求
                # 从属权利要求通常包含"根据权利要求X"、"所述"等关键词
                is_dependent = (
                    "根据权利要求" in line or
                    ("所述" in line and current_claim_number > 1)
                )

                current_claim = {
                    "number": current_claim_number,
                    "type": "dependent" if is_dependent else "independent",
                    "text": line,
                }
            elif current_claim:
                current_claim["text"] += " " + line

        if current_claim:
            claims.append(current_claim)

        return claims if claims else []

            {"number": 1, "type": "independent", "text": claims_text}


    def _extract_essential_features(
        self,
        claim_text: str
    ) -> list[str]:
        """提取必要技术特征"""
        # 简化版特征提取
        features = []

        # 查找常见特征关键词
        keywords = ["包括", "包含", "具有", "设置", "配置"]
        for keyword in keywords:
            if keyword in claim_text:
                # 提取包含关键词的句子
                sentences = claim_text.split("，")
                for sentence in sentences:
                    if keyword in sentence:
                        features.append(sentence.strip())

        return features if features else ["特征1", "特征2", "特征3"]

    def _determine_protection_scope(self, claim_text: str) -> str:
        """确定保护范围"""
        # 简化版保护范围判定
        if "所述" in claim_text or "其特征在于" in claim_text:
            return "中等"
        elif len(claim_text) > 200:
            return "较宽"
        else:
            return "较窄"

    def _feature_covered(
        self,
        feature: str,
        product_features: Optional[[dict[str, Any]]]

    ) -> str:
        """判断特征是否被覆盖"""
        # 简化版判断
        feature_lower = feature.lower()

        # 检查产品特征中是否包含
        for _key, value in product_features.items():
            if isinstance(value, str):
                if feature_lower in value.lower():
                    return True
            elif isinstance(value, list):
                for item in value:
                    if feature_lower in str(item).lower():
                        return True

        return False

    def _find_equivalent_features(
        self,
        missing_features: Optional[list[str],]

        product_features: Optional[[dict[str, Any]]]

    ) -> list[str]:
        """查找等同特征"""
        # 简化版等同特征判定
        equivalent = []

        for feature in missing_features:
            # 检查是否有相似的特征
            for _key, value in product_features.items():
                if isinstance(value, str) and self._is_equivalent(feature, value):
                    equivalent.append(f"{feature} ≈ {value}")
                    break

        return equivalent

    def _is_equivalent(self, feature1: str, feature2: str) -> str:
        """判断两个特征是否等同"""
        # 简化版等同判定
        # 实际应该使用语义相似度
        synonyms_map = {
            "包括": "包含",
            "设置": "配置",
            "连接": "联接",
        }

        for word, synonym in synonyms_map.items():
            if word in feature1 and synonym in feature2:
                return True
            if synonym in feature1 and word in feature2:
                return True

        return False

    def _generate_comparison_summary(
        self,
        comparisons: Optional[[list[dict[str, Any]]]
    ) -> dict[str, Any]:
        """生成比对摘要"""
        total = len(comparisons)
        literal = len([c for c in comparisons if c["infringement_type"] == "literal_infringement"])
        equivalent = len([c for c in comparisons if c["infringement_type"] == "equivalent_infringement"])
        no_infringement = len([c for c in comparisons if c["infringement_type"] == "no_infringement"])

        avg_coverage = sum(c["coverage_ratio"] for c in comparisons) / total if total > 0 else 0

        return {
            "total_claims_compared": total,
            "literal_infringement": literal,
            "equivalent_infringement": equivalent,
            "no_infringement": no_infringement,
            "average_coverage_ratio": avg_coverage,
        }

    def _get_legal_basis(
        self,
        literal_claims: Optional[list[int],]

        equivalent_claims: Optional[[list[int]]]

    ) -> str:
        """获取法律依据"""
        if literal_claims and equivalent_claims:
            return "专利法第11条（全面原则、等同原则）"
        elif literal_claims:
            return "专利法第11条（全面原则）"
        elif equivalent_claims:
            return "专利法第11条（等同原则）"
        else:
            return "不适用"

    def _generate_infringement_reasoning(
        self,
        comparisons: Optional[[list[dict[str, Any]]]
    ) -> str:
        """生成侵权判定推理"""
        reasoning_parts = []

        for comp in comparisons:
            claim_num = comp["claim_number"]
            infringement_type = comp["infringement_type"]
            covered = len(comp.get("covered_features", []))
            missing = len(comp.get("missing_features", []))
            total = covered + missing

            if infringement_type == "literal_infringement":
                reasoning_parts.append(
                    f"权利要求{claim_num}：{covered}/{total}个特征被覆盖，构成字面侵权"
                )
            elif infringement_type == "equivalent_infringement":
                reasoning_parts.append(
                    f"权利要求{claim_num}：部分特征等同，构成等同侵权"
                )
            else:
                reasoning_parts.append(
                    f"权利要求{claim_num}：特征不匹配，不构成侵权"
                )

        return "；".join(reasoning_parts) if reasoning_parts else "无详细推理"

    def _generate_action_recommendations(
        self,
        risk_level: str
    ) -> list[str]:
        """生成行动建议"""
        if risk_level == "high":
            return []

                "立即停止涉嫌侵权行为",
                "寻求专业律师意见",
                "考虑与专利权人协商许可",
                "评估无效宣告的可能性",

        elif risk_level == "medium":
            return []

                "继续监控市场动态",
                "准备规避设计方案",
                "收集不侵权证据",
                "评估许可谈判的可行性",

        else:
            return []

                "继续现有业务",
                "定期更新技术方案",
                "关注专利法律动态",


    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
