#!/usr/bin/env python3
"""
简化版patent_rules图空间设置脚本
作者: 小诺·双鱼公主 v4.0.0
"""

from __future__ import annotations
import logging
from typing import Any

from nebula3.Config import Config
from nebula3.gclient.net import ConnectionPool

from core.config.secure_config import get_config

config = get_config()


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_patent_rules_graph() -> Any:
    """设置patent_rules图空间"""

    # 配置连接
    config = Config()
    config.max_connection_pool_size = 10

    # 创建连接池
    pool = ConnectionPool()

    # 连接参数
    host = "127.0.0.1"
    port = 9669
    user = "root"
    password=config.get("NEBULA_PASSWORD", required=True)

    # 初始化连接
    logger.info(f"🔗 连接到NebulaGraph: {host}:{port}")
    if not pool.init([(host, port)], user, password):
        logger.error("❌ 连接失败!")
        return False

    logger.info("✅ 连接成功!")

    # 获取session
    session = pool.get_session('root', 'nebula')

    try:
        # 步骤1: 创建图空间
        logger.info("\n📊 步骤1: 创建图空间 patent_rules")
        result = session.execute("""
            CREATE SPACE IF NOT EXISTS patent_rules (
                partition_num = 10,
                replica_factor = 1,
                vid_type = FIXED_STRING(256)
            );
        """)

        if result.is_succeeded():
            logger.info("✅ 图空间创建成功!")
        else:
            logger.error(f"❌ 创建失败: {result.error_msg()}")

        # 等待图空间初始化
        logger.info("⏳ 等待20秒让图空间初始化...")
        import time
        time.sleep(20)

        # 使用图空间
        logger.info("\n📊 步骤2: 使用图空间")
        result = session.execute("USE patent_rules;")
        logger.info("✅ 已切换到patent_rules图空间")

        # 步骤3: 创建标签
        logger.info("\n📊 步骤3: 创建标签")

        # legal_term标签
        result = session.execute("""
            CREATE TAG IF NOT EXISTS legal_term(
                name string,
                definition string,
                category string,
                source string,
                confidence double
            );
        """)
        logger.info("✅ legal_term标签已创建")

        # document标签
        result = session.execute("""
            CREATE TAG IF NOT EXISTS document(
                title string,
                doc_type string,
                publish_date string,
                source string,
                confidence double
            );
        """)
        logger.info("✅ document标签已创建")

        # tech_field标签
        result = session.execute("""
            CREATE TAG IF NOT EXISTS tech_field(
                name string,
                description string,
                level string,
                keywords string,
                confidence double
            );
        """)
        logger.info("✅ tech_field标签已创建")

        # 步骤4: 创建边类型
        logger.info("\n📊 步骤4: 创建边类型")

        result = session.execute("""
            CREATE EDGE IF NOT EXISTS related_to(
                relation_type string,
                strength double,
                confidence double
            );
        """)
        logger.info("✅ related_to边已创建")

        result = session.execute("""
            CREATE EDGE IF NOT EXISTS refers_to(
                relationship_type string,
                confidence double
            );
        """)
        logger.info("✅ refers_to边已创建")

        # 步骤5: 插入测试数据
        logger.info("\n📊 步骤5: 插入测试数据")

        # 插入一些法律术语
        test_terms = [
            ("专利法第22条", "创造性的规定", "法律条文", "patent_law", 1.0),
            ("专利法第26条", "充分公开的规定", "法律条文", "patent_law", 1.0),
            ("新颖性", "不属于现有技术", "法律概念", "patent_law", 0.95),
            ("创造性", "突出的实质性特点和显著的进步", "法律概念", "patent_law", 0.95),
        ]

        for term_id, definition, category, source, confidence in test_terms:
            query = f'INSERT VERTEX legal_term(name, definition, category, source, confidence) VALUES "{term_id}": "{term_id}", "{definition}", "{category}", "{source}", {confidence};'
            result = session.execute(query)
            if result.is_succeeded():
                logger.info(f"✅ 插入: {term_id}")
            else:
                logger.warning(f"⚠️ 插入失败: {term_id}")

        # 插入一些关系
        relations = [
            ("专利法第22条", "新颖性", "包含", 0.9),
            ("专利法第22条", "创造性", "包含", 0.9),
        ]

        for src, dst, rel_type, strength in relations:
            query = f'INSERT EDGE related_to(relation_type, strength, confidence) VALUES "{src}"->"{dst}": "{rel_type}", {strength}, 0.9;'
            result = session.execute(query)
            if result.is_succeeded():
                logger.info(f"✅ 关系: {src} -> {dst}")
            else:
                logger.warning(f"⚠️ 关系失败: {src} -> {dst}")

        # 步骤6: 验证
        logger.info("\n📊 步骤6: 验证导入结果")

        result = session.execute("MATCH (v) RETURN count(v) AS node_count;")
        if result.is_succeeded() and result.row_size() > 0:
            node_count = result.row_values(0)[0]
            logger.info(f"✅ 节点总数: {node_count}")

        result = session.execute("MATCH ()-[e]->() RETURN count(e) AS edge_count;")
        if result.is_succeeded() and result.row_size() > 0:
            edge_count = result.row_values(0)[0]
            logger.info(f"✅ 边总数: {edge_count}")

        logger.info("\n" + "="*60)
        logger.info("✅ patent_rules图空间设置完成!")
        logger.info("="*60)

        return True

    except Exception as e:
        logger.error(f"❌ 执行异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.release()
        pool.close()
        logger.info("🔌 连接已关闭")

if __name__ == "__main__":
    setup_patent_rules_graph()
