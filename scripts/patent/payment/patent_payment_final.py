#!/usr/bin/env python3
"""
专利缴费信息最终处理版本
Final Patent Payment Processing Version

考虑各种专利申请号格式，包括带点号和不带点号的格式
"""

import logging
import os
import re

import pandas as pd
import psycopg2

logger = logging.getLogger(__name__)


class PatentPaymentFinalUpdater:
    """专利缴费信息最终更新器"""

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
            elif any(keyword in col_str for keyword in ['金额', '费用', '缴费', '金额(元)', '费用（人民币）']):
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

        # 移除空格、CN和其他字符，只保留数字和点号
        number = re.sub(r'[^\d\.]', '', number_str)

        # 中国专利申请号通常是数字开头
        if number and len(number) >= 9:
            return number
        return None

    def find_patent_in_database(self, conn, payment_number):
        """在数据库中查找专利，考虑多种格式"""
        cursor = conn.cursor()

        # 生成各种可能的匹配格式
        possible_formats = []

        # 1. 原始格式
        possible_formats.append(payment_number)

        # 2. 如果是13位数字（新格式）
        if len(payment_number) == 13 and payment_number.isdigit():
            year = payment_number[:4]
            payment_number[4]
            serial = payment_number[5:12]
            check = payment_number[12]

            # 数据库可能的格式：年份+序号+校验码（去掉类型码）
            format1 = f"{year}{serial}.{check}"
            format2 = f"{year}{serial}{check}"
            format3 = f"{year}{serial[:6]}.{check}"  # 序号可能少一位

            possible_formats.extend([format1, format2, format3])

        # 3. 如果包含点号，也尝试去掉点号的格式
        if '.' in payment_number:
            possible_formats.append(payment_number.replace('.', ''))

        # 4. 如果不包含点号，也尝试添加点号
        if '.' not in payment_number and len(payment_number) >= 10:
            # 尝试在倒数第1位前加点
            format_with_dot = payment_number[:-1] + '.' + payment_number[-1:]
            possible_formats.append(format_with_dot)

        # 尝试精确匹配
        for fmt in possible_formats:
            cursor.execute("""
                SELECT id, patent_number, patent_name, legal_status
                FROM patents
                WHERE patent_number = %s
            """, (fmt,))

            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'patent_number': result[1],
                    'patent_name': result[2],
                    'legal_status': result[3],
                    'matched_format': fmt
                }

        # 如果精确匹配失败，尝试模糊匹配（只对较长的申请号）
        if len(payment_number) >= 10:
            # 提取年份和后6位进行模糊匹配
            year = payment_number[:4]
            last6 = payment_number[-6:]

            cursor.execute("""
                SELECT id, patent_number, patent_name, legal_status
                FROM patents
                WHERE patent_number LIKE %s
                AND patent_number LIKE %s
                LIMIT 3
            """, (f"{year}%", f"%{last6}%"))

            results = cursor.fetchall()
            if results:
                # 返回第一个匹配的结果
                return {
                    'id': results[0][0],
                    'patent_number': results[0][1],
                    'patent_name': results[0][2],
                    'legal_status': results[0][3],
                    'matched_format': 'fuzzy'
                }

        return None

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

                    logger.debug(f"[patent_payment_final] Exception: {e}")
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

                    logger.debug(f"[patent_payment_final] Exception: {e}")
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
                    patent_id INTEGER,
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
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_patent_id ON patent_payments(patent_id);")

            # 更新的专利统计
            updated_count = 0
            inserted_count = 0
            status_updated = 0

            for record in all_payment_records:
                patent_number = record["patent_number"]

                # 查找对应的专利
                patent_info = self.find_patent_in_database(conn, patent_number)

                if not patent_info:
                    print(f"   ⚠️ 未找到专利: {patent_number}")
                    continue

                print(f"   ✅ 找到专利: {patent_number} -> {patent_info['patent_number']} ({patent_info['patent_name'][:30]}...)")

                patent_id = patent_info['id']

                # 检查是否已有缴费记录
                cursor.execute("""
                    SELECT id FROM patent_payments WHERE patent_id = %s
                """, (patent_id,))

                payment_exists = cursor.fetchone()

                # 插入或更新缴费记录
                if not payment_exists:
                    cursor.execute("""
                        INSERT INTO patent_payments
                        (patent_number, patent_id, payment_amount, payment_date, payment_type, source_file)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        patent_info['patent_number'],  # 使用数据库中的实际申请号
                        patent_id,
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
                        WHERE patent_id = %s
                    """, (
                        record["payment_amount"],
                        record["payment_date"],
                        record["payment_type"],
                        record["source_file"],
                        patent_id
                    ))
                    updated_count += 1

                # 更新专利状态为'有效'
                if patent_info['legal_status'] != '有效':
                    cursor.execute("""
                        UPDATE patents
                        SET legal_status = '有效',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (patent_id,))
                    status_updated += 1

            conn.commit()

            print("\n✅ 数据库更新完成:")
            print(f"   新增缴费记录: {inserted_count} 条")
            print(f"   更新缴费记录: {updated_count} 条")
            print(f"   更新为'有效'状态: {status_updated} 个")

            return True

        except Exception as e:
            print(f"❌ 数据库更新失败: {str(e)}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def process_all_files(self):
        """处理所有缴费文件"""
        print("="*80)
        print("💰 开始处理专利缴费信息（最终版本）")
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

        print(f"\n📊 总共提取到 {len(all_payment_records)} 条缴费记录")

        # 更新数据库
        return self.update_database(all_payment_records)


def main():
    """主函数"""
    updater = PatentPaymentFinalUpdater()
    success = updater.process_all_files()

    if success:
        print("\n✅ 专利缴费信息处理完成！")
        print("\n处理说明：")
        print("1. 已将缴费记录插入到 patent_payments 表")
        print("2. 已将对应专利的法律状态更新为'有效'")
        print("3. 缴费申请号与数据库中的申请号进行了智能匹配")
    else:
        print("\n❌ 处理失败，请检查错误信息")


if __name__ == "__main__":
    main()
