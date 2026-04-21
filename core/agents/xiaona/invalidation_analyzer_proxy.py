"""
无效宣告分析智能体

专注于专利无效宣告分析，提供全面的无效理由分析和证据搜集策略。
"""

from typing import Any, Dict, List
import logging
import re
from core.agents.xiaona.base_component import BaseXiaonaComponent

logger = logging.getLogger(__name__)

# 常量定义
HIGH_STRENGTH_CONFIDENCE = 0.8
MEDIUM_STRENGTH_CONFIDENCE = 0.6
HIGH_SUCCESS_PROBABILITY = 0.8
MEDIUM_SUCCESS_PROBABILITY = 0.6
LOW_SUCCESS_PROBABILITY = 0.4
MIN_PROBABILITY = 0.1
MAX_PROBABILITY = 0.95
EVIDENCE_BONUS_THRESHOLD = 3
EVIDENCE_BONUS = 0.05

# 正则表达式预编译（性能优化）
CHINESE_WORD_PATTERN = re.compile(r'[\u4e00-\u9fa5]{2,8}')


class InvalidationAnalyzerProxy(BaseXiaonaComponent):
    """
    无效宣告分析智能体

    核心能力：
    - 无效理由分析（新颖性、创造性、公开不充分、修改超范围）
    - 证据搜集策略制定
    - 成功概率评估
    - 无效请求书撰写支持
    """

    def _initialize(self) -> None:
        """初始化无效宣告分析智能体"""
        self._register_capabilities([
            {
                "name": "invalidation_ground_analysis",
                "description": "无效理由分析",
                "input_types": ["目标专利", "对比文件"],
                "output_types": ["无效理由分析报告"],
                "estimated_time": 30.0,
            },
            {
                "name": "evidence_collection_strategy",
                "description": "证据搜集策略",
                "input_types": ["无效理由"],
                "output_types": ["证据搜集计划"],
                "estimated_time": 20.0,
            },
            {
                "name": "success_probability_assessment",
                "description": "成功概率评估",
                "input_types": ["无效理由", "证据"],
                "output_types": ["成功概率报告"],
                "estimated_time": 15.0,
            },
            {
                "name": "invalidation_petition_support",
                "description": "无效请求书撰写支持",
                "input_types": ["无效理由", "证据"],
                "output_types": ["无效请求书草稿"],
                "estimated_time": 40.0,
            },
        ])

    async def analyze_invalidation(
        self,
        target_patent: Dict[str, Any],
        prior_art_references: List[Dict[str, Any]],
        analysis_depth: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        完整无效宣告分析流程

        Args:
            target_patent: 目标专利数据
            prior_art_references: 对比文件列表
            analysis_depth: 分析深度

        Returns:
            完整无效宣告分析报告
        """
        patent_id = target_patent.get("patent_id", "未知")
        logger.info(f"开始无效宣告分析: {patent_id}, 深度: {analysis_depth}")

        # 1. 无效理由分析
        grounds_analysis = await self.analyze_invalidation_grounds(
            target_patent,
            prior_art_references
        )
        logger.debug(f"找到{len(grounds_analysis.get('valid_grounds', []))}个有效无效理由")

        # 2. 证据搜集策略
        evidence_strategy = await self.develop_evidence_strategy(
            grounds_analysis.get("valid_grounds", []),
            prior_art_references
        )
        logger.debug(f"制定证据搜集策略: {len(evidence_strategy.get('collection_plan', []))}个搜集计划")

        # 3. 成功概率评估
        probability_assessment = await self.assess_success_probability(
            grounds_analysis,
            evidence_strategy
        )
        prob = probability_assessment.get("overall_probability", 0)
        logger.info(f"成功概率评估完成: {prob:.1%}")

        # 4. 无效请求书撰写支持
        petition_support = await self.generate_invalidation_petition(
            target_patent,
            grounds_analysis,
            evidence_strategy,
            probability_assessment
        )
        logger.info(f"无效宣告分析完成: {patent_id}")

        return {
            "target_patent": {
                "patent_id": target_patent.get("patent_id", "未知"),
                "title": target_patent.get("title", ""),
                "grant_date": target_patent.get("grant_date", ""),
            },
            "analysis_depth": analysis_depth,
            "invalidation_grounds_analysis": grounds_analysis,
            "evidence_strategy": evidence_strategy,
            "success_probability": probability_assessment,
            "petition_support": petition_support,
            "overall_recommendation": self._generate_overall_recommendation(
                probability_assessment
            ),
            "analyzed_at": self._get_timestamp(),
        }

    async def analyze_invalidation_grounds(
        self,
        patent: Dict[str, Any],
        references: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析无效理由

        Args:
            patent: 目标专利
            references: 对比文件

        Returns:
            无效理由分析结果
        """
        valid_grounds = []

        # 1. 新颖性分析
        novelty_ground = await self._analyze_novelty_ground(
            patent,
            references
        )
        if novelty_ground["is_valid_ground"]:
            valid_grounds.append({
                "ground_type": "lack_of_novelty",
                "description": "不具备新颖性",
                "analysis": novelty_ground,
            })

        # 2. 创造性分析
        creativity_ground = await self._analyze_creativity_ground(
            patent,
            references
        )
        if creativity_ground["is_valid_ground"]:
            valid_grounds.append({
                "ground_type": "lack_of_creativity",
                "description": "不具备创造性",
                "analysis": creativity_ground,
            })

        # 3. 公开不充分分析
        disclosure_ground = await self._analyze_insufficient_disclosure(
            patent
        )
        if disclosure_ground["is_valid_ground"]:
            valid_grounds.append({
                "ground_type": "insufficient_disclosure",
                "description": "说明书公开不充分",
                "analysis": disclosure_ground,
            })

        # 4. 修改超范围分析
        amendment_ground = await self._analyze_amendment_exceeds_scope(
            patent
        )
        if amendment_ground["is_valid_ground"]:
            valid_grounds.append({
                "ground_type": "amendment_exceeds_scope",
                "description": "修改超出原申请文件记载的范围",
                "analysis": amendment_ground,
            })

        # 评估理由强度
        ground_strengths = []
        for ground in valid_grounds:
            strength = self._assess_ground_strength(ground)
            ground["strength"] = strength
            ground_strengths.append({
                "type": ground["ground_type"],
                "strength": strength,
                "confidence": ground["analysis"].get("confidence", 0.5)
            })

        return {
            "valid_grounds": valid_grounds,
            "total_grounds": len(valid_grounds),
            "ground_strengths": ground_strengths,
            "recommended_grounds": self._select_best_grounds(valid_grounds),
        }

    async def develop_evidence_strategy(
        self,
        valid_grounds: List[str],
        _existing_references: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        制定证据搜集策略

        Args:
            valid_grounds: 有效无效理由列表
            _existing_references: 现有对比文件（保留用于未来扩展）

        Returns:
            证据搜集策略
        """
        strategy = {
            "evidence_categories": [],
            "collection_plan": [],
            "priority_list": [],
        }

        # 根据无效理由制定证据搜集策略
        for ground_type in valid_grounds:
            if ground_type == "lack_of_novelty":
                strategy["evidence_categories"].append({
                    "category": "对比文件",
                    "description": "能够破坏新颖性的对比文件",
                    "sources": [
                        "中国专利申请",
                        "外国专利文献",
                        "非专利文献（书籍、论文）",
                        "公开使用（产品、展览）"
                    ],
                    "search_keywords": self._generate_search_keywords(ground_type),
                })
            elif ground_type == "lack_of_creativity":
                strategy["evidence_categories"].append({
                    "category": "结合启示",
                    "description": "现有技术的结合启示",
                    "sources": [
                        "教科书",
                        "技术手册",
                        "技术综述",
                        "多篇对比文件的组合"
                    ],
                    "search_keywords": self._generate_search_keywords(ground_type),
                })
            elif ground_type == "insufficient_disclosure":
                strategy["evidence_categories"].append({
                    "category": "技术词典",
                    "description": "证明所属领域技术常识的资料",
                    "sources": [
                        "技术标准",
                        "技术词典",
                        "教科书"
                    ],
                    "search_keywords": self._generate_search_keywords(ground_type),
                })

        # 制定搜集计划
        for i, category in enumerate(strategy["evidence_categories"]):
            plan_item = {
                "priority": i + 1,
                "category": category["category"],
                "actions": []
            }

            for source in category["sources"]:
                plan_item["actions"].append({
                    "source": source,
                    "estimated_time": "3-5天",
                    "responsible": "检索者"
                })

            strategy["collection_plan"].append(plan_item)

        # 优先级列表
        strategy["priority_list"] = [
            {
                "ground": g,
                "priority": "high" if i == 0 else "medium"
            }
            for i, g in enumerate(valid_grounds)
        ]

        return strategy

    async def assess_success_probability(
        self,
        grounds_analysis: Dict,
        evidence_strategy: Dict
    ) -> Dict[str, Any]:
        """
        评估成功概率

        Args:
            grounds_analysis: 无效理由分析结果
            evidence_strategy: 证据搜集策略

        Returns:
            成功概率评估报告
        """
        ground_strengths = grounds_analysis.get("ground_strengths", [])

        # 计算综合成功概率
        if not ground_strengths:
            return {
                "overall_probability": 0.0,
                "confidence": "low",
                "reasoning": "未找到有效无效理由"
            }

        # 基于理由强度评估概率
        high_strength_count = len([
            g for g in ground_strengths
            if g["strength"] == "strong"
        ])
        medium_strength_count = len([
            g for g in ground_strengths
            if g["strength"] == "moderate"
        ])

        # 成功概率计算
        if high_strength_count >= 2:
            overall_probability = 0.85
            confidence = "high"
        elif high_strength_count >= 1 and medium_strength_count >= 1:
            overall_probability = 0.70
            confidence = "medium"
        elif high_strength_count >= 1:
            overall_probability = 0.55
            confidence = "low"
        else:
            overall_probability = 0.35
            confidence = "low"

        # 考虑证据因素
        evidence_availability = len(evidence_strategy.get("collection_plan", []))
        if evidence_availability >= EVIDENCE_BONUS_THRESHOLD:
            overall_probability += EVIDENCE_BONUS  # 证据充分，概率略增

        # 限制概率范围
        overall_probability = min(max(overall_probability, MIN_PROBABILITY), MAX_PROBABILITY)

        # 生成预测
        prediction = self._generate_outcome_prediction(
            overall_probability,
            ground_strengths
        )

        return {
            "overall_probability": overall_probability,
            "confidence": confidence,
            "probability_breakdown": {
                "ground_strength": self._calculate_ground_strength_score(ground_strengths),
                "evidence_quality": self._assess_evidence_quality(evidence_strategy),
                "legal_basis": 0.8,  # 法律依据充分性
            },
            "prediction": prediction,
            "risk_factors": self._identify_risk_factors(ground_strengths),
            "recommended_strategy": self._generate_strategy_recommendation(
                overall_probability,
                ground_strengths
            ),
        }

    async def generate_invalidation_petition(
        self,
        patent: Dict[str, Any],
        grounds_analysis: Dict,
        evidence_strategy: Dict,
        probability_assessment: Dict
    ) -> Dict[str, Any]:
        """
        生成无效请求书草稿

        Args:
            patent: 目标专利（用于提取patent_id等信息）
            grounds_analysis: 无效理由分析
            evidence_strategy: 证据策略
            probability_assessment: 成功概率

        Returns:
            无效请求书草稿
        """
        # 选择最佳无效理由
        recommended_grounds = grounds_analysis.get("recommended_grounds", [])

        # 生成请求书结构
        petition_structure = {
            "title": f"专利无效宣告请求书（{patent.get('patent_id')}）",
            "sections": []
        }

        # 1. 请求人信息部分
        petition_structure["sections"].append({
            "section": "请求人信息",
            "content": {
                "name": "请求人姓名",
                "address": "请求人地址",
                "attorney": "代理律师（如有）"
            }
        })

        # 2. 专利基本信息
        petition_structure["sections"].append({
            "section": "专利基本信息",
            "content": {
                "patent_id": patent.get("patent_id"),
                "title": patent.get("title"),
                "grant_date": patent.get("grant_date"),
                "patent_owner": patent.get("patentee", ""),
            }
        })

        # 3. 无效理由
        petition_structure["sections"].append({
            "section": "无效理由及事实证据",
            "content": {
                "grounds": [
                    {
                        "ground_type": g["ground_type"],
                        "description": g["description"],
                        "detailed_reasoning": g["analysis"].get("detailed_reasoning", ""),
                        "evidence_references": []
                    }
                    for g in recommended_grounds
                ]
            }
        })

        # 4. 法律依据
        petition_structure["sections"].append({
            "section": "法律依据",
            "content": {
                "statutes": [
                    "专利法第22条第1款",
                    "专利法实施细则第65条第1款"
                ],
                "legal_reasoning": self._generate_legal_reasoning(recommended_grounds)
            }
        })

        # 5. 具体理由阐述
        petition_structure["sections"].append({
            "section": "具体理由阐述",
            "content": {
                "argument_1": self._generate_argument_1(recommended_grounds),
                "argument_2": self._generate_argument_2(recommended_grounds),
                "conclusion": self._generate_conclusion(probability_assessment)
            }
        })

        return {
            "petition_structure": petition_structure,
            "word_count": self._estimate_word_count(petition_structure),
            "estimated_preparation_time": "2-3天",
            "recommended_evidence_count": len(evidence_strategy.get("collection_plan", [])),
            "completion_checklist": self._generate_completion_checklist(),
        }

    # 辅助方法

    async def _analyze_novelty_ground(
        self,
        patent: Dict,
        references: List[Dict]
    ) -> Dict:
        """分析新颖性无效理由"""
        # 检查是否有对比文件公开了所有必要技术特征
        patent_claims = patent.get("claims", "")
        total_features = len(self._extract_features(patent_claims))

        # 评估对比文件公开程度
        disclosed_count = 0
        for ref in references:
            ref_features = len(self._extract_features(ref.get("content", "")))
            if ref_features >= total_features * 0.8:
                disclosed_count += 1

        is_valid_ground = disclosed_count > 0

        return {
            "is_valid_ground": is_valid_ground,
            "confidence": 0.8 if disclosed_count >= 2 else 0.6,
            "detailed_reasoning": f"发现{disclosed_count}篇对比文件可能破坏新颖性",
            "suggested_evidence": references[:3] if references else []
        }

    async def _analyze_creativity_ground(
        self,
        patent: Dict,
        references: List[Dict]
    ) -> Dict:
        """分析创造性无效理由"""
        # 检查现有技术是否给出技术启示
        has_guidance = len(references) > 0

        # 评估是否显而易见
        is_obvious = has_guidance and len(references) >= 2

        return {
            "is_valid_ground": is_obvious,
            "confidence": 0.7 if is_obvious else 0.5,
            "detailed_reasoning": "现有技术给出了技术启示，权利要求显而易见" if is_obvious else "需要更多证据证明显而易见性",
            "suggested_evidence": references[:2] if references else []
        }

    async def _analyze_insufficient_disclosure(
        self,
        patent: Dict
    ) -> Dict:
        """分析公开不充分无效理由"""
        specification = patent.get("specification", "")
        embodiments = patent.get("embodiments", [])

        # 检查实施方式是否充分
        is_insufficient = (
            len(specification) < 500 or
            len(embodiments) == 0
        )

        return {
            "is_valid_ground": is_insufficient,
            "confidence": 0.6,
            "detailed_reasoning": "说明书技术描述过于简单，本领域技术人员无法实现" if is_insufficient else "说明书公开较为充分",
            "missing_aspects": self._identify_missing_disclosure_aspects(patent)
        }

    async def _analyze_amendment_exceeds_scope(
        self,
        patent: Dict
    ) -> Dict:
        """分析修改超范围无效理由"""
        # 检查是否有修改记录
        prosecution_history = patent.get("prosecution_history", [])

        # 简化版检查
        has_amendments = len(prosecution_history) > 0

        # 检查修改是否超范围
        exceeds_scope = False
        if has_amendments:
            # 实际应该对比原始申请文件和修改后的文件
            exceeds_scope = True  # 简化版假设

        return {
            "is_valid_ground": exceeds_scope,
            "confidence": 0.5,
            "detailed_reasoning": "修改内容超出了原始申请文件记载的范围" if exceeds_scope else "未发现明显超范围修改",
            "amendment_details": prosecution_history[:3] if prosecution_history else []
        }

    def _assess_ground_strength(
        self,
        ground: Dict
    ) -> str:
        """评估理由强度"""
        confidence = ground["analysis"].get("confidence", 0.5)

        if confidence >= HIGH_STRENGTH_CONFIDENCE:
            return "strong"
        elif confidence >= MEDIUM_STRENGTH_CONFIDENCE:
            return "moderate"
        else:
            return "weak"

    def _select_best_grounds(
        self,
        valid_grounds: List[Dict]
    ) -> List[Dict]:
        """选择最佳无效理由"""
        # 按强度排序
        sorted_grounds = sorted(
            valid_grounds,
            key=lambda g: g["analysis"].get("confidence", 0),
            reverse=True
        )

        # 选择top 2-3个理由
        return sorted_grounds[:3]

    def _generate_search_keywords(
        self,
        ground_type: str
    ) -> List[str]:
        """生成检索关键词"""
        keywords_map = {
            "lack_of_novelty": [
                "技术领域",
                "技术问题",
                "技术方案",
                "关键技术特征"
            ],
            "lack_of_creativity": [
                "技术启示",
                "结合动机",
                "常规手段",
                "显而易见"
            ],
            "insufficient_disclosure": [
                "技术常识",
                "标准文献",
                "技术手册"
            ]
        }

        return keywords_map.get(ground_type, [])

    def _calculate_ground_strength_score(
        self,
        ground_strengths: List[Dict]
    ) -> float:
        """计算理由强度得分"""
        if not ground_strengths:
            return 0.0

        strength_scores = {
            "strong": 1.0,
            "moderate": 0.6,
            "weak": 0.3
        }

        scores = [
            strength_scores.get(g["strength"], 0) * g.get("confidence", 0.5)
            for g in ground_strengths
        ]

        return sum(scores) / len(scores) if scores else 0

    def _assess_evidence_quality(
        self,
        evidence_strategy: Dict
    ) -> float:
        """评估证据质量"""
        # 简化版评估
        collection_plan = evidence_strategy.get("collection_plan", [])

        if not collection_plan:
            return 0.5

        # 计划的来源多样性
        source_diversity = 0
        for plan in collection_plan:
            sources_count = len(plan.get("actions", []))
            if sources_count >= 3:
                source_diversity += 1

        return min(source_diversity / len(collection_plan), 1.0)

    def _generate_outcome_prediction(
        self,
        probability: float,
        ground_strengths: List[Dict]
    ) -> Dict:
        """生成结果预测"""
        if probability >= HIGH_SUCCESS_PROBABILITY:
            outcome = "全部无效"
            likelihood = "high"
        elif probability >= MEDIUM_SUCCESS_PROBABILITY:
            outcome = "部分无效"
            likelihood = "medium"
        elif probability >= LOW_SUCCESS_PROBABILITY:
            outcome = "可能维持"
            likelihood = "low"
        else:
            outcome = "维持有效"
            likelihood = "very_low"

        return {
            "predicted_outcome": outcome,
            "likelihood": likelihood,
            "reasoning": f"基于{len(ground_strengths)}个无效理由的综合评估"
        }

    def _identify_risk_factors(
        self,
        ground_strengths: List[Dict]
    ) -> List[str]:
        """识别风险因素"""
        risks = []

        for ground in ground_strengths:
            if ground["strength"] == "weak":
                risks.append(f"{ground['type']}理由强度较弱，可能不被支持")

        # 检查是否有多个理由但都较弱
        weak_count = len([g for g in ground_strengths if g["strength"] == "weak"])
        if weak_count == len(ground_strengths):
            risks.append("所有无效理由强度均较弱，整体风险较高")

        if not risks:
            risks.append("无明显风险因素")

        return risks

    def _generate_strategy_recommendation(
        self,
        probability: float,
        _ground_strengths: List[Dict]
    ) -> str:
        """生成策略建议

        Note: ground_strengths参数保留用于未来扩展（基于理由强度的策略定制）
        """
        if probability >= HIGH_SUCCESS_PROBABILITY:
            return "建议同时主张多个无效理由，重点突出最强理由"
        elif probability >= MEDIUM_SUCCESS_PROBABILITY:
            return "建议主张2-3个无效理由，准备充分的证据支持"
        elif probability >= LOW_SUCCESS_PROBABILITY:
            return "建议继续搜集证据，提高成功概率后再提交"
        else:
            return "建议重新评估无效宣告的可行性"

    def _generate_legal_reasoning(
        self,
        recommended_grounds: List[Dict]
    ) -> str:
        """生成法律依据说明"""
        reasoning_parts = []

        for ground in recommended_grounds:
            ground_type = ground["ground_type"]
            if ground_type == "lack_of_novelty":
                reasoning_parts.append("依据专利法第22条第1款，该专利不具备新颖性")
            elif ground_type == "lack_of_creativity":
                reasoning_parts.append("依据专利法第22条第3款，该专利不具备创造性")
            elif ground_type == "insufficient_disclosure":
                reasoning_parts.append("依据专利法第26条第3款，说明书公开不充分")

        return "；".join(reasoning_parts)

    def _generate_argument_1(
        self,
        recommended_grounds: List[Dict]
    ) -> str:
        """生成论据1"""
        ground = recommended_grounds[0] if recommended_grounds else {}
        return f"根据{ground.get('ground_type')}，{ground.get('description')}。{ground.get('analysis', {}).get('detailed_reasoning', '')}"

    def _generate_argument_2(
        self,
        recommended_grounds: List[Dict]
    ) -> str:
        """生成论据2"""
        if len(recommended_grounds) > 1:
            ground = recommended_grounds[1]
            return f"此外，{ground.get('description')}。{ground.get('analysis', {}).get('detailed_reasoning', '')}"
        else:
            return "（无）"

    def _generate_conclusion(
        self,
        probability_assessment: Dict
    ) -> str:
        """生成结论"""
        probability = probability_assessment.get("overall_probability", 0)
        prediction = probability_assessment.get("prediction", {})

        return f"综上所述，该专利{prediction.get('predicted_outcome', '')}，成功概率约为{probability:.0%}。"

    def _extract_features(self, text: str) -> List[str]:
        """提取技术特征"""
        return CHINESE_WORD_PATTERN.findall(text)

    def _identify_missing_disclosure_aspects(
        self,
        patent: Dict
    ) -> List[str]:
        """识别缺失的披露内容"""
        missing = []

        if not patent.get("embodiments"):
            missing.append("缺少具体实施方式")

        if not patent.get("best_mode"):
            missing.append("未披露最佳实施方式")

        if not patent.get("drawings"):
            missing.append("缺少附图说明")

        return missing if missing else ["无明显缺失"]

    def _estimate_word_count(
        self,
        petition_structure: Dict
    ) -> int:
        """估算字数"""
        # 简化版估算
        return len(str(petition_structure))

    def _generate_completion_checklist(
        self
    ) -> List[str]:
        """生成完成清单"""
        return [
            "确认请求人信息完整",
            "核实专利基本信息准确",
            "完善无效理由阐述",
            "准备证据材料",
            "附上证据副本",
            "准备法律依据文件",
            "撰写具体理由阐述",
            "检查格式规范",
            "准备申请费用"
        ]

    def _generate_overall_recommendation(
        self,
        probability_assessment: Dict
    ) -> str:
        """生成总体建议"""
        probability = probability_assessment.get("overall_probability", 0)
        prediction = probability_assessment.get("prediction", {})

        if probability >= MEDIUM_SUCCESS_PROBABILITY + 0.1:  # 0.7
            return f"建议提交无效宣告，预测结果：{prediction.get('predicted_outcome', '')}"
        elif probability >= LOW_SUCCESS_PROBABILITY:
            return "建议补充证据后再提交，提高成功概率"
        else:
            return "建议重新评估无效宣告的可行性"

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
