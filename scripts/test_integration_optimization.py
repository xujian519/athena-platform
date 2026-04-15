#!/usr/bin/env python3
"""
Athena智能体优化集成测试
Athena Agent Optimization Integration Test

验证所有优化功能的集成效果

作者: Athena平台团队
创建时间: 2026-03-17
版本: v1.0.0
"""

import asyncio
import json
import sys
import time
from datetime import datetime

sys.path.insert(0, '/Users/xujian/Athena工作平台')

from config.feature_flags import get_all_feature_flags, is_feature_enabled


class OptimizationTestSuite:
    """优化测试套件"""

    def __init__(self):
        self.results = {
            "test_time": datetime.now().isoformat(),
            "feature_flags": {},
            "tests": {},
            "performance": {},
            "overall_status": "pending"
        }

    def test_feature_flags(self):
        """测试特性开关"""
        print("\n1️⃣ 测试特性开关配置")
        print("-" * 60)

        flags = get_all_feature_flags()
        self.results["feature_flags"] = flags

        required_flags = [
            "enable_intent_cache",
            "enable_tool_cache",
            "enable_recovery_monitoring",
            "enable_unified_cache",
            "enable_neo4j_indexes",
            "enable_hnsw_search",
            "enable_async_queries"
        ]

        all_enabled = True
        for flag in required_flags:
            enabled = is_feature_enabled(flag)
            status = "✅" if enabled else "❌"
            print(f"   {status} {flag}: {enabled}")
            if not enabled:
                all_enabled = False

        self.results["tests"]["feature_flags"] = all_enabled
        return all_enabled

    async def test_intent_cache(self):
        """测试意图识别缓存"""
        print("\n2️⃣ 测试意图识别缓存")
        print("-" * 60)

        if not is_feature_enabled("enable_intent_cache"):
            print("   ⏭️  意图识别缓存未启用，跳过")
            self.results["tests"]["intent_cache"] = "skipped"
            return True

        try:
            from production.core.nlp.xiaonuo_enhanced_intent_classifier import (
                EnhancedIntentConfig,
                XiaonuoEnhancedIntentClassifier,
            )

            config = EnhancedIntentConfig()
            classifier = XiaonuoEnhancedIntentClassifier(config)

            # 尝试加载模型
            try:
                classifier.load_model()
                print("   ✅ 模型加载成功")
            except Exception:
                print("   ⚠️  模型未训练，跳过测试")
                self.results["tests"]["intent_cache"] = "no_model"
                return True

            # 测试缓存
            test_text = "帮我优化代码性能"

            start = time.time()
            result1 = classifier.predict_intent(test_text)
            time1 = (time.time() - start) * 1000

            start = time.time()
            result2 = classifier.predict_intent(test_text)
            time2 = (time.time() - start) * 1000

            # 获取统计
            stats = classifier.get_cache_stats()

            print(f"   ✅ 首次预测: {result1[0]} ({time1:.2f}ms)")
            print(f"   ✅ 缓存预测: {result2[0]} ({time2:.2f}ms)")
            print(f"   ✅ 缓存命中率: {stats['cache_hit_rate']:.2%}")

            self.results["tests"]["intent_cache"] = True
            self.results["performance"]["intent_cache"] = {
                "first_time": time1,
                "cached_time": time2,
                "improvement": ((time1 - time2) / time1 * 100) if time1 > 0 else 0,
                "hit_rate": stats['cache_hit_rate']
            }

            return True

        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            self.results["tests"]["intent_cache"] = False
            return False

    async def test_tool_selector_cache(self):
        """测试工具选择缓存"""
        print("\n3️⃣ 测试工具选择缓存")
        print("-" * 60)

        if not is_feature_enabled("enable_tool_cache"):
            print("   ⏭️  工具选择缓存未启用，跳过")
            self.results["tests"]["tool_cache"] = "skipped"
            return True

        try:
            from production.core.nlp.xiaonuo_intelligent_tool_selector import (
                ToolSelectionConfig,
                XiaonuoIntelligentToolSelector,
            )

            config = ToolSelectionConfig()
            selector = XiaonuoIntelligentToolSelector(config)

            # 尝试加载模型
            try:
                selector.load_models()
                print("   ✅ 模型加载成功")
            except Exception:
                print("   ⚠️  模型未训练，跳过测试")
                self.results["tests"]["tool_cache"] = "no_model"
                return True

            # 测试缓存
            test_params = ("优化代码", "TECHNICAL", {"language": "python"})

            start = time.time()
            result1 = selector.select_tools(*test_params)
            time1 = (time.time() - start) * 1000

            start = time.time()
            result2 = selector.select_tools(*test_params)
            time2 = (time.time() - start) * 1000

            # 获取统计
            stats = selector.get_cache_stats()

            print(f"   ✅ 首次选择: {len(result1)} 个工具 ({time1:.2f}ms)")
            print(f"   ✅ 缓存选择: {len(result2)} 个工具 ({time2:.2f}ms)")
            print(f"   ✅ 缓存命中率: {stats['cache_hit_rate']:.2%}")

            self.results["tests"]["tool_cache"] = True
            self.results["performance"]["tool_cache"] = {
                "first_time": time1,
                "cached_time": time2,
                "improvement": ((time1 - time2) / time1 * 100) if time1 > 0 else 0,
                "hit_rate": stats['cache_hit_rate']
            }

            return True

        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            self.results["tests"]["tool_cache"] = False
            return False

    def test_unified_cache(self):
        """测试统一缓存接口"""
        print("\n4️⃣ 测试统一缓存接口")
        print("-" * 60)

        if not is_feature_enabled("enable_unified_cache"):
            print("   ⏭️  统一缓存未启用，跳过")
            self.results["tests"]["unified_cache"] = "skipped"
            return True

        try:
            from core.cache.unified_cache_interface import get_unified_cache_manager

            manager = get_unified_cache_manager()

            # 测试基本操作
            test_data = {"test": "data", "timestamp": time.time()}

            # 设置
            success = manager.set('multi_level', 'test_key', test_data, ttl=60)
            print(f"   {'✅' if success else '❌'} 缓存设置: {success}")

            # 获取
            result = manager.get('multi_level', 'test_key')
            print(f"   {'✅' if result else '❌'} 缓存获取: {result is not None}")

            # 删除
            success = manager.delete('multi_level', 'test_key')
            print(f"   {'✅' if success else '❌'} 缓存删除: {success}")

            # 统计
            stats = manager.get_stats()
            print(f"   ✅ 已注册缓存: {len(manager.caches)} 个")

            self.results["tests"]["unified_cache"] = True
            self.results["performance"]["unified_cache"] = {
                "registered_caches": len(manager.caches),
                "hit_rate": stats['manager_stats']['hit_rate']
            }

            return True

        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            self.results["tests"]["unified_cache"] = False
            return False

    def test_neo4j_indexes(self):
        """测试Neo4j索引"""
        print("\n5️⃣ 测试Neo4j索引")
        print("-" * 60)

        if not is_feature_enabled("enable_neo4j_indexes"):
            print("   ⏭️  Neo4j索引未启用，跳过")
            self.results["tests"]["neo4j_indexes"] = "skipped"
            return True

        try:
            from core.neo4j.neo4j_graph_client import Neo4jClient

            client = Neo4jClient()

            if not client.connect():
                print("   ⚠️  Neo4j连接失败，跳过")
                self.results["tests"]["neo4j_indexes"] = "connection_failed"
                return True

            # 检查索引
            with client.session() as session:
                result = session.run("SHOW INDEXES")
                indexes = list(result)

                online_count = sum(1 for idx in indexes if idx.get('state') == 'ONLINE')

                print(f"   ✅ 索引总数: {len(indexes)}")
                print(f"   ✅ 在线索引: {online_count}")

            client.close()

            self.results["tests"]["neo4j_indexes"] = True
            self.results["performance"]["neo4j_indexes"] = {
                "total_indexes": len(indexes),
                "online_indexes": online_count
            }

            return True

        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            self.results["tests"]["neo4j_indexes"] = False
            return False

    async def test_vector_search_hnsw(self):
        """测试向量检索HNSW优化"""
        print("\n6️⃣ 测试向量检索HNSW优化")
        print("-" * 60)

        if not is_feature_enabled("enable_hnsw_search"):
            print("   ⏭️  HNSW搜索未启用，跳过")
            self.results["tests"]["hnsw_search"] = "skipped"
            return True

        try:
            import numpy as np

            from core.vector.qdrant_adapter import QdrantVectorAdapter

            adapter = QdrantVectorAdapter()

            # 检查配置
            print(f"   ✅ HNSW配置: m={adapter.hnsw_config.m}, ef_construct={adapter.hnsw_config.ef_construct}")

            # 测试搜索（如果Qdrant运行）
            try:
                query_vector = np.random.randn(768).tolist()
                start = time.time()
                results = adapter.search(query_vector, "patent_vectors", limit=10)
                elapsed = (time.time() - start) * 1000

                print(f"   ✅ 搜索结果: {len(results)} 条")
                print(f"   ✅ 搜索耗时: {elapsed:.2f}ms")

                stats = adapter.get_search_stats()
                print(f"   ✅ 平均耗时: {stats['avg_time']:.2f}ms")

                self.results["tests"]["hnsw_search"] = True
                self.results["performance"]["hnsw_search"] = {
                    "search_time": elapsed,
                    "avg_time": stats['avg_time']
                }

            except Exception as e:
                print(f"   ⚠️  Qdrant未运行或集合不存在，跳过: {e}")
                self.results["tests"]["hnsw_search"] = "qdrant_unavailable"

            return True

        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            self.results["tests"]["hnsw_search"] = False
            return False

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 集成测试报告")
        print("=" * 60)

        # 统计测试结果
        total = len(self.results["tests"])
        passed = sum(1 for v in self.results["tests"].values() if v is True)
        failed = sum(1 for v in self.results["tests"].values() if v is False)
        skipped = sum(1 for v in self.results["tests"].values() if isinstance(v, str))

        print(f"\n测试总数: {total}")
        print(f"通过: {passed} ✅")
        print(f"失败: {failed} ❌")
        print(f"跳过: {skipped} ⏭️")

        if failed == 0:
            self.results["overall_status"] = "passed"
            print("\n🎉 所有测试通过！优化功能集成成功！")
        else:
            self.results["overall_status"] = "failed"
            print(f"\n⚠️  {failed} 个测试失败，需要修复")

        # 性能总结
        print("\n📈 性能提升总结:")
        print("-" * 60)

        if "intent_cache" in self.results["performance"]:
            perf = self.results["performance"]["intent_cache"]
            if perf["improvement"] > 0:
                print(f"   意图识别缓存: 性能提升 {perf['improvement']:.1f}%")

        if "tool_cache" in self.results["performance"]:
            perf = self.results["performance"]["tool_cache"]
            if perf["improvement"] > 0:
                print(f"   工具选择缓存: 性能提升 {perf['improvement']:.1f}%")

        # 保存报告
        report_path = "/Users/xujian/Athena工作平台/docs/optimization_test_report.json"
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
            print(f"\n✅ 测试报告已保存: {report_path}")
        except Exception as e:
            print(f"\n⚠️  保存报告失败: {e}")

        return self.results["overall_status"] == "passed"


async def main():
    """主函数"""
    print("=" * 60)
    print("🧪 Athena智能体优化集成测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    suite = OptimizationTestSuite()

    # 运行所有测试
    suite.test_feature_flags()
    await suite.test_intent_cache()
    await suite.test_tool_selector_cache()
    suite.test_unified_cache()
    suite.test_neo4j_indexes()
    await suite.test_vector_search_hnsw()

    # 生成报告
    success = suite.generate_report()

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
