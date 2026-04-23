"""
code_analyzer工具包装器

将tool_implementations.py中的code_analyzer_handler包装为统一工具接口。
提供完整的类型注解、文档字符串和错误处理。
"""

from typing import Any, Dict
from datetime import datetime
import asyncio


async def code_analyzer(
    code: str,
    language: str = "python",
    style: str = "basic"
) -> dict[str, Any]:
    """
    分析代码的统计信息、复杂度和潜在问题

    功能特性:
    1. 代码行数统计（总行数、代码行、注释行）
    2. 代码复杂度分析（基于控制流和关键词）
    3. 代码风格检查（检测常见问题）
    4. 潜在问题检测（调试代码、过长行等）
    5. 改进建议生成

    支持的语言:
    - Python
    - JavaScript
    - TypeScript

    Args:
        code: 要分析的代码内容
        language: 编程语言 (python, javascript, typescript, js, ts)
        style: 分析风格
            - "basic": 基础分析（统计+复杂度）
            - "detailed": 详细分析（包含问题检测和建议）

    Returns:
        包含以下字段的字典:
        {
            "language": str,              # 分析的语言
            "statistics": {
                "total_lines": int,       # 总行数
                "non_empty_lines": int,   # 非空行数
                "code_lines": int,        # 代码行数
                "comment_lines": int,     # 注释行数
                "comment_ratio": str      # 注释比例 (百分比字符串)
            },
            "complexity": {
                "score": int,             # 复杂度分数
                "level": str              # 复杂度等级 (简单/中等/复杂/非常复杂)
            },
            "issues": list[str],          # 检测到的问题列表（仅detailed模式）
            "suggestions": list[str],     # 改进建议列表
            "analyzed_at": str            # 分析时间 (ISO格式)
        }

    Examples:
        >>> # 基础分析
        >>> result = await code_analyzer(
        ...     code="def hello(): print('hi')",
        ...     language="python",
        ...     style="basic"
        ... )
        >>> print(result['complexity']['level'])
        '简单'

        >>> # 详细分析
        >>> result = await code_analyzer(
        ...     code="def func():\n    print('debug')",
        ...     language="python",
        ...     style="detailed"
        ... )
        >>> print(result['issues'])
        ['调试代码残留: 存在print语句']

    Raises:
        ValueError: 如果language或style参数无效
    """
    # 参数验证
    if not isinstance(code, str):
        raise ValueError(f"code参数必须是字符串，得到: {type(code)}")

    language = language.lower()
    supported_languages = {"python", "javascript", "typescript", "js", "ts"}
    if language not in supported_languages:
        raise ValueError(
            f"不支持的语言: {language}. "
            f"支持的语言: {', '.join(sorted(supported_languages))}"
        )

    if style not in {"basic", "detailed"}:
        raise ValueError(
            f"无效的style参数: {style}. "
            f"必须是 'basic' 或 'detailed'"
        )

    # 模拟分析延迟（实际工具中可能有真实的计算）
    await asyncio.sleep(0.01)

    # 基础分析
    lines = code.split("\n")
    total_lines = len(lines)
    non_empty_lines = len([l for l in lines if l.strip()])
    comment_lines = 0
    code_lines = 0

    # 语言特定分析
    if language == "python":
        # Python注释分析
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                comment_lines += 1
            elif stripped and not stripped.startswith("#"):
                code_lines += 1

        # 复杂度检测（基于控制流关键词）
        complexity_keywords = [
            "if ", "elif ", "else:", "for ", "while ",
            "try:", "except", "with ", "def ", "class ",
        ]
        complexity_score = sum(code.count(kw) for kw in complexity_keywords)

        # 问题检测（仅detailed模式）
        issues = []
        if style == "detailed":
            if "print(" in code:
                issues.append("调试代码残留: 存在print语句")
            if code.count("def ") > 10:
                issues.append("函数过多: 建议拆分为多个模块")
            if any(len(line) > 100 for line in lines):
                issues.append("代码过长: 存在超过100字符的行")

    elif language in {"javascript", "typescript", "js", "ts"}:
        # JavaScript/TypeScript注释分析
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("//", "/*", "*")):
                comment_lines += 1
            elif stripped:
                code_lines += 1

        # 复杂度检测
        complexity_keywords = [
            "if ", "else if", "else", "for ", "while ",
            "try", "catch", "function ", "=>", "class ",
        ]
        complexity_score = sum(code.count(kw) for kw in complexity_keywords)

        issues = []
        if style == "detailed":
            if "console.log" in code:
                issues.append("调试代码残留: 存在console.log")
            if "var " in code:
                issues.append("代码现代化: 建议使用const/let替代var")

    else:
        # 通用分析（不应该到达这里，因为有参数验证）
        comment_lines = 0
        code_lines = non_empty_lines
        complexity_score = 0
        issues = []

    # 计算复杂度等级
    if complexity_score < 5:
        complexity_level = "简单"
    elif complexity_score < 15:
        complexity_level = "中等"
    elif complexity_score < 30:
        complexity_level = "复杂"
    else:
        complexity_level = "非常复杂"

    # 生成改进建议
    suggestions = []
    if code_lines > 50:
        suggestions.append("保持函数简洁 (< 50行)")
    if comment_lines / max(non_empty_lines, 1) < 0.1:
        suggestions.append("添加更多注释")
    if complexity_score > 20:
        suggestions.append("考虑拆分复杂逻辑")

    return {
        "language": language,
        "statistics": {
            "total_lines": total_lines,
            "non_empty_lines": non_empty_lines,
            "code_lines": code_lines,
            "comment_lines": comment_lines,
            "comment_ratio": f"{comment_lines/max(non_empty_lines, 1)*100:.1f}%",
        },
        "complexity": {
            "score": complexity_score,
            "level": complexity_level
        },
        "issues": issues if style == "detailed" else [],
        "suggestions": suggestions,
        "analyzed_at": datetime.now().isoformat(),
    }


# 便捷函数：快速分析代码（使用默认参数）
async def quick_analyze(code: str, language: str = "python") -> dict[str, Any]:
    """
    快速分析代码（使用基础模式）

    Args:
        code: 要分析的代码
        language: 编程语言

    Returns:
        分析结果字典
    """
    return await code_analyzer(code=code, language=language, style="basic")


# 便捷函数：深度分析代码（使用详细模式）
async def deep_analyze(code: str, language: str = "python") -> dict[str, Any]:
    """
    深度分析代码（使用详细模式，包含问题检测）

    Args:
        code: 要分析的代码
        language: 编程语言

    Returns:
        分析结果字典（包含问题检测和建议）
    """
    return await code_analyzer(code=code, language=language, style="detailed")


if __name__ == "__main__":
    # 简单测试
    import asyncio

    async def test():
        test_code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print(factorial(5))
"""

        result = await deep_analyze(test_code, "python")

        print("代码分析结果:")
        print(f"语言: {result['language']}")
        print(f"总行数: {result['statistics']['total_lines']}")
        print(f"代码行: {result['statistics']['code_lines']}")
        print(f"注释行: {result['statistics']['comment_lines']}")
        print(f"注释比例: {result['statistics']['comment_ratio']}")
        print(f"复杂度: {result['complexity']['level']} ({result['complexity']['score']}分)")
        print(f"问题: {result['issues']}")
        print(f"建议: {result['suggestions']}")

    asyncio.run(test())
