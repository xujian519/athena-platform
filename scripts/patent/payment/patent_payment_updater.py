#!/usr/bin/env python3
"""
专利缴费信息解析与更新
Patent Payment Information Parser and Updater

解析缴费表格，更新数据库中的缴费信息和专利状态
"""

import logging

import psycopg2

logger = logging.getLogger(__name__)

import json
import os
import re
from datetime import datetime

import pandas as pd


class PatentPaymentUpdater:
    """专利缴费信息更新器"""

    def __init__(self):
        # PostgreSQL配置
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "patent_archive",
            "user": "xujian",
            "password": ""
        }

        # 检查PostgreSQL路径
        postgres_path = "/opt/homebrew/opt/postgresql@17/bin"
        if postgres_path not in os.environ.get("PATH", ""):
            os.environ["PATH"] = postgres_path + ":" + os.environ.get("PATH", "")

        self.payment_folder = "/Users/xujian/工作/06_财务档案/04_缴费信息表"

    def get_connection(self):
        """获取数据库连接"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            print(f"❌ 数据库连接失败: {str(e)}")
            return None

    def parse_payment_file(self, file_path):
        """解析缴费文件"""
        print(f"\n📄 解析文件: {os.path.basename(file_path)}")

        try:
            # 尝试读取Excel文件
            df = pd.read_excel(file_path, engine='openpyxl')

            # 显示列名
            print(f"   列名: {list(df.columns)}")
            print(f"   行数: {len(df)}")

            # 查找关键的列
            column_mapping = self.identify_columns(df.columns)
            print(f"   识别的列映射: {column_mapping}")

            # 提取缴费记录
            payment_records = []

            for _index, row in df.iterrows():
                # 跳过空行
                if row.empty or all(pd.isna(row.values)):
                    continue

                # 提取申请号
                patent_number = self.extract_patent_number(row, column_mapping)
                if not patent_number:
                    continue

                # 提取缴费信息
                record = {
                    "patent_number": patent_number,
                    "payment_amount": self.extract_payment_amount(row, column_mapping),
                    "payment_date": self.extract_payment_date(row, column_mapping),
                    "payment_type": self.extract_payment_type(row, column_mapping),
                    "source_file": os.path.basename(file_path)
                }

                payment_records.append(record)

            print(f"   提取到 {len(payment_records)} 条缴费记录")
            return payment_records

        except Exception as e:
            print(f"   ❌ 解析失败: {str(e)}")
            return []

    def identify_columns(self, columns):
        """识别列名"""
        mapping = {}

        for col in columns:
            if not col or pd.isna(col):
                continue

            col_str = str(col).strip()

            # 申请号相关
            if any(keyword in col_str for keyword in ['申请号', '专利号', '案卷号', '专利号']):
                mapping["patent_number"] = col

            # 缴费金额相关
            elif any(keyword in col_str for keyword in ['金额', '费用', '缴费', '金额(元)', '费用(元)']):
                mapping["amount"] = col

            # 缴费日期相关
            elif any(keyword in col_str for keyword in ['缴费日期', '付款日期', '日期', '时间']):
                mapping["date"] = col

            # 缴费类型相关
            elif any(keyword in col_str for keyword in ['费用种类', '类型', '项目', '费用名称']):
                mapping["type"] = col

        return mapping

    def extract_patent_number(self, row, column_mapping):
        """提取申请号"""
        if "patent_number" not in column_mapping:
            # 尝试从其他列找申请号
            for col in row.index:
                if any(keyword in str(col) for keyword in ['申请号', '专利号', '案卷号']):
                    value = row[col]
                    if pd.notna(value):
                        return self.clean_patent_number(str(value))
            return None

        value = row[column_mapping["patent_number"]
        if pd.notna(value):
            return self.clean_patent_number(str(value))
        return None

    def clean_patent_number(self, number_str):
        """清理申请号格式"""
        if not number_str or number_str == 'nan':
            return None

        # 移除空格和其他字符
        number = re.sub(r'[^\d\.]', '', number_str)

        # 中国专利申请号通常是数字开头
        if number and len(number) >= 8:
            return number
        return None

    def convert_patent_number_format(self, payment_number):
        """转换缴费表格中的申请号格式到数据库格式"""
        # 缴费表格式：YYYY(4) + 类型码(1) + 序号(7) + 校验码(1) = 13位
        # 数据库格式：YYYY(4) + 序号(7) + 校验码(1) = 12位（可能包含小数点）

        if len(payment_number) == 13:
            # 提取各部分
            year = payment_number[:4]
            payment_number[4:5]
            serial = payment_number[5:12]
            check = payment_number[12:13]

            # 数据库中的格式：年份 + 序号 + 校验码
            db_format1 = f"{year}{serial}.{check}"
            db_format2 = f"{year}{serial}{check}"
            db_format3 = f"{year}{serial[:6]}.{check}"  # 有时序号少一位

            return [db_format1, db_format2, db_format3]
        elif len(payment_number) > 10:
            # 尝试其他可能的转换
            year = payment_number[:4]
            rest = payment_number[4:]
            return [f"{year}{rest}", f"{year}{rest[:-1]}.{rest[-1]}"]

        return [payment_number]

    def extract_payment_amount(self, row, column_mapping):
        """提取缴费金额"""
        if "amount" in column_mapping:
            value = row[column_mapping["amount"]
            if pd.notna(value):
                # 提取数字
                amount_str = str(value).replace(',', '').replace('元', '')
                try:
                    return float(amount_str)
                except Exception as e:

                    # 记录异常但不中断流程

                    logger.debug(f"[patent_payment_updater] Exception: {e}")
        return None

    def extract_payment_date(self, row, column_mapping):
        """提取缴费日期"""
        if "date" in column_mapping:
            value = row[column_mapping["date"]
            if pd.notna(value):
                # 尝试解析日期
                try:
                    if hasattr(value, 'strftime'):
                        return value.strftime('%Y-%m-%d')
                    else:
                        # 尝试解析字符串日期
                        date_str = str(value)
                        # 简单的日期格式识别
                        if re.match(r'\d{4}-\d{1,2}-\d{1,2}', date_str):
                            return date_str
                except Exception as e:

                    # 记录异常但不中断流程

                    logger.debug(f"[patent_payment_updater] Exception: {e}")
        return None

    def extract_payment_type(self, row, column_mapping):
        """提取缴费类型"""
        if "type" in column_mapping:
            value = row[column_mapping["type"]
            if pd.notna(value):
                return str(value).strip()
        return None

    def update_database(self, all_payment_records):
        """更新数据库"""
        conn = self.get_connection()
        if not conn:
            return False

        cursor = conn.cursor()

        try:
            # 创建缴费记录表（如果不存在）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patent_payments (
                    id SERIAL PRIMARY KEY,
                    patent_number VARCHAR(50) NOT NULL,
                    payment_amount DECIMAL(10,2),
                    payment_date DATE,
                    payment_type VARCHAR(100),
                    source_file VARCHAR(200),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_patent_number ON patent_payments(patent_number);")

            # 更新的专利统计
            updated_count = 0
            inserted_count = 0

            for record in all_payment_records:
                patent_number = record["patent_number"]

                # 查找对应的专利 - 使用格式转换
                patent_id = None

                # 转换申请号格式
                converted_formats = self.convert_patent_number_format(patent_number)

                # 1. 尝试原始格式
                cursor.execute("""
                    SELECT id FROM patents WHERE patent_number = %s
                """, (patent_number,))
                patent_result = cursor.fetchone()
                if patent_result:
                    patent_id = patent_result[0]

                # 2. 尝试转换后的格式
                if not patent_id:
                    for fmt in converted_formats:
                        cursor.execute("""
                            SELECT id FROM patents WHERE patent_number = %s
                        """, (fmt,))
                        patent_result = cursor.fetchone()
                        if patent_result:
                            patent_id = patent_result[0]
                            print(f"   ✅ 找到匹配: {patent_number} -> {fmt}")
                            break

                # 3. 如果还是没找到，尝试更宽松的匹配（只匹配年份+后6位）
                if not patent_id:
                    year = patent_number[:4]
                    last6 = patent_number[-6:]
                    cursor.execute("""
                        SELECT id FROM patents
                        WHERE patent_number LIKE %s
                        AND patent_number LIKE %s
                        LIMIT 1
                    """, (f"{year}%", f"%{last6}"))
                    patent_result = cursor.fetchone()
                    if patent_result:
                        patent_id = patent_result[0]
                        print(f"   ✅ 模糊匹配: {patent_number}")

                if not patent_id:
                    print(f"   ⚠️ 未找到专利: {patent_number}")
                    continue

                # 检查是否已有缴费记录
                cursor.execute("""
                    SELECT id FROM patent_payments WHERE patent_number = %s
                """, (patent_number,))

                payment_exists = cursor.fetchone()

                # 插入或更新缴费记录
                if not payment_exists:
                    cursor.execute("""
                        INSERT INTO patent_payments
                        (patent_number, payment_amount, payment_date, payment_type, source_file)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        record["patent_number"],
                        record["payment_amount"],
                        record["payment_date"],
                        record["payment_type"],
                        record["source_file"]
                    ))
                    inserted_count += 1
                else:
                    cursor.execute("""
                        UPDATE patent_payments
                        SET payment_amount = %s,
                            payment_date = %s,
                            payment_type = %s,
                            source_file = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE patent_number = %s
                    """, (
                        record["payment_amount"],
                        record["payment_date"],
                        record["payment_type"],
                        record["source_file"],
                        patent_number
                    ))
                    updated_count += 1

                # 更新专利状态为'有效'
                cursor.execute("""
                    UPDATE patents
                    SET legal_status = '有效',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (patent_id,))

            conn.commit()

            print("\n✅ 数据库更新完成:")
            print(f"   新增缴费记录: {inserted_count} 条")
            print(f"   更新缴费记录: {updated_count} 条")
            print(f"   标记为'有效'的专利: {inserted_count + updated_count} 个")

            return True

        except Exception as e:
            print(f"❌ 数据库更新失败: {str(e)}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def generate_report(self, all_payment_records):
        """生成报告"""
        print("\n" + "="*80)
        print("📊 专利缴费信息处理报告")
        print("="*80)

        # 统计信息
        total_records = len(all_payment_records)
        total_amount = sum(r["payment_amount"] for r in all_payment_records if r["payment_amount"])

        print("\n1. 处理统计:")
        print(f"   总缴费记录数: {total_records}")
        print(f"   总缴费金额: ¥{total_amount:,.2f}")

        # 按文件统计
        file_stats = {}
        for record in all_payment_records:
            file_name = record["source_file"]
            if file_name not in file_stats:
                file_stats[file_name] = {"count": 0, "amount": 0}
            file_stats[file_name]["count"] += 1
            if record["payment_amount"]:
                file_stats[file_name]["amount"] += record["payment_amount"]

        print("\n2. 文件统计:")
        for file_name, stats in file_stats.items():
            print(f"   {file_name}:")
            print(f"     记录数: {stats['count']}")
            print(f"     金额: ¥{stats['amount']:,.2f}")

        # 按缴费类型统计
        type_stats = {}
        for record in all_payment_records:
            payment_type = record["payment_type"] or "未知"
            if payment_type not in type_stats:
                type_stats[payment_type] = {"count": 0, "amount": 0}
            type_stats[payment_type]["count"] += 1
            if record["payment_amount"]:
                type_stats[payment_type]["amount"] += record["payment_amount"]

        if type_stats:
            print("\n3. 缴费类型统计:")
            for payment_type, stats in type_stats.items():
                print(f"   {payment_type}: {stats['count']}条, ¥{stats['amount']:,.2f}")

        # 保存详细报告
        report_data = {
            "处理时间": datetime.now().isoformat(),
            "统计信息": {
                "总记录数": total_records,
                "总金额": total_amount
            },
            "文件统计": file_stats,
            "类型统计": type_stats,
            "缴费记录": all_payment_records
        }

        with open("patent_payment_report.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print("\n✅ 详细报告已保存到: patent_payment_report.json")

    def process_all_files(self):
        """处理所有缴费文件"""
        print("="*80)
        print("💰 开始处理专利缴费信息")
        print("="*80)

        all_payment_records = []

        # 遍历所有Excel文件
        for file_name in os.listdir(self.payment_folder):
            if file_name.endswith(('.xlsx', '.xls', '.xlsm')):
                file_path = os.path.join(self.payment_folder, file_name)
                records = self.parse_payment_file(file_path)
                all_payment_records.extend(records)

        if not all_payment_records:
            print("\n⚠️ 未找到有效的缴费记录")
            return False

        # 生成报告
        self.generate_report(all_payment_records)

        # 更新数据库
        return self.update_database(all_payment_records)


def main():
    """主函数"""
    updater = PatentPaymentUpdater()
    success = updater.process_all_files()

    if success:
        print("\n✅ 专利缴费信息处理完成！")
    else:
        print("\n❌ 处理失败，请检查错误信息")


if __name__ == "__main__":
    main()
