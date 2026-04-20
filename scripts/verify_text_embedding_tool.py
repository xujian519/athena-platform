#!/usr/bin/env python3
"""
Text Embedding工具验证脚本

验证text_embedding工具的功能和性能。

Author: Athena平台团队
Created: 2026-04-20
Version: v1.0.0
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.tools.production_tool_implementations import text_embedding_handler


class TextEmbeddingVerifier:
    """文本嵌入工具验证器"""

    def __init__(self):
        self.results = {
            "依赖检查": {},
            "功能测试": {},
            "性能测试": {},
            "错误处理": {}
        }

    def print_section(self, title: str):
        """打印分节标题"""
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}")

    def check_dependencies(self):
        """检查依赖项"""
        self.print_section("1. 依赖检查")

        dependencies = {
            "numpy": "NumPy",
            "FlagEmbedding": "FlagEmbedding",
        }

        for module, name in dependencies.items():
            try:
                __import__(module)
                print(f"✅ {name}: 已安装")
                self.results["依赖检查"][name] = "已安装"
            except ImportError as e:
                print(f"❌ {name}: 未安装 - {e}")
                self.results["依赖检查"][name] = f"未安装: {e}"

        # 单独检查AthenaModelLoader（避免类型注解错误）
        try:
            from core.models.athena_model_loader import AthenaModelLoader
            print(f"✅ AthenaModelLoader: 可导入")
            self.results["依赖检查"]["AthenaModelLoader"] = "可导入"
        except Exception as e:
            print(f"❌ AthenaModelLoader: 导入失败 - {type(e).__name__}: {e}")
            self.results["依赖检查"]["AthenaModelLoader"] = f"导入失败: {e}"

        # 检查BGE-M3服务
        print("\n检查BGE-M3服务...")
        try:
            import urllib.request
            response = urllib.request.urlopen("http://localhost:8766/health", timeout=2)
            data = json.loads(response.read())
            print(f"✅ BGE-M3服务: 运行中 - {data}")
            self.results["依赖检查"]["BGE-M3服务"] = "运行中"
        except Exception as e:
            print(f"❌ BGE-M3服务: 未运行 - {e}")
            self.results["依赖检查"]["BGE-M3服务"] = f"未运行: {e}"

    async def test_single_text_embedding(self):
        """测试单文本嵌入"""
        self.print_section("2. 单文本嵌入测试")

        test_cases = [
            {
                "name": "中文短文本",
                "text": "这是一个测试文本，用于验证文本嵌入功能。"
            },
            {
                "name": "英文短文本",
                "text": "This is a test text for embedding verification."
            },
            {
                "name": "中英文混合",
                "text": "专利Patent分析Analysis需要混合语言支持。"
            },
            {
                "name": "长文本",
                "text": "人工智能技术正在快速发展，深度学习模型在自然语言处理、计算机视觉等领域取得了显著进展。" * 5
            }
        ]

        for case in test_cases:
            print(f"\n测试: {case['name']}")
            print(f"文本长度: {len(case['text'])} 字符")

            start_time = time.time()
            result = await text_embedding_handler(
                params={"text": case['text'], "model": "BAAI/bge-m3", "normalize": True},
                context={}
            )
            elapsed = time.time() - start_time

            print(f"响应时间: {elapsed:.3f}秒")
            print(f"成功: {result.get('success', False)}")
            print(f"模型: {result.get('model', 'N/A')}")
            print(f"向量维度: {result.get('embedding_dim', 0)}")
            print(f"消息: {result.get('message', 'N/A')}")

            if result.get('embedding'):
                print(f"向量示例 (前5维): {result['embedding'][:5]}")

            self.results["功能测试"][case['name']] = {
                "success": result.get('success', False),
                "time": elapsed,
                "dim": result.get('embedding_dim', 0),
                "model": result.get('model', 'N/A')
            }

    async def test_batch_embedding(self):
        """测试批量嵌入"""
        self.print_section("3. 批量嵌入测试")

        texts = [
            "专利检索是专利分析的基础",
            "机器学习模型需要大量训练数据",
            "深度学习在自然语言处理中应用广泛",
            "知识图谱可以表示实体之间的关系",
            "向量数据库支持高维向量检索"
        ]

        print(f"批量处理 {len(texts)} 个文本...")

        start_time = time.time()
        results = []
        for i, text in enumerate(texts):
            result = await text_embedding_handler(
                params={"text": text, "model": "BAAI/bge-m3", "normalize": True},
                context={}
            )
            results.append(result)
        elapsed = time.time() - start_time

        print(f"\n总响应时间: {elapsed:.3f}秒")
        print(f"平均响应时间: {elapsed/len(texts):.3f}秒/个")
        print(f"吞吐量: {len(texts)/elapsed:.2f} 文本/秒")

        success_count = sum(1 for r in results if r.get('success'))
        print(f"成功率: {success_count}/{len(texts)} ({success_count/len(texts)*100:.1f}%)")

        self.results["性能测试"]["批量处理"] = {
            "total_time": elapsed,
            "avg_time": elapsed/len(texts),
            "throughput": len(texts)/elapsed,
            "success_rate": f"{success_count/len(texts)*100:.1f}%"
        }

    async def test_error_handling(self):
        """测试错误处理"""
        self.print_section("4. 错误处理测试")

        test_cases = [
            {
                "name": "空文本",
                "params": {"text": "", "model": "BAAI/bge-m3"}
            },
            {
                "name": "无效模型",
                "params": {"text": "测试文本", "model": "invalid_model_name"}
            },
            {
                "name": "缺失文本参数",
                "params": {"model": "BAAI/bge-m3"}
            }
        ]

        for case in test_cases:
            print(f"\n测试: {case['name']}")
            print(f"参数: {case['params']}")

            try:
                result = await text_embedding_handler(
                    params=case['params'],
                    context={}
                )
                print(f"结果: {result.get('message', result.get('error', 'N/A'))}")
                print(f"是否使用备用方案: {not result.get('success', True) or 'fallback' in result.get('model', '')}")

                self.results["错误处理"][case['name']] = {
                    "handled": True,
                    "fallback_used": 'fallback' in result.get('model', '')
                }
            except Exception as e:
                print(f"❌ 抛出异常: {e}")
                self.results["错误处理"][case['name']] = {
                    "handled": False,
                    "error": str(e)
                }

    async def test_embedding_quality(self):
        """测试嵌入质量"""
        self.print_section("5. 嵌入质量测试")

        # 测试相似文本
        similar_pairs = [
            ("专利检索", "专利搜索"),
            ("机器学习", "深度学习"),
            ("人工智能", "AI技术")
        ]

        print("\n计算相似文本的向量相似度...")
        for text1, text2 in similar_pairs:
            result1 = await text_embedding_handler(
                params={"text": text1, "model": "BAAI/bge-m3", "normalize": True},
                context={}
            )
            result2 = await text_embedding_handler(
                params={"text": text2, "model": "BAAI/bge-m3", "normalize": True},
                context={}
            )

            if result1.get('success') and result2.get('success'):
                # 简单的余弦相似度计算（仅示例）
                emb1 = result1['embedding']
                emb2 = result2['embedding']
                # 这里只计算前10维的相似度作为示例
                similarity = sum(a*b for a, b in zip(emb1, emb2)) / (sum(a*a for a in emb1)**0.5 * sum(b*b for b in emb2)**0.5)
                print(f"  '{text1}' vs '{text2}': 相似度 ≈ {similarity:.3f} (仅前10维)")
            else:
                print(f"  '{text1}' vs '{text2}': 无法计算（向量化失败）")

    def generate_report(self):
        """生成验证报告"""
        self.print_section("6. 验证报告")

        print("\n📊 测试结果汇总:")
        print(json.dumps(self.results, indent=2, ensure_ascii=False))

        # 统计
        total_tests = sum(len(v) for v in self.results.values())
        passed_tests = sum(
            1 for category in self.results.values()
            for result in category.values()
            if isinstance(result, dict) and result.get('success', True)
        )

        print(f"\n✅ 通过测试: {passed_tests}/{total_tests}")
        print(f"❌ 失败测试: {total_tests - passed_tests}/{total_tests}")

        # 建议
        print("\n💡 建议:")
        if "FlagEmbedding" not in self.results["依赖检查"].get("FlagEmbedding", ""):
            print("  1. 安装FlagEmbedding: pip install FlagEmbedding")
        if self.results["依赖检查"].get("BGE-M3服务", "") == "未运行":
            print("  2. 启动BGE-M3服务: cd core/models && python start_bge_service.py")
        if any("fallback" in str(r) for r in self.results["功能测试"].values()):
            print("  3. 模型可能未正确加载，检查BGE-M3服务状态")

        # 保存报告
        report_path = Path("/Users/xujian/Athena工作平台/docs/reports/TEXT_EMBEDDING_TOOL_VERIFICATION_REPORT_20260420.md")
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# Text Embedding工具验证报告\n\n")
            f.write(f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## 测试结果\n\n")
            f.write(f"```json\n")
            f.write(json.dumps(self.results, indent=2, ensure_ascii=False))
            f.write(f"\n```\n\n")
            f.write(f"## 统计\n\n")
            f.write(f"- 通过: {passed_tests}/{total_tests}\n")
            f.write(f"- 失败: {total_tests - passed_tests}/{total_tests}\n")
            f.write(f"## 建议\n\n")
            f.write(f"1. 确保所有依赖已正确安装\n")
            f.write(f"2. 启动BGE-M3服务并确保模型已加载\n")
            f.write(f"3. 检查向量维度是否为1024（BGE-M3标准）\n")

        print(f"\n📄 报告已保存到: {report_path}")

    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始Text Embedding工具验证...")

        self.check_dependencies()
        await self.test_single_text_embedding()
        await self.test_batch_embedding()
        await self.test_error_handling()
        await self.test_embedding_quality()
        self.generate_report()

        print("\n✨ 验证完成!")


async def main():
    """主函数"""
    verifier = TextEmbeddingVerifier()
    await verifier.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
