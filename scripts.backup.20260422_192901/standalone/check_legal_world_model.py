#!/usr/bin/env python3
"""检查法律世界模型是否正常运行"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.legal_world_model import (
    CONSTITUTION_RATIFICATION_DATE,
    CONSTITUTION_VERSION,
    create_db_manager,
)


async def check_legal_world_model():
    """检查法律世界模型"""
    print("🌟 检查法律世界模型...")

    try:
        # 检查版本信息
        print(f"📚 版本: {CONSTITUTION_VERSION}")
        print(f"📅 生效日期: {CONSTITUTION_RATIFICATION_DATE}")

        # 检查数据库管理器
        print("\n💾 检查数据库管理器...")
        # 使用正确的Neo4j密码（从Docker Compose中获取）
        db_manager = await create_db_manager(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="athena_neo4j_2024",
            database="neo4j"
        )
        print("✅ 数据库管理器已创建")

        # 检查基本操作
        print("\n🔍 检查基本操作...")

        # 尝试获取场景规则
        scenario_rules = await db_manager.get_scenario_rules()
        print(f"📊 场景规则数量: {len(scenario_rules)}")

        # 尝试获取法律文档
        legal_docs = await db_manager.get_legal_documents()
        print(f"📄 法律文档数量: {len(legal_docs)}")

        # 尝试获取参考案例
        reference_cases = await db_manager.get_reference_cases()
        print(f"🏛️ 参考案例数量: {len(reference_cases)}")

        print("\n🎉 法律世界模型运行正常！")
        return True

    except Exception as e:
        print(f"❌ 法律世界模型检查失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False


async def main():
    """主函数"""
    success = await check_legal_world_model()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
