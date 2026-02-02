#!/usr/bin/env python3
"""
Athena工作平台 - 向量库完整验证器
验证所有向量库是否已正确构建和集成
"""

# Numpy兼容性导入
import logging
import os
import sys
from datetime import datetime
from typing import Any


from config.numpy_compatibility import random
from core.logging_config import setup_logging

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from core.vector_db.unified_search_interface import MemoryService, MemoryType
from core.vector_db.vector_db_manager import VectorDBManager, VectorQuery

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class VectorDBValidator:
    """向量库验证器"""

    def __init__(self):
        self.vector_db_manager = VectorDBManager()
        self.memory_service = MemoryService()

    def validate_all_collections(self) -> dict[str, Any]:
        """验证所有集合"""
        logger.info("🔍 开始验证所有向量库集合...")

        validation_results = {
            "total_collections": len(self.vector_db_manager.existing_collections),
            "validated_collections": {},
            "overall_success": True,
        }

        expected_collections = [
            ("general_memory_db", "共用向量库", MemoryType.GENERAL),
            ("patent_rules_unified_1024", "专利规则库", MemoryType.PATENT_KNOWLEDGE),
            ("legal_vector_db", "法律向量库", MemoryType.LEGAL_KNOWLEDGE),
            ("ai_technical_terms_vector_db", "技术术语库", MemoryType.TECHNICAL_KNOWLEDGE),
            ("patent_invalid_db", "专利无效库", MemoryType.PATENT_KNOWLEDGE),
            ("patent_review_db", "专利复审库", MemoryType.PATENT_KNOWLEDGE),
            ("patent_judgment_db", "专利判决库", MemoryType.PATENT_KNOWLEDGE),
        ]

        logger.info(str("=" * 80))
        logger.info("📋 向量库验证报告")
        logger.info(str("=" * 80))
        logger.info(f"📍 Qdrant服务: {self.vector_db_manager.qdrant_url}")
        logger.info(f"📊 已连接向量库数量: {len(self.vector_db_manager.existing_collections)}")
        logger.info(f"🎯 预期向量库数量: {len(expected_collections)}")
        logger.info(str("=" * 80))

        for collection_name, description, _memory_type in expected_collections:
            logger.info(f"\n🔍 验证: {description} ({collection_name})")
            logger.info(str("-" * 60))

            if collection_name in self.vector_db_manager.existing_collections:
                # 获取集合信息
                info = self.vector_db_manager.get_collection_info(collection_name)
                if info:
                    points_count = info.get("points_count", 0)
                    status = info.get("status", "unknown")
                    dimension = (
                        info.get("config", {})
                        .get("params", {})
                        .get("vectors", {})
                        .get("size", "unknown")
                    )

                    logger.info(f"   ✅ 状态: {status}")
                    logger.info(f"   📊 点数量: {points_count}")
                    logger.info(f"   📐 维度: {dimension}")

                    # 测试搜索功能
                    if dimension == 384:
                        test_vector = random(384).tolist()
                    else:  # 默认使用1024维
                        test_vector = random(1024).tolist()

                    query = VectorQuery(vector=test_vector, limit=1)
                    results = self.vector_db_manager.search_in_collection(collection_name, query)

                    logger.info(f"   🔍 搜索测试: 找到 {len(results)} 个结果")

                    validation_results["validated_collections"][collection_name] = {
                        "status": "success",
                        "points_count": points_count,
                        "dimension": dimension,
                        "search_results": len(results),
                    }
                else:
                    logger.info("   ❌ 无法获取集合信息")
                    validation_results["validated_collections"][collection_name] = {
                        "status": "error"
                    }
                    validation_results["overall_success"] = False
            else:
                logger.info("   ❌ 集合不存在")
                validation_results["validated_collections"][collection_name] = {"status": "missing"}
                validation_results["overall_success"] = False

        logger.info(str("\n" + "=" * 80))
        if validation_results["overall_success"]:
            logger.info("🎉 所有向量库验证通过!")
        else:
            logger.info("⚠️  部分向量库验证失败")
        logger.info(str("=" * 80))

        return validation_results

    def validate_unified_interface(self) -> bool:
        """验证统一接口功能"""
        logger.info("🔍 验证统一检索接口...")

        logger.info("\n🤖 验证统一检索接口")
        logger.info(str("-" * 60))

        test_cases = [
            ("通用知识", "人工智能定义", MemoryType.GENERAL),
            ("专利知识", "专利权利要求", MemoryType.PATENT_KNOWLEDGE),
            ("法律知识", "合同法", MemoryType.LEGAL_KNOWLEDGE),
            ("技术术语", "神经网络", MemoryType.TECHNICAL_KNOWLEDGE),
        ]

        all_success = True

        for case_name, query_text, memory_type in test_cases:
            logger.info(f"\n📝 测试 {case_name} 检索: '{query_text}'")
            try:
                results = self.memory_service.query_memory(
                    query_text=query_text, memory_type=memory_type, limit=2
                )

                total_results = results["total_results"]
                logger.info(f"   ✅ 找到 {total_results} 个结果")
                logger.info(f"   📁 搜索集合: {', '.join(results['collections_searched'])}")

                if total_results == 0:
                    logger.info("   ⚠️  未找到结果,但这可能是正常的(取决于数据内容)")

            except Exception as e:
                logger.info(f"   ❌ 测试失败: {e}")
                all_success = False

        # 测试智能搜索
        logger.info("\n🧠 测试智能搜索功能")
        try:
            results = self.memory_service.query_memory(query_text="专利侵权判定方法", limit=2)

            total_results = results["total_results"]
            logger.info(f"   ✅ 智能搜索找到 {total_results} 个结果")
            logger.info(f"   🎯 自动选择集合: {', '.join(results['collections_searched'])}")

        except Exception as e:
            logger.info(f"   ❌ 智能搜索失败: {e}")
            all_success = False

        return all_success

    def validate_athena_integration(self) -> bool:
        """验证Athena和小诺集成"""
        logger.info("🔍 验证Athena和小诺集成...")

        logger.info("\n🏠 验证Athena和小诺集成")
        logger.info(str("-" * 60))

        try:
            # 测试Athena上下文
            logger.info("📋 测试Athena用户上下文")
            athena_results = self.memory_service.query_memory(
                query_text="专利分析方法", user_context="athena", limit=1
            )
            logger.info(f"   ✅ Athena找到 {athena_results['total_results']} 个结果")

            # 测试小诺上下文
            logger.info("💖 测试小诺用户上下文")
            xiaonuo_results = self.memory_service.query_memory(
                query_text="对话历史", user_context="xiaonuo", limit=1
            )
            logger.info(f"   ✅ 小诺找到 {xiaonuo_results['total_results']} 个结果")

            logger.info("   ✅ 用户上下文功能正常")
            return True

        except Exception as e:
            logger.info(f"   ❌ 集成测试失败: {e}")
            return False


def main() -> None:
    """主函数 - 执行完整验证"""
    logger.info("🏗️  开始执行Athena向量库完整验证...")

    validator = VectorDBValidator()

    logger.info(str("=" * 90))
    logger.info("🏗️  Athena工作平台向量库完整验证器")
    logger.info(str("=" * 90))
    logger.info(f"⏰ 验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("🎯 验证目标: 完整向量库系统")
    logger.info(str("=" * 90))

    # 验证所有集合
    validation_results = validator.validate_all_collections()

    # 验证统一接口
    unified_success = validator.validate_unified_interface()

    # 验证Athena集成
    integration_success = validator.validate_athena_integration()

    # 生成最终报告
    logger.info(f"\n{'='*90}")
    logger.info("📊 最终验证报告")
    logger.info(str("=" * 90))

    logger.info(f"📚 总计向量库: {validation_results['total_collections']}")
    logger.info(f"🔍 集合验证: {'✅ 通过' if validation_results['overall_success'] else '❌ 失败'}")
    logger.info(f"🔗 统一接口: {'✅ 通过' if unified_success else '❌ 失败'}")
    logger.info(f"🏠 系统集成: {'✅ 通过' if integration_success else '❌ 失败'}")

    overall_success = (
        validation_results["overall_success"] and unified_success and integration_success
    )

    print()
    if overall_success:
        logger.info("🎉 所有验证均已通过!")
        logger.info("✅ Athena工作平台向量库系统已完全构建并验证")
        logger.info("✅ 共用向量库和专业向量库均已正常运行")
        logger.info("✅ 统一检索接口已集成到Athena和小诺记忆系统")
        logger.info("🎯 系统已准备就绪,可以开始提供服务")
    else:
        logger.info("❌ 部分验证失败,请检查系统状态")

    logger.info(str("=" * 90))

    return overall_success


if __name__ == "__main__":
    success = main()
    if success:
        logger.info("\n✅ 验证完成 - Athena向量库系统正常运行")
        exit(0)
    else:
        logger.info("\n❌ 验证失败 - 请检查系统配置")
        exit(1)
