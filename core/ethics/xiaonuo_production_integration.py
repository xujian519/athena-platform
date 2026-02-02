#!/usr/bin/env python3
"""
小诺伦理框架生产集成脚本
Production Integration Script for Xiaonuo Ethics Framework

此脚本为小诺主程序添加伦理约束,确保所有行动符合宪法原则
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


# 确保项目根目录在sys.path中
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ.setdefault("ATHENA_PROJECT_ROOT", str(project_root))

from core.ethics.xiaonuo_ethics_patch import XiaonuoEthicsWrapper, patch_xiaonuo


def apply_ethics_to_xiaonuo(xiaonuo_instance, methods_to_wrap=None) -> None:
    """为小诺实例应用伦理约束

    Args:
        xiaonuo_instance: 小诺主程序实例
        methods_to_wrap: 要包装的方法列表(可选)

    Returns:
        XiaonuoEthicsWrapper: 伦理包装器实例
    """
    if methods_to_wrap is None:
        # 默认包装核心方法
        methods_to_wrap = [
            "handle_request",  # 处理用户请求(核心)
            "handle_development_request",  # 开发请求
            "handle_service_request",  # 服务控制请求
            "handle_knowledge_request",  # 知识查询请求
            "handle_planning_request",  # 规划请求
            "handle_decision_request",  # 决策请求
        ]

    print("\n" + "=" * 60)
    print("🛡️ 应用伦理约束到小诺")
    print("=" * 60)

    # 应用伦理补丁
    wrapper = patch_xiaonuo(xiaonuo_instance)

    # 包装额外的方法
    for method_name in methods_to_wrap:
        if hasattr(xiaonuo_instance, method_name):
            wrapper.wrap_method(method_name)
            print(f"✅ 已为 {method_name} 添加伦理约束")
        else:
            print(f"⚠️ 方法 {method_name} 不存在,跳过")

    print("=" * 60)
    print("✅ 伦理约束应用完成!")
    print("=" * 60)

    return wrapper


def create_ethics_enabled_xiaonuo() -> Any:
    """创建带有伦理约束的小诺实例

    Returns:
        tuple: (xiaonuo_instance, ethics_wrapper)
    """
    # 导入小诺主类(使用importlib处理带连字符的目录名)
    import importlib.util

    xiaonuo_path = project_root / "services" / "intelligent-collaboration" / "xiaonuo_main.py"

    if not xiaonuo_path.exists():
        print(f"❌ 找不到小诺主程序: {xiaonuo_path}")
        return None, None

    try:
        # 动态导入模块
        spec = importlib.util.spec_from_file_location("xiaonuo_main", xiaonuo_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["xiaonuo_main"] = module
        spec.loader.exec_module(module)

        XiaonuoMain = module.XiaonuoMain
    except Exception as e:
        print(f"❌ 无法导入XiaonuoMain: {e}")
        print("请确保项目结构正确")
        import traceback

        traceback.print_exc()
        return None, None

    # 创建小诺实例
    print("\n🌸 创建小诺实例...")
    xiaonuo = XiaonuoMain()

    # 应用伦理约束
    ethics_wrapper = apply_ethics_to_xiaonuo(xiaonuo)

    return xiaonuo, ethics_wrapper


async def run_ethics_protected_xiaonuo():
    """运行受伦理保护的小诺"""
    xiaonuo, wrapper = create_ethics_enabled_xiaonuo()

    if xiaonuo is None or wrapper is None:
        print("❌ 创建伦理保护的小诺失败")
        return

    # 显示伦理状态
    wrapper.print_ethics_status()

    # 启动小诺
    await xiaonuo.start_xiaonuo(interactive=True)


def verify_ethics_integration() -> bool:
    """验证伦理集成"""
    print("\n🧪 验证伦理框架集成\n")

    # 创建测试实例
    class TestXiaonuo:
        def handle_request(self, query: str, confidence: float = 0.8) -> Any | None:
            return f"处理: {query}"

    xiaonuo = TestXiaonuo()
    wrapper = apply_ethics_to_xiaonuo(xiaonuo)

    # 测试1:高置信度查询
    print("\n✅ 测试1: 高置信度查询")
    result = xiaonuo.handle_request("检索专利信息", confidence=0.9)
    print(f"结果: {result}")

    # 测试2:低置信度查询(应触发协商)
    print("\n⚠️ 测试2: 低置信度查询")
    result = xiaonuo.handle_request("我不确定的问题", confidence=0.5)
    print(f"结果: {result}")

    # 打印报告
    wrapper.print_ethics_status()

    return wrapper


# 便捷函数
def get_ethics_protected_xiaonuo() -> Any | None:
    """获取受伦理保护的小诺实例(便捷函数)"""
    return create_ethics_enabled_xiaonuo()


if __name__ == "__main__":
    import asyncio

    print("=" * 60)
    print("🛡️ 小诺伦理框架生产集成")
    print("=" * 60)

    # 检查命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "verify":
            # 验证模式
            verify_ethics_integration()

        elif command == "run":
            # 运行模式
            asyncio.run(run_ethics_protected_xiaonuo())

        else:
            print(f"❌ 未知命令: {command}")
            print("用法:")
            print("  python xiaonuo_production_integration.py verify  # 验证集成")
            print("  python xiaonuo_production_integration.py run     # 运行小诺")
    else:
        # 默认:验证模式
        verify_ethics_integration()

        print("\n💡 要启动受伦理保护的小诺,请运行:")
        print("   python xiaonuo_production_integration.py run")
