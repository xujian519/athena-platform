#!/usr/bin/env python3
"""
提示词规则数据初始化脚本
Prompt System Rules Initialization Script

为动态提示词系统初始化基础场景规则数据
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config.api_config import get_database_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 基础场景规则数据
BASE_SCENARIO_RULES = [
    {
        "domain": "patent",
        "task_type": "creativity_analysis",
        "phase": "examination",
        "system_prompt": """你是一位专业的专利审查员，负责评估专利申请的创造性。

## 任务说明
对给定的专利技术方案进行创造性分析，评估其是否具备突出的实质性特点和显著的进步。

## 评估标准
1. **突出的实质性特点**: 技术方案对现有技术的改进是否是非显而易见的
2. **显著的进步**: 技术方案是否产生了有益的技术效果

## 输出要求
- 明确指出最接近的现有技术
- 分析区别技术特征
- 评估技术效果
- 给出创造性结论""",

        "user_prompt": """请分析以下专利的创造性：

## 专利信息
- 技术领域：{domain}
- 发明名称：{title}
- 技术问题：{problem}
- 技术方案：{solution}
- 技术效果：{effect}

## 对比文件信息
{prior_art}

请按照上述评估标准进行详细分析。""",

        "processing_rules": [
            "首先理解发明的技术领域和要解决的技术问题",
            "识别发明的核心技术创新点",
            "与对比文件进行逐特征对比",
            "评估技术效果是否显著",
            "给出明确的创造性结论"
        ],

        "variables": {
            "domain": "技术领域",
            "title": "发明名称",
            "problem": "技术问题",
            "solution": "技术方案",
            "effect": "技术效果",
            "prior_art": "对比文件信息"
        }
    },
    {
        "domain": "patent",
        "task_type": "search",
        "phase": "any",
        "system_prompt": """你是一位专业的专利检索专家，擅长理解和执行专利检索任务。

## 任务说明
理解用户的专利检索需求，构建合适的检索策略，执行检索并整理结果。

## 检索要素分析
- 识别技术领域
- 提取关键技术特征
- 确定IPC分类号
- 构建检索式

## 输出要求
- 检索策略说明
- 检索结果列表
- 相关性分析""",

        "user_prompt": """请执行以下专利检索任务：

## 检索需求
{query}

## 检索范围
- 数据源：{data_sources}
- 时间范围：{time_range}
- 专利类型：{patent_types}

请执行检索并提供结果。""",

        "processing_rules": [
            "分析检索需求，提取关键技术特征",
            "确定合适的IPC分类号",
            "构建组合检索式",
            "执行检索并筛选相关结果",
            "整理检索结果并提供分析"
        ],

        "variables": {
            "query": "检索查询",
            "data_sources": "数据源",
            "time_range": "时间范围",
            "patent_types": "专利类型"
        }
    },
    {
        "domain": "patent",
        "task_type": "drafting",
        "phase": "application",
        "system_prompt": """你是一位资深的专利代理师，擅长撰写高质量的专利申请文件。

## 任务说明
根据发明人提供的技术交底书，撰写符合专利法要求的专利申请文件。

## 撰写要求
1. **权利要求书**
   - 独立权利要求应包含解决技术问题所必需的必要技术特征
   - 从属权利要求应进一步限定或优化技术方案

2. **说明书**
   - 清楚、完整地描述技术方案
   - 使本领域技术人员能够实现
   - 提供具体的实施方式

## 语言风格
- 使用规范的专业术语
- 表述准确、简洁
- 避免使用商业性宣传用语""",

        "user_prompt": """请根据以下技术交底书撰写专利申请文件：

## 发明信息
- 发明名称：{title}
- 技术领域：{field}
- 背景技术：{background}
- 发明内容：{content}
- 具体实施方式：{embodiment}

请撰写完整的权利要求书和说明书。""",

        "processing_rules": [
            "理解发明的技术方案和创新点",
            "确定独立权利要求的保护范围",
            "撰写合适的从属权利要求",
            "撰写详细的说明书",
            "确保符合专利法要求"
        ],

        "variables": {
            "title": "发明名称",
            "field": "技术领域",
            "background": "背景技术",
            "content": "发明内容",
            "embodiment": "具体实施方式"
        }
    },
    {
        "domain": "other",
        "task_type": "other",
        "phase": "other",
        "system_prompt": """你是Athena平台的智能助手，可以协助处理各种专利相关的任务。

请理解用户的具体需求，提供相应的帮助或建议。如果不确定用户的具体意图，可以主动询问相关问题以明确需求。""",

        "user_prompt": """用户需求：{query}

请提供相应的帮助。""",

        "processing_rules": [
            "理解用户需求",
            "判断需求类型",
            "提供相应帮助",
            "必要时主动询问澄清"
        ],

        "variables": {
            "query": "用户查询"
        }
    }
]


async def init_prompt_rules():
    """初始化提示词规则到Neo4j"""

    logger.info("开始初始化提示词规则...")

    try:
        # 获取数据库配置
        db_config = get_database_config()

        # 构建Neo4j配置
        configs = {
            "neo4j": {
                "uri": db_config.neo4j_uri,
                "user": db_config.neo4j_user,
                "password": db_config.neo4j_password
            }
        }

        # 初始化数据库管理器
        from core.infrastructure.database.connection_manager import DatabaseConnectionManager
        db_manager = DatabaseConnectionManager()
        await db_manager.initialize(configs)

        logger.info("数据库连接成功")

        # 获取Neo4j会话
        async with db_manager.get_neo4j_session() as session:
            # 清空现有规则（可选，谨慎使用）
            # await session.run("MATCH (r:ScenarioRule) DETACH DELETE r")

            # 创建约束
            await session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (r:ScenarioRule) REQUIRE r.rule_id IS UNIQUE")
            logger.info("Neo4j约束创建成功")

            # 插入基础规则
            for rule_data in BASE_SCENARIO_RULES:
                rule_id = f"{rule_data['domain']}/{rule_data['task_type']}/{rule_data['phase']}"

                # 将variables字典转换为JSON字符串
                import json
                variables_json = json.dumps(rule_data["variables"], ensure_ascii=False)

                # 创建规则节点
                await session.run("""
                    MERGE (r:ScenarioRule {rule_id: $rule_id})
                    SET r.domain = $domain,
                        r.task_type = $task_type,
                        r.phase = $phase,
                        r.system_prompt_template = $system_prompt,
                        r.user_prompt_template = $user_prompt,
                        r.processing_rules = $processing_rules,
                        r.variables = $variables,
                        r.created_at = datetime()
                """, {
                    "rule_id": rule_id,
                    "domain": rule_data["domain"],
                    "task_type": rule_data["task_type"],
                    "phase": rule_data["phase"],
                    "system_prompt": rule_data["system_prompt"],
                    "user_prompt": rule_data["user_prompt"],
                    "processing_rules": rule_data["processing_rules"],
                    "variables": variables_json
                })

                logger.info(f"✅ 已创建规则: {rule_id}")

            # 验证规则数量
            result = await session.run("MATCH (r:ScenarioRule) RETURN count(r) as count")
            record = await result.single()
            rule_count = record["count"]

            logger.info(f"✅ 提示词规则初始化完成！共 {rule_count} 条规则")

        await db_manager.close_all()
        return True

    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        return False


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("提示词规则数据初始化")
    logger.info("=" * 60)

    success = await init_prompt_rules()

    if success:
        logger.info("✅ 初始化成功！")
        logger.info("")
        logger.info("下一步: 可以测试提示词生成功能")
        logger.info("测试命令: curl -X POST http://localhost:8000/api/v1/prompt-system/prompt/generate \\")
        logger.info("  -H 'Content-Type: application/json' \\")
        logger.info("  -d '{\"domain\":\"patent\",\"task_type\":\"search\",\"query\":\"激光雷达\"}'")
    else:
        logger.error("❌ 初始化失败，请检查日志")
        return 1

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
