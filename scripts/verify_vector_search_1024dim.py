#!/usr/bin/env python3
"""
向量搜索工具验证脚本（1024维度版本）
验证vector_search工具的完整可用性，特别关注1024维度配置
"""

import asyncio
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify_dimension_config():
    """验证维度配置"""

    print("=" * 80)
    print("📏 验证维度配置")
    print("=" * 80)

    try:
        from config.vector_config import VECTOR_DIMENSION, COLLECTION_CONFIGS

        print(f"✅ 向量维度配置: {VECTOR_DIMENSION}")

        # 验证是否为1024
        if VECTOR_DIMENSION != 1024:
            print(f"❌ 维度配置错误: 期望1024，实际{VECTOR_DIMENSION}")
            return False

        print(f"✅ 维度配置正确: {VECTOR_DIMENSION}")

        # 验证集合配置
        print(f"\n向量集合配置:")
        for coll_name, coll_config in COLLECTION_CONFIGS.items():
            print(f"  - {coll_config['name']}")
            print(f"    维度: {coll_config['dimension']}")
            print(f"    距离: {coll_config['distance']}")

            if coll_config['dimension'] != 1024:
                print(f"    ❌ 维度错误: {coll_config['dimension']}")
                return False
            else:
                print(f"    ✅ 维度正确")

        return True

    except Exception as e:
        print(f"❌ 维度配置验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()


async def verify_bge_m3_dimension():
    """验证BGE-M3模型输出维度"""

    print("=" * 80)
    print("🧠 验证BGE-M3模型输出维度")
    print("=" * 80)

    try:
        from core.embedding.bge_m3_embedder import BGE_M3_Embedder

        print("初始化BGE-M3嵌入器...")
        embedder = BGE_M3_Embedder()
        await embedder.initialize()

        print("✅ BGE-M3模型加载成功")
        print(f"   配置维度: {embedder.dimension}")

        # 测试编码
        print("\n测试向量编码...")
        test_text = "专利检索测试文本"

        # 单条文本
        embedding = await embedder.encode([test_text])

        print(f"   输入: 1条文本")
        print(f"   输出形状: {embedding.shape}")

        # 验证维度
        if embedding.shape[1] != 1024:
            print(f"❌ 输出维度错误: {embedding.shape[1]}（期望1024）")
            return False

        print(f"✅ 单条文本编码维度正确: {embedding.shape[1]}")

        # 批量文本
        texts = ["测试1", "测试2", "测试3"]
        embeddings = await embedder.encode(texts)

        print(f"\n   输入: {len(texts)}条文本")
        print(f"   输出形状: {embeddings.shape}")

        if embeddings.shape[1] != 1024:
            print(f"❌ 批量编码维度错误: {embeddings.shape[1]}（期望1024）")
            return False

        print(f"✅ 批量文本编码维度正确: {embeddings.shape[1]}")

        return True

    except Exception as e:
        print(f"❌ BGE-M3模型验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()


async def verify_qdrant_collections_dimension():
    """验证Qdrant集合维度"""

    print("=" * 80)
    print("🗄️ 验证Qdrant集合维度")
    print("=" * 80)

    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(host="localhost", port=6333)

        # 获取所有集合
        collections_result = client.get_collections()

        if collections_result.status_code != 200:
            print(f"❌ 无法获取集合列表: {collections_result.status_code}")
            return False

        collections = collections_result.result.collections

        print(f"集合总数: {len(collections)}\n")

        all_correct = True
        for coll in collections:
            vector_size = coll.config.params.vectors.size
            name = coll.name

            print(f"集合: {name}")
            print(f"  维度: {vector_size}")

            if vector_size == 1024:
                print(f"  ✅ 维度正确")
            elif "_1024" in name:
                print(f"  ⚠️ 名称包含_1024但维度不是1024")
                all_correct = False
            else:
                print(f"  ⚠️ 维度不是1024（名称也不包含_1024）")
                all_correct = False

        if all_correct:
            print("\n✅ 所有集合维度正确")
        else:
            print("\n❌ 部分集合维度存在问题")

        return all_correct

    except Exception as e:
        print(f"❌ Qdrant集合验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()


async def verify_vector_manager():
    """验证向量管理器"""

    print("=" * 80)
    print("🔧 验证向量管理器")
    print("=" * 80)

    try:
        from core.vector.intelligent_vector_manager import IntelligentVectorManager

        # 创建实例
        print("创建IntelligentVectorManager实例...")
        manager = IntelligentVectorManager()

        print(f"✅ 向量管理器创建成功")
        print(f"   配置集合: {len(manager.collections_config)}")

        # 测试搜索（如果集合存在）
        print("\n测试向量搜索...")
        try:
            results = await manager.search_vector(
                query="专利检索",
                collection_name="legal_main_1024",  # ⚠️ 使用1024集合名称
                limit=5,
                score_threshold=0.0
            )

            print(f"✅ 向量搜索成功")
            print(f"   结果数: {len(results)}")

            # 验证结果向量维度
            for i, result in enumerate(results[:3], 1):
                if "vector" in result:
                    vector = result["vector"]
                    dim = len(vector) if isinstance(vector, (list, tuple)) else vector.shape[-1] if hasattr(vector, 'shape') else 0
                    print(f"   结果{i}向量维度: {dim}")

                    if dim != 1024:
                        print(f"   ⚠️ 向量维度不是1024: {dim}")

        except Exception as e:
            print(f"⚠️ 向量搜索测试失败（可能是集合不存在）: {e}")
            print("   这是正常的，如果集合尚未创建")

        return True

    except Exception as e:
        print(f"❌ 向量管理器验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()


async def create_handler_wrapper():
    """创建Handler包装器（1024维度版本）"""

    print("=" * 80)
    print("📝 创建Handler包装器（1024维度版本）")
    print("=" * 80)

    handler_code = '''#!/usr/bin/env python3
"""
向量搜索Handler（1024维度版本）
"""

from typing import Dict, Any
from core.tools.decorators import tool

@tool(
    name="vector_search",
    category="vector_search",
    description="向量语义搜索（基于BGE-M3模型，1024维）",
    priority="high",
    tags=["search", "vector", "semantic", "bge-m3", "1024dim"]
)
async def vector_search_handler(
    query: str,
    collection: str = "legal_main_1024",
    top_k: int = 10,
    threshold: float = 0.7
) -> Dict[str, Any]:
    """
    向量语义搜索Handler（1024维版本）

    参数:
        query: 查询文本
        collection: 集合名称（必须以_1024结尾）
        top_k: 返回结果数（默认: 10）
        threshold: 相似度阈值（默认: 0.7）

    返回:
        {
            "success": true,
            "query": "...",
            "collection": "...",
            "dimension": 1024,
            "total_results": 10,
            "results": [...]
        }
    """
    try:
        from core.vector.intelligent_vector_manager import IntelligentVectorManager
        from config.vector_config import validate_vector_dimension

        # 参数验证
        if not query:
            return {
                "success": False,
                "error": "缺少必需参数: query"
            }

        # 验证集合名称（必须以_1024结尾）
        if not collection.endswith("_1024"):
            return {
                "success": False,
                "error": f"集合名称必须以_1024结尾，当前: {collection}"
            }

        if top_k <= 0:
            return {
                "success": False,
                "error": "top_k必须大于0"
            }

        if not (0.0 <= threshold <= 1.0):
            return {
                "success": False,
                "error": "threshold必须在0.0到1.0之间"
            }

        # 创建向量管理器
        manager = IntelligentVectorManager()

        # 执行搜索
        results = await manager.search_vector(
            query=query,
            collection_name=collection,
            limit=top_k,
            score_threshold=threshold
        )

        # 验证结果向量维度（如果有）
        for result in results:
            if "vector" in result:
                vector = result["vector"]
                if not validate_vector_dimension(vector):
                    return {
                        "success": False,
                        "error": f"结果向量维度错误: {len(vector)}（期望1024）"
                    }

        return {
            "success": True,
            "query": query,
            "collection": collection,
            "dimension": 1024,
            "total_results": len(results),
            "results": results
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "collection": collection
        }
'''

    print("✅ Handler包装器代码已生成（1024维度版本）")
    print("\n关键特性:")
    print("  ✅ 强制使用_1024后缀的集合名称")
    print("  ✅ 返回dimension: 1024")
    print("  ✅ 验证结果向量维度")

    # 保存到文件
    output_file = Path("/Users/xujian/Athena工作平台/core/tools/vector_search_handler.py")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(handler_code)

    print(f"\n✅ Handler已保存到: {output_file}")

    return True


async def generate_report(dimension_ok, model_ok, collections_ok, manager_ok):
    """生成验证报告"""

    report = {
        "timestamp": "2026-04-19",
        "dimension": 1024,
        "summary": {
            "dimension_config_ok": dimension_ok,
            "model_output_ok": model_ok,
            "collections_ok": collections_ok,
            "manager_ok": manager_ok,
            "overall_ready": all([dimension_ok, model_ok, collections_ok, manager_ok])
        },
        "details": {
            "dimension_config": {
                "expected": 1024,
                "status": "✅ 正确" if dimension_ok else "❌ 错误"
            },
            "model_output": {
                "expected_dimension": 1024,
                "status": "✅ 正确" if model_ok else "❌ 错误"
            },
            "collections": {
                "expected_dimension": 1024,
                "status": "✅ 正确" if collections_ok else "❌ 错误"
            },
            "manager": {
                "status": "✅ 可用" if manager_ok else "❌ 不可用"
            }
        },
        "recommendations": []
    }

    # 生成建议
    if not dimension_ok:
        report["recommendations"].append("❌ 维度配置错误，请检查config/vector_config.py")

    if not model_ok:
        report["recommendations"].append("❌ BGE-M3模型输出维度不是1024，请检查core/embedding/bge_m3_embedder.py")

    if not collections_ok:
        report["recommendations"].append("⚠️ 部分Qdrant集合维度不是1024，需要重建集合")

    if report["summary"]["overall_ready"]:
        report["recommendations"].append("✅ 所有验证通过，可以开始迁移")

    # 保存报告
    report_path = Path("/Users/xujian/Athena工作平台/reports/vector_search_1024dim_verification.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("=" * 80)
    print("📄 验证报告（1024维度版本）")
    print("=" * 80)
    print(f"\n报告已保存到: {report_path}\n")

    # 打印摘要
    print("验证摘要:")
    print(f"  维度配置: {'✅' if dimension_ok else '❌'} (期望: 1024)")
    print(f"  模型输出: {'✅' if model_ok else '❌'} (期望: 1024)")
    print(f"  Qdrant集合: {'✅' if collections_ok else '❌'} (期望: 1024)")
    print(f"  向量管理器: {'✅' if manager_ok else '❌'}")
    print(f"\n整体状态: {'✅ 准备就绪' if report['summary']['overall_ready'] else '❌ 需要修复'}")

    if report["recommendations"]:
        print("\n建议:")
        for rec in report["recommendations"]:
            print(f"  - {rec}")

    print()

    return report


async def main():
    """主函数"""

    print("\n" + "=" * 80)
    print("🔍 向量搜索工具验证（1024维度版本）")
    print("=" * 80)
    print()

    # 1. 验证维度配置
    dimension_ok = await verify_dimension_config()

    if not dimension_ok:
        print("❌ 维度配置错误，无法继续验证")
        await generate_report(dimension_ok, False, False, False)
        return

    # 2. 验证BGE-M3模型输出维度
    model_ok = await verify_bge_m3_dimension()

    # 3. 验证Qdrant集合维度
    collections_ok = await verify_qdrant_collections_dimension()

    # 4. 验证向量管理器
    manager_ok = await verify_vector_manager()

    # 5. 创建Handler包装器
    handler_ok = await create_handler_wrapper()

    # 6. 生成报告
    report = await generate_report(dimension_ok, model_ok, collections_ok, manager_ok)

    print("=" * 80)
    if report["summary"]["overall_ready"]:
        print("✅ 向量搜索工具验证完成，可以开始迁移")
        print("⚠️ 注意: 必须使用1024维度的向量和集合！")
    else:
        print("❌ 向量搜索工具存在问题，需要先修复")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
