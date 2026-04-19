#!/usr/bin/env python3
"""
执行知识图谱NGQL脚本
"""

from __future__ import annotations
import logging
import os
from pathlib import Path

# 设置路径
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
PATENT_PROCESSED_DIR = PROJECT_ROOT / "apps/apps/patents" / "processed"
KG_OUTPUT_DIR = PATENT_PROCESSED_DIR / "knowledge_graph"

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_env_password(key: str, default: str = "") -> str:
    """从环境变量获取密码"""
    return os.environ.get(key, default)


def execute_ngql_file(ngql_file: Path, pool) -> dict:
    """执行单个NGQL文件"""
    result = {
        'file': ngql_file.name,
        'success': False,
        'error': None,
        'statements_executed': 0
    }

    try:
        # 读取NGQL文件
        with open(ngql_file, encoding='utf-8') as f:
            ngql_content = f.read()

        # 提取专利号
        patent_number = ngql_file.stem.replace('_kg', '')

        logger.info(f"  执行: {patent_number}")

        # 获取session并执行
        session = pool.get_session()

        # 先切换空间
        session.execute("USE patent_kg")

        # 分割语句并执行
        statements = [s.strip() for s in ngql_content.split(';') if s.strip() and not s.strip().startswith('--')]

        for statement in statements:
            if statement:
                # 跳过USE语句，已经执行过了
                if statement.strip().startswith('USE '):
                    continue

                try:
                    exec_result = session.execute(statement)
                    if exec_result.is_succeeded():
                        result['statements_executed'] += 1
                    else:
                        logger.warning(f"    ⚠️  语句失败: {exec_result.error_msg()[:100]}")
                except Exception as e:
                    logger.warning(f"    ⚠️  执行异常: {str(e)[:100]}")

        session.release()

        result['success'] = True
        logger.info(f"    ✅ 执行完成: {result['statements_executed']} 条语句")

    except Exception as e:
        result['error'] = str(e)
        logger.error(f"    ❌ 失败: {e}")

    return result


def main() -> None:
    """主流程"""
    logger.info("="*70)
    logger.info("执行知识图谱NGQL脚本")
    logger.info("="*70)

    # 查找所有NGQL文件
    ngql_files = list(KG_OUTPUT_DIR.glob("*_kg.ngql"))

    if not ngql_files:
        logger.warning(f"未找到NGQL脚本: {KG_OUTPUT_DIR}")
        return

    logger.info(f"\n找到 {len(ngql_files)} 个NGQL脚本")
    logger.info(f"目录: {KG_OUTPUT_DIR}")

    # 首先检查/创建空间和TAG
    logger.info("\n检查NebulaGraph空间...")
    try:
        from nebula3.Config import Config
        from nebula3.gclient.net import ConnectionPool

        # 创建配置
        config = Config()
        config.max_connection_pool_size = 10

        # 创建连接池
        pool = ConnectionPool()
        addresses = [('127.0.0.1', 9669)]

        # 正确的连接方式
        try:
            pool.init(addresses, user='root', password=get_env_password('NEBULA_PASSWORD'), space_name='patent_kg')
            logger.info("  ✅ 已连接到空间: patent_kg")
        except Exception as e:
            logger.warning(f"  ⚠️  连接失败: {e}")
            logger.info("  💡 请使用现有空间: patent_kg")
            return

        # 获取session
        session = pool.get_session()

        # 检查patent TAG是否存在，不存在则创建
        check_tag_query = "SHOW TAGS"
        result = session.execute(check_tag_query)

        if result.is_succeeded():
            tags = [row.values[0].as_string() for row in result.rows()]
            logger.info(f"  现有TAG: {tags}")

            if 'patent' not in tags:
                logger.info("  创建patent TAG...")
                create_tag_query = """
                CREATE TAG IF NOT EXISTS patent(
                    patent_number string,
                    title string,
                    abstract string,
                    text_length int,
                    extraction_method string,
                    pages_processed int
                )
                """
                result = session.execute(create_tag_query)
                if result.is_succeeded():
                    logger.info("  ✅ 创建patent TAG成功")
                else:
                    logger.warning(f"  ⚠️  创建patent TAG失败: {result.error_msg()}")
            else:
                logger.info("  ✅ patent TAG已存在")

        session.release()
        pool.close()

    except ImportError:
        logger.error("❌ nebula3-python未安装")
        logger.info("💡 安装: pip3 install nebula3-python")
        return

    # 执行每个NGQL文件
    results = []

    # 重新连接池用于执行
    pool = ConnectionPool()
    pool.init(addresses, user='root', password=get_env_password('NEBULA_PASSWORD'), space_name='patent_kg')

    for ngql_file in sorted(ngql_files):
        result = execute_ngql_file(ngql_file, pool)
        results.append(result)

    pool.close()

    # 总结
    logger.info(f"\n{'='*70}")
    logger.info("执行完成")
    logger.info(f"{'='*70}")
    logger.info(f"成功: {sum(1 for r in results if r['success'])}/{len(results)}")

    if any(r['error'] for r in results):
        logger.info("\n❌ 失败的文件:")
        for result in results:
            if result['error']:
                logger.info(f"   - {result['file']}: {result['error']}")


if __name__ == "__main__":
    main()
