"""
申请文件审查智能体

专注于专利申请文件质量审查，确保申请文件符合规范要求。
"""

from typing import Any, Dict, List, Optional
import logging
from core.agents.xiaona.base_component import BaseXiaonaComponent

logger = logging.getLogger(__name__)


class ApplicationDocumentReviewerProxy(BaseXiaonaComponent):
    """
    申请文件审查智能体

    核心能力：
    - 格式规范审查
    - 技术披露充分性审查
    - 权利要求书审查
    - 说明书审查
    """

    def _initialize(self) -> None:
        """初始化申请文件审查智能体"""
        self._register_capabilities([
            {
                "name": "format_review",
                "description": "格式规范审查",
                "input_types": ["专利申请文件"],
                "output_types": ["格式审查报告"],
                "estimated_time": 10.0,
            },
            {
                "name": "disclosure_review",
                "description": "技术披露充分性审查",
                "input_types": ["专利申请文件"],
                "output_types": ["披露审查报告"],
                "estimated_time": 20.0,
            },
            {
                "name": "claims_review",
                "description": "权利要求书审查",
                "input_types": ["权利要求书"],
                "output_types": ["权利要求审查报告"],
                "estimated_time": 25.0,
            },
            {
                "name": "specification_review",
                "description": "说明书审查",
                "input_types": ["说明书"],
                "output_types": ["说明书审查报告"],
                "estimated_time": 25.0,
            },
        ])

    async def review_application(
        self,
        application_data: Dict[str, Any],
        review_scope: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        完整申请文件审查流程

        Args:
            application_data: 申请文件数据
            review_scope: 审查范围（comprehensive/quick）

        Returns:
            完整审查报告
        """
        # 1. 格式规范审查
        format_result = await self.review_format(application_data)

        # 2. 技术披露充分性审查
        disclosure_result = await self.review_disclosure(application_data)

        # 3. 权利要求书审查
        claims_result = await self.review_claims(application_data)

        # 4. 说明书审查
        specification_result = await self.review_specification(application_data)

        # 5. 生成综合评分
        overall_score = self._calculate_overall_score(
            format_result,
            disclosure_result,
            claims_result,
            specification_result
        )

        # 6. 生成建议
        recommendations = self._generate_recommendations(
            format_result,
            disclosure_result,
            claims_result,
            specification_result
        )

        return {
            "application_id": application_data.get("application_id", "未知"),
            "applicant": application_data.get("applicant", "未知"),
            "review_scope": review_scope,
            "format_review": format_result,
            "disclosure_review": disclosure_result,
            "claims_review": claims_result,
            "specification_review": specification_result,
            "overall_score": overall_score,
            "overall_quality": self._get_quality_level(overall_score),
            "recommendations": recommendations,
            "reviewed_at": self._get_timestamp(),
        }

    async def review_format(
        self,
        application: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        审查申请文件格式

        Args:
            application: 申请文件数据

        Returns:
            格式审查结果
        """
        # 必备文件清单
        required_documents = [
            "请求书",
            "说明书",
            "权利要求书",
            "摘要",
            "说明书附图"  # 如有
        ]

        # 检查文件完整性
        provided_documents = application.get("documents", [])
        missing_documents = [
            doc for doc in required_documents
            if doc not in provided_documents
        ]

        # 检查申请人信息
        applicant_data = application.get("applicant_data", {})
        applicant_info = {
            "name": applicant_data.get("name", ""),
            "address": applicant_data.get("address", ""),
            "nationality": applicant_data.get("nationality", ""),
        }

        applicant_complete = all([
            applicant_info["name"],
            applicant_info["address"],
        ])

        # 格式问题检查
        format_issues = []
        if not applicant_complete:
            format_issues.append("申请人信息不完整")

        if missing_documents:
            format_issues.append(f"缺少必备文件：{', '.join(missing_documents)}")

        format_check = "passed" if not format_issues else "failed"

        return {
            "format_check": format_check,
            "required_documents": required_documents,
            "provided_documents": provided_documents,
            "missing_documents": missing_documents,
            "applicant_data": {
                "status": "complete" if applicant_complete else "incomplete",
                "info": applicant_info,
            },
            "format_issues": format_issues,
            "completeness_ratio": len(provided_documents) / len(required_documents) if required_documents else 0,
        }

    async def review_disclosure(
        self,
        application: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        审查技术披露充分性

        Args:
            application: 申请文件数据

        Returns:
            披露审查结果
        """
        # 提取技术信息
        technical_field = application.get("technical_field", "")
        background_art = application.get("background_art", "")
        invention_summary = application.get("invention_summary", "")
        technical_problem = application.get("technical_problem", "")
        technical_solution = application.get("technical_solution", "")
        beneficial_effects = application.get("beneficial_effects", "")

        # 充分性评估
        disclosures = {
            "technical_field": self._assess_disclosure_completeness(
                "技术领域", technical_field
            ),
            "background_art": self._assess_disclosure_completeness(
                "背景技术", background_art
            ),
            "technical_problem": self._assess_disclosure_completeness(
                "技术问题", technical_problem
            ),
            "technical_solution": self._assess_disclosure_completeness(
                "技术方案", technical_solution
            ),
            "beneficial_effects": self._assess_disclosure_completeness(
                "有益效果", beneficial_effects
            ),
        }

        # 识别缺失的披露
        missing_disclosures = []
        for aspect, assessment in disclosures.items():
            if assessment["status"] == "insufficient":
                missing_disclosures.append(f"{aspect}披露不充分")

        # 整体充分性判定
        disclosure_adequacy = "sufficient" if len(missing_disclosures) == 0 else "insufficient"

        return {
            "disclosure_adequacy": disclosure_adequacy,
            "disclosures": disclosures,
            "missing_disclosures": missing_disclosures,
            "completeness_score": sum(d["score"] for d in disclosures.values()) / len(disclosures),
        }

    async def review_claims(
        self,
        application: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        审查权利要求书

        Args:
            application: 申请文件数据

        Returns:
            权利要求审查结果
        """
        claims_text = application.get("claims", "")
        claims_list = self._parse_claims(claims_text)

        # 权利要求审查
        claims_review = {
            "clarity": self._assess_claims_clarity(claims_list),
            "support": self._assess_claims_support(claims_list, application),
            "breadth": self._assess_claims_breadth(claims_list),
            "dependency": self._assess_claims_dependency(claims_list),
        }

        # 识别问题
        issues = []
        suggestions = []

        # 清晰度问题
        if claims_review["clarity"]["score"] < 0.7:
            issues.append("权利要求表述不够清晰")
            suggestions.append("建议使用更明确的技术术语")

        # 支持问题
        if claims_review["support"]["score"] < 0.7:
            issues.append("权利要求与说明书支持不足")
            suggestions.append("确保权利要求的所有特征在说明书中充分描述")

        # 保护范围问题
        if claims_review["breadth"]["score"] > 0.9:
            issues.append("权利要求保护范围可能过宽")
            suggestions.append("考虑增加限定特征，提高授权可能性")

        return {
            "claims_review": claims_review,
            "total_claims": len(claims_list),
            "independent_claims": len([c for c in claims_list if c["type"] == "independent"]),
            "dependent_claims": len([c for c in claims_list if c["type"] == "dependent"]),
            "issues": issues,
            "suggestions": suggestions,
        }

    async def review_specification(
        self,
        application: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        审查说明书

        Args:
            application: 申请文件数据

        Returns:
            说明书审查结果
        """
        specification_text = application.get("specification", "")
        embodiments = application.get("embodiments", [])
        drawings = application.get("drawings", [])

        # 说明书审查
        specification_review = {
            "completeness": self._assess_specification_completeness(application),
            "clarity": self._assess_specification_clarity(specification_text),
            "enablement": self._assess_enablement(specification_text, embodiments),
            "best_mode": self._assess_best_mode(application),
            "drawings_support": self._assess_drawings_support(specification_text, drawings),
        }

        # 识别问题
        issues = []
        if not embodiments:
            issues.append("缺少具体实施方式")

        if specification_review["enablement"]["score"] < 0.7:
            issues.append("说明书公开不充分，本领域技术人员无法实现")

        return {
            "specification_review": specification_review,
            "total_embodiments": len(embodiments),
            "total_drawings": len(drawings),
            "issues": issues,
            "suggestions": self._generate_specification_suggestions(specification_review),
        }

    # 辅助方法

    def _parse_claims(self, claims_text: str) -> List[Dict[str, Any]]:
        """解析权利要求"""
        # 简化版解析
        claims = []
        lines = claims_text.split("\n")

        current_claim = None
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line[0].isdigit() and "." in line[:5]:
                # 新权利要求
                if current_claim:
                    claims.append(current_claim)

                current_claim = {
                    "number": int(line.split(".")[0]),
                    "type": "independent" if len(claims) == 0 else "dependent",
                    "text": line,
                }
            elif current_claim:
                current_claim["text"] += " " + line

        if current_claim:
            claims.append(current_claim)

        return claims if claims else [{"number": 1, "type": "independent", "text": claims_text}]

    def _assess_disclosure_completeness(
        self,
        aspect: str,
        content: str
    ) -> Dict[str, Any]:
        """评估披露充分性"""
        if not content or len(content) < 20:
            return {
                "status": "insufficient",
                "score": 0.0,
                "description": f"{aspect}披露不充分或缺失"
            }

        content_length = len(content)
        if content_length < 100:
            score = 0.5
            description = f"{aspect}披露较为简单"
        elif content_length < 300:
            score = 0.8
            description = f"{aspect}披露较为充分"
        else:
            score = 1.0
            description = f"{aspect}披露充分"

        return {
            "status": "sufficient" if score >= 0.7 else "insufficient",
            "score": score,
            "description": description,
        }

    def _assess_claims_clarity(
        self,
        claims_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """评估权利要求清晰度"""
        avg_length = sum(len(c["text"]) for c in claims_list) / len(claims_list) if claims_list else 0

        # 权利要求长度适中通常更清晰
        if 50 <= avg_length <= 300:
            score = 0.9
            description = "权利要求长度适中，表述清晰"
        elif avg_length < 50:
            score = 0.6
            description = "权利要求过于简单，可能不够明确"
        else:
            score = 0.7
            description = "权利要求较长，可能过于复杂"

        return {
            "score": score,
            "description": description,
            "average_length": avg_length,
        }

    def _assess_claims_support(
        self,
        claims_list: List[Dict[str, Any]],
        application: Dict[str, Any]
    ) -> Dict[str, Any]:
        """评估权利要求与说明书支持"""
        specification = application.get("specification", "")

        # 检查权利要求中的关键词是否在说明书中出现
        supported_count = 0
        for claim in claims_list:
            claim_text = claim["text"]
            # 提取关键词（简化版）
            keywords = self._extract_keywords(claim_text)

            # 检查是否在说明书中
            found_in_spec = any(
                keyword in specification
                for keyword in keywords
            )

            if found_in_spec:
                supported_count += 1

        support_ratio = supported_count / len(claims_list) if claims_list else 0

        return {
            "score": support_ratio,
            "description": f"{supported_count}/{len(claims_list)}个权利要求在说明书中得到支持",
            "supported_count": supported_count,
        }

    def _assess_claims_breadth(
        self,
        claims_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """评估权利要求保护范围"""
        # 独立权利要求的数量通常反映保护范围
        independent_count = len([c for c in claims_list if c["type"] == "independent"])

        if independent_count == 1:
            score = 0.8
            description = "独立权利要求数量合理"
        elif independent_count == 0:
            score = 0.0
            description = "缺少独立权利要求"
        else:
            score = 0.6
            description = f"有{independent_count}个独立权利要求，保护范围可能过宽"

        return {
            "score": score,
            "description": description,
            "independent_count": independent_count,
        }

    def _assess_claims_dependency(
        self,
        claims_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """评估权利要求依赖关系"""
        dependent_count = len([c for c in claims_list if c["type"] == "dependent"])
        independent_count = len([c for c in claims_list if c["type"] == "independent"])

        if dependent_count > 0:
            dependency_ratio = dependent_count / independent_count
            score = min(dependency_ratio / 3.0, 1.0)  # 理想的从属权利要求比例是2-3倍
            description = f"有{dependent_count}个从属权利要求"
        else:
            score = 0.5
            description = "缺少从属权利要求"

        return {
            "score": score,
            "description": description,
            "dependent_count": dependent_count,
        }

    def _assess_specification_completeness(
        self,
        application: Dict[str, Any]
    ) -> Dict[str, Any]:
        """评估说明书完整性"""
        required_sections = [
            "技术领域",
            "背景技术",
            "发明内容",
            "附图说明",
            "具体实施方式",
        ]

        specification = application.get("specification", "")
        complete_sections = sum(
            1 for section in required_sections
            if section in specification
        )

        score = complete_sections / len(required_sections)

        return {
            "score": score,
            "description": f"包含{complete_sections}/{len(required_sections)}个必要部分",
        }

    def _assess_specification_clarity(
        self,
        specification_text: str
    ) -> Dict[str, Any]:
        """评估说明书清晰度"""
        if not specification_text:
            return {"score": 0.0, "description": "说明书为空"}

        # 检查是否有结构化的段落
        paragraphs = specification_text.split("\n\n")
        structured = len(paragraphs) > 3

        score = 0.8 if structured else 0.5

        return {
            "score": score,
            "description": "说明书结构" + ("清晰" if structured else "需要优化"),
        }

    def _assess_enablement(
        self,
        specification_text: str,
        embodiments: List[Any]
    ) -> Dict[str, Any]:
        """评估充分公开（本领域技术人员能否实现）"""
        if not embodiments:
            return {
                "score": 0.3,
                "description": "缺少具体实施方式，充分公开不足"
            }

        # 实施方式的详细程度
        embodiment_detail = sum(len(str(emb)) for emb in embodiments) / len(embodiments) if embodiments else 0

        if embodiment_detail > 500:
            score = 0.9
            description = "实施方式详细，充分公开充分"
        elif embodiment_detail > 200:
            score = 0.7
            description = "实施方式较为详细"
        else:
            score = 0.5
            description = "实施方式较为简单"

        return {
            "score": score,
            "description": description,
            "embodiment_count": len(embodiments),
        }

    def _assess_best_mode(
        self,
        application: Dict[str, Any]
    ) -> Dict[str, Any]:
        """评估最佳实施方式披露"""
        # 简化版评估
        best_mode_mentioned = "最佳实施方式" in application.get("specification", "")

        return {
            "score": 0.8 if best_mode_mentioned else 0.6,
            "description": "最佳实施方式" + ("已披露" if best_mode_mentioned else "未明确披露"),
        }

    def _assess_drawings_support(
        self,
        specification_text: str,
        drawings: List[Any]
    ) -> Dict[str, Any]:
        """评估附图支持"""
        if not drawings:
            return {
                "score": 0.7,
                "description": "无附图"
            }

        # 检查说明书是否引用附图
        drawing_refs = specification_text.count("图")
        drawing_count = len(drawings)

        return {
            "score": min(drawing_refs / 10.0, 1.0),
            "description": f"有{drawing_count}幅附图，说明书中引用{drawing_refs}次",
        }

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简化版关键词提取
        keywords = []

        # 提取中文词汇（2-4个字）
        import re
        words = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)

        # 过滤常见词
        stop_words = ["所述", "其特征在于", "其中", "包括"]
        keywords = [w for w in words if w not in stop_words and len(w) >= 2]

        return keywords[:10]  # 返回前10个关键词

    def _generate_specification_suggestions(
        self,
        specification_review: Dict[str, Any]
    ) -> List[str]:
        """生成说明书改进建议"""
        suggestions = []

        if specification_review["completeness"]["score"] < 0.7:
            suggestions.append("补充说明书的必要部分")

        if specification_review["enablement"]["score"] < 0.7:
            suggestions.append("增加具体实施方式的详细描述")

        if specification_review["best_mode"]["score"] < 0.7:
            suggestions.append("明确披露最佳实施方式")

        if not suggestions:
            suggestions.append("说明书质量良好，建议保持")

        return suggestions

    def _calculate_overall_score(
        self,
        format_result: Dict,
        disclosure_result: Dict,
        claims_result: Dict,
        specification_result: Dict
    ) -> float:
        """计算综合评分"""
        scores = [
            format_result.get("completeness_ratio", 0) * (1 if format_result.get("format_check") == "passed" else 0.5),
            disclosure_result.get("completeness_score", 0),
            claims_result.get("claims_review", {}).get("clarity", {}).get("score", 0),
            specification_result.get("specification_review", {}).get("completeness", {}).get("score", 0),
        ]

        return sum(scores) / len(scores) if scores else 0

    def _get_quality_level(self, score: float) -> str:
        """获取质量等级"""
        if score >= 0.9:
            return "优秀"
        elif score >= 0.75:
            return "良好"
        elif score >= 0.6:
            return "合格"
        else:
            return "待改进"

    def _generate_recommendations(
        self,
        format_result: Dict,
        disclosure_result: Dict,
        claims_result: Dict,
        specification_result: Dict
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 格式建议
        if format_result.get("format_check") == "failed":
            recommendations.append("补充缺失的必备文件")
            recommendations.append("完善申请人信息")

        # 披露建议
        if disclosure_result.get("disclosure_adequacy") == "insufficient":
            recommendations.append("加强技术披露的充分性")

        # 权利要求建议
        if claims_result.get("issues"):
            recommendations.extend(claims_result.get("suggestions", []))

        # 说明书建议
        if specification_result.get("issues"):
            recommendations.extend(specification_result.get("suggestions", []))

        if not recommendations:
            recommendations.append("申请文件质量良好，可直接提交")

        return recommendations

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
