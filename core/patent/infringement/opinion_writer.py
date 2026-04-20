#!/usr/bin/env python3
"""
法律意见书撰写器

生成专业的侵权分析法律意见书。
"""
import logging
from datetime import datetime
from typing import List, Dict, Any

try:
    from .infringement_determiner import InfringementResult
    from .feature_comparator import FeatureComparison
except ImportError:
    from core.patent.infringement.infringement_determiner import InfringementResult
    from core.patent.infringement.feature_comparator import FeatureComparison

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpinionWriter:
    """法律意见书撰写器"""

    def __init__(self):
        """初始化撰写器"""
        logger.info("✅ 法律意见书撰写器初始化成功")

    def write_opinion(
        self,
        infringement_result: InfringementResult,
        comparisons: List[FeatureComparison],
        attorney: str = "专利代理师"
    ) -> str:
        """
        撰写完整的法律意见书

        Args:
            infringement_result: 侵权判定结果
            comparisons: 特征对比结果
            attorney: 代理师姓名

        Returns:
            法律意见书文本
        """
        logger.info("📝 开始撰写法律意见书")

        sections = []

        # 1. 标题和基本信息
        sections.append(self._write_header(attorney))

        # 2. 案件背景
        sections.append(self._write_background(infringement_result))

        # 3. 权利要求分析
        sections.append(self._write_claims_analysis(comparisons))

        # 4. 特征对比分析
        sections.append(self._write_feature_comparison(comparisons))

        # 5. 侵权判定
        sections.append(self._write_infringement_conclusion(infringement_result))

        # 6. 法律依据
        sections.append(self._write_legal_basis(infringement_result))

        # 7. 风险评估
        sections.append(self._write_risk_assessment(infringement_result))

        # 8. 建议措施
        sections.append(self._write_recommendations(infringement_result))

        # 9. 结语
        sections.append(self._write_footer())

        opinion = "\n\n".join(sections)

        logger.info("✅ 法律意见书撰写完成")

        return opinion

    def _write_header(self, attorney: str) -> str:
        """撰写标题部分"""
        return f"""# 专利侵权分析法律意见书

**出具日期**: {datetime.now().strftime("%Y年%m月%d日")}
**出具人**: {attorney}
**文档编号**: LEGAL-OPINION-{datetime.now().strftime("%Y%m%d")}-001

---

## 声明

本法律意见书仅基于提供的资料进行分析，仅供参考，不构成正式法律建议。具体案件请咨询专业专利律师。
"""

    def _write_background(self, result: InfringementResult) -> str:
        """撰写案件背景"""
        return f"""## 一、案件背景

本分析针对以下专利与产品进行侵权风险评估：

- **专利号**: {result.patent_id}
- **涉案产品**: {result.product_name}
- **分析目的**: 评估涉案产品是否落入专利权的保护范围
"""

    def _write_claims_analysis(self, comparisons: List[FeatureComparison]) -> str:
        """撰写权利要求分析"""
        lines = ["## 二、权利要求分析\n"]

        for comp in comparisons:
            lines.append(f"### 权利要求 {comp.claim_number}")
            lines.append(f"- **特征总数**: {comp.total_features}")
            lines.append(f"- **已覆盖**: {comp.mapped_features} ({comp.coverage_ratio:.1%})")
            lines.append(f"- **缺失**: {comp.missing_features}")
            lines.append(f"- **差异**: {comp.different_features}\n")

        return "\n".join(lines)

    def _write_feature_comparison(self, comparisons: List[FeatureComparison]) -> str:
        """撰写特征对比分析"""
        lines = ["## 三、特征对比分析\n"]

        for comp in comparisons:
            lines.append(f"### 权利要求 {comp.claim_number} 对比表")
            lines.append("| 权利要求特征 | 产品特征 | 对应关系 | 置信度 |")
            lines.append("|-------------|---------|---------|--------|")

            for mapping in comp.mappings:
                claim_short = self._truncate_text(mapping.claim_feature_text, 40)
                product_short = self._truncate_text(mapping.product_feature_text, 40)

                if mapping.correspondence_type == "exact":
                    symbol = "✓ 完全一致"
                elif mapping.correspondence_type == "equivalent":
                    symbol = "≈ 等同"
                elif mapping.correspondence_type == "different":
                    symbol = "× 差异"
                else:
                    symbol = "✗ 缺失"

                lines.append(f"| {claim_short} | {product_short} | {symbol} | {mapping.confidence:.2%} |")

            lines.append("")

        return "\n".join(lines)

    def _write_infringement_conclusion(self, result: InfringementResult) -> str:
        """撰写侵权判定结论"""
        lines = ["## 四、侵权判定结论\n"]

        # 总体结论
        overall_text = "构成侵权" if result.overall_infringement else "不构成侵权"
        lines.append(f"### 总体结论")
        lines.append(f"根据全面覆盖原则的分析，涉案产品**{overall_text}**。")
        lines.append(f"**风险等级**: {result.overall_risk.upper()}\n")

        # 各权利要求结论
        lines.append("### 各权利要求判定")
        for conclusion in result.conclusions:
            status = "构成侵权" if conclusion.infringement_found else "不构成侵权"
            lines.append(f"**权利要求 {conclusion.claim_number}**: {status}")
            lines.append(f"- 侵权类型: {conclusion.infringement_type.value}")
            lines.append(f"- 置信度: {conclusion.confidence:.2%}")
            lines.append(f"- 判定理由: {conclusion.reasoning}")

            if conclusion.missing_features:
                lines.append(f"- 缺失特征:")
                for feature in conclusion.missing_features:
                    lines.append(f"  - {feature}")

            lines.append("")

        return "\n".join(lines)

    def _write_legal_basis(self, result: InfringementResult) -> str:
        """撰写法律依据"""
        lines = ["## 五、法律依据\n"]

        for idx, basis in enumerate(result.legal_basis, 1):
            lines.append(f"{idx}. {basis}")

        return "\n".join(lines) + "\n"

    def _write_risk_assessment(self, result: InfringementResult) -> str:
        """撰写风险评估"""
        lines = ["## 六、风险评估\n"]

        if result.overall_risk == "high":
            assessment = """**高风险等级**

涉案产品极有可能被认定为侵权，存在以下风险：

1. **诉讼风险**: 专利权人可能提起侵权诉讼，要求停止侵权并赔偿损失
2. **禁令风险**: 法院可能颁发临时禁令或永久禁令，要求停止生产销售
3. **赔偿风险**: 可能面临专利权人的损害赔偿请求，包括实际损失和违法所得
4. **声誉风险**: 侵权认定可能对企业商业信誉造成负面影响
"""
        elif result.overall_risk == "medium":
            assessment = """**中等风险等级**

涉案产品存在一定的侵权风险，需要进一步分析和应对：

1. **等同原则适用**: 需评估缺失特征是否适用等同原则
2. **专利稳定性**: 建议评估目标专利的稳定性，考虑无效宣告
3. **证据收集**: 建议收集并保留相关技术文档和研发记录
4. **专业咨询**: 建议咨询专业专利律师，制定应对策略
"""
        else:
            assessment = """**低风险等级**

涉案产品的侵权风险较低，但仍需注意：

1. **持续监控**: 建立专利预警机制，持续关注相关专利动态
2. **自主创新**: 加强自主研发，建立自己的专利布局
3. **规避设计**: 如需改进产品，注意规避专利保护范围
4. **定期复审**: 定期进行专利风险复审，确保产品合规
"""

        lines.append(assessment)

        return "\n".join(lines)

    def _write_recommendations(self, result: InfringementResult) -> str:
        """撰写建议措施"""
        lines = ["## 七、建议措施\n"]

        for idx, rec in enumerate(result.recommendations, 1):
            lines.append(f"{idx}. {rec}")

        return "\n".join(lines) + "\n"

    def _write_footer(self) -> str:
        """撰写结语"""
        return """## 八、结语

本法律意见书基于提供的资料进行分析，分析结论仅供参考。实际案件中，还需要考虑更多因素，如：

- 专利的稳定性（是否可能被无效）
- 现有技术的抗辩
- 专利权的滥用
- 诉讼时效
- 管辖法院的判例倾向

建议在实际采取行动前，咨询专业专利律师进行全面评估。

---

**本意见书完**

*本文档由Athena专利工作平台自动生成*
"""

    def _truncate_text(self, text: str, max_length: int) -> str:
        """截断文本"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
