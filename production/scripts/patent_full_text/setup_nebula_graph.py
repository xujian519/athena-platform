#!/usr/bin/env python3
"""
专利全文PDF知识图谱设置 - NebulaGraph空间创建
创建patent_full_text空间及其TAG和EDGE定义

作者: Athena平台团队
创建时间: 2025-12-24
"""

from __future__ import annotations
import logging
from datetime import datetime
from typing import Any

from nebula3.Config import Config
from nebula3.gclient.net import ConnectionPool

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/setup_nebula_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


# NebulaGraph连接配置
NEBULA_HOSTS = ["127.0.0.1:9669"]
NEBULA_USERNAME = "root"
NEBULA_PASSWORD = "xiaonuo@Athena"
SPACE_NAME = "patent_full_text"
REPLICA_FACTOR = 1
VID_TYPE = "FIXED_STRING(64)"


def execute_query(session, query, description="") -> None:
    """执行查询并处理结果"""
    try:
        result = session.execute(query)
        if result.is_succeeded():
            logger.info(f"✅ {description or '查询成功'}")
            return True
        else:
            logger.error(f"❌ {description or '查询失败'}: {result.error_msg()}")
            return False
    except Exception as e:
        logger.error(f"❌ 执行异常 ({description}): {e}")
        return False


def setup_patent_full_text_space() -> Any:
    """设置专利全文知识图谱空间"""

    logger.info("=" * 70)
    logger.info("🚀 NebulaGraph专利全文知识图谱初始化")
    logger.info("=" * 70)

    # 连接NebulaGraph
    try:
        config = Config()
        config.max_connection_pool_size = 10
        connection_pool = ConnectionPool()
        connection_pool.init(NEBULA_HOSTS, config)

        session = connection_pool.get_session(NEBULA_USERNAME, NEBULA_PASSWORD)
        logger.info("✅ NebulaGraph连接成功")

    except Exception as e:
        logger.error(f"❌ NebulaGraph连接失败: {e}")
        return False

    # ========== 创建空间 ==========
    logger.info("")
    logger.info("🔨 创建知识图谱空间...")

    # 检查空间是否存在
    check_query = f"SHOW SPACES LIKE '{SPACE_NAME}'"
    result = session.execute(check_query)

    if result.is_succeeded() and result.row_size() > 0:
        logger.info(f"📋 空间 '{SPACE_NAME}' 已存在，跳过创建")
    else:
        create_space_query = f"""
        CREATE SPACE IF NOT EXISTS {SPACE_NAME} (
            partition_num = 10,
            replica_factor = {REPLICA_FACTOR},
            vid_type = {VID_TYPE}
        );
        """
        if execute_query(session, create_space_query, f"创建空间 {SPACE_NAME}"):
            # 等待空间创建完成
            import time
            logger.info("⏳ 等待空间就绪...")
            time.sleep(15)  # 等待空间创建完成
        else:
            return False

    # 切换到目标空间
    use_query = f"USE {SPACE_NAME};"
    if not execute_query(session, use_query, f"切换到空间 {SPACE_NAME}"):
        return False

    # ========== 创建TAG（顶点类型） ==========

    logger.info("")
    logger.info("🔨 创建TAG（顶点类型）...")

    # 1. patent - 专利主顶点
    patent_tag = """
    CREATE TAG IF NOT EXISTS patent(
        id string,
        application_number string,
        publication_number string,
        title string,
        patent_type string,
        ipc_main_class string,
        applicant string,
        inventor string,
        application_date string,
        publication_date string,
        pdf_path string,
        vector_id string,
        source string,
        created_at string
    );
    """
    execute_query(session, patent_tag, "创建TAG: patent")

    # 2. claim - 权利要求顶点
    claim_tag = """
    CREATE TAG IF NOT EXISTS claim(
        id string,
        patent_id string,
        claim_number int,
        claim_type string,
        claim_text string,
        claim_summary string
    );
    """
    execute_query(session, claim_tag, "创建TAG: claim")

    # 3. applicant - 申请人顶点
    applicant_tag = """
    CREATE TAG IF NOT EXISTS applicant(
        id string,
        name string,
        country string,
        region string,
        type string,
        applicant_type string
    );
    """
    execute_query(session, applicant_tag, "创建TAG: applicant")

    # 4. inventor - 发明人顶点
    inventor_tag = """
    CREATE TAG IF NOT EXISTS inventor(
        id string,
        name string,
        country string
    );
    """
    execute_query(session, inventor_tag, "创建TAG: inventor")

    # 5. ipc_class - IPC分类顶点
    ipc_tag = """
    CREATE TAG IF NOT EXISTS ipc_class(
        id string,
        code string,
        description string,
        section string,
        subclass string
    );
    """
    execute_query(session, ipc_tag, "创建TAG: ipc_class")

    # 6. technology - 技术领域顶点
    tech_tag = """
    CREATE TAG IF NOT EXISTS technology(
        id string,
        name string,
        category string
    );
    """
    execute_query(session, tech_tag, "创建TAG: technology")

    # ========== 创建EDGE（边类型） ==========

    logger.info("")
    logger.info("🔨 创建EDGE（边类型）...")

    # 1. HAS_CLAIM - 专利包含权利要求
    has_claim_edge = """
    CREATE EDGE IF NOT EXISTS HAS_CLAIM(
        sequence int
    );
    """
    execute_query(session, has_claim_edge, "创建EDGE: HAS_CLAIM")

    # 2. HAS_APPLICANT - 专利关联申请人
    has_applicant_edge = """
    CREATE EDGE IF NOT EXISTS HAS_APPLICANT(
        application_date string
    );
    """
    execute_query(session, has_applicant_edge, "创建EDGE: HAS_APPLICANT")

    # 3. HAS_INVENTOR - 专利关联发明人
    has_inventor_edge = """
    CREATE EDGE IF NOT EXISTS HAS_INVENTOR(
        sequence int
    );
    """
    execute_query(session, has_inventor_edge, "创建EDGE: HAS_INVENTOR")

    # 4. BELONGS_TO_IPC - 专利属于IPC分类
    belongs_ipc_edge = """
    CREATE EDGE IF NOT EXISTS BELONGS_TO_IPC(
        relevance double
    );
    """
    execute_query(session, belongs_ipc_edge, "创建EDGE: BELONGS_TO_IPC")

    # 5. RELATES_TO_TECH - 专利关联技术领域
    relates_tech_edge = """
    CREATE EDGE IF NOT EXISTS RELATES_TO_TECH(
        relevance double
    );
    """
    execute_query(session, relates_tech_edge, "创建EDGE: RELATES_TO_TECH")

    # 6. CITES - 引用关系
    cites_edge = """
    CREATE EDGE IF NOT EXISTS CITES(
        citation_type string,
        citation_date string
    );
    """
    execute_query(session, cites_edge, "创建EDGE: CITES")

    # 7. FAMILY - 同族关系
    family_edge = """
    CREATE EDGE IF NOT EXISTS FAMILY(
        family_id string,
        relationship string
    );
    """
    execute_query(session, family_edge, "创建EDGE: FAMILY")

    # 8. SIMILAR_TO - 相似专利
    similar_edge = """
    CREATE EDGE IF NOT EXISTS SIMILAR_TO(
        similarity double,
        compare_date string
    );
    """
    execute_query(session, similar_edge, "创建EDGE: SIMILAR_TO")

    # ========== 创建原生索引 ==========

    logger.info("")
    logger.info("🔨 创建原生索引...")

    # TAG索引
    tag_indexes = [
        "CREATE TAG INDEX IF NOT EXISTS idx_patent_app_number ON patent(application_number(64));",
        "CREATE TAG INDEX IF NOT EXISTS idx_patent_pub_number ON patent(publication_number(64));",
        "CREATE TAG INDEX IF NOT EXISTS idx_applicant_name ON applicant(name(64));",
        "CREATE TAG INDEX IF NOT EXISTS idx_inventor_name ON inventor(name(64));",
        "CREATE TAG INDEX IF NOT EXISTS idx_ipc_code ON ipc_class(code(32));",
    ]

    for idx_query in tag_indexes:
        execute_query(session, idx_query, f"索引: {idx_query.split()[5]}")

    # EDGE索引
    edge_indexes = [
        "CREATE EDGE INDEX IF NOT EXISTS idx_cites ON CITES(citation_type(32));",
        "CREATE EDGE INDEX IF NOT EXISTS idx_family ON FAMILY(family_id(64));",
    ]

    for idx_query in edge_indexes:
        execute_query(session, idx_query, f"索引: {idx_query.split()[5]}")

    # ========== 验证创建结果 ==========
    logger.info("")
    logger.info("=" * 70)
    logger.info("🎉 NebulaGraph知识图谱初始化完成！")
    logger.info("=" * 70)
    logger.info(f"📋 空间名称: {SPACE_NAME}")
    logger.info("")
    logger.info("📊 TAG（顶点类型）:")
    logger.info("   - patent: 专利主顶点")
    logger.info("   - claim: 权利要求顶点")
    logger.info("   - applicant: 申请人顶点")
    logger.info("   - inventor: 发明人顶点")
    logger.info("   - ipc_class: IPC分类顶点")
    logger.info("   - technology: 技术领域顶点")
    logger.info("")
    logger.info("🔗 EDGE（边类型）:")
    logger.info("   - HAS_CLAIM: 专利包含权利要求")
    logger.info("   - HAS_APPLICANT: 专利关联申请人")
    logger.info("   - HAS_INVENTOR: 专利关联发明人")
    logger.info("   - BELONGS_TO_IPC: 专利属于IPC分类")
    logger.info("   - RELATES_TO_TECH: 专利关联技术领域")
    logger.info("   - CITES: 引用关系")
    logger.info("   - FAMILY: 同族关系")
    logger.info("   - SIMILAR_TO: 相似专利")
    logger.info("")

    # 显示空间统计
    logger.info("📈 空间统计:")
    stats_query = f"""
    USE {SPACE_NAME};
    SHOW HOSTS;
    """
    session.execute(stats_query)

    # 关闭连接
    session.release()
    connection_pool.close()

    logger.info("")
    logger.info("💡 使用方法:")
    logger.info(f"   nebula-console -addr 127.0.0.1 -port 9669 -u root -p {NEBULA_PASSWORD}")
    logger.info(f"   USE {SPACE_NAME};")
    logger.info("")

    return True


def main() -> None:
    """主函数"""
    setup_patent_full_text_space()


if __name__ == "__main__":
    main()
