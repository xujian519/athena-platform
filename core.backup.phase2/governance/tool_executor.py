#!/usr/bin/env python3
from __future__ import annotations
"""
工具执行器 - 动态加载和执行tools目录中的函数
Tool Executor - Dynamically load and execute functions from tools directory

这个模块实现了工具的实际执行能力,将静态的函数元数据转换为可调用的工具。

核心功能:
1. 动态导入tools目录中的Python模块
2. 安全地执行工具函数
3. 处理async和sync函数
4. 参数验证和类型转换
5. 执行结果标准化

Author: Athena Team
Date: 2026-02-24
Version: 1.0.0
"""

import asyncio
import inspect
import logging
import sys
import traceback
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

logger = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    """工具执行错误"""
    def __init__(self, message: str, tool_id: str = "", original_error: Exception = None):
        super().__init__(message)
        self.tool_id = tool_id
        self.original_error = original_error


class SafeToolExecutor:
    """
    安全工具执行器

    提供安全的工具执行环境,支持:
    - 动态模块加载
    - 参数验证
    - 超时控制
    - 异常处理
    - 结果格式化
    """

    def __init__(self, tools_dir: Path | str = None, timeout: int = 60):
        """
        初始化工具执行器

        Args:
            tools_dir: 工具目录路径,默认为项目根目录/tools
            timeout: 默认超时时间(秒)
        """
        self.tools_dir = Path(tools_dir) if tools_dir else PROJECT_ROOT / "tools"
        self.timeout = timeout

        # 模块缓存 {module_name: module}
        self._module_cache: dict[str, Any] = {}

        # 函数缓存 {tool_id: function}
        self._function_cache: dict[str, Callable] = {}

        logger.info(f"✅ 工具执行器已初始化,目录: {self.tools_dir}")

    def _parse_tool_id(self, tool_id: str) -> tuple[str, str]:
        """
        解析工具ID

        Args:
            tool_id: 工具ID (如 "utility.platform_cleanup.main")

        Returns:
            (module_name, function_name) 元组
        """
        parts = tool_id.split(".")
        if len(parts) < 2:
            raise ToolExecutionError(f"无效的工具ID: {tool_id}", tool_id)

        # 假设格式为 category.module_name.function_name
        function_name = parts[-1]
        module_file = parts[-2]  # 不包含.py

        return (module_file, function_name)

    async def _load_module(self, module_file: str) -> Any:
        """
        动态加载模块

        Args:
            module_file: 模块文件名 (不含.py扩展名)

        Returns:
            模块对象

        Raises:
            ToolExecutionError: 如果模块加载失败
        """
        # 检查缓存
        if module_file in self._module_cache:
            return self._module_cache[module_file]

        # 构建模块路径
        module_path = self.tools_dir / f"{module_file}.py"

        if not module_path.exists():
            raise ToolExecutionError(f"模块文件不存在: {module_path}", module_file)

        try:
            # 动态导入模块
            import importlib.util

            spec = importlib.util.spec_from_file_location(module_file, str(module_path))
            if spec is None or spec.loader is None:
                raise ToolExecutionError(f"无法创建模块规格: {module_file}", module_file)

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_file] = module
            spec.loader.exec_module(module)

            # 缓存模块
            self._module_cache[module_file] = module

            logger.debug(f"✅ 模块已加载: {module_file}")
            return module

        except Exception as e:
            raise ToolExecutionError(f"模块加载失败: {str(e)}", module_file, e) from e

    async def _get_function(self, tool_id: str) -> Callable:
        """
        获取工具函数

        Args:
            tool_id: 工具ID

        Returns:
            可调用函数

        Raises:
            ToolExecutionError: 如果函数获取失败
        """
        # 检查缓存
        if tool_id in self._function_cache:
            return self._function_cache[tool_id]

        # 解析工具ID
        module_file, function_name = self._parse_tool_id(tool_id)

        # 加载模块
        module = await self._load_module(module_file)

        # 获取函数
        if not hasattr(module, function_name):
            raise ToolExecutionError(
                f"函数不存在: {function_name} (模块: {module_file})",
                tool_id
            )

        func = getattr(module, function_name)

        if not callable(func):
            raise ToolExecutionError(
                f"对象不可调用: {function_name} (类型: {type(func).__name__})",
                tool_id
            )

        # 缓存函数
        self._function_cache[tool_id] = func

        logger.debug(f"✅ 函数已获取: {tool_id}")
        return func

    def _validate_parameters(self, func: Callable, parameters: dict[str, Any]) -> dict[str, Any]:
        """
        验证和规范化参数

        Args:
            func: 函数对象
            parameters: 原始参数

        Returns:
            验证后的参数字典
        """
        try:
            sig = inspect.signature(func)
            validated = {}

            for param_name, param in sig.parameters.items():
                if param_name in parameters:
                    validated[param_name] = parameters[param_name]
                elif param.default == inspect.Parameter.empty:
                    # 必需参数缺失
                    raise ToolExecutionError(
                        f"缺少必需参数: {param_name}",
                        ""
                    )

            return validated

        except ToolExecutionError:
            raise
        except Exception as e:
            raise ToolExecutionError(f"参数验证失败: {str(e)}", "", e) from e

    async def execute(
        self,
        tool_id: str,
        parameters: dict[str, Any],
        timeout: int | None = None,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        执行工具

        Args:
            tool_id: 工具ID
            parameters: 执行参数
            timeout: 超时时间(秒),None使用默认值
            context: 执行上下文

        Returns:
            执行结果字典

        Raises:
            ToolExecutionError: 如果执行失败
        """
        timeout = timeout or self.timeout
        start_time = datetime.now()
        context = context or {}

        logger.info(f"🔧 执行工具: {tool_id}, 参数: {list(parameters.keys())}")

        try:
            # 获取函数
            func = await self._get_function(tool_id)

            # 验证参数
            validated_params = self._validate_parameters(func, parameters)

            # 执行函数
            if inspect.iscoroutinefunction(func):
                # 异步函数
                result = await asyncio.wait_for(
                    func(**validated_params),
                    timeout=timeout
                )
            else:
                # 同步函数 - 在线程池中执行
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: func(**validated_params)),
                    timeout=timeout
                )

            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"✅ 工具执行成功: {tool_id}, 耗时: {execution_time:.2f}秒")

            return {
                "success": True,
                "result": result,
                "execution_time": execution_time,
                "tool_id": tool_id,
                "timestamp": datetime.now().isoformat()
            }

        except asyncio.TimeoutError:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"⏱️ 工具执行超时: {tool_id}, 超时: {timeout}秒")
            raise ToolExecutionError(
                f"工具执行超时({timeout}秒): {tool_id}",
                tool_id
            ) from None

        except ToolExecutionError:
            raise

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ 工具执行失败: {tool_id}, 错误: {str(e)}")
            logger.debug(traceback.format_exc())

            raise ToolExecutionError(
                f"工具执行失败: {str(e)}",
                tool_id,
                e
            ) from e

    def clear_cache(self):
        """清空缓存"""
        self._module_cache.clear()
        self._function_cache.clear()
        logger.info("🗑️ 工具执行器缓存已清空")

    def get_cache_info(self) -> dict[str, int]:
        """获取缓存信息"""
        return {
            "cached_modules": len(self._module_cache),
            "cached_functions": len(self._function_cache)
        }


# ================================
# 全局单例
# ================================

_executor: SafeToolExecutor | None = None


def get_tool_executor(tools_dir: str | Path | None = None, timeout: int = 60) -> SafeToolExecutor:
    """获取工具执行器单例"""
    global _executor
    if _executor is None:
        _executor = SafeToolExecutor(tools_dir=tools_dir, timeout=timeout)
    return _executor


# ================================
# 测试代码
# ================================


async def main():
    """主函数(用于测试)"""
    import logging
    logging.basicConfig(level=logging.INFO)

    print("=" * 80)
    print("🧪 工具执行器测试")
    print("=" * 80)
    print()

    # 获取执行器
    executor = get_tool_executor()

    # 测试执行一个简单工具
    print("⚙️ 测试: 执行 analyze_m4_usage.main")
    try:
        result = await executor.execute(
            "utility.analyze_m4_usage.main",
            {},
            timeout=30
        )

        print(f"   结果: {result['success']}")
        if result['success']:
            print(f"   执行时间: {result['execution_time']:.2f}秒")
    except ToolExecutionError as e:
        print(f"   执行失败: {e}")

    print()

    # 显示缓存信息
    cache_info = executor.get_cache_info()
    print(f"📦 缓存信息: {cache_info}")

    print()
    print("=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
