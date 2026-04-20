#!/usr/bin/env python3
"""
专利清单管理器

维护专利组合清单，记录专利基本信息、法律状态、费用信息等。
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PatentStatus(Enum):
    """专利状态"""
    APPLICATION = "application"  # 申请中
    PUBLISHED = "published"  # 公开
    EXAMINING = "examining"  # 审查中
    GRANTED = "granted"  # 授权
    MAINTAINED = "maintained"  # 维持中
    EXPIRED = "expired"  # 届满
    ABANDONED = "abandoned"  # 放弃
    INVALIDATED = "invalidated"  # 无效
    WITHDRAWN = "withdrawn"  # 撤回


class PatentType(Enum):
    """专利类型"""
    INVENTION = "invention"  # 发明专利
    UTILITY_MODEL = "utility_model"  # 实用新型
    DESIGN = "design"  # 外观设计


@dataclass
class PatentRecord:
    """专利记录"""
    patent_id: str  # 专利号
    patent_type: PatentType
    title: str  # 发明名称
    application_date: str  # 申请日期
    grant_date: Optional[str] = None  # 授权日期
    expiry_date: Optional[str] = None  # 届满日期
    status: PatentStatus = PatentStatus.APPLICATION
    annual_fee_due: Optional[str] = None  # 年费缴纳期限
    annual_fee_amount: Optional[float] = None  # 年费金额
    inventor: str = ""  # 发明人
    applicant: str = ""  # 申请人
    category: str = ""  # 分类
    value_score: float = 0.5  # 价值评分 (0-1)
    notes: str = ""  # 备注

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "patent_id": self.patent_id,
            "patent_type": self.patent_type.value,
            "title": self.title,
            "application_date": self.application_date,
            "grant_date": self.grant_date,
            "expiry_date": self.expiry_date,
            "status": self.status.value,
            "annual_fee_due": self.annual_fee_due,
            "annual_fee_amount": self.annual_fee_amount,
            "inventor": self.inventor,
            "applicant": self.applicant,
            "category": self.category,
            "value_score": self.value_score,
            "notes": self.notes
        }


@dataclass
class PortfolioSummary:
    """专利组合摘要"""
    total_patents: int  # 总专利数
    by_type: Dict[str, int]  # 按类型统计
    by_status: Dict[str, int]  # 按状态统计
    total_value: float  # 总价值评分
    upcoming_deadlines: List[Dict[str, Any]]  # 即将到期的期限
    annual_fee_budget: float  # 年费预算

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_patents": self.total_patents,
            "by_type": self.by_type,
            "by_status": self.by_status,
            "total_value": self.total_value,
            "upcoming_deadlines": self.upcoming_deadlines,
            "annual_fee_budget": self.annual_fee_budget
        }


class PatentListManager:
    """专利清单管理器"""

    def __init__(self):
        """初始化管理器"""
        self.patents: Dict[str, PatentRecord] = {}
        self.annual_fee_schedule = self._load_annual_fee_schedule()
        logger.info("✅ 专利清单管理器初始化成功")

    def _load_annual_fee_schedule(self) -> Dict[str, List[Dict[str, Any]]]:
        """加载年费缴纳标准"""
        return {
            "invention": [
                {"year": 1, "amount": 900},
                {"year": 2, "amount": 900},
                {"year": 3, "amount": 900},
                {"year": 4, "amount": 1200},
                {"year": 5, "amount": 1200},
                {"year": 6, "amount": 1200},
                {"year": 7, "amount": 2000},
                {"year": 8, "amount": 2000},
                {"year": 9, "amount": 2000},
                {"year": 10, "amount": 4000},
                {"year": 11, "amount": 4000},
                {"year": 12, "amount": 4000},
                {"year": 13, "amount": 6000},
                {"year": 14, "amount": 6000},
                {"year": 15, "amount": 6000},
                {"year": 16, "amount": 8000},
                {"year": 17, "amount": 8000},
                {"year": 18, "amount": 8000},
                {"year": 19, "amount": 8000},
                {"year": 20, "amount": 8000},
            ],
            "utility_model": [
                {"year": 1, "amount": 600},
                {"year": 2, "amount": 600},
                {"year": 3, "amount": 600},
                {"year": 4, "amount": 900},
                {"year": 5, "amount": 900},
                {"year": 6, "amount": 900},
                {"year": 7, "amount": 1200},
                {"year": 8, "amount": 1200},
                {"year": 9, "amount": 1200},
                {"year": 10, "amount": 1200},
            ],
            "design": [
                {"year": 1, "amount": 300},
                {"year": 2, "amount": 300},
                {"year": 3, "amount": 300},
                {"year": 4, "amount": 600},
                {"year": 5, "amount": 600},
                {"year": 6, "amount": 600},
                {"year": 7, "amount": 900},
                {"year": 8, "amount": 900},
                {"year": 9, "amount": 900},
                {"year": 10, "amount": 900},
                {"year": 11, "amount": 1200},
                {"year": 12, "amount": 1200},
                {"year": 13, "amount": 1200},
                {"year": 14, "amount": 1200},
                {"year": 15, "amount": 1200},
            ]
        }

    def add_patent(self, patent: PatentRecord) -> bool:
        """
        添加专利记录

        Args:
            patent: 专利记录

        Returns:
            是否添加成功
        """
        if patent.patent_id in self.patents:
            logger.warning(f"专利 {patent.patent_id} 已存在")
            return False

        self.patents[patent.patent_id] = patent
        logger.info(f"✅ 添加专利: {patent.patent_id}")
        return True

    def update_patent(self, patent_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新专利记录

        Args:
            patent_id: 专利号
            updates: 更新内容

        Returns:
            是否更新成功
        """
        if patent_id not in self.patents:
            logger.warning(f"专利 {patent_id} 不存在")
            return False

        patent = self.patents[patent_id]
        for key, value in updates.items():
            if hasattr(patent, key):
                setattr(patent, key, value)
            else:
                logger.warning(f"未知字段: {key}")

        logger.info(f"✅ 更新专利: {patent_id}")
        return True

    def remove_patent(self, patent_id: str) -> bool:
        """
        移除专利记录

        Args:
            patent_id: 专利号

        Returns:
            是否移除成功
        """
        if patent_id not in self.patents:
            logger.warning(f"专利 {patent_id} 不存在")
            return False

        del self.patents[patent_id]
        logger.info(f"✅ 移除专利: {patent_id}")
        return True

    def get_patent(self, patent_id: str) -> Optional[PatentRecord]:
        """
        获取专利记录

        Args:
            patent_id: 专利号

        Returns:
            专利记录或None
        """
        return self.patents.get(patent_id)

    def list_patents(
        self,
        patent_type: Optional[PatentType] = None,
        status: Optional[PatentStatus] = None,
        category: Optional[str] = None
    ) -> List[PatentRecord]:
        """
        列出专利记录

        Args:
            patent_type: 专利类型过滤
            status: 状态过滤
            category: 分类过滤

        Returns:
            专利记录列表
        """
        patents = list(self.patents.values())

        # 应用过滤条件
        if patent_type:
            patents = [p for p in patents if p.patent_type == patent_type]
        if status:
            patents = [p for p in patents if p.status == status]
        if category:
            patents = [p for p in patents if p.category == category]

        return patents

    def generate_summary(self) -> PortfolioSummary:
        """
        生成专利组合摘要

        Returns:
            专利组合摘要
        """
        if not self.patents:
            return PortfolioSummary(
                total_patents=0,
                by_type={},
                by_status={},
                total_value=0.0,
                upcoming_deadlines=[],
                annual_fee_budget=0.0
            )

        # 按类型统计
        by_type: Dict[str, int] = {}
        for patent in self.patents.values():
            ptype = patent.patent_type.value
            by_type[ptype] = by_type.get(ptype, 0) + 1

        # 按状态统计
        by_status: Dict[str, int] = {}
        for patent in self.patents.values():
            pstatus = patent.status.value
            by_status[pstatus] = by_status.get(pstatus, 0) + 1

        # 总价值评分
        total_value = sum(p.value_score for p in self.patents.values())

        # 即将到期的期限（30天内）
        upcoming_deadlines = []
        today = datetime.now()
        thirty_days_later = today + timedelta(days=30)

        for patent in self.patents.values():
            if patent.annual_fee_due:
                due_date = datetime.strptime(patent.annual_fee_due, "%Y-%m-%d")
                if today <= due_date <= thirty_days_later:
                    upcoming_deadlines.append({
                        "patent_id": patent.patent_id,
                        "title": patent.title,
                        "due_date": patent.annual_fee_due,
                        "amount": patent.annual_fee_amount,
                        "type": "annual_fee"
                    })

        # 排序
        upcoming_deadlines.sort(key=lambda x: x["due_date"])

        # 年费预算
        annual_fee_budget = sum(
            p.annual_fee_amount for p in self.patents.values()
            if p.annual_fee_amount
        )

        return PortfolioSummary(
            total_patents=len(self.patents),
            by_type=by_type,
            by_status=by_status,
            total_value=total_value,
            upcoming_deadlines=upcoming_deadlines[:10],  # 最多返回10个
            annual_fee_budget=annual_fee_budget
        )

    def calculate_annual_fee(
        self,
        patent_type: PatentType,
        grant_year: int,
        current_year: int
    ) -> float:
        """
        计算年费金额

        Args:
            patent_type: 专利类型
            grant_year: 授权年份
            current_year: 当前年份

        Returns:
            年费金额
        """
        year = current_year - grant_year + 1

        schedule = self.annual_fee_schedule.get(patent_type.value, [])
        for item in schedule:
            if item["year"] == year:
                return item["amount"]

        # 如果超出标准年限，按最高标准
        if schedule:
            return schedule[-1]["amount"]

        return 0.0


async def test_patent_list_manager():
    """测试专利清单管理器"""
    manager = PatentListManager()

    print("\n" + "="*80)
    print("📋 专利清单管理器测试")
    print("="*80)

    # 添加测试专利
    patents = [
        PatentRecord(
            patent_id="CN123456789A",
            patent_type=PatentType.INVENTION,
            title="一种智能控制系统",
            application_date="2020-01-15",
            grant_date="2022-03-20",
            expiry_date="2040-01-15",
            status=PatentStatus.MAINTAINED,
            annual_fee_due="2026-03-20",
            annual_fee_amount=1200,
            inventor="张三",
            applicant="××科技公司",
            category="人工智能",
            value_score=0.8
        ),
        PatentRecord(
            patent_id="CN987654321U",
            patent_type=PatentType.UTILITY_MODEL,
            title="一种新型机械装置",
            application_date="2021-06-10",
            grant_date="2022-08-15",
            status=PatentStatus.MAINTAINED,
            annual_fee_due="2026-08-15",
            annual_fee_amount=900,
            inventor="李四",
            applicant="××制造公司",
            category="机械制造",
            value_score=0.6
        )
    ]

    for patent in patents:
        manager.add_patent(patent)

    # 生成摘要
    summary = manager.generate_summary()

    print(f"\n📊 专利组合摘要:")
    print(f"   总专利数: {summary.total_patents}")
    print(f"   按类型统计:")
    for ptype, count in summary.by_type.items():
        print(f"      {ptype}: {count}项")
    print(f"   按状态统计:")
    for pstatus, count in summary.by_status.items():
        print(f"      {pstatus}: {count}项")
    print(f"   总价值评分: {summary.total_value:.2f}")
    print(f"   年费预算: {summary.annual_fee_budget:.0f}元")

    print(f"\n   即将到期:")
    for deadline in summary.upcoming_deadlines:
        print(f"      - {deadline['patent_id']}: {deadline['due_date']} ({deadline['amount']:.0f}元)")

    # 计算年费
    fee = manager.calculate_annual_fee(PatentType.INVENTION, 2022, 2026)
    print(f"\n   年费计算: CN专利第5年 = {fee:.0f}元")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_patent_list_manager())
