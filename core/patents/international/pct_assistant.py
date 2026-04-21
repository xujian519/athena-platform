#!/usr/bin/env python3
"""
PCT申请辅助

提供PCT国际申请的完整支持。
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PCTPhase(Enum):
    """PCT阶段"""
    INTERNATIONAL = "international"  # 国际阶段
    NATIONAL = "national"  # 国家阶段


class ApplicationType(Enum):
    """申请类型"""
    PCT = "pct"  # PCT申请
    PARIS_CONVENTION = "paris_convention"  # 巴黎公约
    DIRECT = "direct"  # 直接申请


@dataclass
class PCTApplication:
    """PCT申请"""
    patent_id: str  # 中国申请号
    title: str  # 发明名称
    applicant: str  # 申请人
    inventor: str  # 发明人
    filing_date: str  # 申请日期
    priority_date: str  # 优先权日期
    abstract: str  # 摘要
    claims: List[str]  # 权利要求
    description: str  # 说明书
    drawings: List[str] = field(default_factory=list)  # 附图
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "patent_id": self.patent_id,
            "title": self.title,
            "applicant": self.applicant,
            "inventor": self.inventor,
            "filing_date": self.filing_date,
            "priority_date": self.priority_date,
            "abstract": self.abstract,
            "claims": self.claims,
            "description": self.description,
            "drawings": self.drawings,
            "metadata": self.metadata
        }


class PCTAssistant:
    """PCT申请辅助器"""

    def __init__(self):
        """初始化辅助器"""
        self.pct_guidelines = self._load_pct_guidelines()
        logger.info("✅ PCT申请辅助器初始化成功")

    def _load_pct_guidelines(self) -> Dict[str, Any]:
        """加载PCT指南"""
        return {
            "time_limits": {
                "international_filing": 12,  # 优先权日起12个月内
                "international_search": 16,  # 优先权日起16个月内
                "international_preliminary_examination": 22,  # 优先权日起22个月内
                "national_entry": 30,  # 优先权日起30个月内
                "national_phase_deadline": 31  # 国家阶段截止
            },
            "fees": {
                "international_filing": 1330,  # 瑞郎（约9300元）
                "international_search": 1770,  # 瑞郎（约12400元）
                "preliminary_examination": 1770,  # 瑞郎（约12400元）
                "national_entry": "varies"  # 各国不同
            },
            "required_documents": [
                "请求书",
                "说明书",
                "权利要求书",
                "附图（如有）",
                "摘要",
                "优先权文件"
            ]
        }

    def prepare_pct_application(
        self,
        chinese_app: Dict[str, Any],
        target_countries: List[str]
    ) -> PCTApplication:
        """
        准备PCT申请

        Args:
            chinese_app: 中国专利申请信息
            target_countries: 目标国家列表

        Returns:
            PCTApplication对象
        """
        logger.info(f"🌍 准备PCT申请: {chinese_app.get('patent_id')}")

        # 计算时间期限
        filing_date = chinese_app.get("filing_date", "")
        priority_date = chinese_app.get("filing_date", "")

        # 检查期限
        time_check = self._check_time_limits(filing_date)
        if not time_check["can_file"]:
            logger.warning(f"⚠️ {time_check['reason']}")

        # 创建PCT申请
        pct_app = PCTApplication(
            patent_id=chinese_app.get("patent_id", ""),
            title=chinese_app.get("title", ""),
            applicant=chinese_app.get("applicant", ""),
            inventor=chinese_app.get("inventor", ""),
            filing_date=filing_date,
            priority_date=priority_date,
            abstract=chinese_app.get("abstract", ""),
            claims=chinese_app.get("claims", []),
            description=chinese_app.get("description", ""),
            drawings=chinese_app.get("drawings", []),
            metadata={
                "target_countries": target_countries,
                "time_check": time_check,
                "estimated_fees": self._estimate_fees(target_countries)
            }
        )

        logger.info("✅ PCT申请准备完成")
        return pct_app

    def _check_time_limits(self, filing_date: str) -> Dict[str, Any]:
        """检查时间期限"""
        try:
            file_dt = datetime.strptime(filing_date, "%Y-%m-%d")
            now = datetime.now()

            months_elapsed = (now.year - file_dt.year) * 12 + (now.month - file_dt.month)

            if months_elapsed <= 12:
                return {"can_file": True, "phase": "国际阶段", "months_elapsed": months_elapsed}
            else:
                return {
                    "can_file": False,
                    "reason": f"已超过12个月期限（{months_elapsed}个月）"
                }
        except Exception as e:
            return {"can_file": False, "reason": f"日期解析错误: {e}"}

    def _estimate_fees(self, target_countries: List[str]) -> Dict[str, float]:
        """估算费用"""
        base_fee = 1330 + 1770  # 国际申请+检索费
        country_fees = len(target_countries) * 5000  # 平均每国5000元

        return {
            "international_phase": base_fee,
            "national_phase": country_fees,
            "total": base_fee + country_fees
        }

    def generate_checklist(self, pct_app: PCTApplication) -> Dict[str, List[str]]:
        """生成检查清单"""
        return {
            "documents": self.pct_guidelines["required_documents"],
            "timeline": [
                f"优先权日起12个月内：提交国际申请",
                f"优先权日起16个月内：收到国际检索报告",
                f"优先权日起22个月内：国际初步审查（可选）",
                f"优先权日起30个月内：进入国家阶段"
            ],
            "fees": [
                f"国际申请费：约{self.pct_guidelines['fees']['international_filing']}瑞郎",
                f"国际检索费：约{self.pct_guidelines['fees']['international_search']}瑞郎",
                f"初步审查费：约{self.pct_guidelines['fees']['preliminary_examination']}瑞郎",
                f"国家阶段费：各国不同，预计{len(pct_app.metadata.get('target_countries', [])) * 5000}元"
            ],
            "target_countries": pct_app.metadata.get("target_countries", [])
        }


async def test_pct_assistant():
    """测试PCT申请辅助器"""
    assistant = PCTAssistant()

    print("\n" + "="*80)
    print("🌍 PCT申请辅助器测试")
    print("="*80)

    # 测试数据
    chinese_app = {
        "patent_id": "CN202010123456.7",
        "title": "基于人工智能的智能控制系统",
        "applicant": "××科技公司",
        "inventor": "张三",
        "filing_date": "2025-04-15",
        "abstract": "本发明涉及一种基于深度学习的智能控制方法...",
        "claims": ["1. 一种智能控制方法，其特征在于..."],
        "description": "本发明提供了一种智能控制系统..."
    }

    target_countries = ["美国", "欧洲", "日本"]

    # 准备PCT申请
    pct_app = assistant.prepare_pct_application(chinese_app, target_countries)

    print(f"\n✅ PCT申请准备完成:")
    print(f"   专利号: {pct_app.patent_id}")
    print(f"   标题: {pct_app.title}")
    print(f"   优先权日期: {pct_app.priority_date}")
    print(f"   目标国家: {', '.join(target_countries)}")

    # 生成检查清单
    checklist = assistant.generate_checklist(pct_app)

    print(f"\n📋 检查清单:")
    print(f"   必备文档:")
    for doc in checklist["documents"][:3]:
        print(f"      - {doc}")
    print(f"\n   时间节点:")
    for item in checklist["timeline"][:2]:
        print(f"      - {item}")
    print(f"\n   费用估算:")
    for fee in checklist["fees"][:2]:
        print(f"      - {fee}")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_pct_assistant())
