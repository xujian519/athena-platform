from __future__ import annotations
from pathlib import Path

#!/usr/bin/env python3
"""
对比文件差异分析器
Prior Art Difference Analyzer

分析对比文件与目标专利的技术差异，识别未公开特征

Author: Athena平台团队
Created: 2026-01-26
Version: v1.0.0
"""

import logging
import re
from difflib import SequenceMatcher
from typing import Any

from patents.core.pdf_deep_analyzer import get_pdf_deep_analyzer

logger = logging.getLogger(__name__)


class PriorArtDiffer:
    """
    对比文件差异分析器

    功能：
    1. 识别未公开的技术特征
    2. 分析参数差异
    3. 分析技术效果差异
    4. 分析实施方式差异
    5. 生成差异报告
    """

    def __init__(self):
        """初始化差异分析器"""
        self.pdf_analyzer = get_pdf_deep_analyzer()
        logger.info("✅ 对比文件差异分析器初始化完成")

    def analyze_differences(
        self,
        target_claims: list[str],
        prior_art_path: str,
        prior_art_analysis: dict = None
    ) -> dict[str, Any]:
        """
        分析对比文件与目标专利的差异

        Args:
            target_claims: 目标专利的权利要求列表
            prior_art_path: 对比文件PDF路径
            prior_art_analysis: 已有的对比文件分析（可选）

        Returns:
            差异分析结果：
            {
                "undisclosed_features": ["特征1", "特征2"],
                "different_parameters": {...},
                "technical_effects_diff": {...},
                "implementation_diff": {...},
                "differences_summary": "差异摘要"
            }
        """
        logger.info(f"🔍 分析差异: {prior_art_path}")

        # 1. 如果没有提供分析，先分析对比文件
        if prior_art_analysis is None:
            prior_art_analysis = self.pdf_analyzer.analyze_patent_pdf(prior_art_path)

        # 2. 提取对比文件的技术特征
        prior_features = self._extract_prior_features(prior_art_analysis)

        # 3. 分析目标专利的权利要求
        target_features = self._extract_target_features(target_claims)

        # 4. 找出未公开的特征
        undisclosed = self._find_undisclosed_features(
            target_features,
            prior_features
        )

        # 5. 分析参数差异
        param_diff = self._analyze_parameter_differences(
            target_claims,
            prior_art_analysis
        )

        # 6. 分析技术效果差异
        effect_diff = self._analyze_effect_differences(
            target_claims,
            prior_art_analysis
        )

        # 7. 分析实施方式差异
        impl_diff = self._analyze_implementation_differences(
            target_claims,
            prior_art_analysis
        )

        # 8. 生成差异摘要
        summary = self._generate_summary(
            undisclosed,
            param_diff,
            effect_diff,
            impl_diff
        )

        result = {
            "undisclosed_features": undisclosed,
            "different_parameters": param_diff,
            "technical_effects_diff": effect_diff,
            "implementation_diff": impl_diff,
            "differences_summary": summary
        }

        logger.info(f"✅ 差异分析完成: 发现 {len(undisclosed)} 个未公开特征")

        return result

    def _extract_prior_features(self, prior_art: dict) -> list[str]:
        """从对比文件中提取技术特征"""
        features = []

        # 从权利要求中提取
        for claim in prior_art.get("claims", []):
            features.extend(claim.get("technical_features", []))

        # 从摘要中提取
        abstract = prior_art.get("abstract", "")
        if abstract:
            sentences = re.split(r'[，。；；]', abstract)
            for sentence in sentences:
                if 10 < len(sentence) < 80:
                    features.append(sentence)

        # 从技术领域和发明内容中提取
        for section in ["technical_field", "summary"]:
            section_text = prior_art.get(section, "")
            if section_text:
                sentences = re.split(r'[，。；；]', section_text)
                for sentence in sentences:
                    if 10 < len(sentence) < 80:
                        features.append(sentence)

        # 去重
        seen = set()
        unique_features = []
        for feature in features:
            feature_key = feature[:50]  # 使用前50个字符作为键
            if feature_key not in seen:
                seen.add(feature_key)
                unique_features.append(feature)

        return unique_features

    def _extract_target_features(self, claims: list[str]) -> list[str]:
        """从目标权利要求中提取特征"""
        features = []

        for claim in claims:
            # 按标点符号分割
            parts = re.split(r'[，。；；,;\n]', claim)

            for part in parts:
                part = part.strip()
                # 过滤过短或过长的部分，以及前缀词
                part = re.sub(r'^[一二三四五六七八九十\d]+[、.．]', '', part)
                if 10 < len(part) < 100:
                    features.append(part)

        return features

    def _find_undisclosed_features(
        self,
        target_features: list[str],
        prior_features: list[str]
    ) -> list[str]:
        """找出未在对比文件中公开的特征"""
        undisclosed = []

        for target_feature in target_features:
            is_disclosed = False

            # 与每个对比文件特征比较
            for prior_feature in prior_features:
                similarity = self._calculate_similarity(target_feature, prior_feature)

                # 如果相似度超过阈值，认为已公开
                if similarity > 0.4:  # 40%相似度阈值
                    is_disclosed = True
                    break

            if not is_disclosed:
                undisclosed.append(target_feature)

        return undisclosed

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        # 使用SequenceMatcher计算相似度
        matcher = SequenceMatcher(None, text1, text2)
        return matcher.ratio()

    def _analyze_parameter_differences(
        self,
        target_claims: list[str],
        prior_art: dict
    ) -> dict[str, Any]:
        """分析参数差异"""
        diff = {}

        # 1. 温度参数对比
        target_temp = self._extract_temperature(target_claims)
        prior_temp = prior_art.get("key_parameters", {}).get("temperature")

        if target_temp:
            diff["temperature"] = {
                "target": target_temp,
                "prior_art": prior_temp or "未公开",
                "is_disclosed": prior_temp is not None
            }

        # 2. 时间参数对比
        target_duration = self._extract_duration(target_claims)
        prior_duration = prior_art.get("key_parameters", {}).get("duration")

        if target_duration:
            diff["duration"] = {
                "target": target_duration,
                "prior_art": prior_duration or "未公开",
                "is_disclosed": prior_duration is not None
            }

        # 3. 百分比参数对比
        target_percents = self._extract_percentages(target_claims)
        prior_percents = prior_art.get("key_parameters", {}).get("percentages", [])

        if target_percents:
            diff["percentages"] = {
                "target": target_percents,
                "prior_art": prior_percents or "未公开",
                "is_disclosed": len(prior_percents) > 0
            }

        return diff

    def _extract_temperature(self, claims: list[str]) -> str:
        """从权利要求中提取温度"""
        for claim in claims:
            # 匹配：15-25℃, 15-25度, 15℃
            match = re.search(r'(\d+[\-～至—]\d+)[℃度]', claim)
            if match:
                return match.group(1) + "℃"

            match = re.search(r'(\d+)℃', claim)
            if match:
                return match.group(1) + "℃"

            match = re.search(r'(\d+)度', claim)
            if match:
                return match.group(1) + "℃"

        return ""

    def _extract_duration(self, claims: list[str]) -> str:
        """从权利要求中提取时间"""
        for claim in claims:
            # 匹配：5天, 5天, 5小时
            match = re.search(r'(\d+[\-～至—]\d+)[天日月小时min分]', claim)
            if match:
                return match.group(1)

            match = re.search(r'(\d+)[天日月小时min分]', claim)
            if match:
                return match.group(1)

        return ""

    def _extract_percentages(self, claims: list[str]) -> list[str]:
        """从权利要求中提取百分比"""
        percents = []

        for claim in claims:
            matches = re.findall(r'(\d+(?:\.\d+)?)[%％]', claim)
            percents.extend(matches)

        return list(set(percents))  # 去重

    def _analyze_effect_differences(
        self,
        target_claims: list[str],
        prior_art: dict
    ) -> dict[str, Any]:
        """分析技术效果差异"""
        # 提取目标专利的技术效果
        target_effects = []

        for claim in target_claims:
            # 查找效果关键词
            if any(keyword in claim for keyword in [
                "改善", "提升", "增强", "促进", "去除", "净化",
                "效果", "作用", "实现"
            ]):
                # 提取效果描述
                sentences = re.split(r'[，。；；]', claim)
                for sentence in sentences:
                    if 5 < len(sentence) < 60 and any(kw in sentence for kw in [
                        "改善", "提升", "增强", "促进", "去除", "净化"
                    ]):
                        target_effects.append(sentence)

        # 对比文件的技术效果
        prior_effects = prior_art.get("technical_effects", [])

        return {
            "target": target_effects[:3] if target_effects else ["四要素协同"],
            "prior_art": prior_effects[:3] if prior_effects else ["未明确"],
            "target_count": len(target_effects),
            "prior_count": len(prior_effects)
        }

    def _analyze_implementation_differences(
        self,
        target_claims: list[str],
        prior_art: dict
    ) -> dict[str, Any]:
        """分析实施方式差异"""
        # 提取关键实施方式特征
        target_impl = self._extract_implementation_features(target_claims)

        # 提取对比文件的实施方式
        prior_impl = prior_art.get("embodiments", [])

        if prior_impl:
            prior_features = prior_impl[0].get("description", "")
        else:
            prior_features = prior_art.get("abstract", "")

        # 识别差异
        return {
            "target": target_impl,
            "prior_art": prior_features[:100] if prior_features else "未公开",
            "key_difference": self._identify_key_difference(
                target_impl,
                prior_features
            )
        }

    def _extract_implementation_features(self, claims: list[str]) -> str:
        """从权利要求中提取实施方式特征"""
        features = []

        for claim in claims:
            # 查找实施方式关键词
            if any(keyword in claim for keyword in [
                "包括", "包含", "采用", "使用", "通过", "利用"
            ]):
                # 提取实施描述
                match = re.search(
                    r'(?:包括|包含|采用|使用|通过|利用)[：:：]?\s*(.+?)(?:，。|$)',
                    claim
                )
                if match:
                    features.append(match.group(1))

        return "; ".join(features[:3]) if features else "未明确"

    def _identify_key_difference(
        self,
        target_impl: str,
        prior_impl: str
    ) -> str:
        """识别关键差异"""
        # 常见技术差异类型
        diff_keywords = {
            "盐水": "是否使用盐水处理",
            "活性炭": "是否使用活性炭",
            "维生素C": "是否添加维生素C",
            "臭氧": "是否使用臭氧",
            "清水": "使用清水vs其他介质",
            "温度控制": "是否有特定温度要求",
            "阶段性处理": "是否采用阶段性工艺"
        }

        # 检查目标专利中是否有这些特征
        target_features = []
        for keyword, desc in diff_keywords.items():
            if keyword in " ".join([target_impl, prior_impl]):
                target_features.append(desc)

        return "; ".join(target_features) if target_features else "技术方案不同"

    def _generate_summary(
        self,
        undisclosed: list[str],
        param_diff: dict,
        effect_diff: dict,
        impl_diff: dict
    ) -> str:
        """生成差异摘要"""
        summary_parts = []

        # 1. 未公开特征摘要
        if undisclosed:
            summary_parts.append(
                f"发现{len(undisclosed)}个未公开特征，"
                f"包括：{undisclosed[0][:30]}...等"
            )

        # 2. 参数差异摘要
        if param_diff.get("temperature"):
            temp = param_diff["temperature"]
            if not temp["is_disclosed"]:
                summary_parts.append(
                    f"温度参数{temp['target']}未在对比文件中公开"
                )

        # 3. 技术效果差异
        if effect_diff.get("target_count", 0) > effect_diff.get("prior_count", 0):
            summary_parts.append(
                "目标专利的技术效果多于对比文件"
            )

        # 4. 实施方式差异
        if impl_diff.get("key_difference"):
            summary_parts.append(
                f"关键差异：{impl_diff['key_difference']}"
            )

        return "；".join(summary_parts) if summary_parts else "技术方案存在实质性差异"

    def analyze_all_prior_arts(
        self,
        target_claims: list[str],
        prior_art_paths: list[str]
    ) -> dict[str, dict]:
        """
        分析所有对比文件的差异

        Args:
            target_claims: 目标专利的权利要求
            prior_art_paths: 对比文件路径列表

        Returns:
            所有对比文件的分析结果
        """
        logger.info(f"📊 分析 {len(prior_art_paths)} 个对比文件")

        all_results = {}

        for i, prior_art_path in enumerate(prior_art_paths, 1):
            logger.info(f"进度: {i}/{len(prior_art_paths)}")

            try:
                result = self.analyze_differences(
                    target_claims=target_claims,
                    prior_art_path=prior_art_path
                )
                all_results[f"D{i+1}"] = result
            except Exception as e:
                logger.error(f"分析失败: {prior_art_path} - {e}")
                all_results[f"D{i+1}"] = {"error": str(e)}

        # 生成综合报告
        report = self._generate_comprehensive_report(all_results)

        all_results["_comprehensive_report"] = report

        logger.info("✅ 所有对比文件分析完成")

        return all_results

    def _generate_comprehensive_report(self, all_results: dict) -> dict:
        """生成综合分析报告"""
        total_undisclosed = 0
        key_differences = []

        for key, result in all_results.items():
            if key.startswith("D") and "error" not in result:
                total_undisclosed += len(result.get("undisclosed_features", []))

                # 收集关键差异
                if result.get("different_parameters"):
                    key_differences.append(
                        result["different_parameters"]
                    )

        return {
            "total_undisclosed_features": total_undisclosed,
            "parameter_differences_count": len(key_differences),
            "summary": f"共发现{total_undisclosed}个未公开特征，"
                     f"涉及{len(key_differences)}个参数差异"
        }


# 便捷函数
def get_prior_art_differ() -> PriorArtDiffer:
    """获取对比文件差异分析器单例"""
    return PriorArtDiffer()


# 测试代码
if __name__ == "__main__":
    # 测试差异分析
    differ = get_prior_art_differ()

    # 模拟目标权利要求
    target_claims = [
        "1. 一种吊水净化处理罗非鱼泥腥味的方法，其特征在于："
        "包括盐水处理步骤，水温15-25℃，盐度1-2%，"
        "在盐水中添加0.1%高稳维生素C和100g/m³活性炭。",
        "2. 根据权利要求1所述的方法，其特征在于："
        "所述盐水水温为15-20℃。"
    ]

    # 测试对比文件
    prior_art_path = "data/temp_oa_analysis/对比文件1_CN112616756A.pdf"

    if Path(prior_art_path).exists():
        result = differ.analyze_differences(
            target_claims=target_claims,
            prior_art_path=prior_art_path
        )

        print("\n=== 差异分析结果 ===")
        print(f"未公开特征: {len(result['undisclosed_features'])}")
        for feature in result['undisclosed_features'][:3]:
            print(f"  - {feature}")

        print(f"\n参数差异: {result['different_parameters']}")
        print(f"\n技术效果差异: {result['technical_effects_diff']}")
        print(f"\n实施方式差异: {result['implementation_diff']}")
        print(f"\n差异摘要: {result['differences_summary']}")
