#!/usr/bin/env python3
"""
2025年专利官费缴费记录导入工具
基于成功经验，导入官费缴费记录到数据库
"""

import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FeePaymentImporter:
    """官费缴费记录导入器"""

    def __init__(self):
        # 数据库配置
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "athena_business",
            "user": "postgres",
            "password": "xj781102"
        }

        # 缓存现有数据
        self.existing_patents = set()
        self.client_map = {}
        self.patent_map = {}

    def load_existing_data(self):
        """加载现有专利和客户数据"""
        logger.info("🔗 加载现有数据...")

        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # 加载现有专利申请号
            cursor.execute("""
                SELECT patent_id, application_number, title
                FROM patents
                WHERE application_number IS NOT NULL
            """)
            for row in cursor.fetchall():
                if row[1]:
                    clean_app_num = self._clean_patent_number(row[1])
                    self.existing_patents.add(clean_app_num)
                    self.patent_map[clean_app_num] = row[0]

            # 加载现有客户
            cursor.execute("""
                SELECT id, name
                FROM clients
                WHERE name IS NOT NULL
            """)
            for row in cursor.fetchall():
                name = row[1].strip()
                self.client_map[name] = row[0]

            logger.info(f"  现有专利申请号: {len(self.existing_patents)}")
            logger.info(f"  现有客户: {len(self.client_map)}")

        except Exception as e:
            logger.error(f"加载现有数据失败: {str(e)}")
        finally:
            if conn:
                conn.close()

    def _clean_patent_number(self, patent_num: str) -> str:
        """清理专利申请号"""
        if not patent_num:
            return ""

        patent_num = str(patent_num).strip()

        # 移除常见的格式问题
        patent_num = re.sub(r'[^\d.]', '', patent_num)

        # 标准化格式：移除多余的点
        while '..' in patent_num:
            patent_num = patent_num.replace('..', '.')

        # 确保只有一个点
        if patent_num.count('.') > 1:
            parts = patent_num.split('.')
            patent_num = parts[0] + '.' + parts[1]

        return patent_num

    def analyze_excel_structure(self, excel_path: str) -> dict:
        """分析Excel表格结构"""
        logger.info("📊 分析Excel表格结构...")

        try:
            # 先读取表头行
            try:
                header_df = pd.read_excel(excel_path, nrows=1, engine='openpyxl')
                columns = header_df.columns
                # 再读取数据行，跳过第一行汇总
                df = pd.read_excel(excel_path, engine='openpyxl', skiprows=1, header=None)
                df.columns = columns
            except Exception as e:
                # 记录异常但不中断流程
                logger.debug(f"[fee_payment_importer] Exception: {e}")
                try:
                    header_df = pd.read_excel(excel_path, nrows=1, engine='xlrd')
                    columns = header_df.columns
                    df = pd.read_excel(excel_path, engine='xlrd', skiprows=1, header=None)
                    df.columns = columns
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[fee_payment_importer] Exception: {e}")
                    # 如果都失败了，尝试使用CSV格式
                    header_df = pd.read_csv(excel_path, nrows=1)
                    columns = header_df.columns
                    df = pd.read_csv(excel_path, skiprows=1, header=None)
                    df.columns = columns

            print("\n📋 Excel表格列名:")
            for i, col in enumerate(df.columns):
                print(f"  {i+1:2d}. {col}")

            print("\n📊 数据概览:")
            print(f"  总行数: {len(df)} (不含汇总行)")
            print(f"  总列数: {len(df.columns)}")

            # 智能识别列
            column_mapping = {}
            for col in df.columns:
                col_str = str(col).strip().lower()

                # 精确匹配
                if '申请号' in col_str:
                    column_mapping[col] = 'application_number'
                elif '专利名称' in col_str or '发明名称' in col_str:
                    column_mapping[col] = 'patent_title'
                elif '申请日' in col_str:
                    column_mapping[col] = 'filing_date'
                elif '缴费金额' in col_str or '金额' in col_str:
                    column_mapping[col] = 'payment_amount'
                elif '缴费日期' in col_str or '日期' in col_str:
                    column_mapping[col] = 'payment_date'
                elif '缴费类型' in col_str or '费用类型' in col_str:
                    column_mapping[col] = 'payment_type'
                elif '客户名称' in col_str or '申请人' in col_str:
                    column_mapping[col] = 'client_name'
                elif '专利号' in col_str:
                    column_mapping[col] = 'patent_number'
                elif '缴费项目' in col_str or '缴费说明' in col_str:
                    column_mapping[col] = 'payment_description'
                elif '状态' in col_str:
                    column_mapping[col] = 'status'

            print("\n🔍 智能识别的列映射:")
            for col, mapped in column_mapping.items():
                print(f"  {col} -> {mapped}")

            return {
                "column_mapping": column_mapping,
                "total_rows": len(pd.read_excel(excel_path)),
                "sample_data": df.head(3).to_dict('records')
            }

        except Exception as e:
            logger.error(f"分析失败: {str(e)}")
            return None

    def extract_payment_records(self, excel_path: str, column_mapping: dict) -> list[dict]:
        """提取缴费记录"""
        logger.info("📝 提取缴费记录...")

        try:
            # 先读取表头行
            try:
                header_df = pd.read_excel(excel_path, nrows=1, engine='openpyxl')
                columns = header_df.columns
                # 再读取数据行，跳过第一行汇总
                df = pd.read_excel(excel_path, engine='openpyxl', skiprows=1, header=None)
                df.columns = columns
            except Exception as e:
                # 记录异常但不中断流程
                logger.debug(f"[fee_payment_importer] Exception: {e}")
                try:
                    header_df = pd.read_excel(excel_path, nrows=1, engine='xlrd')
                    columns = header_df.columns
                    df = pd.read_excel(excel_path, engine='xlrd', skiprows=1, header=None)
                    df.columns = columns
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[fee_payment_importer] Exception: {e}")
                    # 如果都失败了，尝试使用CSV格式
                    header_df = pd.read_csv(excel_path, nrows=1)
                    columns = header_df.columns
                    df = pd.read_csv(excel_path, skiprows=1, header=None)
                    df.columns = columns

            payment_records = []

            for idx, row in df.iterrows():
                try:
                    # 提取申请号/专利号
                    patent_num = None
                    if 'patent_number' in column_mapping:
                        col = column_mapping['patent_number']
                        if pd.notna(row[col]):
                            patent_num = self._clean_patent_number(str(row[col]))
                    elif 'application_number' in column_mapping:
                        col = column_mapping['application_number']
                        if pd.notna(row[col]):
                            patent_num = self._clean_patent_number(str(row[col]))

                    # 如果没有申请号，跳过
                    if not patent_num:
                        continue

                    # 提取专利名称
                    patent_title = ""
                    if 'patent_title' in column_mapping:
                        col = column_mapping['patent_title']
                        if pd.notna(row[col]):
                            patent_title = str(row[col]).strip()

                    # 提取客户名称
                    client_name = ""
                    if 'client_name' in column_mapping:
                        col = column_mapping['client_name']
                        if pd.notna(row[col]):
                            client_name = str(row[col]).strip()

                    # 提取缴费金额
                    payment_amount = 0.0
                    if 'payment_amount' in column_mapping:
                        col = column_mapping['payment_amount']
                        if pd.notna(row[col]):
                            amount_str = str(row[col]).replace(',', '').replace('￥', '').replace('¥', '')
                            try:
                                payment_amount = float(amount_str)
                            except Exception as e:
                                # 记录异常但不中断流程
                                logger.debug(f"[fee_payment_importer] Exception: {e}")
                                payment_amount = 0.0

                    # 提取缴费日期
                    payment_date = None
                    if 'payment_date' in column_mapping:
                        col = column_mapping['payment_date']
                        if pd.notna(row[col]):
                            payment_date = self._parse_date(str(row[col]))

                    # 提取缴费类型
                    payment_type = "未知"
                    if 'payment_type' in column_mapping:
                        col = column_mapping['payment_type']
                        if pd.notna(row[col]):
                            payment_type = str(row[col]).strip()
                    elif 'payment_description' in column_mapping:
                        col = column_mapping['payment_description']
                        if pd.notna(row[col]):
                            desc = str(row[col]).strip()
                            # 从描述中推断类型
                            if '申请费' in desc:
                                payment_type = "申请费"
                            elif '实质审查费' in desc:
                                payment_type = "实质审查费"
                            elif '年费' in desc:
                                payment_type = "年费"
                            elif '滞纳金' in desc:
                                payment_type = "滞纳金"

                    # 构建记录
                    record = {
                        "patent_number": patent_num,
                        "patent_title": patent_title,
                        "client_name": client_name,
                        "payment_amount": payment_amount,
                        "payment_date": payment_date,
                        "payment_type": payment_type,
                        "source_file": Path(excel_path).name,
                        "import_time": datetime.now(),
                        "row_index": idx + 2  # +2 因为跳过了第一行汇总和索引从0开始
                    }

                    payment_records.append(record)

                except Exception as e:
                    logger.warning(f"处理第{idx+1}行出错: {str(e)}")
                    continue

            logger.info(f"  提取到 {len(payment_records)} 条缴费记录")
            return payment_records

        except Exception as e:
            logger.error(f"提取记录失败: {str(e)}")
            return []

    def _parse_date(self, date_str: str) -> datetime | None:
        """解析日期"""
        if not date_str or pd.isna(date_str):
            return None

        date_str = str(date_str).strip()

        # 尝试解析各种日期格式
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日", "%Y.%m.%d", "%Y%m%d"]:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt
            except Exception as e:
                # 记录异常但不中断流程
                logger.debug(f"[fee_payment_importer] Exception: {e}")
                continue

        # 尝试解析纯数字格式
        if date_str.isdigit() and len(date_str) == 8:
            try:
                dt = datetime.strptime(date_str, "%Y%m%d")
                return dt
            except Exception as e:

                # 记录异常但不中断流程

                logger.debug(f"[fee_payment_importer] Exception: {e}")
        return None

    def analyze_payment_data(self, payment_records: list[dict]) -> dict:
        """分析缴费数据"""
        logger.info("📈 分析缴费数据...")

        total_amount = sum(r['payment_amount'] for r in payment_records)
        unique_patents = len({r['patent_number'] for r in payment_records})
        payment_types = {}

        for record in payment_records:
            ptype = record['payment_type']
            payment_types[ptype] = payment_types.get(ptype, 0) + 1

        analysis = {
            "total_records": len(payment_records),
            "total_amount": total_amount,
            "unique_patents": unique_patents,
            "payment_types": payment_types,
            "average_amount": total_amount / len(payment_records) if payment_records else 0,
            "date_range": {
                "earliest": min(r['payment_date'] for r in payment_records if r['payment_date']),
                "latest": max(r['payment_date'] for r in payment_records if r['payment_date'])
            }
        }

        logger.info(f"  总记录数: {analysis['total_records']}")
        logger.info(f"  总金额: ¥{analysis['total_amount']:,.2f}")
        logger.info(f"  涉及专利: {analysis['unique_patents']} 项")
        logger.info(f"  平均金额: ¥{analysis['average_amount']:,.2f}")

        return analysis

    def save_to_database(self, payment_records: list[dict]):
        """保存到数据库"""
        logger.info("💾 保存数据到数据库...")

        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # 检查是否存在财务记录表
            table_exists = False
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'financial_records'
                )
            """)
            table_exists = cursor.fetchone()[0]

            if not table_exists:
                logger.info("  创建财务记录表...")
                cursor.execute("""
                    CREATE TABLE financial_records (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        patent_id UUID REFERENCES patents(patent_id),
                        client_id UUID REFERENCES clients(id),
                        record_type VARCHAR(50) NOT NULL,
                        amount DECIMAL(12,2) NOT NULL,
                        record_date DATE,
                        description TEXT,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        source VARCHAR(100),
                        row_number INTEGER
                    );
                """)

                # 创建索引
                cursor.execute("CREATE INDEX idx_financial_patent ON financial_records(patent_id);")
                cursor.execute("CREATE INDEX idx_financial_date ON financial_records(record_date);")
                logger.info("  ✅ 财务记录表创建成功")

            # 准备数据
            records_to_insert = []
            matched_patents = 0
            matched_clients = 0
            unmatched_patents = 0

            for record in payment_records:
                patent_id = self.patent_map.get(record['patent_number'])
                client_id = None

                # 如果有客户名称，尝试匹配
                if record['client_name']:
                    # 尝试精确匹配
                    if record['client_name'] in self.client_map:
                        client_id = self.client_map[record['client_name']]
                    else:
                        # 尝试模糊匹配
                        for name, cid in self.client_map.items():
                            if record['client_name'] in name or name in record['client_name']:
                                client_id = cid
                                break

                if patent_id:
                    matched_patents += 1
                if client_id:
                    matched_clients += 1
                else:
                    unmatched_patents += 1

                financial_record = {
                    'patent_id': patent_id,
                    'client_id': client_id,
                    'record_type': record['payment_type'],
                    'amount': record['payment_amount'],
                    'record_date': record['payment_date'],
                    'description': f"缴费记录 - {record['payment_type']}",
                    'metadata': json.dumps({
                        'source_file': record['source_file'],
                        'import_time': record['import_time'].isoformat(),
                        'patent_number': record['patent_number'],
                        'patent_title': record['patent_title'],
                        'row_index': record['row_index']
                    }, ensure_ascii=False),
                    'source': 'fee_importer',
                    'row_number': record['row_index']
                }

                records_to_insert.append(financial_record)

            # 插入数据
            if records_to_insert:
                columns = records_to_insert[0].keys()
                values = [[record[col] for col in columns] for record in records_to_insert]

                insert_query = f"""
                    INSERT INTO financial_records ({', '.join(columns)})
                    VALUES %s
                """

                execute_values(cursor, insert_query, values)

                conn.commit()
                logger.info(f"✅ 成功保存 {len(records_to_insert)} 条财务记录")
                logger.info(f"  匹配到专利: {matched_patents} 条")
                logger.info(f"  匹配到客户: {matched_clients} 条")
                logger.info(f"  未匹配专利: {unmatched_patents} 条")

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"保存失败: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()

    def export_results(self, payment_records: list[dict], analysis: dict, excel_path: str):
        """导出结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 导出到JSON
        json_file = f"fee_payment_import_result_{timestamp}.json"
        export_data = {
            "excel_file": excel_path,
            "analysis": analysis,
            "total_records": len(payment_records),
            "sample_records": payment_records[:10],
            "import_time": datetime.now().isoformat()
        }

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        logger.info(f"📋 结果已导出到: {json_file}")

        # 导出到Excel
        if payment_records:
            df = pd.DataFrame([
                {
                    '申请号': r.get('patent_number', ''),
                    '专利名称': r.get('patent_title', '')[:50],
                    '客户名称': r.get('client_name', '')[:50],
                    '缴费金额': r.get('payment_amount', 0),
                    '缴费日期': r.get('payment_date', ''),
                    '缴费类型': r.get('payment_type', ''),
                    '来源文件': r.get('source_file', '')
                }
                for r in payment_records
            ])

            excel_file = f"官费缴费记录_{timestamp}.xlsx"
            df.to_excel(excel_file, index=False)
            logger.info(f"📊 数据已导出到: {excel_file}")

        return json_file


def main():
    """主函数"""
    excel_path = "/Users/xujian/工作/10_归档文件/2025年专利官费缴费记录(1).xlsx"

    print("🚀 2025年专利官费缴费记录导入工具")
    print("=" * 60)

    # 检查文件
    if not Path(excel_path).exists():
        logger.error(f"❌ 文件不存在: {excel_path}")
        return False

    # 创建导入器
    importer = FeePaymentImporter()

    try:
        # 1. 加载现有数据
        importer.load_existing_data()

        # 2. 分析Excel结构
        structure_analysis = importer.analyze_excel_structure(excel_path)
        if not structure_analysis:
            logger.error("❌ 无法分析Excel结构")
            return False

        # 3. 提取缴费记录
        payment_records = importer.extract_payment_records(excel_path, structure_analysis['column_mapping'])

        if not payment_records:
            logger.error("❌ 没有提取到缴费记录")
            return False

        # 4. 分析数据
        analysis = importer.analyze_payment_data(payment_records)

        # 5. 保存到数据库
        importer.save_to_database(payment_records)

        # 6. 导出结果
        importer.export_results(payment_records, analysis, excel_path)

        print("\n✨ 导入完成！")
        print(f"  处理记录: {len(payment_records)} 条")
        print(f"  总金额: ¥{analysis['total_amount']:,.2f}")
        print(f"  涉及专利: {analysis['unique_patents']} 项")

        return True

    except Exception as e:
        logger.error(f"❌ 导入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
