#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构专利数据库结构
Restructure Patent Database

将"案源人"和"客户"分开，重新组织数据
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
from pathlib import Path

class PatentDBRestructurer:
    """专利数据库重构器"""

    def __init__(self):
        # 检查PostgreSQL路径
        postgres_path = "/opt/homebrew/opt/postgresql@17/bin"
        if postgres_path not in os.environ.get("PATH", ""):
            os.environ["PATH"] = postgres_path + ":" + os.environ.get("PATH", "")

        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "patent_archive",
            "user": "xujian",
            "password": ""
        }

    def get_connection(self):
        """获取数据库连接"""
        try:
            conn = psycopg2.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                database=self.db_config["database"],
                user=self.db_config["user"]
            )
            return conn
        except Exception as e:
            print(f"❌ 数据库连接失败: {str(e)}")
            return None

    def create_new_tables(self):
        """创建新的表结构"""
        sql_statements = [
            # 案源人表（原来是patent_clients）
            """
            CREATE TABLE IF NOT EXISTS patent_agents (
                id SERIAL PRIMARY KEY,
                agent_name VARCHAR(100) NOT NULL UNIQUE,
                patent_count INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 客户表
            """
            CREATE TABLE IF NOT EXISTS patent_customers (
                id SERIAL PRIMARY KEY,
                customer_name VARCHAR(200) NOT NULL UNIQUE,
                patent_count INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 专利表
            """
            CREATE TABLE IF NOT EXISTS patents_new (
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
                agent_id INTEGER REFERENCES patent_agents(id),
                customer_id INTEGER REFERENCES patent_customers(id),
                agency VARCHAR(200),
                contact_info VARCHAR(500),
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,

            # 创建索引
            "CREATE INDEX IF NOT EXISTS idx_patents_new_agent_id ON patents_new(agent_id);",
            "CREATE INDEX IF NOT EXISTS idx_patents_new_customer_id ON patents_new(customer_id);",
            "CREATE INDEX IF NOT EXISTS idx_patents_new_number ON patents_new(patent_number);",
        ]

        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            print("正在创建新的表结构...")

            for sql in sql_statements:
                cursor.execute(sql)

            conn.commit()
            print("✅ 新表结构创建成功！")
            return True

        except Exception as e:
            print(f"❌ 创建表失败: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def migrate_data(self):
        """迁移数据"""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            # 1. 迁移案源人数据（从patent_agents，原patent_clients）
            print("\n迁移案源人数据...")
            cursor.execute("""
                INSERT INTO patent_agents (agent_name, patent_count)
                SELECT client_name, patent_count FROM patent_agents
                ON CONFLICT (agent_name) DO NOTHING
            """)

            # 2. 从专利名称中提取客户
            print("\n提取客户信息...")
            cursor.execute("""
                INSERT INTO patent_customers (customer_name, patent_count)
                SELECT
                    CASE
                        WHEN patent_name LIKE '山东%' THEN '山东地区客户'
                        WHEN patent_name LIKE '济宁%' THEN '济宁地区客户'
                        WHEN patent_name LIKE '济南%' THEN '济南地区客户'
                        WHEN patent_name LIKE '淄博%' THEN '淄博地区客户'
                        WHEN patent_name LIKE '滨州%' THEN '滨州地区客户'
                        WHEN patent_name LIKE '潍坊%' THEN '潍坊地区客户'
                        WHEN patent_name LIKE '青岛%' THEN '青岛地区客户'
                        WHEN patent_name LIKE '烟台%' THEN '烟台地区客户'
                        WHEN patent_name LIKE '威海%' THEN '威海地区客户'
                        ELSE '其他地区客户'
                    END as customer_name,
                    COUNT(*) as patent_count
                FROM patents
                GROUP BY customer_name
                ON CONFLICT (customer_name) DO UPDATE SET
                    patent_count = patent_customers.patent_count + EXCLUDED.patent_count
            """)

            # 3. 迁移专利数据
            print("\n迁移专利数据...")
            cursor.execute("""
                INSERT INTO patents_new (
                    patent_number, patent_name, patent_type, application_date,
                    grant_date, legal_status, review_status, archive_location,
                    application_method, sequence_number, archive_number,
                    agent_id, customer_id, agency, contact_info, notes
                )
                SELECT
                    p.patent_number,
                    p.patent_name,
                    p.patent_type,
                    p.application_date,
                    p.grant_date,
                    p.legal_status,
                    p.review_status,
                    p.archive_location,
                    p.application_method,
                    p.sequence_number,
                    p.archive_number,
                    a.id as agent_id,
                    CASE
                        WHEN p.patent_name LIKE '山东%' THEN
                            (SELECT id FROM patent_customers WHERE customer_name = '山东地区客户')
                        WHEN p.patent_name LIKE '济宁%' THEN
                            (SELECT id FROM patent_customers WHERE customer_name = '济宁地区客户')
                        WHEN p.patent_name LIKE '济南%' THEN
                            (SELECT id FROM patent_customers WHERE customer_name = '济南地区客户')
                        WHEN p.patent_name LIKE '淄博%' THEN
                            (SELECT id FROM patent_customers WHERE customer_name = '淄博地区客户')
                        WHEN p.patent_name LIKE '滨州%' THEN
                            (SELECT id FROM patent_customers WHERE customer_name = '滨州地区客户')
                        WHEN p.patent_name LIKE '潍坊%' THEN
                            (SELECT id FROM patent_customers WHERE customer_name = '潍坊地区客户')
                        WHEN p.patent_name LIKE '青岛%' THEN
                            (SELECT id FROM patent_customers WHERE customer_name = '青岛地区客户')
                        WHEN p.patent_name LIKE '烟台%' THEN
                            (SELECT id FROM patent_customers WHERE customer_name = '烟台地区客户')
                        WHEN p.patent_name LIKE '威海%' THEN
                            (SELECT id FROM patent_customers WHERE customer_name = '威海地区客户')
                        ELSE
                            (SELECT id FROM patent_customers WHERE customer_name = '其他地区客户')
                    END as customer_id,
                    p.agency,
                    p.contact_info,
                    p.notes
                FROM patents p
                LEFT JOIN patent_agents a ON p.agent_id = a.id
            """)

            conn.commit()
            print("✅ 数据迁移成功！")

            # 显示统计
            print("\n数据统计:")
            cursor.execute("SELECT COUNT(*) FROM patent_agents")
            print(f"- 案源人数: {cursor.fetchone()[0]}")

            cursor.execute("SELECT COUNT(*) FROM patent_customers")
            print(f"- 客户数: {cursor.fetchone()[0]}")

            cursor.execute("SELECT COUNT(*) FROM patents_new")
            print(f"- 专利数: {cursor.fetchone()[0]}")

            # 显示客户分布
            print("\n客户分布:")
            cursor.execute("""
                SELECT customer_name, patent_count
                FROM patent_customers
                ORDER BY patent_count DESC
            """)
            for row in cursor.fetchall():
                print(f"  - {row[0]}: {row[1]}件专利")

            return True

        except Exception as e:
            print(f"❌ 数据迁移失败: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def update_table_names(self):
        """更新表名"""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            # 备份旧表
            print("\n备份旧表...")
            cursor.execute("ALTER TABLE patents RENAME TO patents_backup")

            # 重命名新表
            print("更新表名...")
            cursor.execute("ALTER TABLE patents_new RENAME TO patents")

            conn.commit()
            print("✅ 表名更新成功！")

            return True

        except Exception as e:
            print(f"❌ 更新表名失败: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def run_restructure(self):
        """执行重构"""
        print("开始重构专利数据库结构...")
        print("="*50)

        # 1. 创建新表
        if not self.create_new_tables():
            return False

        # 2. 迁移数据
        if not self.migrate_data():
            return False

        # 3. 更新表名
        if not self.update_table_names():
            return False

        print("\n✅ 数据库重构完成！")
        print("="*50)
        print("\n新的表结构:")
        print("- patent_agents: 案源人表（原patent_clients）")
        print("- patent_customers: 客户表（新增）")
        print("- patents: 专利表（已更新）")
        print("- patents_backup: 备份的旧专利表")

        return True


def main():
    """主函数"""
    restr = PatentDBRestructurer()
    restr.run_restructure()


if __name__ == "__main__":
    main()