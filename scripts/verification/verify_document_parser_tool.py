#!/usr/bin/env python3
"""
document_parser工具验证脚本

验证功能:
1. 文本文件解析(TXT, MD, JSON, YAML, XML, HTML, Python, JavaScript)
2. 文件信息提取(大小、修改时间、MIME类型)
3. 内容提取和截断
4. 编码处理
5. 错误处理(路径遍历、文件不存在)
6. 大文件处理

作者: Athena平台
日期: 2026-04-20
"""

import asyncio
import json

# 添加项目路径
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, "/Users/xujian/Athena工作平台")

from core.tools.production_tool_implementations import document_parser_handler


class DocumentParserVerifier:
    """文档解析工具验证器"""

    def __init__(self):
        self.test_results = []
        # 使用允许的测试目录
        test_base = Path("/tmp/athena_tools")
        test_base.mkdir(parents=True, exist_ok=True)
        self.temp_dir = test_base / "document_parser_test"
        self.temp_dir.mkdir(exist_ok=True)
        print(f"测试目录: {self.temp_dir}")

    def create_test_files(self) -> dict[str, Path]:
        """创建测试文件"""
        files = {}

        # 1. TXT文件
        txt_path = self.temp_dir / "test.txt"
        txt_path.write_text("这是一个测试文本文件。\n包含中文和English混合内容。\n" * 10, encoding="utf-8")
        files["txt"] = txt_path

        # 2. Markdown文件
        md_path = self.temp_dir / "test.md"
        md_content = """# 测试标题

这是一个测试Markdown文件。

## 子标题

- 列表项1
- 列表项2
- 列表项3

**加粗文本** 和 *斜体文本*

```python
def hello():
    print("Hello, World!")
```
"""
        md_path.write_text(md_content, encoding="utf-8")
        files["md"] = md_path

        # 3. JSON文件
        json_path = self.temp_dir / "test.json"
        json_data = {
            "name": "测试",
            "version": "1.0.0",
            "features": ["解析", "分析", "提取"],
            "config": {
                "encoding": "utf-8",
                "max_size": 10485760
            }
        }
        json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")
        files["json"] = json_path

        # 4. YAML文件
        yaml_path = self.temp_dir / "test.yaml"
        yaml_content = """name: 测试配置
version: 1.0.0
features:
  - 解析
  - 分析
  - 提取
config:
  encoding: utf-8
  max_size: 10485760
"""
        yaml_path.write_text(yaml_content, encoding="utf-8")
        files["yaml"] = yaml_path

        # 5. XML文件
        xml_path = self.temp_dir / "test.xml"
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<config>
    <name>测试配置</name>
    <version>1.0.0</version>
    <features>
        <feature>解析</feature>
        <feature>分析</feature>
        <feature>提取</feature>
    </features>
</config>
"""
        xml_path.write_text(xml_content, encoding="utf-8")
        files["xml"] = xml_path

        # 6. HTML文件
        html_path = self.temp_dir / "test.html"
        html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>测试页面</title>
</head>
<body>
    <h1>欢迎测试</h1>
    <p>这是一个测试HTML文件。</p>
    <ul>
        <li>项目1</li>
        <li>项目2</li>
    </ul>
</body>
</html>
"""
        html_path.write_text(html_content, encoding="utf-8")
        files["html"] = html_path

        # 7. Python文件
        py_path = self.temp_dir / "test.py"
        py_content = '''#!/usr/bin/env python3
"""测试Python模块"""

def hello_world():
    """打印Hello World"""
    print("Hello, World!")

class TestClass:
    """测试类"""

    def __init__(self, name: str):
        self.name = name

    def greet(self) -> str:
        return f"Hello, {self.name}!"

if __name__ == "__main__":
    hello_world()
'''
        py_path.write_text(py_content, encoding="utf-8")
        files["py"] = py_path

        # 8. JavaScript文件
        js_path = self.temp_dir / "test.js"
        js_content = '''// 测试JavaScript文件

function helloWorld() {
    console.log("Hello, World!");
}

class TestClass {
    constructor(name) {
        this.name = name;
    }

    greet() {
        return `Hello, ${this.name}!`;
    }
}

// 导出模块
module.exports = { helloWorld, TestClass };
'''
        js_path.write_text(js_content, encoding="utf-8")
        files["js"] = js_path

        # 9. CSS文件
        css_path = self.temp_dir / "test.css"
        css_content = '''/* 测试CSS文件 */

body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    color: #333;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

h1 {
    color: #0066cc;
    font-size: 2em;
}
'''
        css_path.write_text(css_content, encoding="utf-8")
        files["css"] = css_path

        # 10. 大文件 (测试截断)
        large_path = self.temp_dir / "large.txt"
        large_path.write_text("这是一行测试内容。\n" * 1000, encoding="utf-8")
        files["large"] = large_path

        # 11. 空文件
        empty_path = self.temp_dir / "empty.txt"
        empty_path.write_text("", encoding="utf-8")
        files["empty"] = empty_path

        return files

    async def test_file_parsing(self, file_type: str, file_path: Path) -> dict[str, Any]:
        """测试文件解析"""
        params = {
            "file_path": str(file_path),
            "extract_content": True,
            "max_length": 10000
        }

        result = await document_parser_handler(params, {})

        return {
            "type": file_type,
            "path": str(file_path),
            "success": result.get("success", False),
            "has_file_info": result.get("file_info") is not None,
            "has_content": result.get("content") is not None,
            "has_metadata": result.get("metadata") is not None,
            "has_error": result.get("error") is not None,
            "error": result.get("error"),
            "file_size": result.get("file_info", {}).get("size", 0),
            "content_length": len(result.get("content", "")),
            "is_truncated": result.get("content_truncated", False)
        }

    async def test_error_handling(self) -> dict[str, Any]:
        """测试错误处理"""
        error_tests = []

        # 1. 文件不存在
        result1 = await document_parser_handler({
            "file_path": "/nonexistent/file.txt",
            "extract_content": True
        }, {})
        error_tests.append({
            "test": "文件不存在",
            "expected_error": True,
            "actual_error": result1.get("error") is not None,
            "error_message": result1.get("error")
        })

        # 2. 路径遍历攻击 (../)
        result2 = await document_parser_handler({
            "file_path": "/etc/passwd",
            "extract_content": True
        }, {})
        error_tests.append({
            "test": "路径遍历攻击",
            "expected_error": True,
            "actual_error": result2.get("error") is not None,
            "error_message": result2.get("error")
        })

        # 3. 空路径
        result3 = await document_parser_handler({
            "file_path": "",
            "extract_content": True
        }, {})
        error_tests.append({
            "test": "空路径",
            "expected_error": True,
            "actual_error": result3.get("error") is not None,
            "error_message": result3.get("error")
        })

        return error_tests

    async def test_content_accuracy(self, file_type: str, file_path: Path) -> dict[str, Any]:
        """测试内容提取准确性"""
        original_content = file_path.read_text(encoding="utf-8")

        result = await document_parser_handler({
            "file_path": str(file_path),
            "extract_content": True,
            "max_length": 1000000  # 足够大以避免截断
        }, {})

        extracted_content = result.get("content", "")

        return {
            "type": file_type,
            "original_length": len(original_content),
            "extracted_length": len(extracted_content),
            "match_ratio": len(extracted_content) / len(original_content) if len(original_content) > 0 else 1.0,
            "is_complete": len(extracted_content) == len(original_content)
        }

    async def test_large_file_handling(self) -> dict[str, Any]:
        """测试大文件处理"""
        large_path = self.temp_dir / "very_large.txt"
        large_path.write_text("测试内容行。\n" * 10000, encoding="utf-8")  # 约130KB

        # 测试截断
        result = await document_parser_handler({
            "file_path": str(large_path),
            "extract_content": True,
            "max_length": 1000
        }, {})

        original_size = large_path.stat().st_size
        extracted_length = len(result.get("content", ""))

        return {
            "original_size": original_size,
            "extracted_length": extracted_length,
            "is_truncated": result.get("content_truncated", False),
            "truncated_ratio": extracted_length / original_size if original_size > 0 else 0
        }

    async def run_all_tests(self) -> dict[str, Any]:
        """运行所有测试"""
        print("\n" + "="*60)
        print("document_parser工具验证测试")
        print("="*60 + "\n")

        # 创建测试文件
        print("1. 创建测试文件...")
        test_files = self.create_test_files()
        print(f"   已创建 {len(test_files)} 个测试文件\n")

        # 测试文件解析
        print("2. 测试文件解析功能...")
        parse_results = []
        for file_type, file_path in test_files.items():
            result = await self.test_file_parsing(file_type, file_path)
            parse_results.append(result)
            status = "✅" if result["success"] else "❌"
            print(f"   {status} {file_type:10s} - 大小: {result['file_size']:6d} bytes")
        print()

        # 测试内容准确性
        print("3. 测试内容提取准确性...")
        accuracy_results = []
        for file_type, file_path in test_files.items():
            if file_type not in ["large", "empty"]:  # 跳过大文件和空文件
                result = await self.test_content_accuracy(file_type, file_path)
                accuracy_results.append(result)
                status = "✅" if result["is_complete"] else "⚠️"
                print(f"   {status} {file_type:10s} - 匹配率: {result['match_ratio']:.2%}")
        print()

        # 测试错误处理
        print("4. 测试错误处理...")
        error_results = await self.test_error_handling()
        for error_test in error_results:
            status = "✅" if error_test["actual_error"] == error_test["expected_error"] else "❌"
            print(f"   {status} {error_test['test']:20s} - 预期错误: {error_test['expected_error']}, 实际: {error_test['actual_error']}")
        print()

        # 测试大文件处理
        print("5. 测试大文件处理...")
        large_result = await self.test_large_file_handling()
        print(f"   原始大小: {large_result['original_size']} bytes")
        print(f"   提取长度: {large_result['extracted_length']} chars")
        print(f"   已截断: {'是' if large_result['is_truncated'] else '否'}")
        print(f"   截断比例: {large_result['truncated_ratio']:.2%}")
        print()

        # 汇总结果
        print("="*60)
        print("测试结果汇总")
        print("="*60 + "\n")

        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(parse_results),
            "successful_parses": sum(1 for r in parse_results if r["success"]),
            "failed_parses": sum(1 for r in parse_results if not r["success"]),
            "accuracy_tests": len(accuracy_results),
            "complete_extractions": sum(1 for r in accuracy_results if r["is_complete"]),
            "error_tests": len(error_results),
            "error_handling_ok": sum(1 for e in error_results if e["actual_error"] == e["expected_error"]),
            "large_file_truncated": large_result["is_truncated"],
            "supported_formats": [r["type"] for r in parse_results if r["success"],
            "parse_results": parse_results,
            "accuracy_results": accuracy_results,
            "error_results": error_results,
            "large_file_result": large_result
        }

        print(f"总测试数: {summary['total_tests']}")
        print(f"成功解析: {summary['successful_parses']} ✅")
        print(f"解析失败: {summary['failed_parses']} ❌")
        print(f"准确率测试: {summary['accuracy_tests']}")
        print(f"完整提取: {summary['complete_extractions']} ✅")
        print(f"错误处理: {summary['error_handling_ok']}/{summary['error_tests']} ✅")
        print(f"大文件截断: {'正常' if summary['large_file_truncated'] else '异常'}")
        print()

        print("支持的文件格式:")
        for fmt in summary["supported_formats"]:
            print(f"  - {fmt}")
        print()

        return summary

    def cleanup(self):
        """清理测试文件"""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
            print(f"已清理测试目录: {self.temp_dir}")
        except Exception as e:
            print(f"清理失败: {e}")


async def main():
    """主函数"""
    verifier = DocumentParserVerifier()

    try:
        summary = await verifier.run_all_tests()

        # 保存结果
        report_path = Path("/Users/xujian/Athena工作平台/docs/reports/DOCUMENT_PARSER_VERIFICATION_RESULT.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"✅ 验证结果已保存到: {report_path}")

    finally:
        verifier.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
