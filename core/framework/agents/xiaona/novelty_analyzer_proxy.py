"""
新颖性分析专用代理

专注于专利新颖性分析，提供全面的新颖性评估。
集成LLM智能分析能力，支持降级到规则-based分析。
"""

import json
import logging
import re
from typing import Any, Optional

from core.framework.agents.xiaona.base_component import BaseXiaonaComponent

logger = logging.getLogger(__name__)


class NoveltyAnalyzerProxy(BaseXiaonaComponent):
    """
    新颖性分析专用代理

    核心能力：
    - 技术特征提取（LLM增强）
    - 对比文件分析（LLM增强）
    - 新颖性判断（LLM增强）
    - 单独对比原则
    - 同一性判断
    - 自动降级机制
    """

    def _initialize(self) -> str:
        """初始化新颖性分析代理"""
        self.agent_id = "novelty_analyzer"
        self._register_capabilities([

            {
                "name": "individual_comparison",
                "description": "单独对比",
                "input_types": ["目标专利", "对比文件"],
                "output_types": ["新颖性分析报告"],
                "estimated_time": 20.0,
            },
            {
                "name": "difference_identification",
                "description": "区别特征识别",
                "input_types": ["技术特征", "对比文件"],
                "output_types": ["比对结果"],
                "estimated_time": 15.0,
            },
            {
                "name": "novelty_determination",
                "description": "新颖性判断",
                "input_types": ["两个技术方案"],
                "output_types": ["同一性结论"],
                "estimated_time": 10.0,
            },
            {
                "name": "prior_art_search",
                "description": "现有技术检索",
                "input_types": ["技术特征"],
                "output_types": ["对比文件列表"],
                "estimated_time": 30.0,
            },
        )

        # 导入提示词
        try:
            from prompts.agents.xiaona.novelty_analyzer_prompts import (
                NOVELTY_ANALYSIS_SYSTEM_PROMPT,
                build_feature_comparison_prompt,
                build_novelty_analysis_prompt,
                build_novelty_judgment_prompt,
            )
            self.NOVELTY_ANALYSIS_SYSTEM_PROMPT = NOVELTY_ANALYSIS_SYSTEM_PROMPT
            self.build_novelty_analysis_prompt = build_novelty_analysis_prompt
            self.build_feature_comparison_prompt = build_feature_comparison_prompt
            self.build_novelty_judgment_prompt = build_novelty_judgment_prompt
        except ImportError as e:
            self.logger.warning(f"提示词模块导入失败: {e}，将使用内置提示词")
            self.NOVELTY_ANALYSIS_SYSTEM_PROMPT = self._get_default_system_prompt()
            self.build_novelty_analysis_prompt = self._default_build_novelty_analysis_prompt
            self.build_feature_comparison_prompt = self._default_build_feature_comparison_prompt
            self.build_novelty_judgment_prompt = self._default_build_novelty_judgment_prompt

    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示词"""
        return """
你是一位专业的专利新颖性分析专家，具备深厚的专利法知识和丰富的审查经验。

你的职责是：
1. 对比文件技术特征分析
2. 区别技术特征识别
3. 新颖性判断（单独对比原则）
4. 置信度评估

请以专业、严谨的态度进行审查，并提供明确的改进建议。
输出必须是严格的JSON格式，不要添加任何额外的文字说明。
"""

    def _default_build_novelty_analysis_prompt(
        self,
        patent_data: dict,
        reference_docs: list

    )]) -> str:
        """默认新颖性分析提示词构建"""
        return f"""# 任务：专利新颖性分析

## 目标专利
专利号：{patent_data.get('patent_id', '未知')}
权利要求：{patent_data.get('claims', '未提供')}

## 对比文件
共{len(reference_docs)}篇

请分析新颖性并输出JSON结果。
"""

    def _default_build_feature_comparison_prompt(
        self,
        target_features: dict,
        reference_doc: dict
    ) -> str:
        """默认特征对比提示词构建"""
        return f"""# 任务：特征对比

目标特征：{json.dumps(target_features, ensure_ascii=False)}
对比文件：{reference_doc.get('doc_id', '未知')}

请对比分析并输出JSON结果。
"""

    def _default_build_novelty_judgment_prompt(
        self,
        distinguishing_features: list,
        target_features: dict
    ) -> str:
        """默认新颖性判断提示词构建"""
        return f"""# 任务：新颖性判断

区别特征数：{len(distinguishing_features)}
总特征数：{sum(len(f) for f in target_features.values())}

请判断新颖性并输出JSON结果。
"""

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return self.NOVELTY_ANALYSIS_SYSTEM_PROMPT

    async def execute(self, context) -> str:
        """
        执行智能体任务

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        # 根据任务类型执行相应的分析
        task_type = context.config.get("task_type", "novelty_analysis")

        if task_type == "novelty_analysis":
            return await self.analyze_novelty(
                context.input_data,
                context.config.get("analysis_mode", "standard")
            )
        elif task_type == "feature_comparison":
            return await self._compare_with_reference(
                context.input_data.get("target_features"),
                context.input_data.get("reference_doc"),
                context.config.get("comparison_mode", "individual")
            )
        elif task_type == "novelty_judgment":
            return await self._judge_novelty(
                context.input_data.get("novel_features"),
                context.input_data.get("target_features")
            )
        else:
            # 默认执行完整新颖性分析
            return await self.analyze_novelty(
                context.input_data,
                context.config.get("analysis_mode", "standard")
            )

    async def analyze_novelty(
        self,
        patent_data: Optional[dict[str, Any],]

        analysis_mode: str = "standard"
    ) -> dict[str, Any]:
        """
        分析新颖性（LLM增强版本）

        Args:
            patent_data: 专利数据（包含prior_art_references等）
            analysis_mode: 分析模式（comprehensive/quick）

        Returns:
            新颖性分析结果
        """
        reference_docs = patent_data.get("prior_art_references", [])

        # 尝试使用LLM分析
        try:
            prompt = self.build_novelty_analysis_prompt(patent_data, reference_docs)
            response = await self._call_llm_with_fallback(
                prompt=prompt,
                system_prompt=self.NOVELTY_ANALYSIS_SYSTEM_PROMPT,
                task_type="novelty_analysis"
            )

            # 解析LLM响应
            return self._parse_novelty_analysis_response(response, patent_data)

        except Exception as e:
            self.logger.warning(f"LLM新颖性分析失败: {e}，使用规则-based分析")
            return await self._analyze_novelty_by_rules(patent_data, analysis_mode)

    async def _analyze_novelty_by_rules(
        self,
        patent_data: Optional[dict[str, Any],]

        analysis_mode: str
    ) -> dict[str, Any]:
        """
        基于规则的新颖性分析（降级方案）

        Args:
            patent_data: 专利数据
            analysis_mode: 分析模式

        Returns:
            新颖性分析结果
        """
        reference_docs = patent_data.get("prior_art_references", [])

        # 1. 提取目标专利的技术特征
        target_features = await self._extract_all_features(patent_data)

        # 2. 逐一比对对比文件
        comparison_results = []
        for ref_doc in reference_docs:
            result = await self._compare_with_reference(
                target_features,
                ref_doc,
                "individual"
            )
            comparison_results.append(result)

        # 3. 识别区别技术特征
        novel_features = await self._identify_novel_features(
            target_features,
            comparison_results
        )

        # 4. 判断新颖性
        novelty_conclusion = await self._judge_novelty(
            novel_features,
            target_features
        )

        return {
            "patent_id": patent_data.get("patent_id", "未知"),
            "analysis_mode": analysis_mode,
            "analysis_method": "rule-based",
            "target_features": target_features,
            "individual_comparisons": comparison_results,
            "distinguishing_features": novel_features,
            "novelty_conclusion": novelty_conclusion["conclusion"],
            "confidence_score": self._calculate_novelty_confidence(novel_features, target_features),
            "analyzed_at": self._get_timestamp(),
        }

    def _parse_novelty_analysis_response(
        self,
        response: str,
        patent_data: Optional[dict[str, Any]]

    ) -> dict[str, Any]:
        """解析新颖性分析LLM响应"""
        try:
            # 提取JSON
            json_match = re.search(r'```json\s*([\s\S]*?)```', response)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = response.strip()

            result = json.loads(json_str)

            # 添加元数据
            result["patent_id"] = patent_data.get("patent_id", "未知")
            result["analysis_mode"] = "standard"
            result["analysis_method"] = "llm"
            result["analyzed_at"] = self._get_timestamp()

            # 验证必需字段
            required_fields = []

                "individual_comparisons",
                "distinguishing_features",
                "novelty_conclusion",
                "confidence_assessment"
            
            for field in required_fields:
                if field not in result:
                    self.logger.warning(f"LLM响应缺少字段: {field}")
                    result[field] = None

            return result

        except (json.JSONDecodeError, Exception) as e:
            self.logger.error(f"解析新颖性分析响应失败: {e}")
            raise

    async def _compare_with_reference(
        self,
        target_features: Optional[dict[str, Any],]

        reference_doc: Optional[dict[str, Any],]

        comparison_mode: str
    ) -> dict[str, Any]:
        """
        与单个对比文件比对（LLM增强版本）

        Args:
            target_features: 目标特征
            reference_doc: 对比文件
            comparison_mode: 比对模式

        Returns:
            比对结果
        """
        # 尝试使用LLM分析
        try:
            prompt = self.build_feature_comparison_prompt(target_features, reference_doc)
            response = await self._call_llm_with_fallback(
                prompt=prompt,
                system_prompt=self.NOVELTY_ANALYSIS_SYSTEM_PROMPT,
                task_type="feature_comparison"
            )

            # 解析LLM响应
            return self._parse_feature_comparison_response(response, reference_doc)

        except Exception as e:
            self.logger.warning(f"LLM特征对比失败: {e}，使用规则-based对比")
            return await self._compare_by_rules(target_features, reference_doc)

    async def _compare_by_rules(
        self,
        target_features: Optional[dict[str, Any],]

        reference_doc: Optional[dict[str, Any]]

    ) -> dict[str, Any]:
        """
        基于规则的特征对比（降级方案）

        Args:
            target_features: 目标特征
            reference_doc: 对比文件

        Returns:
            比对结果
        """
        ref_features = reference_doc.get("features", {})

        # 逐一特征比对
        feature_comparison = []
        for category, features in target_features.items():
            for feature in features:
                is_disclosed = feature in ref_features.get(category, [])
                feature_comparison.append({
                    "feature": feature,
                    "category": category,
                    "disclosed": is_disclosed,
                    "disclosed_in": reference_doc.get("doc_id", "未知"),
                })

        # 统计公开情况
        disclosed_count = sum(1 for f in feature_comparison if f["disclosed"])
        total_count = len(feature_comparison)

        return {
            "reference_id": reference_doc.get("doc_id", "未知"),
            "reference_title": reference_doc.get("title", ""),
            "feature_comparison": feature_comparison,
            "disclosed_count": disclosed_count,
            "undisclosed_count": total_count - disclosed_count,
            "total_count": total_count,
            "disclosure_ratio": disclosed_count / total_count if total_count > 0 else 0,
            "overall_assessment": f"该对比文件公开了{disclosed_count}个技术特征",
        }

    def _parse_feature_comparison_response(
        self,
        response: str,
        reference_doc: Optional[dict[str, Any]]

    ) -> dict[str, Any]:
        """解析特征对比LLM响应"""
        try:
            # 提取JSON
            json_match = re.search(r'```json\s*([\s\S]*?)```', response)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = response.strip()

            result = json.loads(json_str)

            # 验证必需字段
            required_fields = []

                "reference_id",
                "feature_comparison",
                "disclosed_count",
                "undisclosed_count",
                "total_count",
                "disclosure_ratio"
            
            for field in required_fields:
                if field not in result:
                    result[field] = None

            return result

        except (json.JSONDecodeError, Exception) as e:
            self.logger.error(f"解析特征对比响应失败: {e}")
            raise

    async def _judge_novelty(
        self,
        novel_features: Optional[list[dict[str, Any]],]

        target_features: Optional[dict[str, Any]]

    ) -> dict[str, Any]:
        """
        判断新颖性（LLM增强版本）

        Args:
            novel_features: 新颖特征列表
            target_features: 目标特征

        Returns:
            新颖性判断结果
        """
        # 尝试使用LLM分析
        try:
            prompt = self.build_novelty_judgment_prompt(novel_features, target_features)
            response = await self._call_llm_with_fallback(
                prompt=prompt,
                system_prompt=self.NOVELTY_ANALYSIS_SYSTEM_PROMPT,
                task_type="novelty_judgment"
            )

            # 解析LLM响应
            return self._parse_novelty_judgment_response(response)

        except Exception as e:
            self.logger.warning(f"LLM新颖性判断失败: {e}，使用规则-based判断")
            return self._judge_novelty_by_rules(novel_features, target_features)

    def _judge_novelty_by_rules(
        self,
        novel_features: Optional[list[dict[str, Any]],]

        target_features: Optional[dict[str, Any]]

    ) -> dict[str, Any]:
        """
        基于规则的新颖性判断（降级方案）

        Args:
            novel_features: 新颖特征列表
            target_features: 目标特征

        Returns:
            新颖性判断结果
        """
        total_features = sum(len(f) for f in target_features.values())
        novel_count = len(novel_features)

        has_novelty = novel_count > 0
        novelty_ratio = novel_count / total_features if total_features > 0 else 0

        # 判断新颖性强度
        if novelty_ratio > 0.3:
            strength = "strong"
        elif novelty_ratio > 0.1:
            strength = "medium"
        elif novel_count > 0:
            strength = "weak"
        else:
            strength = "none"

        return {
            "has_novelty": has_novelty,
            "novel_features_count": novel_count,
            "total_features_count": total_features,
            "novelty_ratio": novelty_ratio,
            "conclusion": "具备新颖性" if has_novelty else "不具备新颖性",
            "strength": strength,
            "reasoning": f"共有{novel_count}个区别技术特征未被公开" if has_novelty else "所有技术特征均被公开",
            "legal_basis": "专利法第22条第2款",
        }

    def _parse_novelty_judgment_response(self, response: str) -> dict[str, Any]:
        """解析新颖性判断LLM响应"""
        try:
            # 提取JSON
            json_match = re.search(r'```json\s*([\s\S]*?)```', response)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = response.strip()

            result = json.loads(json_str)

            # 验证必需字段
            required_fields = []

                "has_novelty",
                "novelty_conclusion",
                "strength",
                "reasoning"
            
            for field in required_fields:
                if field not in result:
                    result[field] = None

            return result

        except (json.JSONDecodeError, Exception) as e:
            self.logger.error(f"解析新颖性判断响应失败: {e}")
            raise

    async def _extract_all_features(
        self,
        patent: Optional[dict[str, Any]]

    ) -> dict[str, Any]:
        """提取所有技术特征"""
        claims_text = patent.get("claims", "")

        # 简化版特征提取
        return {
            "essential": self._extract_features_by_type(claims_text, ["必要", "包括"]),
            "additional": self._extract_features_by_type(claims_text, ["其特征在于", "进一步"]),
            "functional": self._extract_features_by_type(claims_text, ["用于", "实现"]),
            "structural": self._extract_features_by_type(claims_text, ["设置", "配置"]),
        }

    def _extract_features_by_type(
        self,
        claims_text: str,
        keywords: Optional[list[str]]

    ) -> list[str]:
        """根据关键词提取特征"""
        import re

        features = []
        for keyword in keywords:
            # 简化提取：查找包含关键词的句子
            pattern = re.compile(f'[^。]*{keyword}[^。]*。')
            matches = pattern.findall(claims_text)
            features.extend(matches[:2])  # 每个关键词最多提取2个

        return features if features else [f"基于关键词{keywords[0]}的特征"]

    async def _identify_novel_features(
        self,
        target_features: Optional[dict[str, Any],]

        comparison_results: Optional[list[dict[str, Any]]
    ) -> list[str, Any]:
        """识别新颖特征"""
        novel_features = []

        # 收集所有被公开的特征
        disclosed_features = set()
        for result in comparison_results:
            for comp in result.get("feature_comparison", []):
                if comp.get("disclosed"):
                    disclosed_features.add(comp["feature"])

        # 找出未被公开的特征
        for category, features in target_features.items():
            for feature in features:
                if feature not in disclosed_features:
                    novel_features.append({
                        "feature": feature,
                        "category": category,
                        "novel": True,
                    })

        return novel_features

    def _calculate_novelty_confidence(
        self,
        novel_features: Optional[list[dict[str, Any]],]

        target_features: Optional[dict[str, Any]]

    ) -> str:
        """
        计算新颖性置信度

        Args:
            novel_features: 新颖特征列表
            target_features: 目标特征字典

        Returns:
            置信度得分（0-1）
        """
        total_features = sum(len(f) for f in target_features.values())
        novel_count = len(novel_features)

        if total_features == 0:
            return 0.0

        novelty_ratio = novel_count / total_features

        # 新颖特征比例越高，置信度越高
        confidence = min(novelty_ratio * 1.5, 1.0)

        return confidence

    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    # 保留旧接口兼容性
    async def analyze_novelty_legacy(
        self,
        target_patent: Optional[dict[str, Any],]

        reference_docs: Optional[list[dict[str, Any]],]

        comparison_mode: str = "individual"
    ) -> dict[str, Any]:
        """
        分析新颖性（兼容旧接口）

        Args:
            target_patent: 目标专利
            reference_docs: 对比文件列表
            comparison_mode: 比对模式（individual/combined）

        Returns:
            新颖性分析结果
        """
        patent_data = {
            "patent_id": target_patent.get("patent_id", "未知"),
            "claims": target_patent.get("claims", ""),
            "prior_art_references": reference_docs
        }

        return await self.analyze_novelty(patent_data, "standard")
