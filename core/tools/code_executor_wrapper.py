"""
code_executor工具包装器

⚠️ 安全警告：
此工具使用exec()执行Python代码，存在严重安全风险：
- 代码注入攻击
- 无限循环风险
- 文件系统访问风险
- 内存耗尽风险
- 恶意代码执行风险

仅在受控环境中使用，且需要用户明确授权。
"""

from __future__ import annotations

import sys
from typing import Any, Dict

# 添加项目路径
project_root = __file__.split("/core/tools/")[0]
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.tools.tool_implementations import code_executor_handler


class CodeExecutorWrapper:
    """
    代码执行器包装器

    ⚠️ 安全警告：
    此工具使用exec()执行Python代码，存在严重安全风险。
    当前沙箱实现不完整，不应在生产环境中使用。

    安全限制：
    - 代码长度限制：1000字符
    - 受限的内置函数
    - 输出重定向
    - 超时保护（不完整）

    推荐使用场景：
    - 教育/演示环境
    - 可信代码执行
    - 受控的测试环境
    - 开发调试环境

    不推荐使用场景：
    - 生产环境
    - 用户提交的代码
    - 不受信任的代码
    - 互联网公开服务
    """

    # 安全级别
    SECURITY_LEVEL = "HIGH_RISK"

    # 推荐的替代方案
    ALTERNATIVES = [
        "Docker容器隔离执行",
        "RestrictedPython库",
        "PyPy沙箱",
        "在线代码执行服务（如Judge0）",
    ]

    def __init__(self) -> None:
        """初始化代码执行器包装器"""
        self._warning_printed = False

    def _print_security_warning(self) -> None:
        """打印安全警告"""
        if not self._warning_printed:
            warning = f"""
{'=' * 70}
⚠️  安全警告 ⚠️
{'=' * 70}
您正在使用code_executor工具，该工具存在以下安全风险：

1. 代码注入攻击 - 恶意代码可能窃取数据或破坏系统
2. 无限循环风险 - 可能导致系统挂起
3. 文件系统访问 - 可能读取或修改敏感文件
4. 资源耗尽攻击 - 可能消耗所有CPU/内存资源
5. 沙箱逃逸风险 - 当前沙箱实现不完整

当前安全级别: {self.SECURITY_LEVEL}

推荐替代方案:
{chr(10).join(f'  - {alt}' for alt in self.ALTERNATIVES)}

使用前请确保:
  ✓ 代码来源可信
  ✓ 环境已隔离（如Docker容器）
  ✓ 已设置资源限制
  ✓ 已备份重要数据
  ✓ 已获得用户明确授权

继续使用表示您了解并接受上述风险。
{'=' * 70}
"""
            print(warning, file=sys.stderr)
            self._warning_printed = True

    async def execute(
        self,
        code: str,
        timeout: int = 5,
        context: Dict[str, Any] | None = None,
        require_authorization: bool = True,
    ) -> Dict[str, Any]:
        """
        执行Python代码

        Args:
            code: 要执行的Python代码
            timeout: 超时时间（秒）
            context: 上下文信息
            require_authorization: 是否需要用户授权

        Returns:
            执行结果字典，包含:
            - success: 是否成功
            - output: 标准输出
            - error: 错误信息
            - execution_time: 执行时间（秒）

        Raises:
            ValueError: 代码不符合安全要求
            PermissionError: 未获得用户授权

        Example:
            >>> wrapper = CodeExecutorWrapper()
            >>> result = await wrapper.execute("print('Hello')")
            >>> print(result['output'])
            Hello
        """
        # 打印安全警告
        self._print_security_warning()

        # 检查授权
        if require_authorization:
            if not self._check_authorization():
                raise PermissionError(
                    "执行代码需要用户明确授权。"
                    "请设置require_authorization=False，或使用安全的替代方案。"
                )

        # 验证代码
        self._validate_code(code)

        # 执行代码
        params = {
            "code": code,
            "timeout": timeout,
        }

        result = await code_executor_handler(params, context or {})

        return result

    def _validate_code(self, code: str) -> None:
        """
        验证代码安全性

        Args:
            code: 要验证的代码

        Raises:
            ValueError: 代码不符合安全要求
        """
        # 检查代码长度
        if len(code) > 1000:
            raise ValueError(f"代码过长 ({len(code)} > 1000字符)")

        # 检查危险操作（简单检测）
        dangerous_patterns = [
            "import os",
            "import sys",
            "import subprocess",
            "import shutil",
            "__import__",
            "eval(",
            "compile(",
            "exec(",
            "open(",
            "file(",
            "input(",
        ]

        code_lower = code.lower()
        detected_patterns = []

        for pattern in dangerous_patterns:
            if pattern in code_lower:
                detected_patterns.append(pattern)

        if detected_patterns:
            raise ValueError(
                f"代码包含危险操作: {', '.join(detected_patterns)}。"
                "这些操作可能存在安全风险。"
            )

    def _check_authorization(self) -> bool:
        """
        检查用户授权

        Returns:
            是否已授权

        Note:
            这是一个简化的实现。实际应用中应该使用更安全的授权机制。
        """
        # 在实际应用中，这里应该检查用户是否明确授权
        # 例如：通过环境变量、配置文件或交互式确认

        # 简化实现：检查环境变量
        import os

        authorized = os.getenv("CODE_EXECUTOR_AUTHORIZED", "false").lower() == "true"

        if not authorized:
            print(
                "\n⚠️  需要授权才能执行代码。\n"
                "请设置环境变量: export CODE_EXECUTOR_AUTHORIZED=true\n"
                "或在调用时设置: require_authorization=False\n",
                file=sys.stderr,
            )

        return authorized

    def get_security_info(self) -> Dict[str, Any]:
        """
        获取安全信息

        Returns:
            安全信息字典
        """
        return {
            "security_level": self.SECURITY_LEVEL,
            "sandbox_complete": False,
            "timeout_protection": "Incomplete",
            "resource_limits": "Not implemented",
            "isolation": "None",
            "recommended_for_production": False,
            "alternatives": self.ALTERNATIVES,
            "risks": [
                "Code injection",
                "Infinite loops",
                "File system access",
                "Resource exhaustion",
                "Sandbox escape",
            ],
        }

    def print_security_info(self) -> None:
        """打印安全信息"""
        info = self.get_security_info()

        print(f"\n{'=' * 70}")
        print("代码执行器安全信息")
        print(f"{'=' * 70}")
        print(f"安全级别: {info['security_level']}")
        print(f"沙箱完整性: {info['sandbox_complete']}")
        print(f"超时保护: {info['timeout_protection']}")
        print(f"资源限制: {info['resource_limits']}")
        print(f"隔离机制: {info['isolation']}")
        print(f"推荐用于生产环境: {info['recommended_for_production']}")

        print(f"\n已知风险:")
        for risk in info["risks"]:
            print(f"  - {risk}")

        print(f"\n推荐替代方案:")
        for alt in info["alternatives"]:
            print(f"  - {alt}")

        print(f"{'=' * 70}\n")


# 便捷函数
async def execute_code(
    code: str,
    timeout: int = 5,
    require_authorization: bool = True,
) -> Dict[str, Any]:
    """
    执行Python代码（便捷函数）

    Args:
        code: 要执行的Python代码
        timeout: 超时时间（秒）
        require_authorization: 是否需要用户授权

    Returns:
        执行结果字典

    Example:
        >>> result = await execute_code("print('Hello')")
        >>> print(result['output'])
        Hello
    """
    wrapper = CodeExecutorWrapper()
    return await wrapper.execute(
        code=code,
        timeout=timeout,
        require_authorization=require_authorization,
    )


if __name__ == "__main__":
    import asyncio

    async def demo() -> None:
        """演示代码执行"""
        wrapper = CodeExecutorWrapper()
        wrapper.print_security_info()

        # 示例1: 简单代码执行
        print("示例1: 简单代码执行")
        result = await wrapper.execute(
            code="print('Hello, World!')",
            require_authorization=False,
        )
        print(f"输出: {result['output']}")
        print(f"成功: {result['success']}")
        print(f"执行时间: {result['execution_time']:.4f}秒")

    asyncio.run(demo())
