#!/usr/bin/env python3
"""
法律世界模型测试脚本 - 使用正确的环境变量
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# 加载环境变量
load_dotenv(Path(__file__).parent.parent / ".env")

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.legal_world_model.db_manager import LegalWorldDBManager
from core.legal_world_model.scenario_identifier import ScenarioIdentifier


async def test_legal_world_model():
    """测试法律世界模型"""

    # 从环境变量读取配置
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

    print("📝 Neo4j 配置:")
    print(f"   URI: {neo4j_uri}")
    print(f"   Username: {neo4j_username}")
    print(f"   Password: {'*' * len(neo4j_password)}")
    print()

    # 1. 测试场景识别器（不需要数据库）
    print("=" * 60)
    print("测试1: 场景识别器")
    print("=" * 60)

    identifier = ScenarioIdentifier()

    test_cases = [
        "请帮我答复审查意见，审查员认为权利要求1不具备创造性",
        "这件专利的新颖性分析",
        "请撰写一份关于相变材料的专利申请书",
        "针对专利CN12345678提出无效宣告请求",
    ]

    for case in test_cases:
        print(f"\n输入: {case}")
        result = identifier.identify_scenario(case)
        print("识别结果:")
        print(f"  - 领域: {result.domain.value}")
        print(f"  - 任务类型: {result.task_type.value}")
        print(f"  - 阶段: {result.phase.value}")
        print(f"  - 置信度: {result.confidence:.2f}")

    # 2. 测试数据库连接和规则检索
    print()
    print("=" * 60)
    print("测试2: 数据库连接和规则检索")
    print("=" * 60)

    db_manager = LegalWorldDBManager(
        uri=neo4j_uri,
        username=neo4j_username,
        password=neo4j_password,
        database="neo4j",  # 使用默认数据库
    )

    success = await db_manager.initialize()

    if success:
        print("✅ 数据库连接成功")

        # 测试检索（使用 db_manager 的异步方法）
        print("\n检索规则: patent/creativity_analysis/examination")

        # 使用 db_manager 的异步方法
        rules = await db_manager.get_scenario_rules(
            domain="patent",
            task_type="creativity_analysis",
            phase="examination",
        )

        if rules:
            print(f"✅ 找到 {len(rules)} 条规则")
            for rule in rules[:3]:
                sr = rule.get("sr", {})
                print(f"   - 规则ID: {sr.get('rule_id', 'N/A')}")
                print(f"     法律依据: {sr.get('legal_basis', 'N/A')[:100]}...")
        else:
            print("⚠️ 未找到规则（可能数据库为空）")

        await db_manager.close()
    else:
        print("❌ 数据库连接失败")
        print("   请检查 Neo4j 是否运行，以及密码是否正确")


if __name__ == "__main__":
    asyncio.run(test_legal_world_model())
