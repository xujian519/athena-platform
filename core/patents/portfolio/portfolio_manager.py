#!/usr/bin/env python3
"""
专利组合管理主控制器

整合所有模块，提供完整的专利组合管理功能。
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional

try:
    from .patent_list_manager import PatentListManager, PatentRecord
    from .patent_classifier import PatentClassifier, ClassificationResult, GradingResult
    from .value_assessor import ValueAssessor, ValueAssessment
    from .maintenance_decider import MaintenanceDecisionMaker, MaintenanceDecision
except ImportError:
    from patents.core.portfolio.patent_list_manager import PatentListManager, PatentRecord
    from patents.core.portfolio.patent_classifier import PatentClassifier, ClassificationResult, GradingResult
    from patents.core.portfolio.value_assessor import ValueAssessor, ValueAssessment
    from patents.core.portfolio.maintenance_decider import MaintenanceDecisionMaker, MaintenanceDecision

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PortfolioManager:
    """专利组合管理器"""

    def __init__(self):
        """初始化管理器"""
        self.list_manager = PatentListManager()
        self.classifier = PatentClassifier()
        self.value_assessor = ValueAssessor()
        self.decision_maker = MaintenanceDecisionMaker()
        logger.info("✅ 专利组合管理器初始化成功")

    def add_patent(self, patent_data: Dict[str, Any]) -> bool:
        """添加专利到组合"""
        patent = PatentRecord(**patent_data)
        return self.list_manager.add_patent(patent)

    def analyze_patent(
        self,
        patent_id: str,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        分析单个专利

        Returns:
            包含分类、分级、价值评估、维持决策的完整分析
        """
        patent = self.list_manager.get_patent(patent_id)
        if not patent:
            return {"error": "专利不存在"}

        # 分类
        classification = self.classifier.classify_patent(patent, additional_info)

        # 分级
        grading = self.classifier.grade_patent(patent, additional_info)

        # 价值评估
        assessment = self.value_assessor.assess_value(
            patent,
            grading.grade,
            additional_info.get("market_data") if additional_info else None
        )

        # 维持决策
        decision = self.decision_maker.make_decision(patent, assessment)

        return {
            "patent_id": patent_id,
            "classification": classification.to_dict(),
            "grading": grading.to_dict(),
            "assessment": assessment.to_dict(),
            "decision": decision.to_dict()
        }

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """获取专利组合摘要"""
        return self.list_manager.generate_summary().to_dict()

    def get_upcoming_deadlines(self, days: int = 30) -> List[Dict[str, Any]]:
        """获取即将到期的期限"""
        summary = self.list_manager.generate_summary()
        return summary.upcoming_deadlines

    def batch_analyze(self, patent_ids: List[str]) -> Dict[str, Dict]:
        """批量分析专利"""
        results = {}
        for patent_id in patent_ids:
            results[patent_id] = self.analyze_patent(patent_id)
        return results


async def test_portfolio_manager():
    """测试专利组合管理器"""
    manager = PortfolioManager()

    print("\n" + "="*80)
    print("📊 专利组合管理器测试")
    print("="*80)

    # 添加测试专利
    patent_data = {
        "patent_id": "CN123456789A",
        "patent_type": "invention",
        "title": "基于人工智能的智能控制系统",
        "application_date": "2020-01-15",
        "grant_date": "2022-03-20",
        "status": "maintained",
        "annual_fee_due": "2026-03-20",
        "annual_fee_amount": 1200,
        "inventor": "张三",
        "applicant": "××科技公司",
        "category": "人工智能",
        "value_score": 0.8
    }

    manager.add_patent(patent_data)

    # 分析专利
    additional_info = {
        "abstract": "本发明涉及人工智能控制技术...",
        "claims_count": 6,
        "citations": 15,
        "market_data": {
            "market_growth": 0.25,
            "market_size": 0.8,
            "competition": 0.3
        }
    }

    analysis = manager.analyze_patent("CN123456789A", additional_info)

    print(f"\n📊 专利分析结果:")
    print(f"   专利号: {analysis['patent_id']}")
    print(f"   技术领域: {analysis['classification']['technology_field']}")
    print(f"   专利等级: {analysis['grading']['grade']}")
    print(f"   总分: {analysis['grading']['score']:.1f}")
    print(f"   当前价值: {analysis['assessment']['current_value']:.1f}")
    print(f"   维持决策: {analysis['decision']['decision']}")

    # 获取组合摘要
    summary = manager.get_portfolio_summary()
    print(f"\n📋 组合摘要:")
    print(f"   总专利数: {summary['total_patents']}")
    print(f"   年费预算: {summary['annual_fee_budget']:.0f}元")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_portfolio_manager())
