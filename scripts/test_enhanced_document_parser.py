#!/usr/bin/env python3
"""
增强文档解析器快速测试

测试OCR功能和文档解析能力
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tools.enhanced_document_parser import (
    EnhancedDocumentParser,
    enhanced_document_parser_handler,
    parse_document,
)


async def test_text_file():
    """测试文本文件解析"""
    print("=" * 60)
    print("📄 测试1: 文本文件解析")
    print("=" * 60)

    # 创建测试文件
    test_file = Path("/tmp/test_document.txt")
    test_file.write_text("""
# 测试文档

这是用于测试增强文档解析器的示例文档。

## 功能列表

1. 文本文件解析
2. PDF OCR识别
3. 图片OCR识别
4. 表格提取

## 结论

增强文档解析器支持多种格式！
""", encoding="utf-8")

    # 解析文件
    result = await parse_document(str(test_file))

    if result["success"]:
        print("✅ 解析成功")
        print(f"   方法: {result['method']}")
        print(f"   内容长度: {len(result['content'])} 字符")
        print(f"   行数: {result['metadata']['line_count']}")
        print(f"   字数: {result['metadata']['word_count']}")
        print(f"\n   内容预览:")
        print("   " + "\n   ".join(result['content'].split('\n')[:5]))
    else:
        print(f"❌ 解析失败: {result.get('error')}")

    # 清理
    test_file.unlink()
    return result["success"]


async def test_mineru_connection():
    """测试minerU连接"""
    print("\n" + "=" * 60)
    print("🔍 测试2: minerU服务连接")
    print("=" * 60)

    parser = EnhancedDocumentParser()

    try:
        health = await parser.check_mineru_health()

        if health:
            print("✅ minerU服务可用")
            print(f"   API地址: {parser.mineru_url}")
        else:
            print("⚠️  minerU服务不可用")
            print("   请启动minerU服务：")
            print("   docker run -p 7860:7860 mineru/mineru:latest")

        await parser.close()
        return health

    except Exception as e:
        print(f"❌ 连接检查失败: {e}")
        return False


async def test_handler():
    """测试处理器函数"""
    print("\n" + "=" * 60)
    print("🔧 测试3: 处理器函数")
    print("=" * 60)

    # 创建测试文件
    test_file = Path("/tmp/test_handler.txt")
    test_file.write_text("处理器测试内容")

    # 测试处理器
    result = await enhanced_document_parser_handler({
        "file_path": str(test_file),
        "use_ocr": False,
        "max_length": 1000
    }, {})

    if result["success"]:
        print("✅ 处理器工作正常")
        print(f"   解析方法: {result.get('method')}")
    else:
        print(f"❌ 处理器失败: {result.get('error')}")

    # 清理
    test_file.unlink()
    return result["success"]


async def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("⚠️  测试4: 错误处理")
    print("=" * 60)

    tests = [
        ("缺少参数", {}),
        ("空路径", {"file_path": ""}),
        ("不存在的文件", {"file_path": "/tmp/nonexistent_12345.txt"}),
        ("不支持的格式", {"file_path": "/tmp/test.xyz", "use_ocr": False}),
    ]

    all_passed = True
    for name, params in tests:
        result = await enhanced_document_parser_handler(params, {})

        if not result["success"]:
            print(f"✅ {name}: 正确返回错误")
        else:
            print(f"❌ {name}: 应该返回错误但没有")
            all_passed = False

    return all_passed


async def main():
    """主测试函数"""
    print("\n🚀 增强文档解析器测试套件")
    print()

    results = []

    # 运行测试
    results.append(("文本文件解析", await test_text_file()))
    results.append(("minerU连接", await test_mineru_connection()))
    results.append(("处理器函数", await test_handler()))
    results.append(("错误处理", await test_error_handling()))

    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
