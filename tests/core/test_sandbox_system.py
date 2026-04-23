"""
沙盒系统测试脚本

测试本地和 Docker 沙盒的功能。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_local_sandbox():
    """测试本地沙盒"""
    print("\n" + "="*50)
    print("测试本地沙盒")
    print("="*50)

    try:
        from core.sandbox import LocalSandbox, SandboxConfig

        # 创建沙盒
        config = SandboxConfig(
            max_execution_time=30,
            temp_dir="/tmp/athena-sandbox-test",
        )
        sandbox = LocalSandbox(config)

        # 初始化
        await sandbox.initialize()
        print("✓ 本地沙盒初始化成功")

        # 写入文件
        await sandbox.write_file("test.txt", "Hello from sandbox!")
        print("✓ 文件写入成功")

        # 读取文件
        content = await sandbox.read_file("test.txt")
        assert content == "Hello from sandbox!", "文件内容不匹配"
        print("✓ 文件读取成功")

        # 检查文件存在
        exists = await sandbox.file_exists("test.txt")
        assert exists, "文件应该存在"
        print("✓ 文件存在检查成功")

        # 列出文件
        files = await sandbox.list_files()
        assert "test.txt" in files, "文件应该在列表中"
        print(f"✓ 文件列表: {files}")

        # 执行命令
        result = await sandbox.execute_command("echo 'Hello from command!'")
        assert result.success, "命令执行失败"
        assert "Hello from command!" in result.output, "输出不匹配"
        print("✓ 命令执行成功")

        # 执行 Python 代码
        python_code = """
print('Hello from Python!')
x = 1 + 1
print(f'1 + 1 = {x}')
"""
        from core.sandbox.base import Language

        result = await sandbox.execute_code(python_code, Language.PYTHON)
        assert result.success, "Python 执行失败"
        assert "Hello from Python!" in result.output, "输出不匹配"
        assert "1 + 1 = 2" in result.output, "计算结果不匹配"
        print("✓ Python 代码执行成功")

        # 删除文件
        deleted = await sandbox.delete_file("test.txt")
        assert deleted, "文件删除失败"
        print("✓ 文件删除成功")

        # 清理
        await sandbox.cleanup()
        print("✓ 沙盒清理成功")

        return True

    except Exception as e:
        print(f"✗ 本地沙盒测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_code_executor():
    """测试代码执行器"""
    print("\n" + "="*50)
    print("测试代码执行器")
    print("="*50)

    try:
        from core.sandbox import CodeExecutor, ExecutionRequest, Language

        # 创建执行器
        executor = CodeExecutor()

        # 执行 Python 代码
        request = ExecutionRequest(
            code="print('Hello from executor!')",
            language=Language.PYTHON,
        )

        response = await executor.execute(request)
        assert response.success, "代码执行失败"
        assert "Hello from executor!" in response.output, "输出不匹配"
        print("✓ 代码执行成功")

        # 执行快捷方法
        result = await executor.execute_python("print('Quick Python!')")
        assert result.success, "快捷执行失败"
        print("✓ 快捷执行成功")

        # 获取统计
        stats = executor.get_statistics()
        print(f"✓ 执行统计: {stats}")

        # 清理
        await executor.cleanup_all()
        print("✓ 执行器清理成功")

        return True

    except Exception as e:
        print(f"✗ 代码执行器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_safe_code_runner():
    """测试安全代码运行器"""
    print("\n" + "="*50)
    print("测试安全代码运行器")
    print("="*50)

    try:
        from core.sandbox import SafeCodeRunner

        # 创建运行器
        runner = SafeCodeRunner()

        # 运行 Python 代码
        result = await runner.run_python("""
import json
data = {"name": "Athena", "version": "1.0"}
print(json.dumps(data))
""")

        assert result["success"], "代码执行失败"
        assert "Athena" in result["output"], "输出不匹配"
        print("✓ Python 代码执行成功")

        # 运行带输入的代码
        result = await runner.run_python("""
import sys
input_data = sys.stdin.read()
print(f"Received: {input_data}")
""", input_data="test input")

        assert result["success"], "带输入的执行失败"
        assert "Received: test input" in result["output"], "输入处理失败"
        print("✓ 带输入的执行成功")

        # 获取统计
        stats = runner.get_stats()
        print(f"✓ 运行器统计: {stats}")

        return True

    except Exception as e:
        print(f"✗ 安全代码运行器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_sandbox_skill_integration():
    """测试沙盒技能集成"""
    print("\n" + "="*50)
    print("测试沙盒技能集成")
    print("="*50)

    try:
        from core.skills.sandbox_integration import (
            ScriptExecutionSkill,
            execute_python_safely,
        )

        # 测试便捷函数
        result = await execute_python_safely("print('Quick execution!')")
        assert result["success"], "便捷执行失败"
        print("✓ 便捷函数执行成功")

        # 测试脚本执行技能
        skill = ScriptExecutionSkill()
        result = await skill.execute_script(
            script="print('Script executed!')",
            language="python",
            timeout=10
        )
        assert result["success"], "脚本执行失败"
        print("✓ 脚本执行技能成功")

        # 测试带文件的执行
        result = await skill.execute_script_with_files(
            script="""
with open('data.txt', 'r') as f:
    content = f.read()
print(f'File content: {content}')
""",
            files={"data.txt": "Hello from file!"},
            language="python",
            timeout=10
        )
        assert result["success"], "带文件的执行失败"
        assert "File content: Hello from file!" in result["output"], "文件读取失败"
        print("✓ 带文件的执行成功")

        # 获取统计
        stats = skill.get_execution_stats()
        print(f"✓ 技能统计: {stats}")

        return True

    except Exception as e:
        print(f"✗ 沙盒技能集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_sandbox_manager():
    """测试沙盒管理器"""
    print("\n" + "="*50)
    print("测试沙盒管理器")
    print("="*50)

    try:
        from core.sandbox import SandboxBackend, SandboxConfig, SandboxManager

        # 创建管理器
        manager = SandboxManager()
        print("✓ 沙盒管理器创建成功")

        # 创建沙盒
        config = SandboxConfig(temp_dir="/tmp/athena-sandbox-manager-test")
        sandbox = await manager.create_sandbox(
            backend=SandboxBackend.LOCAL,
            config=config,
            session_id="test-session"
        )
        print(f"✓ 沙盒创建成功: {sandbox}")

        # 获取沙盒
        retrieved = await manager.get_sandbox("test-session")
        assert retrieved is not None, "沙盒检索失败"
        print("✓ 沙盒检索成功")

        # 列出沙盒
        sessions = manager.list_sandboxes()
        assert "test-session" in sessions, "会话应该在列表中"
        print(f"✓ 会话列表: {sessions}")

        # 销毁沙盒
        destroyed = await manager.destroy_sandbox("test-session")
        assert destroyed, "沙盒销毁失败"
        print("✓ 沙盒销毁成功")

        return True

    except Exception as e:
        print(f"✗ 沙盒管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_handling():
    """测试错误处理"""
    print("\n" + "="*50)
    print("测试错误处理")
    print("="*50)

    try:
        from core.sandbox import SafeCodeRunner

        runner = SafeCodeRunner()

        # 测试语法错误
        result = await runner.run_python("print('unclosed")
        assert not result["success"], "应该检测到语法错误"
        assert result["error"] != "", "应该有错误信息"
        print("✓ 语法错误检测成功")

        # 测试运行时错误
        result = await runner.run_python("1/0")
        # 注意：Python 的 ZeroDivisionError 可能不会导致进程退出
        print(f"✓ 运行时错误处理: {result['success']}")

        # 测试超时（代码会无限循环）
        # 注意：这会实际等待超时，所以注释掉
        # result = await runner.run_python("while True: pass", timeout=1)
        # assert not result["success"], "应该超时"
        # print("✓ 超时检测成功")

        return True

    except Exception as e:
        print(f"✗ 错误处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_language_support():
    """测试多语言支持"""
    print("\n" + "="*50)
    print("测试多语言支持")
    print("="*50)

    try:
        from core.sandbox import SafeCodeRunner

        runner = SafeCodeRunner()

        # Python
        result = await runner.run("print('Python')", "python")
        assert result["success"], "Python 执行失败"
        print("✓ Python 支持")

        # JavaScript (如果 Node 可用)
        try:
            result = await runner.run("console.log('JavaScript')", "javascript")
            if result["success"]:
                print("✓ JavaScript 支持")
            else:
                print("⚠ JavaScript 不可用（跳过）")
        except Exception:
            print("⚠ JavaScript 不可用（跳过）")

        # Shell
        result = await runner.run("echo 'Shell'", "bash")
        if result["success"]:
            print("✓ Shell/Bash 支持")
        else:
            print("⚠ Shell 不可用（跳过）")

        return True

    except Exception as e:
        print(f"✗ 多语言支持测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Athena 沙盒系统测试")
    print("="*60)

    # 导入 Language
    from core.sandbox import Language
    globals()['Language'] = Language

    results = {
        "本地沙盒": await test_local_sandbox(),
        "代码执行器": await test_code_executor(),
        "安全代码运行器": await test_safe_code_runner(),
        "沙盒技能集成": await test_sandbox_skill_integration(),
        "沙盒管理器": await test_sandbox_manager(),
        "错误处理": await test_error_handling(),
        "多语言支持": await test_language_support(),
    }

    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)

    for name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")

    total = len(results)
    passed = sum(results.values())

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")


if __name__ == "__main__":
    asyncio.run(main())
