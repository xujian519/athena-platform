#!/usr/bin/env python3
"""
专利分类分级器

对专利进行自动分类和分级，便于管理和维护。
"""
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

try:
    from .patent_list_manager import PatentRecord, PatentStatus, PatentType
except ImportError:
    from core.patents.portfolio.patent_list_manager import PatentRecord, PatentStatus, PatentType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TechnologyField(Enum):
    """技术领域"""
    ELECTRONICS = "electronics"  # 电子信息
    SOFTWARE = "software"  # 软件互联网
    BIOTECH = "biotech"  # 生物医药
    NEW_MATERIAL = "new_material"  # 新材料
    EQUIPMENT = "equipment"  # 高端装备
    ENERGY = "energy"  # 新能源
    AUTOMOTIVE = "automotive"  # 汽车交通
    CHEMICAL = "chemical"  # 石化化工
    MACHINERY = "machinery"  # 机械制造
    OTHER = "other"  # 其他


class PatentGrade(Enum):
    """专利等级"""
    CORE = "core"  # 核心专利
    IMPORTANT = "important"  # 重要专利
    GENERAL = "general"  # 一般专利
    LOW_VALUE = "low_value"  # 低价值专利


class MaintenanceStrategy(Enum):
    """维持策略"""
    MAINTAIN = "maintain"  # 维持
    MONITOR = "monitor"  # 监控
    ABANDON = "abandon"  # 放弃


@dataclass
class ClassificationResult:
    """分类结果"""
    patent_id: str
    technology_field: TechnologyField
    patent_grade: PatentGrade
    confidence: float  # 置信度 (0-1)
    reasons: list[str]  # 分类理由

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "patent_id": self.patent_id,
            "technology_field": self.technology_field.value,
            "patent_grade": self.patent_grade.value,
            "confidence": self.confidence,
            "reasons": self.reasons
        }


@dataclass
class GradingResult:
    """分级结果"""
    patent_id: str
    grade: PatentGrade
    score: float  # 评分 (0-100)
    factors: dict[str, float]  # 各项得分
    maintenance_strategy: MaintenanceStrategy
    recommendations: list[str]  # 建议

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "patent_id": self.patent_id,
            "grade": self.grade.value,
            "score": self.score,
            "factors": self.factors,
            "maintenance_strategy": self.maintenance_strategy.value,
            "recommendations": self.recommendations
        }


class PatentClassifier:
    """专利分类分级器"""

    def __init__(self):
        """初始化分类器"""
        self.field_keywords = self._load_field_keywords()
        self.grade_criteria = self._load_grade_criteria()
        logger.info("✅ 专利分类分级器初始化成功")

    def _load_field_keywords(self) -> dict[TechnologyField, list[str]:
        """加载领域关键词"""
        return {
            TechnologyField.ELECTRONICS: [
                "芯片", "集成电路", "半导体", "电路", "电子", "通信", "天线",
                "传感器", "显示", "光电子", "微波", "射频"
            ],
            TechnologyField.SOFTWARE: [
                "软件", "算法", "数据", "云计算", "大数据", "人工智能",
                "机器学习", "区块链", "物联网", "虚拟现实", "增强现实"
            ],
            TechnologyField.BIOTECH: [
                "生物", "医药", "基因", "蛋白质", "疫苗", "抗体", "药物",
                "医疗", "诊断", "治疗", "细胞", "微生物"
            ],
            TechnologyField.NEW_MATERIAL: [
                "材料", "合金", "复合材料", "纳米", "陶瓷", "高分子",
                "涂层", "薄膜", "超导", "石墨烯", "碳纳米管"
            ],
            TechnologyField.EQUIPMENT: [
                "数控", "精密仪器", "激光", "机器人", "自动化", "测量",
                "检测", "加工", "制造", "装备", "设备"
            ],
            TechnologyField.ENERGY: [
                "电池", "太阳能", "风能", "核能", "储能", "发电",
                "新能源", "节能", "环保", "绿色", "可再生能源"
            ],
            TechnologyField.AUTOMOTIVE: [
                "汽车", "车辆", "发动机", "变速箱", "制动", "转向",
                "驾驶", "交通", "运输", "自动驾驶", "智能网联"
            ],
            TechnologyField.CHEMICAL: [
                "化学", "化工", "石化", "塑料", "橡胶", "纤维",
                "涂料", "树脂", "合成", "聚合", "催化"
            ],
            TechnologyField.MACHINERY: [
                "机械", "传动", "液压", "气动", "轴承", "齿轮",
                "泵", "阀门", "电机", "减速器", "结构件"
            ]
        }

    def _load_grade_criteria(self) -> dict[str, dict[str, float]:
        """加载分级标准"""
        return {
            "core": {
                "value_score": 0.8,
                "claims_count": 5,
                "citations": 10,
                "family_size": 3
            },
            "important": {
                "value_score": 0.6,
                "claims_count": 3,
                "citations": 5,
                "family_size": 2
            },
            "general": {
                "value_score": 0.4,
                "claims_count": 1,
                "citations": 2,
                "family_size": 1
            },
            "low_value": {
                "value_score": 0.2,
                "claims_count": 0,
                "citations": 0,
                "family_size": 0
            }
        }

    def classify_patent(
        self,
        patent: PatentRecord,
        additional_info: dict[str, Any] | None = None
    ) -> ClassificationResult:
        """
        对专利进行分类

        Args:
            patent: 专利记录
            additional_info: 额外信息（如摘要、权利要求等）

        Returns:
            ClassificationResult对象
        """
        logger.info(f"🔍 分类专利: {patent.patent_id}")

        # 提取文本
        text = patent.title
        if additional_info:
            text += " " + additional_info.get("abstract", "")
            text += " " + additional_info.get("claims", "")

        # 识别技术领域
        technology_field = self._identify_field(text)

        # 确定等级
        patent_grade = self._determine_grade(patent, additional_info)

        # 计算置信度
        confidence = self._calculate_confidence(
            patent,
            technology_field,
            patent_grade
        )

        # 生成理由
        reasons = self._generate_reasons(
            patent,
            technology_field,
            patent_grade,
            additional_info
        )

        return ClassificationResult(
            patent_id=patent.patent_id,
            technology_field=technology_field,
            patent_grade=patent_grade,
            confidence=confidence,
            reasons=reasons
        )

    def _identify_field(self, text: str) -> TechnologyField:
        """识别技术领域"""
        scores = {}

        for field, keywords in self.field_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    score += 1
            scores[field] = score

        # 找出得分最高的领域
        if not scores or max(scores.values()) == 0:
            return TechnologyField.OTHER

        best_field = max(scores, key=scores.get)
        return best_field

    def _determine_grade(
        self,
        patent: PatentRecord,
        additional_info: dict[str, Any] | None
    ) -> PatentGrade:
        """确定专利等级"""
        score = 0

        # 基于价值评分
        score += patent.value_score * 40

        # 基于专利类型
        if patent.patent_type == PatentType.INVENTION:
            score += 20
        elif patent.patent_type == PatentType.UTILITY_MODEL:
            score += 10

        # 基于状态
        if patent.status == PatentStatus.GRANTED:
            score += 15
        elif patent.status == PatentStatus.MAINTAINED:
            score += 10

        # 基于额外信息
        if additional_info:
            claims_count = additional_info.get("claims_count", 0)
            if claims_count >= 5:
                score += 15
            elif claims_count >= 3:
                score += 10

            citations = additional_info.get("citations", 0)
            if citations >= 10:
                score += 10
            elif citations >= 5:
                score += 5

        # 确定等级
        if score >= 80:
            return PatentGrade.CORE
        elif score >= 60:
            return PatentGrade.IMPORTANT
        elif score >= 40:
            return PatentGrade.GENERAL
        else:
            return PatentGrade.LOW_VALUE

    def _calculate_confidence(
        self,
        patent: PatentRecord,
        field: TechnologyField,
        grade: PatentGrade
    ) -> float:
        """计算置信度"""
        confidence = 0.5

        # 如果有分类信息，增加置信度
        if patent.category:
            confidence += 0.2

        # 如果有高价值评分，增加置信度
        if patent.value_score > 0.7:
            confidence += 0.1

        # 如果是发明专利，增加置信度
        if patent.patent_type == PatentType.INVENTION:
            confidence += 0.1

        # 如果是核心专利，增加置信度
        if grade == PatentGrade.CORE:
            confidence += 0.1

        return min(1.0, confidence)

    def _generate_reasons(
        self,
        patent: PatentRecord,
        field: TechnologyField,
        grade: PatentGrade,
        additional_info: dict[str, Any] | None
    ) -> list[str]:
        """生成分类理由"""
        reasons = []

        # 技术领域理由
        field_name = {
            TechnologyField.ELECTRONICS: "电子信息",
            TechnologyField.SOFTWARE: "软件互联网",
            TechnologyField.BIOTECH: "生物医药",
            TechnologyField.NEW_MATERIAL: "新材料",
            TechnologyField.EQUIPMENT: "高端装备",
            TechnologyField.ENERGY: "新能源",
            TechnologyField.AUTOMOTIVE: "汽车交通",
            TechnologyField.CHEMICAL: "石化化工",
            TechnologyField.MACHINERY: "机械制造",
            TechnologyField.OTHER: "其他"
        }.get(field, "其他")

        reasons.append(f"属于{field_name}领域")

        # 等级理由
        if grade == PatentGrade.CORE:
            reasons.append("高价值评分，核心专利")
        elif grade == PatentGrade.IMPORTANT:
            reasons.append("中等价值评分，重要专利")
        elif grade == PatentGrade.GENERAL:
            reasons.append("一般价值评分，普通专利")
        else:
            reasons.append("低价值评分，建议评估")

        # 专利类型理由
        if patent.patent_type == PatentType.INVENTION:
            reasons.append("发明专利，保护期限长")

        # 状态理由
        if patent.status == PatentStatus.MAINTAINED:
            reasons.append("维持中，有效专利")

        return reasons

    def grade_patent(
        self,
        patent: PatentRecord,
        additional_info: dict[str, Any] | None = None
    ) -> GradingResult:
        """
        对专利进行分级

        Args:
            patent: 专利记录
            additional_info: 额外信息

        Returns:
            GradingResult对象
        """
        logger.info(f"⭐ 分级专利: {patent.patent_id}")

        # 计算各项得分
        factors = {}
        factors["value_score"] = patent.value_score * 100

        # 专利类型得分
        type_score = {
            PatentType.INVENTION: 30,
            PatentType.UTILITY_MODEL: 20,
            PatentType.DESIGN: 10
        }.get(patent.patent_type, 10)
        factors["patent_type"] = type_score

        # 状态得分
        status_score = {
            PatentStatus.MAINTAINED: 30,
            PatentStatus.GRANTED: 25,
            PatentStatus.EXAMINING: 20,
            PatentStatus.PUBLISHED: 15,
            PatentStatus.APPLICATION: 10
        }.get(patent.status, 5)
        factors["status"] = status_score

        # 权利要求数量得分
        claims_count = additional_info.get("claims_count", 0) if additional_info else 0
        claims_score = min(30, claims_count * 5)
        factors["claims_count"] = claims_score

        # 引用次数得分
        citations = additional_info.get("citations", 0) if additional_info else 0
        citation_score = min(20, citations * 2)
        factors["citations"] = citation_score

        # 计算总分
        score = sum(factors.values())

        # 确定等级
        if score >= 80:
            grade = PatentGrade.CORE
            strategy = MaintenanceStrategy.MAINTAIN
        elif score >= 60:
            grade = PatentGrade.IMPORTANT
            strategy = MaintenanceStrategy.MAINTAIN
        elif score >= 40:
            grade = PatentGrade.GENERAL
            strategy = MaintenanceStrategy.MONITOR
        else:
            grade = PatentGrade.LOW_VALUE
            strategy = MaintenanceStrategy.ABANDON

        # 生成建议
        recommendations = self._generate_recommendations(grade, score, factors)

        return GradingResult(
            patent_id=patent.patent_id,
            grade=grade,
            score=score,
            factors=factors,
            maintenance_strategy=strategy,
            recommendations=recommendations
        )

    def _generate_recommendations(
        self,
        grade: PatentGrade,
        score: float,
        factors: dict[str, float]
    ) -> list[str]:
        """生成建议"""
        recommendations = []

        if grade == PatentGrade.CORE:
            recommendations.append("核心专利，建议重点维持")
            recommendations.append("可考虑构建专利组合")
            recommendations.append("定期监控市场动态")
        elif grade == PatentGrade.IMPORTANT:
            recommendations.append("重要专利，建议维持")
            recommendations.append("关注技术发展趋势")
        elif grade == PatentGrade.GENERAL:
            recommendations.append("一般专利，建议评估维持价值")
            recommendations.append("可考虑许可或转让")
        else:
            recommendations.append("低价值专利，建议考虑放弃")
            recommendations.append("或评估许可可能性")

        # 基于得分的具体建议
        if factors.get("citations", 0) < 10:
            recommendations.append("引用较少，建议加强市场推广")

        if factors.get("claims_count", 0) < 10:
            recommendations.append("权利要求较少，保护范围可能有限")

        return recommendations


async def test_patent_classifier():
    """测试专利分类分级器"""
    classifier = PatentClassifier()

    print("\n" + "="*80)
    print("🔍 专利分类分级器测试")
    print("="*80)

    # 测试专利
    patent = PatentRecord(
        patent_id="CN123456789A",
        patent_type=PatentType.INVENTION,
        title="基于人工智能的智能控制系统及方法",
        application_date="2020-01-15",
        grant_date="2022-03-20",
        status=PatentStatus.MAINTAINED,
        inventor="张三",
        applicant="××科技公司",
        category="人工智能",
        value_score=0.85
    )

    additional_info = {
        "abstract": "本发明涉及一种基于深度学习算法的智能控制系统...",
        "claims": 6,
        "citations": 15
    }

    # 分类
    classification = classifier.classify_patent(patent, additional_info)

    print("\n📊 分类结果:")
    print(f"   专利号: {classification.patent_id}")
    print(f"   技术领域: {classification.technology_field.value}")
    print(f"   专利等级: {classification.patent_grade.value}")
    print(f"   置信度: {classification.confidence:.2f}")
    print("   理由:")
    for reason in classification.reasons:
        print(f"      - {reason}")

    # 分级
    grading = classifier.grade_patent(patent, additional_info)

    print("\n⭐ 分级结果:")
    print(f"   专利号: {grading.patent_id}")
    print(f"   等级: {grading.grade.value}")
    print(f"   总分: {grading.score:.1f}")
    print(f"   维持策略: {grading.maintenance_strategy.value}")
    print("   各项得分:")
    for factor, score in grading.factors.items():
        print(f"      {factor}: {score:.1f}")
    print("   建议:")
    for rec in grading.recommendations[:3]:
        print(f"      - {rec}")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_patent_classifier())
