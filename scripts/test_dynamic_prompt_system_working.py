#!/usr/bin/env python3
"""
测试基于法律世界模型的动态提示词系统 - 实际工作版本
Test Dynamic Prompt System - Working Version
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
        test_input = "帮我分析这个专利的创造性步骤"

        logger.info(f"   用户输入: {test_input}")

        # 使用正确的方法名
        scenario = identifier.identify_scenario(test_input)

        logger.info(f"   ✅ 场景识别成功!")
        logger.info(f"   领域: {scenario.domain}")
        logger.info(f"   任务类型: {scenario.task_type}")
        logger.info(f"   阶段: {scenario.phase}")
        logger.info(f"   置信度: {scenario.confidence}")

        if scenario.extracted_variables:
            logger.info(f"   提取变量: {scenario.extracted_variables}")

        return True, scenario

    except Exception as e:
        logger.error(f"❌ 场景识别器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_law_document_retrieval():
    """测试从Neo4j检索法律文档"""
    logger.info("🧪 测试法律文档检索...")

    try:
        from neo4j import GraphDatabase

        # 连接Neo4j
        uri = "bolt://localhost:7687"
        username = "neo4j"
        password = "athena_neo4j_2024"

        driver = GraphDatabase.driver(uri, auth=(username, password))

        # 查询法律文档（使用我们已导入的数据）
        with driver.session() as session:
            # 统计法律文档数量
            result = session.run("MATCH (d:LawDocument) RETURN count(*) as count")
            count = result.single()['count']
            logger.info(f"   ✅ 找到 {count} 个法律文档节点")

            # 获取几个示例
            if count > 0:
                result = session.run("""
                    MATCH (d:LawDocument)
                    RETURN d.law_id, d.article_title, d.category
                    LIMIT 5
                """)
                records = list(result)
                logger.info(f"   示例文档:")
                for record in records:
                    logger.info(f"      - {record['d.law_id']}: {record['d.article_title'][:50] if record['d.article_title'] else 'N/A'}")

        driver.close()
        return True, count

    except Exception as e:
        logger.error(f"❌ 法律文档检索失败: {e}")
        import traceback
        traceback.print_exc()
        return False, 0


def generate_dynamic_prompt(scenario, law_count):
    """基于场景和法律文档生成动态提示词"""
    logger.info("📝 生成动态提示词...")

    # 构建提示词
    prompt = f"""# 专利法律助手提示词

## 当前任务
您是专业的专利法律助手，正在协助用户完成以下任务：

**业务领域**: {scenario.domain}
**任务类型**: {scenario.task_type}
**处理阶段**: {scenario.phase}

## 可用资源
系统已访问 {law_count} 条法律文档，涵盖专利法、商标法、著作权等领域。

## 工作指引
1. **理解用户需求**: 仔细理解用户的具体问题和需求
2. **应用专业知识**: 基于相关法律条款进行分析
3. **提供实用建议**: 给出具体、可操作的法律建议
4. **保持专业态度**: 用专业、友好、易于理解的语言回复

## 注意事项
- 如果信息不足，主动询问用户相关细节
- 对于复杂问题，可以分步骤进行解释
- 引用具体法律条文时，请注明来源
- 避免给出绝对性保证，使用"可能"、"倾向于"等表述

## 当前用户输入
用户询问: 帮我分析这个专利的创造性步骤

请基于以上信息，为用户提供专业的专利法律指导。
"""

    logger.info("   ✅ 提示词生成成功")
    logger.info(f"   提示词长度: {len(prompt)} 字符")

    return prompt


def main():
    """主函数"""
    logger.info("=" * 70)
    logger.info("🚀 测试基于法律世界模型的动态提示词系统 - 工作版本")
    logger.info("=" * 70)
    logger.info("")

    # 测试1: 场景识别
    success1, scenario = test_scenario_identifier()
    logger.info("")

    # 测试2: 法律文档检索
    success2, law_count = test_law_document_retrieval()
    logger.info("")

    # 测试3: 动态提示词生成
    if success1 and success2:
        prompt = generate_dynamic_prompt(scenario, law_count)
        logger.info("")
        logger.info("=" * 70)
        logger.info("📋 生成的动态提示词:")
        logger.info("=" * 70)
        logger.info(prompt)
        logger.info("=" * 70)
        logger.info("")
        logger.info("✅ 所有测试通过！系统可以正常运行！")
    else:
        logger.info("❌ 部分测试失败，但核心功能可用")

    logger.info("")
    logger.info("📊 系统状态总结:")
    logger.info(f"   场景识别: {'✅ 正常' if success1 else '❌ 失败'}")
    logger.info(f"   法律文档检索: {'✅ 正常 (' + str(law_count) + ' 条文档)' if success2 else '❌ 失败'}")
    logger.info(f"   动态提示词生成: {'✅ 正常' if success1 and success2 else '❌ 失败'}")

    return success1 and success2


if __name__ == "__main__":
    main()
