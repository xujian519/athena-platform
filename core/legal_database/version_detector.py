#!/usr/bin/env python3
"""
法规版本变更检测器
Legal Norm Version Change Detector

检测法规的修订、废止、代替等版本变更信息
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """变更类型"""

    AMENDED = "修订"  # 修订
    REPEALED = "废止"  # 废止
    REPLACED = "代替"  # 代替
    INTERPRETED = "解释"  # 解释
    CONFLICTS = "冲突"  # 冲突


@dataclass
class NormChange:
    """法规变更"""

    norm_id: str
    change_type: ChangeType
    target_norm_id: Optional[str]  # 目标法规ID(如有)
    change_date: Optional[str]
    change_basis: str  # 变更依据(文号等)
    confidence: float


class VersionDetector:
    """法规版本变更检测器"""

    # 废止模式
    REPEALED_PATTERNS = [
        r"废止本[法规条例规定]",
        r"自[本此][法规条例规定][施行之日起]*废止",
        r"本法[自由]*[本此]*[施行之日起]*废止",
        r"同时废止",
    ]

    # 修订模式
    AMENDED_PATTERNS = [
        r"于(\d{4})年(\d{1,2})月(\d{1,2})日.*修订",
        r"根据.*[修订修改]*",
        r".*[会席]通过.*[第]*[次]*修订",
        r"(\d{4})年.*修订",
    ]

    # 代替模式
    REPLACED_PATTERNS = [
        r"代替.*([一二三四五六七八九]+\.)?[法规条例规定]",
        r"同时废止.*[法规条例规定]",
    ]

    def __init__(self):
        """初始化检测器"""
        self.stats = {
            "total_norms": 0,
            "amended": 0,
            "repealed": 0,
            "replaced": 0,
        }

    def detect_changes(
        self, norm_data: dict[str, Any], all_norms: list[dict[str, Any]]
    ) -> list[NormChange]:
        """
        检测法规的变更信息

        Args:
            norm_data: 法规数据字典
            all_norms: 所有法规列表(用于匹配被引用的法规)

        Returns:
            检测到的变更列表
        """
        self.stats["total_norms"] += 1
        changes = []

        full_text = norm_data.get("full_text", "")
        norm_data.get("name", "")

        # 1. 检测废止
        for pattern in self.REPEALED_PATTERNS:
            if re.search(pattern, full_text):
                changes.append(
                    NormChange(
                        norm_id=norm_data["id"],
                        change_type=ChangeType.REPEALED,
                        target_norm_id=None,
                        change_date=self._extract_change_date(full_text),
                        change_basis=self._extract_change_basis(full_text),
                        confidence=0.90,
                    )
                )
                self.stats["repealed"] += 1
                break  # 只记录一次

        # 2. 检测修订
        for pattern in self.AMENDED_PATTERNS:
            match = re.search(pattern, full_text)
            if match:
                # 提取日期
                if match.lastindex >= 3:
                    change_date = (
                        f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
                    )
                elif match.lastindex >= 1:
                    change_date = f"{match.group(1)}-01-01"
                else:
                    change_date = self._extract_change_date(full_text)

                changes.append(
                    NormChange(
                        norm_id=norm_data["id"],
                        change_type=ChangeType.AMENDED,
                        target_norm_id=None,
                        change_date=change_date,
                        change_basis=self._extract_change_basis(full_text),
                        confidence=0.85,
                    )
                )
                self.stats["amended"] += 1
                break  # 只记录一次

        # 3. 检测代替关系
        for pattern in self.REPLACED_PATTERNS:
            match = re.search(pattern, full_text)
            if match:
                # 尝试查找被代替的法规
                target_norm = self._find_replaced_norm(match.group(0), all_norms)
                if target_norm:
                    changes.append(
                        NormChange(
                            norm_id=norm_data["id"],
                            change_type=ChangeType.REPLACED,
                            target_norm_id=target_norm["id"],
                            change_date=self._extract_change_date(full_text),
                            change_basis=self._extract_change_basis(full_text),
                            confidence=0.80,
                        )
                    )
                    self.stats["replaced"] += 1
                    break  # 只记录一次

        return changes

    def _extract_change_date(self, text: str) -> str | None:
        """提取变更日期"""
        date_pattern = r"(\d{4})年(\d{1,2})月(\d{1,2})日"
        match = re.search(date_pattern, text)
        if match:
            return f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
        return None

    def _extract_change_basis(self, text: str) -> str:
        """提取变更依据(文号)"""
        basis_pattern = r"([^。,;;]{5,30}?号)"
        match = re.search(basis_pattern, text)
        if match:
            return match.group(1)
        return ""

    def _find_replaced_norm(
        self, context: str, all_norms: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        """
        查找被代替的法规

        Args:
            context: 上下文文本
            all_norms: 所有法规列表

        Returns:
            找到的法规字典,未找到返回None
        """
        # 简化实现:基于名称匹配
        for norm in all_norms:
            if norm["name"] in context:
                return norm
        return None

    def print_stats(self) -> Any:
        """打印统计信息"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 版本变更检测统计")
        logger.info("=" * 60)
        logger.info(f"总法规数: {self.stats['total_norms']}")
        logger.info(f"修订: {self.stats['amended']}个")
        logger.info(f"废止: {self.stats['repealed']}个")
        logger.info(f"代替: {self.stats['replaced']}个")
        logger.info(f"总计: {sum(v for k, v in self.stats.items() if k != 'total_norms')}个")
        logger.info("=" * 60 + "\n")


# ========== 便捷函数 ==========


def detect_norm_changes(
    norm_data: dict[str, Any], all_norms: list[dict[str, Any]]
) -> list[NormChange]:
    """
    检测法规变更的便捷函数

    Args:
        norm_data: 法规数据字典
        all_norms: 所有法规列表

    Returns:
        检测到的变更列表
    """
    detector = VersionDetector()
    return detector.detect_changes(norm_data, all_norms)
