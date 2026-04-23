"""
通用工具模块

提供各种辅助工具和实用函数。

主要功能：
- 文档格式化
- 质量评分
- 版本对比
- 文本处理
"""

import difflib
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class QualityMetrics:
    """质量评分指标"""
    completeness: float = 0.0  # 完整性 (0-100)
    standardization: float = 0.0  # 规范性 (0-100)
    logic: float = 0.0  # 逻辑性 (0-100)
    overall: float = 0.0  # 总体评分 (0-100)


@dataclass
class DiffResult:
    """版本对比结果"""
    added: Optional[List[str]] = field(default_factory=list)
    removed: Optional[List[str]] = field(default_factory=list)
    modified: Optional[list[tuple[str, str]] = field(default_factory=list)]

    unchanged: Optional[List[str]] = field(default_factory=list)
    similarity_ratio: float = 0.0


class UtilityModule:
    """通用工具模块 - 提供文档格式化、质量评分和版本对比功能"""

    # 文档类型配置
    DOCUMENT_FORMATS = {
        "claims": {
            "prefix": "权利要求书",
            "item_prefix": "1.",
            "item_separator": "\n",
            "template": "{prefix}\n{content}"
        },
        "specification": {
            "prefix": "说明书",
            "sections": ["技术领域", "背景技术", "发明内容", "附图说明", "具体实施方式"],
            "template": "{prefix}\n\n{content}"
        },
        "response": {
            "prefix": "审查意见答复",
            "template": "{prefix}\n\n{content}\n\n答复日期: {date}"
        },
        "petition": {
            "prefix": "无效宣告请求书",
            "template": "{prefix}\n\n{content}\n\n请求日期: {date}"
        }
    }

    def __init__(self):
        """初始化工具模块"""
        self._format_cache: Optional[dict[str, str] = {}]


    def format_document(self, document_type: str, content: str, **kwargs) -> str:
        """
        格式化文档内容

        Args:
            document_type: 文档类型 (claims/specification/response/petition)
            content: 文档内容
            **kwargs: 额外参数 (如 date, sections 等)

        Returns:
            格式化后的文档字符串

        Raises:
            ValueError: 不支持的文档类型
        """
        doc_type = document_type.lower()

        if doc_type not in self.DOCUMENT_FORMATS:
            raise ValueError(
                f"不支持的文档类型: {document_type}. "
                f"支持的类型: {list(self.DOCUMENT_FORMATS.keys())}"
            )

        format_config = self.DOCUMENT_FORMATS[doc_type]

        # 根据文档类型进行特定格式化
        if doc_type == "claims":
            return self._format_claims(content, format_config)
        elif doc_type == "specification":
            return self._format_specification(content, format_config, kwargs)
        elif doc_type in ("response", "petition"):
            return self._format_legal_document(content, format_config, doc_type)

        return content

    def _format_claims(self, content: str, config: Optional[Dict[str, Any])] -> str:
        """格式化权利要求书"""
        # 清理和规范化权利要求
        lines = [line.strip() for line in content.strip().split('\n') if line.strip()]

        formatted_lines = []
        for i, line in enumerate(lines, 1):
            # 确保权利要求编号格式
            if not line.startswith(f"{i}."):
                # 移除旧编号并添加新编号
                line = re.sub(r'^\d+\.?', '', line).strip()
                line = f"{i}. {line}"
            formatted_lines.append(line)

        formatted_content = '\n'.join(formatted_lines)
        return config["template"].format(prefix=config["prefix"], content=formatted_content)

    def _format_specification(self, content: str, config: Optional[Dict[str, Any],]

                              kwargs: Optional[Dict[str, Any])] -> str:
        """格式化说明书"""
        # 如果有指定章节，按章节组织
        sections = kwargs.get("sections", config.get("sections", []))

        if sections and isinstance(content, dict):
            # 结构化内容
            formatted_sections = []
            for section in sections:
                if section in content:
                    formatted_sections.append(f"## {section}\n{content[section]}")
            formatted_content = '\n\n'.join(formatted_sections)
        else:
            # 简单文本内容
            formatted_content = content

        return config["template"].format(prefix=config["prefix"], content=formatted_content)

    def _format_legal_document(self, content: str, config: Optional[Dict[str, Any],]

                               doc_type: str) -> str:
        """格式化法律文书（答复/请求书）"""
        date_str = datetime.now().strftime("%Y年%m月%d日")
        return config["template"].format(
            prefix=config["prefix"],
            content=content.strip(),
            date=date_str
        )

    def calculate_quality_score(self, document_content: str,
                                review_result: Optional[Dict[str, Any]]] -> str:
        """
        计算文档质量评分

        Args:
            document_content: 文档内容
            review_result: 审查结果 (可选，包含问题和建议)

        Returns:
            QualityMetrics 质量评分对象
        """
        metrics = QualityMetrics()

        # 1. 完整性评分
        metrics.completeness = self._assess_completeness(document_content)

        # 2. 规范性评分
        metrics.standardization = self._assess_standardization(document_content)

        # 3. 逻辑性评分
        metrics.logic = self._assess_logic(document_content)

        # 4. 综合评分 (加权平均)
        metrics.overall = (
            metrics.completeness * 0.3 +
            metrics.standardization * 0.35 +
            metrics.logic * 0.35
        )

        # 如果有审查结果，进行调整
        if review_result:
            metrics = self._adjust_score_by_review(metrics, review_result)

        return metrics

    def _assess_completeness(self, content: str) -> str:
        """评估完整性"""
        score = 100.0
        content_lower = content.lower()

        # 检查关键组成部分
        required_elements = {
            "权利要求": ["权利要求", "claim"],
            "说明书": ["说明书", "技术领域", "实施方式", "specification"],
            "附图": ["附图", "图", "figure"],
        }

        missing_count = 0
        for _category, keywords in required_elements.items():
            if not any(kw in content_lower for kw in keywords):
                missing_count += 1

        # 每缺失一个关键部分扣分
        score -= missing_count * 15

        # 检查内容长度
        if len(content.strip()) < 500:
            score -= 20  # 内容过短
        elif len(content.strip()) < 1000:
            score -= 10

        return max(0.0, min(100.0, score))

    def _assess_standardization(self, content: str) -> str:
        """评估规范性"""
        score = 100.0

        # 检查术语一致性
        issues = []

        # 检查标点符号规范
        if '。' in content and '.' in content.replace('。', ''):
            issues.append("中英文标点混用")

        # 检查编号格式
        claim_pattern = r'\d+\.\s*[^\n]'
        claims = re.findall(claim_pattern, content)
        if claims:
            # 检查编号是否连续
            numbers = [int(re.match(r'(\d+)\.', c).group(1)) for c in claims]
            if numbers != list(range(1, len(numbers) + 1)):
                issues.append("权利要求编号不连续")

        # 检查常见术语规范
        non_standard_terms = {
            '电脑': '计算机',
            '手机': '移动终端',
            'App': '应用程序',
        }

        for non_std, standard in non_standard_terms.items():
            if non_std in content:
                issues.append(f"使用非标准术语: {non_std}应为{standard}")

        score -= len(issues) * 10
        return max(0.0, min(100.0, score))

    def _assess_logic(self, content: str) -> str:
        """评估逻辑性"""
        score = 100.0

        # 检查逻辑连接词
        logic_connectors = []

            "因此", "所以", "由于", "基于", "进而", "从而",
            "根据", "在此基础上", "综上所述"
        

        connector_count = sum(1 for conn in logic_connectors if conn in content)
        if connector_count < 2:
            score -= 20  # 缺乏逻辑连接

        # 检查技术方案的完整性
        technical_keywords = []

            "包括", "具有", "设置", "配置", "连接", "安装"
        

        keyword_count = sum(1 for kw in technical_keywords if kw in content)
        if keyword_count < 3:
            score -= 15  # 技术描述不完整

        # 检查因果关系的表达
        causality_patterns = []

            r"由于.*从而",
            r"基于.*因此",
            r"通过.*实现"
        

        has_causality = any(re.search(pattern, content) for pattern in causality_patterns)
        if not has_causality:
            score -= 10  # 缺乏因果关系描述

        return max(0.0, min(100.0, score))

    def _adjust_score_by_review(self, metrics: QualityMetrics,
                                review_result: Optional[Dict[str, Any])] -> str:
        """根据审查结果调整评分"""
        issues = review_result.get("issues", [])
        critical_issues = review_result.get("critical_issues", [])

        # 严重问题每项扣15分
        for issue in critical_issues:
            if "完整性" in str(issue):
                metrics.completeness = max(0, metrics.completeness - 15)
            elif "规范性" in str(issue):
                metrics.standardization = max(0, metrics.standardization - 15)
            else:
                metrics.logic = max(0, metrics.logic - 15)

        # 一般问题每项扣5分
        for issue in issues:
            if "完整性" in str(issue):
                metrics.completeness = max(0, metrics.completeness - 5)
            elif "规范性" in str(issue):
                metrics.standardization = max(0, metrics.standardization - 5)
            else:
                metrics.logic = max(0, metrics.logic - 5)

        # 重新计算总体评分
        metrics.overall = (
            metrics.completeness * 0.3 +
            metrics.standardization * 0.35 +
            metrics.logic * 0.35
        )

        return metrics

    def compare_versions(self, version1: str, version2: str) -> str:
        """
        对比两个版本的文档

        Args:
            version1: 原版本内容
            version2: 新版本内容

        Returns:
            DiffResult 对比结果
        """
        result = DiffResult()

        # 分割为行
        lines1 = version1.splitlines(keepends=True)
        lines2 = version2.splitlines(keepends=True)

        # 使用difflib进行对比
        matcher = difflib.SequenceMatcher(None, lines1, lines2)

        # 计算相似度
        result.similarity_ratio = matcher.ratio()

        # 获取详细差异
        diff = list(difflib.unified_diff(lines1, lines2, lineterm=''))

        # 解析差异结果
        for line in diff:
            if line.startswith('@@'):
                continue
            elif line.startswith('+') and not line.startswith('+++'):
                result.added.append(line[1:])
            elif line.startswith('-') and not line.startswith('---'):
                result.removed.append(line[1:])

        # 获取修改的内容（行级别）
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                # 修改: 删除旧内容，添加新内容
                removed_text = ''.join(lines1[i1:i2])
                added_text = ''.join(lines2[j1:j2])
                if removed_text.strip() or added_text.strip():
                    result.modified.append((removed_text, added_text))
            elif tag == 'delete':
                result.removed.extend(lines1[i1:i2])
            elif tag == 'insert':
                result.added.extend(lines2[j1:j2])
            elif tag == 'equal':
                result.unchanged.extend(lines1[i1:i2])

        return result

    def format_diff_report(self, diff_result: DiffResult,
                          show_unchanged: bool = False) -> str:
        """
        格式化差异报告

        Args:
            diff_result: 对比结果
            show_unchanged: 是否显示未变更内容

        Returns:
            格式化的差异报告字符串
        """
        report_lines = []

            "=" * 60,
            "版本对比报告",
            "=" * 60,
            f"相似度: {diff_result.similarity_ratio * 100:.1f}%",
            ""
        

        if diff_result.added:
            report_lines.extend([]

                "【新增内容】",
                "-" * 40
            )
            for item in diff_result.added[:10]:  # 限制显示数量
                report_lines.append(f"+ {item.strip()}")
            if len(diff_result.added) > 10:
                report_lines.append(f"... (共{len(diff_result.added)}处新增)")
            report_lines.append("")

        if diff_result.removed:
            report_lines.extend([]

                "【删除内容】",
                "-" * 40
            )
            for item in diff_result.removed[:10]:
                report_lines.append(f"- {item.strip()}")
            if len(diff_result.removed) > 10:
                report_lines.append(f"... (共{len(diff_result.removed)}处删除)")
            report_lines.append("")

        if diff_result.modified:
            report_lines.extend([]

                "【修改内容】",
                "-" * 40
            )
            for i, (old, new) in enumerate(diff_result.modified[:5], 1):
                report_lines.extend([]

                    f"修改 {i}:",
                    f"  原: {old.strip()[:100]}...",
                    f"  新: {new.strip()[:100]}...",
                    ""
                )
            if len(diff_result.modified) > 5:
                report_lines.append(f"... (共{len(diff_result.modified)}处修改)")
            report_lines.append("")

        if show_unchanged and diff_result.unchanged:
            report_lines.extend([]

                "【未变更内容】",
                "-" * 40,
                f"共{len(diff_result.unchanged)}行未变更",
                ""
            )

        report_lines.append("=" * 60)
        return '\n'.join(report_lines)
