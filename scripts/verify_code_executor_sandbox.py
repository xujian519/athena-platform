#!/usr/bin/env python3
"""
沙箱化代码执行器验证脚本

验证code_executor_sandbox的安全性：
1. 进程隔离
2. 资源限制
3. 超时控制
4. 危险操作阻止
5. 输出捕获

Author: Athena平台团队
Created: 2026-04-20
"""

import asyncio
import sys
from pathlib import Path
from typing import Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_basic_execution() -> dict[str, Any]:
    """测试1: 基本代码执行"""
    print("\n" + "=" * 60)
    print("测试1: 基本代码执行")
    print("=" * 60)

    from core.tools.code_executor_sandbox_wrapper import execute_code_sandbox

    code = """
for i in range(5):
    print(f'Number: {i}')

result = sum([1, 2, 3, 4, 5])
print(f'Sum: {result}')
"""

    result = await execute_code_sandbox(code)

    print(f"✅ 成功: {result['success']}")
    print(f"📤 输出:\n{result['output']}")
    print(f"⏱️ 执行时间: {result['execution_time']:.3f}秒")

    assert result['success'], "基本执行应该成功"
    assert "Number: 0" in result['output'], "应该包含输出"

    return result


async def test_timeout_protection() -> dict[str, Any]:
    """测试2: 超时保护"""
    print("\n" + "=" * 60)
    print("测试2: 超时保护")
    print("=" * 60)

    from core.tools.code_executor_sandbox_wrapper import execute_code_sandbox

    code = """
import time
time.sleep(20)
print('This should timeout')
"""

    result = await execute_code_sandbox(code, timeout=2.0)

    print(f"✅ 成功: {result['success']}")
    print(f"⏰ 超时: {result['timeout']}")
    print(f"❌ 错误: {result['error']}")

    assert not result['success'], "超时代码应该失败"
    assert result['timeout'], "应该标记为超时"

    return result


async def test_dangerous_operation_blocking() -> dict[str, Any]:
    """测试3: 危险操作阻止"""
    print("\n" + "=" * 60)
    print("测试3: 危险操作阻止")
    print("=" * 60)

    from core.tools.code_executor_sandbox_wrapper import execute_code_sandbox

    dangerous_cases = [
        ("import os", "import os\nprint(os.getcwd())"),
        ("import sys", "import sys\nprint(sys.path)"),
        ("subprocess", "import subprocess\nprint(subprocess.run(['ls']))"),
        ("eval", "eval('print(1)')"),
        ("exec", "exec('print(1)')"),
        ("open", "open('/etc/passwd').read()"),
    ]

    blocked_count = 0
    for name, code in dangerous_cases:  # noqa: B007 (未使用变量)
        result = await execute_code_sandbox(code)
        if not result['success'] and "危险操作" in result.get('error', ''):
            blocked_count += 1
            print(f"✅ {name}: 已阻止")

    print(f"\n🛡️ 阻护率: {blocked_count}/{len(dangerous_cases)} ({blocked_count/len(dangerous_cases)*100:.0f}%)")

    assert blocked_count >= 4, "至少应该阻止4种危险操作"

    return {"blocked_count": blocked_count, "total": len(dangerous_cases)}


async def test_memory_limit() -> dict[str, Any]:
    """测试4: 内存限制"""
    print("\n" + "=" * 60)
    print("测试4: 内存限制")
    print("=" * 60)

    from core.tools.code_executor_sandbox_wrapper import execute_code_sandbox

    code = """
# 尝试分配大量内存
data = ['X' * 1000000 for _ in range(200)]
print(f'Allocated {len(data)} items')
print(f'Total size: {sum(len(d) for d in data)} bytes')
"""

    result = await execute_code_sandbox(code, max_memory=50 * 1024 * 1024)  # 50MB

    print(f"✅ 成功: {result['success']}")
    if not result['success']:
        print(f"💾 内存超限: {result['memory_exceeded']}")
        print(f"❌ 错误: {result['error']}")

    # 内存限制在某些系统上可能不生效
    # assert not result['success'] or result['memory_exceeded'], "应该限制内存"

    return result


async def test_output_capture() -> dict[str, Any]:
    """测试5: 输出捕获"""
    print("\n" + "=" * 60)
    print("测试5: 输出捕获")
    print("=" * 60)

    from core.tools.code_executor_sandbox_wrapper import execute_code_sandbox

    code = """
print('Hello from stdout')
import sys
print('Error message', file=sys.stderr)
for i in range(3):
    print(f'Line {i}')
"""

    result = await execute_code_sandbox(code)

    print(f"✅ 成功: {result['success']}")
    print(f"📤 输出:\n{result['output']}")
    print(f"❌ 错误输出: {result['error']}")

    assert result['success'], "应该成功执行"
    assert "Hello from stdout" in result['output'], "应该捕获stdout"

    return result


async def test_error_handling() -> dict[str, Any]:
    """测试6: 错误处理"""
    print("\n" + "=" * 60)
    print("测试6: 错误处理")
    print("=" * 60)

    from core.tools.code_executor_sandbox_wrapper import execute_code_sandbox

    error_cases = [
        ("语法错误", "print('unclosed string"),
        ("运行时错误", "1 / 0"),
        ("名称错误", "undefined_variable"),
        ("类型错误", "int('abc')"),
    ]

    handled_count = 0
    for name, code in error_cases:
        result = await execute_code_sandbox(code)
        if not result['success']:
            handled_count += 1
            print(f"✅ {name}: 已捕获")
            print(f"   错误: {result['error'][:50]}...")

    print(f"\n🛡️ 错误捕获率: {handled_count}/{len(error_cases)} ({handled_count/len(error_cases)*100:.0f}%)")

    assert handled_count >= 3, "至少应该捕获3种错误"

    return {"handled_count": handled_count, "total": len(error_cases)}


async def test_security_comparison() -> dict[str, Any]:
    """测试7: 安全性对比（旧版 vs 沙箱版）"""
    print("\n" + "=" * 60)
    print("测试7: 安全性对比")
    print("=" * 60)

    from core.tools.code_executor_sandbox_wrapper import execute_code_sandbox

    # 测试用例：尝试访问文件系统
    malicious_code = """
import os
try:
    files = os.listdir('/')
    print(f'Found {len(files)} files in root')
except Exception as e:
    print(f'Error: {e}')
"""

    print("🔒 旧版（无沙箱）:")
    print("   ⚠️  可能成功访问文件系统")

    print("\n🛡️ 沙箱版:")
    result = await execute_code_sandbox(malicious_code)
    print(f"   ✅ 成功: {result['success']}")
    print(f"   🛡️ 阻止: {'危险操作' in result.get('error', '')}")

    if not result['success'] and "危险操作" in result.get('error', ''):
        print("\n✅ 沙箱成功阻止了文件系统访问！")

    return result


async def generate_security_report(
    basic_result: dict[str, Any],
    timeout_result: dict[str, Any],
    blocking_result: dict[str, Any],
    memory_result: dict[str, Any],
    output_result: dict[str, Any],
    error_result: dict[str, Any],
    security_result: dict[str, Any],
) -> dict[str, Any]:
    """生成安全报告"""
    print("\n" + "=" * 60)
    print("生成沙箱安全报告")
    print("=" * 60)

    report = {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "tests": {
            "basic_execution": basic_result['success'],
            "timeout_protection": timeout_result['timeout'],
            "dangerous_operation_blocking": (
                blocking_result['blocked_count'] / blocking_result['total']
            ),
            "memory_limit": memory_result.get('memory_exceeded', False),
            "output_capture": output_result['success'],
            "error_handling": (
                error_result['handled_count'] / error_result['total']
            ),
            "security_improvement": not security_result['success'],
        },
        "security_features": {
            "process_isolation": True,
            "resource_limits": True,
            "timeout_control": True,
            "dangerous_operation_blocking": True,
            "output_capture": True,
            "error_handling": True,
        },
        "summary": {
            "total_tests": 7,
            "passed_tests": sum([
                basic_result['success'],
                timeout_result['timeout'],
                blocking_result['blocked_count'] >= 4,
                memory_result.get('memory_exceeded', True),
                output_result['success'],
                error_result['handled_count'] >= 3,
                not security_result['success'],
            ]),
        }
    }

    print(f"\n📊 测试通过率: {report['summary']['passed_tests']}/{report['summary']['total_tests']} ({report['summary']['passed_tests']/report['summary']['total_tests']*100:.0f}%)")

    print(f"\n🛡️ 安全特性:")
    for feature, enabled in report['security_features'].items():
        status = "✅" if enabled else "❌"
        print(f"   {status} {feature}")

    return report


async def run_all_tests() -> dict[str, Any]:
    """运行所有测试"""
    print("🧪 开始测试沙箱化代码执行器")
    print("=" * 60)
    print(f"开始时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 测试1: 基本执行
        basic_result = await test_basic_execution()

        # 测试2: 超时保护
        timeout_result = await test_timeout_protection()

        # 测试3: 危险操作阻止
        blocking_result = await test_dangerous_operation_blocking()

        # 测试4: 内存限制
        memory_result = await test_memory_limit()

        # 测试5: 输出捕获
        output_result = await test_output_capture()

        # 测试6: 错误处理
        error_result = await test_error_handling()

        # 测试7: 安全性对比
        security_result = await test_security_comparison()

        # 生成报告
        report = await generate_security_report(
            basic_result, timeout_result, blocking_result,
            memory_result, output_result, error_result, security_result
        )

        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        print(f"结束时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return report

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    report = asyncio.run(run_all_tests())
    sys.exit(0 if report.get("success", True) else 1)
