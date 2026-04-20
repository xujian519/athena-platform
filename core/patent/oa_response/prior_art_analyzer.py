#!/usr/bin/env python3
"""
对比文件分析器

分析目标权利要求与对比文件之间的差异。
"""
import asyncio
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from core.patent.prior_art_differ import get_prior_art_differ
from enhanced_patent_search import EnhancedPatentRetriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PriorArtAnalysis:
    """对比文件分析结果"""
    target_claims: List[str]  # 目标权利要求
    prior_art_references: Dict[str, Any]  # 对比文件信息
    undisclosed_features: List[str]  # 未公开特征
    different_parameters: Dict[str, Any]  # 参数差异
    technical_effects_diff: List[str]  # 技术效果差异
    similarity_scores: Dict[str, float]  # 相似度分数
    analysis_summary: str  # 分析摘要

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "target_claims": self.target_claims,
            "prior_art_references": self.prior_art_references,
            "undisclosed_features": self.undisclosed_features,
            "different_parameters": self.different_parameters,
            "technical_effects_diff": self.technical_effects_diff,
            "similarity_scores": self.similarity_scores,
            "analysis_summary": self.analysis_summary
        }


class PriorArtAnalyzer:
    """对比文件分析器"""

    def __init__(self):
        """初始化分析器"""
        try:
            self.differ = get_prior_art_differ()
            logger.info("✅ 对比文件差异分析器已加载")
        except Exception as e:
            logger.warning(f"⚠️ 差异分析器加载失败: {e}")
            self.differ = None

        try:
            self.retriever = EnhancedPatentRetriever()
            logger.info("✅ 专利检索器已加载")
        except Exception as e:
            logger.warning(f"⚠️ 专利检索器加载失败: {e}")
            self.retriever = None

        logger.info("✅ 对比文件分析器初始化成功")

    async def analyze_prior_art(
        self,
        target_claims: List[str],
        prior_art_references: List[str],
        current_claims_text: Optional[str] = None
    ) -> PriorArtAnalysis:
        """
        分析对比文件

        Args:
            target_claims: 目标权利要求列表
            prior_art_references: 对比文件引用列表（专利号或文献号）
            current_claims_text: 当前权利要求全文（可选）

        Returns:
            PriorArtAnalysis对象
        """
        logger.info(f"🔍 开始分析对比文件: {len(prior_art_references)} 篇")

        try:
            # 1. 检索对比文件全文
            prior_art_docs = await self._retrieve_prior_art(prior_art_references)

            # 2. 执行差异分析
            if self.differ and current_claims_text:
                diff_result = await self._analyze_differences(
                    target_claims,
                    prior_art_docs,
                    current_claims_text
                )
            else:
                # 使用简化的分析逻辑
                diff_result = self._simplified_analysis(
                    target_claims,
                    prior_art_docs
                )

            # 3. 计算相似度
            similarity_scores = await self._calculate_similarity(
                target_claims,
                prior_art_docs
            )

            # 4. 生成分析摘要
            analysis_summary = self._generate_summary(
                diff_result,
                similarity_scores
            )

            logger.info("✅ 对比文件分析完成")

            return PriorArtAnalysis(
                target_claims=target_claims,
                prior_art_references=prior_art_docs,
                undisclosed_features=diff_result.get("undisclosed_features", []),
                different_parameters=diff_result.get("different_parameters", {}),
                technical_effects_diff=diff_result.get("technical_effects_diff", []),
                similarity_scores=similarity_scores,
                analysis_summary=analysis_summary
            )

        except Exception as e:
            logger.error(f"❌ 对比文件分析失败: {e}")
            import traceback
            traceback.print_exc()

            # 返回默认分析结果
            return PriorArtAnalysis(
                target_claims=target_claims,
                prior_art_references={},
                undisclosed_features=[],
                different_parameters={},
                technical_effects_diff=[],
                similarity_scores={},
                analysis_summary="分析失败"
            )

    async def _retrieve_prior_art(
        self,
        references: List[str]
    ) -> Dict[str, Any]:
        """
        检索对比文件全文

        Args:
            references: 对比文件引用列表

        Returns:
            对比文件文档字典
        """
        prior_art_docs = {}

        for ref in references:
            try:
                # 尝试从本地数据库检索
                if self.retriever:
                    results = await self.retriever.search(
                        query=ref,
                        search_fields=["patent_id", "title"],
                        top_k=1
                    )

                    if results:
                        doc = results[0]
                        prior_art_docs[ref] = {
                            "patent_id": doc.patent_id,
                            "title": doc.title,
                            "abstract": doc.abstract,
                            "claims": doc.claims,
                            "description": doc.description if hasattr(doc, 'description') else ""
                        }
                        logger.info(f"✅ 检索到对比文件: {ref}")
                    else:
                        # 如果本地没有，记录为待检索
                        prior_art_docs[ref] = {
                            "patent_id": ref,
                            "title": "待检索",
                            "abstract": "待检索",
                            "claims": "待检索",
                            "description": "待检索"
                        }
                        logger.warning(f"⚠️ 对比文件未找到: {ref}")

            except Exception as e:
                logger.error(f"❌ 检索对比文件失败 {ref}: {e}")
                prior_art_docs[ref] = {
                    "patent_id": ref,
                    "title": "检索失败",
                    "abstract": "",
                    "claims": "",
                    "description": ""
                }

        return prior_art_docs

    async def _analyze_differences(
        self,
        target_claims: List[str],
        prior_art_docs: Dict[str, Any],
        claims_text: str
    ) -> Dict[str, Any]:
        """
        使用差异分析器分析差异

        Args:
            target_claims: 目标权利要求
            prior_art_docs: 对比文件文档
            claims_text: 权利要求全文

        Returns:
            差异分析结果
        """
        try:
            # 使用PriorArtDiffer进行差异分析
            # 这里假设对比文件保存在临时文件中
            import tempfile
            import os

            # 创建临时对比文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                for ref, doc in prior_art_docs.items():
                    f.write(f"【对比文件】{ref}\n")
                    f.write(f"标题: {doc.get('title', '')}\n")
                    f.write(f"摘要: {doc.get('abstract', '')}\n")
                    f.write(f"权利要求: {doc.get('claims', '')}\n\n")
                temp_file = f.name

            try:
                # 执行差异分析
                result = self.differ.analyze_differences(
                    target_claims,
                    temp_file
                )

                return result

            finally:
                # 清理临时文件
                if os.path.exists(temp_file):
                    os.remove(temp_file)

        except Exception as e:
            logger.error(f"❌ 差异分析失败: {e}")
            return self._simplified_analysis(target_claims, prior_art_docs)

    def _simplified_analysis(
        self,
        target_claims: List[str],
        prior_art_docs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        简化的差异分析（不使用PriorArtDiffer）

        Args:
            target_claims: 目标权利要求
            prior_art_docs: 对比文件文档

        Returns:
            简化的分析结果
        """
        undisclosed_features = []
        different_parameters = {}
        technical_effects_diff = []

        # 提取目标权利要求中的关键词
        for claim in target_claims:
            # 提取特征关键词
            features = self._extract_features_from_claim(claim)
            undisclosed_features.extend(features)

        # 与对比文件对比
        for ref, doc in prior_art_docs.items():
            doc_text = f"{doc.get('title', '')} {doc.get('abstract', '')} {doc.get('claims', '')}"

            # 检查哪些特征未公开
            for feature in undisclosed_features[:]:
                if feature.lower() in doc_text.lower():
                    undisclosed_features.remove(feature)
                else:
                    # 未公开的特征
                    pass

        return {
            "undisclosed_features": list(set(undisclosed_features)),
            "different_parameters": different_parameters,
            "technical_effects_diff": technical_effects_diff
        }

    def _extract_features_from_claim(self, claim: str) -> List[str]:
        """从权利要求中提取特征"""
        import re

        features = []

        # 提取"XX层"、"XX模块"等组件
        patterns = [
            r'([^\s，。]{2,8})(?:层|模块|单元|部件|装置)',
            r'([^\s，。]{2,8})为\s*([^\s，。]+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, claim)
            for match in matches:
                if isinstance(match, tuple):
                    features.extend(match)
                else:
                    features.append(match)

        return list(set(features))

    async def _calculate_similarity(
        self,
        target_claims: List[str],
        prior_art_docs: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        计算相似度

        Args:
            target_claims: 目标权利要求
            prior_art_docs: 对比文件文档

        Returns:
            相似度字典
        """
        similarity_scores = {}

        for ref, doc in prior_art_docs.items():
            try:
                # 简单的文本相似度计算
                doc_text = f"{doc.get('title', '')} {doc.get('abstract', '')} {doc.get('claims', '')}"

                # 计算目标权利要求与对比文件的相似度
                max_similarity = 0.0

                for claim in target_claims:
                    similarity = self._text_similarity(claim, doc_text)
                    if similarity > max_similarity:
                        max_similarity = similarity

                similarity_scores[ref] = max_similarity

            except Exception as e:
                logger.error(f"❌ 计算相似度失败 {ref}: {e}")
                similarity_scores[ref] = 0.0

        return similarity_scores

    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        from difflib import SequenceMatcher

        # 简单的序列匹配相似度
        return SequenceMatcher(None, text1, text2).ratio()

    def _generate_summary(
        self,
        diff_result: Dict[str, Any],
        similarity_scores: Dict[str, float]
    ) -> str:
        """生成分析摘要"""
        summary_parts = []

        # 未公开特征
        if diff_result.get("undisclosed_features"):
            summary_parts.append(
                f"发现 {len(diff_result['undisclosed_features'])} 个未公开特征: " +
                "、".join(diff_result["undisclosed_features"][:5])
            )

        # 相似度
        if similarity_scores:
            avg_similarity = sum(similarity_scores.values()) / len(similarity_scores)
            summary_parts.append(f"与对比文件平均相似度: {avg_similarity:.2%}")

        return "；".join(summary_parts)


async def test_prior_art_analyzer():
    """测试对比文件分析器"""
    analyzer = PriorArtAnalyzer()

    print("\n" + "="*80)
    print("🔍 对比文件分析器测试")
    print("="*80)

    # 测试数据
    target_claims = [
        "1. 一种基于深度学习的图像识别方法，其特征在于，包括：输入层，用于接收待识别图像；卷积层，用于提取图像特征；池化层，用于降维。",
        "2. 根据权利要求1所述的方法，其特征在于，所述卷积核大小为3x3。"
    ]

    prior_art_references = ["CN123456789A", "US9876543B2"]

    # 执行分析
    result = await analyzer.analyze_prior_art(
        target_claims,
        prior_art_references
    )

    # 输出结果
    print(f"\n✅ 分析完成:\n")
    print(f"未公开特征: {result.undisclosed_features}")
    print(f"相似度: {result.similarity_scores}")
    print(f"分析摘要: {result.analysis_summary}")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_prior_art_analyzer())
