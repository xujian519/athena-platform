from __future__ import annotations

"""
软件专利风险分析器

基于论文#20《Predicting Patent Quality》
- 软件专利无效风险45%
- 抽象概念是主要风险因素

作者: 小娜·天秤女神
创建时间: 2026-03-20
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SoftwarePatentRiskAssessment:
    """软件专利风险评估结果"""
    is_software_patent: bool
    risk_level: str  # low/medium/high
    risk_score: float  # 0-1
    technical_feature_score: float  # 技术特征评分 0-10
    abstract_idea_risk: float  # 抽象概念风险 0-1
    alice_step1_risk: float  # Alice两步测试第一步风险
    alice_step2_risk: float  # Alice两步测试第二步风险
    suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "is_software_patent": self.is_software_patent,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "technical_feature_score": self.technical_feature_score,
            "abstract_idea_risk": self.abstract_idea_risk,
            "alice_step1_risk": self.alice_step1_risk,
            "alice_step2_risk": self.alice_step2_risk,
            "suggestions": self.suggestions,
        }


class SoftwarePatentRiskAnalyzer:
    """
    软件专利风险分析器

    基于论文#20的关键发现:
    - 软件专利无效风险45%
    - 抽象概念是主要风险因素

    分析框架 (Alice两步测试):
    1. 是否落入抽象概念
    2. 是否包含"发明概念" (inventive concept)

    风险指标:
    - 抽象概念关键词
    - 技术特征充分性
    - 技术三要素完整性
    """

    # 软件专利关键词
    SOFTWARE_KEYWORDS = [
        "计算机", "程序", "软件", "算法", "代码",
        "处理器", "存储器", "指令", "模块", "接口",
        "数据库", "服务器", "客户端", "网络",
        "电子", "数字", "自动化",
    ]

    # 抽象概念模式 (Alice Step 1高风险)
    ABSTRACT_IDEA_PATTERNS = [
        ("收集数据", 0.15),
        ("存储信息", 0.15),
        ("分析数据", 0.15),
        ("计算结果", 0.10),
        ("显示结果", 0.10),
        ("传输数据", 0.10),
        ("比较数据", 0.10),
        ("生成报告", 0.10),
        ("管理流程", 0.15),
        ("优化配置", 0.10),
    ]

    # 技术三要素关键词
    TECHNICAL_ELEMENTS = {
        "technical_problem": [
            "技术问题", "解决的技术问题", "存在的技术问题",
            "技术难点", "技术瓶颈", "技术缺陷",
        ],
        "technical_solution": [
            "技术方案", "技术特征", "技术手段", "技术措施",
            "技术实现", "技术路径", "技术架构",
        ],
        "technical_effect": [
            "技术效果", "有益效果", "技术进步", "技术优势",
            "性能提升", "效率提高", "精度提高",
        ],
    }

    # 发明概念关键词 (Alice Step 2积极因素)
    INVENTIVE_CONCEPT_INDICATORS = [
        "特定", "具体", "专用", "定制", "独特",
        "改进", "优化", "增强", "新颖", "创新",
    ]

    # CPC软件相关分类
    SOFTWARE_CPC_CODES = ["G06F", "G06Q", "G06N", "G10L", "G16B", "G16C"]

    def __init__(self):
        self.name = "软件专利风险分析器"
        self.logger = logging.getLogger(self.name)

    async def analyze(
        self,
        claims: list[str],
        cpc_code: str = "",
        description: str = "",
    ) -> SoftwarePatentRiskAssessment:
        """
        分析软件专利风险

        Args:
            claims: 权利要求列表
            cpc_code: CPC分类代码
            description: 说明书 (可选)

        Returns:
            SoftwarePatentRiskAssessment: 风险评估结果
        """
        claim_text = " ".join(claims)

        # 1. 判断是否软件专利
        is_software = self._is_software_patent(claim_text, cpc_code)

        if not is_software:
            return SoftwarePatentRiskAssessment(
                is_software_patent=False,
                risk_level="low",
                risk_score=0.0,
                technical_feature_score=10.0,
                abstract_idea_risk=0.0,
                alice_step1_risk=0.0,
                alice_step2_risk=0.0,
                suggestions=["非软件专利，按常规专利评估标准"],
            )

        # 2. 评估技术特征充分性
        tech_score = self._evaluate_technical_features(claim_text, description)

        # 3. 评估抽象概念风险 (Alice Step 1)
        abstract_risk = self._evaluate_abstract_idea_risk(claim_text)

        # 4. 评估发明概念 (Alice Step 2)
        inventive_concept = self._evaluate_inventive_concept(claim_text, description)

        # 5. 计算Alice两步测试风险
        alice_step1_risk = abstract_risk
        alice_step2_risk = 1.0 - inventive_concept

        # 6. 计算综合风险
        overall_risk = self._calculate_software_risk(
            tech_score,
            abstract_risk,
            inventive_concept,
        )

        # 7. 生成改进建议
        suggestions = self._generate_software_suggestions(
            tech_score,
            abstract_risk,
            inventive_concept,
        )

        return SoftwarePatentRiskAssessment(
            is_software_patent=True,
            risk_level=overall_risk["level"],
            risk_score=overall_risk["score"],
            technical_feature_score=tech_score,
            abstract_idea_risk=abstract_risk,
            alice_step1_risk=alice_step1_risk,
            alice_step2_risk=alice_step2_risk,
            suggestions=suggestions,
        )

    def _is_software_patent(self, claim_text: str, cpc_code: str) -> bool:
        """判断是否软件专利"""
        # CPC分类判断
        if any(cpc_code.startswith(code) for code in self.SOFTWARE_CPC_CODES):
            return True

        # 关键词判断
        claim_lower = claim_text.lower()
        keyword_matches = sum(1 for kw in self.SOFTWARE_KEYWORDS if kw in claim_lower)

        # 超过3个软件关键词则判定为软件专利
        return keyword_matches >= 3

    def _evaluate_technical_features(self, claim_text: str, description: str) -> float:
        """
        评估技术特征充分性

        Returns:
            float: 0-10分
        """
        score = 5.0  # 基础分

        full_text = claim_text + " " + description

        # 检查技术三要素
        for _element, keywords in self.TECHNICAL_ELEMENTS.items():
            if any(kw in full_text for kw in keywords):
                score += 1.0

        # 检查具体技术实现
        implementation_keywords = [
            "电路", "架构", "协议", "接口", "硬件",
            "寄存器", "总线", "中断", "缓存", "线程",
            "协议栈", "数据结构", "编码", "解码",
        ]
        if any(kw in full_text for kw in implementation_keywords):
            score += 1.5

        # 检查技术效果描述
        effect_keywords = [
            "降低延迟", "提高效率", "减少功耗", "提升性能",
            "优化资源", "增强安全", "改善用户体验",
        ]
        if any(kw in full_text for kw in effect_keywords):
            score += 0.5

        return min(10.0, score)

    def _evaluate_abstract_idea_risk(self, claim_text: str) -> float:
        """
        评估抽象概念风险 (Alice Step 1)

        Returns:
            float: 0-1风险值
        """
        risk = 0.0
        claim_lower = claim_text.lower()

        # 检查抽象概念模式
        for pattern, weight in self.ABSTRACT_IDEA_PATTERNS:
            if pattern in claim_lower:
                risk += weight

        # 检查商业方法泛化
        business_keywords = ["商业", "交易", "支付", "管理"]
        if any(kw in claim_lower for kw in business_keywords):
            # 如果没有具体技术实现
            if not any(kw in claim_lower for kw in ["具体", "特定", "专用"]):
                risk += 0.2

        # 检查纯数学方法
        math_keywords = ["计算", "数学", "公式", "算法"]
        math_count = sum(1 for kw in math_keywords if kw in claim_lower)
        if math_count >= 2:
            risk += 0.15

        return min(1.0, risk)

    def _evaluate_inventive_concept(self, claim_text: str, description: str) -> float:
        """
        评估发明概念 (Alice Step 2)

        Returns:
            float: 0-1发明概念强度
        """
        strength = 0.0
        full_text = claim_text + " " + description

        # 检查发明概念指示词
        for indicator in self.INVENTIVE_CONCEPT_INDICATORS:
            if indicator in full_text:
                strength += 0.1

        # 检查技术改进
        improvement_keywords = [
            "改进", "优化", "增强", "提升", "新",
            "创新", "突破", "革新",
        ]
        if any(kw in full_text for kw in improvement_keywords):
            strength += 0.2

        # 检查非通用技术
        specific_tech = [
            "机器学习", "深度学习", "区块链", "量子",
            "边缘计算", "联邦学习", "差分隐私",
        ]
        if any(kw in full_text for kw in specific_tech):
            strength += 0.3

        # 检查硬件结合
        hardware_keywords = ["传感器", "处理器", "芯片", "电路", "设备"]
        if any(kw in full_text for kw in hardware_keywords):
            strength += 0.2

        return min(1.0, strength)

    def _calculate_software_risk(
        self,
        tech_score: float,
        abstract_risk: float,
        inventive_concept: float,
    ) -> dict:
        """计算综合软件专利风险"""
        # 技术特征越充分，风险越低
        tech_factor = (10.0 - tech_score) / 10.0

        # 发明概念越强，风险越低
        inventive_factor = 1.0 - inventive_concept

        # 加权计算
        overall_risk = (
            tech_factor * 0.3 +
            abstract_risk * 0.4 +
            inventive_factor * 0.3
        )

        # 确定风险等级
        if overall_risk >= 0.7:
            level = "high"
        elif overall_risk >= 0.4:
            level = "medium"
        else:
            level = "low"

        return {"level": level, "score": overall_risk}

    def _generate_software_suggestions(
        self,
        tech_score: float,
        abstract_risk: float,
        inventive_concept: float,
    ) -> list[str]:
        """生成软件专利改进建议"""
        suggestions = []

        if tech_score < 7.0:
            suggestions.append("增加具体的技术实现细节")
            suggestions.append("明确说明技术方案如何解决技术问题")

        if abstract_risk > 0.3:
            suggestions.append("避免仅描述通用的数据处理步骤")
            suggestions.append("强调技术方案的创新性和非显而易见性")

        if inventive_concept < 0.5:
            suggestions.append("增强发明概念的描述")
            suggestions.append("说明与现有技术的区别和创新点")

        if tech_score >= 7.0 and abstract_risk <= 0.3 and inventive_concept >= 0.5:
            suggestions.append("技术特征描述充分，保持当前质量")

        # Alice测试特定建议
        if abstract_risk > 0.5:
            suggestions.append("考虑通过Alice两步测试的风险较高，建议重新审视权利要求")

        return list(dict.fromkeys(suggestions))[:5]


# 便捷函数
def get_software_patent_risk_analyzer() -> SoftwarePatentRiskAnalyzer:
    """获取软件专利风险分析器实例"""
    return SoftwarePatentRiskAnalyzer()
