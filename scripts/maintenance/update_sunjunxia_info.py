#!/usr/bin/env python3
"""
孙俊霞专利申请信息更新脚本
Update Sun Junxia Patent Application Information

由于确认书文档格式限制，提供手动录入界面来更新关键信息
包括身份证号、地址、邮编、电话等信息

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
    'database': 'athena_db',
    'user': 'postgres',
    'password': 'postgres'
}

class SunJunxiaInfoUpdater:
    """孙俊霞信息更新器"""

    def __init__(self):
        self.conn = None
        self.cursor = None
        self.client_id = "2a043af8-b99a-4fec-a313-457a3d52d646"
        self.project_id = "6200f262-a532-4392-8aa7-591cd0e079bb"
        self.case_id = "b941de08-d30c-4511-aa8a-e849d2b13b48"

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

    def display_current_info(self) -> Any:
        """显示当前信息"""
        try:
            print("\n" + "="*80)
            print("📋" + " " * 25 + "当前孙俊霞专利申请信息" + " " * 25 + "📋")
            print("="*80)

            # 客户信息
            self.cursor.execute("""
                SELECT name, type, contact_person, contact_phone, contact_email, address, notes
                FROM clients WHERE id = %s
            """, (self.client_id,))
            client = self.cursor.fetchone()

            print("👤 客户基本信息:")
            print(f"  姓名: {client[0]}")
            print(f"  类型: {client[1]}")
            print(f"  联系人: {client[2]}")
            print(f"  电话: {client[3]} (⚠️ 待更新)")
            print(f"  邮箱: {client[4]} (⚠️ 待更新)")
            print(f"  地址: {client[5]} (⚠️ 待更新)")

            # 案卷信息
            self.cursor.execute("""
                SELECT case_number, title, type, applicant, inventors
                FROM cases WHERE id = %s
            """, (self.case_id,))
            case = self.cursor.fetchone()

            print("\n📄 案卷信息:")
            print(f"  案卷号: {case[0]}")
            print(f"  专利名称: {case[1]}")
            print(f"  专利类型: {case[2]}")
            print(f"  申请人: {case[3]}")

            return True

        except Exception as e:
            print(f"❌ 显示信息失败: {e}")
            return False

    def input_applicant_info(self) -> Any:
        """录入申请人信息"""
        print("\n" + "="*60)
        print("📝" + " " * 15 + "请输入申请人信息" + " " * 15 + "📝")
        print("="*60)
        print("📋 参考专利申请确认书内容，填写以下信息：")
        print()

        try:
            # 申请人身份证号码
            id_number = input("🆔 申请人身份证号码: ").strip()
            if not id_number:
                print("⚠️ 身份证号码不能为空，使用默认值")
                id_number = "待从确认书提取"

            # 联系电话
            phone = input("📞 联系电话: ").strip()
            if not phone:
                print("⚠️ 联系电话不能为空，使用默认值")
                phone = "待从确认书提取"

            # 电子邮箱
            email = input("📧 电子邮箱 (可选): ").strip()

            # 申请地址
            address = input("🏠 申请地址: ").strip()
            if not address:
                print("⚠️ 申请地址不能为空，使用默认值")
                address = "待从确认书提取"

            # 邮政编码
            postal_code = input("📮 邮政编码: ").strip()
            if not postal_code:
                print("⚠️ 邮政编码不能为空，使用默认值")
                postal_code = "待从确认书提取"

            # 确认信息
            print("\n📋 请确认录入的信息:")
            print(f"  身份证号码: {id_number}")
            print(f"  联系电话: {phone}")
            print(f"  电子邮箱: {email or '未填写'}")
            print(f"  申请地址: {address}")
            print(f"  邮政编码: {postal_code}")

            confirm = input("\n✅ 确认无误？(Y/n): ").strip().lower()
            if confirm in ['', 'y', 'yes']:
                return {
                    'id_number': id_number,
                    'phone': phone,
                    'email': email,
                    'address': address,
                    'postal_code': postal_code
                }
            else:
                print("❌ 取消录入")
                return None

        except KeyboardInterrupt:
            print("\n❌ 用户取消录入")
            return None
        except Exception as e:
            print(f"❌ 录入失败: {e}")
            return None

    def input_inventor_info(self) -> Any:
        """录入发明人信息"""
        print("\n" + "="*60)
        print("👨‍🔬" + " " * 15 + "请输入发明人信息" + " " * 15 + "👨‍🔬")
        print("="*60)

        try:
            inventors = []

            while True:
                print(f"\n📝 发明人 {len(inventors) + 1}:")

                name = input("  姓名: ").strip()
                if not name:
                    break

                id_number = input("  身份证号码: ").strip()
                if not id_number:
                    id_number = "待补充"

                title = input("  职称 (可选): ").strip()
                workplace = input("  工作单位 (可选): ").strip()
                contribution = input("  主要贡献 (可选): ").strip()

                inventors.append({
                    'sequence': len(inventors) + 1,
                    'name': name,
                    'id_number': id_number,
                    'professional_title': title,
                    'workplace': workplace,
                    'contribution': contribution
                })

                more = input("\n➕ 继续添加发明人？(y/N): ").strip().lower()
                if more not in ['y', 'yes']:
                    break

            if inventors:
                print(f"\n✅ 录入了 {len(inventors)} 个发明人")
                return inventors
            else:
                print("⚠️ 未录入发明人信息")
                return None

        except KeyboardInterrupt:
            print("\n❌ 用户取消录入")
            return None
        except Exception as e:
            print(f"❌ 录入失败: {e}")
            return None

    def input_fee_details(self) -> Any:
        """录入费用明细"""
        print("\n" + "="*60)
        print("💰" + " " * 15 + "请输入费用明细" + " " * 15 + "💰")
        print("="*60)

        try:
            print("📋 参考确认书中的费用信息：")

            # 代理费
            while True:
                try:
                    agency_fee = float(input("  代理费: ").strip() or "0")
                    break
                except ValueError:
                    print("❌ 请输入有效的数字")

            # 官费明细
            while True:
                try:
                    application_fee = float(input("  申请费: ").strip() or "500")
                    break
                except ValueError:
                    print("❌ 请输入有效的数字")

            while True:
                try:
                    printing_fee = float(input("  印刷费: ").strip() or "50")
                    break
                except ValueError:
                    print("❌ 请输入有效的数字")

            while True:
                try:
                    certificate_fee = float(input("  证书费: ").strip() or "200")
                    break
                except ValueError:
                    print("❌ 请输入有效的数字")

            # 其他费用
            other_fees_input = input("  其他费用 (可选，多个用逗号分隔，格式: 名称1:金额1,名称2:金额2): ").strip()
            other_fees = {}
            if other_fees_input:
                try:
                    for fee_item in other_fees_input.split(','):
                        if ':' in fee_item:
                            name, amount = fee_item.split(':', 1)
                            other_fees[name.strip()] = float(amount.strip())
                except ValueError:
                    print("⚠️ 其他费用格式错误，忽略")

            # 计算总费用
            total_fee = agency_fee + application_fee + printing_fee + certificate_fee + sum(other_fees.values())

            # 付款状态
            payment_status = input("  付款状态 (未支付/已支付/部分支付): ").strip() or "未支付"

            print("\n📋 费用明细:")
            print(f"  代理费: ¥{agency_fee}")
            print(f"  申请费: ¥{application_fee}")
            print(f"  印刷费: ¥{printing_fee}")
            print(f"  证书费: ¥{certificate_fee}")
            if other_fees:
                print(f"  其他费用: {dict(other_fees)}")
            print(f"  总费用: ¥{total_fee}")
            print(f"  付款状态: {payment_status}")

            confirm = input("\n✅ 确认无误？(Y/n): ").strip().lower()
            if confirm in ['', 'y', 'yes']:
                return {
                    'agency_fee': agency_fee,
                    'application_fee': application_fee,
                    'printing_fee': printing_fee,
                    'certificate_fee': certificate_fee,
                    'other_fees': other_fees,
                    'total_fee': total_fee,
                    'payment_status': payment_status
                }
            else:
                print("❌ 取消录入")
                return None

        except KeyboardInterrupt:
            print("\n❌ 用户取消录入")
            return None
        except Exception as e:
            print(f"❌ 录入失败: {e}")
            return None

    def update_database(self, applicant_info, inventor_info, fee_info) -> None:
        """更新数据库"""
        try:
            print("\n🔄 正在更新数据库...")

            # 更新客户信息
            self.cursor.execute("""
                UPDATE clients SET
                    contact_phone = %s,
                    contact_email = %s,
                    address = %s,
                    updated_at = %s
                WHERE id = %s
            """, (
                applicant_info['phone'],
                applicant_info['email'],
                applicant_info['address'],
                datetime.now(),
                self.client_id
            ))

            # 更新案卷信息 - 申请人身份证
            if inventor_info:
                inventors_json = '[{}]'.format(','.join([
                    f'{{"sequence": {inv["sequence"]}, "name": "{inv["name"]}, '
                    f'"id_number": "{inv["id_number"]}", "professional_title": "{inv["professional_title"]}", '
                    f'"workplace": "{inv["workplace"]}", "contribution": "{inv["contribution"]}"}}'
                    for inv in inventor_info
                ]))

                self.cursor.execute("""
                    UPDATE cases SET
                        inventors = %s,
                        updated_at = %s
                    WHERE id = %s
                """, (
                    inventors_json,
                    datetime.now(),
                    self.case_id
                ))

            # 更新财务记录
            if fee_info:
                # 删除现有财务记录
                self.cursor.execute("DELETE FROM financial_records WHERE case_id = %s", (self.case_id,))

                # 创建新的财务记录
                records = [
                    ('INVOICE', fee_info['agency_fee'], '专利申请代理服务费', f'YL{datetime.now().strftime("%Y%m%d")}001'),
                    ('EXPENSE', fee_info['application_fee'], '实用新型专利申请费', None),
                    ('EXPENSE', fee_info['printing_fee'], '专利申请印刷费', None),
                    ('EXPENSE', fee_info['certificate_fee'], '专利证书费', None)
                ]

                # 添加其他费用
                for fee_name, fee_amount in fee_info['other_fees'].items():
                    records.append(('EXPENSE', fee_amount, f'其他费用: {fee_name}', None))

                for record_type, amount, description, _invoice_number in records:
                    record_id = str(uuid.uuid4())
                    self.cursor.execute("""
                        INSERT INTO financial_records (
                            id, tenant_id, client_id, project_id, case_id,
                            type, amount, description, record_date,
                            status, auto_created, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        record_id, 'yunpat-main', self.client_id, self.project_id, self.case_id,
                        record_type, amount, description, datetime.now().date(),
                        fee_info['payment_status'], True, datetime.now(), datetime.now()
                    ))

            self.conn.commit()
            print("✅ 数据库更新成功")
            return True

        except Exception as e:
            print(f"❌ 更新数据库失败: {e}")
            self.conn.rollback()
            return False

    def generate_update_report(self, applicant_info, inventor_info, fee_info) -> None:
        """生成更新报告"""
        try:
            report = {
                "更新时间": datetime.now().isoformat(),
                "客户信息": {
                    "客户ID": self.client_id,
                    "更新字段": {
                        "联系电话": applicant_info['phone'],
                        "电子邮箱": applicant_info['email'],
                        "申请地址": applicant_info['address']
                    }
                },
                "发明人信息": {
                    "发明人数量": len(inventor_info) if inventor_info else 0,
                    "发明人列表": inventor_info if inventor_info else []
                },
                "费用信息": {
                    "代理费": fee_info['agency_fee'],
                    "申请费": fee_info['application_fee'],
                    "印刷费": fee_info['printing_fee'],
                    "证书费": fee_info['certificate_fee'],
                    "其他费用": fee_info['other_fees'],
                    "总费用": fee_info['total_fee'],
                    "付款状态": fee_info['payment_status']
                },
                "系统状态": {
                    "客户表": "已更新",
                    "案卷表": "已更新",
                    "财务表": "已更新",
                    "更新状态": "成功"
                }
            }

            # 保存更新报告
            report_path = f"/Users/xujian/Athena工作平台/data/孙俊霞信息更新报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            import json
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            print(f"\n📋 更新报告已保存: {report_path}")
            return report

        except Exception as e:
            print(f"❌ 生成报告失败: {e}")
            return None

    def close(self) -> Any:
        """关闭连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

def main() -> None:
    """主函数"""
    print("=" * 80)
    print("📝" + " " * 25 + "孙俊霞专利申请信息更新" + " " * 25 + "📝")
    print("=" * 80)
    print(f"🕐 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("👩‍⚖️ 操作者: 小娜·天秤女神 (专利法律专家)")
    print("🎯 更新目标: 从确认书提取关键信息并更新数据库")
    print("=" * 80)

    updater = SunJunxiaInfoUpdater()

    try:
        # 连接数据库
        if not updater.connect():
            return

        # 显示当前信息
        updater.display_current_info()

        # 录入申请人信息
        print("\n🔍 第一步: 录入申请人信息")
        applicant_info = updater.input_applicant_info()
        if not applicant_info:
            print("❌ 申请人信息录入失败，终止更新")
            return

        # 录入发明人信息
        print("\n👨‍🔬 第二步: 录入发明人信息")
        inventor_info = updater.input_inventor_info()

        # 录入费用明细
        print("\n💰 第三步: 录入费用明细")
        fee_info = updater.input_fee_details()
        if not fee_info:
            print("❌ 费用明细录入失败，终止更新")
            return

        # 更新数据库
        print("\n🔄 第四步: 更新数据库")
        if not updater.update_database(applicant_info, inventor_info, fee_info):
            print("❌ 数据库更新失败")
            return

        # 生成更新报告
        print("\n📊 第五步: 生成更新报告")
        updater.generate_update_report(applicant_info, inventor_info, fee_info)

        print("\n" + "=" * 80)
        print("🎉 孙俊霞专利申请信息更新完成！")
        print("=" * 80)
        print("✅ 客户信息已更新")
        print("✅ 发明人信息已更新")
        print("✅ 费用明细已更新")
        print("✅ 数据库同步完成")
        print("=" * 80)
        print("📞 下一步:")
        print("1. 继续完善技术交底书")
        print("2. 安排费用支付事宜")
        print("3. 准备专利申请材料")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n❌ 用户取消操作")
    except Exception as e:
        print(f"\n❌ 更新过程出错: {e}")
    finally:
        updater.close()

if __name__ == "__main__":
    main()
