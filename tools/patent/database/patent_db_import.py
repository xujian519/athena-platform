#!/usr/bin/env python3
"""
专利数据PostgreSQL导入脚本
Patent Data PostgreSQL Import Script

将解析的Excel数据导入到PostgreSQL数据库
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class PatentDBImporter:
    """专利数据库导入器"""

    def __init__(self):
        # 检查PostgreSQL路径
        postgres_path = "/opt/homebrew/opt/postgresql@17/bin"
        if postgres_path not in os.environ.get("PATH", ""):
            os.environ["PATH"] = postgres_path + ":" + os.environ.get("PATH", "")

        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "patent_archive",
            "user": "xujian",  # 使用当前用户
            "password": ""  # 本地PostgreSQL可能不需要密码
        }

    def create_tables(self):
        """创建数据库表"""
        sql_statements = [
            # 专利客户表
            """
            CREATE TABLE IF NOT EXISTS patent_clients (
                id SERIAL PRIMARY KEY,
                client_name VARCHAR(200) NOT NULL UNIQUE,
                patent_count INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 专利表
            """
            CREATE TABLE IF NOT EXISTS patents (
                id SERIAL PRIMARY KEY,
                patent_number VARCHAR(50) NOT NULL UNIQUE,
                patent_name VARCHAR(500),
                patent_type VARCHAR(50),
                application_date DATE,
                grant_date DATE,
                legal_status VARCHAR(100),
                review_status VARCHAR(200),
                archive_location VARCHAR(200),
                application_method VARCHAR(100),
                sequence_number VARCHAR(50),
                archive_number VARCHAR(50),
                client_id INTEGER REFERENCES patent_clients(id),
                agency VARCHAR(200),
                contact_info VARCHAR(500),
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 专利审查记录表
            """
            CREATE TABLE IF NOT EXISTS patent_reviews (
                id SERIAL PRIMARY KEY,
                patent_id INTEGER REFERENCES patents(id),
                review_date DATE,
                review_type VARCHAR(50),
                status VARCHAR(50),
                content TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 专利费用记录表
            """
            CREATE TABLE IF NOT EXISTS patent_fees (
                id SERIAL PRIMARY KEY,
                patent_id INTEGER REFERENCES patents(id),
                fee_type VARCHAR(50),
                amount DECIMAL(12,2),
                due_date DATE,
                paid_date DATE,
                status VARCHAR(20),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 创建索引
            "CREATE INDEX IF NOT EXISTS idx_patents_client_id ON patents(client_id);",
            "CREATE INDEX IF NOT EXISTS idx_patents_number ON patents(patent_number);",
            "CREATE INDEX IF NOT EXISTS idx_patents_status ON patents(legal_status);",
            "CREATE INDEX IF NOT EXISTS idx_patents_application_date ON patents(application_date);",
        ]

        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            print("正在创建数据库表...")
            for sql in sql_statements:
                cursor.execute(sql)

            conn.commit()
            print("✅ 数据库表创建成功！")

        except Exception as e:
            print(f"❌ 创建表失败: {str(e)}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    def get_connection(self):
        """获取数据库连接"""
        try:
            # 如果password为空，则不传递
            if self.db_config["password"]:
                conn = psycopg2.connect(
                    host=self.db_config["host"],
                    port=self.db_config["port"],
                    database=self.db_config["database"],
                    user=self.db_config["user"],
                    password=self.db_config["password"]
                )
            else:
                conn = psycopg2.connect(
                    host=self.db_config["host"],
                    port=self.db_config["port"],
                    database=self.db_config["database"],
                    user=self.db_config["user"]
                )
            return conn
        except Exception as e:
            print(f"❌ 数据库连接失败: {str(e)}")
            print(f"   连接参数: host={self.db_config['host']}, port={self.db_config['port']}, database={self.db_config['database']}, user={self.db_config['user']}")
            return None

    def import_clients(self, clients_data: dict) -> dict[str, int]:
        """导入客户数据"""
        conn = self.get_connection()
        if not conn:
            return {}

        client_map = {}
        try:
            cursor = conn.cursor()

            for client_name, client_info in clients_data.items():
                # 检查客户是否已存在
                cursor.execute(
                    "SELECT id FROM patent_clients WHERE client_name = %s",
                    (client_name,)
                )
                result = cursor.fetchone()

                if result:
                    # 更新现有客户
                    cursor.execute(
                        """
                        UPDATE patent_clients
                        SET patent_count = patent_count + %s
                        WHERE id = %s
                        """,
                        (client_info["patent_count"], result[0])
                    )
                    client_map[client_name] = result[0]
                else:
                    # 插入新客户
                    cursor.execute(
                        """
                        INSERT INTO patent_clients (client_name, patent_count)
                        VALUES (%s, %s)
                        RETURNING id
                        """,
                        (client_name, client_info["patent_count"])
                    )
                    client_id = cursor.fetchone()[0]
                    client_map[client_name] = client_id

            conn.commit()
            print(f"✅ 成功导入/更新 {len(client_map)} 个客户")

        except Exception as e:
            print(f"❌ 导入客户数据失败: {str(e)}")
            conn.rollback()
        finally:
            conn.close()

        return client_map

    def import_patents(self, patents_data: list[dict], client_map: dict[str, int]):
        """导入专利数据"""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            imported_count = 0
            skipped_count = 0

            for patent in patents_data:
                # 获取客户ID
                client_name = patent.get("client_name", "")
                client_id = client_map.get(client_name)

                # 检查专利是否已存在
                cursor.execute(
                    "SELECT id FROM patents WHERE patent_number = %s",
                    (patent["patent_number"],)
                )
                result = cursor.fetchone()

                if result:
                    skipped_count += 1
                    continue

                # 处理日期格式
                def clean_date(date_str):
                    if not date_str or pd.isna(date_str):
                        return None
                    date_str = str(date_str).strip()

                    # 检查是否是有效日期格式
                    valid_date_chars = set('0123456789-/.年月日')
                    if not all(c in valid_date_chars or c.isspace() for c in date_str):
                        return None

                    # 特殊处理类似 "201605-31" 的格式
                    if '-' in date_str and len(date_str.split('-')[0]) == 6:
                        parts = date_str.split('-')
                        if len(parts) == 2 and parts[0].isdigit():
                            year = parts[0][:4]
                            month = parts[0][4:6]
                            day = parts[1]
                            if month.isdigit() and day.isdigit():
                                return f"{year}-{month}-{day.zfill(2)}"

                    # 标准化常见格式
                    replacements = [
                        ('年', '-'), ('月', '-'), ('日', ''),
                        ('/', '-'), ('.', '-')
                    ]
                    for old, new in replacements:
                        date_str = date_str.replace(old, new)

                    # 验证最终的日期格式
                    if '-' in date_str:
                        try:
                            parts = date_str.split('-')
                            # 确保年月日都是有效数字
                            if len(parts) >= 2 and parts[0].isdigit() and len(parts[0]) == 4:
                                year = int(parts[0])
                                if len(parts) == 2 and parts[1].isdigit():
                                    # 只有年月
                                    month = int(parts[1])
                                    if 1 <= month <= 12:
                                        return f"{year:04d}-{month:02d}-01"
                                elif len(parts) >= 3 and parts[1].isdigit() and parts[2].isdigit():
                                    # 完整年月日
                                    month = int(parts[1])
                                    day = int(parts[2])
                                    if 1 <= month <= 12 and 1 <= day <= 31:
                                        return f"{year:04d}-{month:02d}-{day:02d}"
                        except Exception as e:

                            # 记录异常但不中断流程

                            logger.debug(f"[patent_db_import] Exception: {e}")
                    return None

                # 插入新专利
                cursor.execute(
                    """
                    INSERT INTO patents (
                        patent_number, patent_name, patent_type, application_date,
                        grant_date, legal_status, review_status, archive_location,
                        application_method, sequence_number, archive_number,
                        client_id, agency, contact_info, notes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        patent["patent_number"],
                        patent.get("patent_name"),
                        patent.get("patent_type"),
                        clean_date(patent.get("application_date")),
                        clean_date(patent.get("grant_date")),
                        patent.get("status"),
                        patent.get("review_status"),
                        patent.get("archive_location"),
                        patent.get("application_method"),
                        patent.get("sequence_number"),
                        patent.get("archive_number"),
                        client_id,
                        patent.get("agency"),
                        patent.get("contact"),
                        patent.get("notes")
                    )
                )
                imported_count += 1

            conn.commit()
            print(f"✅ 成功导入 {imported_count} 个专利，跳过 {skipped_count} 个重复专利")

            return True

        except Exception as e:
            print(f"❌ 导入专利数据失败: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def import_from_json(self, json_file: str):
        """从JSON文件导入数据"""
        if not os.path.exists(json_file):
            print(f"❌ 文件不存在: {json_file}")
            return False

        try:
            with open(json_file, encoding='utf-8') as f:
                data = json.load(f)

            # 创建表
            self.create_tables()

            # 导入客户
            print("\n开始导入客户数据...")
            client_map = self.import_clients(data["clients"])

            # 导入专利
            print("\n开始导入专利数据...")
            success = self.import_patents(data["patents"], client_map)

            if success:
                print("\n✅ 数据导入成功！")

                # 显示统计
                print("\n导入统计:")
                print(f"- 客户数: {len(client_map)}")
                print(f"- 专利数: {len(data['patents'])}")
                print(f"- 导入时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                # 保存导入日志
                log_data = {
                    "import_time": datetime.now().isoformat(),
                    "clients_count": len(client_map),
                    "patents_count": len(data["patents"]),
                    "json_file": json_file
                }

                log_file = f"patent_import_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(log_file, 'w', encoding='utf-8') as f:
                    json.dump(log_data, f, ensure_ascii=False, indent=2)

                print(f"- 导入日志: {log_file}")

            return success

        except Exception as e:
            print(f"❌ 导入失败: {str(e)}")
            return False

    def query_patent_by_number(self, patent_number: str):
        """根据专利号查询专利"""
        conn = self.get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT p.*, c.client_name
                FROM patents p
                LEFT JOIN patent_clients c ON p.client_id = c.id
                WHERE p.patent_number = %s
                """,
                (patent_number,)
            )
            result = cursor.fetchone()
            return dict(result) if result else None

        except Exception as e:
            print(f"❌ 查询失败: {str(e)}")
            return None
        finally:
            conn.close()

    def query_patents_by_client(self, client_name: str):
        """根据客户查询专利"""
        conn = self.get_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT p.*, c.client_name
                FROM patents p
                INNER JOIN patent_clients c ON p.client_id = c.id
                WHERE c.client_name ILIKE %s
                ORDER BY p.application_date DESC
                """,
                (f"%{client_name}%",)
            )
            results = cursor.fetchall()
            return [dict(row) for row in results]

        except Exception as e:
            print(f"❌ 查询失败: {str(e)}")
            return []
        finally:
            conn.close()

    def get_statistics(self):
        """获取统计信息"""
        conn = self.get_connection()
        if not conn:
            return {}

        try:
            cursor = conn.cursor()

            stats = {}

            # 客户统计
            cursor.execute("SELECT COUNT(*) FROM patent_clients")
            stats["total_clients"] = cursor.fetchone()[0]

            # 专利统计
            cursor.execute("SELECT COUNT(*) FROM patents")
            stats["total_patents"] = cursor.fetchone()[0]

            # 专利类型分布
            cursor.execute(
                """
                SELECT patent_type, COUNT(*) as count
                FROM patents
                WHERE patent_type IS NOT NULL
                GROUP BY patent_type
                ORDER BY count DESC
                """
            )
            stats["patent_types"] = dict(cursor.fetchall())

            # 法律状态分布
            cursor.execute(
                """
                SELECT legal_status, COUNT(*) as count
                FROM patents
                WHERE legal_status IS NOT NULL
                GROUP BY legal_status
                ORDER BY count DESC
                LIMIT 10
                """
            )
            stats["legal_status"] = dict(cursor.fetchall())

            # 年度申请趋势
            cursor.execute(
                """
                SELECT EXTRACT(YEAR FROM application_date) as year, COUNT(*) as count
                FROM patents
                WHERE application_date IS NOT NULL
                GROUP BY year
                ORDER BY year DESC
                """
            )
            stats["yearly_applications"] = dict(cursor.fetchall())

            return stats

        except Exception as e:
            print(f"❌ 获取统计失败: {str(e)}")
            return {}
        finally:
            conn.close()


def main():
    """主函数"""
    # 查找最新的JSON文件
    json_files = list(Path('.').glob('patent_data_extracted_*.json'))
    if not json_files:
        print("❌ 未找到解析的JSON文件")
        return

    latest_file = max(json_files, key=os.path.getctime)
    print(f"使用文件: {latest_file}")

    # 创建导入器并导入数据
    importer = PatentDBImporter()
    success = importer.import_from_json(str(latest_file))

    if success:
        # 测试查询
        print("\n" + "="*50)
        print("测试查询功能:")
        print("="*50)

        # 查询统计
        print("\n📊 统计信息:")
        stats = importer.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # 测试客户查询
        print("\n🔍 查询示例:")
        example_patents = importer.query_patents_by_client("")
        if example_patents:
            patent = example_patents[0]
            print(f"专利号: {patent['patent_number']}")
            print(f"名称: {patent['patent_name']}")
            print(f"客户: {patent['client_name']}")
            print(f"类型: {patent['patent_type']}")
            print(f"状态: {patent['legal_status']}")


if __name__ == "__main__":
    main()
