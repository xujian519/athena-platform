"""
DOCX输入验证器 - 在执行技能前验证输入参数

借鉴MiniMax Skills的验证机制设计

版本: 1.0.0
更新日期: 2026-03-31
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    confidence: float = 1.0


class DocxInputValidator:
    """DOCX输入验证器

    支持三种管道的输入验证：
    - CREATE: 创建新文档
    - EDIT: 编辑现有文档
    - APPLY_TEMPLATE: 应用模板创建文档
    """

    # 文档类型关键词映射
    DOCUMENT_TYPE_KEYWORDS = {
        "contract": ["合同", "协议", "NDA", "保密", "劳动", "采购", "销售"],
        "report": ["报告", "分析", "研究", "调研", "评估"],
        "proposal": ["提案", "建议", "方案", "计划"],
        "specification": ["说明书", "规格", "规范", "技术文档"],
        "letter": ["信函", "通知", "函件", "邮件"],
    }

    # 模板名称映射
    TEMPLATE_MAPPING = {
        "contract": "legal-contract",
        "nda": "nda-agreement",
        "patent-analysis": "patent-analysis-report",
        "technical-report": "technical-report",
        "business-proposal": "business-proposal",
    }

    def __init__(self, templates_dir: Path | None = None):
        """
        初始化验证器

        Args:
            templates_dir: 模板目录路径
        """
        self.templates_dir = templates_dir or Path(__file__).parent.parent / "templates"

    def validate(self, pipeline: str, **kwargs) -> ValidationResult:
        """
        统一验证入口

        Args:
            pipeline: 管道名称 (create, edit, apply_template)
            **kwargs: 管道特定的参数

        Returns:
            ValidationResult: 验证结果
        """
        validators = {
            "create": self.validate_create,
            "edit": self.validate_edit,
            "apply_template": self.validate_apply_template,
        }

        validator = validators.get(pipeline)
        if not validator:
            return ValidationResult(
                valid=False,
                errors=[f"未知的管道类型: {pipeline}"],
                suggestions=["支持的管道: create, edit, apply_template"]
            )

        return validator(**kwargs)

    def validate_create(
        self,
        content: str,
        document_type: str | None = None,
        format_hints: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """
        验证创建文档的输入

        Args:
            content: 文档内容描述
            document_type: 文档类型
            format_hints: 格式提示

        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        suggestions = []

        # 1. 检查内容是否为空
        if not content or len(content.strip()) < 10:
            errors.append("文档内容描述过短，请提供更详细的内容描述")
            suggestions.append("建议提供: 文档目的、主要章节、目标受众等信息")

        # 2. 检查内容长度
        if content and len(content) > 10000:
            warnings.append("内容描述较长，可能会生成较长的文档")

        # 3. 检测文档类型
        detected_type = self._detect_document_type(content)
        if document_type and document_type != detected_type:
            warnings.append(
                f"检测到的文档类型 '{detected_type}' 与指定的 '{document_type}' 不匹配"
            )

        # 4. 检查格式提示
        if format_hints:
            format_errors = self._validate_format_hints(format_hints)
            errors.extend(format_errors)

        # 5. 建议使用模板
        if detected_type and detected_type in self.TEMPLATE_MAPPING:
            template_name = self.TEMPLATE_MAPPING[detected_type]
            if self._template_exists(template_name):
                suggestions.append(
                    f"检测到您可能需要'{detected_type}'类型文档，"
                    f"建议使用模板 '{template_name}' 以获得更专业的格式"
                )

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            confidence=self._calculate_confidence(errors, warnings)
        )

    def validate_edit(
        self,
        file_path: str,
        changes: dict[str, Any],
        mode: str = "tracked",
    ) -> ValidationResult:
        """
        验证编辑文档的输入

        Args:
            file_path: 文档文件路径
            changes: 修改内容
            mode: 编辑模式 (tracked, direct)

        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        suggestions = []

        path = Path(file_path)

        # 1. 检查文件是否存在
        if not path.exists():
            errors.append(f"文件不存在: {file_path}")
            return ValidationResult(valid=False, errors=errors)

        # 2. 检查文件扩展名
        if path.suffix.lower() not in [".docx", ".docm", ".dotx"]:
            if path.suffix.lower() == ".doc":
                warnings.append("检测到旧版.doc格式，建议先转换为.docx格式")
                suggestions.append("可以使用: libreoffice --headless --convert-to docx file.doc")
            else:
                warnings.append(f"文件扩展名 '{path.suffix}' 可能不是有效的Word文档")

        # 3. 检查文件大小
        try:
            file_size = path.stat().st_size
            if file_size == 0:
                errors.append("文件为空")
            elif file_size > 50 * 1024 * 1024:  # 50MB
                warnings.append(f"文件较大 ({file_size / 1024 / 1024:.1f}MB)，处理可能需要较长时间")
        except Exception as e:
            errors.append(f"无法读取文件信息: {e}")

        # 4. 检查修改内容
        if not changes:
            errors.append("未指定修改内容")
        else:
            change_errors = self._validate_changes(changes)
            errors.extend(change_errors)

        # 5. 检查编辑模式
        if mode == "direct":
            warnings.append("使用直接编辑模式将不会保留修改历史")
            suggestions.append("对于重要文档，建议使用追踪修改模式 (mode='tracked')")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            confidence=self._calculate_confidence(errors, warnings)
        )

    def validate_apply_template(
        self,
        template_name: str,
        variables: dict[str, Any],
        customizations: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """
        验证应用模板的输入

        Args:
            template_name: 模板名称
            variables: 模板变量
            customizations: 自定义配置

        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        suggestions = []

        # 1. 检查模板是否存在
        if not self._template_exists(template_name):
            errors.append(f"模板 '{template_name}' 不存在")
            available_templates = self._list_available_templates()
            if available_templates:
                suggestions.append(f"可用的模板: {', '.join(available_templates)}")

        # 2. 检查必需变量
        template_vars = self._get_template_variables(template_name)
        if template_vars:
            missing_vars = []
            for var in template_vars:
                if var.get("required", False) and var["name"] not in variables:
                    missing_vars.append(var["name"])

            if missing_vars:
                errors.append(f"缺少必需的变量: {', '.join(missing_vars)}")

        # 3. 检查变量值的有效性
        for var_name, var_value in variables.items():
            if var_value is None or var_value == "":
                warnings.append(f"变量 '{var_name}' 的值为空")

        # 4. 检查自定义配置
        if customizations:
            custom_errors = self._validate_customizations(customizations)
            errors.extend(custom_errors)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            confidence=self._calculate_confidence(errors, warnings)
        )

    # ==================== 辅助方法 ====================

    def _detect_document_type(self, content: str) -> str | None:
        """检测文档类型"""
        content_lower = content.lower()

        for doc_type, keywords in self.DOCUMENT_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    return doc_type

        return None

    def _template_exists(self, template_name: str) -> bool:
        """检查模板是否存在"""
        template_path = self.templates_dir / template_name
        return template_path.exists() and template_path.is_dir()

    def _list_available_templates(self) -> list[str]:
        """列出可用的模板"""
        if not self.templates_dir.exists():
            return []

        return [
            d.name for d in self.templates_dir.iterdir()
            if d.is_dir() and (d / "template.docx").exists()
        ]

    def _get_template_variables(self, template_name: str) -> list[dict[str, Any]]:
        """获取模板变量定义"""
        import json

        placeholders_file = self.templates_dir / template_name / "placeholders.json"
        if not placeholders_file.exists():
            return []

        try:
            with open(placeholders_file, encoding='utf-8') as f:
                data = json.load(f)
                return data.get("placeholders", [])
        except Exception:
            return []

    def _validate_format_hints(self, format_hints: dict[str, Any]) -> list[str]:
        """验证格式提示"""
        errors = []

        # 检查页面大小
        valid_page_sizes = ["A4", "A3", "Letter", "Legal"]
        if "page_size" in format_hints:
            if format_hints["page_size"] not in valid_page_sizes:
                errors.append(
                    f"无效的页面大小 '{format_hints['page_size']}', "
                    f"支持的值: {', '.join(valid_page_sizes)}"
                )

        # 检查边距
        if "margins" in format_hints:
            margins = format_hints["margins"]
            required_keys = ["top", "bottom", "left", "right"]
            for key in required_keys:
                if key not in margins:
                    errors.append(f"边距配置缺少 '{key}'")

        return errors

    def _validate_changes(self, changes: dict[str, Any]) -> list[str]:
        """验证修改内容"""
        errors = []

        # 检查修改类型
        valid_operations = ["replace", "insert", "delete", "format"]
        if "operation" in changes:
            if changes["operation"] not in valid_operations:
                errors.append(
                    f"无效的操作类型 '{changes['operation']}', "
                    f"支持的操作: {', '.join(valid_operations)}"
                )

        # 检查目标位置
        if "target" not in changes and "search_pattern" not in changes:
            errors.append("修改内容必须指定 'target' 或 'search_pattern'")

        return errors

    def _validate_customizations(self, customizations: dict[str, Any]) -> list[str]:
        """验证自定义配置"""
        errors = []

        # 检查输出文件名
        if "output_filename" in customizations:
            filename = customizations["output_filename"]
            if not filename.endswith(".docx"):
                errors.append("输出文件名必须以 '.docx' 结尾")

        return errors

    def _calculate_confidence(self, errors: list[str], warnings: list[str]) -> float:
        """计算置信度"""
        confidence = 1.0
        confidence -= len(errors) * 0.3
        confidence -= len(warnings) * 0.1
        return max(0.0, min(1.0, confidence))


# 使用示例
if __name__ == "__main__":
    validator = DocxInputValidator()

    # 示例1: 验证创建文档
    result = validator.validate_create(
        content="创建一份专利分析报告，包含技术特征对比和创造性分析",
        document_type="report"
    )
    print(f"创建验证: valid={result.valid}, confidence={result.confidence:.2f}")
    if result.suggestions:
        print(f"建议: {result.suggestions}")

    # 示例2: 验证编辑文档
    result = validator.validate_edit(
        file_path="example.docx",
        changes={"operation": "replace", "target": "日期", "new_value": "2026-03-31"},
        mode="tracked"
    )
    print(f"编辑验证: valid={result.valid}, confidence={result.confidence:.2f}")

    # 示例3: 验证应用模板
    result = validator.validate_apply_template(
        template_name="patent-analysis-report",
        variables={
            "patent_number": "CN109459075A",
            "client_name": "测试公司"
        }
    )
    print(f"模板验证: valid={result.valid}, confidence={result.confidence:.2f}")
