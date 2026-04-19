#!/usr/bin/env python3
"""
执行知识图谱NGQL脚本 - 正确版本
"""

from __future__ import annotations
import logging
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

    # 连接到NebulaGraph
    try:
        from nebula3.Config import Config
        from nebula3.gclient.net import ConnectionPool

        # 创建配置
        config = Config()
        config.max_connection_pool_size = 10

        # 创建连接池
        pool = ConnectionPool()
        addresses = [('127.0.0.1', 9669)]

        # 正确的初始化方式
        if pool.init(addresses, config):
            logger.info("  ✅ 已连接到NebulaGraph")
        else:
            logger.error("  ❌ 连接失败")
            return

        # 获取session (需要用户名和密码)
        session = pool.get_session('root', 'nebula')

        # 检查并切换到patent_kg空间
        logger.info("\n检查patent_kg空间...")

        # 检查空间
        result = session.execute("SHOW SPACES")
        if result.is_succeeded():
            spaces = []
            for row in result.rows():
                # row.values是一个列表，取第一个元素
                val = row.values[0]
                # 获取字符串值
                if hasattr(val, 'get_sVal'):
                    spaces.append(val.get_sVal().decode() if isinstance(val.get_sVal(), bytes) else val.get_sVal())
                elif hasattr(val, 's_val'):
                    spaces.append(val.s_val.decode() if isinstance(val.s_val, bytes) else val.s_val)
            logger.info(f"  现有空间: {spaces}")

            if 'patent_kg' not in spaces:
                logger.warning("  ⚠️  patent_kg空间不存在，请先创建")
                logger.info("  💡 使用NGQL创建:")
                logger.info("     CREATE SPACE IF NOT EXISTS patent_kg;")
                logger.info("     :sleep 10;")
                logger.info("     USE patent_kg;")
                logger.info("     CREATE TAG IF NOT EXISTS patent(")
                logger.info("         patent_number string,")
                logger.info("         title string,")
                logger.info("         abstract string,")
                logger.info("         text_length int,")
                logger.info("         extraction_method string,")
                logger.info("         pages_processed int")
                logger.info("     );")
                session.release()
                pool.close()
                return

        # 切换到patent_kg空间
        result = session.execute("USE patent_kg")
        if result.is_succeeded():
            logger.info("  ✅ 已切换到patent_kg空间")
        else:
            logger.error(f"  ❌ 切换空间失败: {result.error_msg()}")
            session.release()
            pool.close()
            return

        # 检查patent TAG
        result = session.execute("SHOW TAGS")
        if result.is_succeeded():
            tags = []
            for row in result.rows():
                val = row.values[0]
                if hasattr(val, 's_val') and val.s_val:
                    tag_name = val.s_val.decode() if isinstance(val.s_val, bytes) else val.s_val
                    tags.append(tag_name)
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
                );
                """
                result = session.execute(create_tag_query)
                if result.is_succeeded():
                    logger.info("  ✅ 创建patent TAG成功")
                else:
                    logger.warning(f"  ⚠️  创建patent TAG失败: {result.error_msg()}")

        # 执行每个NGQL文件
        logger.info("\n执行NGQL脚本...")
        results = []

        for ngql_file in sorted(ngql_files):
            patent_number = ngql_file.stem.replace('_kg', '')
            logger.info(f"  执行: {patent_number}")

            # 读取NGQL文件
            with open(ngql_file, encoding='utf-8') as f:
                ngql_content = f.read()

            # 分割语句并执行
            statements = [s.strip() for s in ngql_content.split(';')
                         if s.strip() and not s.strip().startswith('--')]

            success_count = 0
            for statement in statements:
                # 跳过USE语句
                if statement.strip().startswith('USE '):
                    continue

                try:
                    exec_result = session.execute(statement)
                    if exec_result.is_succeeded():
                        success_count += 1
                    else:
                        logger.warning(f"    ⚠️  语句失败: {exec_result.error_msg()[:100]}")
                except Exception as e:
                    logger.warning(f"    ⚠️  执行异常: {str(e)[:100]}")

            logger.info(f"    ✅ 完成: {success_count} 条语句")
            results.append({'patent': patent_number, 'success': True, 'statements': success_count})

        session.release()
        pool.close()

        # 总结
        logger.info(f"\n{'='*70}")
        logger.info("执行完成")
        logger.info(f"{'='*70}")
        logger.info(f"成功: {len(results)}/{len(ngql_files)}")
        logger.info("")

        # 验证结果
        logger.info("验证结果...")
        session = pool.get_session('root', 'nebula')
        session.execute("USE patent_kg")

        result = session.execute("MATCH (v:patent) RETURN count(v) as total")
        if result.is_succeeded() and result.row_size() > 0:
            count = result.row_values(0)[0]
            if hasattr(count, 'i_val'):
                logger.info(f"  patent顶点总数: {count.i_val}")

        result = session.execute("MATCH (v:patent) RETURN v.patent_number, v.title LIMIT 10")
        if result.is_succeeded():
            logger.info("  专利示例:")
            for row in result.rows():
                patent_num = row.values[0]
                title = row.values[1]
                patent_num_str = patent_num.s_val.decode() if hasattr(patent_num, 's_val') and patent_num.s_val else str(patent_num)
                title_str = ""
                if hasattr(title, 's_val') and title.s_val:
                    title_str = title.s_val.decode() if isinstance(title.s_val, bytes) else title.s_val
                logger.info(f"    - {patent_num_str}: {title_str[:50]}...")

        session.release()
        pool.close()

    except ImportError:
        logger.error("❌ nebula3-python未安装")
        logger.info("💡 安装: pip3 install nebula3-python")
    except Exception as e:
        logger.error(f"❌ 执行失败: {e}")


if __name__ == "__main__":
    main()
