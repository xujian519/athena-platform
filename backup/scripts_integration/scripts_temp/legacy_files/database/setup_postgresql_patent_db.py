#!/usr/bin/env python3
"""
PostgreSQL专利数据库设置脚本
自动配置PostgreSQL环境、创建数据库、配置全文检索
"""

import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import psycopg2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('documentation/logs/postgresql_setup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PostgreSQLPatentSetup:
    """PostgreSQL专利数据库设置器"""

    def __init__(self):
        self.db_name = 'patent_db'
        self.db_user = 'postgres'
        self.db_password = 'postgres'  # 生产环境应该使用更安全的密码
        self.db_host = 'localhost'
        self.db_port = '5432'

        # 创建必要目录
        os.makedirs('logs', exist_ok=True)

    def check_postgresql_status(self):
        """检查PostgreSQL服务状态"""
        try:
            # 检查PostgreSQL是否运行
            result = subprocess.run(
                ['pg_isready', '-h', self.db_host, '-p', self.db_port],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info('✅ PostgreSQL服务正在运行')
                return True
            else:
                logger.error('❌ PostgreSQL服务未运行')
                return False

        except FileNotFoundError:
            logger.error('❌ 未找到PostgreSQL客户端工具')
            return False

    def start_postgresql(self):
        """启动PostgreSQL服务（macOS）"""
        try:
            logger.info('尝试启动PostgreSQL服务...')

            # macOS使用brew services
            result = subprocess.run(
                ['brew', 'services', 'start', 'postgresql'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info('✅ PostgreSQL服务启动成功')
                # 等待服务完全启动
                time.sleep(3)
                return True
            else:
                logger.error(f"❌ PostgreSQL启动失败: {result.stderr}")
                return False

        except FileNotFoundError:
            logger.error('❌ 未找到brew，请手动启动PostgreSQL')
            return False

    def create_database(self):
        """创建专利数据库"""
        try:
            # 连接到默认postgres数据库
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database='postgres',
                user=self.db_user,
                password=self.db_password
            )
            conn.autocommit = True
            cursor = conn.cursor()

            # 检查数据库是否已存在
            cursor.execute(
                'SELECT 1 FROM pg_database WHERE datname = %s',
                (self.db_name,)
            )

            if cursor.fetchone():
                logger.info(f"📊 数据库 {self.db_name} 已存在")
            else:
                # 创建数据库（使用template0避免collation冲突）
                cursor.execute(
                    f"CREATE DATABASE {self.db_name} "
                    f"WITH ENCODING 'UTF8' "
                    f"LC_COLLATE='en_US.UTF-8' "
                    f"LC_CTYPE='en_US.UTF-8' "
                    f"TEMPLATE=template0"
                )
                logger.info(f"✅ 成功创建数据库 {self.db_name}")

            cursor.close()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"❌ 创建数据库失败: {str(e)}")
            return False

    def setup_database(self):
        """设置数据库架构"""
        try:
            # 连接到专利数据库
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            cursor = conn.cursor()

            # 读取并执行SQL架构文件
            schema_file = Path('database/postgresql_patent_schema.sql')
            if not schema_file.exists():
                logger.error(f"❌ 找不到架构文件: {schema_file}")
                return False

            with open(schema_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # 执行整个SQL文件
            try:
                cursor.execute(sql_content)
                conn.commit()
                logger.info('✅ 数据库架构执行成功')
            except Exception as e:
                logger.error(f"❌ SQL执行错误: {str(e)}")
                conn.rollback()
                return False

            conn.commit()
            cursor.close()
            conn.close()

            logger.info('✅ 数据库架构设置完成')
            return True

        except Exception as e:
            logger.error(f"❌ 设置数据库失败: {str(e)}")
            return False

    def install_chinese_search(self):
        """安装中文全文检索支持"""
        try:
            logger.info('配置中文全文检索...')

            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            cursor = conn.cursor()

            # 安装jieba分词（如果需要）
            # 注意：需要先在系统层面安装jieba PostgreSQL扩展

            # 创建中文检索配置
            cursor.execute("""
                CREATE TEXT SEARCH CONFIGURATION chinese_patent (
                    COPY = simple
                );

                CREATE TEXT SEARCH DICTIONARY chinese_patent_dict (
                    TEMPLATE = simple,
                    STOPWORDS = chinese
                );

                ALTER TEXT SEARCH CONFIGURATION chinese_patent
                    ALTER MAPPING FOR asciiword, asciihword, hword_asciipart,
                                   word, hword, hword_part
                    WITH chinese_patent_dict;
            """)

            conn.commit()
            cursor.close()
            conn.close()

            logger.info('✅ 中文全文检索配置完成')
            return True

        except Exception as e:
            logger.error(f"❌ 配置中文检索失败: {str(e)}")
            return False

    def create_connection_config(self):
        """创建数据库连接配置文件"""
        config_content = f"""
# PostgreSQL专利数据库连接配置
import psycopg2
from psycopg2.extras import DictCursor

# 数据库连接参数
DB_CONFIG = {{
    'host': '{self.db_host}',
    'port': {self.db_port},
    'database': '{self.db_name}',
    'user': '{self.db_user}',
    'password': '{self.db_password}',
    'options': '-c client_encoding=UTF8'
}}

def get_patent_db_connection():
    \"\"\"获取专利数据库连接\"\"\"
    return psycopg2.connect(**DB_CONFIG, cursor_factory=DictCursor)

def get_patent_db_connection_pool():
    \"\"\"获取连接池\"\"\"
    from psycopg2 import pool

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query
    return psycopg2.pool.SimpleConnectionPool(
        minconn=2,
        maxconn=20,
        **DB_CONFIG
    )

# 测试连接
def test_connection():
    \"\"\"测试数据库连接\"\"\"
    try:
        conn = get_patent_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()[0]
        conn.close()
        logger.info(f"✅ 数据库连接成功: {{version[:50]}}...")
        return True
    except Exception as e:
        logger.info(f"❌ 数据库连接失败: {{str(e)}}")
        return False
"""

        config_file = Path('database/db_config.py')
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)

        logger.info(f"✅ 创建连接配置文件: {config_file}")
        return True

    def test_setup(self):
        """测试设置结果"""
        try:
            logger.info('测试数据库设置...')

            # 测试连接
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            cursor = conn.cursor()

            # 检查表是否创建成功
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'patent'
            """)

            tables = [row[0] for row in cursor.fetchall()]
            expected_tables = ['patents', 'data_import_log']

            for table in expected_tables:
                if table in tables:
                    logger.info(f"✅ 表 {table} 创建成功")
                else:
                    logger.error(f"❌ 表 {table} 未找到")
                    return False

            # 检查分区表
            cursor.execute("""
                SELECT inhrelid::regclass as partition_table
                FROM pg_inherits
                WHERE inhparent = 'patent.patents'::regclass
            """)

            partitions = [row[0] for row in cursor.fetchall()]
            logger.info(f"✅ 创建了 {len(partitions)} 个分区表")

            # 检查扩展
            cursor.execute("""
                SELECT extname
                FROM pg_extension
                WHERE extname IN ('uuid-ossp', 'pg_trgm', 'btree_gin', 'btree_gist')
            """)

            extensions = [row[0] for row in cursor.fetchall()]
            logger.info(f"✅ 安装了扩展: {', '.join(extensions)}")

            cursor.close()
            conn.close()

            logger.info('✅ 数据库设置测试通过')
            return True

        except Exception as e:
            logger.error(f"❌ 测试失败: {str(e)}")
            return False

    def run(self):
        """执行完整的设置流程"""
        logger.info('='*60)
        logger.info('开始设置PostgreSQL专利数据库')
        logger.info('='*60)

        # 1. 检查PostgreSQL状态
        if not self.check_postgresql_status():
            logger.info('尝试启动PostgreSQL...')
            if not self.start_postgresql():
                logger.error('❌ 无法启动PostgreSQL，请手动启动后重试')
                return False

        # 2. 创建数据库
        if not self.create_database():
            return False

        # 3. 设置架构
        if not self.setup_database():
            return False

        # 4. 配置中文检索
        if not self.install_chinese_search():
            logger.warning('⚠️  中文检索配置失败，但基础架构已设置')

        # 5. 创建配置文件
        if not self.create_connection_config():
            return False

        # 6. 测试设置
        if not self.test_setup():
            return False

        logger.info("\n" + '='*60)
        logger.info('PostgreSQL专利数据库设置完成！')
        logger.info('='*60)
        logger.info(f"数据库名: {self.db_name}")
        logger.info(f"连接信息: {self.db_user}@{self.db_host}:{self.db_port}")
        logger.info('下一步：运行数据导入脚本')

        return True

def main():
    """主函数"""
    # 检查是否在正确目录
    if not Path('database').exists():
        logger.error('❌ 请在Athena工作平台根目录运行此脚本')
        return

    # 创建设置器并运行
    setup = PostgreSQLPatentSetup()

    if setup.run():
        logger.info("\n🎉 设置成功！可以开始导入专利数据了。")
        logger.info("\n使用方法：")
        logger.info('1. 导入单年数据: python3 scripts/import_patents_to_postgres.py --year 2023')
        logger.info('2. 批量导入: python3 scripts/import_patents_to_postgres.py --batch 1985-2025')
        logger.info("3. 测试连接: python3 -c \"from database.db_config import test_connection; test_connection()\"")
    else:
        logger.error("\n❌ 设置失败，请检查错误信息并重试")

if __name__ == '__main__':
    main()