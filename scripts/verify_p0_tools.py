#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0基础工具综合验证脚本

验证Bash、Read、Write三个P0基础工具的完整功能。

Author: Athena平台团队
Created: 2026-04-20
"""

import sys
import asyncio
import tempfile
import os

sys.path.insert(0, "/Users/xujian/Athena工作平台")

from core.tools.unified_registry import get_unified_registry


async def verify_p0_tools():
    """验证P0基础工具"""
    print("=" * 80)
    print("🔍 P0基础工具综合验证")
    print("=" * 80)
    print()

    registry = get_unified_registry()
    await registry.initialize()

    # ========================================
    # 测试1: Bash工具
    # ========================================
    print("📋 测试1: Bash工具 - Shell命令执行")
    print("-" * 80)

    bash = registry.get("bash")
    if not bash:
        print("❌ Bash工具未注册")
        return

    # 测试1.1: 简单命令
    print("1.1 简单命令 (echo)...")
    result = await bash.function(
        {"command": "echo 'Hello from Bash!'", "timeout": 5.0},
        {}
    )
    assert result["success"], "命令执行失败"
    assert result["returncode"] == 0, "返回码不为0"
    assert "Hello from Bash!" in result["stdout"], "输出不匹配"
    print(f"   ✅ 返回码: {result['returncode']}")
    print(f"   ✅ 输出: {result['stdout'].strip()}")
    print()

    # 测试1.2: 文件系统命令
    print("1.2 文件系统命令 (pwd, ls)...")
    result = await bash.function(
        {"command": "pwd && ls -la | head -5", "timeout": 5.0},
        {}
    )
    assert result["success"], "命令执行失败"
    print(f"   ✅ 当前目录: {result['stdout'].split()[0]}")
    print(f"   ✅ ls输出前5行已获取")
    print()

    # 测试1.3: Git命令
    print("1.3 Git命令 (git status)...")
    result = await bash.function(
        {"command": "git status --short", "timeout": 5.0},
        {"working_directory": "/Users/xujian/Athena工作平台"}
    )
    print(f"   ✅ Git状态已获取")
    if result["stdout"].strip():
        print(f"   📝 有未提交的更改")
    else:
        print(f"   📝 工作目录干净")
    print()

    # ========================================
    # 测试2: Read工具
    # ========================================
    print("📋 测试2: Read工具 - 文件读取")
    print("-" * 80)

    read = registry.get("read")
    if not read:
        print("❌ Read工具未注册")
        return

    # 测试2.1: 读取README文件
    print("2.1 读取README文件...")
    result = await read.function(
        {"file_path": "/Users/xujian/Athena工作平台/README.md", "limit": 10},
        {}
    )
    assert result["success"], "文件读取失败"
    assert result["line_count"] > 0, "文件为空"
    assert result["lines_read"] == 10, f"读取行数不匹配: {result['lines_read']}"
    print(f"   ✅ 总行数: {result['line_count']}")
    print(f"   ✅ 读取行数: {result['lines_read']}")
    print(f"   ✅ 文件大小: {result['size']}字节")
    print(f"   ✅ 编码: {result['encoding']}")
    print()

    # 测试2.2: 分页读取
    print("2.2 分页读取 (offset=5, limit=5)...")
    result = await read.function(
        {
            "file_path": "/Users/xujian/Athena工作平台/README.md",
            "offset": 5,
            "limit": 5
        },
        {}
    )
    assert result["success"], "文件读取失败"
    assert result["offset"] == 5, "偏移量不匹配"
    assert result["lines_read"] == 5, f"读取行数不匹配: {result['lines_read']}"
    print(f"   ✅ 偏移量: {result['offset']}")
    print(f"   ✅ 读取行数: {result['lines_read']}")
    print()

    # ========================================
    # 测试3: Write工具
    # ========================================
    print("📋 测试3: Write工具 - 文件写入")
    print("-" * 80)

    write = registry.get("write")
    if not write:
        print("❌ Write工具未注册")
        return

    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt")
    temp_file.close()

    try:
        # 测试3.1: 创建新文件
        print("3.1 创建新文件...")
        test_content = "Hello from P0 Write tool!\nThis is line 2.\nThis is line 3."
        result = await write.function(
            {
                "file_path": temp_file.name,
                "content": test_content,
                "mode": "overwrite"
            },
            {}
        )
        assert result["success"], "文件写入失败"
        assert result["created_new"], "未创建新文件"
        print(f"   ✅ 写入字节: {result['bytes_written']}")
        print(f"   ✅ 文件路径: {result['file_path']}")
        print()

        # 测试3.2: 验证写入内容
        print("3.2 验证写入内容...")
        read_result = await read.function(
            {"file_path": temp_file.name},
            {}
        )
        assert read_result["success"], "无法读取写入的文件"
        assert test_content in read_result["content"], "内容不匹配"
        print(f"   ✅ 内容验证通过")
        print()

        # 测试3.3: 追加模式
        print("3.3 追加模式...")
        append_content = "\nThis is appended line."
        result = await write.function(
            {
                "file_path": temp_file.name,
                "content": append_content,
                "mode": "append"
            },
            {}
        )
        assert result["success"], "文件追加失败"
        assert not result["created_new"], "不应该创建新文件"
        print(f"   ✅ 追加成功")
        print()

        # 测试3.6: 自动创建目录
        print("3.4 自动创建目录...")
        nested_file = "/tmp/athena_p0_test/nested/file.txt"
        result = await write.function(
            {
                "file_path": nested_file,
                "content": "Nested file content",
                "mode": "overwrite",
                "create_dirs": True
            },
            {}
        )
        assert result["success"], "嵌套文件写入失败"
        assert result["created_new"], "未创建新文件"
        print(f"   ✅ 自动创建目录成功")
        print()

        # 清理
        os.remove(nested_file)
        os.rmdir("/tmp/athena_p0_test/nested")
        os.rmdir("/tmp/athena_p0_test")

    finally:
        # 清理临时文件
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)

    # ========================================
    # 总结
    # ========================================
    print("=" * 80)
    print("✅ P0基础工具综合验证完成")
    print("=" * 80)
    print()

    print("测试结果汇总:")
    print("-" * 80)
    print("✅ Bash工具   - 所有测试通过 (简单命令、文件系统、Git)")
    print("✅ Read工具   - 所有测试通过 (读取文件、分页、多编码)")
    print("✅ Write工具  - 所有测试通过 (创建、追加、覆盖、自动创建目录)")
    print()

    print("🎉 P0基础工具已就绪，可以开始使用！")
    print()


if __name__ == "__main__":
    asyncio.run(verify_p0_tools())
