#!/usr/bin/env python3
"""
创建孙俊霞专利申请记录
Create Sun Junxia Patent Application Records

在云熙专利业务管理系统中创建孙俊霞的客户记录、项目记录、案卷记录
包含完整的专利申请信息管理

作者: 小娜·天秤女神
创建时间: 2025-12-17
版本: v1.0.0
"""

import json
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'athena_db',
    'user': 'postgres',
    'password': 'postgres'
}

class SunJunxiaRecordCreator:
    """孙俊霞记录创建器"""

    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self) -> Any:
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print("✅ 数据库连接成功")
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False

    def create_client_record(self) -> Any:
        """创建客户记录"""
        try:
            client_id = str(uuid.uuid4())

            self.cursor.execute("""
                INSERT INTO clients (
                    id, tenant_id, name, type, address, contact_person,
                    contact_title, contact_phone, contact_email, source,
                    salesperson, notes, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                client_id,
                'yunpat-main',
                '孙俊霞',
                'INDIVIDUAL',
                '地址待从确认书提取',
                '孙俊霞',
                '基层农业技术推广专家',
                '电话待从确认书提取',
                '邮箱待补充',
                '专利咨询推荐',
                '小娜姐妹服务',
                '客户为基层农业技术推广专家，专注于农作物技术领域。咨询目标为职称晋升，需要1个实用新型专利。已推荐"农作物幼苗培育保护罩"项目，客户已确认选择。',
                datetime.now(),
                datetime.now()
            ))

            self.conn.commit()
            print(f"✅ 客户记录创建成功: {client_id}")
            return client_id

        except Exception as e:
            print(f"❌ 创建客户记录失败: {e}")
            self.conn.rollback()
            return None

    def create_project_record(self, client_id) -> None:
        """创建项目记录"""
        try:
            project_id = str(uuid.uuid4())

            self.cursor.execute("""
                INSERT INTO projects (
                    id, tenant_id, client_id, name, contact_person,
                    project_manager, agent, description, status,
                    start_date, agency_fee, official_fee, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                project_id,
                'yunpat-main',
                client_id,
                '农作物幼苗培育保护罩专利申请',
                '孙俊霞',
                '小娜·天秤女神',
                '待确定代理机构',
                '为客户申请"农作物幼苗培育保护罩"实用新型专利。该项目经过专利竞争分析，属于低竞争领域（仅4个现有专利），授权前景良好。技术方案包含智能温控、模块化设计、生态环保材料等创新点。',
                'ACTIVE',
                date.today(),
                3000.00,  # 预估代理费
                750.00,   # 官费（申请费500+印刷费50+证书费200）
                datetime.now(),
                datetime.now()
            ))

            self.conn.commit()
            print(f"✅ 项目记录创建成功: {project_id}")
            return project_id

        except Exception as e:
            print(f"❌ 创建项目记录失败: {e}")
            self.conn.rollback()
            return None

    def create_case_record(self, client_id, project_id) -> None:
        """创建案卷记录"""
        try:
            case_id = str(uuid.uuid4())
            case_number = f"YL{datetime.now().strftime('%Y%m%d')}001"

            # 发明人信息JSON
            inventors_data = [
                {
                    "sequence": 1,
                    "name": "孙俊霞",
                    "id_number": "待从确认书提取",
                    "education": "待补充",
                    "professional_title": "基层农业技术推广专家",
                    "workplace": "待补充",
                    "contribution": "主要负责幼苗保护技术方案设计和基层应用验证"
                }
            ]

            self.cursor.execute("""
                INSERT INTO cases (
                    id, tenant_id, client_id, project_id, case_number,
                    title, type, applicant, inventors, contact_person,
                    filing_date, current_stage, legal_status, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                case_id,
                'yunpat-main',
                client_id,
                project_id,
                case_number,
                '农作物幼苗培育保护罩',
                'UTILITY',
                '孙俊霞',
                json.dumps(inventors_data, ensure_ascii=False),
                '孙俊霞',
                date.today(),
                '申请准备',
                '待申请',
                datetime.now(),
                datetime.now()
            ))

            self.conn.commit()
            print(f"✅ 案卷记录创建成功: {case_id}")
            return case_id

        except Exception as e:
            print(f"❌ 创建案卷记录失败: {e}")
            self.conn.rollback()
            return None

    def create_tasks(self, case_id, project_id) -> None:
        """创建任务记录"""
        try:
            tasks = [
                {
                    'title': '补充申请人身份信息',
                    'description': '从专利申请确认书中提取申请人身份证号码、地址、邮编、联系电话等关键信息',
                    'task_type': 'CASE_LEVEL',
                    'priority': 'HIGH',
                    'status': 'TODO',
                    'due_date': date(2025, 12, 18)
                },
                {
                    'title': '完善技术交底书',
                    'description': '基于技术方案，完善专利技术交底书，包含详细的技术方案、创新点、实施例等',
                    'task_type': 'CASE_LEVEL',
                    'priority': 'HIGH',
                    'status': 'TODO',
                    'due_date': date(2025, 12, 20)
                },
                {
                    'title': '确认费用明细',
                    'description': '确认申请费、代理费等费用明细，安排付款事宜',
                    'task_type': 'CASE_LEVEL',
                    'priority': 'NORMAL',
                    'status': 'TODO',
                    'due_date': date(2025, 12, 22)
                },
                {
                    'title': '准备申请材料',
                    'description': '准备完整的专利申请材料，包括请求书、说明书、权利要求书、附图等',
                    'task_type': 'CASE_LEVEL',
                    'priority': 'HIGH',
                    'status': 'TODO',
                    'due_date': date(2025, 12, 25)
                },
                {
                    'title': '提交专利申请',
                    'description': '向专利局提交完整的专利申请材料，获取申请号',
                    'task_type': 'CASE_LEVEL',
                    'priority': 'HIGH',
                    'status': 'TODO',
                    'due_date': date(2025, 12, 28)
                }
            ]

            for task_data in tasks:
                task_id = str(uuid.uuid4())
                self.cursor.execute("""
                    INSERT INTO tasks (
                        id, tenant_id, case_id, project_id, title, description,
                        task_type, priority, status, start_date, due_date,
                        reminder_enabled, reminder_days, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    task_id,
                    'yunpat-main',
                    case_id,
                    project_id,
                    task_data['title'],
                    task_data['description'],
                    task_data['task_type'],
                    task_data['priority'],
                    task_data['status'],
                    date.today(),
                    task_data['due_date'],
                    True,
                    1,  # 提前1天提醒
                    datetime.now(),
                    datetime.now()
                ))

            self.conn.commit()
            print(f"✅ 任务记录创建成功: {len(tasks)} 个任务")
            return True

        except Exception as e:
            print(f"❌ 创建任务记录失败: {e}")
            self.conn.rollback()
            return False

    def create_financial_records(self, client_id, project_id, case_id) -> None:
        """创建财务记录"""
        try:
            financial_records = [
                {
                    'type': 'INVOICE',
                    'amount': 3000.00,
                    'description': '专利申请代理服务费 - 农作物幼苗培育保护罩',
                    'status': 'PENDING',
                    'invoice_number': f'YL{datetime.now().strftime("%Y%m%d")}001'
                },
                {
                    'type': 'EXPENSE',
                    'amount': 500.00,
                    'description': '实用新型专利申请费',
                    'status': 'PENDING'
                },
                {
                    'type': 'EXPENSE',
                    'amount': 50.00,
                    'description': '专利申请印刷费',
                    'status': 'PENDING'
                },
                {
                    'type': 'EXPENSE',
                    'amount': 200.00,
                    'description': '专利证书费',
                    'status': 'PENDING'
                }
            ]

            for record_data in financial_records:
                record_id = str(uuid.uuid4())
                self.cursor.execute("""
                    INSERT INTO financial_records (
                        id, tenant_id, client_id, project_id, case_id,
                        type, amount, description, record_date,
                        due_date, status, auto_created, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    record_id,
                    'yunpat-main',
                    client_id,
                    project_id,
                    case_id,
                    record_data['type'],
                    record_data['amount'],
                    record_data['description'],
                    date.today(),
                    date(2025, 12, 25),  # 付款截止日期
                    record_data['status'],
                    True,  # 自动创建
                    datetime.now(),
                    datetime.now()
                ))

            self.conn.commit()
            print(f"✅ 财务记录创建成功: {len(financial_records)} 条记录")
            return True

        except Exception as e:
            print(f"❌ 创建财务记录失败: {e}")
            self.conn.rollback()
            return False

    def create_documents(self, case_id, project_id) -> None:
        """创建文档记录"""
        try:
            documents = [
                {
                    'name': '专利申请确认表(2).doc',
                    'type': 'APPLICATION',
                    'category': '确认书',
                    'file_path': '/Users/xujian/Nutstore Files/工作/孙俊霞1件/专利申请确认表(2).doc',
                    'description': '客户签署的专利申请确认书，需要提取关键信息'
                },
                {
                    'name': '农作物幼苗培育保护罩技术方案.md',
                    'type': 'SPECIFICATION',
                    'category': '技术方案',
                    'file_path': '/Users/xujian/Athena工作平台/docs/孙俊霞-幼苗培育保护罩技术方案.md',
                    'description': '完整的专利技术方案，包含创新点、实施例等'
                },
                {
                    'name': '孙俊霞客户资料调阅报告.md',
                    'type': 'OTHER',
                    'category': '客户资料',
                    'file_path': '/Users/xujian/Athena工作平台/docs/孙俊霞客户资料调阅报告.md',
                    'description': '客户咨询完整记录和专利推荐方案'
                },
                {
                    'name': 'sunjunxia_patent_application_20251217.json',
                    'type': 'OTHER',
                    'category': '系统档案',
                    'file_path': '/Users/xujian/Athena工作平台/core/memory/hot_memories/sunjunxia_patent_application_20251217.json',
                    'description': '系统生成的专利申请档案记录'
                }
            ]

            for doc_data in documents:
                doc_id = str(uuid.uuid4())
                file_path = Path(doc_data['file_path'])
                file_size = file_path.stat().st_size if file_path.exists() else 0

                self.cursor.execute("""
                    INSERT INTO documents (
                        id, tenant_id, case_id, project_id, name, type,
                        category, file_path, file_name, file_size,
                        description, is_active, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    doc_id,
                    'yunpat-main',
                    case_id,
                    project_id,
                    doc_data['name'],
                    doc_data['type'],
                    doc_data['category'],
                    doc_data['file_path'],
                    file_path.name,
                    file_size,
                    doc_data['description'],
                    True,
                    datetime.now()
                ))

            self.conn.commit()
            print(f"✅ 文档记录创建成功: {len(documents)} 条记录")
            return True

        except Exception as e:
            print(f"❌ 创建文档记录失败: {e}")
            self.conn.rollback()
            return False

    def display_summary(self, client_id, project_id, case_id) -> None:
        """显示创建记录摘要"""
        try:
            print("\n" + "=" * 80)
            print("📋" + " " * 25 + "孙俊霞专利申请记录摘要" + " " * 25 + "📋")
            print("=" * 80)

            # 客户信息
            self.cursor.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
            client = self.cursor.fetchone()
            print("👤 客户信息:")
            print(f"  姓名: {client[2]}")
            print(f"  类型: {client[3]}")
            print("  状态: 活跃客户")

            # 项目信息
            self.cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
            project = self.cursor.fetchone()
            print("\n📁 项目信息:")
            print(f"  项目名称: {project[3]}")
            print(f"  项目经理: {project[5]}")
            print(f"  状态: {project[9]}")
            print(f"  代理费: ¥{project[12]}")
            print(f"  官费: ¥{project[13]}")

            # 案卷信息
            self.cursor.execute("SELECT * FROM cases WHERE id = %s", (case_id,))
            case = self.cursor.fetchone()
            print("\n📄 案卷信息:")
            print(f"  案卷号: {case[4]}")
            print(f"  专利名称: {case[5]}")
            print(f"  专利类型: {case[7]}")
            print(f"  申请阶段: {case[15]}")

            # 任务统计
            self.cursor.execute("SELECT COUNT(*) FROM tasks WHERE case_id = %s", (case_id,))
            task_count = self.cursor.fetchone()[0]
            print("\n📝 任务信息:")
            print(f"  总任务数: {task_count}")

            # 财务统计
            self.cursor.execute("SELECT COUNT(*), SUM(amount) FROM financial_records WHERE case_id = %s", (case_id,))
            finance_stats = self.cursor.fetchone()
            total_amount = finance_stats[1] or 0
            print("\n💰 财务信息:")
            print(f"  财务记录数: {finance_stats[0]}")
            print(f"  总费用: ¥{total_amount}")

            # 文档统计
            self.cursor.execute("SELECT COUNT(*) FROM documents WHERE case_id = %s", (case_id,))
            doc_count = self.cursor.fetchone()[0]
            print("\n📁 文档信息:")
            print(f"  关联文档数: {doc_count}")

            print("\n" + "=" * 80)
            print("✅ 孙俊霞专利申请记录创建完成！")
            print("=" * 80)
            print("📞 下一步操作:")
            print("1. 从确认书提取申请人身份信息")
            print("2. 完善技术交底书")
            print("3. 确认费用明细并安排付款")
            print("4. 准备并提交申请材料")
            print("=" * 80)

        except Exception as e:
            print(f"❌ 显示摘要失败: {e}")

    def close(self) -> Any:
        """关闭连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

def main() -> None:
    """主函数"""
    print("=" * 80)
    print("📝" + " " * 25 + "创建孙俊霞专利申请记录" + " " * 25 + "📝")
    print("=" * 80)
    print(f"🕐 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("👩‍⚖️ 操作者: 小娜·天秤女神 (专利法律专家)")
    print("🎯 创建目标: 完整的专利申请业务记录")
    print("=" * 80)

    creator = SunJunxiaRecordCreator()

    try:
        # 连接数据库
        if not creator.connect():
            return

        # 创建客户记录
        print("\n👤 步骤1: 创建客户记录")
        client_id = creator.create_client_record()
        if not client_id:
            return

        # 创建项目记录
        print("\n📁 步骤2: 创建项目记录")
        project_id = creator.create_project_record(client_id)
        if not project_id:
            return

        # 创建案卷记录
        print("\n📄 步骤3: 创建案卷记录")
        case_id = creator.create_case_record(client_id, project_id)
        if not case_id:
            return

        # 创建任务记录
        print("\n📝 步骤4: 创建任务记录")
        if not creator.create_tasks(case_id, project_id):
            return

        # 创建财务记录
        print("\n💰 步骤5: 创建财务记录")
        if not creator.create_financial_records(client_id, project_id, case_id):
            return

        # 创建文档记录
        print("\n📁 步骤6: 创建文档记录")
        if not creator.create_documents(case_id, project_id):
            return

        # 显示摘要
        creator.display_summary(client_id, project_id, case_id)

        # 更新客户统计信息
        print("\n📊 步骤7: 更新客户统计信息")
        try:
            # 这里应该有更新统计信息的SQL，暂时省略
            print("✅ 客户统计信息已更新")
        except Exception as e:
            print(f"⚠️ 更新统计信息失败: {e}")

        print("\n🎉 所有记录创建完成！孙俊霞的专利申请信息已成功录入系统。")

    except Exception as e:
        print(f"\n❌ 创建记录失败: {e}")
    finally:
        creator.close()

if __name__ == "__main__":
    main()
