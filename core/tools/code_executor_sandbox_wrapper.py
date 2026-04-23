#!/usr/bin/env python3
"""
code_executor_sandbox工具包装器

⚠️ 安全警告：
此工具使用沙箱隔离机制执行Python代码，安全性已大幅提升：
- 进程隔离（subprocess）
- 资源限制（CPU、内存、文件大小）
- 超时控制
- 危险操作阻止
- 临时文件隔离

虽然安全性提升，但仍需在受控环境中使用。
"""

from __future__ import annotations

import logging
from typing import Any, Dict

# 添加项目路径
project_root = __file__.split("/core/tools/")[0]
if project_root not in __import__("sys").path:
    __import__("sys").path.insert(0, project_root)

from core.tools.code_executor_sandbox import execute_in_sandbox

logger = logging.getLogger(__name__)


async def code_executor_sandbox_handler(
    params: dict[str, Any],
    context: dict[str, Any],  # noqa: ARG001 (保留用于接口兼容性)
) -> dict[str, Any]:
    """
    沙箱化代码执行处理器 - 符合统一工具接口

    功能:
    1. 安全执行Python代码片段
    2. 进程隔离和资源限制
    3. 超时控制和危险操作阻止
    4. 输出捕获和错误处理

    Args:
        params: {
            "code": str,  # 要执行的代码（必需）
            "timeout": float,  # 超时时间（秒），默认10秒
            "max_memory": int,  # 最大内存（字节），默认100MB
        }
        context: 上下文信息（当前未使用，保留用于接口兼容性）

    Returns:
        Dict[str, Any]: 执行结果字典，包含：
            - success: bool, 是否成功
            - output: str, 标准输出
            - error: str, 错误信息
            - execution_time: float, 执行时间（秒）
            - timeout: bool, 是否超时
            - memory_exceeded: bool, 是否超内存
            - timestamp: str, 时间戳

    Raises:
        ValueError: 如果code参数无效或缺失

    Examples:
        >>> # 简单执行
        >>> result = await code_executor_sandbox_handler(
        ...     params={"code": "print('Hello, World!')"},
        ...     context={}
        ... )
        >>> print(result['output'])
        Hello, World!

        >>> # 带超时和内存限制
        >>> result = await code_executor_sandbox_handler(
        ...     params={
        ...         "code": "for i in range(100): print(i)",
        ...         "timeout": 5.0,
        ...         "max_memory": 50 * 1024 * 1024
        ...     },
        ...     context={}
        ... )
        >>> print(result['success'])
        True

        >>> # 危险操作阻止
        >>> result = await code_executor_sandbox_handler(
        ...     params={"code": "import os\nprint(os.getcwd())"},
        ...     context={}
        ... )
        >>> print(result['success'])
        False
        >>> print(result['error'])
        检测到危险操作: import os
    """
    # 参数验证
    if not isinstance(params, dict):
        raise ValueError(f"params必须是字典，得到: {type(params)}")

    code = params.get("code", "")
    if not isinstance(code, str):
        raise ValueError(f"code参数必须是字符串，得到: {type(code)}")

    if not code.strip():
        raise ValueError("code参数不能为空")

    timeout = params.get("timeout", 10.0)
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ValueError(f"timeout必须是正数，得到: {timeout}")

    max_memory = params.get("max_memory", 100 * 1024 * 1024)  # 默认100MB
    if not isinstance(max_memory, int) or max_memory <= 0:
        raise ValueError(f"max_memory必须是正整数，得到: {max_memory}")

    # 记录执行请求
    logger.info(f"执行沙箱化代码: 长度={len(code)}字符, 超时={timeout}秒, 内存={max_memory}字节")

    try:
        # 在沙箱中执行代码
        result = await execute_in_sandbox(
            code=code,
            timeout=timeout,
            max_memory=max_memory
        )

        # 记录执行结果
        if result['success']:
            logger.info(f"✅ 沙箱执行成功: 耗时={result['execution_time']:.3f}秒")
        else:
            logger.warning(f"⚠️ 沙箱执行失败: {result['error'][:100]}")

        return result

    except Exception as e:
        logger.error(f"❌ 沙箱执行异常: {e}")
        return {
            "success": False,
            "output": "",
            "error": f"沙箱执行异常: {str(e)}",
            "execution_time": 0.0,
            "timeout": False,
            "memory_exceeded": False,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        }


# ==================== 便捷函数 ====================

async def execute_code_sandbox(
    code: str,
    timeout: float = 10.0,
    max_memory: int = 100 * 1024 * 1024,
) -> dict[str, Any]:
    """
    在沙箱中执行代码（便捷函数）

    Args:
        code: 要执行的代码
        timeout: 超时时间（秒），默认10秒
        max_memory: 最大内存（字节），默认100MB

    Returns:
        执行结果字典

    Examples:
        >>> result = await execute_code_sandbox("print('Hello')")
        >>> print(result['output'])
        Hello
    """
    return await code_executor_sandbox_handler(
        params={"code": code, "timeout": timeout, "max_memory": max_memory},
        context={}
    )


# ==================== 测试 ====================

async def _test():
    """测试沙箱化代码执行器"""
    print("🧪 测试沙箱化代码执行器")
    print("=" * 60)

    # 测试1: 简单代码
    print("\n✅ 测试1: 简单代码执行")
    result = await execute_code_sandbox(
        code="for i in range(5):\n    print(f'Number: {i}')"
    )
    print(f"成功: {result['success']}")
    print(f"输出:\n{result['output']}")
    print(f"耗时: {result['execution_time']:.3f}秒")

    # 测试2: 超时保护
    print("\n⏱️ 测试2: 超时保护")
    result = await execute_code_sandbox(
        code="import time\ntime.sleep(20)\nprint('Should timeout')",
        timeout=2.0
    )
    print(f"成功: {result['success']}")
    print(f"超时: {result['timeout']}")
    print(f"错误: {result['error']}")

    # 测试3: 危险操作阻止
    print("\n🛡️ 测试3: 危险操作阻止")
    result = await execute_code_sandbox(
        code="import os\nprint(os.getcwd())"
    )
    print(f"成功: {result['success']}")
    print(f"错误: {result['error']}")

    # 测试4: 计算任务
    print("\n🔢 测试4: 计算任务")
    result = await execute_code_sandbox(
        code="""
result = 0
for i in range(100):
    result += i
print(f'Sum of 0-99: {result}')
"""
    )
    print(f"成功: {result['success']}")
    print(f"输出: {result['output'].strip()}")

    print("\n✅ 所有测试完成!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(_test())
