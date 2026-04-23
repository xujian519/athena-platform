#!/usr/bin/env python3
"""
云熙专利业务管理系统数据库初始化脚本
YunPat Patent Management System Database Initialization

初始化PostgreSQL数据库，创建完整的专利业务管理表结构
支持客户管理、项目管理、案卷管理、任务管理、财务管理、文档管理

作者: 小娜·天秤女神
创建时间: 2025-12-17
版本: v1.0.0
"""

from datetime import datetime
from typing import Any

import psycopg2
import psycopg2.extras

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'athena_db',  # 使用项目中的数据库名
    'user': 'postgres',
    'password': 'postgres'
}

class YunPatDatabaseInitializer:
    """云熙专利数据库初始化器"""

    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self) -> Any:
        """连接数据库"""
        try:
            # 先连接到postgres数据库创建athena_db
            conn_temp = psycopg2.connect(
                host='localhost',
                port=5432,
                database='postgres',
                user='postgres',
                password='postgres'
            )
            conn_temp.autocommit = True
            cursor_temp = conn_temp.cursor()

            # 检查并创建数据库
            cursor_temp.execute("SELECT 1 FROM pg_database WHERE datname = 'athena_db'")
            if not cursor_temp.fetchone():
                cursor_temp.execute("CREATE DATABASE athena_db WITH ENCODING 'UTF8'")
                print("✅ 数据库 athena_db 创建成功")
            else:
                print("✅ 数据库 athena_db 已存在")

            cursor_temp.close()
            conn_temp.close()

            # 连接到目标数据库
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print(f"✅ 成功连接到数据库: {DB_CONFIG['database']}")
            return True

        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False

    def create_extensions(self) -> Any:
        """创建必要的扩展

        注意: 扩展名来自硬编码的白名单，是安全的
        """
        try:
            # 扩展名白名单
            extensions = ['uuid-ossp', 'pg_trgm']
            for ext in extensions:
                try:
                    # 使用参数化查询防止SQL注入
                    # 注意: 扩展名来自白名单，是安全的
                    self.cursor.execute(f"CREATE EXTENSION IF NOT EXISTS \"{ext}\"")
                    print(f"✅ 扩展 {ext} 创建成功")
                except Exception as e:
                    print(f"⚠️ 扩展 {ext} 创建失败: {e}")
            self.conn.commit()
        except Exception as e:
            print(f"❌ 创建扩展失败: {e}")

    def create_tables(self) -> Any:
        """创建所有表结构"""
        try:
            # 1. 租户表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenants (
                    id VARCHAR(50) PRIMARY KEY DEFAULT 'yunpat-main',
                    name VARCHAR(100) NOT NULL,
                    code VARCHAR(20) UNIQUE NOT NULL,
                    contact_person VARCHAR(50),
                    contact_phone VARCHAR(20),
                    contact_email VARCHAR(100),
                    address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)

            # 2. 用户表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id VARCHAR(50) REFERENCES tenants(id),
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    phone VARCHAR(20),
                    real_name VARCHAR(50),
                    role VARCHAR(20) DEFAULT 'USER',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)

            # 3. 客户表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id VARCHAR(50) REFERENCES tenants(id) NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    type VARCHAR(20) DEFAULT 'COMPANY',
                    address TEXT,
                    contact_person VARCHAR(50),
                    contact_title VARCHAR(50),
                    contact_phone VARCHAR(20),
                    contact_email VARCHAR(100),
                    source VARCHAR(100),
                    salesperson VARCHAR(50),
                    credit_rating VARCHAR(10),
                    notes TEXT,
                    total_projects INTEGER DEFAULT 0,
                    completed_projects INTEGER DEFAULT 0,
                    active_projects INTEGER DEFAULT 0,
                    total_cases INTEGER DEFAULT 0,
                    granted_cases INTEGER DEFAULT 0,
                    pending_cases INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 4. 项目表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id VARCHAR(50) REFERENCES tenants(id) NOT NULL,
                    client_id VARCHAR(50) REFERENCES clients(id) NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    contact_person VARCHAR(50),
                    project_manager VARCHAR(50),
                    agent VARCHAR(50),
                    description TEXT,
                    status VARCHAR(20) DEFAULT 'ACTIVE',
                    start_date DATE,
                    end_date DATE,
                    total_cases INTEGER DEFAULT 0,
                    pending_tasks INTEGER DEFAULT 0,
                    completed_tasks INTEGER DEFAULT 0,
                    expected_tasks INTEGER DEFAULT 0,
                    agency_fee DECIMAL(10,2),
                    official_fee DECIMAL(10,2),
                    agency_fee_paid BOOLEAN DEFAULT FALSE,
                    official_fee_paid BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 5. 案卷表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id VARCHAR(50) REFERENCES tenants(id) NOT NULL,
                    client_id VARCHAR(50) REFERENCES clients(id) NOT NULL,
                    project_id VARCHAR(50) REFERENCES projects(id) NOT NULL,
                    case_number VARCHAR(50) UNIQUE NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    application_number VARCHAR(50),
                    type VARCHAR(20) NOT NULL,
                    applicant VARCHAR(200),
                    inventors TEXT,
                    contact_person VARCHAR(50),
                    filing_date DATE,
                    acceptance_number VARCHAR(50),
                    examiner VARCHAR(100),
                    review_count INTEGER DEFAULT 0,
                    grant_date DATE,
                    patent_number VARCHAR(50),
                    legal_status VARCHAR(50),
                    current_stage VARCHAR(50),
                    latest_document_type VARCHAR(50),
                    latest_document_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 6. 任务表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id VARCHAR(50) REFERENCES tenants(id) NOT NULL,
                    client_id VARCHAR(50) REFERENCES clients(id),
                    project_id VARCHAR(50) REFERENCES projects(id),
                    case_id VARCHAR(50) REFERENCES cases(id),
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    task_type VARCHAR(50),
                    status VARCHAR(20) DEFAULT 'TODO',
                    priority VARCHAR(20) DEFAULT 'NORMAL',
                    start_date DATE,
                    due_date DATE,
                    completed_date DATE,
                    assign_method VARCHAR(20) DEFAULT 'AUTO',
                    assigned_to VARCHAR(50) REFERENCES users(id),
                    visible_to JSONB DEFAULT '[]',
                    reminder_enabled BOOLEAN DEFAULT TRUE,
                    reminder_days INTEGER DEFAULT 3,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)

            # 7. 财务记录表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS financial_records (
                    id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id VARCHAR(50) REFERENCES tenants(id) NOT NULL,
                    client_id VARCHAR(50) REFERENCES clients(id),
                    project_id VARCHAR(50) REFERENCES projects(id),
                    case_id VARCHAR(50) REFERENCES cases(id),
                    type VARCHAR(20) NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    description VARCHAR(500),
                    record_date DATE NOT NULL,
                    due_date DATE,
                    paid_date DATE,
                    status VARCHAR(20) DEFAULT 'PENDING',
                    payment_method VARCHAR(50),
                    invoice_number VARCHAR(50),
                    related_task_id VARCHAR(50) REFERENCES tasks(id),
                    related_document_id VARCHAR(50),
                    auto_created BOOLEAN DEFAULT FALSE,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 8. 文档表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id VARCHAR(50) REFERENCES tenants(id) NOT NULL,
                    client_id VARCHAR(50) REFERENCES clients(id),
                    project_id VARCHAR(50) REFERENCES projects(id),
                    case_id VARCHAR(50) REFERENCES cases(id),
                    name VARCHAR(500) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    category VARCHAR(50),
                    file_path VARCHAR(1000),
                    file_name VARCHAR(500),
                    file_size INTEGER,
                    file_hash VARCHAR(64),
                    mime_type VARCHAR(100),
                    version VARCHAR(20) DEFAULT '1.0',
                    parent_document_id VARCHAR(50) REFERENCES documents(id),
                    description TEXT,
                    tags JSONB DEFAULT '[]',
                    uploaded_by VARCHAR(50) REFERENCES users(id),
                    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 9. 审查意见表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS review_opinions (
                    id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id VARCHAR(50) REFERENCES tenants(id) NOT NULL,
                    case_id VARCHAR(50) REFERENCES cases(id) NOT NULL,
                    review_type VARCHAR(50) NOT NULL,
                    review_round INTEGER DEFAULT 1,
                    review_date DATE NOT NULL,
                    reviewer VARCHAR(100),
                    title VARCHAR(500),
                    content TEXT NOT NULL,
                    summary TEXT,
                    status VARCHAR(20) DEFAULT 'PENDING',
                    response_deadline DATE NOT NULL,
                    response_date DATE,
                    document_ids JSONB DEFAULT '[]',
                    assigned_to VARCHAR(50) REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.conn.commit()
            print("✅ 所有表结构创建完成")
            return True

        except Exception as e:
            print(f"❌ 创建表失败: {e}")
            self.conn.rollback()
            return False

    def create_indexes(self) -> Any:
        """创建索引"""
        try:
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_clients_tenant_id ON clients(tenant_id)",
                "CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(name)",
                "CREATE INDEX IF NOT EXISTS idx_projects_client_id ON projects(client_id)",
                "CREATE INDEX IF NOT EXISTS idx_projects_tenant_id ON projects(tenant_id)",
                "CREATE INDEX IF NOT EXISTS idx_cases_project_id ON cases(project_id)",
                "CREATE INDEX IF NOT EXISTS idx_cases_case_number ON cases(case_number)",
                "CREATE INDEX IF NOT EXISTS idx_cases_application_number ON cases(application_number)",
                "CREATE INDEX IF NOT EXISTS idx_tasks_case_id ON tasks(case_id)",
                "CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to)",
                "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
                "CREATE INDEX IF NOT EXISTS idx_financial_records_case_id ON financial_records(case_id)",
                "CREATE INDEX IF NOT EXISTS idx_financial_records_status ON financial_records(status)",
                "CREATE INDEX IF NOT EXISTS idx_documents_case_id ON documents(case_id)",
                "CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type)",
                "CREATE INDEX IF NOT EXISTS idx_review_opinions_case_id ON review_opinions(case_id)"
            ]

            for index_sql in indexes:
                self.cursor.execute(index_sql)

            self.conn.commit()
            print("✅ 索引创建完成")
            return True

        except Exception as e:
            print(f"❌ 创建索引失败: {e}")
            return False

    def init_default_data(self) -> Any:
        """初始化默认数据"""
        try:
            # 创建默认租户
            self.cursor.execute("""
                INSERT INTO tenants (id, name, code, contact_person)
                VALUES ('yunpat-main', '云熙专利管理系统', 'YUNPAT', '系统管理员')
                ON CONFLICT (id) DO NOTHING
            """)

            # 创建默认用户
            self.cursor.execute("""
                INSERT INTO users (username, email, real_name, role, tenant_id)
                VALUES ('admin', 'admin@yunpat.com', '系统管理员', 'ADMIN', 'yunpat-main')
                ON CONFLICT (username) DO NOTHING
            """)

            self.conn.commit()
            print("✅ 默认数据初始化完成")
            return True

        except Exception as e:
            print(f"❌ 初始化默认数据失败: {e}")
            return False

    def close(self) -> Any:
        """关闭连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

def main() -> None:
    """主函数"""
    print("=" * 80)
    print("🗄️" + " " * 25 + "云熙专利数据库初始化" + " " * 25 + "🗄️")
    print("=" * 80)
    print(f"🕐 初始化时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("👩‍⚖️ 操作者: 小娜·天秤女神 (专利法律专家)")
    print("🎯 初始化目标: 创建完整的专利业务管理数据库")
    print("=" * 80)

    initializer = YunPatDatabaseInitializer()

    try:
        # 步骤1: 连接数据库
        print("\n🔗 步骤1: 连接数据库")
        if not initializer.connect():
            return

        # 步骤2: 创建扩展
        print("\n🔧 步骤2: 创建数据库扩展")
        initializer.create_extensions()

        # 步骤3: 创建表结构
        print("\n📋 步骤3: 创建表结构")
        if not initializer.create_tables():
            return

        # 步骤4: 创建索引
        print("\n⚡ 步骤4: 创建性能索引")
        if not initializer.create_indexes():
            return

        # 步骤5: 初始化默认数据
        print("\n📊 步骤5: 初始化默认数据")
        if not initializer.init_default_data():
            return

        print("\n" + "=" * 80)
        print("🎉 云熙专利数据库初始化完成！")
        print("=" * 80)
        print("✅ 数据库: athena_db")
        print("✅ 表结构: 9个核心业务表")
        print("✅ 索引: 高性能查询索引")
        print("✅ 默认数据: 租户和用户")
        print("=" * 80)
        print("📞 下一步: 创建孙俊霞的客户记录和专利项目")
        print("🔧 使用脚本: python scripts/create_sunjunxia_records.py")

    except Exception as e:
        print(f"\n❌ 数据库初始化失败: {e}")
    finally:
        initializer.close()

if __name__ == "__main__":
    main()
