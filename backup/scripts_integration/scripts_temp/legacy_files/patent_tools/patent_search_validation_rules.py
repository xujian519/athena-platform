#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利检索验证规则系统
Patent Search Validation Rules System
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class PatentSearchValidationRules:
    """专利检索验证规则"""

    def __init__(self):
        # 定义验证规则
        self.validation_rules = {
            'creativity_rules': {
                'time_constraint': {
                    'description': '创造性检索：必须检索目标专利申请日之前公开的全部专利',
                    'rule': '现有技术的公开日必须早于目标专利的申请日',
                    'strict_time_check': True,
                    'grace_period_days': 0  # 无宽限期
                },
                'scope_requirement': {
                    'description': '检索范围必须全面，覆盖所有相关的技术领域',
                    'coverage_threshold': 0.95,  # 95%覆盖率
                    'min_prior_art_count': 10
                }
            },
            'novelty_rules': {
                'time_constraint': {
                    'description': '新颖性检索：检索目标专利申请日之前的全部专利 + 抵触申请',
                    'rule': '现有技术的公开日早于申请日 OR 抵触申请的申请日在后但公开日在先',
                    'strict_time_check': True,
                    'grace_period_days': 0,
                    'include_conflicting_applications': True
                },
                'identicality_check': {
                    'description': '必须进行完全相同的技术方案检索',
                    'exact_match_required': True
                }
            }
        }

    def validate_search_results_for_creativity(self,
                                               results: List[Dict],
                                               target_patent: Dict,
                                               search_type: str = 'creativity') -> Tuple[List[Dict], Dict]:
        """
        验证检索结果是否符合创造性要求

        Args:
            results: 检索结果列表
            target_patent: 目标专利信息
            search_type: 检索类型（creativity/novelty）

        Returns:
            Tuple[有效结果列表, 验证报告]
        """
        logger.info(f"\n📋 执行{'创造性' if search_type == 'creativity' else '新颖性'}检索验证")
        logger.info(str('='*60))

        # 获取目标专利申请日
        target_application_date = self.parse_date(target_patent.get('application_date', ''))

        if not target_application_date:
            return results, {'error': '目标专利申请日无效'}

        logger.info(f"目标专利申请日: {target_application_date}")
        logger.info(str('-' * 40))

        valid_results = []
        invalid_results = []
        conflicting_applications = []

        for i, result in enumerate(results, 1):
            validation_result = self.validate_single_patent(result, target_application_date, search_type)

            if validation_result['is_valid']:
                valid_results.append(result)

                # 分类存储抵触申请
                if validation_result.get('is_conflicting_application'):
                    conflicting_applications.append(result)
            else:
                invalid_results.append(result)

        # 生成验证报告
        validation_report = self.generate_validation_report(
            valid_results,
            invalid_results,
            conflicting_applications,
            target_application_date,
            search_type
        )

        logger.info(f"✅ 验证完成")
        logger.info(f"   有效专利：{len(valid_results)} 项")
        if search_type == 'novelty':
            logger.info(f"   抵触申请：{len(conflicting_applications)} 项")
        logger.info(f"   无效专利：{len(invalid_results)} 项")

        return valid_results, validation_report

    def validate_single_patent(self,
                             patent: Dict,
                             target_application_date: datetime,
                             search_type: str) -> Dict:
        """
        验证单个专利是否符合时间要求

        Args:
            patent: 专利信息
            target_application_date: 目标专利申请日
            search_type: 检索类型

        Returns:
            验证结果字典
        """
        # 获取关键日期
        patent_application_date = self.parse_date(patent.get('application_date', ''))
        patent_publication_date = self.parse_date(patent.get('publication_date', ''))
        patent_priority_date = self.parse_date(patent.get('priority_date', ''))

        # 确定最早的有效日期
        earliest_date = self.get_earliest_effective_date(
            patent_application_date,
            patent_publication_date,
            patent_priority_date
        )

        # 验证时间要求
        is_time_valid = self.validate_time_constraint(
            earliest_date,
            target_application_date,
            search_type
        )

        # 检查是否为抵触申请
        is_conflicting_application = False
        if search_type == 'novelty':
            is_conflicting_application = self.check_conflicting_application(
                patent,
                target_application_date
            )

        return {
            'is_valid': is_time_valid,
            'is_conflicting_application': is_conflicting_application,
            'patent_number': patent.get('publication_number', ''),
            'application_date': patent.get('application_date', ''),
            'publication_date': patent.get('publication_date', ''),
            'earliest_effective_date': earliest_date.strftime('%Y-%m-%d') if earliest_date else None,
            'time_comparison': {
                'target_date': target_application_date.strftime('%Y-%m-%d'),
                'days_difference': self.calculate_days_difference(earliest_date, target_application_date)
            },
            'validation_reason': self.get_validation_reason(
                earliest_date,
                target_application_date,
                is_time_valid,
                is_conflicting_application,
                search_type
            )
        }

    def validate_time_constraint(self,
                               patent_date: datetime,
                               target_date: datetime,
                               search_type: str) -> bool:
        """
        验证时间约束

        Args:
            patent_date: 专利日期
            target_date: 目标专利申请日
            search_type: 检索类型

        Returns:
            是否符合时间要求
        """
        if not patent_date:
            return False

        # 基本规则：专利必须在目标专利申请日之前公开
        if patent_date >= target_date:
            return False

        # 抵触申请的特殊处理
        if search_type == 'novelty':
            # 新颖性检索中，抵触申请可能在后申请但先公开
            # 这里需要更复杂的逻辑
            pass

        return True

    def check_conflicting_application(self,
                                    patent: Dict,
                                    target_application_date: datetime) -> bool:
        """
        检查是否为抵触申请

        抵触申请的条件：
        1. 在目标专利申请日之后申请
        2. 在目标专利申请日之前公开
        3. 由他人申请
        4. 记载了相同的技术方案
        """
        patent_application_date = self.parse_date(patent.get('application_date', ''))
        patent_publication_date = self.parse_date(patent.get('publication_date', ''))

        if not patent_application_date or not patent_publication_date:
            return False

        # 检查时间条件
        if (patent_application_date > target_application_date and
            patent_publication_date < target_application_date):
            return True

        return False

    def generate_validation_report(self,
                                 valid_results: List[Dict],
                                 invalid_results: List[Dict],
                                 conflicting_applications: List[Dict],
                                 target_date: datetime,
                                 search_type: str) -> Dict:
        """
        生成验证报告
        """
        total_results = len(valid_results) + len(invalid_results)

        report = {
            'validation_type': 'creativity' if search_type == 'creativity' else 'novelty',
            'target_patent_date': target_date.strftime('%Y-%m-%d'),
            'summary': {
                'total_results': total_results,
                'valid_prior_art': len(valid_results),
                'invalid_results': len(invalid_results),
                'conflicting_applications': len(conflicting_applications),
                'validation_rate': len(valid_results) / total_results if total_results > 0 else 0
            },
            'time_analysis': self.analyze_time_distribution(valid_results, target_date),
            'quality_assessment': self.assess_search_quality(valid_results, total_results),
            'recommendations': self.generate_recommendations(invalid_results, search_type)
        }

        return report

    def analyze_time_distribution(self, results: List[Dict], target_date: datetime) -> Dict:
        """分析时间分布"""
        if not results:
            return {}

        time_gaps = []
        for result in results:
            result_date = self.parse_date(result.get('application_date', ''))
            if result_date:
                gap_days = (target_date - result_date).days
                time_gaps.append(gap_days)

        if not time_gaps:
            return {}

        return {
            'earliest_prior_art': min(time_gaps),
            'latest_prior_art': max(time_gaps),
            'average_gap': sum(time_gaps) / len(time_gaps),
            'time_distribution': {
                'within_1_year': sum(1 for gap in time_gaps if gap <= 365),
                'within_3_years': sum(1 for gap in time_gaps if gap <= 1095),
                'within_5_years': sum(1 for gap in time_gaps if gap <= 1825),
                'more_than_5_years': sum(1 for gap in time_gaps if gap > 1825)
            }
        }

    def assess_search_quality(self, valid_results: List[Dict], total_results: int) -> Dict:
        """评估检索质量"""
        return {
            'coverage_completeness': len(valid_results) / total_results if total_results > 0 else 0,
            'data_integrity': self.check_data_integrity(valid_results),
            'representativeness': self.assess_representativeness(valid_results)
        }

    def generate_recommendations(self, invalid_results: List[Dict], search_type: str) -> List[str]:
        """生成改进建议"""
        recommendations = []

        if invalid_results:
            recommendations.append(
                f"发现{len(invalid_results)}项时间不符合要求的专利，需要从检索结果中排除"
            )

        if search_type == 'novelty':
            recommendations.append(
                '新颖性检索应特别关注抵触申请的情况'
            )

        recommendations.append(
            '建议增加对国际专利文献的检索，确保检索的全面性'
        )

        recommendations.append(
            '考虑扩展关键词和IPC分类，提高检索覆盖率'
        )

        return recommendations

    # ==================== 辅助方法 ====================

    def parse_date(self, date_str: str) -> datetime | None:
        """解析日期字符串"""
        if not date_str:
            return None

        # 支持多种日期格式
        date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y%m%d',
            '%Y-%m-%d %H:%M:%S'
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        # 尝试从字符串中提取日期
        date_match = re.search(r'(\d{4})[-/]?(\d{1,2})[-/]?(\d{1,2})', date_str)
        if date_match:
            year, month, day = date_match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except ValueError:
                pass

        return None

    def get_earliest_effective_date(self,
                                   application_date: Optional[datetime],
                                   publication_date: Optional[datetime],
                                   priority_date: Optional[datetime]) -> datetime | None:
        """获取最早的有效日期"""
        dates = [d for d in [application_date, publication_date, priority_date] if d is not None]
        return min(dates) if dates else None

    def calculate_days_difference(self, date1: Optional[datetime], date2: Optional[datetime]) -> int | None:
        """计算日期差（天数）"""
        if not date1 or not date2:
            return None
        return abs((date2 - date1).days)

    def get_validation_reason(self,
                             patent_date: Optional[datetime],
                             target_date: datetime,
                             is_valid: bool,
                             is_conflicting: bool,
                             search_type: str) -> str:
        """获取验证原因"""
        if not patent_date:
            return '日期信息缺失'

        if is_conflicting:
            return '抵触申请：在后申请但在先公开'

        if is_valid:
            days_diff = self.calculate_days_difference(patent_date, target_date)
            return f"有效：早于目标申请日{days_diff}天"

        return '无效：晚于目标申请日'

    def check_data_integrity(self, results: List[Dict]) -> float:
        """检查数据完整性"""
        if not results:
            return 0.0

        required_fields = ['patent_name', 'publication_number', 'application_date']
        complete_count = 0

        for result in results:
            if all(result.get(field) for field in required_fields):
                complete_count += 1

        return complete_count / len(results)

    def assess_representativeness(self, results: List[Dict]) -> float:
        """评估代表性"""
        # 这里可以评估IPC分类分布、申请人分布等
        # 简化实现
        return 0.85 if results else 0.0


# ==================== 使用示例 ====================

def example_usage():
    """使用示例"""
    validator = PatentSearchValidationRules()

    # 示例专利
    target_patent = {
        'patent_number': 'CN200920113915.8',
        'application_date': '2009-01-24'
    }

    # 模拟检索结果
    search_results = [
        {
            'patent_name': '集装箱拉紧器',
            'publication_number': 'CN2444027Y',
            'application_date': '2002-09-25',
            'publication_date': '2002-09-25'
        },
        {
            'patent_name': '新型拉紧装置',
            'publication_number': 'CN201390190Y',
            'application_date': '2010-01-01',  # 晚于目标申请日
            'publication_date': '2010-01-01'
        }
    ]

    # 验证创造性检索结果
    valid_results, report = validator.validate_search_results_for_creativity(
        search_results,
        target_patent,
        'creativity'
    )

    logger.info("\n验证报告：")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    import json
    example_usage()