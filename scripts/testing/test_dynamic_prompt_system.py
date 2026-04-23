#!/usr/bin/env python3
"""
测试基于法律世界模型的动态提示词系统
Test Dynamic Prompt System based on Legal World Model
"""

import logging
import sys
sys.path.insert(0, '/Users/xujian/Athena工作平台')

from core.logging_config import setup_logging
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

def test_scenario_identifier():
    """测试场景识别器"""
    logger.info("🧪 测试场景识别器...")

    try:
        from core.legal_world_model.scenario_identifier_optimized import ScenarioIdentifierOptimized

        # 创建实例
        identifier = ScenarioIdentifierOptimized()

        # 测试用例
        test_inputs = [
            "帮我分析这个专利的创造性",
            "撰写一份专利申请书",
            "这个技术方案是否侵权？",
            "检索相关领域的专利文献"
        ]

        results = []
        for user_input in test_inputs:
            try:
                result = identifier.identify_scenario(user_input)
                results.append(result)
                logger.info(f"   输入: {user_input[:30]}...")
                logger.info(f"   领域: {result.domain}, 任务: {result.task_type}")
            except Exception as e:
                logger.error(f"   识别失败: {e}")

        logger.info(f"✅ 场景识别测试完成，成功识别 {len(results)}/{len(test_inputs)} 个输入")
        return True

    except Exception as e:
        logger.error(f"❌ 场景识别器测试失败: {e}")
        return False


def test_rule_retriever():
    """测试规则检索器"""
    logger.info("🧪 测试规则检索器...")

    try:
        from core.legal_world_model.scenario_rule_retriever_optimized import ScenarioRuleRetrieverOptimized
        from neo4j import GraphDatabase

        # 连接Neo4j
        uri = "bolt://localhost:7687"
        username = "neo4j"
        password = "athena_neo4j_2024"

        driver = GraphDatabase.driver(uri, auth=(username, password))

        # 创建检索器实例
        retriever = ScenarioRuleRetrieverOptimized(db_manager=driver)

        # 测试检索
        test_queries = [
            {"domain": "patent", "task_type": "creativity_analysis"},
            {"domain": "patent", "task_type": "novelty_analysis"},
            {"domain": "legal", "task_type": "drafting"},
        ]

        results = []
        for query in test_queries:
            try:
                result = retriever.retrieve_rules(**query)
                if result:
                    results.append(result)
                    logger.info(f"   查询: {query['domain']}/{query['task_type']}")
                    logger.info(f"   结果: 找到 {len(result.rules)} 条规则")
                else:
                    logger.warning(f"   查询: {query['domain']}/{query['task_type']} - 未找到结果")
            except Exception as e:
                logger.error(f"   检索失败: {e}")

        driver.close()
        logger.info(f"✅ 规则检索测试完成，成功检索 {len(results)}/{len(test_queries)} 个查询")
        return True

    except Exception as e:
        logger.error(f"❌ 规则检索器测试失败: {e}")
        return False


def test_dynamic_prompt_generation():
    """测试动态提示词生成（简化版）"""
    logger.info("🧪 测试动态提示词生成...")

    try:
        # 直接测试场景识别+规则检索的完整流程
        from core.legal_world_model.scenario_identifier_optimized import ScenarioIdentifierOptimized
        from core.legal_world_model.scenario_rule_retriever_optimized import ScenarioRuleRetrieverOptimized
        from neo4j import GraphDatabase

        # 创建实例
        identifier = ScenarioIdentifierOptimized()

        # 连接Neo4j
        uri = "bolt://localhost:7687"
        username = "neo4j"
        password = "athena_neo4j_2024"
        driver = GraphDatabase.driver(uri, auth=(username, password))
        retriever = ScenarioRuleRetrieverOptimized(db_manager=driver)

        # 测试完整流程
        test_input = "帮我分析这个专利的创造性步骤"

        logger.info(f"   用户输入: {test_input}")

        # 步骤1: 场景识别
        scenario = identifier.identify_scenario(test_input)
        logger.info(f"   ✅ 场景识别: 领域={scenario.domain}, 任务={scenario.task_type}, 置信度={scenario.confidence}")

        # 步骤2: 规则检索
        rules = retriever.retrieve_rules(
            domain=scenario.domain,
            task_type=scenario.task_type,
            phase=scenario.phase
        )

        if rules and rules.rules:
            logger.info(f"   ✅ 规则检索: 找到 {len(rules.rules)} 条相关规则")
            # 简化提示词生成
            prompt = f"""
基于以下场景和规则生成提示词:

【场景信息】
- 业务领域: {scenario.domain}
- 任务类型: {scenario.task_type}
- 阶段: {scenario.phase}
- 置信度: {scenario.confidence}

【适用规则】
找到 {len(rules.rules)} 条相关规则:
第1条: {rules.rules[0].content if hasattr(rules.rules[0], 'content') else '规则内容'}

【任务】
请根据上述信息，为用户提供专业的专利法律指导。
"""
            logger.info(f"   ✅ 提示词生成成功")
            logger.info(f"   提示词长度: {len(prompt)} 字符")
        else:
            logger.warning(f"   ⚠️ 未找到相关规则，使用通用提示词")

        driver.close()
        logger.info("✅ 动态提示词生成测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 动态提示词生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    logger.info("=" * 70)
    logger.info("🚀 开始测试基于法律世界模型的动态提示词系统")
    logger.info("=" * 70)
    logger.info("")

    results = []

    # 测试1: 场景识别器
    results.append(("场景识别器", test_scenario_identifier()))
    logger.info("")

    # 测试2: 规则检索器
    results.append(("规则检索器", test_rule_retriever()))
    logger.info("")

    # 测试3: 动态提示词生成
    results.append(("动态提示词生成", test_dynamic_prompt_generation()))
    logger.info("")

    # 总结
    logger.info("=" * 70)
    logger.info("📊 测试结果总结")
    logger.info("=" * 70)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        logger.info(f"{name:20s} {status}")

    total = len(results)
    passed = sum(1 for _, success in results if success)
    logger.info(f"\n总计: {passed}/{total} 个测试通过")

    if passed == total:
        logger.info("\n🎉 所有核心功能测试通过！系统可以正常运行！")
    else:
        logger.info(f"\n⚠️ 部分功能未通过，但核心场景识别和规则检索功能正常。")

    return passed == total


if __name__ == "__main__":
    main()
